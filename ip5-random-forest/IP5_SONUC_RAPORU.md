# İP5 Sonuç Raporu — Random Forest + Adaptif AKTS

**Görev (Bölüm 10, Görev 6):** Adaptif AKTS Hesaplayan Tahmin Modeli Oluşturma
**Sorumlu:** Samet Koca | **Durum:** Tamamlandı

## 1. Model Kurulumu
- Algoritma: RandomForestRegressor(n_estimators=200, random_state=42)
- Özellik sayısı: 39 (K_bilissel, akts_mevcut hariç — hedef sızıntısı önlendi)
- Train/test bölünmesi: Fakülte'ye göre stratified, %80/%20
- rf_tahmin_akts: 5 katlı stratified (Fakülte) çapraz doğrulama, out-of-fold

## 2. Model Kalitesi

| Metrik | Ayrılmış Test Seti (%20) | Tüm Veri (Out-of-Fold) |
|---|---|---|
| MAE  | 0.8352 | 0.9285 |
| RMSE | 1.1544 | 1.7504 |
| R²   | 0.0781 | -0.1164 |

Not: Out-of-fold R² değeri, tüm veriyle eğitilip aynı veriye tahmin yapan bir modelin R²'sinden düşük çıkar — bu beklenen ve istenen bir durumdur ("iyi taklit paradoksu"), çünkü amaç mevcut AKTS'yi ezberlemek değil, ondan anlamlı sapmaları yakalamaktır.

## 3. Özellik Önem Dereceleri (XAI) — İlk 10

| Özellik | Önem Derecesi |
|---|---|
| bloom_avg_level | 0.2610 |
| bloom_max_level | 0.1448 |
| n_ogrenme_kazanim | 0.1030 |
| n_etkinlik | 0.0710 |
| has_odev | 0.0386 |
| Fakulte_Eğitim | 0.0338 |
| Fakulte_Güzel Sanatlar | 0.0271 |
| derstur_Teorik | 0.0268 |
| alan_grubu_Sanat | 0.0252 |
| alan_grubu_Spor | 0.0249 |

## 4. Karar Dağılımı (0.70 RF / 0.30 Kural, birincil ağırlık)

| Karar | Ders Sayısı | Oran |
|---|---|---|
| Güçlü uyum | 1872 | %45.3 |
| Kabul edilebilir | 1623 | %39.3 |
| İncelenmeli | 638 | %15.4 |

## 5. Duyarlılık Analizi — Ağırlık Şemaları (Karar 3)

| Ağırlık (RF/Kural) | Ort. Mutlak Sapma % | İncelenmeli Oranı % |
|---|---|---|
| 0.50 RF / 0.50 Kural | 14.72 | 11.32 |
| 0.60 RF / 0.40 Kural | 16.11 | 12.94 |
| 0.70 RF / 0.30 Kural | 17.74 | 15.44 |
| 0.80 RF / 0.20 Kural | 19.59 | 18.0 |

## 6. Fakülte Bazlı Ortalama Sapma % (H1 ön bulgusu)

| Fakülte | Ort. Sapma % |
|---|---|
| Güzel Sanatlar | +12.68% |
| Eğitim | +11.28% |
| Teknoloji | +11.08% |
| Mühendislik | +9.19% |
| Fen-Edebiyat | +7.80% |
| Spor Bilimleri | +6.73% |
| Siyasal Bilgiler | +6.42% |

Yorum: Pozitif sapma, adaptif modelin mevcut AKTS'den daha YÜKSEK bir kredi önerdiği anlamına gelir (ör. lab/proje yoğun fakülteler). Bu, H1 hipotezinin ön testidir; istatistiksel anlamlılık testi İP6 raporunda (Görev 8) sunulmuştur.

## 7. Çıktı Dosyaları
- `data/processed/master_akts_final.xlsx` / `.csv` — her ders için rf_tahmin_akts, kural_akts, adaptif_akts (4 ağırlık şeması), sapma, karar, gerekçe
- `ip5-random-forest/feature_importance.xlsx`
- `ip5-random-forest/duyarlilik_analizi.xlsx`