# Data Pipeline

## Raw Data Format

Each recording is a CSV file with 12 sensor channels sampled at **2 Hz**:

```
timestamp, NO2, C2H5OH, VOC, CO, Alcohol, LPG, Benzene,
Temperature, Pressure, Humidity, Gas_Resistance, Altitude
```

- **timestamp**: milliseconds since recording start
- **NO2, C2H5OH, VOC, CO**: raw ADC counts from Seeed Multichannel Gas V2
- **Alcohol, LPG, Benzene**: derived from the MQ-series analog sensors (MQ-3, MQ-5, MQ-9 read via ADS1115 in `collection/collect.py`; PPM conversion happens downstream from raw voltages)
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
