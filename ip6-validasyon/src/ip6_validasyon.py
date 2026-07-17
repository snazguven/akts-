"""
ip6_validasyon.py
Görev 8 (Bölüm 10) — Tutarsızlık Analizi ve Karşılaştırmalı Validasyon.

Metodoloji (README.md Bölüm 6) karşılığı:
  Aşama 2 (Tutarsızlık Analizi):
    (a) Kurum-içi sapma        -> aynı isimli derslerin farklı bölümlerdeki AKTS varyansı
                                   (H2'nin gerçek kurumlar-arası testi için Kanal B verisi
                                   toplanmadığından, bu kurum-İÇİ bir proxy analizdir — bkz. Sınırlılıklar)
    (b) Etkinlik bazlı etki    -> hangi etkinlik bayrakları en büyük sapmaya yol açıyor
    (c) Gerçek vs. Tahmin      -> öğrenci anketi (Kanal C) toplanmadığı için TEST EDİLEMEZ
                                   (bkz. Sınırlılıklar)
  Aşama 4 (Karşılaştırma ve Validasyon):
    - Mevcut motor AKTS vs. AI-önerilen (adaptif_akts) karşılaştırması
    - Üçüncü bacak (öğrenci gerçek iş yükü) veri eksikliği nedeniyle iki-yönlü karşılaştırma
    - Uzman görüşü validasyonu yerine somut bir "inceleme kuyruğu" (review queue) üretilir —
      bu, projenin pratik katkı hedefiyle (Bölüm 12.2) doğrudan örtüşür.

  Hipotez Testleri (Bölüm 3.2):
    H1: Lab/proje yoğun dersler sistematik olarak düşük kredi mi alıyor?
        -> Mann-Whitney U: has_lab/has_proje=1 grubunun sapma_yuzde'si 0 grubundan anlamlı yüksek mi?
    H2: Aynı isimli derslerde AKTS sapması ±2 kredi aralığını aşıyor mu?
        -> Kurum-içi proxy: aynı DersAdi, farklı BolumAd kombinasyonlarında AKTS aralığı.
    H3: Adaptif model gerçek iş yüküne >=%20 daha yakın mı?
        -> TEST EDİLEMEZ (ground truth/öğrenci anketi verisi yok, Kanal C toplanmadı).
    H4: Üst düzey Bloom (L4-L6) derslerin sapması anlamlı ölçüde yüksek mi?
        -> Kruskal-Wallis (bloom_dominant_level grupları) + Spearman korelasyonu (bloom_avg_level, sapma_yuzde).
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

BASE = Path(__file__).resolve().parents[2]
FINAL_PATH = BASE / "data" / "processed" / "master_akts_final.xlsx"
BLOOM_PATH = BASE / "data" / "processed" / "master_bloom.xlsx"
OUT_DIR = BASE / "ip6-validasyon"
REPORT_PATH = OUT_DIR / "IP6_SONUC_RAPORU.md"

ALPHA = 0.05


def main():
    print("=" * 60)
    print("İP6 — TUTARSIZLIK ANALİZİ VE KARŞILAŞTIRMALI VALİDASYON")
    print("=" * 60)

    final_df = pd.read_excel(FINAL_PATH, dtype={"Katalogid": str})
    bloom_df = pd.read_excel(BLOOM_PATH, dtype={"Katalogid": str})
    df = final_df.merge(
        bloom_df[["Katalogid", "BolumAd", "has_lab", "has_proje", "has_uygulama", "has_atolye",
                  "has_odev", "has_sinav", "has_sunum", "bloom_avg_level", "bloom_dominant_level"]],
        on="Katalogid", how="left",
    )
    print(f"\nYüklendi: {len(df)} ders (master_akts_final.xlsx + master_bloom.xlsx birleşimi)")

    # ── AŞAMA 2(a) / H2 — Kurum-içi tutarsızlık (aynı isimli ders, farklı bölüm) ──
    print("\n" + "-" * 60)
    print("AŞAMA 2(a) / H2 — Kurum-İçi Tutarsızlık (aynı isimli ders, farklı bölüm)")
    print("-" * 60)

    name_groups = (
        df.groupby("DersAdi")
        .agg(n_bolum=("BolumAd", "nunique"), n_kayit=("DersAdi", "size"),
             akts_min=("AKTSKredi", "min"), akts_max=("AKTSKredi", "max"),
             akts_std=("AKTSKredi", "std"))
        .reset_index()
    )
    name_groups["akts_araligi"] = name_groups["akts_max"] - name_groups["akts_min"]
    multi_dept = name_groups[(name_groups["n_bolum"] >= 2) & (name_groups["n_kayit"] >= 2)].copy()
    multi_dept = multi_dept.sort_values("akts_araligi", ascending=False)

    h2_asan = (multi_dept["akts_araligi"] > 2).sum()
    h2_oran = h2_asan / len(multi_dept) * 100 if len(multi_dept) else 0.0
    print(f"  Aynı isimle birden fazla bölümde geçen ders sayısı: {len(multi_dept)}")
    print(f"  Bunlardan ±2 AKTS aralığını AŞANLAR: {h2_asan} ({h2_oran:.1f}%)")
    print(f"  Ortalama AKTS aralığı (bu gruplarda): {multi_dept['akts_araligi'].mean():.2f}")

    multi_dept.to_excel(OUT_DIR / "ayni_isimli_ders_tutarsizligi.xlsx", index=False)

    # ── AŞAMA 2(b) — Etkinlik bazlı etki (hangi etkinlikler en çok sapma yaratıyor) ──
    print("\n" + "-" * 60)
    print("AŞAMA 2(b) — Etkinlik Bazlı Etki")
    print("-" * 60)

    flags = ["has_lab", "has_proje", "has_uygulama", "has_atolye", "has_odev", "has_sinav", "has_sunum"]
    etkinlik_rows = []
    for flag in flags:
        grp1 = df.loc[df[flag] == 1, "sapma_yuzde"].dropna()
        grp0 = df.loc[df[flag] == 0, "sapma_yuzde"].dropna()
        if len(grp1) < 5 or len(grp0) < 5:
            continue
        u_stat, p_val = stats.mannwhitneyu(grp1, grp0, alternative="two-sided")
        etkinlik_rows.append({
            "etkinlik": flag,
            "n_var": len(grp1),
            "ort_sapma_pct_var": round(grp1.mean(), 2),
            "n_yok": len(grp0),
            "ort_sapma_pct_yok": round(grp0.mean(), 2),
            "fark": round(grp1.mean() - grp0.mean(), 2),
            "mannwhitney_p": round(p_val, 6),
            "anlamli_mi(p<0.05)": p_val < ALPHA,
        })
        print(f"  {flag:<14} var={grp1.mean():+.2f}%  yok={grp0.mean():+.2f}%  "
              f"fark={grp1.mean()-grp0.mean():+.2f}%  p={p_val:.4f}")

    etkinlik_df = pd.DataFrame(etkinlik_rows).sort_values("fark", ascending=False)
    etkinlik_df.to_excel(OUT_DIR / "etkinlik_bazli_etki.xlsx", index=False)

    # ── H1 — Lab/proje yoğun dersler sistematik düşük kredi mi alıyor? ──────────
    print("\n" + "-" * 60)
    print("H1 — Lab/Proje Yoğun Dersler Sistematik Düşük Kredi Alıyor mu?")
    print("-" * 60)

    yogun_mask = (df["has_lab"] == 1) | (df["has_proje"] == 1)
    grp_yogun = df.loc[yogun_mask, "sapma_yuzde"].dropna()
    grp_diger = df.loc[~yogun_mask, "sapma_yuzde"].dropna()
    u_stat_h1, p_h1 = stats.mannwhitneyu(grp_yogun, grp_diger, alternative="greater")
    h1_destekleniyor = (p_h1 < ALPHA) and (grp_yogun.mean() > grp_diger.mean())

    print(f"  Lab/Proje dersleri (n={len(grp_yogun)}): ort. sapma = {grp_yogun.mean():+.2f}%")
    print(f"  Diğer dersler      (n={len(grp_diger)}): ort. sapma = {grp_diger.mean():+.2f}%")
    print(f"  Mann-Whitney U (one-sided, 'greater') p-değeri: {p_h1:.6f}")
    print(f"  H1 destekleniyor mu? {'EVET' if h1_destekleniyor else 'HAYIR'}")

    # ── H4 — Üst düzey Bloom dersler anlamlı ölçüde yüksek yük mü? ──────────────
    print("\n" + "-" * 60)
    print("H4 — Üst Düzey Bloom (L4-L6) Derslerin Sapması Anlamlı mı?")
    print("-" * 60)

    bloom_groups = [g["sapma_yuzde"].dropna().values for _, g in df.groupby("bloom_dominant_level")
                    if g["sapma_yuzde"].notna().sum() >= 5]
    kw_stat, p_kw = stats.kruskal(*bloom_groups) if len(bloom_groups) >= 2 else (np.nan, np.nan)
    rho, p_rho = stats.spearmanr(df["bloom_avg_level"], df["sapma_yuzde"], nan_policy="omit")

    print(f"  Kruskal-Wallis (bloom_dominant_level grupları): H={kw_stat:.4f}, p={p_kw:.6f}")
    print(f"  Spearman korelasyonu (bloom_avg_level vs sapma_yuzde): rho={rho:.4f}, p={p_rho:.6f}")
    h4_destekleniyor = (p_rho < ALPHA) and (rho > 0)
    print(f"  H4 destekleniyor mu? {'EVET' if h4_destekleniyor else 'HAYIR'}")

    bloom_ozet = df.groupby("bloom_dominant_level")["sapma_yuzde"].agg(["count", "mean", "std"]).round(2)
    bloom_ozet.to_excel(OUT_DIR / "bloom_duzeyi_sapma_ozet.xlsx")

    # ── AŞAMA 4 — Üçlü (burada iki-yönlü) karşılaştırma ─────────────────────────
    print("\n" + "-" * 60)
    print("AŞAMA 4 — Karşılaştırma: Mevcut Motor AKTS vs. AI-Önerilen (adaptif_akts)")
    print("-" * 60)

    fark = df["adaptif_akts"] - df["AKTSKredi"]
    korelasyon, p_korr = stats.pearsonr(df["AKTSKredi"], df["adaptif_akts"])
    print(f"  Pearson korelasyonu (mevcut vs adaptif): r={korelasyon:.4f} (p={p_korr:.2e})")
    print(f"  Ortalama fark (adaptif - mevcut): {fark.mean():+.4f} AKTS")
    print(f"  Fark std sapması: {fark.std():.4f} AKTS")
    print(f"  Uyum sınırları (mean ± 1.96·std): [{fark.mean()-1.96*fark.std():.2f}, {fark.mean()+1.96*fark.std():.2f}]")
    print("  NOT: Üçüncü bacak (öğrenci gerçek iş yükü / Kanal C anketi) toplanmadığından,")
    print("       H3 test edilememektedir. Bkz. rapor 'Sınırlılıklar' bölümü.")

    # ── İnceleme kuyruğu (Uzman görüşü validasyonu yerine somut çıktı) ──────────
    print("\n" + "-" * 60)
    print("Kalite Güvence İnceleme Kuyruğu (Pratik Katkı — Bölüm 12.2)")
    print("-" * 60)

    inceleme = df[df["karar"] == "İncelenmeli"].copy()
    inceleme["abs_sapma_yuzde"] = inceleme["sapma_yuzde"].abs()
    inceleme = inceleme.sort_values("abs_sapma_yuzde", ascending=False)
    top_queue = inceleme[[
        "Katalogid", "DersAdi", "Fakulte", "AKTSKredi", "adaptif_akts", "sapma_yuzde", "gerekce"
    ]].head(50)
    top_queue.to_excel(OUT_DIR / "inceleme_kuyrugu_ilk50.xlsx", index=False)
    print(f"  Toplam 'İncelenmeli' işaretli ders: {len(inceleme)}")
    print(f"  En yüksek sapmalı ilk 50 ders 'inceleme_kuyrugu_ilk50.xlsx' dosyasına kaydedildi.")

    write_report(
        multi_dept, h2_asan, h2_oran, etkinlik_df,
        grp_yogun, grp_diger, p_h1, h1_destekleniyor,
        kw_stat, p_kw, rho, p_rho, h4_destekleniyor, bloom_ozet,
        korelasyon, p_korr, fark, len(inceleme), len(df),
    )
    print(f"\nKaydedildi: {REPORT_PATH}")


def write_report(multi_dept, h2_asan, h2_oran, etkinlik_df,
                  grp_yogun, grp_diger, p_h1, h1_destekleniyor,
                  kw_stat, p_kw, rho, p_rho, h4_destekleniyor, bloom_ozet,
                  korelasyon, p_korr, fark, n_incelenmeli, n_toplam):
    lines = []
    lines.append("# İP6 Sonuç Raporu — Tutarsızlık Analizi ve Karşılaştırmalı Validasyon")
    lines.append("")
    lines.append("**Görev (Bölüm 10, Görev 8):** Tutarsızlık Analizi ve Karşılaştırmalı Validasyon")
    lines.append("**Sorumlu:** Samet Koca | **Durum:** Tamamlandı")
    lines.append("")
    lines.append("## 1. Kurum-İçi Tutarsızlık (Aşama 2a / H2 Proxy)")
    lines.append("")
    lines.append(
        f"Aynı isimle birden fazla bölümde okutulan **{len(multi_dept)}** ders grubu tespit edildi. "
        f"Bunlardan **{h2_asan} tanesi ({h2_oran:.1f}%)**, aynı ders için bölümler arası AKTS "
        f"aralığının ±2 kredi sınırını aştığını gösteriyor."
    )
    lines.append("")
    lines.append("En yüksek AKTS aralığına sahip ilk 10 ders:")
    lines.append("")
    lines.append("| Ders Adı | Bölüm Sayısı | Min AKTS | Maks AKTS | Aralık |")
    lines.append("|---|---|---|---|---|")
    for _, row in multi_dept.head(10).iterrows():
        lines.append(f"| {row['DersAdi']} | {row['n_bolum']} | {row['akts_min']} | {row['akts_max']} | {row['akts_araligi']} |")
    lines.append("")
    lines.append(
        "**H2 değerlendirmesi:** Bu analiz, hipotezde tanımlanan *kurumlar arası* (farklı üniversiteler) "
        "sapmanın değil, **kurum-içi** (Kocaeli Üniversitesi bünyesinde farklı bölümler arası) sapmanın "
        "bir proxy'sidir — çünkü Kanal B (5+ farklı üniversiteden çapraz doğrulama verisi, Bölüm 6.1) "
        "henüz toplanmamıştır. Kurum-içi veride dahi anlamlı bir tutarsızlık gözlenmesi, H2'nin "
        "kurumlar arası halinde de muhtemelen doğrulanacağına dair dolaylı bir işarettir, ancak "
        "kesin sonuç için Kanal B verisi gereklidir."
    )
    lines.append("")
    lines.append("## 2. Etkinlik Bazlı Etki (Aşama 2b)")
    lines.append("")
    lines.append("| Etkinlik | Ort. Sapma% (var) | Ort. Sapma% (yok) | Fark | Mann-Whitney p | Anlamlı mı |")
    lines.append("|---|---|---|---|---|---|")
    for _, row in etkinlik_df.iterrows():
        anlamli = "Evet" if row["anlamli_mi(p<0.05)"] else "Hayır"
        lines.append(
            f"| {row['etkinlik']} | {row['ort_sapma_pct_var']:+.2f}% | {row['ort_sapma_pct_yok']:+.2f}% | "
            f"{row['fark']:+.2f}% | {row['mannwhitney_p']:.4f} | {anlamli} |"
        )
    lines.append("")
    lines.append("## 3. H1 — Lab/Proje Yoğun Dersler Sistematik Düşük Kredi Alıyor mu?")
    lines.append("")
    lines.append(f"- Lab veya proje içeren dersler (n={len(grp_yogun)}): ortalama sapma = **{grp_yogun.mean():+.2f}%**")
    lines.append(f"- Diğer dersler (n={len(grp_diger)}): ortalama sapma = **{grp_diger.mean():+.2f}%**")
    lines.append(f"- Mann-Whitney U testi (one-sided, 'greater'): p = {p_h1:.6f}")
    lines.append(f"- **Sonuç: H1 {'DESTEKLENİYOR' if h1_destekleniyor else 'DESTEKLENMİYOR'}** "
                 f"({'p<0.05 ve yön beklenen gibi' if h1_destekleniyor else 'istatistiksel olarak anlamlı fark bulunamadı veya yön ters'}).")
    lines.append("")
    lines.append("## 4. H4 — Üst Düzey Bloom (L4-L6) Derslerin Sapması Anlamlı mı?")
    lines.append("")
    lines.append("Bloom baskın düzeyine göre ortalama sapma%:")
    lines.append("")
    lines.append("| Bloom Düzeyi | n | Ort. Sapma% | Std |")
    lines.append("|---|---|---|---|")
    for lvl, row in bloom_ozet.iterrows():
        lines.append(f"| L{int(lvl)} | {int(row['count'])} | {row['mean']:+.2f}% | {row['std']:.2f} |")
    lines.append("")
    lines.append(f"- Kruskal-Wallis testi (bloom_dominant_level grupları arası): H = {kw_stat:.4f}, p = {p_kw:.6f}")
    lines.append(f"- Spearman korelasyonu (bloom_avg_level vs sapma_yuzde): rho = {rho:.4f}, p = {p_rho:.6f}")
    lines.append(f"- **Sonuç: H4 {'DESTEKLENİYOR' if h4_destekleniyor else 'DESTEKLENMİYOR'}**")
    lines.append("")
    lines.append("## 5. Aşama 4 — Mevcut Motor AKTS vs. AI-Önerilen (adaptif_akts) Karşılaştırması")
    lines.append("")
    lines.append(f"- Pearson korelasyonu: r = {korelasyon:.4f} (p = {p_korr:.2e})")
    lines.append(f"- Ortalama fark (adaptif − mevcut): {fark.mean():+.4f} AKTS")
    lines.append(f"- Fark standart sapması: {fark.std():.4f} AKTS")
    lines.append(f"- %95 uyum sınırları (Bland-Altman tarzı): [{fark.mean()-1.96*fark.std():.2f}, {fark.mean()+1.96*fark.std():.2f}] AKTS")
    lines.append("")
    lines.append(
        f"Kalite güvence inceleme kuyruğu: **{n_incelenmeli}/{n_toplam} ders "
        f"(%{n_incelenmeli/n_toplam*100:.1f})** 'İncelenmeli' olarak işaretlendi. En yüksek sapmalı "
        "50 ders `inceleme_kuyrugu_ilk50.xlsx` dosyasında koordinatör incelemesi için hazırlandı — "
        "bu, projenin pratik katkı hedefinin (Bölüm 12.2) somut bir uygulamasıdır."
    )
    lines.append("")
    lines.append("## 6. Sınırlılıklar (Aşama 2c / H3 — Test Edilemeyen Kısımlar)")
    lines.append("")
    lines.append(
        "- **Gerçek öğrenci iş yükü (Kanal C anketi)** bu iş paketi kapsamında toplanmadı. Bu yüzden "
        "'gerçek vs. tahmin' karşılaştırması (Aşama 2c) ve **H3** ('adaptif model gerçek iş yüküne "
        "≥%20 daha yakın') test EDİLEMEMİŞTİR. Bu, İP1-4 raporunda (Bölüm 4.1) baştan beri bilinen "
        "ve kabul edilen bir kısıttır; Risk R1/R4'te (Bölüm 9) planlanan yedek plan uyarınca makale, "
        "anketi ayrı bir gelecek çalışma olarak raporlamalı ya da anket toplanana kadar bu bölüm "
        "kısmi kanıtla (Kanal A + kurum-içi tutarsızlık) ilerlemelidir."
    )
    lines.append(
        "- **Kurumlar arası çapraz doğrulama (Kanal B, 5+ üniversite)** toplanmadığından, H2 gerçek "
        "biçimiyle değil, kurum-içi bir proxy ile test edilmiştir (bkz. Bölüm 1)."
    )
    lines.append(
        "- **Uzman görüşü validasyonu** (Aşama 4) gerçek koordinatör/öğretim üyesi görüşmesi yerine, "
        "somut bir inceleme kuyruğu (review queue) çıktısıyla operasyonel hale getirilmiştir; "
        "gerçek uzman değerlendirmesi hâlâ ayrı bir adım olarak yapılmalıdır."
    )
    lines.append("")
    lines.append("## 7. Çıktı Dosyaları")
    lines.append("- `ip6-validasyon/ayni_isimli_ders_tutarsizligi.xlsx`")
    lines.append("- `ip6-validasyon/etkinlik_bazli_etki.xlsx`")
    lines.append("- `ip6-validasyon/bloom_duzeyi_sapma_ozet.xlsx`")
    lines.append("- `ip6-validasyon/inceleme_kuyrugu_ilk50.xlsx`")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
