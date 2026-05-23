from plant_bacteria_match.biosafety import compute_biosafety_penalty, detect_risky_genus


def test_risky_genus_correctly_detected() -> None:
    assert detect_risky_genus("Klebsiella", "variicola")
    assert detect_risky_genus("Enterobacter", "cloacae")
    assert detect_risky_genus("Serratia", "marcescens")
    assert detect_risky_genus("Burkholderia", "cepacia")
    assert detect_risky_genus("Pseudomonas", "aeruginosa group")
    assert detect_risky_genus("Stenotrophomonas", "maltophilia")
    assert detect_risky_genus("Acinetobacter", "baumannii")
    assert not detect_risky_genus("Bacillus", "velezensis")
    assert not detect_risky_genus("Paraburkholderia", "phytofirmans")


def test_high_biosafety_penalty_with_pathogen_and_amr() -> None:
    penalty = compute_biosafety_penalty(
        amr_gene_count=4,
        virulence_gene_count=4,
        pathogen_flag=True,
        risky_genus_flag=True,
        plasmid_amr_flag=True,
        strictness="high",
    )
    assert penalty > 20

