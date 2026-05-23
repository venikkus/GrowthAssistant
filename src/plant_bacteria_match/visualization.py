"""Plotly visualizations for the Streamlit app."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from plant_bacteria_match.models import Recommendation

TRAIT_COLUMNS = [
    "nitrogen_fixation_score",
    "phosphate_solubilization_score",
    "siderophore_score",
    "iaa_score",
    "acc_deaminase_score",
    "biocontrol_score",
    "stress_tolerance_score",
    "colonization_score",
    "secondary_metabolite_score",
]


def plot_ranked_scores(recommendations: list[Recommendation]) -> go.Figure:
    df = pd.DataFrame([rec.model_dump() for rec in recommendations])
    fig = px.bar(
        df,
        x="strain_id",
        y="final_score",
        color="recommendation_class",
        hover_data=["evidence_level"],
        title="Ranked candidate scores",
    )
    fig.update_layout(xaxis_title="Strain", yaxis_title="Final score")
    return fig


def plot_trait_profile(traits_df: pd.DataFrame, top_strain_ids: list[str]) -> go.Figure:
    subset = traits_df[traits_df["strain_id"].isin(top_strain_ids)]
    long_df = subset.melt(
        id_vars="strain_id",
        value_vars=TRAIT_COLUMNS,
        var_name="trait",
        value_name="score",
    )
    long_df["trait"] = long_df["trait"].str.replace("_score", "", regex=False)
    fig = px.bar(
        long_df,
        x="trait",
        y="score",
        color="strain_id",
        barmode="group",
        title="PGP trait profile for top candidates",
    )
    fig.update_layout(xaxis_title="Trait", yaxis_title="Normalized score")
    return fig

