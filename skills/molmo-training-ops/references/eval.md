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

The wrapper runs `precompute`, `inference`, `append`, and `serve` stages. Until
the remaining one-off inference/append scripts are fully consolidated, configure:

```bash
MOLMO_HOLDOUT20_INFERENCE_CMD='<modal inference command>'
MOLMO_HOLDOUT20_APPEND_CMD='<local append command>'
```

Before running inference:

1. Confirm the checkpoint path points at a merged HSDP checkpoint, usually
   `<run_root>/merged_checkpoints/step...`.
2. Confirm the holdout frame cache uses the same crop mode as training.
3. Write outputs into the campaign holdout eval root and add the model as a
   named column in the top-checkpoint viewer.
4. For blur-pad models, use `expand_square_blur` holdout precompute.
