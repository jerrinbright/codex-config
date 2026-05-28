# Preference Methods

## Method Routing

- **SFT**: one correct answer or corrected label.
- **DPO**: prompt, chosen answer, rejected answer; stable and common.
- **SimPO**: preference optimization without explicit reference-model logprobs in some setups.
- **TRL**: common HF toolkit for SFT/DPO/PPO-style workflows.
- **OpenRLHF / verl**: larger-scale RLHF/RL training infrastructure.
- **GRPO**: reward-driven group-relative optimization; only use when reward signal is reliable.

## Auditor Corrections

Good post-training rows:

```json
{
  "input": "...",
  "chosen": "corrected label",
  "rejected": "wrong model label",
  "reason": "wrong object",
  "source": "audit campaign id"
}
```

Ambiguous rows should be excluded or marked for manual review.

## Eval

- Preference win rate on heldout pairs.
- Object/action exact and similar accuracy.
- Regression on standard GT.
- False-correction rate.

