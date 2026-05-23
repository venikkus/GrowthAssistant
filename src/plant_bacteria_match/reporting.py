"""Report generation helpers."""

from __future__ import annotations

from pathlib import Path

from plant_bacteria_match.models import PlantProfile, Recommendation


def generate_markdown_report(
    plant_profile: PlantProfile,
    selected_problem: str,
    recommendations: list[Recommendation],
) -> str:
    lines = [
        "# PlantBacteriaMatch report",
        "",
        "**Demo/prototype output. Not an agronomic prescription.**",
        "",
        f"- Plant: {plant_profile.plant_name} ({plant_profile.scientific_name})",
        f"- Problem: {selected_problem}",
        f"- Crop group: {plant_profile.crop_group}",
        "",
        "## Ranked candidates",
        "",
        "| Rank | Strain | Score | Class | Evidence | Key risks |",
        "|---:|---|---:|:---:|---|---|",
    ]
    for rank, rec in enumerate(recommendations, start=1):
        risks = "; ".join(rec.risks[:2]) if rec.risks else "No demo warnings"
        lines.append(
            f"| {rank} | {rec.strain_id} | {rec.final_score:.2f} | "
            f"{rec.recommendation_class} | {rec.evidence_level} | {risks} |"
        )
    lines.extend(["", "## Explanations", ""])
    for rec in recommendations:
        lines.extend(
            [
                f"### {rec.strain_id}",
                "",
                rec.explanation,
                "",
                f"- Strengths: {', '.join(rec.strengths) or 'none in demo data'}",
                f"- Missing data: {', '.join(rec.missing_data) or 'none flagged'}",
                f"- Suggested validation: {', '.join(rec.suggested_validation_tests)}",
                "",
            ]
        )
    return "\n".join(lines)


def save_report(report: str, path: str | Path) -> None:
    Path(path).write_text(report, encoding="utf-8")

