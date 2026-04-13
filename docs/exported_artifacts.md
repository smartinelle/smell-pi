# Exported SmellNet Artifacts

## Current best edge-ready checkpoint

Exported artifact directory:

- `artifacts/smellnet_base_phase2_exact_upstream/`

Contents:

- `checkpoint.pt`
- `labels.json`
- `preprocessing.json`
- `training_metrics.json`
- `final_test_metrics.json`

This bundle comes from the best local benchmark-faithful supervised run currently tracked in the source `SmellNet` repo.

Held-out test metrics:

- Top-1: `57.97`
- Top-5: `88.05`

## Input contract

This checkpoint expects the exact-upstream 6-channel sensor subset, in this order:

1. `NO2`
2. `C2H5OH`
3. `VOC`
4. `CO`
5. `Alcohol`
6. `LPG`

The full raw 12-channel order is:

1. `NO2`
2. `C2H5OH`
3. `VOC`
4. `CO`
5. `Alcohol`
6. `LPG`
7. `Benzene`
8. `Temperature`
9. `Pressure`
10. `Humidity`
11. `Gas_Resistance`
12. `Altitude`

Dropped channels for this exported model:

- `Benzene`
- `Temperature`
- `Pressure`
- `Humidity`
- `Gas_Resistance`
- `Altitude`

## Preprocessing contract

Use the exact preprocessing in `artifacts/smellnet_base_phase2_exact_upstream/preprocessing.json`.

In short:

- subtract the first row of each recording
- keep the 6 channels above in that order
- apply `diff(periods=25)`
- build windows of length `100`
- use stride `50`
- standardize with the saved `scaler_mean` and `scaler_scale`

The saved label order is in `labels.json`.

## Model config

The exported model is a transformer classifier with:

- `input_dim = 6`
- `model_dim = 512`
- `num_heads = 8`
- `num_layers = 6`
- `dropout = 0.05`

## Deployment note

This is the best straightforward edge inference target right now because it is a standard classifier checkpoint.

The current contrastive checkpoints are smaller, but they require a GC-MS embedding bank and retrieval logic, so they are not the simplest first deployment path on the Pi.

---

## Compatibility with smell-pi raw collections

`collection/collect.py` writes **14 raw sensor channels**, not the SmellNet 12-channel paper format and not the 6-channel subset this checkpoint expects. See [`data_pipeline.md`](data_pipeline.md#channel-layers) for the full three-layer map.

To feed a locally collected CSV into this checkpoint, the following bridge is needed (and is not yet implemented in this repo):

1. **Voltage → PPM conversion**: turn the raw `MQ3` / `MQ5` / `MQ9` voltages from `collect.py` into the `Alcohol` and `LPG` PPM channels the model expects. This requires per-sensor R0 calibration — see [`hardware.md`](hardware.md). The mapping from "which MQ produces which named channel" has to match the upstream SmellNet convention, not just any plausible assignment.
2. **Drop unused channels**: `Benzene`, BME680 (`Temperature`, `Pressure`, `Humidity`, `Gas_Resistance`, `Altitude`), plus the `HCHO` and `AirQuality` columns smell-pi records but the paper doesn't.
3. **Reorder** the remaining columns to `[NO2, C2H5OH, VOC, CO, Alcohol, LPG]`.
4. **Apply** the FOTD / windowing / scaling pipeline above, using the `scaler_mean` and `scaler_scale` from `preprocessing.json`.

Until that bridge exists, the exported checkpoint can only be run on CSVs already in the SmellNet 12-channel format (i.e. from the upstream Hugging Face dataset), not on freshly collected smell-pi recordings.
