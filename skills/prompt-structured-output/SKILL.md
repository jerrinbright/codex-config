---
name: prompt-structured-output
description: "Design reliable prompts and parsers for structured outputs, JSON-only responses, constrained decoding, object/noun extraction, tiny LLM extraction, prompt caching, schema validation, and deterministic fallbacks."
---

# Prompt Structured Output

## Purpose

Make model outputs parseable, cached, and production-safe.

Use this for Qwen noun extraction, JSON labels, candidate extraction, prompt tuning, `instructor`, `guidance`, `outlines`, DSPy-style prompt experiments, and deterministic parser fallbacks.

Read `references/json-and-extraction.md` for strict JSON and noun/object extraction patterns.
Read `references/prompt-evaluation.md` when comparing prompts, parsers, tiny models, or structured-output regressions.

## Workflow

1. **Define schema**
   - Minimal fields, types, and allowed values.
   - Invalid/empty behavior.

2. **Write prompt**
   - State the task.
   - Include output schema.
   - Add 2-5 examples only when needed.
   - For extraction, require copying from input unless transformation is explicitly allowed.

3. **Validate**
   - Parse JSON.
   - Validate schema.
   - Enforce copy-only or allowed vocabulary.
   - Retry/fallback only on invalid outputs.

4. **Cache**
   - Normalize input string.
   - Cache by model, prompt version, schema version, and input hash.

5. **Evaluate**
   - JSON validity.
   - Field accuracy.
   - Hallucination rate.
   - Latency per unique input.
   - Regression examples where the new prompt/parser worsens previously correct outputs.

## Safety

- Do not trust LLM output without schema validation.
- Avoid per-segment LLM calls when unique-string caching works.
- Keep prompt versions explicit in output metadata.
