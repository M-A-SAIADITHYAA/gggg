"""
Tribology Feature Engineering Module
Directly reproduces the 76 engineered features and leakage controls from Tribo.ipynb.
Supports both batch dataset engineering and real-time single-row inference.
"""

import os
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd

# Functional filler keywords mapping
LUBRICANT_KEYWORDS = [
    "ptfe", "graphite", "mos2", "molybdenum", "boron nitride", "bn", "wax", "silicone"
]
REINFORCEMENT_KEYWORDS = [
    "glass fiber", "glass fibre", "carbon fiber", "carbon fibre", "cf", "fiber", "fibre", "whisker"
]
NANOFILLER_KEYWORDS = [
    "graphene", "graphene nanoplatelet", "gnp", "cnt", "carbon nanotube", "nanotube",
    "nanoclay", "nanozeolite", "nanofiller", "nano"
]

def parse_other_ingredients(df: pd.DataFrame) -> pd.DataFrame:
    """Parse 'other_ingredients' and 'other_ingredients_wt_pct' into functional counts and weights."""
    df = df.copy()
    if "other_ingredients" not in df.columns:
        df["other_ingredients"] = ""
    df["other_ingredients"] = df["other_ingredients"].fillna("").astype(str)

    def _parse_row(row):
        names = [x.strip().lower() for x in str(row["other_ingredients"]).split(";") if x.strip()]
        raw_values = str(row.get("other_ingredients_wt_pct", "") if pd.notna(row.get("other_ingredients_wt_pct", "")) else "")
        values = [x.strip() for x in raw_values.split(";") if x.strip()]
        result = []
        for i, name in enumerate(names):
            val = 0.0
            if i < len(values):
                try:
                    val = float(values[i])
                except (ValueError, TypeError):
                    val = 0.0
            result.append((name, val))
        return result

    parsed_other = df.apply(_parse_row, axis=1)

    df["other_total_pct"] = parsed_other.apply(lambda components: sum(val for _, val in components))
    df["other_component_count"] = parsed_other.apply(len)

    df["other_lubricant_pct"] = 0.0
    df["other_reinforcement_pct"] = 0.0
    df["other_nanofiller_pct"] = 0.0
    df["other_lubricant_count"] = 0
    df["other_reinforcement_count"] = 0
    df["other_nanofiller_count"] = 0

    for idx, components in enumerate(parsed_other):
        lub_pct, reinf_pct, nano_pct = 0.0, 0.0, 0.0
        lub_count, reinf_count, nano_count = 0, 0, 0
        for name, val in components:
            name_low = name.lower()
            if any(k in name_low for k in LUBRICANT_KEYWORDS):
                lub_pct += val
                lub_count += 1
            if any(k in name_low for k in REINFORCEMENT_KEYWORDS):
                reinf_pct += val
                reinf_count += 1
            if any(k in name_low for k in NANOFILLER_KEYWORDS):
                nano_pct += val
                nano_count += 1

        row_idx = df.index[idx]
        df.loc[row_idx, "other_lubricant_pct"] = lub_pct
        df.loc[row_idx, "other_reinforcement_pct"] = reinf_pct
        df.loc[row_idx, "other_nanofiller_pct"] = nano_pct
        df.loc[row_idx, "other_lubricant_count"] = lub_count
        df.loc[row_idx, "other_reinforcement_count"] = reinf_count
        df.loc[row_idx, "other_nanofiller_count"] = nano_count

    return df


def calculate_flash_temperature(row: pd.Series) -> float:
    """Ashby/Archard interfacial flash temperature rise calculation (ΔT_flash in °C)."""
    try:
        load = float(row.get("load_N", 30.0)) if pd.notna(row.get("load_N")) else 30.0
        speed = float(row.get("speed_ms", 0.5)) if pd.notna(row.get("speed_ms")) else 0.5
        cof_approx = float(row.get("COF", 0.35)) if pd.notna(row.get("COF")) and row.get("COF") > 0 else 0.35
        # Mechanical hardness H ~ 100 MPa, thermal conductivity K_poly ~ 0.25 W/mK, K_steel ~ 45 W/mK
        a_contact = np.sqrt(max(load, 0.1) / (np.pi * 100e6))  # contact radius in meters
        k_equiv = 0.25 + 45.0  # equivalent thermal conductivity
        delta_T = (cof_approx * load * speed) / (4.0 * max(a_contact, 1e-6) * k_equiv)
        return float(np.clip(delta_T, 0.0, 350.0))
    except Exception:
        return 0.0


def engineer_tribology_features(data: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
    """
    Build domain-rich features from Tribo.ipynb and advanced physical pipeline.
    Returns engineered dataframe and feature groupings.
    """
    df = data.copy()

    # 1. Numeric conversions
    numeric_cols = [
        "pa6_pct", "pa66_pct", "glass_fiber_pct", "graphite_pct", "mos2_pct",
        "other_ingredients_wt_pct", "load_N", "speed_ms", "distance_m",
        "PV_factor", "humidity_pct", "temperature_C", "COF", "wear_rate_mm3Nm"
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # 2. Fill main composition missing values with 0
    main_comp = ["pa6_pct", "pa66_pct", "glass_fiber_pct", "graphite_pct", "mos2_pct"]
    for c in main_comp:
        if c not in df.columns:
            df[c] = 0.0
        else:
            df[c] = df[c].fillna(0.0)

    # 3. Matrix features
    df["matrix_pct"] = df["pa6_pct"] + df["pa66_pct"]
    matrix_safe = df["matrix_pct"].replace(0, np.nan)
    df["pa6_fraction"] = (df["pa6_pct"] / matrix_safe).fillna(0.0)
    df["pa66_fraction"] = (df["pa66_pct"] / matrix_safe).fillna(0.0)
    df["pa6_dominant"] = (df["pa6_pct"] > df["pa66_pct"]).astype(int)

    # 4. Main filler presence
    df["gf_present"] = (df["glass_fiber_pct"] > 0).astype(int)
    df["graphite_present"] = (df["graphite_pct"] > 0).astype(int)
    df["mos2_present"] = (df["mos2_pct"] > 0).astype(int)

    # 5. Parse Other Ingredients
    df = parse_other_ingredients(df)

    # 6. Total Fillers & Ratios
    df["known_filler_pct"] = df["glass_fiber_pct"] + df["graphite_pct"] + df["mos2_pct"]
    df["total_filler_pct"] = df["known_filler_pct"] + df["other_total_pct"]
    df["reported_composition_pct"] = df["matrix_pct"] + df["total_filler_pct"]
    df["composition_gap"] = 100.0 - df["reported_composition_pct"]

    df["filler_matrix_ratio"] = (df["total_filler_pct"] / matrix_safe).fillna(0.0)
    df["gf_matrix_ratio"] = (df["glass_fiber_pct"] / matrix_safe).fillna(0.0)
    df["graphite_matrix_ratio"] = (df["graphite_pct"] / matrix_safe).fillna(0.0)
    df["mos2_matrix_ratio"] = (df["mos2_pct"] / matrix_safe).fillna(0.0)

    total_solid_lubricant = df["graphite_pct"] + df["mos2_pct"] + df["other_lubricant_pct"]
    total_reinforcement = df["glass_fiber_pct"] + df["other_reinforcement_pct"]
    reinf_safe = total_reinforcement.replace(0, np.nan)
    df["lubricant_reinforcement_ratio"] = (total_solid_lubricant / reinf_safe).fillna(0.0)

    # 7. Hybrid / Complexity
    df["main_filler_type_count"] = df["gf_present"] + df["graphite_present"] + df["mos2_present"]
    df["filler_type_count"] = df["main_filler_type_count"] + (df["other_total_pct"] > 0).astype(int)
    df["multiple_filler_system"] = (df["filler_type_count"] >= 2).astype(int)
    df["hybrid_composite"] = (df["filler_type_count"] >= 2).astype(int)

    # 8. Operating condition features
    for c in ["load_N", "speed_ms", "distance_m", "PV_factor", "humidity_pct", "temperature_C"]:
        if c not in df.columns:
            df[c] = np.nan
        else:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df["load_speed_product"] = df["load_N"] * df["speed_ms"]
    speed_safe = df["speed_ms"].replace(0, np.nan)
    load_safe = df["load_N"].replace(0, np.nan)
    df["load_speed_ratio"] = (df["load_N"] / speed_safe).fillna(0.0)
    df["speed_load_ratio"] = (df["speed_ms"] / load_safe).fillna(0.0)

    df["log_load"] = np.log1p(df["load_N"].clip(lower=0)).fillna(0.0)
    df["log_speed"] = np.log1p(df["speed_ms"].clip(lower=0)).fillna(0.0)
    df["log_distance"] = np.log1p(df["distance_m"].clip(lower=0)).fillna(0.0)
    df["log_PV"] = np.log1p(df["PV_factor"].clip(lower=0)).fillna(0.0)

    df["humidity_available"] = df["humidity_pct"].notna().astype(int)
    df["temperature_available"] = df["temperature_C"].notna().astype(int)

    df["delta_T_flash"] = df.apply(calculate_flash_temperature, axis=1)
    df["total_contact_temp"] = df["temperature_C"].fillna(23.0) + df["delta_T_flash"]
    df["exceeds_Tg_50C"] = (df["total_contact_temp"] > 50.0).astype(int)

    # 9. Non-linear Composition terms (squared)
    df["gf_pct_sq"] = df["glass_fiber_pct"] ** 2
    df["graphite_pct_sq"] = df["graphite_pct"] ** 2
    df["mos2_pct_sq"] = df["mos2_pct"] ** 2
    df["total_filler_pct_sq"] = df["total_filler_pct"] ** 2
    df["matrix_pct_sq"] = df["matrix_pct"] ** 2

    # 10. Filler x Filler Interactions
    df["gf_graphite_interaction"] = df["glass_fiber_pct"] * df["graphite_pct"]
    df["gf_mos2_interaction"] = df["glass_fiber_pct"] * df["mos2_pct"]
    df["graphite_mos2_interaction"] = df["graphite_pct"] * df["mos2_pct"]

    # 11. Filler x Matrix Interactions
    df["gf_matrix_interaction"] = df["glass_fiber_pct"] * df["matrix_pct"]
    df["graphite_matrix_interaction"] = df["graphite_pct"] * df["matrix_pct"]
    df["mos2_matrix_interaction"] = df["mos2_pct"] * df["matrix_pct"]

    # 12. Filler x Operating Interactions
    df["gf_load_interaction"] = df["glass_fiber_pct"] * df["load_N"].fillna(0)
    df["gf_speed_interaction"] = df["glass_fiber_pct"] * df["speed_ms"].fillna(0)
    df["graphite_load_interaction"] = df["graphite_pct"] * df["load_N"].fillna(0)
    df["graphite_speed_interaction"] = df["graphite_pct"] * df["speed_ms"].fillna(0)
    df["mos2_load_interaction"] = df["mos2_pct"] * df["load_N"].fillna(0)
    df["mos2_speed_interaction"] = df["mos2_pct"] * df["speed_ms"].fillna(0)

    # 13. Environmental Interactions
    temp_val = df["temperature_C"].fillna(23.0)
    humid_val = df["humidity_pct"].fillna(50.0)

    df["speed_temperature_interaction"] = df["speed_ms"].fillna(0) * temp_val
    df["load_temperature_interaction"] = df["load_N"].fillna(0) * temp_val
    df["gf_temperature_interaction"] = df["glass_fiber_pct"] * temp_val
    df["graphite_temperature_interaction"] = df["graphite_pct"] * temp_val
    df["mos2_temperature_interaction"] = df["mos2_pct"] * temp_val

    df["speed_humidity_interaction"] = df["speed_ms"].fillna(0) * humid_val
    df["load_humidity_interaction"] = df["load_N"].fillna(0) * humid_val
    df["gf_humidity_interaction"] = df["glass_fiber_pct"] * humid_val

    # Configuration categorical columns
    for c in ["counterface", "test_type", "environment", "fabrication"]:
        if c not in df.columns:
            df[c] = "unknown"
        else:
            df[c] = df[c].fillna("unknown").astype(str)

    # Clean infinities
    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    # Define standard feature sets from Tribo.ipynb
    composition_features = [
        "pa6_pct", "pa66_pct", "matrix_pct", "pa6_fraction", "pa66_fraction", "pa6_dominant",
        "glass_fiber_pct", "graphite_pct", "mos2_pct",
        "gf_present", "graphite_present", "mos2_present",
        "other_total_pct", "other_component_count",
        "other_lubricant_pct", "other_reinforcement_pct", "other_nanofiller_pct",
        "other_lubricant_count", "other_reinforcement_count", "other_nanofiller_count",
        "known_filler_pct", "total_filler_pct", "reported_composition_pct", "composition_gap",
        "filler_matrix_ratio", "gf_matrix_ratio", "graphite_matrix_ratio", "mos2_matrix_ratio",
        "lubricant_reinforcement_ratio", "main_filler_type_count", "filler_type_count", "multiple_filler_system", "hybrid_composite",
        "gf_pct_sq", "graphite_pct_sq", "mos2_pct_sq", "total_filler_pct_sq", "matrix_pct_sq"
    ]

    operating_features = [
        "load_N", "speed_ms", "distance_m", "PV_factor", "humidity_pct", "temperature_C",
        "load_speed_product", "load_speed_ratio", "speed_load_ratio",
        "log_load", "log_speed", "log_distance", "log_PV",
        "humidity_available", "temperature_available",
        "delta_T_flash", "total_contact_temp", "exceeds_Tg_50C"
    ]

    interaction_features = [
        "gf_graphite_interaction", "gf_mos2_interaction", "graphite_mos2_interaction",
        "gf_matrix_interaction", "graphite_matrix_interaction", "mos2_matrix_interaction",
        "gf_load_interaction", "gf_speed_interaction", "graphite_load_interaction",
        "graphite_speed_interaction", "mos2_load_interaction", "mos2_speed_interaction",
        "speed_temperature_interaction", "load_temperature_interaction",
        "gf_temperature_interaction", "graphite_temperature_interaction", "mos2_temperature_interaction",
        "speed_humidity_interaction", "load_humidity_interaction", "gf_humidity_interaction"
    ]

    configuration_features = [
        "counterface", "test_type", "environment", "fabrication"
    ]

    full_features = list(dict.fromkeys(
        composition_features + operating_features + interaction_features + configuration_features
    ))

    feature_groups = {
        "composition": composition_features,
        "operating": operating_features,
        "interaction": interaction_features,
        "configuration": configuration_features,
        "full": full_features
    }

    return df, feature_groups
