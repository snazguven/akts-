# Model Seçimi Gerekçesi — Neden Random Forest Değil, XGBoost?

**Konu:** Görev 6 (İP5) kapsamında kullanılan makine öğrenmesi algoritmasının değişikliği
**Eski model:** Random Forest
**Yeni model:** XGBoost (Gradient Boosting)
**Tarih:** 20 Temmuz 2026

---

## 1. Neden Random Forest ile Başlanmıştı?

İlk uygulamada (`ip5_adaptif_akts.py`) Random Forest kullanıldı çünkü bu, ekibin İP1-4 sürecinde hazırladığı iç planlama dokümanında (`README.md`, Bölüm 15.1) belirtilen algoritmaydı. Klasör adı bile bu kararı yansıtıyordu: `ip5-adaptif-akts/`.

Random Forest, o aşamada makul bir seçimdi çünkü:
- Küçük-orta ölçekli (4.133 satır) tablo verisinde dayanıklı çalışır.
- Kategorik + sayısal karışık özellik setiyle sorunsuz başa çıkar.
- Aşırı öğrenmeye (overfitting) karşı görece dirençlidir.

## 2. Sorun Nerede Ortaya Çıktı?

Konferansa gönderilecek asıl proje metodolojisi (Google Doc'taki proje planı, **Bölüm 6.3 — Aşama 3: AI Tabanlı Adaptif Model**) incelendiğinde, resmi olarak şu yazıyordu:

> **Bileşen 3 – Dinamik Ağırlık:** *"Gradient Boosting modeli, her etkinlik için derse özgü ağırlık üretecektir."*

Bu kritik bir ayrıntı: **Random Forest, Gradient Boosting DEĞİLDİR.**

| | Random Forest | Gradient Boosting (XGBoost) |
|---|---|---|
| Çalışma mantığı | Birçok ağacı **bağımsız ve paralel** kurar, sonuçlarını ortalar (bagging) | Ağaçları **ardışık** kurar, her yeni ağaç bir öncekinin hatasını düzeltir (boosting) |
| Adı nereden geliyor | "Rastgele Orman" — ağaçlar birbirinden habersiz | "Gradyan Artırma" — hata gradyanını takip ederek iyileşir |

Yani İP5'in ilk uygulaması, ekibin kendi iç planlama notuna (README) uygundu ama **makalenin resmi metodoloji bölümüne (Bölüm 6.3) uygun değildi.** Makale "Gradient Boosting kullandık" diye yazacaksa, gerçekten Gradient Boosting kullanılmış olması gerekir — aksi hâlde makale ile kod arasında tutarsızlık olur ve bu, hakem değerlendirmesinde (peer review) ciddi bir sorun teşkil eder.

## 3. Karar Öncesi Yapılan Test: Sadece Metodolojiye Uymak Yetmez, Performansı da Doğrulamak Gerekir

Metodolojiye uymak tek başına yeterli bir gerekçe değildir — aynı zamanda Gradient Boosting'in gerçekten işe yarayıp yaramadığı da test edilmeliydi. Bu yüzden üç model, **birebir aynı koşullarda** (aynı 39 özellik, aynı hedef sızıntısı önlemi, aynı stratified train/test bölünmesi, aynı 5-katlı out-of-fold çapraz doğrulama) karşılaştırıldı (`model_karsilastirma.py`):

| Model | OOF MAE | OOF RMSE | OOF R² |
|---|---|---|---|
| **XGBoost (Gradient Boosting)** | **0.89** (en iyi) | 1.84 | -0.23 |
| Random Forest | 0.93 | 1.75 | -0.12 |
| Ridge Regresyon (taban çizgisi) | 0.93 | **1.62** (en iyi) | **+0.04** (tek pozitif) |

**Dürüst değerlendirme:** XGBoost ortalama hatada (MAE) en iyi sonucu verdi, ancak RMSE/R²'de en değişken model o çıktı (bazı derslerde büyük hata payı var). Yani XGBoost'a geçiş sadece "performans daha iyi" diye değil, **iki gerekçenin birleşimiyle** yapıldı:

1. **Metodolojik tutarlılık (asıl belirleyici gerekçe):** Makale Bölüm 6.3'te "Gradient Boosting" diye yazıyor; kodun bunu yansıtması gerekir.
2. **Performans:** XGBoost, ortalama hata (MAE) açısından da diğer iki modelden daha iyi çıktı — yani metodolojiye uymak performanstan feragat etmeyi gerektirmedi.

## 4. Neden Ridge Regresyon'a Geçmedik? (En İstikrarlı Model O Olduğu Halde)

Ridge Regresyon, OOF RMSE ve R²'de en iyi sonucu verse de, **makalenin metodolojisinde yeri yok.** Bölüm 6.3 açıkça "Gradient Boosting" diyor, "Lineer Regresyon" ya da "Ridge" demiyor. Ridge sonuçları, ayrı bir "sağlamlık kontrolü" (robustness check) olarak `MODEL_KARSILASTIRMA_RAPORU.md`'de raporlandı ama üretim modeli olarak seçilmedi.

## 5. Sonuç

**Kullanılan/kullanılacak model: XGBoost (Gradient Boosting).**

Gerekçe özetle:
- Proje planının resmi metodoloji bölümü (Bölüm 6.3, Bileşen 3) doğrudan "Gradient Boosting" diyor — Random Forest bu tanıma girmiyor.
- Bağımsız karşılaştırma testinde XGBoost, ortalama hata (MAE) açısından da en iyi sonucu verdi.
- Böylece hem makalenin yazdığıyla kodun yaptığı örtüşüyor, hem de bu tercih veriyle doğrulanmış oluyor.

**Güncelleme (20 Temmuz 2026):** `ip5_adaptif_akts.py` (üretim pipeline'ı) artık fiilen XGBoost kullanıyor — Random Forest tamamen kaldırıldı. Ayrıca yukarıdaki karşılaştırmadan sonra XGBoost, Optuna ile ayrıca ayarlandı (early stopping + hiperparametre araması, bkz. `xgboost_hiperparametre_arama.py`) ve sonuçlar daha da iyileşti: OOF MAE=0.8863, RMSE=1.5503, R²=0.1242 — Random Forest'ı artık MAE/RMSE/R²'nin **üçünde de** geçiyor (yukarıdaki tablo ayarsız XGBoost'u gösteriyor; ayrıntı: `MODEL_KARSILASTIRMA_RAPORU.md` ve `IP5_SONUC_RAPORU.md`).

Hâlâ yapılmayan tek şey: Bölüm 6.3 Bileşen 1'de tanımlanan k-means/DBSCAN ders kümeleme adımı — bu henüz uygulanmadı.
