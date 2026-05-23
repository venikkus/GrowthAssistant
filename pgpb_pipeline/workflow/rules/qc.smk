rule quast:
    input:
        fasta=lambda wc: pd.read_csv("config/samples.tsv", sep="\t").set_index("sample_id").loc[wc.sample, "fasta"]
    output:
        directory("results/qc/{sample}/quast")
    log:
        "results/logs/qc/{sample}.quast.log"
    conda:
        "../envs/quast.yaml"
    shell:
        "mkdir -p {output} results/logs/qc && "
        "command -v quast.py >/dev/null 2>&1 || "
        "(echo 'ERROR: QUAST not found. Install quast or run with --config mode=mock.' >&2; exit 127) && "
        "quast.py {input.fasta} -o {output} > {log} 2>&1"

rule checkm:
    input:
        fasta=lambda wc: pd.read_csv("config/samples.tsv", sep="\t").set_index("sample_id").loc[wc.sample, "fasta"]
    output:
        directory("results/qc/{sample}/checkm")
    log:
        "results/logs/qc/{sample}.checkm.log"
    conda:
        "../envs/checkm.yaml"
    shell:
        "mkdir -p {output} results/logs/qc && "
        "command -v checkm >/dev/null 2>&1 || "
        "(echo 'ERROR: CheckM not found. Install checkm-genome or run with --config mode=mock.' >&2; exit 127) && "
        "echo 'CheckM rule template: provide bins directory for production runs.' > {log}"

rule busco:
    input:
        fasta=lambda wc: pd.read_csv("config/samples.tsv", sep="\t").set_index("sample_id").loc[wc.sample, "fasta"]
    output:
        directory("results/qc/{sample}/busco")
    log:
        "results/logs/qc/{sample}.busco.log"
    conda:
        "../envs/busco.yaml"
    shell:
        "mkdir -p {output} results/logs/qc && "
        "command -v busco >/dev/null 2>&1 || "
        "(echo 'ERROR: BUSCO not found. Install busco and bacteria_odb database or run with --config mode=mock.' >&2; exit 127) && "
        "busco -i {input.fasta} -m genome -l bacteria_odb10 -o {wildcards.sample} --out_path {output} > {log} 2>&1"
