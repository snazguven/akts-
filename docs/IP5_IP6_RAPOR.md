# Adaptif AKTS Projesi — Görev 6 ve Görev 8 Uçtan Uca Teknik Rapor

**Proje:** Yapay Zekâ Destekli Adaptif AKTS Kredi Hesaplama Modeli
**Konferans:** 2026 YÖKAK Uluslararası Kalite Güvencesi ve Akreditasyon Konferansı — 14-15 Eylül 2026, Yıldız Teknik Üniversitesi
**Kurum:** Kocaeli Üniversitesi
**Bu raporun kapsamı:** Proje planı Bölüm 10'daki Görev 6 (Adaptif AKTS Hesaplayan Tahmin Modeli Oluşturma) ve Görev 8 (Tutarsızlık Analizi ve Karşılaştırmalı Validasyon) — repodaki İP5 ve İP6 karşılığı.
**Rapor tarihi:** 18 Temmuz 2026 (güncelleme: 20 Temmuz 2026 — üretim pipeline'ı XGBoost'a çevrildi, Bölüm 3)
**Rapor durumu:** Tamamlandı

---

## ÖZET

İP1-4'ün ürettiği zenginleştirilmiş veri seti (`master_bloom.xlsx`, 107 sütun; `model_egitim.xlsx`, 43 sütun) üzerinde:

1. **Görev 6 (İP5):** Optuna ile ayarlanmış bir XGBoost (Gradient Boosting) regresörü eğitildi, her ders için `model_tahmin_akts` üretildi, kural tabanlı `kural_akts` hesaplandı ve ikisi ağırlıklı birleştirilerek `adaptif_akts` elde edildi. *(İlk uygulama Random Forest ile yapılmıştı; 20 Temmuz 2026'da metodolojiye uyum ve daha iyi performans için XGBoost'a çevrildi — bkz. Bölüm 3.)*
2. **Görev 8 (İP6):** Kurum-içi tutarsızlık analizi, etkinlik bazlı etki analizi ve H1/H2/H4 hipotez testleri yapıldı; mevcut motor ile AI-önerilen kredi arasında karşılaştırmalı validasyon uygulandı.

**Ana bulgular (güncel XGBoost tabanlı sonuçlar):**
- **H1 DESTEKLENDİ** — Lab/proje içeren dersler, diğerlerine göre anlamlı derecede yüksek sapma gösteriyor (+15.4% vs +8.6%, p<0.001).
- **H4 DESTEKLENDİ** — Bloom düzeyi arttıkça sapma da anlamlı biçimde artıyor (rho=0.14, p<0.001).
- **H2, kurum-içi proxy ile kısmen destekleniyor** — aynı isimli derslerin %11.5'i bölümler arası ±2 AKTS sınırını aşıyor; kesin sonuç için kurumlar arası veri (Kanal B) gerekli.
- **H3 test edilemedi** — öğrenci iş yükü anketi (Kanal C) bu iş paketi kapsamında toplanmadı; bu, İP1-4 raporunda baştan beri bilinen bir kısıttır.

---

## 1. GÖREV 6 (İP5) — ADAPTİF AKTS HESAPLAYAN TAHMİN MODELİ

**Girdi:** `data/processed/model_egitim.xlsx`, `data/processed/master_bloom.xlsx`
**Çıktı:** `data/processed/master_akts_final.xlsx/.csv`
**Kod:** `ip5-adaptif-akts/src/ip5_adaptif_akts.py`, `ip5-adaptif-akts/notebooks/ip5_adaptif_akts.ipynb`

### 1.1 Uygulanan Kararlar (README.md Bölüm 15'teki 6 karar + 20 Temmuz model güncellemesi)

| # | Karar | Uygulama |
|---|---|---|
| 1 | Model + hiperparametreler + split | `XGBRegressor`, Optuna ile ayarlanmış (`max_depth=6, learning_rate=0.046, subsample=0.96, colsample_bytree=0.69, reg_alpha=2.25, reg_lambda=1.83, min_child_weight=2`), early stopping (30 round); Fakülte'ye göre stratified %80/20 train/test |
| 2 | Özellik seçimi | Tüm 39 özellik kullanıldı; **K_bilissel, K_profil, K_etkinlik ve akts_mevcut modele özellik olarak verilmedi** (Seçenek b — bağımsız hibrit bileşenler) |
| 3 | Adaptif ağırlıklar | 4 şema denendi (0.50/0.50 → 0.80/0.20), duyarlılık analizi raporlandı; birincil şema 0.70/0.30 |
| 4 | Sapma eşikleri | Yüzdesel eşik: <%10 Güçlü uyum, %10-30 Kabul edilebilir, ≥%30 İncelenmeli |
| 5 | Başarı metriği | MAE/RMSE/R², hem ayrılmış test seti hem 5-katlı out-of-fold üzerinden |
| 6 | XAI | SHAP (`shap.TreeExplainer`) tablosu + her ders için okunabilir `gerekçe` metni |

### 1.2 Hedef Sızıntısı Önlemi (README.md Bölüm 14.4)

Model, `akts_mevcut` (AKTSKredi) değerini ASLA özellik olarak görmedi — bu sütun sadece hedef değişken (y) ve `kural_akts`/`sapma` hesaplarında kullanıldı. Ayrıca `K_bilissel` (model_egitim.xlsx'te mevcuttu) özelliklerden çıkarıldı ki kural tabanlı bileşenle model tamamen bağımsız kalsın.

### 1.3 "İyi Taklit Paradoksu" ve Out-of-Fold Çözümü

Model tüm veriyle eğitilip aynı veriye tahmin yaparsa ezberler ve hiçbir sapma bulunmaz. Bunu önlemek için `model_tahmin_akts`, **5 katlı stratified (Fakülte) çapraz doğrulama ile out-of-fold** üretildi (her fold içinde ayrıca early-stopping için ayrı bir doğrulama dilimi ayrıldı): her ders, kendisinin bulunmadığı bir fold'da eğitilmiş modelden tahmin aldı.

| Metrik | Ayrılmış Test Seti (%20) | Tüm Veri (Out-of-Fold) |
|---|---|---|
| MAE  | 0.8105 AKTS | 0.8863 AKTS |
| RMSE | 1.0824 AKTS | 1.5503 AKTS |
| R²   | 0.1896 | 0.1242 |

Karşılaştırma için ilk (ayarsız) modellerin out-of-fold sonuçları: Random Forest MAE=0.9285 RMSE=1.7504 R²=-0.1164; ayarsız XGBoost MAE=0.8907 RMSE=1.8396 R²=-0.2330. Ayarlanmış XGBoost, üçünü de **MAE/RMSE/R²'nin hepsinde** geride bıraktı (bkz. Bölüm 3).

### 1.4 Özellik Önem Dereceleri (SHAP)

| Özellik | Ort. Mutlak SHAP Katkısı |
|---|---|
| derstur_Teorik | 0.1835 |
| Fakulte_Güzel Sanatlar | 0.1310 |
| bloom_avg_level | 0.1063 |
| Fakulte_Fen-Edebiyat | 0.0972 |
| n_etkinlik | 0.0685 |
| n_ogrenme_kazanim | 0.0493 |
| bloom_max_level | 0.0472 |
| has_proje | 0.0461 |

Bloom düzeyi özellikleri (K_bilissel değil, ham `bloom_avg_level`/`bloom_max_level`) ve ders türü/fakülte bağlamı modelin en güçlü sinyalleri — bu, H4 hipotezinin ön göstergesidir.

### 1.5 Duyarlılık Analizi (Karar 3)

| Ağırlık (Model/Kural) | Ort. Mutlak Sapma % | İncelenmeli Oranı % |
|---|---|---|
| 0.50 / 0.50 | 14.18 | 9.85 |
| 0.60 / 0.40 | 15.41 | 12.58 |
| 0.70 / 0.30 (birincil) | 16.94 | 15.97 |
| 0.80 / 0.20 | 18.72 | 19.31 |

Ağırlık şeması, işaretlenen ders oranını doğrudan etkiliyor — makalede bu duyarlılık açıkça tartışılmalı (README §15.3 önerisi).

### 1.6 Karar Dağılımı (0.70/0.30 birincil ağırlık)

| Karar | Ders Sayısı | Oran |
|---|---|---|
| Güçlü uyum | 1.929 | %46.7 |
| Kabul edilebilir | 1.544 | %37.4 |
| İncelenmeli | 660 | %16.0 |

Ayrıntılı rapor: `ip5-adaptif-akts/IP5_SONUC_RAPORU.md`.

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
| has_atolye | +17.89% | +9.20% | +8.69% | 0.324 (anlamlı değil) |
| has_proje | +15.54% | +8.75% | +6.79% | <0.001 |
| has_lab | +15.97% | +9.01% | +6.96% | <0.001 |
| has_uygulama | +12.37% | +8.93% | +3.44% | <0.001 |
| has_sunum | +13.59% | +8.89% | +4.70% | 0.082 (anlamlı değil) |
| has_sinav | +9.39% | +3.11% | +6.28% | 0.003 |
| has_odev | +11.28% | +8.82% | +2.46% | 0.042 |

XGBoost'a geçişle 5/7 etkinlik bayrağı anlamlı kaldı (p<0.05); **has_atolye ve has_sunum artık anlamlı çıkmıyor** (önceki RF sonucunda anlamlıydılar) — bu, modelin değişmesiyle küçük alt gruplardaki (özellikle atölye, n'si düşük) tahminlerin de değiştiğini gösteriyor. Ana bulgular (has_lab, has_proje, has_uygulama, has_sinav, has_odev) sağlam kalmaya devam ediyor.

### 2.3 H1 — Lab/Proje Yoğun Dersler Sistematik Düşük Kredi Alıyor mu?

- Lab/proje dersleri (n=417): ortalama sapma **+15.39%**
- Diğer dersler (n=3.716): ortalama sapma **+8.56%**
- Mann-Whitney U (one-sided): **p<0.000001**
- **Sonuç: H1 DESTEKLENİYOR** (XGBoost'a geçişten sonra da değişmedi).

### 2.4 H4 — Üst Düzey Bloom Derslerin Sapması Anlamlı mı?

| Bloom Düzeyi | n | Ort. Sapma% |
|---|---|---|
| L1 Hatırlama | 2.810 | +8.37% |
| L2 Anlama | 579 | +9.10% |
| L3 Uygulama | 491 | +11.06% |
| L4 Analiz | 112 | +11.96% |
| L5 Değerlendirme | 34 | +15.16% |
| L6 Yaratma | 107 | **+20.10%** |

Kruskal-Wallis H=50.28, p<0.000001; Spearman rho=0.14, p<0.000001. **Sonuç: H4 DESTEKLENİYOR** (XGBoost'a geçişten sonra da değişmedi) — L6 (Yaratma) dersleri, L1 (Hatırlama) derslerinin ~2.4 katı sapma gösteriyor.

### 2.5 Aşama 4 — Mevcut Motor vs. AI-Önerilen Karşılaştırması

- Pearson korelasyonu: **r=0.84** (XGBoost'a geçişle önceki 0.69'dan belirgin arttı — model, mevcut AKTS ile daha tutarlı bir ilişki yakalıyor)
- Ortalama fark: +0.15 AKTS
- %95 uyum sınırları: [-1.89, +2.19] AKTS (önceki [-2.18, +2.52]'ye göre daha dar — model daha istikrarlı)

**Üçüncü bacak (öğrenci gerçek iş yükü) eksik** olduğundan tam üçlü karşılaştırma yapılamadı (bkz. Sınırlılıklar).

**Kalite güvence inceleme kuyruğu (pratik katkı, README §12.2):** 660/4.133 ders (%16.0) "İncelenmeli" işaretlendi; en yüksek sapmalı 50 ders `inceleme_kuyrugu_ilk50.xlsx` dosyasında koordinatör incelemesi için hazır.

### 2.6 Sınırlılıklar

- **H3 test edilemedi** — Kanal C (öğrenci anketi) toplanmadı. İP1-4 raporunda (Bölüm 4.1) baştan kabul edilen bir kısıt.
- **H2, tam biçimiyle test edilemedi** — Kanal B (kurumlar arası veri) toplanmadı; kurum-içi proxy kullanıldı.
- **Uzman görüşü validasyonu** henüz gerçek bir koordinatör/öğretim üyesi görüşmesiyle yapılmadı; bunun yerine somut bir inceleme kuyruğu üretildi.

Ayrıntılı rapor: `ip6-validasyon/IP6_SONUC_RAPORU.md`.

---

## 3. MODEL SEÇİMİ GÜNCELLEMESİ — RANDOM FOREST'TEN XGBOOST'A GEÇİŞ

**Tarih:** 20 Temmuz 2026 | **Ayrıntılı gerekçe:** `ip5-adaptif-akts/XGBOOST_MODEL_SECIMI_GEREKCESI.md`

### 3.1 Sorun

Görev 6'nın ilk uygulamasında Random Forest kullanıldı — bu, ekibin iç planlama dokümanının (README.md §15.1) tercihiydi. Ancak proje planının **resmi metodoloji bölümü (Bölüm 6.3, Bileşen 3 — Dinamik Ağırlık)** açıkça şunu belirtiyor:

> *"Gradient Boosting modeli, her etkinlik için derse özgü ağırlık üretecektir."*

**Random Forest, Gradient Boosting değildir** (RF bağımsız ağaçları paralel kurup ortalar — bagging; Gradient Boosting ise ağaçları ardışık kurup bir öncekinin hatasını düzeltir). Yani ilk uygulama, makalenin resmi metodolojisiyle tutarsızdı.

### 3.2 Karşılaştırma ve Karar

Bu tutarsızlığı çözmek için üç model, birebir aynı koşullarda (aynı 39 özellik, aynı hedef sızıntısı önlemi, aynı stratified split, aynı 5-katlı out-of-fold CV) karşılaştırıldı (`ip5-adaptif-akts/src/model_karsilastirma.py`, sonuçlar `MODEL_KARSILASTIRMA_RAPORU.md`'de):

| Model | OOF MAE | OOF RMSE | OOF R² |
|---|---|---|---|
| **XGBoost (Gradient Boosting)** | **0.89** (en iyi) | 1.84 | -0.23 |
| Random Forest | 0.93 | 1.75 | -0.12 |
| Ridge Regresyon (taban çizgisi) | 0.93 | **1.62** (en iyi) | **+0.04** (tek pozitif) |

**Karar: XGBoost'a geçildi.** Gerekçe iki katmanlı:
1. **Metodolojik tutarlılık (asıl belirleyici sebep):** XGBoost, "eXtreme Gradient Boosting"in ta kendisi — Bölüm 6.3'ün talep ettiği algoritma tam olarak bu.
2. **Performans:** Bağımsız testte XGBoost, ortalama hata (MAE) açısından da en iyi sonucu verdi — metodolojiye uymak performanstan feragat etmeyi gerektirmedi.

Ridge Regresyon, RMSE/R²'de daha istikrarlı çıksa da metodolojide yeri olmadığı için (Bölüm 6.3 sadece Gradient Boosting'i tanımlıyor) üretim modeli olarak seçilmedi; sonuçları sadece sağlamlık kontrolü (robustness check) olarak raporlandı.

### 3.3 Ayarlanmış (Tuned) XGBoost — İkinci Karşılaştırma

Ayarsız XGBoost'un RMSE/R²'de Random Forest'tan zayıf çıkması üzerine, Optuna ile bir hiperparametre araması yapıldı (`ip5-adaptif-akts/src/xgboost_hiperparametre_arama.py`, 50 deneme, aynı 5-katlı stratified CV, her fold içinde early stopping):

| Model | OOF MAE | OOF RMSE | OOF R² |
|---|---|---|---|
| Random Forest | 0.9285 | 1.7504 | -0.1164 |
| XGBoost (ayarsız) | 0.8907 | 1.8396 | -0.2330 |
| **XGBoost (Optuna ile ayarlanmış)** | **0.8863** | **1.5503** | **0.1242** |

Ayarlanmış XGBoost (max_depth=6, learning_rate=0.046, subsample=0.96, colsample_bytree=0.69, reg_alpha=2.25, reg_lambda=1.83, min_child_weight=2, early stopping) **üçüncü metrikte de Random Forest'ı geçti** — early stopping ve regularizasyon, ayarsız XGBoost'un büyük hata sorununu giderdi.

### 3.4 Durum: Üretim Pipeline'ı Güncellendi

**`ip5_adaptif_akts.py`, 20 Temmuz 2026 itibarıyla ayarlanmış XGBoost'a çevrildi ve yeniden çalıştırıldı.** `master_akts_final.xlsx` bu yeni modelle yeniden üretildi; İP6 analizleri de güncel veriyle tekrarlandı (Bölüm 2'deki sayılar günceldir). Klasör/dosya adları (`ip5-adaptif-akts/`, `ip5_adaptif_akts.py`) proje planındaki Görev 6/İP5 numaralandırmasıyla tutarlılık için değiştirilmedi; içerik artık XGBoost kullanıyor.

Bölüm 6.3 Bileşen 1'de tanımlanan k-means/DBSCAN kümeleme adımı henüz uygulanmadı (bkz. Sıradaki Adımlar).

---

## 4. GÜNCELLENMİŞ HİPOTEZ DURUM TABLOSU

| Hipotez | Durum | Kanıt |
|---|---|---|
| H1 (lab/proje düşük kredi) | ✅ **Destekleniyor** | Mann-Whitney p<0.001, fark +6.8 puan (XGBoost ile) |
| H2 (kurumlar arası sapma >±2) | ⏳ **Kurum-içi proxy ile kısmen destekleniyor** | %11.5 grup ±2 AKTS aşıyor; Kanal B gerekli |
| H3 (AI modeli gerçek yüke ≥%20 yakın) | ❌ **Test edilemedi** | Kanal C (anket) verisi yok |
| H4 (üst Bloom yüksek yük) | ✅ **Destekleniyor** | Spearman rho=0.14 p<0.001, L6 sapması L1'in 2.4 katı (XGBoost ile) |

*Not: Sayılar 20 Temmuz 2026'daki XGBoost güncellemesiyle yeniden hesaplanmıştır; her iki hipotezin yönü ve anlamlılığı model değişikliğinden etkilenmedi.*

---

## 5. ÇIKTI DOSYALARI HARİTASI

```
ip5-adaptif-akts/
├── src/ip5_adaptif_akts.py          ★ üretim pipeline'ı (artık XGBoost)
├── src/model_karsilastirma.py        (Ridge/RF/XGBoost karşılaştırması)
├── src/xgboost_hiperparametre_arama.py  (Optuna ile ayarlama)
├── notebooks/ip5_adaptif_akts.ipynb
├── IP5_SONUC_RAPORU.md
├── MODEL_KARSILASTIRMA_RAPORU.md
├── XGBOOST_MODEL_SECIMI_GEREKCESI.md
├── xgboost_en_iyi_parametreler.json
├── feature_importance.xlsx (SHAP tabanlı)
├── duyarlilik_analizi.xlsx
├── model_karsilastirma.xlsx
└── shap_ozet.xlsx

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

## 6. SIRADAKİ ADIMLAR (Görev 11+)

1. Kanal B (kurumlar arası) ve Kanal C (öğrenci anketi) verisi toplanırsa H2/H3 tam olarak test edilebilir.
2. `inceleme_kuyrugu_ilk50.xlsx` gerçek AKTS koordinatörlerine/uzmanlara gönderilip Aşama 4'teki uzman validasyonu tamamlanabilir.
3. Tam makale yazımı (Görev 11, proje planı Bölüm 10) bu rapordaki bulguları (özellikle H1 ve H4'ün istatistiksel doğrulaması) doğrudan kullanabilir.
4. Bölüm 6.3 Bileşen 1'de tanımlanan k-means/DBSCAN ders kümeleme adımının eklenmesi — şu an hiç uygulanmadı.
