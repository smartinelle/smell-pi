# Wiring Reference

## Breadboard Basics (first-timer guide)

An 830-point breadboard has:
- **Two long power rails on each side** (the horizontal rows marked + and −)
- **Columns of 5 connected holes** in the main area (a–e and f–j, separated by the center gap)
- Rows are numbered 1–63; each row's a–e holes are connected together, and f–j are connected together

Rules that matter:
- **Jumper to the same row** = electrically connected
- **Jumper across the center gap** = NOT connected (use a wire to bridge)
- **Power rails run the full length** — use them for 3.3V, 5V, and GND buses

---

## RPi 4 GPIO Header (pin 1 is top-left, USB ports face down)

```
       3V3  (1) (2)  5V
   SDA/GP2  (3) (4)  5V
   SCL/GP3  (5) (6)  GND
       GP4  (7) (8)  GP14
       GND  (9) (10) GP15
      GP17 (11) (12) GP18
      GP27 (13) (14) GND
      GP22 (15) (16) GP23
       3V3 (17) (18) GP24
      GP10 (19) (20) GND
       GP9 (21) (22) GP25
      GP11 (23) (24) GP8
       GND (25) (26) GP7
      GP0* (27) (28) GP1*
       GP5 (29) (30) GND
       GP6 (31) (32) GP12
      GP13 (33) (34) GND
      GP19 (35) (36) GP16
      GP26 (37) (38) GP20
       GND (39) (40) GP21
```

**You only need to touch 5 pins today:**

| RPi pin | Label | Goes to |
|---------|-------|---------|
| 1 | 3.3V | 3.3V rail (I2C devices) |
| 2 | 5V | 5V rail (MQ sensor heaters) |
| 6 | GND | GND rail (all GNDs tie here) |
| 3 | SDA | SDA line (all I2C sensors) |
| 5 | SCL | SCL line (all I2C sensors) |

---

## Step A — Set Up Power Rails

**Goal**: two independent voltage buses, one shared ground.

```
Breadboard top-left (+) rail  ←── RPi pin 1  (3.3V)
Breadboard top-left (−) rail  ←── RPi pin 6  (GND)
Breadboard top-right (+) rail ←── RPi pin 2  (5V)
Breadboard top-right (−) rail ←── wire to top-left (−)  ← same GND
```

Use a short jumper to connect the two (−) rails together at one end so all GNDs are the same.

---

## Step B — ADS1115 #1 (address 0x48, I2C bus 1)

This ADC converts the analog MQ sensor voltages into I2C data the Pi can read.

| ADS1115 pin | Connect to |
|------------|-----------|
| VCC | 3.3V rail |
| GND | GND rail |
| SCL | RPi pin 5 (SCL, GPIO3) |
| SDA | RPi pin 3 (SDA, GPIO2) |
| A0 | MQ-3 (via voltage divider, see Step F) |
| A1 | MQ-5 (via voltage divider) |
| A2 | MQ-9 (via voltage divider) |
| A3 | Grove Air Quality signal |

**Verify**: `i2cdetect -y 1` should show `48` in the grid.

---

## Step C — ADS1115 #2 (address 0x48, I2C bus 3)

Both Soldered ADS1115 boards are hardwired to 0x48 with no ADDR pin exposed.
Solution: use a second hardware I2C bus (i2c-3) enabled via `/boot/firmware/config.txt`:

```
dtoverlay=i2c3    # SDA=GPIO4(pin7), SCL=GPIO5(pin29)
```

| ADS1115 pin | Connect to |
|------------|-----------|
| VCC | 3.3V rail |
| GND | GND rail |
| SCL | RPi pin 29 (GPIO5) |
| SDA | RPi pin 7  (GPIO4) |
| A0 | Grove HCHO signal |
| A1–A3 | spare |

**Verify**: `i2cdetect -y 3` should show `48`.

---

## Step D — BME680

I2C environmental sensor (temperature, pressure, humidity, gas resistance).

| BME680 pin | Connect to |
|-----------|-----------|
| VIN / VCC | 3.3V rail |
| GND | GND rail |
| SDA / SDI | RPi pin 3 (SDA) |
| SCL / SCK | RPi pin 5 (SCL) |
| SDO | GND rail → I2C address **0x76** |
| CS | leave unconnected (or 3.3V) |

**Verify**: `i2cdetect -y 1` should now show `76`.

---

## Step E — Seeed Grove Multichannel Gas Sensor V2

I2C sensor (NO2, C2H5OH/Ethanol, VOC, CO). Uses a Grove-to-female jumper cable.

Grove cable colors:
- **Red** → 3.3V rail
- **Black** → GND rail
- **White** → RPi pin 3 (SDA)
- **Yellow** → RPi pin 5 (SCL)

**Verify**: `i2cdetect -y 1` should now show `08`.

---

## Step F — Voltage Divider for MQ Sensors

The MQ sensors output 0–5V. The ADS1115 (powered at 3.3V) accepts max ~3.6V. Use a resistor divider to scale down.

```
MQ AOUT ──── R1 (10kΩ) ──────┬──── R2 (20kΩ) ──── GND
                              │
                         ADS1115 Ax
```

`Vout = 5V × 20 / (10+20) = 3.33V` → safe for 3.3V ADS1115.

**Build one divider per MQ sensor** (3 total). Use breadboard rows:
- R1 and R2 in series; the midpoint row connects to the ADS1115 input.

---

## Step G — MQ-3 (Benzene / Alcohol)

| MQ-3 pin | Connect to |
|---------|-----------|
| VCC (+) | 5V rail |
| GND (−) | GND rail |
| AOUT (A0) | voltage divider input |
| DOUT (D0) | leave unconnected |

Divider output → ADS1115 #1, pin **A0**.

---

## Step H — MQ-5 (LPG / Natural Gas / Methane)

| MQ-5 pin | Connect to |
|---------|-----------|
| VCC (+) | 5V rail |
| GND (−) | GND rail |
| AOUT (A0) | voltage divider input |
| DOUT (D0) | leave unconnected |

Divider output → ADS1115 #1, pin **A1**.

---

## Step I — MQ-9 (CO / LPG)

| MQ-9 pin | Connect to |
|---------|-----------|
| VCC (+) | 5V rail |
| GND (−) | GND rail |
| AOUT (A0) | voltage divider input |
| DOUT (D0) | leave unconnected |

Divider output → ADS1115 #1, pin **A2**.

---

## Step J — Seeed Grove Air Quality Sensor

Analog sensor (general air quality index). Powered at 3.3V.

Grove cable colors:
- **Red** → 3.3V rail
- **Black** → GND rail
- **White** → ADS1115 #1, pin **A3** (direct, no divider needed at 3.3V)
- **Yellow** → leave unconnected

---

## Step K — Seeed Grove HCHO Sensor

Analog sensor (formaldehyde). On ADS1115 #2 (I2C bus 3, pin 7/29).

Grove cable colors:
- **Red** → 3.3V rail
- **Black** → GND rail
- **White** → ADS1115 #2, pin **A0** (direct)
- **Yellow** → leave unconnected

---

## Final I2C Map

| Bus | Command | Address | Device |
|-----|---------|---------|--------|
| 1 | `i2cdetect -y 1` | 0x08 | Seeed Grove Multichannel Gas V2 |
| 1 | `i2cdetect -y 1` | 0x48 | ADS1115 #1 (MQ-3, MQ-5, MQ-9, Air Quality) |
| 1 | `i2cdetect -y 1` | 0x76 | BME680 |
| 3 | `i2cdetect -y 3` | 0x48 | ADS1115 #2 (HCHO) |

---

## Final Channel Map (15 channels total)

| Channel | Sensor | Measures | Source |
|---------|--------|----------|--------|
| NO2 | Gas V2 | Nitrogen dioxide | I2C bus 1, 0x08 |
| C2H5OH | Gas V2 | Ethanol | I2C bus 1, 0x08 |
| VOC | Gas V2 | Volatile organic compounds | I2C bus 1, 0x08 |
| CO | Gas V2 | Carbon monoxide | I2C bus 1, 0x08 |
| Temperature | BME680 | °C | I2C bus 1, 0x76 |
| Pressure | BME680 | hPa | I2C bus 1, 0x76 |
| Humidity | BME680 | %RH | I2C bus 1, 0x76 |
| Gas_Resistance | BME680 | kΩ (VOC proxy) | I2C bus 1, 0x76 |
| Altitude | BME680 | m | I2C bus 1, 0x76 |
| MQ3 | MQ-3 | Benzene / Alcohol | ADS1115 #1, A0 |
| MQ5 | MQ-5 | LPG / Natural Gas | ADS1115 #1, A1 |
| MQ9 | MQ-9 | CO / LPG | ADS1115 #1, A2 |
| AirQuality | Grove AQ | Air quality index | ADS1115 #1, A3 |
| HCHO | Grove HCHO | Formaldehyde | ADS1115 #2, A0 |

---

## Safety Notes

- Always power the Pi from its USB-C port; never supply more than 3.3V to I2C pins.
- MQ sensor heaters draw ~150mA each at 5V. With 3 sensors: ~450mA total. Use a ≥2.5A USB-C power supply.
- MQ sensors need a ~30 min warm-up on first use; ~5 min on subsequent uses before readings stabilize.
- Never connect MQ AOUT directly to the ADS1115 without the voltage divider.
