"""
xgboost_hiperparametre_arama.py
XGBoost'un varsayılan parametrelerle test edildiğinde (model_karsilastirma.py)
OOF RMSE/R² açısından Random Forest'tan daha DENGESİZ çıkması üzerine yapılan
düzgün hiperparametre araması.

Yöntem:
  - Optuna ile Bayesian hiperparametre araması
  - Aynı 5 katlı stratified (Fakülte) out-of-fold düzeni (ip5/ip6 ile birebir aynı, random_state=42)
  - Her fold içinde ayrıca bir early-stopping doğrulama dilimi ayrılır (aşırı öğrenmeyi
    ve büyük hataları önlemek için — tam olarak RF'e kıyasla zayıf kaldığımız nokta)
  - Amaç fonksiyonu: OOF RMSE (XGBoost'un tespit edilen zayıf noktası); MAE ve R² de
    ayrıca raporlanır.

Çıktı: ip5-adaptif-akts/xgboost_en_iyi_parametreler.json
"""

import json
import warnings
from pathlib import Path

import numpy as np
import optuna
import pandas as pd
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)

BASE = Path(__file__).resolve().parents[2]
MODEL_EGITIM = BASE / "data" / "processed" / "model_egitim.xlsx"
OUT_DIR = BASE / "ip5-adaptif-akts"
BEST_PARAMS_PATH = OUT_DIR / "xgboost_en_iyi_parametreler.json"

RANDOM_STATE = 42
N_FOLDS = 5
N_TRIALS = 50
EXCLUDE_FROM_FEATURES = ["Katalogid", "DersAdi", "AKTSKredi", "K_bilissel"]


def load_data():
    model_df = pd.read_excel(MODEL_EGITIM, dtype={"Katalogid": str})
    feature_cols = [c for c in model_df.columns if c not in EXCLUDE_FROM_FEATURES]
    X = model_df[feature_cols].copy()
    y = model_df["AKTSKredi"].copy()
    fakulte_cols = [c for c in feature_cols if c.startswith("Fakulte_")]
    strat_labels = model_df[fakulte_cols].idxmax(axis=1)
    return X, y, strat_labels, feature_cols


def oof_predict(params, X, y, strat_labels):
    """5 katlı stratified CV, her foldda early-stopping ile out-of-fold tahmin üretir."""
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    oof = np.zeros(len(X))

    for train_idx, test_idx in skf.split(X, strat_labels):
        X_tr_full, y_tr_full = X.iloc[train_idx], y.iloc[train_idx]
        strat_tr_full = strat_labels.iloc[train_idx]

        # Early stopping için eğitim foldundan ayrı bir doğrulama dilimi ayır
        X_tr, X_val, y_tr, y_val = train_test_split(
            X_tr_full, y_tr_full, test_size=0.15, random_state=RANDOM_STATE, stratify=strat_tr_full
        )

        model = XGBRegressor(
            **params,
            random_state=RANDOM_STATE,
            n_jobs=-1,
            verbosity=0,
            early_stopping_rounds=30,
            eval_metric="rmse",
        )
        model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)
        oof[test_idx] = model.predict(X.iloc[test_idx])

    return oof


def objective(trial, X, y, strat_labels):
    params = {
        "n_estimators": 1000,  # early stopping gerçek sayıyı belirleyecek
        "max_depth": trial.suggest_int("max_depth", 2, 6),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 5.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 0.1, 10.0, log=True),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
    }
    oof = oof_predict(params, X, y, strat_labels)
    rmse = np.sqrt(mean_squared_error(y, oof))
    return rmse


def main():
    print("=" * 60)
    print("XGBOOST HİPERPARAMETRE ARAMASI (Optuna)")
    print("=" * 60)

    X, y, strat_labels, feature_cols = load_data()
    print(f"\nVeri: {len(X)} ders, {len(feature_cols)} özellik")
    print(f"Amaç: OOF RMSE'yi minimize etmek ({N_TRIALS} deneme, {N_FOLDS} katlı CV, her foldda early stopping)\n")

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE))
    study.optimize(lambda t: objective(t, X, y, strat_labels), n_trials=N_TRIALS, show_progress_bar=False)

    best_params = dict(study.best_params)
    best_params["n_estimators"] = 1000  # early stopping ile birlikte kullanılacak üst sınır

    print(f"En iyi OOF RMSE: {study.best_value:.4f}")
    print(f"En iyi parametreler: {study.best_params}")

    # En iyi parametrelerle tam metrik seti (MAE, RMSE, R²) hesapla
    oof_best = oof_predict(best_params, X, y, strat_labels)
    mae = mean_absolute_error(y, oof_best)
    rmse = np.sqrt(mean_squared_error(y, oof_best))
    r2 = r2_score(y, oof_best)

    print("\n── Ayarlanmış XGBoost — Out-of-Fold Sonuçları ─────────────")
    print(f"  MAE  : {mae:.4f}")
    print(f"  RMSE : {rmse:.4f}")
    print(f"  R²   : {r2:.4f}")

    print("\n── Karşılaştırma (önceki sonuçlarla) ───────────────────────")
    print("  Random Forest        : MAE=0.9285  RMSE=1.7504  R²=-0.1164")
    print("  XGBoost (ayarsız)    : MAE=0.8907  RMSE=1.8396  R²=-0.2330")
    print(f"  XGBoost (ayarlanmış) : MAE={mae:.4f}  RMSE={rmse:.4f}  R²={r2:.4f}")

    result = {
        "best_params": best_params,
        "oof_metrics": {"MAE": round(mae, 4), "RMSE": round(rmse, 4), "R2": round(r2, 4)},
        "n_trials": N_TRIALS,
        "n_folds": N_FOLDS,
        "random_state": RANDOM_STATE,
    }
    BEST_PARAMS_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nKaydedildi: {BEST_PARAMS_PATH}")


if __name__ == "__main__":
    main()
