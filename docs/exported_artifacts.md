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
