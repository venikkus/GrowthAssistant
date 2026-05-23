rule plasmidfinder:
    input:
        fasta=lambda wc: pd.read_csv("config/samples.tsv", sep="\t").set_index("sample_id").loc[wc.sample, "fasta"]
    output:
        directory("results/mobile_elements/{sample}/plasmidfinder")
    log:
        "results/logs/mobile_elements/{sample}.plasmidfinder.log"
    conda:
        "../envs/core.yaml"
    shell:
        "mkdir -p {output} results/logs/mobile_elements && echo 'placeholder: PlasmidFinder' > {log}"

rule mobsuite:
    input:
        fasta=lambda wc: pd.read_csv("config/samples.tsv", sep="\t").set_index("sample_id").loc[wc.sample, "fasta"]
    output:
        directory("results/mobile_elements/{sample}/mobsuite")
    log:
        "results/logs/mobile_elements/{sample}.mobsuite.log"
    conda:
        "../envs/core.yaml"
    shell:
        "mkdir -p {output} results/logs/mobile_elements && echo 'placeholder: MOB-suite' > {log}"

