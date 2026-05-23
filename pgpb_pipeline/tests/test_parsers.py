from pathlib import Path

from pgpb_pipeline.parsers.busco import parse_busco_summary
from pgpb_pipeline.parsers.quast import parse_quast_report


BASE = Path(__file__).resolve().parents[1]


def test_quast_parser_reads_mock_metrics() -> None:
    df = parse_quast_report(BASE / "mock_outputs/strain_001/quast_report.tsv", "strain_001")
    assert int(df.loc[0, "num_contigs"]) == 42
    assert int(df.loc[0, "n50"]) == 210000


def test_busco_parser_reads_mock_percentages() -> None:
    df = parse_busco_summary(BASE / "mock_outputs/strain_001/busco_short_summary.txt", "strain_001")
    assert float(df.loc[0, "busco_complete"]) == 98.1
    assert float(df.loc[0, "busco_missing"]) == 1.1

