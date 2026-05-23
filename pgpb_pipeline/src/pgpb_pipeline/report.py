"""Markdown and HTML report generation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def _table(df: pd.DataFrame) -> str:
    if df.empty:
        return "No rows."
    view = df.fillna("NA").astype(str)
    headers = list(view.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(row[col].replace("|", "/") for col in headers) + " |")
    return "\n".join(lines)


def _html(markdown: str) -> str:
    body = markdown.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    body = body.replace("\n", "<br>\n")
    return f"<!doctype html><html><head><meta charset='utf-8'><title>PGPB report</title></head><body>{body}</body></html>"


def sample_report(
    sample_id: str,
    ranking_row: pd.Series,
    qc_df: pd.DataFrame,
    taxonomy_df: pd.DataFrame,
    pgp_df: pd.DataFrame,
    bgc_df: pd.DataFrame,
    biosafety_df: pd.DataFrame,
    plasmid_df: pd.DataFrame,
    crispr_df: pd.DataFrame,
    phage_df: pd.DataFrame,
) -> str:
    lines = [
        f"# PGPB genome report: {sample_id}",
        "",
        "**Prototype output. Candidates require laboratory, greenhouse, field, and biosafety validation.**",
        "",
        "## Final recommendation",
        "",
        f"- Status: {ranking_row.get('recommended_status', 'NA')}",
        f"- Confidence: {ranking_row.get('confidence_level', 'NA')}",
        f"- Final score: {ranking_row.get('final_score', 'NA')}",
        f"- Validation plan: {ranking_row.get('recommended_validation_tests', 'NA')}",
        "",
        "## Taxonomy",
        "",
        _table(taxonomy_df[taxonomy_df["sample_id"] == sample_id]),
        "",
        "## Genome QC",
        "",
        _table(qc_df[qc_df["sample_id"] == sample_id]),
        "",
        "## PGP traits",
        "",
        _table(pgp_df[pgp_df["sample_id"] == sample_id]) if not pgp_df.empty else "No PGP markers detected.",
        "",
        "## Secondary metabolites",
        "",
        _table(bgc_df[bgc_df["sample_id"] == sample_id]) if not bgc_df.empty else "No BGC summary available.",
        "",
        "## Biosafety risks",
        "",
        _table(biosafety_df[biosafety_df["sample_id"] == sample_id]),
        "",
        "## Plasmids/mobile elements",
        "",
        _table(plasmid_df[plasmid_df["sample_id"] == sample_id]) if not plasmid_df.empty else "No plasmid summary available.",
        "",
        "## CRISPR/phage",
        "",
        _table(crispr_df[crispr_df["sample_id"] == sample_id]) if not crispr_df.empty else "No CRISPR summary available.",
        "",
        _table(phage_df[phage_df["sample_id"] == sample_id]) if not phage_df.empty else "No phage summary available.",
    ]
    return "\n".join(lines)


def write_reports(results_dir: str | Path) -> None:
    results_dir = Path(results_dir)
    tables = results_dir / "tables"
    reports = results_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    ranking = pd.read_csv(tables / "final_ranking.tsv", sep="\t")
    qc = pd.read_csv(tables / "qc_summary.tsv", sep="\t")
    taxonomy = pd.read_csv(tables / "taxonomy_summary.tsv", sep="\t")
    pgp = pd.read_csv(tables / "pgp_traits_long.tsv", sep="\t")
    bgc = pd.read_csv(tables / "bgc_summary.tsv", sep="\t")
    biosafety = pd.read_csv(tables / "biosafety_summary.tsv", sep="\t")
    plasmid = pd.read_csv(tables / "plasmid_summary.tsv", sep="\t")
    crispr = pd.read_csv(tables / "crispr_summary.tsv", sep="\t")
    phage = pd.read_csv(tables / "phage_summary.tsv", sep="\t")

    final_lines = [
        "# PGPB pipeline final report",
        "",
        "**This MVP ranking is not a biological recommendation. All candidates require validation.**",
        "",
        "## Final ranking",
        "",
        _table(ranking),
        "",
    ]
    for _, row in ranking.iterrows():
        md = sample_report(row["sample_id"], row, qc, taxonomy, pgp, bgc, biosafety, plasmid, crispr, phage)
        (reports / f"{row['sample_id']}.md").write_text(md, encoding="utf-8")
        (reports / f"{row['sample_id']}.html").write_text(_html(md), encoding="utf-8")
        final_lines.extend(["", f"## {row['sample_id']}", "", row.get("top_positive_evidence", ""), "", row.get("top_risk_evidence", "")])
    final_md = "\n".join(final_lines)
    (reports / "final_report.md").write_text(final_md, encoding="utf-8")
    (reports / "final_report.html").write_text(_html(final_md), encoding="utf-8")
