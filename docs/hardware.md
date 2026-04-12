# Hardware Setup

## Original SmellNet Hardware

The paper used an **Adafruit ESP32 Feather** running Arduino firmware, sampling at **2 Hz** via a button-press trigger on the Feather. Its sensor suite includes a Seeed Grove Multichannel Gas Sensor V2 for NO2/C2H5OH/VOC/CO, several MQ-series analog gas sensors, and an Adafruit BME680 for temperature/pressure/humidity/gas resistance. See [MIT-MI/SmellNet](https://github.com/MIT-MI/SmellNet) for the exact original BOM.

---

## smell-pi Hardware

smell-pi uses a Raspberry Pi instead of the ESP32. Since the RPi has no built-in ADC, analog MQ sensors are read through **two ADS1115** 16-bit ADC boards over I2C. All other sensors connect directly.

### Bill of Materials

| Component | Purpose | Notes |
|---|---|---|
| Raspberry Pi 4 (or 3B+) | Host / compute | 2 GB+ recommended |
| Seeed Grove Multichannel Gas Sensor V2 | NO2, C2H5OH, VOC, CO | I2C, 3.3V–5V |
| Adafruit BME680 breakout | Temp, Pressure, Humidity, Gas R, Altitude | I2C (0x76 or 0x77) |
| MQ-3 module | Alcohol / benzene | Analog — ADS1115 #1 A0 |
| MQ-5 module | LPG / natural gas / methane | Analog — ADS1115 #1 A1 |
| MQ-9 module | CO / flammable gases | Analog — ADS1115 #1 A2 |
| HCHO sensor (analog) | Formaldehyde | Analog — ADS1115 #1 A3 |
| Air Quality sensor (analog) | General VOC / air quality | Analog — ADS1115 #2 A0 |
| ADS1115 breakout ×2 | 16-bit 4-channel ADC | I2C (0x48, 0x49) |
| 5V power supply / breadboard | Power + wiring | MQ sensors need a 5V heater supply |

> The two ADS1115 boards are distinguished by their ADDR pin: `ADDR → GND` gives 0x48, `ADDR → VDD` gives 0x49. See `collection/collect.py` for the canonical pinout in code.

### I2C Address Map

| Device | Default I2C Address |
|---|---|
| Seeed Multichannel Gas V2 | 0x08 |
| Adafruit BME680 | 0x76 (SDO low) |
| ADS1115 #1 | 0x48 (ADDR → GND) |
| ADS1115 #2 | 0x49 (ADDR → VDD) |

> All four devices share the same I2C bus on RPi pins 3/SDA and 5/SCL.

### Analog Sensor Wiring

```
ADS1115 #1 (0x48)
  A0 ← MQ-3   AOUT
  A1 ← MQ-5   AOUT
  A2 ← MQ-9   AOUT
  A3 ← HCHO   AOUT

ADS1115 #2 (0x49)
  A0 ← Air Quality sensor AOUT
  A1 / A2 / A3 spare

MQ VCC → 5V rail
MQ GND → GND
ADS1115 VDD  → 3.3V
ADS1115 SDA  → RPi GPIO 2 (pin 3)
ADS1115 SCL  → RPi GPIO 3 (pin 5)
```

### Calibration

MQ sensors require warm-up (~30 min first use, ~5 min thereafter) and calibration of R0 in clean air. Each sensor module must be calibrated for the specific unit and environment — don't blindly copy R0 values from datasheets or other implementations. The collection script (`collection/collect.py`) writes raw voltages from the ADS1115 for `MQ3`, `MQ5`, `MQ9`, `HCHO`, and `AirQuality`; conversion to PPM happens downstream.

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
