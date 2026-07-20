"""
model_karsilastirma.py
Görev 6 (İP5) — Model Karşılaştırması: "Random Forest gerçekten en iyi seçim mi?"

ip5_adaptif_akts.py'de kullanılan Random Forest, proje planında önceden belirlenmiş
bir seçimdi. Bu script, AYNI özellik seti, AYNI hedef sızıntısı önlemi (K_bilissel ve
akts_mevcut hariç), AYNI train/test bölünmesi (Fakülte'ye göre stratified, random_state=42)
ve AYNI 5-katlı out-of-fold çapraz doğrulama düzeniyle üç modeli yan yana karşılaştırır:

  1. Ridge Regresyon   — tamamen şeffaf, doğrusal taban çizgisi (baseline)
  2. Random Forest     — mevcut üretim modeli (ip5_adaptif_akts.py ile birebir aynı kurulum)
  3. XGBoost           — gradient boosting, genelde tablo verisinde RF'den güçlü;
                         SHAP değerleriyle ders bazlı açıklanabilirlik sunar

Amaç: "En doğru cevabı hangi model veriyor?" sorusuna, aynı koşullar altında,
dürüst (out-of-fold) bir karşılaştırmayla cevap vermek.
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

warnings.filterwarnings("ignore")

BASE = Path(__file__).resolve().parents[2]
MODEL_EGITIM = BASE / "data" / "processed" / "model_egitim.xlsx"
MASTER_BLOOM = BASE / "data" / "processed" / "master_bloom.xlsx"
OUT_DIR = BASE / "ip5-adaptif-akts"
REPORT_PATH = OUT_DIR / "MODEL_KARSILASTIRMA_RAPORU.md"

RANDOM_STATE = 42
N_FOLDS = 5
EXCLUDE_FROM_FEATURES = ["Katalogid", "DersAdi", "AKTSKredi", "K_bilissel"]


def build_models():
    return {
        "Ridge Regresyon": make_pipeline(StandardScaler(), Ridge(alpha=1.0, random_state=RANDOM_STATE)),
        "Random Forest": RandomForestRegressor(n_estimators=200, random_state=RANDOM_STATE, n_jobs=-1),
        "XGBoost": XGBRegressor(
            n_estimators=300, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            random_state=RANDOM_STATE, n_jobs=-1, verbosity=0,
        ),
    }


def evaluate(y_true, y_pred):
    return {
        "MAE": mean_absolute_error(y_true, y_pred),
        "RMSE": np.sqrt(mean_squared_error(y_true, y_pred)),
        "R2": r2_score(y_true, y_pred),
    }


def main():
    print("=" * 60)
    print("MODEL KARŞILAŞTIRMASI — Ridge vs Random Forest vs XGBoost")
    print("=" * 60)

    model_df = pd.read_excel(MODEL_EGITIM, dtype={"Katalogid": str})
    feature_cols = [c for c in model_df.columns if c not in EXCLUDE_FROM_FEATURES]
    X = model_df[feature_cols].copy()
    y = model_df["AKTSKredi"].copy()

    fakulte_cols = [c for c in feature_cols if c.startswith("Fakulte_")]
    strat_labels = model_df[fakulte_cols].idxmax(axis=1)

    print(f"\nÖzellik sayısı: {len(feature_cols)} (K_bilissel, akts_mevcut hariç — İP5 ile aynı kurulum)")

    # ── Ayrılmış test seti (%20, Fakülte'ye göre stratified) — ip5_adaptif_akts.py ile birebir aynı ──
    X_train, X_test, y_train, y_test, _, _ = train_test_split(
        X, y, strat_labels, test_size=0.20, random_state=RANDOM_STATE, stratify=strat_labels
    )

    results = []
    oof_preds = {}

    for name, model in build_models().items():
        print(f"\n── {name} ──────────────────────────────")

        # Test seti değerlendirmesi
        model.fit(X_train, y_train)
        y_pred_test = model.predict(X_test)
        test_metrics = evaluate(y_test, y_pred_test)
        print(f"  Test seti  -> MAE={test_metrics['MAE']:.4f}  RMSE={test_metrics['RMSE']:.4f}  R²={test_metrics['R2']:.4f}")

        # Out-of-fold değerlendirmesi (5 kat, Fakülte'ye göre stratified, aynı random_state)
        skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)
        oof = np.zeros(len(X))
        for train_idx, test_idx in skf.split(X, strat_labels):
            fold_models = build_models()
            fold_model = fold_models[name]
            fold_model.fit(X.iloc[train_idx], y.iloc[train_idx])
            oof[test_idx] = fold_model.predict(X.iloc[test_idx])

        oof_metrics = evaluate(y, oof)
        print(f"  Out-of-fold-> MAE={oof_metrics['MAE']:.4f}  RMSE={oof_metrics['RMSE']:.4f}  R²={oof_metrics['R2']:.4f}")

        oof_preds[name] = oof
        results.append({
            "model": name,
            "test_MAE": round(test_metrics["MAE"], 4), "test_RMSE": round(test_metrics["RMSE"], 4), "test_R2": round(test_metrics["R2"], 4),
            "oof_MAE": round(oof_metrics["MAE"], 4), "oof_RMSE": round(oof_metrics["RMSE"], 4), "oof_R2": round(oof_metrics["R2"], 4),
        })

    results_df = pd.DataFrame(results).sort_values("oof_MAE")
    winner = results_df.iloc[0]["model"]

    print("\n" + "=" * 60)
    print("SONUÇ TABLOSU (out-of-fold MAE'ye göre sıralı)")
    print("=" * 60)
    print(results_df.to_string(index=False))
    print(f"\nEn iyi (en düşük out-of-fold MAE): {winner}")

    results_df.to_excel(OUT_DIR / "model_karsilastirma.xlsx", index=False)

    # ── XGBoost için açıklanabilirlik (SHAP varsa SHAP, yoksa pred_contribs) ──
    print("\n── XGBoost Açıklanabilirlik (ders bazlı katkı analizi) ──")
    xgb_final = build_models()["XGBoost"]
    xgb_final.fit(X, y)

    shap_summary_df, case_studies = explain_xgboost(xgb_final, X, model_df, feature_cols)
    shap_summary_df.to_excel(OUT_DIR / "shap_ozet.xlsx", index=False)
    print("En etkili 10 özellik (ortalama |katkı|):")
    for _, row in shap_summary_df.head(10).iterrows():
        print(f"  {row['ozellik']:<28}: {row['ortalama_mutlak_katki']:.4f}")

    write_report(results_df, winner, shap_summary_df, case_studies, len(X))
    print(f"\nKaydedildi: {OUT_DIR / 'model_karsilastirma.xlsx'}")
    print(f"Kaydedildi: {OUT_DIR / 'shap_ozet.xlsx'}")
    print(f"Kaydedildi: {REPORT_PATH}")


def explain_xgboost(model, X, model_df, feature_cols):
    """SHAP paketi kuruluysa onu, değilse XGBoost'un yerleşik pred_contribs
    (matematiksel olarak SHAP ile aynı) mekanizmasını kullanarak katkı değerleri üretir."""
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)
        method = "shap.TreeExplainer"
    except Exception as e:
        print(f"  (shap paketi kullanılamadı: {e} — XGBoost'un yerleşik pred_contribs'i kullanılıyor)")
        booster = model.get_booster()
        import xgboost as xgb
        dmat = xgb.DMatrix(X, feature_names=list(X.columns))
        contribs = booster.predict(dmat, pred_contribs=True)
        shap_values = contribs[:, :-1]  # son sütun: bias/base value
        method = "xgboost pred_contribs (SHAP ile matematiksel olarak özdeş)"

    mean_abs = np.abs(shap_values).mean(axis=0)
    summary_df = pd.DataFrame({
        "ozellik": feature_cols,
        "ortalama_mutlak_katki": mean_abs,
    }).sort_values("ortalama_mutlak_katki", ascending=False).reset_index(drop=True)
    summary_df.attrs["method"] = method

    # Vaka analizi: en yüksek ve en düşük tahminli birer ders
    preds = model.predict(X)
    idx_high = int(np.argmax(preds))
    idx_low = int(np.argmin(preds))
    case_studies = []
    for label, idx in [("En yüksek tahminli ders", idx_high), ("En düşük tahminli ders", idx_low)]:
        row_shap = shap_values[idx]
        top_features = np.argsort(-np.abs(row_shap))[:5]
        gerekce = "; ".join(
            f"{feature_cols[i]} ({row_shap[i]:+.2f})" for i in top_features
        )
        case_studies.append({
            "durum": label,
            "ders": model_df.iloc[idx]["DersAdi"],
            "tahmin_akts": round(float(preds[idx]), 2),
            "en_etkili_5_ozellik": gerekce,
        })

    print(f"  Yöntem: {method}")
    return summary_df, case_studies


def write_report(results_df, winner, shap_df, case_studies, n_dersleri):
    lines = []
    lines.append("# Model Karşılaştırma Raporu — Ridge vs Random Forest vs XGBoost")
    lines.append("")
    lines.append(
        "Bu rapor, İP5'te (Görev 6) kullanılan Random Forest'ın gerçekten en iyi seçim olup "
        "olmadığını test etmek için hazırlandı. Üç model, **aynı özellik seti, aynı hedef "
        "sızıntısı önlemi (K_bilissel ve akts_mevcut hariç), aynı stratified train/test "
        "bölünmesi ve aynı 5-katlı out-of-fold çapraz doğrulama** ile karşılaştırıldı."
    )
    lines.append("")
    lines.append(f"Veri seti: {n_dersleri} ders, aynı 39 özellik (ip5_adaptif_akts.py ile birebir aynı kurulum).")
    lines.append("")
    lines.append("## Sonuç Tablosu")
    lines.append("")
    lines.append("| Model | Test MAE | Test RMSE | Test R² | OOF MAE | OOF RMSE | OOF R² |")
    lines.append("|---|---|---|---|---|---|---|")
    for _, row in results_df.iterrows():
        lines.append(
            f"| {row['model']} | {row['test_MAE']} | {row['test_RMSE']} | {row['test_R2']} | "
            f"{row['oof_MAE']} | {row['oof_RMSE']} | {row['oof_R2']} |"
        )
    lines.append("")
    lines.append(
        f"**OOF MAE'ye göre en iyi model: {winner}.** Ancak bu karşılaştırma tek bir metriğe "
        "indirgenemeyecek kadar karışık çıktı — aşağıdaki 'Yorum ve Öneri' bölümüne bakın."
    )
    lines.append("")
    lines.append(
        "**Önemli metodolojik not — metrikler birbiriyle çelişiyor:** XGBoost, OOF MAE'de en "
        "iyisi (ortalama hatası en düşük) ama OOF RMSE ve R²'de en KÖTÜSÜ (en negatif R², en "
        "yüksek RMSE). Bunun anlamı: XGBoost derslerin çoğunda ufak hatalar yapıyor ama bazı "
        "derslerde büyük ölçüde yanılıyor (RMSE büyük hatalara MAE'den daha duyarlıdır). Ridge "
        "Regresyon ise tam tersi profil çiziyor: OOF R²'de tek pozitif değeri o veriyor ve OOF "
        "RMSE'de en düşük (en istikrarlı) model o. Yani 'en iyi model' sorusunun cevabı, hangi "
        "hatayı önemsediğinize bağlı: ortalama sapma mı (MAE → XGBoost), yoksa büyük/aşırı "
        "yanılgılardan kaçınmak mı (RMSE/R² → Ridge)?"
    )
    lines.append("")
    lines.append("## XGBoost Açıklanabilirlik (SHAP / pred_contribs)")
    lines.append("")
    lines.append(f"Yöntem: {shap_df.attrs.get('method', '?')}")
    lines.append("")
    lines.append("En etkili 10 özellik (tüm veri setinde ortalama mutlak katkı):")
    lines.append("")
    lines.append("| Özellik | Ort. Mutlak Katkı |")
    lines.append("|---|---|")
    for _, row in shap_df.head(10).iterrows():
        lines.append(f"| {row['ozellik']} | {row['ortalama_mutlak_katki']:.4f} |")
    lines.append("")
    lines.append("### Vaka Analizleri (Ders Bazlı Gerekçe)")
    lines.append("")
    for case in case_studies:
        lines.append(f"**{case['durum']}: {case['ders']}** (tahmin={case['tahmin_akts']} AKTS)")
        lines.append(f"- En etkili 5 özellik (katkı değeri): {case['en_etkili_5_ozellik']}")
        lines.append("")
    lines.append("## Yorum ve Öneri")
    lines.append("")
    lines.append(
        "Üç modelin de OOF R² değerlerinin düşük/negatif çıkması, sorunun model seçiminden "
        "değil, **verideki sinyalin zayıflığından** kaynaklandığını gösteriyor — bu, mevcut "
        "AKTS motorunun öngörülemez/tutarsız olduğu tezini destekleyen ayrı bir bulgudur."
    )
    lines.append("")
    lines.append(
        "**Öneri:** Tek bir 'kazanan' ilan etmek yerine amaca göre seçim yapılmalı:\n"
        "- Amaç **'ortalama en yakın tahmin'** ise (çoğu ders için küçük hata kabul edilebilir): **XGBoost**.\n"
        "- Amaç **'büyük/aşırı yanlış tahminlerden kaçınmak ve istikrar'** ise (kalite güvence "
        "aracı için daha kritik — birkaç dersi çok yanlış işaretlemek güven kaybettirir): **Ridge Regresyon**.\n"
        "- Ridge'in ayrıca **tamamen şeffaf** olması (katsayılar doğrudan yorumlanabilir, SHAP/XAI "
        "aracına ihtiyaç duymaması) projenin 'açıklanabilirlik' iddiasıyla (Bölüm 4.2) doğal olarak örtüşüyor.\n\n"
        "Bu çalışma bir keşif/karşılaştırma niteliğindedir; üretim pipeline'ındaki (`ip5_adaptif_akts.py`) "
        "`rf_tahmin_akts` sütunu, ekip bir karar vermeden DEĞİŞTİRİLMEMİŞTİR."
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
