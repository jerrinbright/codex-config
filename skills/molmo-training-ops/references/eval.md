# Heldout-20 Eval Checklist

Standard viewer:

```text
modal/runs/campaign_6a15_missed_action10_eval/top6_ckpt_compare/index.html
```

Serve it with:

```bash
CAMPAIGN_TOP6_VIEWER_APP_NAME=campaign6a15-top6-ckpt-compare-viewer \
modal run --detach -e jerrin modal/scripts/eval/serve_campaign_top6_ckpt_compare_viewer.py
```

Use the staged compare wrapper for new checkpoint spot-checks:

```bash
python runs/eval_holdout20_compare.py --dry-run
```

Preferred flow is metadata-driven. If the run has
`/ckpt_vol/runs/molmo2/<run>/run_metadata.json`, pass it in:

```bash
MOLMO_RUN_METADATA_PATH=/ckpt_vol/runs/molmo2/<run>/run_metadata.json \
MOLMO_HOLDOUT20_INFERENCE_CMD='<modal inference command>'
python runs/eval_holdout20_compare.py --dry-run
```

The wrapper runs `precompute`, `inference`, `append`, and `serve` stages.
Metadata supplies the default model id/label, checkpoint step, crop policy,
heldout annotations path, heldout input root, results path, and viewer note.

Until checkpoint-specific inference scripts are fully consolidated, configure
only `MOLMO_HOLDOUT20_INFERENCE_CMD`. The injected command should read:

- `MOLMO_HOLDOUT20_ANNOTATIONS_PATH`
- `MOLMO_HOLDOUT20_INPUT_ROOT`
- `MOLMO_HOLDOUT20_NATIVE_CKPT`
- `MOLMO_HOLDOUT20_RESULTS_PATH`
- `MOLMO_HOLDOUT20_PREDICTION_KEY`

Before running inference:

1. Confirm the checkpoint path points at a merged HSDP checkpoint, usually
   `<run_root>/merged_checkpoints/step...`.
2. Confirm `run_metadata.json` records the same crop mode used by training.
3. Confirm the heldout frame cache uses that same crop mode. The policy keys are
   `campaign6a15_crop_prior_yolo_f96_fps8`,
   `campaign6a15_squarepad_yolo_f96_fps8`,
   `campaign6a15_expand_square_edge_yolo_f96_fps8`, and
   `campaign6a15_blurpad_yolo_f96_fps8`.
4. Write outputs into the campaign holdout eval root and add the model as a
   named column in the top-checkpoint viewer.
5. For blur-pad models, use `expand_square_blur` holdout precompute.

Direct viewer update for an already completed result:

```bash
python runs/update_holdout20_viewer.py \
  --add-result /ckpt_vol/runs/molmo2/.../results.json \
  --model-id my_model_step2000 \
  --model-label "My model step2000"
```

Serve the standard Modal viewer:

```bash
CAMPAIGN_TOP6_VIEWER_APP_NAME=campaign6a15-top6-ckpt-compare-viewer \
modal run --detach -e jerrin modal/scripts/eval/serve_campaign_top6_ckpt_compare_viewer.py
```
