# smell-pi

**Replicating [SmellNet](https://github.com/MIT-MI/SmellNet) on a Raspberry Pi.**

![smell-pi hardware rig — Raspberry Pi, breadboard, and the full sensor array](docs/img/rig_overview.jpg)

SmellNet (Feng et al., 2025) is the first large-scale open-source dataset for real-world smell recognition using portable gas and chemical sensors. The original study collected data with an Adafruit ESP32 Feather running Arduino firmware. `smell-pi` adapts the full pipeline — sensor collection, preprocessing, model training, and edge inference — to run natively in Python on a Raspberry Pi.

- **Paper**: [SMELLNET: A Large-scale Dataset for Real-world Smell Recognition](https://arxiv.org/abs/2506.00239) (Feng et al., 2025)
- **Original repo**: https://github.com/MIT-MI/SmellNet
- **Dataset**: [SmellNet on Hugging Face](https://huggingface.co/datasets/DeweiFeng/smell-net)

This project is an independent replication effort and is not affiliated with the SmellNet authors.

---

## Scope

This repo is specifically the **Pi-side collection + inference package**:

- **Shipped today**: Python data-collection scripts that drive the sensor suite at 2 Hz and write CSV recordings, plus one pre-trained checkpoint bundle exported from the upstream training harness.
- **Training happens elsewhere**: the supervised + autoresearch training harness lives in the sibling repo [`smellnet-autoresearch`](https://github.com/smartinelle/smellnet-autoresearch), which trains on the upstream SmellNet dataset.
- **Planned**: an on-device real-time inference loop that runs the exported checkpoint against live sensor data.

See [`docs/overview.md`](docs/overview.md) for the full phase plan and how `smell-pi` differs from the original SmellNet setup.

---

## Hardware

![Close-up of the sensor array — Seeed Multichannel Gas V2, three MQ sensors on breakout boards, and walnuts in frame for a live recording](docs/img/sensor_array.jpg)

The Raspberry Pi has no built-in ADC, so analog MQ sensors are read through an **ADS1115** 16-bit ADC over I2C. All other sensors connect directly.

| Component | Channels | Interface |
|---|---|---|
| Seeed Grove Multichannel Gas Sensor V2 | NO2, C2H5OH, VOC, CO | I2C (0x08) |
| Adafruit BME680 | Temperature, Pressure, Humidity, Gas Resistance | I2C (0x76) |
| MQ-3 / MQ-5 / MQ-9 | Alcohol, LPG / natural gas, CO / flammable gases | Analog → ADS1115 (0x48) |

Full wiring diagrams, I2C address map, calibration notes, and BOM live in [`docs/hardware.md`](docs/hardware.md) and [`docs/wiring.md`](docs/wiring.md).

---

## Repository Layout

```
smell-pi/
├── CLAUDE.md                # agent-facing project context
├── README.md
├── collection/              # RPi data collection scripts
│   ├── collect.py           #   2 Hz sensor recorder → data/{split}/{substance}/*.csv
│   └── test_sensors.py      #   bus sanity check
├── artifacts/               # exported edge-ready checkpoint bundles (trained upstream)
│   └── smellnet_base_phase2_exact_upstream/
│       ├── checkpoint.pt    #   ScentFormer 6-channel classifier, 57.97% Top-1
│       ├── labels.json
│       ├── preprocessing.json
│       ├── training_metrics.json
│       └── final_test_metrics.json
└── docs/                    # project documentation (see below)
```

`data/` is gitignored — raw recordings live only on the Pi that produced them. Training / experiment code is **not** in this repo; it lives in [`smellnet-autoresearch`](https://github.com/smartinelle/smellnet-autoresearch).

Documentation in [`docs/`](docs/):

- [`overview.md`](docs/overview.md) — project goals, phase plan, differences from original
- [`hardware.md`](docs/hardware.md) — sensor suite, BOM, calibration
- [`wiring.md`](docs/wiring.md) — pin-level wiring diagrams
- [`data_pipeline.md`](docs/data_pipeline.md) — CSV formats (raw collection, paper, exported), FOTD preprocessing, sliding windows
- [`models.md`](docs/models.md) — ScentFormer and baseline architectures
- [`exported_artifacts.md`](docs/exported_artifacts.md) — edge-ready checkpoint bundle and input contract
- [`commands.md`](docs/commands.md) — common commands cheat sheet

---

## Quick Start

### 1. Install dependencies (on the Raspberry Pi)

```bash
sudo apt install -y python3-pip i2c-tools
sudo raspi-config   # enable I2C

pip install \
    adafruit-circuitpython-bme680 \
    adafruit-circuitpython-ads1x15 \
    smbus2 RPi.GPIO \
    torch pandas numpy
```

Verify sensors are on the bus:

```bash
i2cdetect -y 1      # expect 0x08 (Seeed), 0x48 (ADS1115), 0x76 (BME680)
python collection/test_sensors.py
```

### 2. Collect data

```bash
# Collect a 2-minute cinnamon training recording at 2 Hz
python collection/collect.py cinnamon --duration 120

# Collect into the testing split
python collection/collect.py cinnamon --split testing --duration 60
```

Recordings land in `data/{split}/{substance}/{substance}_NNN.csv` with 14 raw sensor channels at 2 Hz. The full channel layout is documented in [`docs/data_pipeline.md`](docs/data_pipeline.md).

### 3. Train a model

Training is **not** performed in this repo. The pre-trained checkpoint in [`artifacts/smellnet_base_phase2_exact_upstream/`](artifacts/smellnet_base_phase2_exact_upstream/) was produced by the training harness in the sibling repo [`smellnet-autoresearch`](https://github.com/smartinelle/smellnet-autoresearch), trained on the upstream SmellNet dataset. See [`docs/exported_artifacts.md`](docs/exported_artifacts.md) for the input contract and test metrics.

### 4. Real-time inference (planned)

An on-device inference loop is planned but not yet committed. It will need to (a) apply the 6-channel input contract from `preprocessing.json`, (b) bridge smell-pi's raw MQ voltages to the `Alcohol` / `LPG` PPM channels the model expects, and (c) run the sliding-window classifier on-device.

---

## Preprocessing (matches original SmellNet)

1. **Baseline subtraction** — subtract the first row of each recording to remove sensor offset.
2. **First-order temporal difference (FOTD)** — `df.diff(periods=25)` at 2 Hz (= 12.5 s lag), emphasizing rate-of-change over absolute values.
3. **Sliding window** — default window length 100 samples, stride 50.

Details in [`docs/data_pipeline.md`](docs/data_pipeline.md).

---

## Primary Model — ScentFormer

A 4-layer, 8-head Transformer encoder with sinusoidal positional encoding, mean pooling, and a small MLP classifier head. In the SmellNet paper, input shape is `(batch, T, 12)` over 50 substance classes and the model reaches **58.5% Top-1 accuracy** on the offline test set.

The exported checkpoint shipped in this repo is a variant trained on a **6-channel subset** (`NO2, C2H5OH, VOC, CO, Alcohol, LPG`) with `input_dim = 6, model_dim = 512, num_heads = 8, num_layers = 6`, reaching **57.97% Top-1** on held-out test data. See [`docs/exported_artifacts.md`](docs/exported_artifacts.md) for the full input contract. Baselines (LSTM / CNN / MLP) and the autoresearch training loops live in [`smellnet-autoresearch`](https://github.com/smartinelle/smellnet-autoresearch), not in this repo.

---

## Citation

If you use this work, please cite the original SmellNet paper:

```bibtex
@article{feng2025smellnet,
  title   = {SMELLNET: A Large-scale Dataset for Real-world Smell Recognition},
  author  = {Feng, Dewei and others},
  journal = {arXiv preprint arXiv:2506.00239},
  year    = {2025},
  url     = {https://arxiv.org/abs/2506.00239}
}
```

And a link back to the original implementation: https://github.com/MIT-MI/SmellNet

---

## License

See the original SmellNet repo for dataset and upstream code licensing. Code authored in this repo is released under the same terms unless otherwise noted.
