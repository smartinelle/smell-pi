# Hardware Setup

## Original SmellNet Hardware

The paper used an **Adafruit ESP32 Feather** running Arduino firmware. The sensor suite is:

| Sensor | Measured channels | Interface |
|---|---|---|
| Seeed Grove Multichannel Gas Sensor V2 | NO2, C2H5OH, VOC, CO | I2C |
| MQ-135 | Alcohol / CO2 | Analog |
| MQ-9 | LPG | Analog |
| MQ-3 | Benzene / Alcohol | Analog |
| Adafruit BME680 | Temperature, Pressure, Humidity, Gas Resistance | I2C |

**Sampling rate**: 2 Hz  
**Collection trigger**: button press on the Feather

The 12 CSV columns produced are:
```
timestamp, NO2, C2H5OH, VOC, CO, Alcohol, LPG, Benzene,
Temperature, Pressure, Humidity, Gas_Resistance, Altitude
```
(HCHO sensor was present in hardware but disabled due to unreliable readings.)

---

## RPi Adaptation

The Raspberry Pi has no built-in ADC, so MQ analog sensors need an external ADC. All I2C sensors connect directly.

### Bill of Materials

| Component | Purpose | Notes |
|---|---|---|
| Raspberry Pi 4 (or 3B+) | Host / compute | 2GB+ recommended |
| Seeed Grove Multichannel Gas Sensor V2 | NO2, C2H5OH, VOC, CO | I2C, 3.3V–5V |
| Adafruit BME680 breakout | Temp, Pressure, Humidity, Gas R | I2C (0x76 or 0x77) |
| MQ-3 module | Benzene / Alcohol | Analog — via ADS1115 |
| MQ-9 module | LPG | Analog — via ADS1115 |
| MQ-135 module | Alcohol / CO2 | Analog — via ADS1115 |
| ADS1115 breakout (Adafruit or similar) | 16-bit 4-ch ADC | I2C (0x48) |
| 5V power supply / breadboard | Power + wiring | MQ sensors need 5V heater |

### I2C Address Map

| Device | Default I2C Address |
|---|---|
| Seeed Multichannel Gas V2 | 0x08 |
| Adafruit BME680 | 0x76 (SDO low) |
| ADS1115 | 0x48 (ADDR → GND) |

> All three can coexist on the same I2C bus (RPi pins 3/SDA, 5/SCL).

### MQ Sensor Wiring (via ADS1115)

```
MQ-3  AOUT → ADS1115 A0
MQ-9  AOUT → ADS1115 A1
MQ-135 AOUT → ADS1115 A2
(A3 spare)

MQ VCC → 5V rail
MQ GND → GND
ADS1115 VDD → 3.3V
ADS1115 SDA/SCL → RPi GPIO 2/3
```

### Calibration

MQ sensors require warm-up (~30 min first use, ~5 min thereafter) and calibration of R0 in clean air. The original firmware used:

| Sensor | RatioInCleanAir | Calibrated R0 |
|---|---|---|
| MQ-135 | 3.6 | 14.29 |
| MQ-9 | 9.6 | 2.96 |
| MQ-3 | 60 | 0.04 |

These values will need to be re-calibrated for our specific units and environment.

### BME680 Configuration

Matches original Arduino setup:
- Temperature oversampling: 8×
- Humidity oversampling: 2×
- Pressure oversampling: 4×
- IIR filter size: 3
- Gas heater: 320°C for 150 ms

### Python Libraries Needed

```
adafruit-circuitpython-bme680
adafruit-circuitpython-ads1x15
smbus2                          # for Seeed Multichannel Gas V2
RPi.GPIO
```

---

## Differences from Original

1. **No Arduino needed** — collection script is pure Python.
2. **ADS1115 for analog channels** — the ESP32's built-in 12-bit ADC is replaced by the ADS1115's 16-bit ADC (actually better resolution).
3. **Button trigger** — can be replicated with a GPIO button, or replaced by a keyboard/CLI trigger.
4. **Voltage reference** — ADS1115 operates at 3.3V logic; MQ sensors output 0–5V so ensure the voltage divider / ADS1115 input range is set correctly (use ±4.096V PGA setting).
