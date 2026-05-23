rule aggregate_results:
    input:
        TOOL_OUTPUTS
    output:
        "results/tables/qc_summary.tsv",
        "results/tables/taxonomy_summary.tsv",
        "results/tables/annotation_summary.tsv",
        "results/tables/functional_summary.tsv",
        "results/tables/pgp_traits_long.tsv",
        "results/tables/pgp_traits_matrix.tsv",
        "results/tables/pgp_trait_summary.tsv",
        "results/tables/bgc_summary.tsv",
        "results/tables/biosafety_summary.tsv",
        "results/tables/external_database_evidence.tsv",
        "results/tables/database_evidence_summary.tsv",
        "results/tables/plasmid_summary.tsv",
        "results/tables/crispr_summary.tsv",
        "results/tables/phage_summary.tsv"
    log:
        "results/logs/ranking/aggregate.log"
    conda:
        "../envs/core.yaml"
    shell:
        "mkdir -p results/logs/ranking && PYTHONPATH=src python scripts/aggregate_results.py --config config/config.yaml --samples config/samples.tsv --results results > {log} 2>&1"

rule score_strains:
    input:
        "results/tables/qc_summary.tsv",
        "results/tables/taxonomy_summary.tsv",
        "results/tables/annotation_summary.tsv",
        "results/tables/pgp_traits_long.tsv",
        "results/tables/bgc_summary.tsv",
        "results/tables/biosafety_summary.tsv",
        "results/tables/database_evidence_summary.tsv"
    output:
        "results/tables/final_ranking.tsv"
    log:
        "results/logs/ranking/score.log"
    conda:
        "../envs/core.yaml"
    shell:
        "mkdir -p results/logs/ranking && PYTHONPATH=src python scripts/score_strains.py --config config/config.yaml --samples config/samples.tsv --results results > {log} 2>&1"

rule make_report:
    input:
        "results/tables/final_ranking.tsv"
    output:
        "results/reports/final_report.html"
    log:
        "results/logs/ranking/report.log"
    conda:
        "../envs/core.yaml"
    shell:
        "mkdir -p results/logs/ranking && PYTHONPATH=src python scripts/make_report.py --results results > {log} 2>&1"
