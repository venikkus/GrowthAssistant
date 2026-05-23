# Optional PGPT-Pred / PLaBAse Import

Put manually downloaded PGPT-Pred/PLaBAse result tables here as:

```text
data/external/pgpt_pred/{sample_id}.tsv
```

The pipeline treats these files as optional supporting PGP evidence. If a file is absent, the mock/real pipeline continues without it.

Expected useful columns, with flexible aliases:

- `sample_id`
- `locus_tag` / `protein_id` / `query`
- `gene` / `marker`
- `trait_category` / `trait` / `prediction`
- `confidence` / `score`
- `description` / `function`

