import pandas as pd
import numpy as np
from pathlib import Path

# Yol tanımları
BASE = Path(__file__).resolve().parents[2]  # course-credits-system köküne çık
IN_PATH = BASE / "data" / "processed" / "master_bloom.xlsx"
OUT_PATH = BASE / "data" / "processed" / "master_bloom.xlsx"

print("master_bloom.xlsx yükleniyor...")
df = pd.read_excel(IN_PATH, dtype={"Katalogid": str})
print(f"  {len(df)} satır, {len(df.columns)} sütun")

# ─── K_profil ───────────────────────────────────
# Ders profilinin yapısal yoğunluğu
# Lab, proje ve uygulama varlığına göre ağırlıklandırma
# Proje en yüksek ağırlık (0.15) çünkü en fazla iş yükü
df["K_profil"] = (
    1
    + 0.10 * df["has_lab"]
    + 0.15 * df["has_proje"]
    + 0.05 * df["has_uygulama"]
).round(4)

# ─── K_etkinlik ─────────────────────────────────
# Etkinlik yoğunluğunun ortalamadan sapması
ort_etkinlik = df["n_etkinlik"].mean()
df["K_etkinlik"] = (
    1 + 0.03 * (df["n_etkinlik"] - ort_etkinlik)
).round(4)

print(f"\nOrtalama n_etkinlik: {ort_etkinlik:.2f}")

# ─── Kaydet ─────────────────────────────────────
df.to_excel(OUT_PATH, index=False)
df.to_csv(OUT_PATH.with_suffix(".csv"), index=False, encoding="utf-8-sig")
print(f"\nKaydedildi: {OUT_PATH}")
print(f"Toplam sütun: {len(df.columns)}")

# ─── Özet Rapor ─────────────────────────────────
print("\n=== K_profil İstatistikleri ===")
print(f"  Min : {df['K_profil'].min():.4f}")
print(f"  Max : {df['K_profil'].max():.4f}")
print(f"  Ort : {df['K_profil'].mean():.4f}")
print(f"  K_profil > 1.20 (yüksek yoğunluk): {(df['K_profil'] > 1.20).sum()} ders")

print("\n=== K_etkinlik İstatistikleri ===")
print(f"  Min : {df['K_etkinlik'].min():.4f}")
print(f"  Max : {df['K_etkinlik'].max():.4f}")
print(f"  Ort : {df['K_etkinlik'].mean():.4f}")

print("\n=== K_profil Dağılımı ===")
print(df["K_profil"].value_counts().sort_index().to_string())

print("\n=== Fakülte bazlı ortalama K_profil ===")
print(df.groupby("Fakulte")["K_profil"].mean().round(4).sort_values(ascending=False).to_string())
