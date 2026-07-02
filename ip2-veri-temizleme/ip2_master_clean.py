"""
ip2_master_clean.py
Master temizleme scripti — 7 fakülte Excel'ini birleştirir, temizler, zenginleştirir.
"""

import subprocess, sys

# Gerekli kütüphane kontrolü
for pkg in ["pandas", "openpyxl"]:
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

import warnings
import pandas as pd
from pathlib import Path

warnings.filterwarnings("ignore")

# ── Yollar ──────────────────────────────────────────────────────────────────
RAW = Path("data/raw")
OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

# ── 1. Dosyaları yükle ──────────────────────────────────────────────────────
files = {
    "Mühendislik":      "Mu_hendislik.xlsx",
    "Güzel Sanatlar":   "Gu_zel_Sanatlar.xlsx",
    "Fen-Edebiyat":     "FenEdebiyat.xlsx",
    "Eğitim":           "Eg_itim.xlsx",
    "Siyasal Bilgiler": "Siyasal_Bilgiler.xlsx",
    "Spor Bilimleri":   "Spor_Bilimleri.xlsx",
    "Teknoloji":        "Teknoloji.xlsx",
}

alan_grubu_map = {
    "Mühendislik":      "STEM",
    "Teknoloji":        "STEM",
    "Fen-Edebiyat":     "Fen-Sosyal",
    "Eğitim":           "Sosyal",
    "Siyasal Bilgiler": "Sosyal",
    "Güzel Sanatlar":   "Sanat",
    "Spor Bilimleri":   "Spor",
}

dfs = []
for fakulte, fname in files.items():
    path = RAW / fname
    df_tmp = pd.read_excel(path)
    df_tmp["Fakulte"] = fakulte
    dfs.append(df_tmp)
    print(f"  Yüklendi: {fname:<30} ({len(df_tmp):>5} satır)")

df = pd.concat(dfs, ignore_index=True)
raw_count = len(df)
print(f"\nHam birleşik satır: {raw_count}")

# ── 3. Temizlik ─────────────────────────────────────────────────────────────
# AKTSKredi == 0
df = df[df["AKTSKredi"] != 0]
drop_akts = raw_count - len(df)

# OgrenmeKazanim_1 boş
df = df[df["OgrenmeKazanim_1"].notna()]
df = df[df["OgrenmeKazanim_1"].astype(str).str.strip().str.lower() != "nan"]
drop_kaz = raw_count - drop_akts - len(df)

# EtkinlikAd sütunlarında strip
etkinlik_cols = [f"EtkinlikAd_{i}" for i in range(1, 22)]
for c in etkinlik_cols:
    if c in df.columns:
        df[c] = df[c].astype(str).str.strip().replace("nan", pd.NA)

# ── 4. İÖ tekilleştirme ─────────────────────────────────────────────────────
df["is_io"] = df["BolumAd"].astype(str).str.contains(r"\(İÖ\)|\(IO\)", regex=True, na=False)
before_dedup = len(df)
# Sırala: is_io=False önce gelsin → keep='first' ile İÖ olanı atar (aynı id varsa)
df = df.sort_values("is_io").drop_duplicates(subset="Katalogid", keep="first")
drop_io = before_dedup - len(df)

# ── 5. Yeni sütunlar ────────────────────────────────────────────────────────
df["alan_grubu"] = df["Fakulte"].map(alan_grubu_map)

# Öğrenme kazanımları
kaz_cols = [f"OgrenmeKazanim_{i}" for i in range(1, 26)]

def count_kaz(row):
    return sum(
        1 for c in kaz_cols
        if c in row and pd.notna(row[c]) and str(row[c]).strip().lower() not in ("", "nan")
    )

def concat_kaz(row):
    vals = [
        str(row[c]).strip()
        for c in kaz_cols
        if c in row and pd.notna(row[c]) and str(row[c]).strip().lower() not in ("", "nan")
    ]
    return " | ".join(vals)

df["n_ogrenme_kazanim"] = df.apply(count_kaz, axis=1)
df["kazanim_concat"]    = df.apply(concat_kaz, axis=1)

# Etkinlik özellikleri — büyük/küçük harf duyarsız eşleştirme
def etkinlik_features(row):
    vals = " | ".join([
        str(row[c]).strip().lower()
        for c in etkinlik_cols
        if c in row and pd.notna(row[c]) and str(row[c]).strip().lower() not in ("", "nan")
    ])
    n = vals.count("|") + 1 if vals.strip() else 0
    return pd.Series({
        "n_etkinlik":    n,
        "has_lab":       int("laboratuvar" in vals),
        "has_proje":     int("proje" in vals),
        "has_uygulama":  int("uygulama" in vals),
        "has_atolye":    int("atölye" in vals or "atolye" in vals),
        "has_odev":      int("ödev" in vals or "odev" in vals),
        "has_sinav":     int("sınav" in vals or "sinav" in vals or "quiz" in vals),
        "has_sunum":     int("sunum" in vals or "seminer" in vals),
    })

ef = df.apply(etkinlik_features, axis=1)
df = pd.concat([df, ef], axis=1)

# ── 6. Kaydet ───────────────────────────────────────────────────────────────
df.reset_index(drop=True, inplace=True)
df.to_excel(OUT / "master_clean.xlsx", index=False)
df.to_csv(OUT / "master_clean.csv", index=False, encoding="utf-8-sig")

# ── 7. Rapor ────────────────────────────────────────────────────────────────
n_rows = len(df)
n_cols = len(df.columns)

print("\n" + "=" * 45)
print("         TEMİZLİK RAPORU")
print("=" * 45)
print(f"Ham satır              : {raw_count}")
print(f"AKTSKredi=0 düşülen   : {drop_akts}")
print(f"Kazanım boş düşülen   : {drop_kaz}")
print(f"İÖ tekrar düşülen     : {drop_io}")
print(f"MASTER SATIR           : {n_rows}")
print(f"MASTER KOLON           : {n_cols}")

print("\n── Fakülte Dağılımı ──────────────────────")
for fak, cnt in df["Fakulte"].value_counts().items():
    pct = cnt / n_rows * 100
    print(f"  {fak:<22}: {cnt:>5}  ({pct:.1f}%)")

print("\n── Etkinlik Oranları ─────────────────────")
for col in ["has_lab", "has_proje", "has_uygulama", "has_atolye", "has_odev", "has_sinav", "has_sunum"]:
    if col in df.columns:
        s = df[col].sum()
        r = s / n_rows * 100
        print(f"  {col:<18}: {s:>5}  ({r:.1f}%)")

print("\n── Diğer ─────────────────────────────────")
print(f"  Ort. n_etkinlik      : {df['n_etkinlik'].mean():.2f}")
print(f"  Ort. n_kazanim       : {df['n_ogrenme_kazanim'].mean():.2f}")
print(f"  Ort. AKTSKredi       : {df['AKTSKredi'].mean():.2f}")

print("\nDosyalar kaydedildi:")
print(f"  {OUT / 'master_clean.xlsx'}")
print(f"  {OUT / 'master_clean.csv'}")
