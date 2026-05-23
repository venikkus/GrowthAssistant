# PGPB genome report: strain_001

**Prototype output. Candidates require laboratory, greenhouse, field, and biosafety validation.**

## Final recommendation

- Status: strong_candidate
- Confidence: A
- Final score: 32.32
- Validation plan: phosphate solubilization assay; ACC deaminase assay; CAS siderophore assay; plant pot experiment under stress; colonization assay by re-isolation/qPCR/GFP-tagging; lab/greenhouse validation before field use

## Taxonomy

| sample_id | gtdb_classification | genus | species | closest_reference | ani | mash_distance | kraken_top_hit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strain_001 | d__Bacteria;p__Bacillota;c__Bacilli;o__Bacillales;f__Bacillaceae;g__Bacillus;s__Bacillus velezensis | Bacillus | velezensis | GCF_demo_B_velezensis | 98.8 | 0.018 | Bacillus velezensis |

## Genome QC

| sample_id | total_length | num_contigs | n50 | gc | completeness | contamination | busco_complete | busco_single | busco_duplicated | busco_fragmented | busco_missing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strain_001 | 5200000 | 42 | 210000 | 58.4 | 98.7 | 0.8 | 98.1 | 97.4 | 0.7 | 0.8 | 1.1 |

## PGP traits

| sample_id | trait_category | trait_name | gene_or_marker | locus_tag | evidence_type | source_tool | confidence | description |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strain_001 | ACC_deaminase | ACC deaminase | acdS | gene_001 | annotation_keyword | annotation | high | gene_001: ACC deaminase acdS |
| strain_001 | ACC_deaminase | ACC deaminase | acdS | PGPT_001 | pgpt_pred_import | PGPT-Pred/PLaBAse | high | PGPT-Pred demo hit for ACC deaminase |
| strain_001 | biocontrol | biocontrol | lanthipeptide | NA | antismash_cluster | antismash | medium | lanthipeptide antimicrobial peptide antimicrobial region_2 90000-120000 |
| strain_001 | biocontrol | biocontrol | nrps | NA | antismash_cluster | antismash | medium | NRPS siderophore-like siderophore region_1 1000-55000 |
| strain_001 | phosphate_solubilization | phosphate solubilization | gcd | gene_003 | annotation_keyword | annotation | high | gene_003: gcd glucose dehydrogenase / gcd+pqq combination detected |
| strain_001 | phosphate_solubilization | phosphate solubilization | pqq | gene_002 | annotation_keyword | annotation | high | gene_002: pqqC pyrroloquinoline quinone biosynthesis / gcd+pqq combination detected |
| strain_001 | phosphate_solubilization | phosphate solubilization | pqqC | PGPT_002 | pgpt_pred_import | PGPT-Pred/PLaBAse | high | PGPT-Pred demo hit for PQQ pathway |
| strain_001 | root_colonization | root colonization | motility/chemotaxis/pili | gene_005 | annotation_keyword | annotation | medium | gene_005: flagellar biosynthesis protein |
| strain_001 | siderophore | siderophore production | siderophore | NA | antismash_cluster | antismash | high | NRPS siderophore-like siderophore region_1 1000-55000 |
| strain_001 | stress_tolerance | stress tolerance | osmoprotection/cold stress | gene_004 | annotation_keyword | annotation | medium | gene_004: trehalose biosynthesis protein |

## Secondary metabolites

| sample_id | region | bgc_type | product | similarity | coordinates | potential_role |
| --- | --- | --- | --- | --- | --- | --- |
| strain_001 | region_1 | NRPS | siderophore-like | 0.62 | 1000-55000 | siderophore |
| strain_001 | region_2 | lanthipeptide | antimicrobial peptide | 0.41 | 90000-120000 | antimicrobial |

## Biosafety risks

| sample_id | amr_gene_count | virulence_factor_count | taxonomy_risk | mobile_amr | biosafety_penalty |
| --- | --- | --- | --- | --- | --- |
| strain_001 | 0 | 0 | low | False | 0.0 |

## Plasmids/mobile elements

No rows.

## CRISPR/phage

| sample_id | array_count | cas_genes |
| --- | --- | --- |
| strain_001 | 2 | cas1;cas2 |

| sample_id | region_count | intact_count |
| --- | --- | --- |
| strain_001 | 1 | 0 |