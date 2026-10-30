# Mimir — expression analysis, annotation and H5AD splitting

Mimir is a Nextflow DSL2 workflow that runs `sc-analyse gex` or reuses an existing H5AD, optionally imports reviewed cluster annotations, and optionally splits the resulting H5AD by an observation column.

## 1. Prepare `config/datasets.tsv`

This is a **tab-separated** file with a case-sensitive header:

```tsv
dataset	input	mode	annotations	split_by
own	/absolute/path/to/own/raw_feature_bc_matrix	gex		cell_type
GSE156441	/absolute/path/to/GSE156441/sc_analysis_combined/analysis.h5ad	existing		cell_type
reviewed	/absolute/path/to/reviewed/analysis.h5ad	existing	/absolute/path/to/cell_types.tsv	cell_type
```

Each row is one input dataset:

| Column | Meaning |
| --- | --- |
| `dataset` | Unique identifier; used in output directory names. Use letters, digits, `_`, `-`. |
| `input` | Input MEX directory (for `gex`) or existing `.h5ad` (for `existing`); use absolute paths. |
| `mode` | `gex` recomputes the expression analysis; `existing` reuses the H5AD without recalculating clustering. |
| `annotations` | Optional path to a reviewed cluster-annotation TSV. Required for rows you want to annotate. Leave the field **empty**, but retain its tab separators, if not annotating. |
| `split_by` | H5AD `obs` column for splitting, typically `cell_type`; defaults to `cell_type` if blank. |

**Important:** Use `existing` for the combined GSE156441 H5AD if you want to preserve its current clustering. Use `gex` only when recomputing the analysis is intended. Do not pass an existing H5AD to `gex` merely to reuse it.

The reviewed annotations file must match what `sc-analyse annotate` expects. For the default CLI settings it should contain `cluster` and `cell_type` columns, with cluster IDs matching the H5AD's cluster values. Additional confidence/evidence columns may be present; consult `sc-analyse annotate --help` for the installed version. An annotation file is **not** the same thing as `datasets.tsv`.

## 2. Choose the operations

- Default: run expression analysis for `gex` rows and reuse H5ADs for `existing` rows.
- `--run_annotate true`: copy each eligible H5AD and apply its reviewed annotation TSV. Only rows with nonempty `annotations` participate.
- `--run_split true`: split annotated H5ADs by their `split_by` column. **The current workflow requires `--run_annotate true` when splitting.** Rows without an annotations file are not split by this workflow, even if they already have `cell_type`.

Inputs are not edited in place. Annotation works on a copied H5AD; splitting writes new H5AD files.

## 3. Validate the input table (preflight)

```bash
cd ~/git_Projects/mimir
nextflow run . -entry PREFLIGHT -profile local \
  --samples "$PWD/config/datasets.tsv" \
  --outdir /absolute/path/to/mimir_results \
  --sc_analyse /absolute/path/to/sc-analyse
```

Preflight uses Python 3 on the Nextflow launch host, checks configuration, and does not launch the biological analysis. For container mode supply `--preflight_profile apptainer` and an appropriate `--lumrik_image`; a local SIF path can be checked without pulling a remote image.

## 4. Execute

Local run:

```bash
nextflow run . -profile local -resume \
  --samples "$PWD/config/datasets.tsv" \
  --sc_analyse /absolute/path/to/sc-analyse \
  --outdir /absolute/path/to/mimir_results \
  --max_parallel 1
```

With reviewed annotations and splitting:

```bash
nextflow run . -profile local -resume \
  --samples "$PWD/config/datasets.tsv" \
  --sc_analyse /absolute/path/to/sc-analyse \
  --outdir /absolute/path/to/mimir_results \
  --run_annotate true --run_split true
```

For Apptainer or Slurm, use `-profile apptainer` or `-profile slurm` and supply a **verified** `--lumrik_image` containing `sc-analyse annotate` and `sc-analyse split`. The default v0.9.2 tag is not verified as published. For `gex`, additional parameters include `--min_umi_count`, `--variable_genes`, `--pca_components` and `--merge_pearson` (defaults are in `nextflow.config`).

## 5. Expected output layout

```text
mimir_results/
  <dataset>/
    gex/analysis/analysis.h5ad     # gex rows
    annotated/annotated.h5ad       # rows with reviewed annotations when enabled
    split/                         # split H5AD files when enabled
```

For `existing` rows, the workflow reuses the input H5AD rather than publishing a newly computed GEX result. The exact split filenames depend on `sc-analyse split`.

`-resume` reuses successful tasks. Existing published outputs are not overwritten, but publication is not a full immutable-output guarantee. Avoid mixing independent runs in one output directory. Mimir does not delete existing analyses or original H5AD files.

## 6. Common problems

- **Empty `annotations` column:** retain both tabs around the empty field; do not omit the column.
- **Wrong mode:** `gex` recomputes analysis; `existing` preserves the current H5AD.
- **Split skipped:** supply `--run_annotate true --run_split true` and a valid annotation TSV for each dataset to split.
- **Annotation mismatch:** verify `cluster` IDs and `cell_type` labels in the reviewed TSV.
- **Wrong executable version:** verify `sc-analyse annotate --help` and `sc-analyse split --help` against your installed binary.

This is the behavior of the supplied Mimir source, not a proposed future workflow. The pipeline still needs validation on representative data before production use.
