"""
analysis.py
------------
Statistical analysis logic for survey data collected via the project's
Google Form and exported/uploaded as CSV.

Expected column naming follows data_dictionary.csv (short survey codes,
e.g. B1..B10, C1..C10, D1_1..D1_5). Raw Google Forms exports use the full
question text as the header row; rename columns to these codes before
upload (see README.md), or adapt COLUMN_MAP below to your own export.
"""

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

# ---------------------------------------------------------------------------
# Construct definitions (mirrors data_dictionary.csv)
# ---------------------------------------------------------------------------
SCALES = {
    "AdoptionTAM": {
        "label": "AI Tool Adoption (TAM)",
        "cols": [f"B{i}" for i in range(1, 11)],
        "reverse": [],
    },
    "AdoptionMaturity": {
        "label": "AI Adoption Maturity",
        "cols": [f"C{i}" for i in range(1, 11)],
        "reverse": [],
    },
    "MTTD": {
        "label": "Mean Time to Detect (MTTD)",
        "cols": [f"D1_{i}" for i in range(1, 6)],
        "reverse": [],
    },
    "MTTR": {
        "label": "Mean Time to Respond (MTTR)",
        "cols": [f"D2_{i}" for i in range(1, 6)],
        "reverse": [],
    },
    "TriageAccuracy": {
        "label": "Alert Triage Accuracy",
        "cols": [f"E{i}" for i in range(1, 11)],
        "reverse": [],
    },
    "Productivity": {
        "label": "Analyst Productivity",
        "cols": [f"F{i}" for i in range(1, 11)],
        "reverse": [],
    },
    "Trust": {
        "label": "Trust in AI",
        "cols": [f"G1_{i}" for i in range(1, 9)],
        "reverse": [],
    },
    "Explainability": {
        "label": "Explainability & Transparency",
        "cols": [f"G2_{i}" for i in range(1, 9)],
        "reverse": ["G2_5"],  # reverse-worded item
    },
    "OrgFactors": {
        "label": "Organisational Factors & Challenges",
        "cols": [f"H{i}" for i in range(1, 11)],
        "reverse": [],
    },
}

DEMOGRAPHIC_COLS = {
    "A5_JobRole": "Job Role",
    "A6_YearsInCybersecurity": "Years in Cybersecurity",
    "A8_IndustrySector": "Industry Sector",
    "A9_OrganizationSize": "Organisation Size",
}

OPEN_TEXT_COLS = {
    "O1_MostValuableAIUseCase": "Most valuable AI use case",
    "O2_BiggestChallenge": "Biggest challenge",
    "O3_SuggestedImprovement": "Suggested improvement",
}


class AnalysisError(Exception):
    pass


def _cronbach_alpha(items_df: pd.DataFrame) -> float:
    items_df = items_df.dropna()
    k = items_df.shape[1]
    if k < 2 or len(items_df) < 3:
        return float("nan")
    item_vars = items_df.var(axis=0, ddof=1)
    total_var = items_df.sum(axis=1).var(ddof=1)
    if total_var == 0:
        return float("nan")
    return float((k / (k - 1)) * (1 - item_vars.sum() / total_var))


def load_csv(filepath: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(filepath)
    except Exception as exc:
        raise AnalysisError(f"Could not read CSV file: {exc}")
    if df.empty:
        raise AnalysisError("The uploaded CSV file is empty.")
    return df


def compute_composites(df: pd.DataFrame):
    """Returns (composites_df, available_scales, missing_scales_report)."""
    composites = pd.DataFrame(index=df.index)
    missing_report = []

    for key, spec in SCALES.items():
        cols_present = [c for c in spec["cols"] if c in df.columns]
        cols_missing = [c for c in spec["cols"] if c not in df.columns]
        if len(cols_present) < max(2, len(spec["cols"]) // 2):
            missing_report.append(
                f"{spec['label']}: only {len(cols_present)}/{len(spec['cols'])} "
                f"items found in the uploaded file — this construct was skipped."
            )
            continue
        sub = df[cols_present].apply(pd.to_numeric, errors="coerce")
        for rev_col in spec["reverse"]:
            if rev_col in sub.columns:
                sub[rev_col] = 6 - sub[rev_col]
        composites[key] = sub.mean(axis=1)
        if cols_missing:
            missing_report.append(
                f"{spec['label']}: {len(cols_missing)} item(s) missing "
                f"({', '.join(cols_missing)}) — composite computed from the "
                f"remaining {len(cols_present)} item(s)."
            )

    return composites, missing_report


def reliability_table(df: pd.DataFrame):
    rows = []
    for key, spec in SCALES.items():
        cols_present = [c for c in spec["cols"] if c in df.columns]
        if len(cols_present) < 2:
            continue
        sub = df[cols_present].apply(pd.to_numeric, errors="coerce")
        for rev_col in spec["reverse"]:
            if rev_col in sub.columns:
                sub[rev_col] = 6 - sub[rev_col]
        alpha = _cronbach_alpha(sub)
        rows.append({
            "construct": spec["label"],
            "items": len(cols_present),
            "mean": round(float(sub.stack().mean()), 2) if not sub.empty else None,
            "sd": round(float(sub.stack().std()), 2) if not sub.empty else None,
            "alpha": round(alpha, 3) if not np.isnan(alpha) else None,
        })
    return rows


def demographics_summary(df: pd.DataFrame):
    summary = {}
    for col, label in DEMOGRAPHIC_COLS.items():
        if col in df.columns:
            counts = df[col].value_counts(dropna=True)
            summary[label] = {
                "labels": counts.index.tolist(),
                "values": [int(v) for v in counts.values.tolist()],
            }
    return summary


def correlation_matrix(composites: pd.DataFrame):
    if composites.shape[1] < 2:
        return {"labels": [], "matrix": []}
    corr = composites.corr(method="pearson").round(2)
    return {
        "labels": corr.columns.tolist(),
        "matrix": corr.values.tolist(),
    }


def _simple_regression(y, x, data):
    valid = data[[y, x]].dropna()
    if len(valid) < 10:
        return None
    X = sm.add_constant(valid[x])
    model = sm.OLS(valid[y], X).fit()
    return {
        "beta": round(float(model.params[x]), 3),
        "r2": round(float(model.rsquared), 3),
        "f": round(float(model.fvalue), 2),
        "df": (int(model.df_model), int(model.df_resid)),
        "p": float(model.pvalues[x]),
        "n": int(len(valid)),
    }


def hypothesis_tests(composites: pd.DataFrame):
    """Run the same five-hypothesis framework used in the underlying study,
    skipping any hypothesis whose required constructs are not available."""
    results = []
    have = lambda *keys: all(k in composites.columns for k in keys)

    if have("MTTD", "AdoptionMaturity"):
        r = _simple_regression("MTTD", "AdoptionMaturity", composites)
        if r:
            results.append({
                "id": "H1",
                "statement": "AI adoption maturity is associated with faster detection (MTTD)",
                "test": "Simple regression",
                "result": f"β = {r['beta']}, R² = {r['r2']}, F({r['df'][0]},{r['df'][1]}) = {r['f']}",
                "p": r["p"],
            })

    if have("MTTR", "AdoptionMaturity"):
        r = _simple_regression("MTTR", "AdoptionMaturity", composites)
        if r:
            results.append({
                "id": "H2",
                "statement": "AI adoption maturity is associated with faster response (MTTR)",
                "test": "Simple regression",
                "result": f"β = {r['beta']}, R² = {r['r2']}, F({r['df'][0]},{r['df'][1]}) = {r['f']}",
                "p": r["p"],
            })

    if have("TriageAccuracy", "AdoptionMaturity"):
        r = _simple_regression("TriageAccuracy", "AdoptionMaturity", composites)
        if r:
            results.append({
                "id": "H3",
                "statement": "AI adoption maturity is associated with alert-triage accuracy",
                "test": "Simple regression",
                "result": f"β = {r['beta']}, R² = {r['r2']}, F({r['df'][0]},{r['df'][1]}) = {r['f']}",
                "p": r["p"],
            })

    if have("Productivity", "AdoptionMaturity"):
        valid = composites[["Productivity", "AdoptionMaturity"]].dropna()
        if len(valid) >= 10:
            rho, p = stats.pearsonr(valid["Productivity"], valid["AdoptionMaturity"])
            results.append({
                "id": "H4",
                "statement": "AI adoption maturity correlates with analyst productivity",
                "test": "Pearson correlation",
                "result": f"r = {round(rho, 3)}",
                "p": float(p),
            })

    if have("MTTD", "MTTR", "TriageAccuracy", "Productivity", "AdoptionMaturity", "Trust"):
        c = composites[["MTTD", "MTTR", "TriageAccuracy", "Productivity", "AdoptionMaturity", "Trust"]].dropna()
        if len(c) >= 15:
            c = c.copy()
            c["IREfficiency"] = c[["MTTD", "MTTR", "TriageAccuracy", "Productivity"]].mean(axis=1)
            c["AM_c"] = c["AdoptionMaturity"] - c["AdoptionMaturity"].mean()
            c["Tr_c"] = c["Trust"] - c["Trust"].mean()
            c["Interaction"] = c["AM_c"] * c["Tr_c"]
            X1 = sm.add_constant(c[["AM_c", "Tr_c"]])
            m1 = sm.OLS(c["IREfficiency"], X1).fit()
            X2 = sm.add_constant(c[["AM_c", "Tr_c", "Interaction"]])
            m2 = sm.OLS(c["IREfficiency"], X2).fit()
            delta_r2 = round(float(m2.rsquared - m1.rsquared), 3)
            results.append({
                "id": "H5",
                "statement": "Analyst trust moderates the adoption-maturity → efficiency relationship",
                "test": "Hierarchical regression",
                "result": f"ΔR² = {delta_r2}, interaction β = {round(float(m2.params['Interaction']), 3)}",
                "p": float(m2.pvalues["Interaction"]),
            })

    return results


def qualitative_themes(df: pd.DataFrame):
    """Very lightweight keyword screening of open-ended responses, if present."""
    themes = {}
    keyword_sets = {
        "O2_BiggestChallenge": ["explainab", "false positive", "tun", "train",
                                 "trust", "integrat", "cost", "skill"],
        "O1_MostValuableAIUseCase": ["triage", "detect", "correlat", "prioriti",
                                       "phishing", "anomal"],
    }
    for col, keywords in keyword_sets.items():
        if col in df.columns:
            texts = df[col].dropna().astype(str).str.lower()
            counts = {kw: int(texts.str.contains(kw).sum()) for kw in keywords}
            themes[OPEN_TEXT_COLS.get(col, col)] = counts
    return themes


def run_full_analysis(filepath: str):
    df = load_csv(filepath)
    composites, missing_report = compute_composites(df)

    if composites.empty:
        raise AnalysisError(
            "None of the expected construct columns were found in this file. "
            "Please check that your CSV columns follow the codes in "
            "data_dictionary.csv (e.g. B1..B10, C1..C10, D1_1..D1_5, ...)."
        )

    results = {
        "n_responses": int(len(df)),
        "missing_report": missing_report,
        "reliability": reliability_table(df),
        "demographics": demographics_summary(df),
        "correlation": correlation_matrix(composites),
        "hypotheses": hypothesis_tests(composites),
        "qualitative": qualitative_themes(df),
        "construct_means": {
            key: round(float(composites[key].mean()), 2)
            for key in composites.columns
            if composites[key].notna().any()
        },
    }
    return results
