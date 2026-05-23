# PGPB genome report: strain_002

**Prototype output. Candidates require laboratory, greenhouse, field, and biosafety validation.**

## Final recommendation

- Status: reject_or_manual_review
- Confidence: E
- Final score: -2.416
- Validation plan: CAS siderophore assay; dual culture assay against target pathogen; mandatory biosafety review before any plant assay; lab/greenhouse validation before field use

## Taxonomy

| sample_id | gtdb_classification | genus | species | closest_reference | ani | mash_distance | kraken_top_hit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strain_002 | d__Bacteria;p__Pseudomonadota;c__Gammaproteobacteria;o__Enterobacterales;f__Enterobacteriaceae;g__Enterobacter;s__Enterobacter cloacae | Enterobacter | cloacae | GCF_demo_E_cloacae | 96.1 | 0.042 | Enterobacter cloacae complex |

## Genome QC

| sample_id | total_length | num_contigs | n50 | gc | completeness | contamination | busco_complete | busco_single | busco_duplicated | busco_fragmented | busco_missing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strain_002 | 4900000 | 310 | 24000 | 55.1 | 89.2 | 6.4 | 88.0 | 86.0 | 2.0 | 5.0 | 7.0 |

## PGP traits

| sample_id | trait_category | trait_name | gene_or_marker | locus_tag | evidence_type | source_tool | confidence | description |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| strain_002 | biocontrol | biocontrol | bacteriocin | NA | antismash_cluster | antismash | medium | bacteriocin bacteriocin-like antimicrobial region_2 100000-130000 |
| strain_002 | biocontrol | biocontrol | lytic enzyme/protease | gene_010 | annotation_keyword | annotation | medium | gene_010: chitinase family protein |
| strain_002 | biocontrol | biocontrol | lytic enzyme/protease | gene_011 | annotation_keyword | annotation | medium | gene_011: beta-1,3-glucanase |
| strain_002 | biocontrol | biocontrol | lytic enzyme/protease | gene_014 | annotation_keyword | annotation | medium | gene_014: protease |
| strain_002 | biocontrol | biocontrol | nrps | NA | antismash_cluster | antismash | medium | NRPS siderophore siderophore region_1 5000-61000 |
| strain_002 | siderophore | siderophore production | siderophore | NA | antismash_cluster | antismash | high | NRPS siderophore siderophore region_1 5000-61000 |
| strain_002 | siderophore | siderophore production | siderophore | gene_012 | annotation_keyword | annotation | medium | gene_012: siderophore biosynthesis protein |

## Secondary metabolites

| sample_id | region | bgc_type | product | similarity | coordinates | potential_role |
| --- | --- | --- | --- | --- | --- | --- |
| strain_002 | region_1 | NRPS | siderophore | 0.55 | 5000-61000 | siderophore |
| strain_002 | region_2 | bacteriocin | bacteriocin-like | 0.37 | 100000-130000 | antimicrobial |

## Biosafety risks

| sample_id | amr_gene_count | virulence_factor_count | taxonomy_risk | mobile_amr | biosafety_penalty |
| --- | --- | --- | --- | --- | --- |
| strain_002 | 2 | 2 | high | False | 16.0 |

## Plasmids/mobile elements

| sample_id | replicon | mobility_type | conjugative | amr_near_mobile |
| --- | --- | --- | --- | --- |
| strain_002 | IncF | MOBF | 1.0 | 1.0 |

## CRISPR/phage

| sample_id | array_count | cas_genes |
| --- | --- | --- |
| strain_002 | 0 | NA |

| sample_id | region_count | intact_count |
| --- | --- | --- |
| strain_002 | 3 | 1 |