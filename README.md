# Mimir — Lumrik expression analysis workflow

Standalone Nextflow DSL2 workflow. Runs `sc-analyse gex` on MEX/Norn/H5AD inputs, optionally imports reviewed annotations and splits H5AD by an `obs` column.

## Setup

Edit `config/datasets.tsv` with **absolute paths**. Columns:
- `dataset`: unique ASCII identifier
- `input`: source MEX/Norn/H5AD for `gex`, or existing `analysis.h5ad` for `existing`
- `mode`: `gex` or `existing`
- `annotations`: optional reviewed TSV, one row per cluster (required for annotation)
- `split_by`: `obs` column to split by (default `cell_type`)

Do **not** add a GSE156441 combined H5AD as a `gex` input if you want to retain its original clustering: use `existing`. Set `mode=gex` if you explicitly want to recompute it.

## Commands

```bash
# Local, using installed executable:
nextflow run . -profile local -resume --sc_analyse /path/to/sc-analyse --samples config/datasets.tsv --outdir /path/to/mimir_results

# Apptainer, using published Lumrik image containing new annotation/split commands:
nextflow run . -profile apptainer -resume --samples config/datasets.tsv --outdir /path/to/mimir_results --lumrik_image ghcr.io/stela2502/lumrik:v0.9.2

# After reviewing the AI-ready package and filling annotations column in datasets.tsv:
nextflow run . -profile apptainer -resume --samples config/datasets.tsv --outdir /path/to/mimir_results --run_annotate true --run_split true
```

The workflow never modifies input H5AD files: annotation copies the file first. GEX creates an independent analysis. Split creates separate H5ADs.

**Caution:** This is an initial implementation, not yet executed against your data or Nextflow. Nextflow's `publishDir overwrite:false` protects published outputs from replacement but is **not** a full immutable-output or transaction guarantee. Keep `-resume` and do not use a preexisting published directory for an unrelated new run. Existing published analyses should be treated as immutable; use `mode=existing` to reuse their H5AD. This workflow does not yet perform SNP integration, sample-ID restoration, or TraConMech modeling—those belong in Runar/Vidar or a later targeted Mimir feature.

For a memory-constrained workstation, `--max_parallel 1` keeps compute processes sequential. Note `cp` of large H5AD for annotation requires disk space.

**Image:** v0.9.2 is a proposed tag, not verified as published. Use an image that actually includes `sc-analyse annotate` and `split`.

## Preflight (no analysis)

```bash
nextflow run . -entry PREFLIGHT -profile local \
  --samples /absolute/path/to/datasets.tsv \
  --outdir /absolute/path/to/mimir_results \
  --sc_analyse /absolute/path/to/sc-analyse
```

For container mode, also supply `--preflight_profile apptainer` and
`--lumrik_image ...`. The preflight checks the host Apptainer executable and
image path if it is a local SIF; it **does not pull or inspect remote images**.
No output directories are created and no analysis is run. Python 3 standard
library is used **only by the preflight checker**, not the biological pipeline.
