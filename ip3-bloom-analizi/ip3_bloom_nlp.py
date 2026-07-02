"""
ip3_bloom_nlp.py
Bloom taksonomisi NLP analizi — master_clean.xlsx üzerinde her kazanımı sınıflandırır.
"""

import warnings
import pandas as pd
from pathlib import Path

warnings.filterwarnings("ignore")

# ── Yollar ──────────────────────────────────────────────────────────────────
IN_FILE  = Path("data/processed/master_clean.xlsx")
OUT_DIR  = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Bloom sözlüğü (L6→L1 sırasıyla) ────────────────────────────────────────
BLOOM = [
    (6, "Yaratma",        1.50, [
        "tasarlar", "geliştirir", "oluşturur", "üretir",
        "planlar", "inşa eder", "kurar", "formüle eder",
    ]),
    (5, "Değerlendirme",  1.40, [
        "değerlendirir", "yargılar", "savunur", "eleştirir",
        "karar verir", "doğrular", "önceliklendirir",
    ]),
    (4, "Analiz",         1.30, [
        "analiz eder", "inceler", "test eder", "sorgular",
        "kıyaslar", "ayırt eder", "karşılaştırır", "karmaşıklığını",
    ]),
    (3, "Uygulama",       1.20, [
        "uygular", "hesaplar", "çözer", "kullanır",
        "gerçekleştirir", "dener", "yapar", "işletir", "seçer",
    ]),
    (2, "Anlama",         1.10, [
        "açıklar", "özetler", "sınıflandırır", "yorumlar",
        "karşılaştırır", "örnekler", "betimler", "kavrar",
        "ilişkilendirir", "anlar",
    ]),
    (1, "Hatırlama",      1.00, [
        "tanımlar", "listeler", "adlandırır", "belirtir",
        "ifade eder", "öğrenir", "sıralar", "hatırlar", "tekrarlar",
    ]),
]

KAZ_COLS = [f"OgrenmeKazanim_{i}" for i in range(1, 26)]

# ── Tek bir kazanım metnini sınıflandır ─────────────────────────────────────
def classify_kazanim(text: str) -> int:
    """L6→L1 tarayarak ilk eşleşen düzeyi döndür; eşleşme yoksa 1."""
    if not text or str(text).strip().lower() in ("", "nan"):
        return 0  # boş
    t = str(text).lower()
    for level, _, _, keywords in BLOOM:
        for kw in keywords:
            if kw in t:
                return level
    return 1  # güvenli taban

# ── Bir satırı (ders) işle ───────────────────────────────────────────────────
def process_row(row) -> dict:
    levels = []
    for c in KAZ_COLS:
        val = row.get(c, None)
        if pd.notna(val) and str(val).strip().lower() not in ("", "nan"):
            lv = classify_kazanim(str(val))
            if lv > 0:
                levels.append(lv)

    if not levels:
        levels = [1]

    counts = {i: levels.count(i) for i in range(1, 7)}
    total  = len(levels)
    ratios = {i: counts[i] / total for i in range(1, 7)}

    avg_level  = sum(levels) / total
    max_level  = max(levels)
    dom_level  = max(counts, key=counts.get)

    K = 1 + ((avg_level - 1) / 5) * 0.50

    justification = (
        f"Dominant: L{dom_level} | "
        f"Ort: {avg_level:.2f} | "
        f"Maks: L{max_level} | "
        f"K={K:.4f}"
    )

    result = {}
    for i in range(1, 7):
        result[f"bloom_l{i}_count"] = counts[i]
        result[f"bloom_l{i}_ratio"] = round(ratios[i], 4)
    result["bloom_avg_level"]      = round(avg_level, 4)
    result["bloom_max_level"]      = max_level
    result["bloom_dominant_level"] = dom_level
    result["K_bilissel"]           = round(K, 4)
    result["bloom_justification"]  = justification
    return result

# ── Ana akış ────────────────────────────────────────────────────────────────
print(f"Girdi yükleniyor: {IN_FILE}")
df = pd.read_excel(IN_FILE)
print(f"  {len(df)} satır, {len(df.columns)} kolon yüklendi.")

print("Bloom analizi çalışıyor...")
bloom_rows = df.apply(process_row, axis=1, result_type="expand")
df = pd.concat([df, bloom_rows], axis=1)
print("  Tamamlandı.")

# ── Kaydet ──────────────────────────────────────────────────────────────────
df.to_excel(OUT_DIR / "master_bloom.xlsx", index=False)
df.to_csv(OUT_DIR / "master_bloom.csv",   index=False, encoding="utf-8-sig")

# ── Rapor ───────────────────────────────────────────────────────────────────
level_labels = {1:"L1 Hatırlama", 2:"L2 Anlama", 3:"L3 Uygulama",
                4:"L4 Analiz",    5:"L5 Değerlendirme", 6:"L6 Yaratma"}

print("\n" + "=" * 50)
print("         BLOOM ANALİZİ RAPORU")
print("=" * 50)

print("\n── Dominant Düzey Dağılımı ───────────────────────")
dom_dist = df["bloom_dominant_level"].value_counts().sort_index()
for lv, cnt in dom_dist.items():
    pct = cnt / len(df) * 100
    label = level_labels.get(lv, f"L{lv}")
    print(f"  {label:<22}: {cnt:>5}  ({pct:.1f}%)")

print("\n── Fakülte Bazlı Ort. Bloom Düzeyi ──────────────")
if "Fakulte" in df.columns:
    fak_avg = df.groupby("Fakulte")["bloom_avg_level"].mean().sort_values(ascending=False)
    for fak, avg in fak_avg.items():
        print(f"  {fak:<22}: {avg:.3f}")

print("\n── K_bilissel İstatistikleri ─────────────────────")
k = df["K_bilissel"]
print(f"  Min      : {k.min():.4f}")
print(f"  Max      : {k.max():.4f}")
print(f"  Ortalama : {k.mean():.4f}")
print(f"  Std      : {k.std():.4f}")

print("\nDosyalar kaydedildi:")
print(f"  {OUT_DIR / 'master_bloom.xlsx'}")
print(f"  {OUT_DIR / 'master_bloom.csv'}")
