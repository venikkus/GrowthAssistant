rule detect_pgp_traits:
    input:
        rules.eggnog_mapper.output
    output:
        directory("results/pgp_traits/{sample}")
    log:
        "results/logs/pgp_traits/{sample}.log"
    conda:
        "../envs/core.yaml"
    shell:
        "mkdir -p {output} results/logs/pgp_traits && echo 'placeholder: internal marker/HMM/keyword PGP detection' > {log}"

rule pgpt_pred_optional_import:
    output:
        touch("results/pgp_traits/{sample}/pgpt_pred_import.done")
    log:
        "results/logs/pgp_traits/{sample}.pgpt_pred_import.log"
    conda:
        "../envs/core.yaml"
    shell:
        "mkdir -p results/pgp_traits/{wildcards.sample} results/logs/pgp_traits && "
        "if [ -f data/external/pgpt_pred/{wildcards.sample}.tsv ]; then "
        "echo 'Using optional PGPT-Pred/PLaBAse import: data/external/pgpt_pred/{wildcards.sample}.tsv' > {log}; "
        "else "
        "echo 'Optional PGPT-Pred/PLaBAse import not found for {wildcards.sample}; continuing without it.' > {log}; "
        "fi"
