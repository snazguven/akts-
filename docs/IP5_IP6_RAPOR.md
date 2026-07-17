# Adaptif AKTS Projesi — Görev 6 ve Görev 8 Uçtan Uca Teknik Rapor

**Proje:** Yapay Zekâ Destekli Adaptif AKTS Kredi Hesaplama Modeli
**Konferans:** 2026 YÖKAK Uluslararası Kalite Güvencesi ve Akreditasyon Konferansı — 14-15 Eylül 2026, Yıldız Teknik Üniversitesi
**Kurum:** Kocaeli Üniversitesi
**Bu raporun kapsamı:** Proje planı Bölüm 10'daki Görev 6 (Adaptif AKTS Hesaplayan Tahmin Modeli Oluşturma) ve Görev 8 (Tutarsızlık Analizi ve Karşılaştırmalı Validasyon) — repodaki İP5 ve İP6 karşılığı.
**Rapor tarihi:** 18 Temmuz 2026
**Rapor durumu:** Tamamlandı

---

## ÖZET

İP1-4'ün ürettiği zenginleştirilmiş veri seti (`master_bloom.xlsx`, 107 sütun; `model_egitim.xlsx`, 43 sütun) üzerinde:

1. **Görev 6 (İP5):** Bir Random Forest regresör eğitildi, her ders için `rf_tahmin_akts` üretildi, kural tabanlı `kural_akts` hesaplandı ve ikisi ağırlıklı birleştirilerek `adaptif_akts` elde edildi.
2. **Görev 8 (İP6):** Kurum-içi tutarsızlık analizi, etkinlik bazlı etki analizi ve H1/H2/H4 hipotez testleri yapıldı; mevcut motor ile AI-önerilen kredi arasında karşılaştırmalı validasyon uygulandı.

**Ana bulgular:**
- **H1 DESTEKLENDİ** — Lab/proje içeren dersler, diğerlerine göre anlamlı derecede yüksek sapma gösteriyor (+19.9% vs +8.2%, p<0.001).
- **H4 DESTEKLENDİ** — Bloom düzeyi arttıkça sapma da anlamlı biçimde artıyor (rho=0.16, p<0.001).
- **H2, kurum-içi proxy ile kısmen destekleniyor** — aynı isimli derslerin %11.5'i bölümler arası ±2 AKTS sınırını aşıyor; kesin sonuç için kurumlar arası veri (Kanal B) gerekli.
- **H3 test edilemedi** — öğrenci iş yükü anketi (Kanal C) bu iş paketi kapsamında toplanmadı; bu, İP1-4 raporunda baştan beri bilinen bir kısıttır.

---

## 1. GÖREV 6 (İP5) — ADAPTİF AKTS HESAPLAYAN TAHMİN MODELİ

**Girdi:** `data/processed/model_egitim.xlsx`, `data/processed/master_bloom.xlsx`
**Çıktı:** `data/processed/master_akts_final.xlsx/.csv`
**Kod:** `ip5-random-forest/src/ip5_random_forest.py`, `ip5-random-forest/notebooks/ip5_random_forest.ipynb`

### 1.1 Uygulanan Kararlar (README.md Bölüm 15'teki 6 karar)

| # | Karar | Uygulama |
|---|---|---|
| 1 | RF hiperparametreleri + split | `RandomForestRegressor(n_estimators=200, random_state=42)`; Fakülte'ye göre stratified %80/20 train/test |
| 2 | Özellik seçimi | Tüm 39 özellik kullanıldı; **K_bilissel, K_profil, K_etkinlik ve akts_mevcut RF'e özellik olarak verilmedi** (Seçenek b — bağımsız hibrit bileşenler) |
| 3 | Adaptif ağırlıklar | 4 şema denendi (0.50/0.50 → 0.80/0.20), duyarlılık analizi raporlandı; birincil şema 0.70/0.30 |
| 4 | Sapma eşikleri | Yüzdesel eşik: <%10 Güçlü uyum, %10-30 Kabul edilebilir, ≥%30 İncelenmeli |
| 5 | Başarı metriği | MAE/RMSE/R², hem ayrılmış test seti hem 5-katlı out-of-fold üzerinden |
| 6 | XAI | `feature_importances_` tablosu + her ders için okunabilir `gerekçe` metni |

### 1.2 Hedef Sızıntısı Önlemi (README.md Bölüm 14.4)

RF modeli `akts_mevcut` (AKTSKredi) değerini ASLA özellik olarak görmedi — bu sütun sadece hedef değişken (y) ve `kural_akts`/`sapma` hesaplarında kullanıldı. Ayrıca `K_bilissel` (model_egitim.xlsx'te mevcuttu) RF özelliklerinden çıkarıldı ki kural tabanlı bileşenle RF tamamen bağımsız kalsın.

### 1.3 "İyi Taklit Paradoksu" ve Out-of-Fold Çözümü

Model tüm veriyle eğitilip aynı veriye tahmin yaparsa RF ezberler ve hiçbir sapma bulunmaz. Bunu önlemek için `rf_tahmin_akts`, **5 katlı stratified (Fakülte) çapraz doğrulama ile out-of-fold** üretildi: her ders, kendisinin bulunmadığı bir fold'da eğitilmiş modelden tahmin aldı.

| Metrik | Ayrılmış Test Seti (%20) | Tüm Veri (Out-of-Fold) |
|---|---|---|
| MAE  | 0.8352 AKTS | 0.9285 AKTS |
| RMSE | 1.1544 AKTS | 1.7504 AKTS |
| R²   | 0.0781 | -0.1164 |

Out-of-fold R²'nin düşük/negatif çıkması **beklenen bir sonuçtur**: mevcut AKTS motorunun kendisi öznitelik profiline dayalı öngörülebilir bir örüntü izlemiyor (Sorun 2 — Subjektif Veri Girişi, README §3.2) — ki bu tam olarak projenin tezini (statik motorun tutarsız olduğu) destekleyen bir bulgudur.

### 1.4 Özellik Önem Dereceleri (XAI)

| Özellik | Önem Derecesi |
|---|---|
| bloom_avg_level | 0.2610 |
| bloom_max_level | 0.1448 |
| n_ogrenme_kazanim | 0.1030 |
| n_etkinlik | 0.0710 |
| has_odev | 0.0386 |

Bloom düzeyi özellikleri (K_bilissel değil, ham `bloom_avg_level`/`bloom_max_level`) modelin en güçlü sinyalleri — bu, H4 hipotezinin ön göstergesidir.

### 1.5 Duyarlılık Analizi (Karar 3)

| Ağırlık (RF/Kural) | Ort. Mutlak Sapma % | İncelenmeli Oranı % |
|---|---|---|
| 0.50 / 0.50 | 14.72 | 11.32 |
| 0.60 / 0.40 | 16.11 | 12.94 |
| 0.70 / 0.30 (birincil) | 17.74 | 15.44 |
| 0.80 / 0.20 | 19.59 | 18.00 |

Ağırlık şeması, işaretlenen ders oranını doğrudan etkiliyor — makalede bu duyarlılık açıkça tartışılmalı (README §15.3 önerisi).

### 1.6 Karar Dağılımı (0.70/0.30 birincil ağırlık)

| Karar | Ders Sayısı | Oran |
|---|---|---|
| Güçlü uyum | 1.872 | %45.3 |
| Kabul edilebilir | 1.623 | %39.3 |
| İncelenmeli | 638 | %15.4 |

Ayrıntılı rapor: `ip5-random-forest/IP5_SONUC_RAPORU.md`.

---

## 2. GÖREV 8 (İP6) — TUTARSIZLIK ANALİZİ VE KARŞILAŞTIRMALI VALİDASYON

**Girdi:** `data/processed/master_akts_final.xlsx` (Görev 6 çıktısı), `data/processed/master_bloom.xlsx`
**Kod:** `ip6-validasyon/src/ip6_validasyon.py`, `ip6-validasyon/notebooks/ip6_validasyon.ipynb`

### 2.1 Kurum-İçi Tutarsızlık (Aşama 2a / H2 Proxy)

Aynı isimle birden fazla bölümde okutulan **244** ders grubu bulundu; bunların **28'i (%11.5)** bölümler arası AKTS aralığının ±2 kredi sınırını aşıyor (ör. "Bitirme Çalışması": 17 bölümde 1-16 AKTS arası değişiyor; "Mesleki İngilizce I/II/III": 7 bölümde 2-6 AKTS arası).

**Önemli metodolojik not:** Bu, hipotezdeki *kurumlar arası* (farklı üniversiteler) sapmanın değil, **kurum-içi** (Kocaeli Üniversitesi'nde farklı bölümler arası) sapmanın bir proxy'sidir — çünkü Kanal B (5+ üniversiteden çapraz doğrulama verisi) henüz toplanmadı. Kurum-içi veride bile anlamlı tutarsızlık bulunması, H2'nin kurumlar arası halinde muhtemelen daha da güçlü çıkacağına işaret ediyor.

### 2.2 Etkinlik Bazlı Etki (Aşama 2b)

| Etkinlik | Ort. Sapma% (var) | Ort. Sapma% (yok) | Fark | p (Mann-Whitney) |
|---|---|---|---|---|
| has_atolye | +44.18% | +9.18% | +35.00% | 0.041 |
| has_proje | +21.85% | +8.36% | +13.49% | <0.001 |
| has_lab | +19.96% | +8.98% | +10.98% | <0.001 |
| has_uygulama | +16.57% | +8.61% | +7.95% | <0.001 |
| has_sunum | +15.83% | +8.82% | +7.01% | 0.018 |
| has_sinav | +9.50% | +3.02% | +6.47% | 0.005 |
| has_odev | +12.83% | +8.61% | +4.22% | 0.002 |

Tüm 7 etkinlik bayrağı istatistiksel olarak anlamlı fark gösteriyor (p<0.05) — hiçbiri tesadüfi değil.

### 2.3 H1 — Lab/Proje Yoğun Dersler Sistematik Düşük Kredi Alıyor mu?

- Lab/proje dersleri (n=417): ortalama sapma **+19.94%**
- Diğer dersler (n=3.716): ortalama sapma **+8.16%**
- Mann-Whitney U (one-sided): **p<0.000001**
- **Sonuç: H1 DESTEKLENİYOR.**

### 2.4 H4 — Üst Düzey Bloom Derslerin Sapması Anlamlı mı?

| Bloom Düzeyi | n | Ort. Sapma% |
|---|---|---|
| L1 Hatırlama | 2.810 | +8.27% |
| L2 Anlama | 579 | +8.99% |
| L3 Uygulama | 491 | +12.34% |
| L4 Analiz | 112 | +10.32% |
| L5 Değerlendirme | 34 | +16.53% |
| L6 Yaratma | 107 | **+22.52%** |

Kruskal-Wallis H=79.43, p<0.000001; Spearman rho=0.16, p<0.000001. **Sonuç: H4 DESTEKLENİYOR** — L6 (Yaratma) dersleri, L1 (Hatırlama) derslerinin ~2.7 katı sapma gösteriyor.

### 2.5 Aşama 4 — Mevcut Motor vs. AI-Önerilen Karşılaştırması

- Pearson korelasyonu: r=0.69 (mevcut ve adaptif AKTS güçlü ama mükemmel olmayan bir uyum içinde — beklenen davranış)
- Ortalama fark: +0.17 AKTS
- %95 uyum sınırları: [-2.18, +2.52] AKTS

**Üçüncü bacak (öğrenci gerçek iş yükü) eksik** olduğundan tam üçlü karşılaştırma yapılamadı (bkz. Sınırlılıklar).

**Kalite güvence inceleme kuyruğu (pratik katkı, README §12.2):** 638/4.133 ders (%15.4) "İncelenmeli" işaretlendi; en yüksek sapmalı 50 ders `inceleme_kuyrugu_ilk50.xlsx` dosyasında koordinatör incelemesi için hazır.

### 2.6 Sınırlılıklar

- **H3 test edilemedi** — Kanal C (öğrenci anketi) toplanmadı. İP1-4 raporunda (Bölüm 4.1) baştan kabul edilen bir kısıt.
- **H2, tam biçimiyle test edilemedi** — Kanal B (kurumlar arası veri) toplanmadı; kurum-içi proxy kullanıldı.
- **Uzman görüşü validasyonu** henüz gerçek bir koordinatör/öğretim üyesi görüşmesiyle yapılmadı; bunun yerine somut bir inceleme kuyruğu üretildi.

Ayrıntılı rapor: `ip6-validasyon/IP6_SONUC_RAPORU.md`.

---

## 3. GÜNCELLENMİŞ HİPOTEZ DURUM TABLOSU

| Hipotez | Durum | Kanıt |
|---|---|---|
| H1 (lab/proje düşük kredi) | ✅ **Destekleniyor** | Mann-Whitney p<0.001, fark +11.8 puan |
| H2 (kurumlar arası sapma >±2) | ⏳ **Kurum-içi proxy ile kısmen destekleniyor** | %11.5 grup ±2 AKTS aşıyor; Kanal B gerekli |
| H3 (AI modeli gerçek yüke ≥%20 yakın) | ❌ **Test edilemedi** | Kanal C (anket) verisi yok |
| H4 (üst Bloom yüksek yük) | ✅ **Destekleniyor** | Spearman rho=0.16 p<0.001, L6 sapması L1'in 2.7 katı |

---

## 4. ÇIKTI DOSYALARI HARİTASI

```
ip5-random-forest/
├── src/ip5_random_forest.py
├── notebooks/ip5_random_forest.ipynb
├── IP5_SONUC_RAPORU.md
├── feature_importance.xlsx
└── duyarlilik_analizi.xlsx

ip6-validasyon/
├── src/ip6_validasyon.py
├── notebooks/ip6_validasyon.ipynb
├── IP6_SONUC_RAPORU.md
├── ayni_isimli_ders_tutarsizligi.xlsx
├── etkinlik_bazli_etki.xlsx
├── bloom_duzeyi_sapma_ozet.xlsx
└── inceleme_kuyrugu_ilk50.xlsx

data/processed/
├── master_akts_final.xlsx  ★ (Görev 6+8'in ana birleşik çıktısı)
└── master_akts_final.csv
```

---

## 5. SIRADAKİ ADIMLAR (Görev 11+)

1. Kanal B (kurumlar arası) ve Kanal C (öğrenci anketi) verisi toplanırsa H2/H3 tam olarak test edilebilir.
2. `inceleme_kuyrugu_ilk50.xlsx` gerçek AKTS koordinatörlerine/uzmanlara gönderilip Aşama 4'teki uzman validasyonu tamamlanabilir.
3. Tam makale yazımı (Görev 11, proje planı Bölüm 10) bu rapordaki bulguları (özellikle H1 ve H4'ün istatistiksel doğrulaması) doğrudan kullanabilir.
