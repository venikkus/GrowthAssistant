rule bakta:
    input:
        fasta=lambda wc: pd.read_csv("config/samples.tsv", sep="\t").set_index("sample_id").loc[wc.sample, "fasta"]
    output:
        directory("results/annotation/{sample}/bakta")
    log:
        "results/logs/annotation/{sample}.bakta.log"
    conda:
        "../envs/bakta.yaml"
    shell:
        "mkdir -p {output} results/logs/annotation && "
        "command -v bakta >/dev/null 2>&1 || "
        "(echo 'ERROR: Bakta not found or database is not configured. Install bakta/bakta_db or run with --config mode=mock.' >&2; exit 127) && "
        "bakta {input.fasta} --output {output} --prefix {wildcards.sample} --force > {log} 2>&1"

rule prokka_optional:
    input:
        fasta=lambda wc: pd.read_csv("config/samples.tsv", sep="\t").set_index("sample_id").loc[wc.sample, "fasta"]
    output:
        directory("results/annotation/{sample}/prokka")
    log:
        "results/logs/annotation/{sample}.prokka.log"
    conda:
        "../envs/prokka.yaml"
    shell:
        "mkdir -p {output} results/logs/annotation && "
        "command -v prokka >/dev/null 2>&1 || "
        "(echo 'ERROR: Prokka not found. Install prokka or run with --config mode=mock.' >&2; exit 127) && "
        "prokka {input.fasta} --outdir {output} --prefix {wildcards.sample} --force > {log} 2>&1"
