---
name: pytorch-lightning-engineering
description: Engineering rules for PyTorch and Lightning training code (twiga's neural forecasters and the experiment repos). Use when writing or reviewing a LightningModule, optimiser, scheduler, callback, weight averaging, manual optimisation, loss or metric, or a model that must run on CPU, MPS and CUDA. It records the pitfalls that produced real bugs in twiga PRs 129 to 135.
---

# PyTorch and Lightning: the pitfalls that already cost a bug

Load [[coding-standards]] and [[python-performance]] first. Each rule below came from a defect found and fixed in twiga; each fix has a test that fails on the old code.

## Optimisation

1. **Manual optimisation does not step schedulers, clip or accumulate for you.** With `automatic_optimization = False`, Lightning never calls `scheduler.step()`; step the schedulers yourself in `on_train_epoch_end` (epoch-interval ones) or in the step (step-interval ones). The Trainer arguments `gradient_clip_val` and `accumulate_grad_batches` raise a configuration error with manual optimisation: clip inside the step. A plateau scheduler needs a metric that the model actually logs: choose from the names it logs, and skip with one warning if none exists.
2. **Step a scheduler only with its own optimiser.** In sequential two-stage training one optimiser is idle in each stage: stepping its scheduler spends its schedule in the wrong stage. Compare `scheduler.optimizer` with the active optimiser.
3. **A closure optimiser needs a closure.** SAM and L-BFGS re-evaluate the loss, so they cannot run under manual optimisation unless the step passes a closure. Reject the combination in `configure_optimizers` with a clear `ValueError`, not on the first batch.
4. **Resolve configuration once, in one place.** A shared default (`optimizer_params`) silently overrode each optimiser's own defaults, so Lion trained at ten times its rate. A config field that is a default for one optimiser family must not replace another's; resolve it where the optimiser type is known, and cover `model_copy(update=...)` paths (they skip validation).
5. **Forward every config field the network accepts.** A field added to a shared config but wired into two of five model families was silently ignored in the others. When you add one, grep every builder of that family and add a forwarding test (a source-level test that the builder names the field is enough).
6. **Unknown names fail.** An unknown optimiser or scheduler name must raise, never fall back to a default.
7. **Parameter groups** (a proposal at a smaller rate, no weight decay on biases): build the group list explicitly, keep it through schedulers that rewrite learning rates (`cyclic`, `one_cycle` set it themselves), and test the group rates after a scheduler step.
8. **Private fused ops** (`torch._foreach_*`) are fine for speed but private: write the plain-loop reference and test the two agree.

## Callbacks and averaging

9. **Weight averaging starts from a copy of the initial weights.** Lightning's `WeightAveraging` builds the averaged model at fit start, so until the first update the average is the untrained network. A delayed-start average (SWA) must validate with the current weights and finish with the last iterate until the average exists; otherwise early stopping, plateau schedulers and the final model use random weights. EMA that updates every step is safe from step one.
10. **`state_dict()` of a torch optimiser returns references**, not copies: `copy.deepcopy` it in a save and restore test or the test compares an object with itself.
11. **A logged tensor must not carry a graph.** Metric objects from `torchmetrics` keep a non-leaf `_forward_cache`; wrap them so the inputs are detached, or averaging deep-copies fail.

## Numerics and devices

12. **Code that runs on CPU, MPS and CUDA.** Not every op has an MPS kernel (`torch.special.ndtri` does not; `torch.erfinv` does, so `sqrt(2) * erfinv(2p - 1)` is the portable normal quantile). Clip probabilities away from 0 and 1 before an inverse CDF. Keep a CPU test; mark device tests.
13. **Seeds and determinism.** `lightning.seed_everything(seed, workers=True)`, a `torch.Generator` for any local randomness, explicit dropout seeds in tests; record the seed in the run.
14. **Losses are proper and exact where the claim needs it.** Use the exact pinball loss for calibration claims; a softplus-smoothed or Huber version is a different estimator (it widened or narrowed intervals and was the cause of an under-coverage finding). Sort or rearrange quantiles after training instead of inside the loss unless the guarantee is the point.

## Memory and speed in training

15. Detach what you log; `zero_grad(set_to_none=True)`; `inference_mode` in predict; gradient accumulation instead of a larger batch on the 8 GB laptop; `torch.compile` only for a stable-shape model. See [[python-performance]].

## Testing a LightningModule

16. Test with a tiny module and `Trainer(max_epochs=few, accelerator="cpu", logger=False, enable_checkpointing=False, enable_progress_bar=False)`. Assert the behaviour (learning rates after N epochs, which weights validation saw, which optimiser stepped), not that the code ran. Confirm each new test fails on the old code (stash the fix). See [[python-testing]].

## Review checklist

1. Manual optimisation anywhere? Then schedulers, clipping, accumulation, closures and logging are all explicit: Lightning raises if `gradient_clip_val` or gradient accumulation is set on the Trainer under manual optimisation, so clip with `self.clip_gradients(...)` inside the step and accumulate yourself.
2. Every new config field forwarded in every model family, with a test?
3. Averaging, schedulers and early stopping consistent about which weights and which metric they see?
4. Runs on CPU and MPS? Seeds recorded?
5. A test that fails on the previous behaviour?
