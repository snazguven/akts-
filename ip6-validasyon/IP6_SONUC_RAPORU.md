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
| has_atolye | +17.89% | +9.20% | +8.69% | 0.3239 | Hayır |
| has_lab | +15.97% | +9.01% | +6.96% | 0.0005 | Evet |
| has_proje | +15.54% | +8.75% | +6.79% | 0.0000 | Evet |
| has_sinav | +9.39% | +3.11% | +6.28% | 0.0028 | Evet |
| has_sunum | +13.59% | +8.89% | +4.70% | 0.0820 | Hayır |
| has_uygulama | +12.37% | +8.93% | +3.44% | 0.0001 | Evet |
| has_odev | +11.28% | +8.82% | +2.46% | 0.0419 | Evet |

## 3. H1 — Lab/Proje Yoğun Dersler Sistematik Düşük Kredi Alıyor mu?

- Lab veya proje içeren dersler (n=417): ortalama sapma = **+15.39%**
- Diğer dersler (n=3716): ortalama sapma = **+8.56%**
- Mann-Whitney U testi (one-sided, 'greater'): p = 0.000000
- **Sonuç: H1 DESTEKLENİYOR** (p<0.05 ve yön beklenen gibi).

## 4. H4 — Üst Düzey Bloom (L4-L6) Derslerin Sapması Anlamlı mı?

Bloom baskın düzeyine göre ortalama sapma%:

| Bloom Düzeyi | n | Ort. Sapma% | Std |
|---|---|---|---|
| L1 | 2810 | +8.37% | 24.02 |
| L2 | 579 | +9.10% | 21.28 |
| L3 | 491 | +11.06% | 19.34 |
| L4 | 112 | +11.96% | 22.75 |
| L5 | 34 | +15.16% | 21.87 |
| L6 | 107 | +20.10% | 38.12 |

- Kruskal-Wallis testi (bloom_dominant_level grupları arası): H = 50.2799, p = 0.000000
- Spearman korelasyonu (bloom_avg_level vs sapma_yuzde): rho = 0.1375, p = 0.000000
- **Sonuç: H4 DESTEKLENİYOR**

## 5. Aşama 4 — Mevcut Motor AKTS vs. AI-Önerilen (adaptif_akts) Karşılaştırması

- Pearson korelasyonu: r = 0.8367 (p = 0.00e+00)
- Ortalama fark (adaptif − mevcut): +0.1475 AKTS
- Fark standart sapması: 1.0403 AKTS
- %95 uyum sınırları (Bland-Altman tarzı): [-1.89, 2.19] AKTS

Kalite güvence inceleme kuyruğu: **660/4133 ders (%16.0)** 'İncelenmeli' olarak işaretlendi. En yüksek sapmalı 50 ders `inceleme_kuyrugu_ilk50.xlsx` dosyasında koordinatör incelemesi için hazırlandı — bu, projenin pratik katkı hedefinin (Bölüm 12.2) somut bir uygulamasıdır.

## 6. Sınırlılıklar (Aşama 2c / H3 — Test Edilemeyen Kısımlar)

- **Gerçek öğrenci iş yükü (Kanal C anketi)** bu iş paketi kapsamında toplanmadı. Bu yüzden 'gerçek vs. tahmin' karşılaştırması (Aşama 2c) ve **H3** ('adaptif model gerçek iş yüküne ≥%20 daha yakın') test EDİLEMEMİŞTİR. Bu, İP1-4 raporunda (Bölüm 4.1) baştan beri bilinen ve kabul edilen bir kısıttır; Risk R1/R4'te (Bölüm 9) planlanan yedek plan uyarınca makale, anketi ayrı bir gelecek çalışma olarak raporlamalı ya da anket toplanana kadar bu bölüm kısmi kanıtla (Kanal A + kurum-içi tutarsızlık) ilerlemelidir.
- **Kurumlar arası çapraz doğrulama (Kanal B, 5+ üniversite)** toplanmadığından, H2 gerçek biçimiyle değil, kurum-içi bir proxy ile test edilmiştir (bkz. Bölüm 1).
- **Uzman görüşü validasyonu** (Aşama 4) gerçek koordinatör/öğretim üyesi görüşmesi yerine, somut bir inceleme kuyruğu (review queue) çıktısıyla operasyonel hale getirilmiştir; gerçek uzman değerlendirmesi hâlâ ayrı bir adım olarak yapılmalıdır.

## 7. Çıktı Dosyaları
- `ip6-validasyon/ayni_isimli_ders_tutarsizligi.xlsx`
- `ip6-validasyon/etkinlik_bazli_etki.xlsx`
- `ip6-validasyon/bloom_duzeyi_sapma_ozet.xlsx`
- `ip6-validasyon/inceleme_kuyrugu_ilk50.xlsx`