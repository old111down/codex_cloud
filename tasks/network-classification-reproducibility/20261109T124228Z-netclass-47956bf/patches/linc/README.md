# LINC isolated audit patches

Base: `haolinyan/LINC main@4a44171c84547de885a54e5f1a234640cd8501d4`. Original checkout remains pristine. These three patches were applied, in order, only under `papers/linc/runtime-artifacts/patched/`; each `git apply --check` and actual application has original logs in `logs/linc/patch{1,2,3}_{check,apply}.*`.

| Patch | Category | Reason and equivalence |
| --- | --- | --- |
| `0001-small-batch-progress.patch` | Runtime error repair | `_train_epoch` computes `num_batch //10` as a logging modulus; fewer than10 batches raises ZeroDivisionError after the first optimizer step. Guarding the log interval changes logging only, not the optimizer/loss. Original small-input failure retained. |
| `0002-cpu-export-simulator.patch` | Environment compatibility | Preserve model device for NumPy→Torch export tensors and add CPU fallback to the Python rule simulator. It does not port the full `update_streaming.py` CUDA path, reproduce GPU timing or implement P4 simulation. Numerical device equivalence on original data remains Unknown. |
| `0003-default-subspace-index.patch` | Algorithm logic modification | `Switch.scores` has shape(1,N), so `len(self.scores)` is1. Unmatched samples were assigned to rule1 instead of reserved default bucketN, affecting cached subspace allocations. Use `self.num_keys`. Eight synthetic3-bit inputs with3 rules demonstrate five incorrect allocations before patch, zero after. Predicted default class stayed0, so no accuracy drop on paper data is inferred. After this local fix, `update_streaming.py:179` still indexes `values[N]` for unmatched new-class samples; an independent original-expression probe confirms IndexError. Full update repair is not claimed. |

Environment changes are separate: inactive unavailable `swanlab==0.3.16` omitted, official PyTorch CPU build selected, NumPy2.0.1→1.26.4 after an observed bridge failure. See `environment/linc/README.md`. The original requirements are preserved. Patched synthetic training/export succeeds but is neither an original-code success nor a network-classification metric reproduction.
