# Data Pipeline

## Channel Layers

smell-pi touches **three distinct sensor-channel layouts** that must be reconciled. The docs, model contracts, and collection script each refer to one of these, so a reader needs the map up front.

| Layer | Sensor channels | Where it lives |
|---|---|---|
| **Raw collection (smell-pi)** | 14 | `collection/collect.py` output |
| **SmellNet paper format** | 12 | Upstream [Hugging Face dataset](https://huggingface.co/datasets/DeweiFeng/smell-net); expected by [`smellnet-autoresearch`](https://github.com/smartinelle/smellnet-autoresearch) training code |
| **Exported model input** | 6 | `artifacts/smellnet_base_phase2_exact_upstream/` (see [`exported_artifacts.md`](exported_artifacts.md)) |

### Raw collection (14 channels)

`collect.py` writes these columns (plus `timestamp_ms`):

```
NO2, C2H5OH, VOC, CO,
Temperature, Pressure, Humidity, Gas_Resistance, Altitude,
MQ3, MQ5, MQ9, HCHO, AirQuality
```

- **NO2, C2H5OH, VOC, CO** — raw integer readings from the Seeed Multichannel Gas V2 over I2C.
- **Temperature, Pressure, Humidity, Gas_Resistance, Altitude** — BME680 over I2C.
- **MQ3, MQ5, MQ9, HCHO, AirQuality** — **raw ADS1115 voltages**, not PPM. Conversion to calibrated concentrations is a downstream step and requires per-sensor R0 calibration (see [`hardware.md`](hardware.md)).

### SmellNet paper format (12 channels)

The original dataset and all training code use:

```
NO2, C2H5OH, VOC, CO, Alcohol, LPG, Benzene,
Temperature, Pressure, Humidity, Gas_Resistance, Altitude
```

Here `Alcohol`, `LPG`, and `Benzene` are **PPM concentrations** derived from the MQ sensors on the original ESP32 rig. smell-pi does **not** currently produce these columns — there is no raw-voltage → PPM conversion committed in this repo, so locally collected CSVs can't be dropped directly into the paper-compatible training pipeline without that bridge.

### Exported model input (6 channels)

The checkpoint in `artifacts/smellnet_base_phase2_exact_upstream/` uses only `NO2, C2H5OH, VOC, CO, Alcohol, LPG`, dropping `Benzene` and all BME680 channels. See [`exported_artifacts.md`](exported_artifacts.md) for the full contract.

---

## SmellNet 12-channel Raw Data Format

The rest of this document describes the SmellNet 12-channel format — the preprocessing steps below all operate on that layer, not on smell-pi's 14-channel raw CSVs.

```
timestamp, NO2, C2H5OH, VOC, CO, Alcohol, LPG, Benzene,
Temperature, Pressure, Humidity, Gas_Resistance, Altitude
```

- **timestamp**: milliseconds since recording start
- **NO2, C2H5OH, VOC, CO**: raw ADC counts from Seeed Multichannel Gas V2
- **Alcohol, LPG, Benzene**: PPM concentrations derived from the MQ sensors (conversion is applied upstream of this pipeline)
- **Temperature** (°C), **Pressure** (hPa), **Humidity** (%RH), **Gas_Resistance** (kΩ), **Altitude** (m): from BME680

File naming convention (matches SmellNet):
```
data/
  training/
    cinnamon/
      cinnamon_001.csv
      cinnamon_002.csv
      ...
  testing/
    cinnamon/
      cinnamon_test_001.csv
```

---

## Preprocessing Steps

These match the original SmellNet pipeline.

### Step 1: Baseline Subtraction

Subtract the first row of each recording from all rows. This removes sensor offset drift and anchors each session to zero.

```python
df = df - df.iloc[0]
```

### Step 2: First-Order Temporal Difference (FOTD)

Compute a temporal diff over a lag of 25 samples (= 12.5 seconds at 2 Hz). This emphasizes rate-of-change rather than absolute values, making the signal more robust to slow drift.

```python
df = df.diff(periods=25).iloc[25:]  # drop the first 25 NaN rows
```

### Step 3: Sliding Window

Slice each preprocessed time series into overlapping windows:

| Parameter | Default | Notes |
|---|---|---|
| `window_size` | 100 samples | = 50 seconds at 2 Hz |
| `stride` | 50 samples | = 25 seconds overlap |

Each window becomes one training example of shape `[window_size, 12]` = `[100, 12]`.

### Step 4: StandardScaler Normalization

Fit a `sklearn.preprocessing.StandardScaler` on training windows, apply to test windows. The scaler operates per-feature across the time dimension.

---

## Data Augmentation

The original repo also uses:

- **Random feature dropout** (`dropout_fraction=0.25`): zeros out 25% of randomly chosen sensor channels per sample. Improves robustness to sensor failures.
- **FFT high-frequency noise removal** (optional): zeroes high-frequency components via `rfft`.

---

## Dataset Splits

SmellNet uses:
- `offline_training/` — main training set (same substances, different recording sessions)
- `offline_testing/` — held-out test set (same substances)
- `online_nuts/`, `online_spices/` — real-time "online" test recordings

For smell-pi: replicate the same split structure. Within a substance, the first N recordings go to training, remainder to testing.

---

## Data Collection Script (planned)

The `collection/` directory will contain a Python script that:

1. Initialises I2C devices (BME680, ADS1115, Seeed Gas V2).
2. Waits for a trigger (GPIO button or Enter key).
3. Collects 12-channel data at 2 Hz for a configurable duration (default: 5 minutes).
4. Writes timestamped CSV to `data/{split}/{substance}/`.
5. Optionally plots a live preview.

---

## Notes on RPi vs. ESP32 Differences

- The ADS1115 at 3.3V with ±4.096V PGA maps MQ analog output to different raw counts than the ESP32 12-bit ADC at 3.3V. The PPM conversion formula (using `RatioMQxCleanAir` and `R0`) is the same, but R0 must be re-calibrated.
- BME680 readings are identical — same I2C protocol, same oversampling config.
- Seeed Gas V2 readings are identical — same I2C protocol.
- Sampling jitter: Python's `time.sleep` is less precise than Arduino's `delay`. Use `time.perf_counter` or a hardware timer interrupt for tighter 2 Hz control.
