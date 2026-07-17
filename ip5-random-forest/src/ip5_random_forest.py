"""
ip5_random_forest.py
Görev 6 (Bölüm 10) — Adaptif AKTS Hesaplayan Tahmin Modeli Oluşturma.

Pipeline Aşama 8-11 (README.md, Bölüm 14.2):
  8  Random Forest eğitimi         -> model
  9  RF tahmini                    -> rf_tahmin_akts
  10 Kural tabanlı AKTS            -> kural_akts
  11 Adaptif AKTS                  -> adaptif_akts

Kararlar (README.md Bölüm 15 önerileri uygulanmıştır):
  Karar 1: RandomForestRegressor(n_estimators=200, random_state=42), Fakülte'ye göre
           stratified train/test bölünmesi.
  Karar 2: K_bilissel / K_profil / K_etkinlik modele ÖZELLİK olarak verilmez
           (Seçenek b) — RF ve kural tabanlı bileşen birbirinden bağımsız kalır.
           akts_mevcut (AKTSKredi) da hedef sızıntısını önlemek için özellik değildir.
  Karar 3: adaptif_akts birden çok ağırlık şemasıyla hesaplanır (duyarlılık analizi),
           birincil şema 0.70/0.30'dur.
  Karar 4: Sapma eşikleri hem mutlak hem yüzdesel olarak raporlanır.
  Karar 5: MAE, RMSE, R² raporlanır; "iyi taklit paradoksu" out-of-fold tahminle
           azaltılır (bkz. aşağıdaki not).
  Karar 6: feature_importances_ ile XAI tablosu üretilir.

Not (Karar 5 detayı - "iyi taklit paradoksu"):
  Model tüm veriyle eğitilip aynı veriye tahmin yaparsa (in-sample), RF neredeyse
  ezberleyerek AKTSKredi'yi birebir taklit eder ve hiçbir ders sapma göstermez.
  Bunun önüne geçmek için rf_tahmin_akts, 5 katlı (Fakülte'ye göre stratified)
  çapraz doğrulama ile OUT-OF-FOLD üretilir: her ders, o dersin bulunmadığı bir
  fold'da eğitilen modelden tahmin alır. Model kalitesi metrikleri (MAE/RMSE/R²)
  ayrıca ayrılmış bir train/test bölünmesi üzerinden de raporlanır.
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

warnings.filterwarnings("ignore")

BASE = Path(__file__).resolve().parents[2]
MODEL_EGITIM = BASE / "data" / "processed" / "model_egitim.xlsx"
MASTER_BLOOM = BASE / "data" / "processed" / "master_bloom.xlsx"
OUT_DIR = BASE / "data" / "processed"
REPORT_PATH = BASE / "ip5-random-forest" / "IP5_SONUC_RAPORU.md"

RANDOM_STATE = 42
N_ESTIMATORS = 200
N_FOLDS = 5

# Karar 2b: kural tabanlı katsayılar ve hedef değişken RF özelliği DEĞİLDİR.
EXCLUDE_FROM_FEATURES = ["Katalogid", "DersAdi", "AKTSKredi", "K_bilissel"]

# Karar 3: duyarlılık analizi için denenecek ağırlık şemaları (rf_agirlik, kural_agirlik)
WEIGHT_SCHEMES = [(0.50, 0.50), (0.60, 0.40), (0.70, 0.30), (0.80, 0.20)]
PRIMARY_WEIGHTS = (0.70, 0.30)

# Karar 4: sapma eşikleri
def karar_ver(sapma_pct: float) -> str:
    a = abs(sapma_pct)
    if a < 10:
        return "Güçlü uyum"
    if a < 30:
        return "Kabul edilebilir"
    return "İncelenmeli"


def main():
    print("=" * 60)
    print("İP5 — RANDOM FOREST + ADAPTİF AKTS")
    print("=" * 60)

    print(f"\nYükleniyor: {MODEL_EGITIM.name}")
    model_df = pd.read_excel(MODEL_EGITIM, dtype={"Katalogid": str})
    print(f"  {model_df.shape[0]} satır, {model_df.shape[1]} sütun")

    print(f"Yükleniyor: {MASTER_BLOOM.name}")
    bloom_df = pd.read_excel(MASTER_BLOOM, dtype={"Katalogid": str})
    print(f"  {bloom_df.shape[0]} satır, {bloom_df.shape[1]} sütun")

    # ── Aşama 8: Random Forest eğitimi ──────────────────────────────────────
    feature_cols = [c for c in model_df.columns if c not in EXCLUDE_FROM_FEATURES]
    X = model_df[feature_cols].copy()
    y = model_df["AKTSKredi"].copy()

    # Stratified anahtar: Fakülte one-hot sütunlarından tek bir etiket türet
    fakulte_cols = [c for c in feature_cols if c.startswith("Fakulte_")]
    strat_labels = model_df[fakulte_cols].idxmax(axis=1)

    print(f"\nÖzellik sayısı (X): {len(feature_cols)}")
    print(f"Hariç tutulan sütunlar: {EXCLUDE_FROM_FEATURES}")

    # Karar 5 — dürüst model kalitesi metrikleri (ayrılmış test seti)
    X_train, X_test, y_train, y_test, strat_train, strat_test = train_test_split(
        X, y, strat_labels, test_size=0.20, random_state=RANDOM_STATE, stratify=strat_labels
    )
    eval_model = RandomForestRegressor(n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE, n_jobs=-1)
    eval_model.fit(X_train, y_train)
    y_pred_test = eval_model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    r2 = r2_score(y_test, y_pred_test)

    print("\n── Model Kalitesi (ayrılmış %20 test seti) ──────────────")
    print(f"  MAE  : {mae:.4f} AKTS")
    print(f"  RMSE : {rmse:.4f} AKTS")
    print(f"  R²   : {r2:.4f}")

    # ── Aşama 9: RF tahmini — out-of-fold (tüm veri için, ezberleme riski olmadan) ──
    print(f"\n{N_FOLDS} katlı stratified (Fakülte) çapraz doğrulama ile out-of-fold tahmin üretiliyor...")
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    rf_oof = np.zeros(len(X))
    fold_importances = []

    for fold_i, (train_idx, test_idx) in enumerate(skf.split(X, strat_labels), start=1):
        fold_model = RandomForestRegressor(n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE, n_jobs=-1)
        fold_model.fit(X.iloc[train_idx], y.iloc[train_idx])
        rf_oof[test_idx] = fold_model.predict(X.iloc[test_idx])
        fold_importances.append(fold_model.feature_importances_)
        print(f"  Fold {fold_i}/{N_FOLDS} tamamlandı ({len(test_idx)} ders tahmin edildi)")

    model_df["rf_tahmin_akts"] = rf_oof.round(4)

    oof_mae = mean_absolute_error(y, rf_oof)
    oof_rmse = np.sqrt(mean_squared_error(y, rf_oof))
    oof_r2 = r2_score(y, rf_oof)
    print("\n── Model Kalitesi (tüm veri, out-of-fold) ────────────────")
    print(f"  MAE  : {oof_mae:.4f} AKTS")
    print(f"  RMSE : {oof_rmse:.4f} AKTS")
    print(f"  R²   : {oof_r2:.4f}")

    # ── Karar 6 — XAI: feature importance (tam veriyle eğitilmiş final model üzerinden) ──
    final_model = RandomForestRegressor(n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE, n_jobs=-1)
    final_model.fit(X, y)
    importance_df = pd.DataFrame({
        "ozellik": feature_cols,
        "onem_derecesi": final_model.feature_importances_,
    }).sort_values("onem_derecesi", ascending=False).reset_index(drop=True)

    print("\n── En Önemli 10 Özellik (feature_importances_) ───────────")
    for _, row in importance_df.head(10).iterrows():
        print(f"  {row['ozellik']:<28}: {row['onem_derecesi']:.4f}")

    # ── Aşama 10: Kural tabanlı AKTS ─────────────────────────────────────────
    # model_df zaten K_bilissel içeriyor (model_egitim.xlsx'ten) — merge çakışmasını
    # önlemek için bloom_df'ten sadece K_profil/K_etkinlik (İP4 çıktısı) alınır.
    k_cols = ["Katalogid", "K_profil", "K_etkinlik", "Fakulte", "alan_grubu"]
    merged = model_df.merge(bloom_df[k_cols], on="Katalogid", how="left")

    merged["kural_akts"] = (
        merged["AKTSKredi"] * merged["K_etkinlik"] * merged["K_profil"] * merged["K_bilissel"]
    ).round(4)

    # ── Aşama 11: Adaptif AKTS (Karar 3 — duyarlılık analizi) ───────────────
    for w_rf, w_kural in WEIGHT_SCHEMES:
        col = f"adaptif_akts_{int(w_rf*100)}_{int(w_kural*100)}"
        merged[col] = (w_rf * merged["rf_tahmin_akts"] + w_kural * merged["kural_akts"]).round(4)

    primary_col = f"adaptif_akts_{int(PRIMARY_WEIGHTS[0]*100)}_{int(PRIMARY_WEIGHTS[1]*100)}"
    merged["adaptif_akts"] = merged[primary_col]

    # ── Sapma ve karar (Karar 4) ─────────────────────────────────────────────
    merged["sapma"] = (merged["adaptif_akts"] - merged["AKTSKredi"]).round(4)
    merged["sapma_yuzde"] = (merged["sapma"] / merged["AKTSKredi"] * 100).round(2)
    merged["karar"] = merged["sapma_yuzde"].apply(karar_ver)
    merged["gerekce"] = merged.apply(
        lambda r: (
            f"AKTS_mevcut={r['AKTSKredi']:.1f} | rf_tahmin={r['rf_tahmin_akts']:.2f} | "
            f"kural_akts={r['kural_akts']:.2f} (K_bilissel={r['K_bilissel']:.2f}, "
            f"K_profil={r['K_profil']:.2f}, K_etkinlik={r['K_etkinlik']:.2f}) | "
            f"adaptif={r['adaptif_akts']:.2f} | sapma={r['sapma_yuzde']:+.1f}%"
        ),
        axis=1,
    )

    print("\n── Karar Dağılımı (0.70/0.30 ağırlık, primary) ───────────")
    for karar_adi, cnt in merged["karar"].value_counts().items():
        pct = cnt / len(merged) * 100
        print(f"  {karar_adi:<18}: {cnt:>5} ders  ({pct:.1f}%)")

    print("\n── Duyarlılık Analizi: Ağırlık Şemalarına Göre Ortalama |Sapma%| ──")
    sensitivity_rows = []
    for w_rf, w_kural in WEIGHT_SCHEMES:
        col = f"adaptif_akts_{int(w_rf*100)}_{int(w_kural*100)}"
        sapma_pct = (merged[col] - merged["AKTSKredi"]) / merged["AKTSKredi"] * 100
        mean_abs_pct = sapma_pct.abs().mean()
        incelenmeli_pct = (sapma_pct.abs() >= 30).mean() * 100
        sensitivity_rows.append({
            "agirlik": f"{w_rf:.2f} RF / {w_kural:.2f} Kural",
            "ort_mutlak_sapma_yuzde": round(mean_abs_pct, 2),
            "incelenmeli_oran_yuzde": round(incelenmeli_pct, 2),
        })
        print(f"  {w_rf:.2f}/{w_kural:.2f}  -> ort |sapma%|={mean_abs_pct:.2f}  incelenmeli oranı={incelenmeli_pct:.2f}%")
    sensitivity_df = pd.DataFrame(sensitivity_rows)

    # ── Kaydet ────────────────────────────────────────────────────────────────
    out_cols = [
        "Katalogid", "DersAdi", "Fakulte", "alan_grubu", "AKTSKredi",
        "rf_tahmin_akts", "kural_akts",
    ] + [f"adaptif_akts_{int(w[0]*100)}_{int(w[1]*100)}" for w in WEIGHT_SCHEMES] + [
        "adaptif_akts", "sapma", "sapma_yuzde", "karar", "gerekce",
        "K_bilissel", "K_profil", "K_etkinlik",
    ]
    final_df = merged[out_cols].copy()
    final_df.to_excel(OUT_DIR / "master_akts_final.xlsx", index=False)
    final_df.to_csv(OUT_DIR / "master_akts_final.csv", index=False, encoding="utf-8-sig")
    importance_df.to_excel(BASE / "ip5-random-forest" / "feature_importance.xlsx", index=False)
    sensitivity_df.to_excel(BASE / "ip5-random-forest" / "duyarlilik_analizi.xlsx", index=False)

    print(f"\nKaydedildi: {OUT_DIR / 'master_akts_final.xlsx'}")
    print(f"Kaydedildi: {BASE / 'ip5-random-forest' / 'feature_importance.xlsx'}")
    print(f"Kaydedildi: {BASE / 'ip5-random-forest' / 'duyarlilik_analizi.xlsx'}")

    # ── Rapor dosyası ─────────────────────────────────────────────────────────
    write_report(
        final_df, importance_df, sensitivity_df,
        mae, rmse, r2, oof_mae, oof_rmse, oof_r2, feature_cols,
    )
    print(f"Kaydedildi: {REPORT_PATH}")

    return final_df


def write_report(final_df, importance_df, sensitivity_df, mae, rmse, r2, oof_mae, oof_rmse, oof_r2, feature_cols):
    karar_dist = final_df["karar"].value_counts()
    fakulte_sapma = (
        final_df.groupby("Fakulte")["sapma_yuzde"].mean().round(2).sort_values(ascending=False)
    )

    lines = []
    lines.append("# İP5 Sonuç Raporu — Random Forest + Adaptif AKTS")
    lines.append("")
    lines.append("**Görev (Bölüm 10, Görev 6):** Adaptif AKTS Hesaplayan Tahmin Modeli Oluşturma")
    lines.append("**Sorumlu:** Samet Koca | **Durum:** Tamamlandı")
    lines.append("")
    lines.append("## 1. Model Kurulumu")
    lines.append(f"- Algoritma: RandomForestRegressor(n_estimators={N_ESTIMATORS}, random_state={RANDOM_STATE})")
    lines.append(f"- Özellik sayısı: {len(feature_cols)} (K_bilissel, akts_mevcut hariç — hedef sızıntısı önlendi)")
    lines.append("- Train/test bölünmesi: Fakülte'ye göre stratified, %80/%20")
    lines.append(f"- rf_tahmin_akts: {N_FOLDS} katlı stratified (Fakülte) çapraz doğrulama, out-of-fold")
    lines.append("")
    lines.append("## 2. Model Kalitesi")
    lines.append("")
    lines.append("| Metrik | Ayrılmış Test Seti (%20) | Tüm Veri (Out-of-Fold) |")
    lines.append("|---|---|---|")
    lines.append(f"| MAE  | {mae:.4f} | {oof_mae:.4f} |")
    lines.append(f"| RMSE | {rmse:.4f} | {oof_rmse:.4f} |")
    lines.append(f"| R²   | {r2:.4f} | {oof_r2:.4f} |")
    lines.append("")
    lines.append(
        "Not: Out-of-fold R² değeri, tüm veriyle eğitilip aynı veriye tahmin yapan bir modelin "
        "R²'sinden düşük çıkar — bu beklenen ve istenen bir durumdur (\"iyi taklit paradoksu\"), "
        "çünkü amaç mevcut AKTS'yi ezberlemek değil, ondan anlamlı sapmaları yakalamaktır."
    )
    lines.append("")
    lines.append("## 3. Özellik Önem Dereceleri (XAI) — İlk 10")
    lines.append("")
    lines.append("| Özellik | Önem Derecesi |")
    lines.append("|---|---|")
    for _, row in importance_df.head(10).iterrows():
        lines.append(f"| {row['ozellik']} | {row['onem_derecesi']:.4f} |")
    lines.append("")
    lines.append("## 4. Karar Dağılımı (0.70 RF / 0.30 Kural, birincil ağırlık)")
    lines.append("")
    lines.append("| Karar | Ders Sayısı | Oran |")
    lines.append("|---|---|---|")
    for karar_adi, cnt in karar_dist.items():
        lines.append(f"| {karar_adi} | {cnt} | %{cnt/len(final_df)*100:.1f} |")
    lines.append("")
    lines.append("## 5. Duyarlılık Analizi — Ağırlık Şemaları (Karar 3)")
    lines.append("")
    lines.append("| Ağırlık (RF/Kural) | Ort. Mutlak Sapma % | İncelenmeli Oranı % |")
    lines.append("|---|---|---|")
    for _, row in sensitivity_df.iterrows():
        lines.append(f"| {row['agirlik']} | {row['ort_mutlak_sapma_yuzde']} | {row['incelenmeli_oran_yuzde']} |")
    lines.append("")
    lines.append("## 6. Fakülte Bazlı Ortalama Sapma % (H1 ön bulgusu)")
    lines.append("")
    lines.append("| Fakülte | Ort. Sapma % |")
    lines.append("|---|---|")
    for fak, val in fakulte_sapma.items():
        lines.append(f"| {fak} | {val:+.2f}% |")
    lines.append("")
    lines.append(
        "Yorum: Pozitif sapma, adaptif modelin mevcut AKTS'den daha YÜKSEK bir kredi önerdiği "
        "anlamına gelir (ör. lab/proje yoğun fakülteler). Bu, H1 hipotezinin ön testidir; "
        "istatistiksel anlamlılık testi İP6 raporunda (Görev 8) sunulmuştur."
    )
    lines.append("")
    lines.append("## 7. Çıktı Dosyaları")
    lines.append("- `data/processed/master_akts_final.xlsx` / `.csv` — her ders için rf_tahmin_akts, "
                  "kural_akts, adaptif_akts (4 ağırlık şeması), sapma, karar, gerekçe")
    lines.append("- `ip5-random-forest/feature_importance.xlsx`")
    lines.append("- `ip5-random-forest/duyarlilik_analizi.xlsx`")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
