rule amrfinder:
    input:
        fasta=lambda wc: pd.read_csv("config/samples.tsv", sep="\t").set_index("sample_id").loc[wc.sample, "fasta"]
    output:
        directory("results/biosafety/{sample}/amrfinder")
    log:
        "results/logs/biosafety/{sample}.amrfinder.log"
    conda:
        "../envs/amrfinder.yaml"
    shell:
        "mkdir -p {output} results/logs/biosafety && "
        "command -v amrfinder >/dev/null 2>&1 || "
        "(echo 'ERROR: AMRFinderPlus not found or database is missing. Install ncbi-amrfinderplus or run with --config mode=mock.' >&2; exit 127) && "
        "amrfinder -n {input.fasta} --output {output}/{wildcards.sample}.amrfinder.tsv > {log} 2>&1"

rule vfdb_placeholder:
    input:
        fasta=lambda wc: pd.read_csv("config/samples.tsv", sep="\t").set_index("sample_id").loc[wc.sample, "fasta"]
    output:
        directory("results/biosafety/{sample}/vfdb")
    log:
        "results/logs/biosafety/{sample}.vfdb.log"
    conda:
        "../envs/core.yaml"
    shell:
        "mkdir -p {output} results/logs/biosafety && echo 'placeholder: VFDB BLAST/HMM screen' > {log}"
