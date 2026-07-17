# İP6 Sonuç Raporu — Tutarsızlık Analizi ve Karşılaştırmalı Validasyon

**Görev (Bölüm 10, Görev 8):** Tutarsızlık Analizi ve Karşılaştırmalı Validasyon
**Sorumlu:** Samet Koca | **Durum:** Tamamlandı

## 1. Kurum-İçi Tutarsızlık (Aşama 2a / H2 Proxy)

Aynı isimle birden fazla bölümde okutulan **244** ders grubu tespit edildi. Bunlardan **28 tanesi (11.5%)**, aynı ders için bölümler arası AKTS aralığının ±2 kredi sınırını aştığını gösteriyor.

En yüksek AKTS aralığına sahip ilk 10 ders:

| Ders Adı | Bölüm Sayısı | Min AKTS | Maks AKTS | Aralık |
|---|---|---|---|---|
| Bitirme Çalışması | 17 | 1 | 16 | 15 |
| Spor Bilimlerinde Araştırma Projesi I | 2 | 4 | 10 | 6 |
| Bilgisayar Grafikleri | 2 | 2 | 6 | 4 |
| Bitirme Projesi | 3 | 2 | 6 | 4 |
| Osmanlı Türkçesi I | 2 | 2 | 6 | 4 |
| Osmanlı Türkçesi II | 2 | 2 | 6 | 4 |
| Mesleki İngilizce I | 7 | 2 | 6 | 4 |
| Mesleki İngilizce II | 7 | 2 | 6 | 4 |
| Yazarlık I | 2 | 3 | 7 | 4 |
| Mesleki İngilizce III | 2 | 2 | 6 | 4 |

**H2 değerlendirmesi:** Bu analiz, hipotezde tanımlanan *kurumlar arası* (farklı üniversiteler) sapmanın değil, **kurum-içi** (Kocaeli Üniversitesi bünyesinde farklı bölümler arası) sapmanın bir proxy'sidir — çünkü Kanal B (5+ farklı üniversiteden çapraz doğrulama verisi, Bölüm 6.1) henüz toplanmamıştır. Kurum-içi veride dahi anlamlı bir tutarsızlık gözlenmesi, H2'nin kurumlar arası halinde de muhtemelen doğrulanacağına dair dolaylı bir işarettir, ancak kesin sonuç için Kanal B verisi gereklidir.

## 2. Etkinlik Bazlı Etki (Aşama 2b)

| Etkinlik | Ort. Sapma% (var) | Ort. Sapma% (yok) | Fark | Mann-Whitney p | Anlamlı mı |
|---|---|---|---|---|---|
| has_atolye | +44.18% | +9.18% | +35.00% | 0.0408 | Evet |
| has_proje | +21.85% | +8.36% | +13.49% | 0.0000 | Evet |
| has_lab | +19.96% | +8.98% | +10.98% | 0.0000 | Evet |
| has_uygulama | +16.57% | +8.61% | +7.95% | 0.0002 | Evet |
| has_sunum | +15.83% | +8.82% | +7.01% | 0.0175 | Evet |
| has_sinav | +9.50% | +3.02% | +6.47% | 0.0050 | Evet |
| has_odev | +12.83% | +8.61% | +4.22% | 0.0024 | Evet |

## 3. H1 — Lab/Proje Yoğun Dersler Sistematik Düşük Kredi Alıyor mu?

- Lab veya proje içeren dersler (n=417): ortalama sapma = **+19.94%**
- Diğer dersler (n=3716): ortalama sapma = **+8.16%**
- Mann-Whitney U testi (one-sided, 'greater'): p = 0.000000
- **Sonuç: H1 DESTEKLENİYOR** (p<0.05 ve yön beklenen gibi).

## 4. H4 — Üst Düzey Bloom (L4-L6) Derslerin Sapması Anlamlı mı?

Bloom baskın düzeyine göre ortalama sapma%:

| Bloom Düzeyi | n | Ort. Sapma% | Std |
|---|---|---|---|
| L1 | 2810 | +8.27% | 29.91 |
| L2 | 579 | +8.99% | 23.76 |
| L3 | 491 | +12.34% | 30.56 |
| L4 | 112 | +10.32% | 18.83 |
| L5 | 34 | +16.53% | 15.98 |
| L6 | 107 | +22.52% | 40.71 |

- Kruskal-Wallis testi (bloom_dominant_level grupları arası): H = 79.4335, p = 0.000000
- Spearman korelasyonu (bloom_avg_level vs sapma_yuzde): rho = 0.1609, p = 0.000000
- **Sonuç: H4 DESTEKLENİYOR**

## 5. Aşama 4 — Mevcut Motor AKTS vs. AI-Önerilen (adaptif_akts) Karşılaştırması

- Pearson korelasyonu: r = 0.6900 (p = 0.00e+00)
- Ortalama fark (adaptif − mevcut): +0.1700 AKTS
- Fark standart sapması: 1.1994 AKTS
- %95 uyum sınırları (Bland-Altman tarzı): [-2.18, 2.52] AKTS

Kalite güvence inceleme kuyruğu: **638/4133 ders (%15.4)** 'İncelenmeli' olarak işaretlendi. En yüksek sapmalı 50 ders `inceleme_kuyrugu_ilk50.xlsx` dosyasında koordinatör incelemesi için hazırlandı — bu, projenin pratik katkı hedefinin (Bölüm 12.2) somut bir uygulamasıdır.

## 6. Sınırlılıklar (Aşama 2c / H3 — Test Edilemeyen Kısımlar)

- **Gerçek öğrenci iş yükü (Kanal C anketi)** bu iş paketi kapsamında toplanmadı. Bu yüzden 'gerçek vs. tahmin' karşılaştırması (Aşama 2c) ve **H3** ('adaptif model gerçek iş yüküne ≥%20 daha yakın') test EDİLEMEMİŞTİR. Bu, İP1-4 raporunda (Bölüm 4.1) baştan beri bilinen ve kabul edilen bir kısıttır; Risk R1/R4'te (Bölüm 9) planlanan yedek plan uyarınca makale, anketi ayrı bir gelecek çalışma olarak raporlamalı ya da anket toplanana kadar bu bölüm kısmi kanıtla (Kanal A + kurum-içi tutarsızlık) ilerlemelidir.
- **Kurumlar arası çapraz doğrulama (Kanal B, 5+ üniversite)** toplanmadığından, H2 gerçek biçimiyle değil, kurum-içi bir proxy ile test edilmiştir (bkz. Bölüm 1).
- **Uzman görüşü validasyonu** (Aşama 4) gerçek koordinatör/öğretim üyesi görüşmesi yerine, somut bir inceleme kuyruğu (review queue) çıktısıyla operasyonel hale getirilmiştir; gerçek uzman değerlendirmesi hâlâ ayrı bir adım olarak yapılmalıdır.

## 7. Çıktı Dosyaları
- `ip6-validasyon/ayni_isimli_ders_tutarsizligi.xlsx`
- `ip6-validasyon/etkinlik_bazli_etki.xlsx`
- `ip6-validasyon/bloom_duzeyi_sapma_ozet.xlsx`
- `ip6-validasyon/inceleme_kuyrugu_ilk50.xlsx`