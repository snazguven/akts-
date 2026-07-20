# Model Karşılaştırma Raporu — Ridge vs Random Forest vs XGBoost

Bu rapor, İP5'te (Görev 6) kullanılan Random Forest'ın gerçekten en iyi seçim olup olmadığını test etmek için hazırlandı. Üç model, **aynı özellik seti, aynı hedef sızıntısı önlemi (K_bilissel ve akts_mevcut hariç), aynı stratified train/test bölünmesi ve aynı 5-katlı out-of-fold çapraz doğrulama** ile karşılaştırıldı.

Veri seti: 4133 ders, aynı 39 özellik (ip5_adaptif_akts.py ile birebir aynı kurulum).

## Sonuç Tablosu

| Model | Test MAE | Test RMSE | Test R² | OOF MAE | OOF RMSE | OOF R² |
|---|---|---|---|---|---|---|
| XGBoost | 0.7995 | 1.0733 | 0.2031 | 0.8907 | 1.8396 | -0.233 |
| Random Forest | 0.8352 | 1.1544 | 0.0781 | 0.9285 | 1.7504 | -0.1164 |
| Ridge Regresyon | 0.8732 | 1.1563 | 0.0752 | 0.934 | 1.6191 | 0.0448 |

**OOF MAE'ye göre en iyi model: XGBoost.** Ancak bu karşılaştırma tek bir metriğe indirgenemeyecek kadar karışık çıktı — aşağıdaki 'Yorum ve Öneri' bölümüne bakın.

**Önemli metodolojik not — metrikler birbiriyle çelişiyor:** XGBoost, OOF MAE'de en iyisi (ortalama hatası en düşük) ama OOF RMSE ve R²'de en KÖTÜSÜ (en negatif R², en yüksek RMSE). Bunun anlamı: XGBoost derslerin çoğunda ufak hatalar yapıyor ama bazı derslerde büyük ölçüde yanılıyor (RMSE büyük hatalara MAE'den daha duyarlıdır). Ridge Regresyon ise tam tersi profil çiziyor: OOF R²'de tek pozitif değeri o veriyor ve OOF RMSE'de en düşük (en istikrarlı) model o. Yani 'en iyi model' sorusunun cevabı, hangi hatayı önemsediğinize bağlı: ortalama sapma mı (MAE → XGBoost), yoksa büyük/aşırı yanılgılardan kaçınmak mı (RMSE/R² → Ridge)?

## XGBoost Açıklanabilirlik (SHAP / pred_contribs)

Yöntem: shap.TreeExplainer

En etkili 10 özellik (tüm veri setinde ortalama mutlak katkı):

| Özellik | Ort. Mutlak Katkı |
|---|---|
| Fakulte_Güzel Sanatlar | 0.1653 |
| derstur_Teorik | 0.1456 |
| bloom_avg_level | 0.1118 |
| Fakulte_Fen-Edebiyat | 0.1118 |
| n_etkinlik | 0.0831 |
| derstur_Teori+Uygulama | 0.0589 |
| has_proje | 0.0453 |
| n_ogrenme_kazanim | 0.0417 |
| alan_grubu_Fen-Sosyal | 0.0358 |
| bloom_max_level | 0.0348 |

### Vaka Analizleri (Ders Bazlı Gerekçe)

**En yüksek tahminli ders: İngilizce Hazırlık** (tahmin=54.21 AKTS)
- En etkili 5 özellik (katkı değeri): n_etkinlik (+22.69); bloom_avg_level (+11.78); Fakulte_Eğitim (+3.63); n_ogrenme_kazanim (+2.84); bloom_max_level (+2.80)

**En düşük tahminli ders: Bitirme Çalışması** (tahmin=2.28 AKTS)
- En etkili 5 özellik (katkı değeri): n_ogrenme_kazanim (-0.63); derstur_Bitirme Çalışması (-0.61); bloom_avg_level (-0.40); derstur_Teorik (-0.12); has_sunum (-0.11)

## Yorum ve Öneri

Üç modelin de OOF R² değerlerinin düşük/negatif çıkması, sorunun model seçiminden değil, **verideki sinyalin zayıflığından** kaynaklandığını gösteriyor — bu, mevcut AKTS motorunun öngörülemez/tutarsız olduğu tezini destekleyen ayrı bir bulgudur.

**Öneri:** Tek bir 'kazanan' ilan etmek yerine amaca göre seçim yapılmalı:
- Amaç **'ortalama en yakın tahmin'** ise (çoğu ders için küçük hata kabul edilebilir): **XGBoost**.
- Amaç **'büyük/aşırı yanlış tahminlerden kaçınmak ve istikrar'** ise (kalite güvence aracı için daha kritik — birkaç dersi çok yanlış işaretlemek güven kaybettirir): **Ridge Regresyon**.
- Ridge'in ayrıca **tamamen şeffaf** olması (katsayılar doğrudan yorumlanabilir, SHAP/XAI aracına ihtiyaç duymaması) projenin 'açıklanabilirlik' iddiasıyla (Bölüm 4.2) doğal olarak örtüşüyor.

Bu çalışma bir keşif/karşılaştırma niteliğindedir; üretim pipeline'ındaki (`ip5_adaptif_akts.py`) `rf_tahmin_akts` sütunu, ekip bir karar vermeden DEĞİŞTİRİLMEMİŞTİR.