rule gtdbtk:
    input:
        fasta=lambda wc: pd.read_csv("config/samples.tsv", sep="\t").set_index("sample_id").loc[wc.sample, "fasta"]
    output:
        directory("results/taxonomy/{sample}/gtdbtk")
    log:
        "results/logs/taxonomy/{sample}.gtdbtk.log"
    conda:
        "../envs/taxonomy.yaml"
    shell:
        "mkdir -p {output} results/logs/taxonomy && echo 'placeholder: gtdbtk classify_wf {input.fasta}' > {log}"

rule kraken2:
    input:
        fasta=lambda wc: pd.read_csv("config/samples.tsv", sep="\t").set_index("sample_id").loc[wc.sample, "fasta"]
    output:
        directory("results/taxonomy/{sample}/kraken2")
    log:
        "results/logs/taxonomy/{sample}.kraken2.log"
    conda:
        "../envs/taxonomy.yaml"
    shell:
        "mkdir -p {output} results/logs/taxonomy && echo 'placeholder: kraken2 --db DB {input.fasta}' > {log}"

rule mash_fastani:
    input:
        fasta=lambda wc: pd.read_csv("config/samples.tsv", sep="\t").set_index("sample_id").loc[wc.sample, "fasta"]
    output:
        directory("results/taxonomy/{sample}/ani")
    log:
        "results/logs/taxonomy/{sample}.ani.log"
    conda:
        "../envs/taxonomy.yaml"
    shell:
        "mkdir -p {output} results/logs/taxonomy && echo 'placeholder: mash dist / fastANI {input.fasta}' > {log}"

