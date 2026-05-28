# Data Engines

Use this reference when native Python scripts and Modal functions are not enough for ML data prep.

## Routing

- **Plain Python + Modal**: best for simple remote fanout, R2/Mongo/video jobs, and existing Modal infrastructure.
- **Ray Data**: best for large ML data processing, streaming execution, batch inference, image/video-like multimodal pipelines, and CPU/GPU transforms across a cluster.
- **Dask**: best for larger-than-memory pandas/NumPy-style processing and multi-file tabular workflows.
- **Polars**: best for fast in-memory dataframe work, lazy query optimization, and local/medium metadata processing.
- **Vaex**: useful for memory-mapped/lazy dataframe workflows, but less common than Polars/Dask.
- **Zarr**: useful for chunked arrays, repeated random access, and packed frame/crop tensors.

## Video And Frame Work

Prefer:

- group by video URI,
- open video once per group,
- sort requested timestamps,
- decode sequentially when possible,
- resize/crop once,
- write durable frame/crop references.

Avoid:

- opening the same video once per segment,
- one remote call per frame,
- writing millions of tiny files without a merge/packing plan,
- rerunning deterministic detectors when DB/R2 already stores outputs.

## R2/Mongo

- Batch Mongo lookups by episode ID.
- Pull WES from `episodes.pipeline_results.hands.bbox_url` when available.
- Cache downloaded bbox JSON per episode.
- Keep failed/missing IDs in durable files.
- Separate test-set exclusion before expensive preprocessing.

## Packed Storage

Consider Zarr/WebDataset/Parquet-style packing when:

- the same frames/crops are reused across many runs,
- tiny file overhead dominates,
- training dataloader spends time opening files,
- random frame access is needed repeatedly.

Do not introduce packed storage unless the repo can read it cleanly and the conversion cost is justified.

