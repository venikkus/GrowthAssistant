import pandas as pd

from pgpb_pipeline.pgp_traits import extract_pgp_traits, make_trait_matrix, parse_pgpt_pred_results


def test_acds_correctly_detected() -> None:
    annotation = pd.DataFrame(
        [
            {
                "sample_id": "s1",
                "locus_tag": "LT001",
                "gene": "acdS",
                "product": "ACC deaminase",
                "db_xrefs": "Bakta",
            }
        ]
    )
    traits = extract_pgp_traits(annotation)
    hit = traits[traits["trait_category"] == "ACC_deaminase"].iloc[0]
    assert hit["gene_or_marker"] == "acdS"
    assert hit["locus_tag"] == "LT001"
    assert hit["confidence"] == "high"


def test_nif_genes_correctly_detected() -> None:
    annotation = pd.DataFrame(
        [
            {"sample_id": "s1", "locus_tag": "LT010", "gene": "nifH", "product": "nitrogenase iron protein", "db_xrefs": ""},
            {"sample_id": "s1", "locus_tag": "LT011", "gene": "nifD", "product": "nitrogenase molybdenum-iron protein", "db_xrefs": ""},
            {"sample_id": "s1", "locus_tag": "LT012", "gene": "nifK", "product": "nitrogenase molybdenum-iron protein", "db_xrefs": ""},
        ]
    )
    traits = extract_pgp_traits(annotation)
    nif_hits = traits[traits["trait_category"] == "nitrogen_fixation"]
    assert set(nif_hits["locus_tag"]) == {"LT010", "LT011", "LT012"}
    assert set(nif_hits["confidence"]) == {"high"}


def test_pqq_gcd_combination_increases_confidence() -> None:
    annotation = pd.DataFrame(
        [
            {"sample_id": "s1", "locus_tag": "LT020", "gene": "gcd", "product": "glucose dehydrogenase", "db_xrefs": ""},
            {"sample_id": "s1", "locus_tag": "LT021", "gene": "pqqC", "product": "pyrroloquinoline quinone biosynthesis protein", "db_xrefs": ""},
        ]
    )
    traits = extract_pgp_traits(annotation)
    phosphate = traits[traits["trait_category"] == "phosphate_solubilization"]
    assert {"gcd", "pqq"} <= set(phosphate["gene_or_marker"])
    assert set(phosphate["confidence"]) == {"high"}


def test_siderophore_antismash_cluster_detected() -> None:
    annotation = pd.DataFrame(columns=["sample_id", "locus_tag", "gene", "product", "db_xrefs"])
    bgc = pd.DataFrame(
        [
            {
                "sample_id": "s1",
                "region": "region_1",
                "bgc_type": "siderophore",
                "product": "siderophore-like",
                "potential_role": "siderophore",
            }
        ]
    )
    traits = extract_pgp_traits(annotation, antismash_df=bgc)
    hit = traits[traits["trait_category"] == "siderophore"].iloc[0]
    assert hit["evidence_type"] == "antismash_cluster"
    assert hit["confidence"] == "high"


def test_virulence_amr_genes_are_not_counted_as_positive_pgp_traits() -> None:
    annotation = pd.DataFrame(
        [
            {"sample_id": "s1", "locus_tag": "LT100", "gene": "blaACT", "product": "beta-lactamase antibiotic resistance protein", "db_xrefs": ""},
            {"sample_id": "s1", "locus_tag": "LT101", "gene": "hlyA", "product": "hemolysin virulence factor", "db_xrefs": ""},
            {"sample_id": "s1", "locus_tag": "LT102", "gene": "acrB", "product": "multidrug resistance efflux pump", "db_xrefs": ""},
        ]
    )
    traits = extract_pgp_traits(annotation)
    assert traits.empty


def test_trait_matrix_uses_required_category_names() -> None:
    annotation = pd.DataFrame(
        [{"sample_id": "s1", "locus_tag": "LT001", "gene": "acdS", "product": "ACC deaminase", "db_xrefs": ""}]
    )
    matrix = make_trait_matrix(extract_pgp_traits(annotation))
    assert matrix.loc[0, "ACC_deaminase"] == 1


def test_pgpt_pred_import_parser(tmp_path) -> None:
    path = tmp_path / "s1.tsv"
    path.write_text(
        "sample_id\tprotein_id\tgene\ttrait\tscore\tdescription\n"
        "s1\tprot1\tacdS\tACC deaminase\t0.95\tPGPT hit\n"
        "s1\tprot2\tpqqC\tphosphate solubilization\t0.7\tPGPT hit\n",
        encoding="utf-8",
    )
    traits = parse_pgpt_pred_results(path, "s1")
    assert {"ACC_deaminase", "phosphate_solubilization"} <= set(traits["trait_category"])
    assert set(traits["source_tool"]) == {"PGPT-Pred/PLaBAse"}
    assert "pgpt_pred_import" in set(traits["evidence_type"])
