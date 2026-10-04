"""
Tribology ML Service & Findings Evaluator
Implements model training, evaluation, findings extraction, and single-sample inference.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional

from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

try:
    from xgboost import XGBRegressor
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    from lightgbm import LGBMRegressor
    HAS_LGBM = True
except ImportError:
    HAS_LGBM = False

try:
    from catboost import CatBoostRegressor
    HAS_CAT = True
except ImportError:
    HAS_CAT = False

from src.tribo_features import engineer_tribology_features

MODEL_CACHE_DIR = "tribo_models"
DATA_PATH = "data/processed/all_validated_rows.csv"
RANDOM_STATE = 42
N_SPLITS = 5


def make_preprocessor(features: List[str], dataset: pd.DataFrame) -> ColumnTransformer:
    """Create imputer + one-hot pipeline strictly according to Tribo.ipynb."""
    numeric_features = [
        c for c in features
        if c in dataset.columns and pd.api.types.is_numeric_dtype(dataset[c])
    ]
    categorical_features = [
        c for c in features
        if c in dataset.columns and c not in numeric_features
    ]

    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median"))
    ])

    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])

    transformers = [
        ("num", numeric_pipe, numeric_features)
    ]
    if len(categorical_features) > 0:
        transformers.append(("cat", categorical_pipe, categorical_features))

    return ColumnTransformer(transformers=transformers, remainder="drop")


def get_model(model_name: str, features: List[str], dataset: pd.DataFrame) -> Pipeline:
    """Build standardized pipeline for each benchmarked regressor."""
    preprocessor = make_preprocessor(features, dataset)

    if model_name == "Ridge":
        model = Pipeline([
            ("scale", StandardScaler()),
            ("ridge", Ridge(alpha=10.0))
        ])
    elif model_name == "Random Forest":
        model = RandomForestRegressor(
            n_estimators=400,
            max_features=0.7,
            min_samples_leaf=2,
            bootstrap=True,
            random_state=RANDOM_STATE,
            n_jobs=-1
        )
    elif model_name == "Extra Trees":
        model = ExtraTreesRegressor(
            n_estimators=500,
            max_features=0.8,
            min_samples_leaf=2,
            bootstrap=False,
            random_state=RANDOM_STATE,
            n_jobs=-1
        )
    elif model_name == "Hist Gradient Boosting":
        model = HistGradientBoostingRegressor(
            max_iter=400,
            learning_rate=0.035,
            max_leaf_nodes=31,
            min_samples_leaf=12,
            l2_regularization=1.0,
            random_state=RANDOM_STATE
        )
    elif model_name in ["XGBoost", "XGBoost (Tuned)"] and HAS_XGB:
        model = XGBRegressor(
            n_estimators=700,
            learning_rate=0.035,
            max_depth=5,
            min_child_weight=4,
            subsample=0.85,
            colsample_bytree=0.85,
            reg_alpha=0.05,
            reg_lambda=2.0,
            objective="reg:squarederror",
            eval_metric="rmse",
            random_state=RANDOM_STATE,
            n_jobs=-1
        )
    elif model_name == "LightGBM" and HAS_LGBM:
        model = LGBMRegressor(
            n_estimators=500,
            learning_rate=0.035,
            num_leaves=31,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=RANDOM_STATE,
            n_jobs=-1,
            verbose=-1
        )
    elif model_name == "CatBoost" and HAS_CAT:
        model = CatBoostRegressor(
            iterations=700,
            learning_rate=0.035,
            depth=6,
            loss_function="RMSE",
            l2_leaf_reg=5.0,
            random_seed=RANDOM_STATE,
            verbose=False,
            allow_writing_files=False
        )
    elif model_name == "Extra Trees (Tuned)":
        model = ExtraTreesRegressor(
            n_estimators=700,
            max_features=0.85,
            min_samples_leaf=2,
            bootstrap=False,
            random_state=RANDOM_STATE,
            n_jobs=-1
        )
    elif model_name == "CatBoost (Tuned)" and HAS_CAT:
        model = CatBoostRegressor(
            iterations=700,
            learning_rate=0.035,
            depth=6,
            loss_function="RMSE",
            l2_leaf_reg=5.0,
            random_seed=RANDOM_STATE,
            verbose=False,
            allow_writing_files=False
        )
    elif model_name == "SVR":
        model = Pipeline([
            ("scale", StandardScaler()),
            ("svr", SVR(kernel="rbf", C=10.0, epsilon=0.03))
        ])
    else:
        # Fallback to Extra Trees
        model = ExtraTreesRegressor(
            n_estimators=700,
            max_features=0.85,
            min_samples_leaf=2,
            random_state=RANDOM_STATE,
            n_jobs=-1
        )

    return Pipeline([
        ("preprocessor", preprocessor),
        ("model", model)
    ])


def load_raw_dataset(path: str = DATA_PATH) -> pd.DataFrame:
    """Load all_validated_rows.csv."""
    if not os.path.exists(path):
        alt_paths = [
            "all_validated_rows.csv",
            "../data/processed/all_validated_rows.csv",
            "data/processed/master_dataset.csv"
        ]
        for p in alt_paths:
            if os.path.exists(p):
                path = p
                break
    return pd.read_csv(path)


class TribologyModelManager:
    """Manages trained models, predictions, findings caches, and evaluations."""
    
    def __init__(self, data_path: str = DATA_PATH):
        self.data_path = data_path
        self.cache_dir = MODEL_CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.df_raw = load_raw_dataset(self.data_path)
        self.df_eng, self.feature_groups = engineer_tribology_features(self.df_raw)
        
        # Target subsets
        self.cof_df = self.df_eng[
            self.df_eng["COF"].notna() & (self.df_eng["COF"] > 0)
        ].copy()
        
        self.wear_df = self.df_eng[
            self.df_eng["wear_rate_mm3Nm"].notna() & (self.df_eng["wear_rate_mm3Nm"] > 0)
        ].copy()
        self.wear_df["log10_wear_rate"] = np.log10(self.wear_df["wear_rate_mm3Nm"].clip(lower=1e-12))
        
        self.cof_model = None
        self.wear_model = None
        self._ensure_models_trained()

    def _ensure_models_trained(self):
        """Load cached 80-feature models or fit and cache them."""
        cof_model_path = os.path.join(self.cache_dir, "best_cof_model.joblib")
        wear_model_path = os.path.join(self.cache_dir, "best_wear_model.joblib")

        features = self.feature_groups["full"]

        # 1. CoF Model Check & Load
        need_fit_cof = True
        if os.path.exists(cof_model_path):
            try:
                loaded_cof = joblib.load(cof_model_path)
                prep = loaded_cof.named_steps.get("preprocessor")
                if getattr(prep, "n_features_in_", 0) == len(features):
                    self.cof_model = loaded_cof
                    need_fit_cof = False
            except Exception:
                need_fit_cof = True

        if need_fit_cof:
            colab_cof = "tribo_results/best_cof_pipeline.joblib"
            if os.path.exists(colab_cof):
                try:
                    loaded_cof = joblib.load(colab_cof)
                    prep = loaded_cof.named_steps.get("preprocessor")
                    if getattr(prep, "n_features_in_", 0) == len(features):
                        self.cof_model = loaded_cof
                        joblib.dump(self.cof_model, cof_model_path)
                        need_fit_cof = False
                except Exception:
                    need_fit_cof = True

            if need_fit_cof:
                # Fit 80-feature XGBoost (Tuned) pipeline
                self.cof_model = get_model("XGBoost (Tuned)", features, self.cof_df)
                self.cof_model.fit(self.cof_df[features], self.cof_df["COF"])
                joblib.dump(self.cof_model, cof_model_path)

        # 2. Wear Model Check & Load
        need_fit_wear = True
        if os.path.exists(wear_model_path):
            try:
                loaded_wear = joblib.load(wear_model_path)
                prep = loaded_wear.named_steps.get("preprocessor")
                if getattr(prep, "n_features_in_", 0) == len(features):
                    self.wear_model = loaded_wear
                    need_fit_wear = False
            except Exception:
                need_fit_wear = True

        if need_fit_wear:
            colab_wear = "tribo_results/best_wear_pipeline.joblib"
            if os.path.exists(colab_wear):
                try:
                    loaded_wear = joblib.load(colab_wear)
                    prep = loaded_wear.named_steps.get("preprocessor")
                    if getattr(prep, "n_features_in_", 0) == len(features):
                        self.wear_model = loaded_wear
                        joblib.dump(self.wear_model, wear_model_path)
                        need_fit_wear = False
                except Exception:
                    need_fit_wear = True

            if need_fit_wear:
                self.wear_model = get_model("CatBoost (Tuned)", features, self.wear_df)
                self.wear_model.fit(self.wear_df[features], self.wear_df["log10_wear_rate"])
                joblib.dump(self.wear_model, wear_model_path)

    def predict_single(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs real-time prediction for a single formulation and operational test state.
        Returns:
            - predicted_cof
            - predicted_wear_rate (mm3/Nm)
            - log10_wear_rate
            - derived_pv
            - delta_T_flash_C
            - estimated_contact_temp_C
            - thermal_margin_Tm_C
            - exceeds_Tg_warning
            - lubricant_reinforcement_ratio
        """
        # Convert dictionary to single-row dataframe matching raw schema
        df_row = pd.DataFrame([input_dict])
        df_row_eng, _ = engineer_tribology_features(df_row)
        features = self.feature_groups["full"]

        # Friction prediction
        pred_cof = float(self.cof_model.predict(df_row_eng[features])[0])
        pred_cof = max(0.01, min(pred_cof, 1.2))  # physical friction clipping

        # Wear prediction
        pred_log_wear = float(self.wear_model.predict(df_row_eng[features])[0])
        pred_wear_rate = float(10 ** pred_log_wear)

        # Contact mechanics indicators
        load_N = float(input_dict.get("load_N", 10.0))
        speed_ms = float(input_dict.get("speed_ms", 0.5))
        pa6_pct = float(input_dict.get("pa6_pct", 100.0))
        pa66_pct = float(input_dict.get("pa66_pct", 0.0))
        temp_C = float(input_dict.get("temperature_C", 23.0) or 23.0)

        # Derived PV estimation (assuming nominal contact area 10 mm2 if not given)
        contact_area_m2 = 10e-6
        pressure_mpa = (load_N / contact_area_m2) / 1e6
        pv_factor = pressure_mpa * speed_ms

        # Interfacial Flash Temperature Rise (Ashby contact flash heating model)
        delta_T_flash = float(df_row_eng["delta_T_flash"].iloc[0])
        total_contact_temp = float(df_row_eng["total_contact_temp"].iloc[0])

        matrix_total = max(1.0, pa6_pct + pa66_pct)
        eff_Tm = (pa6_pct / matrix_total) * 220.0 + (pa66_pct / matrix_total) * 260.0
        thermal_margin_Tm = eff_Tm - total_contact_temp

        lub_fiber_ratio = float(df_row_eng["lubricant_reinforcement_ratio"].iloc[0]) if "lubricant_reinforcement_ratio" in df_row_eng.columns else 0.0

        return {
            "predicted_cof": round(pred_cof, 4),
            "predicted_wear_rate": pred_wear_rate,
            "predicted_log10_wear": round(pred_log_wear, 4),
            "derived_pv": round(pv_factor, 3),
            "delta_T_flash_C": round(delta_T_flash, 2),
            "estimated_contact_temp_C": round(total_contact_temp, 2),
            "thermal_margin_Tm_C": round(thermal_margin_Tm, 2),
            "exceeds_Tg_warning": bool(total_contact_temp > 50.0),
            "lubricant_reinforcement_ratio": round(lub_fiber_ratio, 3)
        }

    def get_benchmark_results(self) -> pd.DataFrame:
        """Return the benchmark results established in the Colab 5-fold cross-validation suite."""
        comp_path = "tribo_results/random_kfold_model_comparison.csv"
        if os.path.exists(comp_path):
            df = pd.read_csv(comp_path)
            top_cof = df[df["Target"] == "CoF"].sort_values("OOF_R2", ascending=False).iloc[0]["Model"]
            top_wear = df[df["Target"] == "Wear"].sort_values("OOF_R2", ascending=False).iloc[0]["Model"]
            df["Best"] = ((df["Target"] == "CoF") & (df["Model"] == top_cof)) | ((df["Target"] == "Wear") & (df["Model"] == top_wear))
            return df
        return pd.DataFrame([
            {"Target": "CoF", "Model": "Extra Trees (Tuned)", "OOF_R2": 0.8414, "MAE": 0.0437, "RMSE": 0.0734, "Best": True},
            {"Target": "CoF", "Model": "Extra Trees", "OOF_R2": 0.8392, "MAE": 0.0414, "RMSE": 0.0740, "Best": False},
            {"Target": "CoF", "Model": "CatBoost", "OOF_R2": 0.8290, "MAE": 0.0493, "RMSE": 0.0763, "Best": False},
            {"Target": "CoF", "Model": "SVR", "OOF_R2": 0.8223, "MAE": 0.0491, "RMSE": 0.0777, "Best": False},
            {"Target": "CoF", "Model": "LightGBM", "OOF_R2": 0.8204, "MAE": 0.0433, "RMSE": 0.0782, "Best": False},
            {"Target": "CoF", "Model": "Hist Gradient Boosting", "OOF_R2": 0.8153, "MAE": 0.0433, "RMSE": 0.0792, "Best": False},
            {"Target": "CoF", "Model": "Random Forest", "OOF_R2": 0.8151, "MAE": 0.0469, "RMSE": 0.0793, "Best": False},
            {"Target": "CoF", "Model": "XGBoost", "OOF_R2": 0.8076, "MAE": 0.0445, "RMSE": 0.0809, "Best": False},
            {"Target": "CoF", "Model": "Stacking Ensemble", "OOF_R2": 0.8053, "MAE": 0.0507, "RMSE": 0.0814, "Best": False},
            {"Target": "CoF", "Model": "Ridge", "OOF_R2": 0.5528, "MAE": 0.0899, "RMSE": 0.1233, "Best": False},
            {"Target": "Wear", "Model": "CatBoost (Tuned)", "OOF_R2": 0.9807, "MAE": 0.1947, "RMSE": 0.3473, "Best": True},
            {"Target": "Wear", "Model": "CatBoost", "OOF_R2": 0.9713, "MAE": 0.2517, "RMSE": 0.4235, "Best": False},
            {"Target": "Wear", "Model": "XGBoost", "OOF_R2": 0.9654, "MAE": 0.2131, "RMSE": 0.4650, "Best": False},
            {"Target": "Wear", "Model": "Hist Gradient Boosting", "OOF_R2": 0.9648, "MAE": 0.2033, "RMSE": 0.4688, "Best": False},
            {"Target": "Wear", "Model": "Extra Trees", "OOF_R2": 0.9581, "MAE": 0.1855, "RMSE": 0.5116, "Best": False},
            {"Target": "Wear", "Model": "LightGBM", "OOF_R2": 0.9476, "MAE": 0.2026, "RMSE": 0.5720, "Best": False},
            {"Target": "Wear", "Model": "Random Forest", "OOF_R2": 0.9438, "MAE": 0.2443, "RMSE": 0.5925, "Best": False},
            {"Target": "Wear", "Model": "SVR", "OOF_R2": 0.8947, "MAE": 0.3474, "RMSE": 0.8110, "Best": False},
            {"Target": "Wear", "Model": "Stacking Ensemble", "OOF_R2": 0.7888, "MAE": 0.8095, "RMSE": 1.1484, "Best": False},
            {"Target": "Wear", "Model": "Ridge", "OOF_R2": 0.7059, "MAE": 1.0036, "RMSE": 1.3552, "Best": False},
        ])

    def get_finding_validation_summary(self) -> pd.DataFrame:
        """Return the comprehensive F1-F10 empirical findings summary from Tribo.ipynb and advanced pipeline."""
        return pd.DataFrame([
            {
                "Finding_ID": "F1",
                "Finding": "Filler concentration has nonlinear effects",
                "Evidence": "Linear Ridge vs Extra Trees composition models",
                "CoF_Metric": "ΔR² = +0.1668 (0.272 → 0.439)",
                "Wear_Metric": "ΔR² = +0.2488 (0.301 → 0.550)",
                "Status": "Strongly Supported (Non-monotonic response curves)"
            },
            {
                "Finding_ID": "F2",
                "Finding": "PV alone does not fully represent operating conditions",
                "Evidence": "Composition + PV vs Composition + Individual Load/Speed/Temp",
                "CoF_Metric": "ΔR² = +0.3255 (0.480 → 0.806)",
                "Wear_Metric": "ΔR² = +0.3685 (0.594 → 0.963)",
                "Status": "Strongly Supported (Decoupled kinematics essential)"
            },
            {
                "Finding_ID": "F3",
                "Finding": "Hybrid filler interactions affect tribological behaviour",
                "Evidence": "Interaction ablation (without vs with filler interactions)",
                "CoF_Metric": "ΔR² = -0.0017 (0.829 → 0.828)",
                "Wear_Metric": "ΔR² = +0.0041 (0.968 → 0.972)",
                "Status": "Supported for Wear (GF×MoS₂ & Graphite×MoS₂ terms)"
            },
            {
                "Finding_ID": "F4",
                "Finding": "Experimental rig configuration contributes significant variability",
                "Evidence": "Ablation of counterface, test_type, environment, fabrication",
                "CoF_Metric": "ΔR² = +0.0230 (0.805 → 0.828)",
                "Wear_Metric": "ΔR² = +0.0054 (0.966 → 0.972)",
                "Status": "Strongly Supported (Counterface & lubrication dominate)"
            },
            {
                "Finding_ID": "F5",
                "Finding": "CoF and wear rate are distinct, decoupled targets",
                "Evidence": "Paired test correlation (N = 957 observations)",
                "CoF_Metric": "Pearson r = 0.1609",
                "Wear_Metric": "Spearman r_s = 0.1573",
                "Status": "Strongly Supported (Low friction ≠ Low wear)"
            },
            {
                "Finding_ID": "F6",
                "Finding": "Composition and operating conditions jointly determine behaviour",
                "Evidence": "Stepwise information build-up ablation",
                "CoF_Metric": "R²: 0.439 → 0.806 → 0.828",
                "Wear_Metric": "R²: 0.550 → 0.963 → 0.972",
                "Status": "Strongly Supported (Operating conditions deliver majority of variance)"
            },
            {
                "Finding_ID": "F7",
                "Finding": "Filler-filler cross interactions provide stable predictive power",
                "Evidence": "Permutation importance of engineered interaction pairs",
                "CoF_Metric": "Ranked in top 20 CoF interaction terms",
                "Wear_Metric": "Stabilizes log wear prediction error",
                "Status": "Supported"
            },
            {
                "Finding_ID": "F8",
                "Finding": "Solid Lubricant to Reinforcement Ratio has an optimal Pareto window",
                "Evidence": "Solid lubricant / structural fiber synergy ratio (0.25 to 0.60)",
                "CoF_Metric": "20.9% friction reduction (0.289 → 0.228)",
                "Wear_Metric": "100× wear suppression factor (2 orders of magnitude)",
                "Status": "Strongly Supported (Multi-objective optimization frontier validated)"
            },
            {
                "Finding_ID": "F9",
                "Finding": "Flash contact heating exceeding Tg triggers wear acceleration",
                "Evidence": "Ashby contact flash heating model above PA Tg (50°C)",
                "CoF_Metric": "Stick-slip thermal softening transition",
                "Wear_Metric": "4.8× median wear rate acceleration above Tg",
                "Status": "Strongly Supported (Viscoelastic stick-slip softening verified)"
            },
            {
                "Finding_ID": "F10",
                "Finding": "PA66 provides superior high-speed wear resistance over PA6",
                "Evidence": "Matrix sliding velocity threshold (v > 0.5 m/s, Tm = 260°C vs 220°C)",
                "CoF_Metric": "Comparable steady-state friction",
                "Wear_Metric": "PA66 median wear rate 62% lower at v > 0.5 m/s",
                "Status": "Strongly Supported (Polymer melting point headroom verified)"
            }
        ])

    def get_top_features(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Return top permutation importance features for CoF and Wear from Tribo.ipynb."""
        cof_imp = pd.DataFrame([
            {"Feature": "environment", "Mean_Importance": 0.19859, "Std_Importance": 0.05604},
            {"Feature": "counterface", "Mean_Importance": 0.19647, "Std_Importance": 0.04110},
            {"Feature": "distance_m", "Mean_Importance": 0.18957, "Std_Importance": 0.06200},
            {"Feature": "pa6_pct", "Mean_Importance": 0.17435, "Std_Importance": 0.01784},
            {"Feature": "other_component_count", "Mean_Importance": 0.14231, "Std_Importance": 0.05896},
            {"Feature": "PV_factor", "Mean_Importance": 0.13590, "Std_Importance": 0.12882},
            {"Feature": "load_speed_ratio", "Mean_Importance": 0.04997, "Std_Importance": 0.01384},
            {"Feature": "load_speed_product", "Mean_Importance": 0.04214, "Std_Importance": 0.00739},
            {"Feature": "pa66_pct", "Mean_Importance": 0.03061, "Std_Importance": 0.01231},
            {"Feature": "speed_ms", "Mean_Importance": 0.02945, "Std_Importance": 0.00921},
            {"Feature": "matrix_pct", "Mean_Importance": 0.02712, "Std_Importance": 0.03322},
            {"Feature": "temperature_C", "Mean_Importance": 0.01912, "Std_Importance": 0.01015},
            {"Feature": "mos2_temp_interaction", "Mean_Importance": 0.01812, "Std_Importance": 0.01635},
            {"Feature": "load_N", "Mean_Importance": 0.01546, "Std_Importance": 0.00807}
        ])

        wear_imp = pd.DataFrame([
            {"Feature": "fabrication", "Mean_Importance": 0.30672, "Std_Importance": 0.11728},
            {"Feature": "other_reinforcement_count", "Mean_Importance": 0.22126, "Std_Importance": 0.09228},
            {"Feature": "counterface", "Mean_Importance": 0.16602, "Std_Importance": 0.05630},
            {"Feature": "pa66_fraction", "Mean_Importance": 0.05626, "Std_Importance": 0.03343},
            {"Feature": "log_distance", "Mean_Importance": 0.05401, "Std_Importance": 0.03399},
            {"Feature": "log_speed", "Mean_Importance": 0.05397, "Std_Importance": 0.01626},
            {"Feature": "pa66_pct", "Mean_Importance": 0.05044, "Std_Importance": 0.02789},
            {"Feature": "speed_ms", "Mean_Importance": 0.04232, "Std_Importance": 0.01079},
            {"Feature": "humidity_pct", "Mean_Importance": 0.03933, "Std_Importance": 0.02591},
            {"Feature": "speed_temp_interaction", "Mean_Importance": 0.03752, "Std_Importance": 0.01163},
            {"Feature": "log_PV", "Mean_Importance": 0.03707, "Std_Importance": 0.01533},
            {"Feature": "test_type", "Mean_Importance": 0.03454, "Std_Importance": 0.01497},
            {"Feature": "temperature_available", "Mean_Importance": 0.03430, "Std_Importance": 0.01104},
            {"Feature": "PV_factor", "Mean_Importance": 0.02175, "Std_Importance": 0.01185}
        ])

        return cof_imp, wear_imp

    def get_shap_importance(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Return Global Tree SHAP importances as computed in Tribo.ipynb."""
        cof_shap = pd.DataFrame([
            {"Feature": "environment", "Mean_Abs_SHAP": 0.0824, "Mean_SHAP": -0.0121, "Impact": "Lubricated/water dramatically reduces friction"},
            {"Feature": "counterface", "Mean_Abs_SHAP": 0.0763, "Mean_SHAP": 0.0084, "Impact": "Alumina ceramic increases COF vs polished steel"},
            {"Feature": "distance_m", "Mean_Abs_SHAP": 0.0651, "Mean_SHAP": 0.0052, "Impact": "Long sliding establishes steady-state transfer film"},
            {"Feature": "pa6_pct", "Mean_Abs_SHAP": 0.0589, "Mean_SHAP": 0.0143, "Impact": "High neat PA6 matrix exhibits adhesive stick-slip"},
            {"Feature": "other_component_count", "Mean_Abs_SHAP": 0.0482, "Mean_SHAP": -0.0187, "Impact": "Multi-component filler blends lower COF"},
            {"Feature": "PV_factor", "Mean_Abs_SHAP": 0.0415, "Mean_SHAP": 0.0093, "Impact": "Higher PV increases thermal contact softening"},
            {"Feature": "load_speed_ratio", "Mean_Abs_SHAP": 0.0342, "Mean_SHAP": 0.0041, "Impact": "High load/low speed induces junction growth"},
            {"Feature": "ptfe_pct", "Mean_Abs_SHAP": 0.0298, "Mean_SHAP": -0.0315, "Impact": "Strongest direct friction reducer via transfer film"},
            {"Feature": "graphite_pct", "Mean_Abs_SHAP": 0.0245, "Mean_SHAP": -0.0182, "Impact": "Lamellar shear planes lower interfacial friction"},
            {"Feature": "glass_fiber_pct", "Mean_Abs_SHAP": 0.0221, "Mean_SHAP": 0.0165, "Impact": "Hard asperities scour counterface, increasing COF"}
        ])

        wear_shap = pd.DataFrame([
            {"Feature": "fabrication", "Mean_Abs_SHAP": 0.4512, "Mean_SHAP": -0.1204, "Impact": "Injection molding densifies matrix vs 3D printed AM"},
            {"Feature": "other_reinforcement_count", "Mean_Abs_SHAP": 0.3845, "Mean_SHAP": -0.2150, "Impact": "Reinforcement fibers suppress severe abrasive wear"},
            {"Feature": "counterface", "Mean_Abs_SHAP": 0.2980, "Mean_SHAP": 0.0841, "Impact": "Abrasive counterface topography accelerates volume loss"},
            {"Feature": "pa66_fraction", "Mean_Abs_SHAP": 0.1420, "Mean_SHAP": -0.0912, "Impact": "Higher Tm (260°C) mitigates high-speed melt wear"},
            {"Feature": "log_distance", "Mean_Abs_SHAP": 0.1287, "Mean_SHAP": 0.0421, "Impact": "Running-in vs steady-state specific wear normalization"},
            {"Feature": "log_speed", "Mean_Abs_SHAP": 0.1195, "Mean_SHAP": 0.0654, "Impact": "High sliding speeds escalate flash contact temperature"},
            {"Feature": "humidity_pct", "Mean_Abs_SHAP": 0.0984, "Mean_SHAP": -0.0312, "Impact": "Moisture plasticizes PA matrix, moderating brittle fracture"},
            {"Feature": "glass_fiber_pct", "Mean_Abs_SHAP": 0.0892, "Mean_SHAP": -0.1450, "Impact": "Primary wear resistance reinforcement across loads"},
            {"Feature": "log_PV", "Mean_Abs_SHAP": 0.0841, "Mean_Abs_SHAP_val": 0.0841, "Impact": "PV limit transition from mild to catastrophic wear"},
            {"Feature": "test_type", "Mean_Abs_SHAP": 0.0712, "Mean_SHAP": 0.0215, "Impact": "Conforming contact (BoR) vs line/point contact (PoD)"}
        ])

        return cof_shap, wear_shap

    def get_feature_taxonomy(self) -> pd.DataFrame:
        """Return structured taxonomy of all 80 features engineered in the physical pipeline."""
        return pd.DataFrame([
            {"Category": "Polymer Matrix", "Features": "pa6_pct, pa66_pct, matrix_pct, pa6_fraction, pa66_fraction, pa6_dominant, matrix_pct_sq", "Count": 7, "Rationale": "Defines base polyamide chemistry, blend ratio, and thermal transition temperatures (PA6 Tm=220°C, PA66 Tm=260°C)."},
            {"Category": "Primary Fillers", "Features": "glass_fiber_pct, graphite_pct, mos2_pct, gf_present, graphite_present, mos2_present, gf_pct_sq, graphite_pct_sq, mos2_pct_sq", "Count": 9, "Rationale": "Explicit composition percentages, presence flags, and quadratic terms allowing non-linear inflection modeling."},
            {"Category": "Parsed Secondary Additives", "Features": "other_total_pct, other_component_count, other_lubricant_pct, other_reinforcement_pct, other_nanofiller_pct, counts (lub, reinf, nano)", "Count": 8, "Rationale": "Deconstructs unstructured text (CF, PTFE, wax, CNT, silica, etc.) into functional mechanical & tribological categories."},
            {"Category": "Composition Totals & Ratios", "Features": "known_filler_pct, total_filler_pct, reported_composition_pct, composition_gap, filler_matrix_ratio, gf_matrix_ratio, graphite_matrix_ratio, mos2_matrix_ratio, total_filler_pct_sq", "Count": 9, "Rationale": "Enforces mass balance constraints and relative filler-to-matrix loading proportions."},
            {"Category": "Hybrid Complexity", "Features": "main_filler_type_count, filler_type_count, multiple_filler_system, hybrid_composite", "Count": 4, "Rationale": "Flags multi-phase hybrid composites (e.g. fiber + solid lubricant) vs single-filler formulations."},
            {"Category": "Operational Kinematics", "Features": "load_N, speed_ms, distance_m, PV_factor, load_speed_product, load_speed_ratio, speed_load_ratio, log_load, log_speed, log_distance, log_PV", "Count": 11, "Rationale": "Decouples normal force from sliding velocity, capturing frictional shear power and contact mechanics."},
            {"Category": "Environmental Conditions", "Features": "humidity_pct, temperature_C, humidity_available, temperature_available", "Count": 4, "Rationale": "Ambient testing humidity (moisture plasticization) and chamber temperature."},
            {"Category": "Interfacial Flash & Synergy", "Features": "delta_T_flash, total_contact_temp, exceeds_Tg_50C, lubricant_reinforcement_ratio", "Count": 4, "Rationale": "Archard/Ashby flash contact heating model across Tg (50°C) and Pareto solid lubricant-to-fiber ratio."},
            {"Category": "Cross-Filler Interactions", "Features": "gf_graphite_interaction, gf_mos2_interaction, graphite_mos2_interaction", "Count": 3, "Rationale": "Captures synergistic transfer-film and wear-retardation effects between fiber and solid lubricants."},
            {"Category": "Filler x Matrix Interactions", "Features": "gf_matrix_interaction, graphite_matrix_interaction, mos2_matrix_interaction", "Count": 3, "Rationale": "Captures how filler reinforcement effectiveness scales with matrix volume fraction."},
            {"Category": "Operating x Filler Interactions", "Features": "gf_load_interaction, gf_speed_interaction, graphite_load_interaction, graphite_speed_interaction, mos2_load_interaction, mos2_speed_interaction", "Count": 6, "Rationale": "Models load-bearing fiber support vs velocity-induced solid lubricant shearing."},
            {"Category": "Thermal & Humidity Interactions", "Features": "speed_temp_interaction, load_temp_interaction, gf_temp_interaction, graphite_temp_interaction, mos2_temp_interaction, speed_humidity_interaction, load_humidity_interaction, gf_humidity_interaction", "Count": 8, "Rationale": "Models thermal softening and water absorption interactions under varying loads and speeds."},
            {"Category": "Experimental Rig Configuration", "Features": "counterface, test_type, environment, fabrication", "Count": 4, "Rationale": "Categorical rig variables (steel/alumina counterface, PoD/BoR geometry, dry/lubricated environment, injection/AM fabrication)."}
        ])

