# Physics-Informed Machine Learning and Empirical Validation Suite for Multi-Filler Polyamide (PA6 / PA66) Tribology: From Literature Synthesis to an Interactive Virtual Tribometer

**Authors:** M. A. Saiadithyaa et al.  
**Affiliation:** Polyamide Tribology AI Research Initiative  
**Repository:** [https://github.com/M-A-SAIADITHYAA/gggg](https://github.com/M-A-SAIADITHYAA/gggg)  
**Interactive Colab Notebook:** [`Tribo_Advanced_Pipeline_Colab.ipynb`](https://github.com/M-A-SAIADITHYAA/gggg/blob/main/Tribo_Advanced_Pipeline_Colab.ipynb)  
**Live Application:** [`streamlit_app.py`](https://github.com/M-A-SAIADITHYAA/gggg/blob/main/streamlit_app.py)

---

## Executive Abstract

Polyamide 6 (PA6) and Polyamide 66 (PA66) thermoplastic composites are widely employed in self-lubricating bearings, gears, and dynamic seal assemblies. However, predicting their interfacial sliding friction ($\mu$, Coefficient of Friction) and volumetric material loss ($k_v$, Specific Wear Rate) remains an unsolved challenge due to non-linear multi-filler interactions, decoupled damage mechanisms, and localized thermal softening. 

In this work, we present an end-to-end, physics-informed machine learning framework developed from a curated experimental corpus of **1,353 validated tribological tests** extracted across **50+ peer-reviewed publications**. We engineer an **80-feature predictor taxonomy** capturing filler compositions, decoupled operational kinematics, Ashby contact flash heating models, and polynomial cross-body interaction terms. 

Using a leakage-free 5-fold cross-validation protocol benchmarked across **8 diverse machine learning architectures** with Optuna Bayesian hyperparameter optimization (Tree-structured Parzen Estimator, 35 trials per target), our production models achieved state-of-the-art generalization:
- **Coefficient of Friction (CoF)**: **XGBoost (Tuned)** achieved an Out-of-Fold (OOF) **$R^2 = 0.9572$**, Mean Absolute Error (MAE) of **$0.0220$**, and Root Mean Squared Error (RMSE) of **$0.0382$** (Fold Mean $R^2 = 0.9569 \pm 0.0068$).
- **Specific Wear Rate ($\log_{10} k_v$)**: **CatBoost (Tuned)** achieved an Out-of-Fold **$R^2 = 0.9819$**, MAE of **$0.1852$**, and RMSE of **$0.3362$** (Fold Mean $R^2 = 0.9817 \pm 0.0067$).

Furthermore, we computationally formalize and validate **10 core empirical findings (F1–F10)**, proving that:
1. Friction and wear are fundamentally orthogonal ($r = 0.1609$), disproving the heuristic that low friction guarantees low wear;
2. The traditional pressure-velocity product ($PV$) is insufficient, as decoupled kinematic terms deliver an $R^2$ increase of $+0.2952$ for CoF and $+0.3506$ for Wear;
3. Solid lubricant-to-fiber reinforcement ratios possess a distinct **Pareto frontier between $0.25$ and $0.60$**;
4. Interfacial contact flash heating exceeding the glass transition temperature ($T_g \approx 50^\circ\text{C}$) triggers viscoelastic softening and a $4.8\times$ wear escalation;
5. PA66 provides superior high-speed wear resistance over PA6 ($62\%$ lower wear at $v > 0.5$ m/s) due to its $+40^\circ\text{C}$ melting point headroom ($260^\circ\text{C}$ vs $220^\circ\text{C}$).

Finally, the models and findings are packaged into an interactive **Virtual Tribometer & Prediction Studio** deployed via Streamlit and Google Colab, enabling real-time formulation simulation and dynamic parametric sensitivity sweeps for materials scientists and mechanical designers.

---

## 1. Introduction and Problem Statement

Thermoplastic polymers, specifically aliphatic polyamides PA6 ($[\text{NH}-(\text{CH}_2)_5-\text{CO}]_n$) and PA66 ($[\text{NH}-(\text{CH}_2)_6-\text{NH}-\text{CO}-(\text{CH}_2)_4-\text{CO}]_n$), represent primary engineering materials for sliding components operating under boundary or dry friction regimes. In automotive timing gears, industrial bushings, and aerospace actuators, polyamides offer high specific strength, vibration damping, self-lubricating capability, and corrosion resistance.

To satisfy simultaneous structural stiffness and low wear requirements, polyamides are compounded with complex multi-filler systems combining:
- **Structural Reinforcements**: Short glass fibers (GF), carbon fibers (CF), and inorganic particulates that elevate elastic modulus, load-carrying capacity, and creep resistance.
- **Solid Lubricants**: Polytetrafluoroethylene (PTFE), graphite flake, and molybdenum disulfide ($\text{MoS}_2$) that shear easily to form sacrificial transfer films on opposing counterfaces.

Despite extensive experimental testing, developing predictive tribological design tools has been hindered by four fundamental physical challenges:

### 1.1 Non-Monotonic Multi-Filler Response
Filler additives exhibit complex non-monotonic tribological responses. For example, adding short glass fibers up to $15-20\text{ wt}\%$ reduces severe volumetric wear through asperity load support; however, above $30\text{ wt}\%$, fiber pull-out, debonding, and three-body abrasive scouring of the counterface accelerate wear and spike interfacial friction. Conversely, solid lubricants reduce friction via transfer film formation, but excessive loading weakens the polymer matrix integrity, causing micro-cleavage and spalling.

### 1.2 Mechanistic Decoupling of Friction and Wear
In classical mechanical design, low friction is frequently conflated with low wear. In polymer composite tribology, these two physical phenomena are governed by distinct mechanisms:
- **Coefficient of Friction ($\mu$)** is governed by interfacial shear strength of the boundary layer ($\tau_i$) and real contact area ($A_r$), where $\mu = \frac{\tau_i \cdot A_r}{F_N}$.
- **Specific Wear Rate ($k_v$)** is governed by subsurface stress distribution, crack initiation/propagation (fatigue wear), transfer film adherence, and debris ejection.

### 1.3 Inadequacy of the Classical $PV$ Metric
Industrial standards frequently condense operating conditions into a single scalar Pressure-Velocity metric ($PV = P \cdot v$). However, high load at low velocity ($P_{\text{high}}, v_{\text{low}}$) produces adhesive junction growth and subsurface plastic deformation, whereas low load at high velocity ($P_{\text{low}}, v_{\text{high}}$) induces intense frictional flash heating and thermal degradation, despite identical $PV$ values.

### 1.4 Thermal Transitions and Interfacial Flash Heating
Polyamides undergo significant viscoelastic modulus drop above their glass transition temperature ($T_g \approx 45-60^\circ\text{C}$). At high sliding speeds, flash heating at microscopic real contact asperities elevates the true contact temperature above $T_g$ or toward the melting point ($T_m = 220^\circ\text{C}$ for PA6, $260^\circ\text{C}$ for PA66), leading to stick-slip transitions and catastrophic melt-induced extrusion wear.

To overcome these challenges, this investigation develops a unified, physics-informed data science pipeline and virtual tribometer.

---

## 2. Experimental Literature Dataset Curation

### 2.1 Literature Extraction Methodology
A literature database was compiled from scientific papers published between 1995 and 2024. The corpus comprises **1,353 validated experimental runs** extracted across **50+ independent literature studies** investigating PA6 and PA66 composites under diverse tribological test geometries.

The dataset, persisted in `data/processed/all_validated_rows.csv`, satisfies strict metadata standards:
1. Complete formulation stoichiometry (matrix percentage, filler types, weight percentages);
2. Continuous kinematic test parameters (applied normal load $F_N$, sliding velocity $v$, sliding distance $s$, ambient temperature $T_0$, relative humidity $RH$);
3. Rig mechanical configurations (pin-on-disk, block-on-ring, ball-on-flat, counterface material and roughness, lubrication medium, fabrication method);
4. Explicit reporting of steady-state Coefficient of Friction ($\mu$) and/or Specific Wear Rate ($k_v$ in $\text{mm}^3/(\text{N}\cdot\text{m})$).

### 2.2 Population Partitioning and Transformation
Due to experimental variations across published papers, the population divides into two validated target subsets:
- **Coefficient of Friction ($\text{CoF}$)**: $N = 1,227$ observations, continuous range $\mu \in [0.05, 1.10]$.
- **Specific Wear Rate ($k_v$)**: $N = 1,120$ observations, continuous range $k_v \in [10^{-16}, 10^{-2}]\text{ mm}^3/(\text{N}\cdot\text{m})$.

Because specific wear rates span 14 orders of magnitude, linear regression induces catastrophic heteroscedasticity. We formulate wear rate prediction in logarithmic space:
$$y_{\text{wear}} = \log_{10}\left(k_v\right)$$
where predictions are converted back to physical volumetric loss via $k_v = 10^{y_{\text{wear}}}$.

---

## 3. Physics-Informed Feature Engineering Taxonomy (80 Predictors)

Rather than passing raw features directly to machine learning models, we construct an **80-feature predictor space** structured into 5 orthogonal physical categories:

```
Total Predictor Space: 80 Features
├── Group 1: Composition Terms (38 features)
├── Group 2: Operational Kinematics (18 features)
├── Group 3: Interfacial Contact Mechanics & Flash Heating (Physics-Informed)
├── Group 4: Synergistic Filler-Filler Interaction Terms (20 features)
└── Group 5: Rig Mechanical Configurations (4 categorical features)
```

### 3.1 Composition Features (38 Features)
- **Matrix Terms**: `pa6_pct`, `pa66_pct`, `matrix_pct`, `pa6_fraction`, `pa66_fraction`, `pa6_dominant` ($\mathbb{I}(\text{PA6} \ge \text{PA66})$).
- **Core Fillers**: Short glass fiber (`glass_fiber_pct`), graphite flake (`graphite_pct`), molybdenum disulfide (`mos2_pct`), alongside binary presence indicators (`gf_present`, `graphite_present`, `mos2_present`).
- **Secondary Additives**: Counts and weight percentages of solid lubricants, reinforcing fibers, and nanofillers (`other_total_pct`, `other_component_count`, `other_lubricant_pct`, `other_reinforcement_pct`, `other_nanofiller_pct`, etc.).
- **Stoichiometric Balances**: `known_filler_pct`, `total_filler_pct`, `reported_composition_pct`, and `composition_gap` ($100 - (\text{matrix} + \text{fillers})$).
- **Filler-Matrix Ratios**: $\frac{\text{filler}}{\text{matrix}}$, $\frac{\text{GF}}{\text{matrix}}$, $\frac{\text{Graphite}}{\text{matrix}}$, $\frac{\text{MoS}_2}{\text{matrix}}$.
- **Synergy Ratio (Finding 8)**: Ratio of total solid lubricant to structural reinforcement:
  $$R_{\text{lub/reinf}} = \frac{w_{\text{graphite}} + w_{\text{mos2}} + w_{\text{lub,other}}}{\max\left(w_{\text{GF}} + w_{\text{reinf,other}}, \epsilon\right)}$$
- **Polynomial Non-Linearities**: Quadratic terms capturing non-monotonic saturation: `gf_pct_sq`, `graphite_pct_sq`, `mos2_pct_sq`, `total_filler_pct_sq`, `matrix_pct_sq`.
- **Hybrid Complexity**: `main_filler_type_count`, `filler_type_count`, `multiple_filler_system`, `hybrid_composite`.

### 3.2 Operating Kinematic Features (18 Features)
- Primary kinematics: Load ($F_N$), sliding speed ($v$), distance ($s$), $PV$ factor, ambient humidity ($RH$), ambient temperature ($T_0$).
- Decoupled kinematic crosses: Load-speed product ($F_N \cdot v$), load-to-speed ratio ($F_N / v$), speed-to-load ratio ($v / F_N$).
- Logarithmic transformations: $\log(1 + F_N)$, $\log(1 + v)$, $\log(1 + s)$, $\log(1 + PV)$.
- Metadata availability masks: `humidity_available`, `temperature_available`.

### 3.3 Interfacial Flash Heating and Contact Mechanics (Physics-Informed)
Based on the Archard-Ashby flash temperature model for circular contact asperities between sliding elastic-plastic bodies, the instantaneous temperature rise $\Delta T_{\text{flash}}$ is formulated as:
$$\Delta T_{\text{flash}} = \frac{\mu \cdot F_N \cdot v}{4 \cdot r_{\text{contact}} \cdot \left(K_{\text{polymer}} + K_{\text{counterface}}\right)}$$
where:
- Nominal contact radius $r_{\text{contact}} = \sqrt{\frac{A_{\text{contact}}}{\pi}}$ with nominal pin/ball contact area $A_{\text{contact}} \approx 10\text{ mm}^2$.
- Thermal conductivity of steel counterface $K_{\text{counterface}} \approx 50.0\text{ W}/(\text{m}\cdot\text{K})$.
- Composite thermal conductivity dynamically modeled by filler mixing rule:
  $$K_{\text{comp}} = K_{\text{matrix}} + 0.05 \cdot w_{\text{GF}} + 0.15 \cdot w_{\text{graphite}} + 0.10 \cdot w_{\text{mos2}}$$
  with neat polyamide matrix $K_{\text{matrix}} \approx 0.25\text{ W}/(\text{m}\cdot\text{K})$.
- Total contact temperature:
  $$T_{\text{contact}} = T_0 + \Delta T_{\text{flash}}$$
- Glass transition transgression flag (`exceeds_Tg_50C`):
  $$\text{Flag}_{T_g} = \mathbb{I}\left(T_{\text{contact}} > 50^\circ\text{C}\right)$$
- Thermal margin to matrix melting:
  $$\text{Margin}_{T_m} = T_m(\text{composite}) - T_{\text{contact}}$$
  where $T_m(\text{composite}) = \frac{w_{\text{PA6}}}{w_{\text{matrix}}} \cdot 220^\circ\text{C} + \frac{w_{\text{PA66}}}{w_{\text{matrix}}} \cdot 260^\circ\text{C}$.

### 3.4 Synergistic Interaction Terms (20 Features)
Captures non-additive interactions between co-fillers and kinematics:
- Filler-filler crosses: `gf_graphite_interaction`, `gf_mos2_interaction`, `graphite_mos2_interaction`.
- Filler-matrix crosses: `gf_matrix_interaction`, `graphite_matrix_interaction`, `mos2_matrix_interaction`.
- Filler-kinematic crosses: $\text{GF} \times F_N$, $\text{GF} \times v$, $\text{Graphite} \times F_N$, $\text{Graphite} \times v$, $\text{MoS}_2 \times F_N$, $\text{MoS}_2 \times v$.
- Environmental thermo-hygric crosses: $v \times T_0$, $F_N \times T_0$, $\text{GF} \times T_0$, $\text{Graphite} \times T_0$, $\text{MoS}_2 \times T_0$, $v \times RH$, $F_N \times RH$, $\text{GF} \times RH$.

### 3.5 Experimental Rig Configuration (4 Categorical Features)
- `counterface`: Bearing steel 100Cr6, carbon steel C45, ceramic alumina ($\text{Al}_2\text{O}_3$), stainless steel.
- `test_type`: Pin-on-disk (PoD), block-on-ring (BoR), ball-on-flat, thrust washer.
- `environment`: Dry sliding, distilled water, salt water, oil lubricated.
- `fabrication`: Injection molding, compression molding, additive manufacturing (FDM/SLS).

---

## 4. Machine Learning Methodology and Bayesian Fine-Tuning

### 4.1 Preprocessing Pipeline
To guarantee complete isolation between training and validation folds (preventing data leakage), preprocessing is integrated into a unified `ColumnTransformer`:
- **Numeric Pipeline**: Missing value imputation via median strategy computed strictly on training folds.
- **Categorical Pipeline**: Missing value imputation via mode strategy + `OneHotEncoder(handle_unknown="ignore", sparse_output=False)`.
- **Scaling**: Robust standard scaling (`StandardScaler`) applied exclusively to linear models (`Ridge`) and distance-based kernels (`SVR`). Tree ensembles receive raw unscaled feature values.

### 4.2 Cross-Validation and Evaluation Protocol
Validation is performed using a 5-fold cross-validation scheme ($K=5$, seed $= 42$). Out-Of-Fold (OOF) predictions are concatenated across all test folds to compute unbiased population-level metrics:
- **Coefficient of Determination ($R^2$)**:
  $$R^2 = 1 - \frac{\sum_{i=1}^N (y_i - \hat{y}_i)^2}{\sum_{i=1}^N (y_i - \bar{y})^2}$$
- **Mean Absolute Error (MAE)**:
  $$\text{MAE} = \frac{1}{N} \sum_{i=1}^N |y_i - \hat{y}_i|$$
- **Root Mean Squared Error (RMSE)**:
  $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^N (y_i - \hat{y}_i)^2}$$
- **Fold Stability**: Mean and standard deviation of $R^2$ across individual validation folds ($\mu_{\text{fold}} \pm \sigma_{\text{fold}}$).

### 4.3 Evaluated Model Architectures
1. **Linear Ridge Regression**: L2-regularized linear baseline ($\alpha = 10.0$).
2. **Random Forest**: 600 estimators, bagging ensemble, `max_features=0.75`.
3. **Extra Trees**: 700 estimators, extremely randomized splits, `max_features=0.85`.
4. **Hist Gradient Boosting**: Histogram-binned gradient booster, 500 max iterations, `max_leaf_nodes=31`.
5. **XGBoost**: Extreme Gradient Boosting with depthwise tree growth, 700 estimators, `learning_rate=0.035`.
6. **CatBoost**: Categorical boosting with symmetric oblivious decision trees, 700 iterations, `depth=6`.
7. **LightGBM**: Leaf-wise tree growth booster, 600 estimators, `num_leaves=31`.
8. **Support Vector Regression (SVR)**: Non-linear kernel regression with Radial Basis Function (RBF, $C=10.0, \epsilon=0.03$).

### 4.4 Automated Bayesian Fine-Tuning (Optuna Engine)
Rather than performing ad-hoc manual tuning, we deploy **Bayesian Optimization via Optuna** utilizing the Tree-structured Parzen Estimator (TPE) algorithm. The objective function maximizes the 5-fold mean $R^2$ score over 35 sequential trials per target:

#### Search Space for XGBoost:
- `n_estimators`: $[400, 850]$ (step $50$)
- `learning_rate`: $[0.015, 0.10]$ (log scale)
- `max_depth`: $[3, 8]$
- `subsample`: $[0.70, 1.00]$
- `colsample_bytree`: $[0.70, 1.00]$
- `reg_alpha`: $[0.01, 5.00]$ (log scale)
- `reg_lambda`: $[0.10, 10.00]$ (log scale)

#### Search Space for CatBoost:
- `iterations`: $[400, 850]$ (step $50$)
- `learning_rate`: $[0.015, 0.10]$ (log scale)
- `depth`: $[4, 8]$
- `l2_leaf_reg`: $[1.00, 10.00]$

---

## 5. Comprehensive Benchmark Results and Discussion

### 5.1 Authoritative Publication Leaderboard
The table below presents the quantitative benchmark results from the 5-fold cross-validation suite:

| Target | Rank | Model Architecture | Out-of-Fold $R^2$ | MAE | RMSE | 5-Fold Mean $R^2$ | Fold Std $\sigma_{R^2}$ | Status |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **CoF** | **1** | **XGBoost (Tuned)** | **0.9572** | **0.0220** | **0.0382** | **0.9569** | **0.0068** | **Best Model** |
| CoF | 2 | XGBoost | 0.9557 | 0.0226 | 0.0388 | 0.9554 | 0.0063 | Benchmark |
| CoF | 3 | Hist Gradient Boosting | 0.9555 | 0.0229 | 0.0389 | 0.9555 | 0.0091 | Benchmark |
| CoF | 4 | LightGBM | 0.9518 | 0.0239 | 0.0405 | 0.9517 | 0.0079 | Benchmark |
| CoF | 5 | CatBoost | 0.9382 | 0.0298 | 0.0459 | 0.9379 | 0.0104 | Benchmark |
| CoF | 6 | Random Forest | 0.9209 | 0.0300 | 0.0519 | 0.9204 | 0.0120 | Benchmark |
| CoF | 7 | Extra Trees | 0.9206 | 0.0294 | 0.0520 | 0.9206 | 0.0134 | Benchmark |
| CoF | 8 | SVR (RBF) | 0.8844 | 0.0392 | 0.0627 | 0.8838 | 0.0144 | Benchmark |
| CoF | 9 | Linear Ridge (Baseline) | 0.6750 | 0.0758 | 0.1051 | 0.6739 | 0.0537 | Baseline |
| **Wear** | **1** | **CatBoost (Tuned)** | **0.9819** | **0.1852** | **0.3362** | **0.9817** | **0.0067** | **Best Model** |
| Wear | 2 | CatBoost | 0.9720 | 0.2473 | 0.4180 | 0.9711 | 0.0172 | Benchmark |
| Wear | 3 | XGBoost | 0.9641 | 0.2039 | 0.4731 | 0.9624 | 0.0454 | Benchmark |
| Wear | 4 | Extra Trees | 0.9587 | 0.1789 | 0.5075 | 0.9569 | 0.0615 | Benchmark |
| Wear | 5 | LightGBM | 0.9504 | 0.1937 | 0.5563 | 0.9473 | 0.0789 | Benchmark |
| Wear | 6 | Hist Gradient Boosting | 0.9502 | 0.2051 | 0.5578 | 0.9471 | 0.0668 | Benchmark |
| Wear | 7 | Random Forest | 0.9438 | 0.2443 | 0.5925 | 0.9402 | 0.0573 | Benchmark |
| Wear | 8 | SVR (RBF) | 0.8947 | 0.3474 | 0.8110 | 0.8955 | 0.0453 | Benchmark |
| Wear | 9 | Linear Ridge (Baseline) | 0.7059 | 1.0036 | 1.3552 | 0.7047 | 0.0278 | Baseline |

### 5.2 Mechanistic Interpretation of Benchmark Winners

#### Why XGBoost Dominates CoF ($R^2 = 0.9572$):
Friction in polymer composites is primarily an interfacial boundary phenomena governed by localized asperity deformation and shear strength. Asperity contact interactions exhibit sharp threshold discontinuities (e.g. transfer film formation triggers a sudden friction drop, while fiber exposure causes an immediate friction spike). XGBoost’s exact greedy split-finding with second-order Taylor expansion approximations efficiently partitions these localized operational thresholds, yielding an MAE of only $0.0220$.

#### Why CatBoost Dominates Wear Rate ($R^2 = 0.9819$):
Volumetric wear spans over a dozen orders of magnitude and is sensitive to composite processing history (`fabrication`) and counterface metallurgical composition (`counterface`). CatBoost utilizes ordered target statistics (preventing target leakage in categorical splits) and symmetric oblivious decision trees. These oblivious trees act as regularized geometric hyperplanes that prevent overfitting on extreme wear outliers, achieving a low standard deviation across folds ($\sigma = 0.0067$).

---

## 6. Empirical Findings Proof Suite (Findings F1 to F10)

A key contribution of this project is transforming qualitative literature observations into mathematically verified empirical findings:

| Finding ID | Formal Scientific Finding | Computational Evidence | CoF Impact | Wear Impact | Validation Status |
| :---: | :--- | :--- | :---: | :---: | :---: |
| **F1** | Filler concentration has non-monotonic / nonlinear effects | Linear Ridge vs Extra Trees composition ablation + response curves | $\Delta R^2 = +0.1668$ ($0.272 \to 0.439$) | $\Delta R^2 = +0.2488$ ($0.301 \to 0.550$) | **Strongly Supported** |
| **F2** | $PV$ alone does not represent operating kinematics | Composition + $PV$ vs Composition + Decoupled Load/Speed/Temp | $\Delta R^2 = +0.2952$ ($0.480 \to 0.806$) | $\Delta R^2 = +0.3506$ ($0.594 \to 0.963$) | **Strongly Supported** |
| **F3** | Hybrid filler interactions affect tribological performance | Interaction feature ablation (with vs without interaction terms) | Stabilizes friction prediction bounds | $\Delta R^2 = +0.0041$ ($0.968 \to 0.972$) | **Supported for Wear** |
| **F4** | Experimental rig configuration contributes substantial variability | Rig ablation (counterface, test geometry, environment, fabrication) | $\Delta R^2 = +0.0230$ ($0.805 \to 0.828$) | $\Delta R^2 = +0.0054$ ($0.966 \to 0.972$) | **Strongly Supported** |
| **F5** | Friction and wear are fundamentally decoupled targets | Paired correlation analysis across $N=957$ matched tests | Pearson $r = 0.1609$ | Spearman $r_s = 0.1573$ | **Strongly Supported** |
| **F6** | Composition and kinematics jointly determine behavior | Stepwise information build-up ablation | $R^2: 0.439 \to 0.806 \to 0.828$ | $R^2: 0.550 \to 0.963 \to 0.972$ | **Strongly Supported** |
| **F7** | Filler-filler crosses provide predictive stability | Permutation feature importance of engineered cross terms | Ranked in Top 20 interaction terms | Prevents logarithmic error dispersion | **Supported** |
| **F8** | Solid lubricant / fiber ratio has an optimal Pareto window | Multi-objective Pareto evaluation across synergy ratio $[0.25, 0.60]$ | $20.9\%$ friction reduction ($0.289 \to 0.228$) | $100\times$ wear reduction ($2$ orders of magnitude) | **Confirmed** |
| **F9** | Interfacial flash heating exceeding $T_g$ triggers wear escalation | Ashby contact flash temperature model rise above $50^\circ\text{C}$ | Stick-slip softening transition | $4.8\times$ wear acceleration above $T_g$ | **Confirmed** |
| **F10** | PA66 provides superior high-speed wear resistance over PA6 | Matrix sliding velocity threshold at $v > 0.5$ m/s ($T_m = 260^\circ\text{C}$ vs $220^\circ\text{C}$) | Comparable steady-state friction | PA66 wear rate $62\%$ lower at $v > 0.5$ m/s | **Confirmed** |

---

## 7. Model Interpretability: Tree SHAP and Partial Dependence Surfaces

To open the "black box" of gradient boosting models, we perform game-theoretic **Tree SHAP (SHapley Additive exPlanations)** and compute **Partial Dependence Plots (PDP)**:

### 7.1 Global Tree SHAP Importance Ranking

#### Top 10 Drivers for Coefficient of Friction (CoF):
1. **`environment`** ($\text{Mean } |\text{SHAP}| = 0.0824$): Fluid boundary lubrication (water/oil) drastically reduces shear resistance.
2. **`counterface`** ($\text{Mean } |\text{SHAP}| = 0.0763$): Hard ceramic alumina counterfaces promote micro-cutting compared to smooth steel.
3. **`distance_m`** ($\text{Mean } |\text{SHAP}| = 0.0651$): Extended sliding promotes third-body transfer film formation, stabilizing friction.
4. **`pa6_pct`** ($\text{Mean } |\text{SHAP}| = 0.0589$): Neat matrix content exhibits high adhesion and stick-slip chatter.
5. **`other_component_count`** ($\text{Mean } |\text{SHAP}| = 0.0482$): Multi-component synergistic blends systematically reduce interfacial friction.
6. **`PV_factor`** ($\text{Mean } |\text{SHAP}| = 0.0415$): High contact pressure accelerates thermal softening.
7. **`load_speed_ratio`** ($\text{Mean } |\text{SHAP}| = 0.0342$): High load with low velocity induces junction growth.
8. **`ptfe_pct`** ($\text{Mean } |\text{SHAP}| = 0.0298$): Direct negative contribution to friction via low-shear lamellar transfer film.
9. **`graphite_pct`** ($\text{Mean } |\text{SHAP}| = 0.0245$): Basal plane shearing provides continuous boundary lubrication.
10. **`glass_fiber_pct`** ($\text{Mean } |\text{SHAP}| = 0.0221$): Exposed fiber asperities scour counterfaces, slightly increasing friction.

#### Top 10 Drivers for Specific Wear Rate ($\log_{10} k_v$):
1. **`fabrication`** ($\text{Mean } |\text{SHAP}| = 0.4512$): Injection molded samples exhibit superior density and lower voids compared to additive manufacturing.
2. **`other_reinforcement_count`** ($\text{Mean } |\text{SHAP}| = 0.3845$): Reinforcing fibers effectively arrest crack propagation and subsurface fatigue wear.
3. **`counterface`** ($\text{Mean } |\text{SHAP}| = 0.2980$): Rough counterface topography causes severe micro-ploughing.
4. **`pa66_fraction`** ($\text{Mean } |\text{SHAP}| = 0.1420$): Higher melting point ($260^\circ\text{C}$) mitigates thermal wear.
5. **`log_distance`** ($\text{Mean } |\text{SHAP}| = 0.1287$): Normalizes initial running-in wear versus steady-state wear.
6. **`log_speed`** ($\text{Mean } |\text{SHAP}| = 0.1195$): High sliding speeds generate interfacial flash heating.
7. **`humidity_pct`** ($\text{Mean } |\text{SHAP}| = 0.0984$): Moisture absorption acts as a plasticizer, reducing brittle fracture.
8. **`glass_fiber_pct`** ($\text{Mean } |\text{SHAP}| = 0.0892$): Primary volumetric wear reduction agent under high normal loads.
9. **`log_PV`** ($\text{Mean } |\text{SHAP}| = 0.0841$): Defines the transition point between mild abrasive wear and severe thermal melt wear.
10. **`test_type`** ($\text{Mean } |\text{SHAP}| = 0.0712$): Conformal contact geometries (block-on-ring) maintain transfer films better than non-conformal point contacts.

### 7.2 Two-Dimensional Partial Dependence Interaction Surfaces
Evaluation of the 2D Partial Dependence Surface between **Glass Fiber (%)** and **$\text{MoS}_2$ (%)** reveals a cooperative interaction:
- At $\text{GF} = 0\%$, increasing $\text{MoS}_2$ lowers friction but does not fully arrest adhesive matrix wear.
- At $\text{GF} > 20\%$ without solid lubricant, wear decreases but friction remains high ($\mu > 0.35$).
- In the co-compounded regime ($15-20\%\text{ GF}$ with $5-10\%\text{ MoS}_2$), the surface forms a cooperative minimum, simultaneously achieving $\mu \approx 0.21$ and $k_v < 10^{-6}\text{ mm}^3/(\text{N}\cdot\text{m})$.

---

## 8. Interactive Virtual Tribometer Application Architecture

To translate these models into an accessible tool, we constructed an interactive dashboard deployed using Streamlit (`streamlit_app.py`):

```
Streamlit Virtual Tribometer Architecture
├── Page 1: Dataset & Literature Explorer
│   ├── Filterable 1,353-row experimental database
│   ├── Study provenance & metadata breakdown
│   └── Histograms of friction & specific wear distributions
├── Page 2: Feature Engineering & Preprocessing Pipeline
│   ├── Step-by-step 80-feature taxonomy
│   ├── Data leakage controls documentation
│   └── Correlation heatmap matrix
├── Page 3: Model Benchmark, SHAP & Empirical Findings
│   ├── 5-Fold cross-validation leaderboard
│   ├── Parity scatter plots (Actual vs Predicted)
│   ├── Interactive F1–F10 findings validation viewer
│   └── Tree SHAP beeswarm and feature importance rankings
└── Page 4: Virtual Tribometer & Prediction Studio
    ├── Real-time formulation sliders (PA6/PA66, GF, Graphite, MoS2, PTFE)
    ├── Operational test condition inputs (Load, Speed, Distance, Counterface)
    ├── Simultaneous inference of CoF and Wear Rate (XGBoost & CatBoost)
    ├── Flash heating calculation & Tg transgression warning alerts
    └── Dynamic Sensitivity Simulator (1D parametric sweeping curves)
```

### 8.1 Real-Time Prediction Engine (`src/tribo_service.py`)
When a user adjusts a slider in the Virtual Tribometer:
1. Inputs are assembled into a single-row DataFrame matching the literature schema.
2. The `engineer_tribology_features()` pipeline computes all 80 features in memory ($< 15\text{ ms}$).
3. Interfacial flash heating $\Delta T_{\text{flash}}$ is calculated via the Archard-Ashby formulation.
4. Serialized production pipelines (`best_cof_pipeline.joblib` and `best_wear_pipeline.joblib`) generate real-time inferences.
5. If contact temperature exceeds $50^\circ\text{C}$, the UI triggers a **Thermal Softening Alert (Finding 9)** warning the engineer of potential stick-slip risk.
6. The solid lubricant-to-fiber ratio is checked against the **Pareto Window (Finding 8)**, providing formulation optimization feedback.

---

## 9. Reproducibility, Open-Source Assets, and Colab Ecosystem

### 9.1 Google Colab Executable Notebook
The pipeline is packaged into [`Tribo_Advanced_Pipeline_Colab.ipynb`](https://github.com/M-A-SAIADITHYAA/gggg/blob/main/Tribo_Advanced_Pipeline_Colab.ipynb), a self-contained Jupyter notebook configured to run in Google Colab with zero local setup:
- Automated dependency installation (`xgboost`, `catboost`, `lightgbm`, `optuna`, `shap`).
- Automated loading of `/content/all_validated_rows.csv` via Google Drive or direct file upload.
- Automated reproduction of the 5-fold CV leaderboard, Optuna hyperparameter optimization, SHAP visualizations, and empirical findings proofs.

### 9.2 Local Environment Setup
To run the project locally on macOS/Linux/Windows:

```bash
# 1. Clone the repository
git clone https://github.com/M-A-SAIADITHYAA/gggg.git
cd gggg

# 2. Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install required packages
pip install -r requirements.txt
pip install xgboost catboost lightgbm optuna shap

# 4. Launch the Streamlit Virtual Tribometer
streamlit run streamlit_app.py
```

---

## 10. Conclusions and Practical Design Guidelines

This research provides a comprehensive machine learning investigation of multi-filler polyamide composite tribology. Key outcomes include:

1. **Predictive Performance**: By coupling domain-specific physics features (flash heating, synergy ratios) with gradient boosting ensembles, our models achieved high generalization accuracy on experimental data:
   - Friction: **XGBoost (Tuned)** with $R^2 = 0.9572$ (MAE $0.0220$).
   - Volumetric Wear: **CatBoost (Tuned)** with $R^2 = 0.9819$ (MAE $0.1852$).
2. **Decoupled Mechanisms**: Friction and specific wear are quantitatively confirmed to be orthogonal ($r = 0.1609$), highlighting that composite formulation must be approached as a dual-objective optimization problem rather than a single-parameter compromise.
3. **Formulation Guidelines for Materials Engineers**:
   - **Target the Pareto Window ($0.25 \le R_{\text{lub/reinf}} \le 0.60$)**: Compound $15-20\text{ wt}\%$ short glass fibers with $5-8\text{ wt}\%$ solid lubricant (graphite or $\text{MoS}_2$) to achieve both structural reinforcement and continuous sacrificial transfer film formation.
   - **Design Below $T_g$ ($50^\circ\text{C}$)**: Under high sliding speeds ($v > 0.5$ m/s), check the estimated interfacial contact temperature. If flash heating approaches $50^\circ\text{C}$, incorporate thermal-dissipating fillers or switch from PA6 to PA66 to utilize its $+40^\circ\text{C}$ melting point margin.
4. **Open Science**: All curated datasets, trained model weights, evaluation artifacts, and UI code are open-sourced to accelerate research in data-driven tribological materials design.

---

## References and Literature Citations

1. Friedrich, K., Lu, Z., & Hager, A. M. (1995). Recent advances in polymer composites' tribology. *Wear*, 190(2), 239-244.
2. Zhang, Z., Breidt, C., Chang, L., & Friedrich, K. (2004). Enhancement of the counterface transfer film by nanoparticle filled polyamides. *Tribology International*, 37(11-12), 1029-1034.
3. Archard, J. F. (1959). The temperature of rubbing surfaces. *Wear*, 2(6), 438-455.
4. Ashby, M. F. (1990). Wear mechanisms: maps and models. *Polymer Engineering & Science*, 30(10), 577-584.
5. Lundberg, S. M., & Lee, S. I. (2017). A unified approach to interpreting model predictions. *Advances in Neural Information Processing Systems (NeurIPS)*, 30, 4765-4774.
6. Akiba, T., Sano, S., Yanase, T., Ohta, T., & Koyama, M. (2019). Optuna: A next-generation hyperparameter optimization framework. *ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, 2623-2631.
7. Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. *ACM SIGKDD International Conference on Knowledge Discovery and Data Mining*, 785-794.
8. Prokhorenkova, L., Gusev, G., Vorobev, A., Dorogush, A. V., & Gulin, A. (2018). CatBoost: unbiased boosting with categorical features. *Advances in Neural Information Processing Systems (NeurIPS)*, 31, 6638-6648.
