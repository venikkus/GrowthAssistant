rule antismash:
    input:
        fasta=lambda wc: pd.read_csv("config/samples.tsv", sep="\t").set_index("sample_id").loc[wc.sample, "fasta"]
    output:
        directory("results/secondary_metabolites/{sample}/antismash")
    log:
        "results/logs/secondary_metabolites/{sample}.antismash.log"
    conda:
        "../envs/antismash.yaml"
    shell:
        "mkdir -p {output} results/logs/secondary_metabolites && "
        "command -v antismash >/dev/null 2>&1 || "
        "(echo 'ERROR: antiSMASH not found or databases are missing. Install antismash or run with --config mode=mock.' >&2; exit 127) && "
        "antismash {input.fasta} --output-dir {output} > {log} 2>&1"

rule bagel:
    input:
        fasta=lambda wc: pd.read_csv("config/samples.tsv", sep="\t").set_index("sample_id").loc[wc.sample, "fasta"]
    output:
        directory("results/secondary_metabolites/{sample}/bagel")
    log:
        "results/logs/secondary_metabolites/{sample}.bagel.log"
    conda:
        "../envs/core.yaml"
    shell:
        "mkdir -p {output} results/logs/secondary_metabolites && echo 'placeholder: BAGEL bacteriocin screen' > {log}"

rule dbcan:
    input:
        rules.bakta.output
    output:
        directory("results/cazy/{sample}")
    log:
        "results/logs/cazy/{sample}.dbcan.log"
    conda:
        "../envs/dbcan.yaml"
    shell:
        "mkdir -p {output} results/logs/cazy && echo 'placeholder: run_dbcan' > {log}"
