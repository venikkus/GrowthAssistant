from pathlib import Path

from plant_bacteria_match.io import load_demo_dataset
from plant_bacteria_match.models import PlantProfile
from plant_bacteria_match.recommender import recommend_strains


def test_recommender_returns_ranked_recommendations() -> None:
    data = load_demo_dataset(Path("data/demo"))
    plant = PlantProfile(**data["plant_profiles"].iloc[0].to_dict())
    recommendations = recommend_strains(
        plant,
        "drought",
        data["strains"],
        data["pgp_traits"],
        data["biosafety"],
        data["literature_evidence"],
    )
    assert len(recommendations) == len(data["strains"])
    assert recommendations[0].final_score >= recommendations[-1].final_score
    assert all(rec.recommendation_class in {"A", "B", "C", "D", "E"} for rec in recommendations)

