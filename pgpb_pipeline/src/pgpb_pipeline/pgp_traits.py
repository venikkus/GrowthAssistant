"""Plant growth-promoting trait extraction from annotation and BGC tables."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
import pandas as pd

from pgpb_pipeline.io import safe_read_table

OUTPUT_COLUMNS = [
    "sample_id",
    "trait_category",
    "trait_name",
    "gene_or_marker",
    "locus_tag",
    "evidence_type",
    "source_tool",
    "confidence",
    "description",
]

EXCLUDED_POSITIVE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\b(beta[- ]?lactamase|bla[A-Z0-9_-]*)\b",
        r"\b(qnr|tet[A-Z]?|erm[A-Z]?|sul[0-9]?|aac|aph|ant)\b",
        r"\b(amr|antibiotic resistance|multidrug resistance|efflux pump)\b",
        r"\b(virulence|toxin|hemolysin|invasion|type\s*(iii|3)\s*secretion)\b",
    ]
]


@dataclass(frozen=True)
class MarkerRule:
    trait_category: str
    trait_name: str
    marker: str
    exact_genes: tuple[str, ...] = ()
    product_patterns: tuple[str, ...] = ()
    keyword_patterns: tuple[str, ...] = ()
    confidence: str = "medium"


MARKER_RULES: tuple[MarkerRule, ...] = (
    MarkerRule(
        "ACC_deaminase",
        "ACC deaminase",
        "acdS",
        exact_genes=("acds",),
        product_patterns=(r"\bacc\s+deaminase\b", r"\b1-aminocyclopropane-1-carboxylate deaminase\b"),
        confidence="high",
    ),
    MarkerRule(
        "nitrogen_fixation",
        "nitrogen fixation",
        "nifHDK",
        exact_genes=("nifh", "nifd", "nifk", "nife", "nifn", "vnfh", "anfh"),
        product_patterns=(r"\bnitrogenase\b", r"\bnif[HDKEN]\b"),
        confidence="high",
    ),
    MarkerRule(
        "phosphate_solubilization",
        "phosphate solubilization",
        "gcd",
        exact_genes=("gcd",),
        product_patterns=(r"\bglucose dehydrogenase\b",),
        confidence="medium",
    ),
    MarkerRule(
        "phosphate_solubilization",
        "phosphate solubilization",
        "pqq",
        exact_genes=("pqqa", "pqqb", "pqqc", "pqqd", "pqqe", "pqqf", "pqqg"),
        product_patterns=(r"\bpyrroloquinoline quinone\b", r"\bpqq[A-G]?\b"),
        confidence="medium",
    ),
    MarkerRule(
        "phosphate_solubilization",
        "phosphate solubilization",
        "phosphatase/pho",
        exact_genes=("phoa", "phod", "phox", "phou", "phor", "phob"),
        product_patterns=(r"\b(alkaline|acid)\s+phosphatase\b", r"\bphosphatase\b"),
        confidence="medium",
    ),
    MarkerRule(
        "phytohormone_IAA",
        "IAA phytohormone biosynthesis",
        "ipdC",
        exact_genes=("ipdc",),
        product_patterns=(r"\bindole-3-pyruvate decarboxylase\b",),
        confidence="high",
    ),
    MarkerRule(
        "phytohormone_IAA",
        "IAA phytohormone biosynthesis",
        "iaaM/iaaH",
        exact_genes=("iaam", "iaah"),
        product_patterns=(r"\bindole-3-acetamide\b", r"\btryptophan monooxygenase\b"),
        confidence="medium",
    ),
    MarkerRule(
        "phytohormone_IAA",
        "IAA phytohormone biosynthesis",
        "tryptophan metabolism",
        product_patterns=(r"\btryptophan\b.*\b(indole|auxin|iaa)\b",),
        keyword_patterns=(r"\bindole-3-acetic acid\b",),
        confidence="low",
    ),
    MarkerRule(
        "siderophore",
        "siderophore production",
        "siderophore",
        product_patterns=(r"\bsiderophore\b", r"\benterobactin\b", r"\bpyoverdine\b", r"\baerobactin\b"),
        confidence="medium",
    ),
    MarkerRule(
        "EPS_biofilm",
        "EPS and biofilm formation",
        "EPS/biofilm",
        exact_genes=("epsa", "epsb", "epsc", "epsd", "pelA".lower(), "pslA".lower()),
        product_patterns=(r"\bexopolysaccharide\b", r"\bbiofilm\b", r"\bcellulose\b"),
        keyword_patterns=(r"\bEPS\b",),
        confidence="medium",
    ),
    MarkerRule(
        "root_colonization",
        "root colonization",
        "motility/chemotaxis/pili",
        exact_genes=("flic", "flgb", "flgc", "chea", "chew", "chey", "pilA".lower(), "fimA".lower()),
        product_patterns=(r"\bflagell", r"\bchemotaxis\b", r"\bpilus\b", r"\bpili\b", r"\bfimbr"),
        confidence="medium",
    ),
    MarkerRule(
        "stress_tolerance",
        "stress tolerance",
        "osmoprotection/cold stress",
        exact_genes=("otsa", "otsb", "trez", "betc", "betb", "ectA".lower(), "ectB".lower(), "ectC".lower(), "cspA".lower()),
        product_patterns=(
            r"\btrehalose\b",
            r"\bglycine betaine\b",
            r"\bectoine\b",
            r"\bosmoprotect",
            r"\bcold[- ]shock protein\b",
        ),
        confidence="medium",
    ),
    MarkerRule(
        "biocontrol",
        "biocontrol",
        "lytic enzyme/protease",
        product_patterns=(r"\bchitinase\b", r"\bglucanase\b", r"\bprotease\b", r"\bantifungal\b"),
        confidence="medium",
    ),
    MarkerRule(
        "potassium_zinc_solubilization",
        "potassium/zinc solubilization",
        "mineral solubilization",
        product_patterns=(r"\bpotassium solubil", r"\bzinc solubil", r"\bgluconic acid\b"),
        keyword_patterns=(r"\bk-solubil", r"\bzn-solubil"),
        confidence="low",
    ),
)

ANTISMASH_BGC_MAPPING: dict[str, tuple[str, str, str]] = {
    "siderophore": ("siderophore", "siderophore production", "high"),
    "bacteriocin": ("biocontrol", "biocontrol", "medium"),
    "lanthipeptide": ("biocontrol", "biocontrol", "medium"),
    "nrps": ("biocontrol", "biocontrol", "medium"),
    "t1pks": ("biocontrol", "biocontrol", "medium"),
    "t2pks": ("biocontrol", "biocontrol", "medium"),
    "t3pks": ("biocontrol", "biocontrol", "medium"),
    "terpene": ("stress_tolerance", "stress tolerance", "low"),
}

PGPT_TRAIT_ALIASES = {
    "nitrogen": ("nitrogen_fixation", "nitrogen fixation"),
    "n fixation": ("nitrogen_fixation", "nitrogen fixation"),
    "phosphate": ("phosphate_solubilization", "phosphate solubilization"),
    "phosphorus": ("phosphate_solubilization", "phosphate solubilization"),
    "iaa": ("phytohormone_IAA", "IAA phytohormone biosynthesis"),
    "auxin": ("phytohormone_IAA", "IAA phytohormone biosynthesis"),
    "acc": ("ACC_deaminase", "ACC deaminase"),
    "siderophore": ("siderophore", "siderophore production"),
    "biofilm": ("EPS_biofilm", "EPS and biofilm formation"),
    "eps": ("EPS_biofilm", "EPS and biofilm formation"),
    "colonization": ("root_colonization", "root colonization"),
    "motility": ("root_colonization", "root colonization"),
    "stress": ("stress_tolerance", "stress tolerance"),
    "osmotic": ("stress_tolerance", "stress tolerance"),
    "biocontrol": ("biocontrol", "biocontrol"),
    "antagon": ("biocontrol", "biocontrol"),
    "potassium": ("potassium_zinc_solubilization", "potassium/zinc solubilization"),
    "zinc": ("potassium_zinc_solubilization", "potassium/zinc solubilization"),
}


def _norm(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _norm_gene(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", _norm(value).lower())


def _is_excluded_positive(text: str) -> bool:
    return any(pattern.search(text) for pattern in EXCLUDED_POSITIVE_PATTERNS)


def _annotation_source_tool(row: pd.Series) -> str:
    db_xrefs = _norm(row.get("db_xrefs"))
    if "eggnog" in db_xrefs.lower() or "cog" in db_xrefs.lower():
        return "eggnog"
    if "bakta" in db_xrefs.lower():
        return "bakta"
    return "annotation"


def _match_rule(row: pd.Series, rule: MarkerRule) -> tuple[bool, str]:
    gene = _norm_gene(row.get("gene"))
    locus_tag = _norm(row.get("locus_tag"))
    product = _norm(row.get("product"))
    db_xrefs = _norm(row.get("db_xrefs"))
    text = " ".join([gene, locus_tag, product, db_xrefs])
    if _is_excluded_positive(text):
        return False, ""
    if gene and gene in rule.exact_genes:
        return True, "exact_gene"
    for pattern in rule.product_patterns:
        if re.search(pattern, product, flags=re.IGNORECASE):
            return True, "annotation_keyword"
    for pattern in rule.keyword_patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True, "annotation_keyword"
    return False, ""


def _boost_phosphate_confidence(rows: list[dict[str, str]]) -> None:
    by_sample: dict[str, set[str]] = {}
    for row in rows:
        if row["trait_category"] != "phosphate_solubilization":
            continue
        by_sample.setdefault(row["sample_id"], set()).add(row["gene_or_marker"])
    for row in rows:
        markers = by_sample.get(row["sample_id"], set())
        has_gcd = "gcd" in markers
        has_pqq = "pqq" in markers
        if row["trait_category"] == "phosphate_solubilization" and has_gcd and has_pqq:
            row["confidence"] = "high"
            row["description"] = f"{row['description']} | gcd+pqq combination detected"


def extract_traits_from_annotations(annotation_df: pd.DataFrame) -> pd.DataFrame:
    """Extract PGP traits from Bakta/Prokka/eggNOG-like annotation tables."""
    rows: list[dict[str, str]] = []
    if annotation_df.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    for _, ann in annotation_df.iterrows():
        sample_id = _norm(ann.get("sample_id"))
        locus_tag = _norm(ann.get("locus_tag")) or _norm(ann.get("gene_id"))
        gene = _norm(ann.get("gene"))
        product = _norm(ann.get("product"))
        for rule in MARKER_RULES:
            matched, evidence_type = _match_rule(ann, rule)
            if not matched:
                continue
            rows.append(
                {
                    "sample_id": sample_id,
                    "trait_category": rule.trait_category,
                    "trait_name": rule.trait_name,
                    "gene_or_marker": rule.marker,
                    "locus_tag": locus_tag,
                    "evidence_type": evidence_type,
                    "source_tool": _annotation_source_tool(ann),
                    "confidence": rule.confidence,
                    "description": f"{gene or locus_tag}: {product}".strip(": "),
                }
            )
    _boost_phosphate_confidence(rows)
    return _deduplicate(pd.DataFrame(rows, columns=OUTPUT_COLUMNS))


def extract_traits_from_antismash(sample_id: str, antismash_df: pd.DataFrame | None) -> pd.DataFrame:
    """Extract PGP trait evidence from antiSMASH BGC summaries."""
    rows: list[dict[str, str]] = []
    if antismash_df is None or antismash_df.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    for _, bgc in antismash_df.iterrows():
        text = " ".join(
            _norm(bgc.get(column))
            for column in ["bgc_type", "product", "potential_role", "region", "coordinates"]
        )
        text_norm = text.lower()
        for bgc_key, (category, trait_name, confidence) in ANTISMASH_BGC_MAPPING.items():
            if bgc_key not in text_norm:
                continue
            rows.append(
                {
                    "sample_id": _norm(bgc.get("sample_id")) or sample_id,
                    "trait_category": category,
                    "trait_name": trait_name,
                    "gene_or_marker": bgc_key,
                    "locus_tag": "",
                    "evidence_type": "antismash_cluster",
                    "source_tool": "antismash",
                    "confidence": confidence,
                    "description": text,
                }
            )
    return _deduplicate(pd.DataFrame(rows, columns=OUTPUT_COLUMNS))


def extract_pgp_traits(
    annotation_df: pd.DataFrame,
    protein_fasta: str | Path | None = None,
    antismash_df: pd.DataFrame | None = None,
    external_pgp_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Extract PGP traits from annotations and optional BGC/external trait tables.

    The optional protein FASTA is accepted for API stability and future HMM searches;
    this MVP does not scan sequences directly.
    """
    _ = protein_fasta
    frames = [extract_traits_from_annotations(annotation_df)]
    sample_ids = annotation_df["sample_id"].dropna().astype(str).unique().tolist() if "sample_id" in annotation_df else [""]
    for sample_id in sample_ids or [""]:
        frames.append(extract_traits_from_antismash(sample_id, antismash_df))
    if external_pgp_df is not None and not external_pgp_df.empty:
        frames.append(external_pgp_df.reindex(columns=OUTPUT_COLUMNS))
    combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=OUTPUT_COLUMNS)
    return _deduplicate(combined.reindex(columns=OUTPUT_COLUMNS))


def parse_pgpt_pred_results(path: str | Path, sample_id: str | None = None) -> pd.DataFrame:
    """Parse optional manually downloaded PGPT-Pred/PLaBAse result tables.

    The public PGPT-Pred endpoint is a web form, so the reproducible MVP expects
    users to place downloaded result TSV/CSV files under data/external/pgpt_pred.
    This parser is intentionally permissive about column names.
    """
    df = safe_read_table(path)
    if df.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    lower = {str(col).strip().lower(): col for col in df.columns}

    def col(*names: str) -> str | None:
        for name in names:
            if name in lower:
                return lower[name]
        return None

    sample_col = col("sample_id", "sample", "genome", "strain")
    locus_col = col("locus_tag", "protein_id", "query", "query_id", "sequence_id", "id")
    gene_col = col("gene", "marker", "gene_or_marker")
    trait_col = col("trait_category", "trait", "prediction", "predicted_trait", "pgp_trait", "class")
    conf_col = col("confidence", "confidence_level")
    score_col = col("score", "probability", "confidence_score")
    desc_col = col("description", "function", "annotation", "product")

    rows: list[dict[str, str]] = []
    for _, row in df.iterrows():
        raw_trait = _norm(row.get(trait_col)) if trait_col else ""
        gene = _norm(row.get(gene_col)) if gene_col else ""
        desc = _norm(row.get(desc_col)) if desc_col else raw_trait
        combined_text = " ".join([raw_trait, gene, desc]).lower()
        if _is_excluded_positive(combined_text):
            continue
        category, trait_name = _map_pgpt_trait(combined_text)
        if not category:
            continue
        confidence = _pgpt_confidence(row.get(conf_col) if conf_col else None, row.get(score_col) if score_col else None)
        rows.append(
            {
                "sample_id": _norm(row.get(sample_col)) if sample_col else (sample_id or ""),
                "trait_category": category,
                "trait_name": trait_name,
                "gene_or_marker": gene or raw_trait or category,
                "locus_tag": _norm(row.get(locus_col)) if locus_col else "",
                "evidence_type": "pgpt_pred_import",
                "source_tool": "PGPT-Pred/PLaBAse",
                "confidence": confidence,
                "description": desc or raw_trait,
            }
        )
    return _deduplicate(pd.DataFrame(rows, columns=OUTPUT_COLUMNS))


def _map_pgpt_trait(text: str) -> tuple[str, str]:
    for key, value in PGPT_TRAIT_ALIASES.items():
        if key in text:
            return value
    for rule in MARKER_RULES:
        pseudo = pd.Series({"gene": text, "product": text, "db_xrefs": ""})
        matched, _ = _match_rule(pseudo, rule)
        if matched:
            return rule.trait_category, rule.trait_name
    return "", ""


def _pgpt_confidence(confidence: object, score: object) -> str:
    conf = _norm(confidence).lower()
    if conf in {"high", "medium", "low"}:
        return conf
    try:
        value = float(score)
    except (TypeError, ValueError):
        return "medium"
    if value > 1:
        value = value / 100
    if value >= 0.8:
        return "high"
    if value >= 0.5:
        return "medium"
    return "low"


def detect_pgp_traits(
    sample_id: str,
    functional_df: pd.DataFrame,
    antismash_df: pd.DataFrame | None = None,
    external_pgp_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Backward-compatible wrapper used by the workflow aggregation code."""
    annotation_df = _coerce_annotation_table(functional_df, sample_id)
    return extract_pgp_traits(annotation_df, antismash_df=antismash_df, external_pgp_df=external_pgp_df)


def _coerce_annotation_table(df: pd.DataFrame, sample_id: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["sample_id", "locus_tag", "gene", "product", "db_xrefs"])
    coerced = pd.DataFrame()
    coerced["sample_id"] = df.get("sample_id", pd.Series([sample_id] * len(df))).fillna(sample_id)
    coerced["locus_tag"] = df.get("locus_tag", df.get("gene_id", pd.Series([""] * len(df))))
    coerced["gene"] = df.get("gene", pd.Series([""] * len(df)))
    coerced["product"] = df.get("product", pd.Series([""] * len(df)))
    coerced["db_xrefs"] = df.get("db_xrefs", pd.Series([""] * len(df)))
    return coerced


def _deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    return (
        df.drop_duplicates(
            subset=[
                "sample_id",
                "trait_category",
                "gene_or_marker",
                "locus_tag",
                "evidence_type",
                "source_tool",
            ]
        )
        .sort_values(["sample_id", "trait_category", "confidence", "gene_or_marker"])
        .reset_index(drop=True)
    )


def make_trait_matrix(pgp_long_df: pd.DataFrame) -> pd.DataFrame:
    if pgp_long_df.empty:
        return pd.DataFrame(columns=["sample_id"])
    matrix = (
        pgp_long_df.assign(value=1)
        .pivot_table(index="sample_id", columns="trait_category", values="value", aggfunc="sum", fill_value=0)
        .reset_index()
    )
    matrix.columns.name = None
    return matrix


def summarize_pgp_traits(pgp_long_df: pd.DataFrame) -> pd.DataFrame:
    if pgp_long_df.empty:
        return pd.DataFrame(columns=["sample_id", "trait_count", "high_confidence_count", "low_confidence_count"])
    return (
        pgp_long_df.groupby("sample_id")
        .agg(
            trait_count=("gene_or_marker", "count"),
            high_confidence_count=("confidence", lambda s: int((s == "high").sum())),
            low_confidence_count=("confidence", lambda s: int((s == "low").sum())),
        )
        .reset_index()
    )
