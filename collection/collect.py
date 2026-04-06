#!/usr/bin/env python3
"""
Collect a timed sensor recording and save to data/{split}/{substance}/{substance}_NNN.csv

Usage:
    python collection/collect.py cinnamon
    python collection/collect.py cinnamon --split testing --duration 120
    python collection/collect.py cinnamon --duration 300   # 5 minutes

Columns: timestamp_ms, NO2, C2H5OH, VOC, CO,
         Temperature, Pressure, Humidity, Gas_Resistance, Altitude,
         MQ3, MQ5, MQ9, HCHO, AirQuality

Sampling rate: 2 Hz (configurable via --hz)
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import smbus2
import board
import busio
import adafruit_bme680
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# ── sensor setup ───────────────────────────────────────────────────────────

def init_sensors():
    i2c = busio.I2C(board.SCL, board.SDA)

    # BME680
    bme = adafruit_bme680.Adafruit_BME680_I2C(i2c, address=0x76)
    bme.sea_level_pressure  = 1017.0
    bme.temperature_oversample = 8
    bme.humidity_oversample    = 2
    bme.pressure_oversample    = 4
    bme.filter_size            = 3
    bme.gas_heater_temperature = 320
    bme.gas_heater_duration    = 150

    # ADS1115 boards
    ads1 = ADS.ADS1115(i2c, address=0x48)
    ads1.gain = 1   # ±4.096V — covers 0–3.33V after voltage divider
    ads2 = ADS.ADS1115(i2c, address=0x49)
    ads2.gain = 1

    # Analog channels
    mq3      = AnalogIn(ads1, 0)
    mq5      = AnalogIn(ads1, 1)
    mq9      = AnalogIn(ads1, 2)
    hcho     = AnalogIn(ads1, 3)
    air_qual = AnalogIn(ads2, 0)

    # Seeed Gas V2 via smbus2
    bus = smbus2.SMBus(1)

    return bme, mq3, mq5, mq9, hcho, air_qual, bus


GAS_V2_ADDR    = 0x08
CMD_NO2        = 0x01
CMD_C2H5OH     = 0x02
CMD_VOC        = 0x03
CMD_CO         = 0x04

def read_gas_v2(bus, cmd):
    bus.write_byte(GAS_V2_ADDR, cmd)
    time.sleep(0.02)
    data = bus.read_i2c_block_data(GAS_V2_ADDR, cmd, 4)
    return data[0] | (data[1] << 8) | (data[2] << 16) | (data[3] << 24)


def read_all(bme, mq3, mq5, mq9, hcho, air_qual, bus, t0_ms):
    ts = int((time.perf_counter() * 1000) - t0_ms)
    no2    = read_gas_v2(bus, CMD_NO2)
    c2h5oh = read_gas_v2(bus, CMD_C2H5OH)
    voc    = read_gas_v2(bus, CMD_VOC)
    co     = read_gas_v2(bus, CMD_CO)
    return {
        "timestamp_ms":   ts,
        "NO2":            no2,
        "C2H5OH":         c2h5oh,
        "VOC":            voc,
        "CO":             co,
        "Temperature":    round(bme.temperature, 3),
        "Pressure":       round(bme.pressure, 3),
        "Humidity":       round(bme.humidity, 3),
        "Gas_Resistance": round(bme.gas / 1000.0, 3),  # Ω → kΩ
        "Altitude":       round(bme.altitude, 3),
        "MQ3":            round(mq3.voltage, 4),
        "MQ5":            round(mq5.voltage, 4),
        "MQ9":            round(mq9.voltage, 4),
        "HCHO":           round(hcho.voltage, 4),
        "AirQuality":     round(air_qual.voltage, 4),
    }


# ── file handling ──────────────────────────────────────────────────────────

COLUMNS = [
    "timestamp_ms", "NO2", "C2H5OH", "VOC", "CO",
    "Temperature", "Pressure", "Humidity", "Gas_Resistance", "Altitude",
    "MQ3", "MQ5", "MQ9", "HCHO", "AirQuality",
]

def next_csv_path(substance: str, split: str) -> Path:
    folder = Path("data") / split / substance
    folder.mkdir(parents=True, exist_ok=True)
    existing = sorted(folder.glob(f"{substance}_*.csv"))
    n = len(existing) + 1
    return folder / f"{substance}_{n:03d}.csv"


# ── main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Record sensor data for one substance.")
    parser.add_argument("substance", help="Name of the substance being tested (e.g. cinnamon)")
    parser.add_argument("--split", default="training", choices=["training", "testing"],
                        help="Data split folder (default: training)")
    parser.add_argument("--duration", type=int, default=300,
                        help="Recording duration in seconds (default: 300 = 5 min)")
    parser.add_argument("--hz", type=float, default=2.0,
                        help="Sampling rate in Hz (default: 2)")
    parser.add_argument("--warmup", type=int, default=30,
                        help="Sensor warm-up wait in seconds (default: 30)")
    args = parser.parse_args()

    out_path = next_csv_path(args.substance, args.split)
    period   = 1.0 / args.hz
    n_samples = int(args.duration * args.hz)

    print(f"\n  Substance : {args.substance}")
    print(f"  Split     : {args.split}")
    print(f"  Output    : {out_path}")
    print(f"  Duration  : {args.duration}s  ({n_samples} samples @ {args.hz} Hz)")
    print(f"\n  Initialising sensors...")

    try:
        bme, mq3, mq5, mq9, hcho, air_qual, bus = init_sensors()
    except Exception as e:
        print(f"\n  ERROR initialising sensors: {e}")
        print("  Run:  python collection/test_sensors.py   to diagnose")
        sys.exit(1)

    print(f"  Warming up for {args.warmup}s — do not expose sensor to the substance yet.")
    for i in range(args.warmup, 0, -1):
        print(f"    {i}s...", end="\r", flush=True)
        time.sleep(1)

    print(f"\n  Recording — place the substance near the sensors now.")
    print(f"  Press Ctrl+C to stop early.\n")

    t0_ms   = time.perf_counter() * 1000
    written = 0

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()

        try:
            for i in range(n_samples):
                loop_start = time.perf_counter()

                row = read_all(bme, mq3, mq5, mq9, hcho, air_qual, bus, t0_ms)
                writer.writerow(row)
                f.flush()
                written += 1

                elapsed = int(row["timestamp_ms"] / 1000)
                print(
                    f"  [{elapsed:4d}s/{args.duration}s] "
                    f"T={row['Temperature']:.1f}°C  "
                    f"H={row['Humidity']:.1f}%  "
                    f"MQ3={row['MQ3']:.3f}V  "
                    f"MQ5={row['MQ5']:.3f}V  "
                    f"MQ9={row['MQ9']:.3f}V  "
                    f"NO2={row['NO2']}  "
                    f"CO={row['CO']}",
                    end="\r",
                )

                sleep_for = period - (time.perf_counter() - loop_start)
                if sleep_for > 0:
                    time.sleep(sleep_for)

        except KeyboardInterrupt:
            print(f"\n\n  Stopped early.")

    bus.close()
    print(f"\n  Saved {written} rows → {out_path}\n")


if __name__ == "__main__":
    main()
