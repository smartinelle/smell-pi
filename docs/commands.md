# Quick Reference — Useful Commands

## I2C — what's connected

```bash
i2cdetect -y 1      # scan main bus (pins 3/5) — ADS1115, BME680, Gas V2
i2cdetect -y 3      # scan second bus (pins 7/29) — ADS1115 #2 (when working)
```

Expected addresses on bus 1:
- `0x08` — Seeed Gas V2
- `0x48` — ADS1115 #1
- `0x76` — BME680

## Sensor data — test each sensor

```bash
cd ~/smell-pi && source .venv/bin/activate

python collection/test_sensors.py           # test all detected sensors
python collection/test_sensors.py i2c       # I2C scan only
python collection/test_sensors.py bme680    # BME680 only
python collection/test_sensors.py ads       # ADS1115 + MQ sensors only
python collection/test_sensors.py gas       # Seeed Gas V2 only
```

## Data collection — record a substance

```bash
python collection/collect.py cinnamon                        # 5 min, training split
python collection/collect.py cinnamon --duration 120         # 2 min
python collection/collect.py cinnamon --split testing        # testing split
python collection/collect.py cinnamon --warmup 5             # short warmup (testing only)
```

Saves to: `data/{split}/{substance}/{substance}_NNN.csv`
