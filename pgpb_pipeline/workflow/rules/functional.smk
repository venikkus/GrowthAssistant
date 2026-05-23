rule eggnog_mapper:
    input:
        rules.bakta.output
    output:
        directory("results/functional/{sample}/eggnog")
    log:
        "results/logs/functional/{sample}.eggnog.log"
    conda:
        "../envs/eggnog.yaml"
    shell:
        "mkdir -p {output} results/logs/functional && "
        "command -v emapper.py >/dev/null 2>&1 || "
        "(echo 'ERROR: eggNOG-mapper emapper.py not found or databases are missing. Install eggnog-mapper or run with --config mode=mock.' >&2; exit 127) && "
        "echo 'Run emapper.py on Bakta FAA output here; adapter kept explicit for production wiring.' > {log}"

rule interproscan_placeholder:
    input:
        rules.bakta.output
    output:
        directory("results/functional/{sample}/interproscan")
    log:
        "results/logs/functional/{sample}.interproscan.log"
    conda:
        "../envs/core.yaml"
    shell:
        "mkdir -p {output} results/logs/functional && echo 'optional placeholder: InterProScan' > {log}"
