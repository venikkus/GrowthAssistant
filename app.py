"""Streamlit UI for PlantBacteriaMatch."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from plant_bacteria_match.io import load_demo_dataset
from plant_bacteria_match.models import PlantProfile
from plant_bacteria_match.recommender import recommend_strains
from plant_bacteria_match.reporting import generate_markdown_report
from plant_bacteria_match.visualization import plot_ranked_scores, plot_trait_profile

ROOT = Path(__file__).resolve().parent
DEMO_DIR = ROOT / "data" / "demo"


def _plant_from_row(row: pd.Series) -> PlantProfile:
    data = row.to_dict()
    return PlantProfile(**data)


st.set_page_config(page_title="PlantBacteriaMatch", layout="wide")
st.title("PlantBacteriaMatch — PGPR/PGPB candidate recommender")
st.caption(
    "Prototype assistant for narrowing bacterial strain candidates for lab, greenhouse, "
    "and field validation."
)

dataset = load_demo_dataset(DEMO_DIR)
plants_df = dataset["plant_profiles"]

with st.sidebar:
    st.header("Candidate search")
    plant_name = st.selectbox("Plant", plants_df["plant_name"].tolist())
    selected_problem = st.selectbox(
        "Stress/problem",
        [
            "drought",
            "salinity",
            "phosphorus_deficiency",
            "nitrogen_limitation",
            "pathogen_pressure",
            "cold_stress",
            "heavy_metals",
        ],
    )
    pathogen = st.text_input("Optional pathogen", "")
    strictness = st.select_slider("Biosafety strictness", options=["low", "medium", "high"], value="medium")

plant_profile = _plant_from_row(plants_df[plants_df["plant_name"] == plant_name].iloc[0])
if pathogen:
    plant_profile.target_pathogens = sorted(set(plant_profile.target_pathogens + [pathogen]))

recommendations = recommend_strains(
    plant_profile=plant_profile,
    selected_problem=selected_problem,
    strains_df=dataset["strains"],
    traits_df=dataset["pgp_traits"],
    biosafety_df=dataset["biosafety"],
    literature_df=dataset["literature_evidence"],
    strictness=strictness,
)

left, right = st.columns([1.2, 1])
with left:
    st.subheader(f"{plant_profile.plant_name} profile")
    st.write(
        {
            "Scientific name": plant_profile.scientific_name,
            "Crop group": plant_profile.crop_group,
            "Target stresses": ", ".join(plant_profile.target_stresses),
            "Target pathogens": ", ".join(plant_profile.target_pathogens),
            "Nutrient limits": ", ".join(plant_profile.target_nutrient_limits),
            "Region": plant_profile.region,
            "Soil pH": plant_profile.soil_pH,
        }
    )
with right:
    st.subheader("Biosafety principle")
    st.info(
        "Biosafety screening is mandatory. Pathogen flags or high virulence burden "
        "cap candidates below A/B even when PGP traits look strong."
    )

ranked_df = pd.DataFrame([rec.model_dump() for rec in recommendations])

strain_lookup_cols = [
    "strain_id",
    "strain_name",
    "genus",
    "species",
    "host_plant",
    "region",
    "genome_accession",
    "notes",
]

strain_lookup = dataset["strains"][
    [col for col in strain_lookup_cols if col in dataset["strains"].columns]
].copy()

ranked_df = ranked_df.merge(strain_lookup, on="strain_id", how="left")

if "strain_name" not in ranked_df.columns:
    ranked_df["strain_name"] = ranked_df["strain_id"]

ranked_df["display_name"] = ranked_df["strain_name"].fillna(ranked_df["strain_id"])

st.subheader("Ranked bacterial strains")

visible_columns = [
    "display_name",
    "strain_id",
    "final_score",
    "recommendation_class",
    "evidence_level",
    "strengths",
    "risks",
    "missing_data",
]

visible_columns = [col for col in visible_columns if col in ranked_df.columns]

display_df = ranked_df[visible_columns].rename(
    columns={
        "display_name": "strain_name",
    }
)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)

st.subheader("Top-3 candidate details")

top3_details = ranked_df.head(3)[
    [
        "display_name",
        "strain_id",
        "host_plant",
        "region",
        "genome_accession",
        "notes",
    ]
].rename(
    columns={
        "display_name": "strain_name",
    }
)

st.dataframe(top3_details, use_container_width=True, hide_index=True)

st.plotly_chart(plot_ranked_scores(recommendations), use_container_width=True)
top_ids = ranked_df.head(5)["strain_id"].tolist()
st.plotly_chart(plot_trait_profile(dataset["pgp_traits"], top_ids), use_container_width=True)

st.subheader("Explanations")
for rec in recommendations:
    with st.expander(f"{rec.strain_id} | class {rec.recommendation_class} | score {rec.final_score:.2f}"):
        st.write(rec.explanation)
        st.markdown("**Strengths**")
        st.write(rec.strengths or ["No major strengths in demo data"])
        st.markdown("**Risks**")
        st.write(rec.risks or ["No demo biosafety warnings"])
        st.markdown("**Missing data**")
        st.write(rec.missing_data or ["None flagged"])

st.subheader("Biosafety warnings")
warning_rows = [
    {"strain_id": rec.strain_id, "class": rec.recommendation_class, "warnings": "; ".join(rec.risks)}
    for rec in recommendations
    if rec.risks
]
st.dataframe(pd.DataFrame(warning_rows), use_container_width=True, hide_index=True)

st.subheader("Suggested validation tests")
validation_rows = [
    {
        "strain_id": rec.strain_id,
        "tests": "; ".join(rec.suggested_validation_tests),
    }
    for rec in recommendations[:8]
]
st.dataframe(pd.DataFrame(validation_rows), use_container_width=True, hide_index=True)

report = generate_markdown_report(plant_profile, selected_problem, recommendations)
st.download_button(
    "Export report to Markdown",
    data=report,
    file_name=f"plant_bacteria_match_{plant_profile.plant_name}_{selected_problem}.md",
    mime="text/markdown",
)
st.download_button(
    "Export report to HTML",
    data=report.replace("\n", "<br>\n"),
    file_name=f"plant_bacteria_match_{plant_profile.plant_name}_{selected_problem}.html",
    mime="text/html",
)
