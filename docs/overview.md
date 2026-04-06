# Project Overview

## What is SmellNet?

SmellNet (Feng et al., 2025) is the first large-scale open-source dataset for real-world smell recognition using portable gas and chemical sensors. It contains:

- ~828,000 data points / 68 hours of sensor recordings
- 50 individual substances (nuts, spices, herbs, fruits, vegetables) + 43 mixture combinations
- 12 sensor channels sampled at 2 Hz
- Paired GC-MS chemical composition data and CLIP text embeddings

The core ML contribution is **ScentFormer**, a Transformer-based classifier that achieves **58.5% Top-1 accuracy** on the 50-class single-substance recognition task.

**Paper**: https://arxiv.org/abs/2506.00239  
**Original repo**: https://github.com/smartinelle/SmellNet  
**Dataset**: hosted on Hugging Face

---

## This Repo: smell-pi

smell-pi is a replication and adaptation of SmellNet designed to run end-to-end on a Raspberry Pi. The goals differ slightly from the original:

| Dimension | SmellNet (original) | smell-pi |
|---|---|---|
| Collection hardware | Adafruit ESP32 Feather + Arduino | Raspberry Pi (direct Python) |
| ADC for analog sensors | Built-in ESP32 ADC (12-bit) | ADS1115 external ADC via I2C |
| Data scale | 68 hours, 50 substances | Start small; grow incrementally |
| Training | Offline, GPU/CPU workstation | On-device or transferred to stronger machine |
| Inference | Not addressed | Edge inference on RPi in real time |

---

## Phase Plan

### Phase 1 — Data Collection
- Wire sensors to RPi GPIO/I2C bus
- Write a Python collection script producing the same 12-channel CSV format
- Collect baseline recordings for a small substance set (e.g., 5–10 spices/herbs)
- Validate signal quality against SmellNet sample data

### Phase 2 — Model Training & Evaluation
- Port or re-implement ScentFormer, LSTM, CNN, MLP baselines from the original repo
- Implement FOTD preprocessing and sliding-window dataset builder
- Train on locally collected data; log accuracy vs. paper benchmarks
- Optionally fine-tune on SmellNet public data for comparison

### Phase 3 — Edge Inference
- Export trained model (TorchScript or ONNX) for fast on-device inference
- Write a real-time inference loop that reads live sensor data and outputs predictions
- Display results on an attached screen or a companion app (TBD)

---

## Key Papers / References

- Feng et al. (2025), "SMELLNET" — primary reference
- Vaswani et al. (2017), "Attention Is All You Need" — Transformer backbone
- Adafruit BME680 datasheet — environmental sensor
- Seeed Multichannel Gas Sensor V2 datasheet — gas channels
