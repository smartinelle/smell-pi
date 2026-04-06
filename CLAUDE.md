# smell-pi — Claude Code Context

## Project Goal

Replicate the SmellNet paper ("SMELLNET: A Large-scale Dataset for Real-world Smell Recognition", Feng et al., 2025) on a Raspberry Pi. The original study used an Adafruit ESP32 Feather + Arduino for data collection; here we adapt everything to run natively in Python on the Pi.

**Paper**: https://arxiv.org/abs/2506.00239  
**Original repo**: https://github.com/smartinelle/SmellNet

## Three-phase Plan

1. **Data collection** — wire the same sensors to the RPi, write a Python data-collection script that produces CSV files in the same format as SmellNet.
2. **Model training & evaluation** — implement ScentFormer (Transformer) + baselines (LSTM, CNN, MLP), train on locally collected data, compare accuracy against paper's 58.5% Top-1.
3. **Edge inference** — run the trained model on-device in real time; display results on a screen or app.

## Directory Layout (intended)

```
smell-pi/
├── CLAUDE.md               # this file
├── docs/                   # project documentation
│   ├── overview.md
│   ├── hardware.md
│   ├── data_pipeline.md
│   └── models.md
├── data/                   # raw CSV recordings (one folder per substance)
│   ├── training/
│   └── testing/
├── collection/             # RPi data collection scripts
├── src/                    # model code (dataset, training, evaluation)
│   ├── models.py
│   ├── dataset.py
│   ├── train.py
│   └── evaluate.py
├── notebooks/              # exploration and analysis
└── inference/              # edge inference / display code
```

## Key Technical Facts

- **Sensors**: Seeed Grove Multichannel Gas V2 (I2C), MQ-3, MQ-9, MQ-135 (analog via ADS1115 ADC), Adafruit BME680 (I2C). See `docs/hardware.md`.
- **Data format**: CSV, 12 channels, 2 Hz. See `docs/data_pipeline.md`.
- **Preprocessing**: baseline subtraction (subtract first row) + first-order temporal diff (`df.diff(periods=25)`) + sliding window (default 100 samples, stride 50).
- **Primary model**: ScentFormer — a 4-layer, 8-head Transformer encoder with sinusoidal positional encoding and mean pooling. See `docs/models.md`.
- **RPi-specific constraint**: no built-in ADC → need ADS1115 (or similar) for MQ sensors.

## Working Conventions

- Data files: `data/{split}/{substance_name}/{recording_N}.csv`
- Model checkpoints: `src/saved_models/`
- Keep data collection scripts decoupled from model code.
- Target PyTorch for all models (matches original repo).
- Prefer `requirements.txt` for dependencies; keep Pi-compatible package versions.
