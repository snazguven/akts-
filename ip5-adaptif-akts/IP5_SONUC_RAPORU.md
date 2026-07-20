# İP5 Sonuç Raporu — XGBoost (Gradient Boosting) + Adaptif AKTS

**Görev (Bölüm 10, Görev 6):** Adaptif AKTS Hesaplayan Tahmin Modeli Oluşturma
**Sorumlu:** Samet Koca | **Durum:** Tamamlandı

**20 Temmuz 2026 güncellemesi:** Model, Random Forest'tan ayarlanmış XGBoost'a çevrildi (bkz. `XGBOOST_MODEL_SECIMI_GEREKCESI.md`) — proje planının resmi metodolojisi (Bölüm 6.3) Gradient Boosting talep ediyor ve Optuna ile ayarlanmış XGBoost, MAE/RMSE/R²'nin üçünde de Random Forest'ı geçti.

## 1. Model Kurulumu
- Algoritma: XGBRegressor (Optuna ile ayarlanmış hiperparametreler)
- Parametreler: {'max_depth': 6, 'learning_rate': 0.04614126735633599, 'subsample': 0.9641437513503683, 'colsample_bytree': 0.6864936147132107, 'reg_alpha': 2.2536604744440076, 'reg_lambda': 1.8297509620765344, 'min_child_weight': 2, 'n_estimators': 1000}
- Early stopping: 30 round (her fold içinde ayrı doğrulama dilimiyle)
- Özellik sayısı: 39 (K_bilissel, akts_mevcut hariç — hedef sızıntısı önlendi)
- Train/test bölünmesi: Fakülte'ye göre stratified, %80/%20
- model_tahmin_akts: 5 katlı stratified (Fakülte) çapraz doğrulama, out-of-fold

## 2. Model Kalitesi

| Metrik | Ayrılmış Test Seti (%20) | Tüm Veri (Out-of-Fold) |
|---|---|---|
| MAE  | 0.8105 | 0.8863 |
| RMSE | 1.0824 | 1.5503 |
| R²   | 0.1896 | 0.1242 |

Karşılaştırma için önceki modellerin out-of-fold sonuçları (aynı veri/fold düzeni): Random Forest MAE=0.9285 RMSE=1.7504 R²=-0.1164; ayarsız XGBoost MAE=0.8907 RMSE=1.8396 R²=-0.2330. Ayrıntılar: `MODEL_KARSILASTIRMA_RAPORU.md`.

## 3. Özellik Önem Dereceleri (SHAP) — İlk 10

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
| alan_grubu_Fen-Sosyal | 0.0396 |
| derstur_Teori+Uygulama | 0.0347 |

## 4. Karar Dağılımı (0.70 Model / 0.30 Kural, birincil ağırlık)

| Karar | Ders Sayısı | Oran |
|---|---|---|
| Güçlü uyum | 1929 | %46.7 |
| Kabul edilebilir | 1544 | %37.4 |
| İncelenmeli | 660 | %16.0 |

## 5. Duyarlılık Analizi — Ağırlık Şemaları (Karar 3)

| Ağırlık (Model/Kural) | Ort. Mutlak Sapma % | İncelenmeli Oranı % |
|---|---|---|
| 0.50 Model / 0.50 Kural | 14.18 | 9.85 |
| 0.60 Model / 0.40 Kural | 15.41 | 12.58 |
| 0.70 Model / 0.30 Kural | 16.94 | 15.97 |
| 0.80 Model / 0.20 Kural | 18.72 | 19.31 |

## 6. Fakülte Bazlı Ortalama Sapma % (H1 ön bulgusu)

| Fakülte | Ort. Sapma % |
|---|---|
| Güzel Sanatlar | +12.51% |
| Teknoloji | +10.27% |
| Mühendislik | +9.50% |
| Eğitim | +8.76% |
| Fen-Edebiyat | +8.32% |
| Spor Bilimleri | +7.17% |
| Siyasal Bilgiler | +6.09% |

Yorum: Pozitif sapma, adaptif modelin mevcut AKTS'den daha YÜKSEK bir kredi önerdiği anlamına gelir (ör. lab/proje yoğun fakülteler). Bu, H1 hipotezinin ön testidir; istatistiksel anlamlılık testi İP6 raporunda (Görev 8) sunulmuştur.

## 7. Çıktı Dosyaları
- `data/processed/master_akts_final.xlsx` / `.csv` — her ders için model_tahmin_akts, kural_akts, adaptif_akts (4 ağırlık şeması), sapma, karar, gerekçe
- `ip5-adaptif-akts/feature_importance.xlsx` (SHAP tabanlı)
- `ip5-adaptif-akts/duyarlilik_analizi.xlsx`