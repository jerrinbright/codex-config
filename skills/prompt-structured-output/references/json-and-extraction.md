# JSON And Extraction

## Strict JSON Prompt Shape

```text
Task: Extract manipulated physical object noun phrases.
Rules:
- Return JSON only.
- Use this schema: {"objects": string[]}
- Objects must be copied from the current input text.
- Do not include verbs.
- Do not include standalone colors/materials unless part of an object phrase.
- Return [] if no object is present.
Input: ...
```

## Post-Filters

- JSON parse.
- Schema validate.
- Lowercase/normalize.
- Remove action verbs.
- Remove standalone colors/materials.
- Ensure phrase words appear in input or allowed vocabulary.
- Deduplicate while preserving order.

## Tiny LLM Use

- Run on unique strings, not every segment.
- Prefer rule parser first, LLM fallback for ambiguous strings.
- Store prompt version and model name with cached output.

## Structured Libraries

- `instructor`: typed schema extraction with Pydantic.
- `outlines`: constrained generation / JSON regex style outputs.
- `guidance`: prompt programs and constrained generation.
- `DSPy`: systematic prompt/program optimization when there is an eval set.

