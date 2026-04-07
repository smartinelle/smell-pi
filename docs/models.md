# Models

See also: `docs/exported_artifacts.md` for the currently exported edge-ready checkpoint bundle and its exact preprocessing contract.

All models are PyTorch. The primary model to replicate is ScentFormer. LSTM, CNN, and MLP are baselines.

Input shape for all sequential models: `(batch, T, 12)` — `T` time steps, 12 sensor channels.

---

## ScentFormer (Transformer)

The main model from the paper. A standard Transformer encoder with:

- **Input projection**: `Linear(12, model_dim)` + `LayerNorm`
- **Positional encoding**: sinusoidal, max_len=10000
- **Encoder**: 4 layers, 8 heads, `dim_feedforward = 4 × model_dim`, GELU activation, **pre-norm** (`norm_first=True`)
- **Pooling**: mean over time dimension (masked if sequences are padded)
- **Classifier head**: `Linear(D, D//2)` → `GELU` → `Dropout` → `Linear(D//2, num_classes)`

```python
Transformer(
    input_dim=12,
    model_dim=128,       # to confirm from run configs
    num_classes=50,      # 50 substances in SmellNet-Base
    num_heads=8,
    num_layers=4,
    dropout=0.1,
    activation="gelu",
    use_positional_encoding=True,
    pool="mean",
)
```

**Performance**: 58.5% Top-1 accuracy on SmellNet-Base (50-class, offline test set).

---

## LSTMNet

Bidirectional LSTM with mean pooling:

```python
LSTMNet(
    input_dim=12,
    hidden_dim=128,
    embedding_dim=64,
    num_classes=50,
    num_layers=1,
    bidirectional=True,
    dropout=0.1,
    pool="mean",
)
```

Architecture:
- `nn.LSTM` (bidirectional) → output `(B, T, 2*hidden_dim)`
- Mean pool over T → `(B, 2*hidden_dim)`
- `Linear(2*hidden_dim, embedding_dim)` → `(B, embedding_dim)`
- `Linear(embedding_dim, num_classes)` → logits

---

## CNN1DClassifier

1D convolutional network with global average pooling:

```python
CNN1DClassifier(
    in_channels=12,
    num_classes=50,
    channels=(64, 128, 256),
    kernel_size=5,
    dropout=0.2,
)
```

Architecture:
- 3× `[Conv1d → BatchNorm → ReLU → Dropout]` blocks
- Global average pooling → `(B, 256)`
- `Linear(256, num_classes)` → logits

Works with variable window sizes (no fixed flattening).

---

## MLPClassifier

Baseline: mean-pool over time, then feed-forward network:

```python
MLPClassifier(
    in_features=12,
    num_classes=50,
    hidden_sizes=(256, 256),
    dropout=0.2,
    pool="mean",
)
```

Architecture:
- Mean pool `(B, T, 12)` → `(B, 12)`
- 2× `[Linear → BatchNorm → ReLU → Dropout]`
- `Linear(256, num_classes)` → logits

---

## Training Configuration

From the original repo (`run_experiments.sh` / `main.py`):

| Hyperparameter | Value |
|---|---|
| Window sizes tried | 50, 100, 500 samples |
| Stride | 50% of window |
| Batch size | ~64 (inferred) |
| Optimizer | AdamW |
| Loss | CrossEntropyLoss |
| Preprocessing | FOTD (diff period=25) + StandardScaler |
| Augmentation | Random feature dropout (25%) |

---

## Edge Inference (Phase 3)

For on-device inference on the RPi:

1. **TorchScript** (`torch.jit.script`) — easiest path, no extra dependencies.
2. **ONNX export** — enables ONNX Runtime for potentially faster CPU inference.
3. **Quantization** — `torch.quantization.quantize_dynamic` can halve model size and improve CPU throughput.

ScentFormer with `model_dim=128`, 4 layers is small enough to run comfortably on an RPi 4 for single-sample inference (sub-second latency expected).

---

## Contrastive / Multimodal Extensions (future)

The original repo also has paired training between sensor embeddings and:
- GC-MS chemical composition vectors (from `GCMSMLPEncoder`)
- CLIP text embeddings (from `clip_text_embeddings.npy`)

These are not the primary target for smell-pi but could be added in a later phase to explore cross-modal smell retrieval.
