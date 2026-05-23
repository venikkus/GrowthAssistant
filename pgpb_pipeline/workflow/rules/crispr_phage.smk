rule crisprcasfinder:
    input:
        fasta=lambda wc: pd.read_csv("config/samples.tsv", sep="\t").set_index("sample_id").loc[wc.sample, "fasta"]
    output:
        directory("results/crispr_phage/{sample}/crisprcasfinder")
    log:
        "results/logs/crispr_phage/{sample}.crispr.log"
    conda:
        "../envs/core.yaml"
    shell:
        "mkdir -p {output} results/logs/crispr_phage && echo 'placeholder: CRISPRCasFinder' > {log}"

rule phaster:
    input:
        fasta=lambda wc: pd.read_csv("config/samples.tsv", sep="\t").set_index("sample_id").loc[wc.sample, "fasta"]
    output:
        directory("results/crispr_phage/{sample}/phaster")
    log:
        "results/logs/crispr_phage/{sample}.phaster.log"
    conda:
        "../envs/core.yaml"
    shell:
        "mkdir -p {output} results/logs/crispr_phage && echo 'placeholder: PHASTER API/manual import' > {log}"

