# Precompute Checklist

Use repo wrappers:

```bash
python precompute/naruto543_blurpad.py --dry-run
python precompute/holdout20_blurpad.py --dry-run
python precompute/holdout20_squarepad.py --dry-run
python precompute/holdout20_expand_square_edge.py --dry-run
python precompute/run_precompute.py precompute.naruto543_blurpad --dry-run
```

Crop policies:

- `square_pad`: crop saved box, edge-pad to square, resize.
- `expand_square_edge`: expand saved box toward square with real frame context,
  then edge-pad only if needed.
- `expand_square_blur`: expand saved box toward square with real frame context,
  then use blurred context for unavoidable padding. This is the recommended
  current policy.

Heldout-20 policy keys:

- `campaign6a15_crop_prior_yolo_f96_fps8`
- `campaign6a15_squarepad_yolo_f96_fps8`
- `campaign6a15_expand_square_edge_yolo_f96_fps8`
- `campaign6a15_blurpad_yolo_f96_fps8`

Use the policy key from `run_metadata.json` instead of picking a holdout cache
by hand when possible.

Before combine:

- non-error index shard count matches expected shard count
- frame tar shard count matches expected shard count
- zero-size tar shard count is zero
- stale `.errors.json` markers are either gone or deliberately handled with
  `combine-skip-stale`

For eval, precompute with the same crop policy used during training.
