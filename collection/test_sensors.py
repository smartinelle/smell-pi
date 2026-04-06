#!/usr/bin/env python3
"""
Run after connecting each sensor to verify it's working.
Usage:
    python collection/test_sensors.py           # test everything found
    python collection/test_sensors.py bme680    # test one sensor by name
    python collection/test_sensors.py i2c       # just scan the bus
"""

import sys
import time
import smbus2
import board
import busio

# ── helpers ────────────────────────────────────────────────────────────────

def scan_i2c():
    bus = smbus2.SMBus(1)
    found = []
    for addr in range(0x03, 0x78):
        try:
            bus.read_byte(addr)
            found.append(addr)
        except OSError:
            pass
    bus.close()
    return found

def print_i2c():
    found = scan_i2c()
    known = {0x08: "Seeed Gas V2", 0x48: "ADS1115 #1", 0x49: "ADS1115 #2", 0x76: "BME680 (0x76)", 0x77: "BME680 (0x77)"}
    print("\n── I2C bus scan ──────────────────────────────")
    if not found:
        print("  No devices found. Check wiring and that I2C is enabled.")
    for addr in found:
        label = known.get(addr, "unknown")
        print(f"  0x{addr:02X}  {label}")
    print()
    return found

# ── sensor tests ───────────────────────────────────────────────────────────

def test_bme680():
    print("── BME680 ────────────────────────────────────")
    try:
        import adafruit_bme680
        i2c = busio.I2C(board.SCL, board.SDA)
        bme = adafruit_bme680.Adafruit_BME680_I2C(i2c, address=0x76)
        bme.sea_level_pressure = 1017
        bme.temperature_oversample  = 8
        bme.humidity_oversample     = 2
        bme.pressure_oversample     = 4
        bme.filter_size             = 3
        bme.gas_heater_temperature  = 320
        bme.gas_heater_duration     = 150
        time.sleep(1)
        print(f"  Temperature   : {bme.temperature:.2f} °C")
        print(f"  Pressure      : {bme.pressure:.2f} hPa")
        print(f"  Humidity      : {bme.humidity:.2f} %")
        print(f"  Gas resistance: {bme.gas:.0f} Ω")
        print(f"  Altitude      : {bme.altitude:.2f} m")
        print("  ✓ BME680 OK")
    except Exception as e:
        print(f"  ✗ BME680 FAILED: {e}")
    print()

def test_ads1115():
    print("── ADS1115 (both boards) ─────────────────────")
    try:
        import adafruit_ads1x15.ads1115 as ADS
        from adafruit_ads1x15.analog_in import AnalogIn
        i2c = busio.I2C(board.SCL, board.SDA)
        channels = [
            (0x48, 0, "MQ-3    (ADS#1 A0)"),
            (0x48, 1, "MQ-5    (ADS#1 A1)"),
            (0x48, 2, "MQ-9    (ADS#1 A2)"),
            (0x48, 3, "AirQual (ADS#1 A3)"),
            (0x49, 0, "HCHO    (ADS#2 A0)"),
        ]
        for addr, ch, label in channels:
            try:
                ads = ADS.ADS1115(i2c, address=addr)
                ads.gain = 1          # ±4.096V range
                ain = AnalogIn(ads, ch)
                v = ain.voltage
                print(f"  {label}: {v:.4f} V")
            except Exception as e:
                print(f"  {label}: ✗ {e}")
        print("  ✓ ADS1115 read complete")
    except Exception as e:
        print(f"  ✗ ADS1115 FAILED: {e}")
    print()

def test_gas_v2():
    print("── Seeed Multichannel Gas V2 ─────────────────")
    ADDR = 0x08
    CMD_NO2    = 0x01
    CMD_C2H5OH = 0x02
    CMD_VOC    = 0x03
    CMD_CO     = 0x04
    try:
        bus = smbus2.SMBus(1)
        def read_channel(cmd):
            bus.write_byte(ADDR, cmd)
            time.sleep(0.05)
            data = bus.read_i2c_block_data(ADDR, cmd, 4)
            raw = data[0] | (data[1] << 8) | (data[2] << 16) | (data[3] << 24)
            return raw
        print(f"  NO2   : {read_channel(CMD_NO2)}")
        print(f"  C2H5OH: {read_channel(CMD_C2H5OH)}")
        print(f"  VOC   : {read_channel(CMD_VOC)}")
        print(f"  CO    : {read_channel(CMD_CO)}")
        bus.close()
        print("  ✓ Gas V2 OK")
    except Exception as e:
        print(f"  ✗ Gas V2 FAILED: {e}")
    print()

# ── main ───────────────────────────────────────────────────────────────────

def main():
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "all"

    found = print_i2c()

    if arg in ("i2c", "scan"):
        return

    run_all = arg == "all"

    if run_all or arg == "bme680":
        if 0x76 in found or 0x77 in found:
            test_bme680()
        else:
            print("── BME680 ── not detected on I2C bus, skipping\n")

    if run_all or arg == "ads" or arg == "ads1115":
        if 0x48 in found or 0x49 in found:
            test_ads1115()
        else:
            print("── ADS1115 ── not detected on I2C bus, skipping\n")

    if run_all or arg == "gasv2" or arg == "gas":
        if 0x08 in found:
            test_gas_v2()
        else:
            print("── Seeed Gas V2 ── not detected on I2C bus, skipping\n")

if __name__ == "__main__":
    main()
