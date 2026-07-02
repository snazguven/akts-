# Adaptif AKTS Projesi — İş Paketi 1-4 Uçtan Uca Teknik Rapor

**Proje:** Yapay Zekâ Destekli Adaptif AKTS Kredi Hesaplama Modeli
**Konferans:** 2026 YÖKAK Uluslararası Kalite Güvencesi ve Akreditasyon Konferansı — 14-15 Eylül 2026, Yıldız Teknik Üniversitesi
**Kurum:** Kocaeli Üniversitesi
**Ekip:** Dr. Ayhan Gültekin · Samet Koca · Sudenaz Güven · Mevlüt Alp Kılınç
**Bu raporun kapsamı:** İş Paketi 1'den İş Paketi 4'e kadar (dahil) yapılan tüm çalışmaların teorik, metodolojik ve teknik dökümü
**Rapor tarihi:** 2 Temmuz 2026
**Rapor durumu:** İP5 (Random Forest + Adaptif AKTS) öncesi beyin fırtınası ve konsolidasyon belgesi

---

## İÇİNDEKİLER

1. Yönetici Özeti
2. Projenin Büyük Resmi: Neden Bu Projeyi Yapıyoruz?
3. Problem Tanımı: Statik AKTS Motorunun Kusurları
4. Çözüm Felsefesi: Adaptif AKTS Nedir, Ne Değildir?
5. Metodolojik Omurga: Feature Enrichment Pipeline Mantığı
6. İş Paketi 1 — Ham Veri Toplama (EBS)
7. İş Paketi 2 — Veri Temizleme, İÖ Tekilleştirme, Master Tablo
8. İş Paketi 3 — Bloom Taksonomisi ve Bilişsel Katsayı
9. Ara Aşama — One-Hot Encoding ve Model Veri Seti
10. İş Paketi 4 — Yapısal Gruplama Katsayısı (K_profil, K_etkinlik)
11. Şu Ana Kadar Üretilen Tüm Katsayıların Sentezi
12. Veri Setinin Anatomisi: Sütun Sütun Açıklama
13. Kritik Bulgular ve Bunların Makaleye Yansıması
14. İP5'e Devir: Ne Hazır, Ne Eksik?
15. İP5 Beyin Fırtınası: Karşımızdaki Kararlar
16. Ekler: Formül Kütüphanesi ve Dosya Haritası

---

# 1. YÖNETİCİ ÖZETİ

Bu proje, Türkiye'deki yükseköğretim kurumlarının AKTS (Avrupa Kredi Transfer Sistemi) kredilerini hesaplarken kullandığı **statik iş yükü motorunun** yapısal kusurlarını veri ile ortaya koymayı ve bunun yerine **yapay zekâ destekli, açıklanabilir, adaptif bir karar destek modeli** önermeyi amaçlıyor.

İş Paketi 1'den 4'e kadar olan süreçte, projenin **veri hazırlama ve öznitelik mühendisliği omurgası** kuruldu. Bu, bütün makine öğrenmesi projelerinin en kritik ve en çok zaman alan kısmıdır — çünkü model ancak kendisine verilen verinin kalitesi kadar iyi olabilir ("garbage in, garbage out" ilkesi).

Kısaca yapılanlar:

- **İP1:** Kocaeli Üniversitesi Bologna/EBS sisteminden 7 fakülteye ait 5.807 ham ders kaydı toplandı.
- **İP2:** Bu ham veri temizlendi (hatalı kayıtlar atıldı), ikinci öğretim tekrarları tekilleştirildi ve 4.133 satırlık temiz bir "master tablo" oluşturuldu. Ayrıca etkinlik profili öznitelikleri (has_lab, has_proje vb.) türetildi.
- **İP3:** Her dersin öğrenme kazanımları, Bloom Taksonomisi'ne göre NLP (doğal dil işleme) ile analiz edildi ve her ders için bir **bilişsel zorluk katsayısı (K_bilissel)** üretildi.
- **Ara aşama:** Kategorik değişkenler (fakülte, alan grubu, ders türü) One-Hot Encoding ile sayısallaştırıldı, böylece modelin okuyabileceği bir eğitim tablosu (model_egitim.xlsx) hazırlandı.
- **İP4:** Dersin etkinlik profiline dayalı **yapısal gruplama katsayıları (K_profil ve K_etkinlik)** hesaplandı.

Bu noktada elimizde, her dersin bağlamını, bilişsel zorluğunu ve yapısal yoğunluğunu sayısal olarak tarif eden zengin bir veri seti var. İP5'te bu veri seti, mevcut AKTS örüntüsünü öğrenecek bir Random Forest modeline verilecek ve nihai adaptif AKTS değeri üretilecek.

Bu rapor, bu dört iş paketinin **neden, nasıl ve ne sonuçla** yapıldığını en ince ayrıntısına kadar açıklıyor.

---

# 2. PROJENİN BÜYÜK RESMİ: NEDEN BU PROJEYİ YAPIYORUZ?

## 2.1 AKTS Nedir ve Neden Önemlidir?

AKTS (Avrupa Kredi Transfer ve Toplama Sistemi / ECTS), 1989'da Erasmus programı kapsamında, farklı Avrupa üniversiteleri arasında öğrenci hareketliliğini kolaylaştırmak için doğdu. Temel fikir basittir: bir dersin "ne kadar iş" olduğunu ölçmek için ortak bir para birimi yaratmak. 2015'ten itibaren AKTS, Avrupa Yükseköğretim Alanı'nın (EHEA) resmi kredi sistemi hâline geldi.

AKTS'nin temel varsayımı şudur: **1 akademik yıl = 60 AKTS = yaklaşık 1500-1800 saat öğrenci iş yükü.** Buradan geriye doğru gidildiğinde, **1 AKTS = 25-30 saat öğrenci iş yükü** olarak tanımlanır.

Bu neden önemli? Çünkü AKTS sadece bir muhasebe birimi değil — öğrencinin mezun olmak için ne kadar emek harcayacağını, bir dersin diploma programındaki ağırlığını, ve kurumlar arası denklik süreçlerini doğrudan belirler. Yanlış hesaplanmış bir AKTS, öğrencinin gerçek yükünü gizler; bazı dersler hak ettiğinden az kredi alırken bazıları fazla alır. Bu da hem öğrenci adaletini hem de akreditasyon kalitesini zedeler.

## 2.2 Mevcut Sistem Nasıl Çalışıyor?

Türkiye'de üniversiteler AKTS'yi şöyle hesaplar. Her ders için 14 etkinlik kategorisi tanımlıdır:

1. Ders Hafta Sayısı ve Saati
2. Sınıf Dışı Çalışma Süresi
3. Ara Sınav
4. Kısa Sınav (Quiz)
5. Ödev
6. Uygulama
7. Laboratuvar
8. Proje
9. Atölye
10. Sunum / Seminer Hazırlama
11. Alan Çalışması
12. Diğer
13. Yarıyıl Sonu Sınavı

Her etkinlik için öğretim üyesi veya AKTS koordinatörü şunu girer: **Sayı × Süre (saat) = O etkinliğin toplam yükü.** Örneğin "14 hafta × 3 saat ders = 42 saat". Bütün etkinliklerin yükü toplanır ve **25'e (veya 30'a) bölünerek** AKTS kredisi elde edilir.

Bu, düz bir aritmetik işlemdir. Hiçbir ağırlıklandırma yoktur. İşte projenin tüm çıkış noktası da burada gizli.

## 2.3 Bu Projenin Doğuş Noktası: "1 Saat = 1 Saat mi?"

Sistemin temel varsayımı şudur: **bir saat, hangi etkinlikte harcanırsa harcansın, bir saattir.** Yani:

> 1 saat laboratuvarda deney yapmak = 1 saat amfide ders dinlemek = 1 saat evde ödev yapmak = 1 saat sınav olmak.

Ama bu doğru mu? Sezgisel olarak hayır. Bir mühendislik laboratuvarında karmaşık bir deneyi kurmak, çalıştırmak, veri toplamak ve rapor yazmak; pasif olarak bir konferans dinlemekten bilişsel olarak çok daha yüklüdür. Bir bitirme projesi tasarlamak, çoktan seçmeli bir quiz'e çalışmaktan kat kat ağırdır.

İşte projenin **araştırma boşluğu (research gap)** tam olarak budur: mevcut literatür bu sorunu *tespit* etmiştir (Impola 2025, Rivadeneyra 2022, Navarro vd. 2014), ama çözümü hep "politika değişikliği" veya "farkındalık artırma" düzeyinde bırakmıştır. **Hiç kimse AKTS hesaplama motorunun kendisini yapay zekâ ile yeniden tasarlamayı önermemiştir.** Bizim özgün katkımız budur.

## 2.4 Projenin Üç Katkı Ekseni

Bu proje üç düzeyde katkı hedefliyor:

**Akademik katkı:** AKTS hesaplamasında açıklanabilir, ders bazlı, yapay zekâ destekli adaptif değerlendirmeyi literatüre ilk kez sistematik olarak sokmak. Özellikle Bloom düzeyi ile kredi ilişkisini gerçek veriden modellemek.

**Pratik katkı:** Kalite güvence koordinatörlerine "bu dersin yükü emsallerine göre yüksek/düşük görünüyor, incelemelisiniz" uyarısı veren somut bir karar destek prototipi üretmek.

**Politika katkısı:** YÖKAK ve üniversitelere, AKTS süreçlerini veri güdümlü ve daha tutarlı hâle getirmeleri için kanıta dayalı öneriler sunmak.

---

# 3. PROBLEM TANIMI: STATİK AKTS MOTORUNUN KUSURLARI

Bu bölümde, mevcut sistemin beş temel yapısal sorununu tek tek, derinlemesine ele alıyoruz. Bu sorunlar projenin var oluş sebebidir ve her biri doğrudan bir hipoteze bağlanır.

## 3.1 Sorun 1 — Eşit Ağırlıklandırma

Motor, tüm etkinlik türlerini aynı katsayıyla (1.0) değerlendirir. Bilişsel yük, zorluk derecesi ve gerçek zaman maliyeti arasındaki farklar tamamen görmezden gelinir. Bir öğrencinin bir saat boyunca pasif dinlemesi ile bir saat boyunca aktif problem çözmesi bilişsel olarak eşdeğer sayılır. Oysa eğitim psikolojisi literatürü (Kyndt vd. 2014) bunun yanlış olduğunu net biçimde gösterir: görev karmaşıklığı arttıkça algılanan ve gerçek iş yükü doğrusal olmayan biçimde artar.

## 3.2 Sorun 2 — Subjektif Veri Girişi

Etkinlik değerleri manuel girilir. Aynı ders için farklı öğretim üyeleri veya koordinatörler farklı değerler girebilir. Bu, veriye sistematik olmayan bir gürültü (noise) katar. Bir bölümde "Ödev: 5 saat" yazan bir hoca, komşu bölümde aynı içerikteki ders için "Ödev: 15 saat" yazabilir. Bu subjektiflik, kredi değerlerini kişiye bağımlı ve tutarsız kılar.

## 3.3 Sorun 3 — Ders Profili Duyarsızlığı

Mühendislik laboratuvarı ile sosyal bilim semineri **aynı formülden** geçer. Sistemin ders türüne göre ağırlık diferansiyasyonu yapacak hiçbir mekanizması yoktur. Bir laboratuvar dersinin doğası gereği gerektirdiği ekipman hazırlığı, güvenlik prosedürleri, veri analizi ve raporlama; bir seminer dersinin okuma ve tartışma yükünden yapısal olarak farklıdır. Ama motor bu farkı göremez.

## 3.4 Sorun 4 — Kurum/Bölüm İçi Tutarsızlık

Aynı isimli dersler (örneğin "Matematik I") farklı bölümlerde farklı AKTS değerleri alır. Bu, bazen meşru bir sebebe dayanır (farklı bölümlerde farklı derinlikte işlenebilir), ama çoğu zaman sadece tutarsız veri girişinin sonucudur. Bu tutarsızlık, öğrenci denklik süreçlerinde ve programlar arası karşılaştırmada ciddi sorunlar doğurur.

## 3.5 Sorun 5 — Bilişsel Yük Görmezliği

Bu, projenin kalbindeki sorundur. Bloom Taksonomisi'nde "Hatırla" (en alt düzey) bir kazanıma sahip bir ders ile "Yarat" (en üst düzey) bir kazanıma sahip bir ders, aynı saatlik iş yükü için **aynı krediyi** alabilir. Oysa bilgiyi hatırlamak ile özgün bir şey yaratmak arasında devasa bir bilişsel uçurum vardır. Motor bu uçurumu göremez çünkü sadece saatlere bakar, öğrenme kazanımlarının bilişsel derinliğine bakmaz.

## 3.6 Bu Sorunların Hipotezlere Bağlanması

Bu beş sorun, projenin dört hipotezine doğrudan bağlanır:

- **H1:** Statik motor, laboratuvar ve proje yoğun derslerde beklenen iş yüküne göre sistematik olarak DÜŞÜK kredi eğilimindedir. (Sorun 1 ve 3'ten doğar.)
- **H2:** Aynı isimli dersler için bölümler arası AKTS sapması anlamlı düzeydedir. (Sorun 2 ve 4'ten doğar.)
- **H3:** Adaptif model, mevcut motora kıyasla ders profiline daha duyarlı ve açıklanabilir kredi değerleri üretir. (Çözümün kendisi.)
- **H4:** Üst düzey Bloom çıktısı içeren derslerin beklenen yükü, mevcut AKTS'nin öngördüğünden yüksektir. (Sorun 5'ten doğar.)

Şimdiye kadarki İP1-4 çalışması, özellikle **H4'ü test etmek için gereken bilişsel altyapıyı** ve **H1'i test etmek için gereken yapısal altyapıyı** kurdu.

---

# 4. ÇÖZÜM FELSEFESİ: ADAPTİF AKTS NEDİR, NE DEĞİLDİR?

## 4.1 En Kritik Konumlandırma: Biz "Doğru AKTS'yi" İddia Etmiyoruz

Bu, projenin en sık yanlış anlaşılan ve en dikkatli açıklanması gereken noktasıdır. Bizim amacımız **mevcut AKTS değerini doğrudan "yanlış" ilan etmek DEĞİLDİR.** Çünkü:

1. Gerçek öğrenci iş yükü verimiz yok (anket yapılmadı, sadece EBS kayıtları var).
2. "Doğru" AKTS'nin tek bir nesnel değeri yoktur — bağlama bağlıdır.

Bunun yerine amacımız şudur: dersin **fakülte/bölüm bağlamı, alan grubu, ders türü, etkinlik profili ve öğrenme kazanımlarının Bloom temelli bilişsel düzeyi** dikkate alınarak, o dersin **beklenen (adaptif) AKTS değerini** üretmek; ve mevcut değerinden **anlamlı ölçüde sapan** dersleri kalite güvence açısından **işaretlemek.**

Yani çıktımız bir "hüküm" değil, bir "uyarı bayrağıdır." Sistem şunu der: *"Bu dersin profili, veri setindeki benzer derslere göre daha yüksek/düşük bir kredi bekletiyor — bir koordinatör bunu incelemeli."*

## 4.2 Neden Bu Konumlandırma Akademik Olarak Daha Güçlü?

Bu konumlandırma bize üç avantaj sağlar:

**Savunulabilirlik:** "Doğru AKTS budur" demek, elimizde ground truth (gerçek referans) olmadığı için savunulamaz. Ama "bu ders emsallerinden sapıyor" demek, tamamen veriden türetilen, savunulabilir bir istatistiksel iddiadır.

**Açıklanabilirlik:** Her uyarının bir gerekçesi vardır (bu dersin proje + laboratuvarı var, Bloom düzeyi yüksek, bu yüzden beklenen yük daha fazla). Bu, kara kutu bir tahmin değil, şeffaf bir karar destek sistemidir.

**Pratik değer:** Koordinatörler binlerce dersi tek tek inceleyemez. Sistem onlara "önce şu 200 derse bakın" der. Bu, gerçek bir kalite güvence aracıdır.

## 4.3 Hibrit Yaklaşım: Neden Sadece Makine Öğrenmesi Değil?

Projenin metodolojik zarafeti, **iki farklı yaklaşımı birleştirmesindedir:**

**Makine öğrenmesi bileşeni (Random Forest):** Veri setindeki mevcut AKTS örüntüsünü öğrenir. "Bu tür özelliklere sahip dersler genellikle kaç AKTS alıyor?" sorusunu yanıtlar. Bu, veriden gelen, veri-güdümlü bir tahmindir.

**Kural tabanlı bileşen (K katsayıları):** Uzman bilgisini ve pedagojik teoriyi (Bloom, etkinlik yoğunluğu) açıklanabilir formüllere kodlar. "Bu dersin lab'ı ve projesi var, bu yüzden yükü %25 daha yüksek olmalı" der.

Nihai adaptif değer, bu ikisinin **ağırlıklı birleşimidir:**

```
adaptif_akts = 0.70 × rf_tahmin_akts + 0.30 × kural_akts
```

Random Forest ana bileşendir (%70) çünkü veriden öğrenir ve genellenebilir. Kural tabanlı bileşen (%30) açıklanabilir bir düzeltme katmanı ekler — modelin gözden kaçırabileceği pedagojik nüansları hesaba katar. Bu hibrit yapı, hem veri-güdümlü hem teori-güdümlü olmanın avantajlarını birleştirir.

---

# 5. METODOLOJİK OMURGA: FEATURE ENRICHMENT PIPELINE MANTIĞI

## 5.1 Pipeline (Boru Hattı) Nedir?

Projenin tüm teknik omurgası, **tek bir master tabloyu adım adım zenginleştiren bir boru hattı (pipeline)** üzerine kuruludur. Bu yaklaşımın adı "feature enrichment" (öznitelik zenginleştirme).

Temel ilke şudur: **Ham veri asla bozulmaz.** Her aşamada, mevcut tabloya yeni sütunlar (öznitelikler) eklenir. Hiçbir aşama önceki veriyi silmez veya değiştirmez; sadece üzerine bilgi ekler. Bu sayede:

- Her adım geri izlenebilir (traceable).
- Bir hata olursa hangi aşamada olduğu bellidir.
- Ara çıktılar bağımsız olarak incelenebilir.

## 5.2 14 Aşamalı Pipeline Haritası

Projenin tam pipeline'ı 14 aşamadan oluşur. İP1-4 bu aşamaların ilk yarısını kapsar:

| Aşama | İşlem | Çıktı | Durum |
|-------|-------|-------|-------|
| 1 | Yedi fakülteden ham veri | Ham ders tablosu | ✅ İP1 |
| 2 | Temizlik + İÖ tekilleştirme | Temiz ders tablosu | ✅ İP2 |
| 3 | Öğrenme kazanımı metinleri | Kazanım tablosu | ✅ İP2 |
| 4 | Bloom analizi (NLP) | bloom_level, K_bilissel | ✅ İP3 |
| 5 | Etkinlik profili öznitelikleri | has_*, act_*, n_etkinlik | ✅ İP2 |
| 6 | Master veri seti | Birleşik analiz tablosu | ✅ İP2/3 |
| 7 | One-Hot Encoding | Model eğitim tablosu | ✅ Ara aşama |
| — | Yapısal gruplama katsayısı | K_profil, K_etkinlik | ✅ İP4 |
| 8 | Random Forest eğitimi | AKTS tahmin modeli | ⏳ İP5 |
| 9 | Her ders için RF tahmini | rf_tahmin_akts | ⏳ İP5 |
| 10 | Kural tabanlı düzeltme | kural_akts | ⏳ İP5 |
| 11 | Adaptif AKTS hesabı | adaptif_akts | ⏳ İP5 |
| 12 | Sapma + karar + gerekçe | sapma, karar, gerekçe | ⏳ İP6 |
| 13 | Açıklanabilir AI (XAI) | özellik önem dereceleri | ⏳ İP6 |
| 14 | Özet analizler | Konferans bulguları | ⏳ İP6 |

Not: Pipeline aşama numaraları ile iş paketi numaraları birebir örtüşmez. İş paketleri kişilere göre bölünmüştür; pipeline aşamaları ise mantıksal işlem adımlarıdır. Örneğin İP2 (Sudenaz), pipeline'ın 2, 3, 5 ve 6. aşamalarını kapsar.

## 5.3 Neden Bu Sıra?

Pipeline'ın sırası keyfi değildir — her aşama bir öncekine bağımlıdır:

- Temizlik (2) yapılmadan hiçbir analiz güvenilir olmaz.
- Bloom analizi (4) için kazanım metinlerinin (3) hazır olması gerekir.
- One-Hot Encoding (7), model eğitimi (8) için ön koşuldur çünkü modeller metin değil sayı okur.
- K katsayıları (İP4), kural tabanlı AKTS (10) için gereklidir.
- Random Forest tahmini (9) ve kural tabanlı AKTS (10) olmadan adaptif AKTS (11) hesaplanamaz.

Bu bağımlılık zinciri, iş paketlerinin neden belirli bir sırayla ve belirli kişilere atandığını açıklar.

---

# 6. İŞ PAKETİ 1 — HAM VERİ TOPLAMA (EBS)

**Sorumlu:** Dr. Ayhan Gültekin
**Durum:** Tamamlandı
**Çıktı:** `ip1-ham-veri/` ve `data/raw/` klasörlerinde 7 fakülte xlsx dosyası

## 6.1 Amaç ve Kapsam

İş Paketi 1, tüm projenin hammaddesini sağlar. Kocaeli Üniversitesi'nin Bologna/EBS (Eğitim Bilgi Sistemi) portalından, yedi fakülteye ait tüm ders kayıtları sistematik olarak indirildi. Her fakülte ayrı bir Excel dosyası olarak dışa aktarıldı.

## 6.2 Veri Kaynağı: Bologna/EBS Sistemi Nedir?

Bologna Bilgi Sistemi (EBS), Türkiye'deki üniversitelerin Bologna sürecine uyum kapsamında tuttuğu resmi ders kataloğudur. Her ders için şu bilgileri barındırır: ders kodu (katalog id), ders adı, bölüm, fakülte, eğitim yılı, AKTS kredisi, öğrenme kazanımları ve etkinlik profili. Bu sistem, üniversitenin resmi ve en güvenilir ders veri kaynağıdır.

## 6.3 Toplanan Veri: Yedi Fakülte

| Fakülte | Ham Ders Satırı | Bölüm Sayısı | Ortalama AKTS |
|---------|-----------------|--------------|---------------|
| Mühendislik | 1.623 | 17 | 4,22 |
| Güzel Sanatlar | 1.149 | 11 | 3,56 |
| Fen-Edebiyat | 978 | 10 | 4,42 |
| Eğitim | 641 | 8 | 3,90 |
| Siyasal Bilgiler | 568 | 6 | 4,07 |
| Spor Bilimleri | 442 | 4 | 4,35 |
| Teknoloji | 406 | 4 | 4,16 |
| **TOPLAM** | **5.807** | **60** | **≈4,1** |

Dosya adları: `Mu_hendislik.xlsx`, `Gu_zel_Sanatlar.xlsx`, `FenEdebiyat.xlsx`, `Eg_itim.xlsx`, `Siyasal_Bilgiler.xlsx`, `Spor_Bilimleri.xlsx`, `Teknoloji.xlsx`

## 6.4 Neden Bu Yedi Fakülte?

Bu yedi fakülte, üniversitenin **disiplinsel çeşitliliğini** temsil edecek şekilde seçildi. Amacımız, adaptif modelin farklı ders profillerinde nasıl davrandığını test etmek. Bunun için elimizde:

- **STEM ağırlıklı fakülteler:** Mühendislik, Teknoloji (laboratuvar ve proje yoğun)
- **Sosyal bilim fakülteleri:** Siyasal Bilgiler, Eğitim (teori ağırlıklı)
- **Karma fakülte:** Fen-Edebiyat (hem fen hem sosyal bölümler içerir)
- **Sanat fakültesi:** Güzel Sanatlar (atölye ve uygulama yoğun)
- **Uygulamalı fakülte:** Spor Bilimleri (uygulama ve saha yoğun)

Bu çeşitlilik, modelin genellenebilirliğini test etmek için idealdir. Eğer sadece mühendislik verisi olsaydı, model sosyal bilimlerdeki farklı yük örüntülerini öğrenemezdi.

## 6.5 Kritik Metodolojik Not: Veri Gerçeği

İP1'in en önemli çıktısı sadece veri değil, aynı zamanda bir **veri gerçeğinin (data reality) keşfidir.** EBS dışa aktarımında etkinlik bilgisi **yalnızca etkinlik kimliği ve adı olarak** gelmektedir. Yani "bu derste laboratuvar var" bilgisi mevcuttur, ama **her etkinliğin kaç saat sürdüğü (sayı × süre) bilgisi veri setinde YOKTUR.**

Bu, projenin metodolojisini kökten şekillendiren bir kısıttır. Şöyle ki:

- **Yapamadığımız:** "Saat × katsayı" temelli bir iş yükü motoru kuramayız, çünkü saat verisi yok.
- **Yaptığımız:** Etkinliklerin **varlık/sayı** özniteliklerini (has_lab = var mı yok mu, n_etkinlik = kaç etkinlik türü var) kullanan bir model kurduk.

Bu kısıt aslında bir zayıflık değil, dürüst bir metodolojik tercih. İleride gerçek etkinlik saatleri elde edilirse (örneğin öğrenci anketleriyle), model bu özniteliklerle güçlendirilebilir. Ama şimdilik pilot analiz için varlık öznitelikleri yeterlidir.

## 6.6 Veride Gözlenen 14 Etkinlik Türü

Ham veride şu 14 etkinlik türü gözlendi: Ders Hafta Sayısı ve Saati, Sınıf Dışı Çalışma, Yarıyıl Sonu Sınavı, Ara Sınav, Ödev, Uygulama, Proje, Sunum/Seminer Hazırlama, Kısa Sınav, Laboratuvar, Diğer, Quiz, Alan Çalışması, Atölye.

Ders başına ortalama yaklaşık **6 öğrenme kazanımı** ve **4,5 etkinlik** düşmektedir. Bu istatistikler, sonraki aşamalarda öznitelik mühendisliğinin temelini oluşturdu.

## 6.7 Bilinen Veri Kalitesi Sorunları (İP2'ye Devredilenler)

İP1 sırasında şu kalite sorunları tespit edildi ve İP2'de çözülmek üzere not edildi:

- AKTS = 0 olan 57 kayıt (veri girişi hatası).
- Öğrenme kazanımı boş olan birkaç kayıt.
- Aynı dersin normal ve ikinci öğretim (İÖ) tekrarları — katalog kimliği üzerinden tekilleştirilmeli.
- Yapısı diğerlerinden farklı (bölüm/ders türü sütunları olmayan) 296 satırlık bir ek dosya — ana boru hattına dâhil edilmeden önce ayrıca değerlendirilmeli.

---

# 7. İŞ PAKETİ 2 — VERİ TEMİZLEME, İÖ TEKİLLEŞTİRME, MASTER TABLO

**Sorumlu:** Sudenaz Güven
**Durum:** Tamamlandı
**Girdi:** `data/raw/` (7 ham xlsx)
**Çıktı:** `data/processed/master_clean.xlsx` (4.133 satır, ~65 sütun)
**Kod:** `ip2-veri-temizleme/ip2_master_clean.py` + `notebooks/ip2_veri_temizleme.ipynb`

## 7.1 Neden Temizlik Şart? "Garbage In, Garbage Out"

Makine öğrenmesinin en temel ilkesi: model, kendisine verilen verinin kalitesi kadar iyidir. Kirli veri ile eğitilen bir model, o kiri öğrenir ve yanlış tahminler üretir. Bu yüzden İP2, tüm projenin en kritik temel taşıdır. Buradaki bir hata, sonraki tüm aşamalara yayılır.

İP2 dört ana adımdan oluşur: (1) yükleme ve birleştirme, (2) temizleme, (3) İÖ tekilleştirme, (4) öznitelik mühendisliği.

## 7.2 Adım 1 — Yükleme ve Birleştirme

Yedi ayrı fakülte dosyası tek tek pandas ile okundu. Her dosyaya, hangi fakülteden geldiğini belirten bir `fakulte` sütunu eklendi. Ardından hepsi `pd.concat()` ile tek bir DataFrame'de birleştirildi.

**Neden birleştirme gerekli?** Çünkü model tek bir tablo üzerinde eğitilir. Yedi ayrı dosya, yedi ayrı analiz demektir — bu hem verimsizdir hem de fakülteler arası karşılaştırmayı imkânsız kılar. Tek master tablo, tüm dersleri aynı çatı altında toplar.

Bu adımın sonunda: **5.807 satır, 76 sütun** (ham hâl).

## 7.3 Adım 2 — Temizleme (Üç Alt Adım)

### 7.3.1 AKTS = 0 Satırlarının Silinmesi

```python
onceki = len(df)
df = df[df["AKTSKredi"] != 0]
drop_akts = onceki - len(df)  # 57 satır
```

**Neden?** AKTS kredisi sıfır olan bir ders, mantıksal olarak imkânsızdır — her dersin bir iş yükü vardır. Bu kayıtlar kesinlikle veri girişi hatasıdır. Eğer bunları tutarsak, model "bazı dersler 0 AKTS alır" diye yanlış bir örüntü öğrenir. **57 satır silindi.**

### 7.3.2 Boş Öğrenme Kazanımı Satırlarının Silinmesi

```python
df["OgrenmeKazanim_1"] = df["OgrenmeKazanim_1"].astype(str).str.strip()
df = df[df["OgrenmeKazanim_1"].notna() &
        (df["OgrenmeKazanim_1"] != "") &
        (df["OgrenmeKazanim_1"] != "nan")]
```

**Neden?** İP3'te Bloom analizi tamamen öğrenme kazanımı metinlerine dayanır. Hiç kazanımı olmayan bir ders için Bloom düzeyi hesaplanamaz. Bu dersler analiz dışı kalmalıdır. **Yaklaşık 12 satır silindi.**

### 7.3.3 Etkinlik Metinlerinde Boşluk Temizliği

```python
for col in ETKINLIK_COLS:  # EtkinlikAd_1 ... EtkinlikAd_21
    df[col] = df[col].astype(str).str.strip().replace("nan", None)
```

**Neden?** EBS dışa aktarımında "  Laboratuvar  " gibi baştan/sondan boşluklu değerler gelir. Sonraki adımda etkinlik türlerini anahtar kelimeyle eşleştireceğiz (örneğin "laboratuvar" kelimesini arayacağız). Eğer boşlukları temizlemezsek, " Laboratuvar" ile "laboratuvar" farklı sayılır ve eşleşme kaçar. Bu yüzden `str.strip()` kritiktir.

## 7.4 Adım 3 — İkinci Öğretim (İÖ) Tekilleştirme

Bu, İP2'nin en teknik ve en önemli adımıdır.

### 7.4.1 Problem

EBS sisteminde, aynı ders hem Normal Öğretim hem de İkinci Öğretim (İÖ) programına ayrı ayrı kayıtlıdır. Örneğin:

```
Katalogid=201206, BolumAd="Bilgisayar Müh."        → Normal
Katalogid=201206, BolumAd="Bilgisayar Müh. (İÖ)"   → İkinci Öğretim
```

İkisi de **aynı içeriğe, aynı kazanımlara ve aynı etkinliklere** sahiptir. Yani bu bir **duplikasyondur (tekrar).** Eğer bu tekrarları tutarsak:

- Veri seti şişer (yapay olarak büyür).
- Model, aynı dersi iki kez görerek ona fazla ağırlık verir (bias).
- İstatistikler çarpıtılır.

### 7.4.2 Çözüm Kuralı

Uygulanan mantık şudur:

- Bir Katalogid için **hem Normal hem İÖ** kaydı varsa → **İÖ kaydını sil, Normal'i tut.**
- Bir Katalogid için **sadece İÖ** kaydı varsa → **koru** (o programın özgün İÖ dersidir).

```python
df["_is_io"] = df["BolumAd"].str.contains(r"\(İÖ\)", na=False)

# Hangi Katalogid'lerde normal öğretim var?
katalogid_normal = df.groupby("Katalogid")["_is_io"].apply(
    lambda x: (~x).any()
)

def keep_row(row):
    kid = row["Katalogid"]
    has_normal = katalogid_normal.get(kid, False)
    if row["_is_io"] and has_normal:
        return False  # Normal da var → İÖ'yü at
    return True

df = df[df.apply(keep_row, axis=1)].copy()
df.drop(columns=["_is_io"], inplace=True)
```

**Sonuç:** Yaklaşık **1.605 İÖ tekrar satırı silindi.**

### 7.4.3 Neden "(İÖ)" Etiketine Bakıyoruz?

İÖ dersleri, bölüm adında parantez içinde "(İÖ)" etiketiyle işaretlidir. Bu, onları Normal öğretimden ayırmanın en güvenilir yoludur. Katalog kimliği (Katalogid) ise aynı dersin farklı öğretim türlerini birbirine bağlayan anahtardır. Bu iki bilgiyi birleştirerek tekilleştirme yapılır.

## 7.5 Adım 4 — Öznitelik Mühendisliği (Feature Engineering)

Bu adımda, ham veriden **modelin işine yarayacak yeni sütunlar** türetilir. Bu, makine öğrenmesinin sanat kısmıdır — doğru öznitelikler modelin başarısını doğrudan belirler.

### 7.5.1 Öğrenme Kazanım Sayısı (n_ogrenme_kazanim)

```python
KAZANIM_COLS = [f"OgrenmeKazanim_{i}" for i in range(1, 26)]
df["n_ogrenme_kazanim"] = df[KAZANIM_COLS].apply(
    lambda row: sum(1 for v in row
                    if pd.notna(v) and str(v).strip() not in ("", "nan")),
    axis=1
)
```

Her ders için kaç dolu öğrenme kazanımı olduğunu sayar. Ortalama ~6 kazanım/ders. **Neden önemli?** Çünkü daha fazla kazanımı olan bir ders, genellikle daha kapsamlı ve daha yüklüdür. Bu, modelin kullanabileceği bir sinyaldir.

### 7.5.2 Birleşik Kazanım Metni (kazanim_concat)

```python
df["kazanim_concat"] = df[KAZANIM_COLS].apply(
    lambda row: " | ".join(str(v).strip() for v in row
                           if pd.notna(v) and str(v).strip() not in ("", "nan")),
    axis=1
)
```

Tüm kazanımları tek bir metinde birleştirir. **Neden?** İP3'teki Bloom NLP analizi, her dersin tüm kazanımlarını topluca işlemek için bu birleşik metni kullanır. Örnek çıktı: "Veri yapılarını açıklar | Algoritmaları analiz eder | ...".

### 7.5.3 Etkinlik Sayısı (n_etkinlik)

```python
ETKINLIK_COLS = [f"EtkinlikAd_{i}" for i in range(1, 22)]
df["n_etkinlik"] = df[ETKINLIK_COLS].apply(
    lambda row: sum(1 for v in row
                    if pd.notna(v) and str(v).strip() not in ("", "nan")),
    axis=1
)
```

Her ders için kaç farklı etkinlik türü olduğunu sayar. Ortalama ~4,4 etkinlik/ders. **Neden önemli?** Çeşitli etkinlikleri olan bir ders (ders + lab + proje + sunum), sadece teorik ders olandan yapısal olarak daha yüklüdür.

### 7.5.4 Etkinlik Varlık Bayrakları (has_* sütunları)

Bu, İP4'ün temelini oluşturan en kritik özniteliklerdir. Her etkinlik türü için bir 0/1 bayrağı üretilir:

```python
ETK_MAP = {
    "has_lab"           : ["laboratuvar"],
    "has_proje"         : ["proje"],
    "has_uygulama"      : ["uygulama"],
    "has_atolye"        : ["atölye", "atolye"],
    "has_odev"          : ["ödev", "odev"],
    "has_sinav"         : ["sınav", "sinav", "quiz"],
    "has_sunum"         : ["sunum", "seminer"],
}

def make_flags(row):
    combined = " ".join(str(v).lower() for v in row[ETKINLIK_COLS]
                        if pd.notna(v) and str(v).strip() not in ("", "nan"))
    return {flag: int(any(kw in combined for kw in kws))
            for flag, kws in ETK_MAP.items()}
```

**Mantık:** Bir dersin tüm etkinlik adları tek metinde birleştirilir, küçük harfe çevrilir, sonra her anahtar kelime aranır. "laboratuvar" kelimesi geçiyorsa `has_lab = 1`, geçmiyorsa `has_lab = 0`.

**Bu bayrakların İP4'teki rolü:** K_profil formülü tam olarak bu bayrakları kullanır. `has_lab`, `has_proje`, `has_uygulama` olan bir ders daha yüksek yapısal katsayı alır.

### 7.5.5 Alan Grubu Etiketi (alan_grubu)

```python
ALAN_GRUBU = {
    "Mühendislik"     : "STEM",
    "Teknoloji"       : "STEM",
    "Fen-Edebiyat"    : "Fen-Sosyal",
    "Eğitim"          : "Sosyal",
    "Siyasal Bilgiler": "Sosyal",
    "Güzel Sanatlar"  : "Sanat",
    "Spor Bilimleri"  : "Spor",
}
df["alan_grubu"] = df["fakulte"].map(ALAN_GRUBU)
```

Fakülteleri daha üst düzey disiplin gruplarına eşler. **Neden?** Çünkü fakülte çok spesifik olabilir, ama alan grubu daha genel bir örüntü yakalar. STEM dersleri (Mühendislik + Teknoloji) benzer yük profillerine sahiptir; bunları gruplamak modele yardımcı olur.

## 7.6 İP2 Sonuç Özeti

```
Girdi  : 5.807 satır (7 fakülte)
Çıktı  : 4.133 satır, ~65 sütun
Düşülen: 1.674 satır
  ├─ AKTS=0        : 57
  ├─ Boş kazanım   : ~12
  └─ İÖ tekrarı    : ~1.605

Fakülte dağılımı (temizlik sonrası):
  Mühendislik      : 1.090 (%26.4)
  Fen-Edebiyat     :   890 (%21.5)
  Güzel Sanatlar   :   710 (%17.2)
  Spor Bilimleri   :   431 (%10.4)
  Eğitim           :   366 (%8.9)
  Teknoloji        :   323 (%7.8)
  Siyasal Bilgiler :   323 (%7.8)

Etkinlik oranları:
  has_sinav    : %97.7  (neredeyse her derste sınav var)
  has_odev     : %17.5
  has_uygulama : %9.2
  has_sunum    : %7.5
  has_proje    : %7.3
  has_lab      : %3.4   (sadece lab dersleri)
```

**Bu istatistiklerin yorumu:** has_sinav %97.7 mantıklı — neredeyse her dersin bir sınavı vardır. has_lab %3.4 de mantıklı — sadece belirli mühendislik/fen dersleri laboratuvar içerir. Bu oranlar veri kalitesinin sağlıklı olduğunu doğrular.

---

# 8. İŞ PAKETİ 3 — BLOOM TAKSONOMİSİ VE BİLİŞSEL KATSAYI

**Sorumlu:** Sudenaz Güven
**Durum:** Tamamlandı
**Girdi:** `data/processed/master_clean.xlsx`
**Çıktı:** `data/processed/master_bloom.xlsx` (105 sütun)
**Kod:** `ip3-bloom-analizi/ip3_bloom_nlp.py` + `notebooks/ip3_bloom_analizi.ipynb`

## 8.1 Bloom Taksonomisi Nedir?

Bloom Taksonomisi (1956, revize 2001), öğrenme çıktılarını bilişsel derinliklerine göre altı hiyerarşik düzeye ayıran bir eğitim çerçevesidir. En alttan en üste:

1. **Hatırlama (Remember):** Bilgiyi hatırlamak, tanımak. (tanımlar, listeler, adlandırır)
2. **Anlama (Understand):** Anlamı kavramak, açıklamak. (açıklar, özetler, sınıflandırır)
3. **Uygulama (Apply):** Bilgiyi yeni durumlarda kullanmak. (uygular, hesaplar, çözer)
4. **Analiz (Analyze):** Parçalara ayırmak, ilişkileri görmek. (analiz eder, karşılaştırır)
5. **Değerlendirme (Evaluate):** Yargıda bulunmak, eleştirmek. (değerlendirir, yorumlar)
6. **Yaratma (Create):** Özgün bir şey üretmek. (tasarlar, geliştirir, oluşturur)

Bu hiyerarşi, projenin kalbindeki fikri temsil eder: **bilişsel olarak daha derin bir öğrenme çıktısı, daha fazla iş yükü gerektirir.** "Bir kavramı hatırlamak" ile "özgün bir sistem tasarlamak" arasındaki uçurum, kredi hesabında yansıtılmalıdır.

## 8.2 Neden Bloom'u Kullanıyoruz?

Projenin H4 hipotezi der ki: *"Üst düzey Bloom çıktısı (Analiz, Değerlendirme, Yaratma) içeren derslerin beklenen yükü, mevcut AKTS'nin öngördüğünden yüksektir."* Bu hipotezi test etmek için, her dersin öğrenme kazanımlarının Bloom düzeyini ölçmemiz gerekir. İşte İP3 tam olarak bunu yapar.

## 8.3 Metodoloji: Kural Tabanlı NLP (Fiil Eşleştirme)

İP3, her öğrenme kazanımını Bloom düzeyine sınıflandırmak için **kural tabanlı bir NLP yaklaşımı** kullanır. Yöntem şudur: her Bloom düzeyi için bir Türkçe fiil listesi tanımlanır, ve kazanım metninde bu fiiller aranır.

### 8.3.1 Fiil Sözlüğü

```python
BLOOM_VERBS = {
    6: ["tasarlar", "geliştirir", "oluşturur", "üretir", "planlar", "inşa eder"],
    5: ["değerlendirir", "yargılar", "savunur", "eleştirir", "karar verir"],
    4: ["analiz eder", "inceler", "test eder", "sorgular", "kıyaslar"],
    3: ["uygular", "hesaplar", "çözer", "kullanır", "gerçekleştirir"],
    2: ["açıklar", "özetler", "sınıflandırır", "yorumlar", "karşılaştırır"],
    1: ["tanımlar", "listeler", "adlandırır", "belirtir", "öğrenir"],
}
```

### 8.3.2 Sınıflandırma Mantığı (Greedy — En Yüksek Düzey Kazanır)

```python
def classify_kazanim(text: str) -> int:
    text_lower = str(text).lower()
    for level in range(6, 0, -1):          # L6'dan L1'e doğru tara
        for verb in BLOOM_VERBS[level]:
            if verb in text_lower:
                return level
    return 1  # Hiç eşleşme yoksa L1 (güvenli taban)
```

**Neden L6'dan L1'e doğru tarıyoruz?** Çünkü bir kazanımda birden fazla fiil olabilir. Örneğin "Kavramları açıklar ve özgün çözümler tasarlar" cümlesinde hem "açıklar" (L2) hem "tasarlar" (L6) var. Bu durumda en yüksek bilişsel düzeyi (L6) almak daha doğrudur, çünkü ders o düzeye çıkabiliyor demektir. Bu yüzden yüksekten başlayıp ilk eşleşmede dururuz.

### 8.3.3 Güvenli Taban Stratejisi (Safe Baseline)

E�er bir kazanımda hiçbir Bloom fiili eşleşmezse, ona L1 (Hatırlama) atanır. **Neden?** Çünkü:

1. Sınıflandırılamayan bir kazanımı tamamen atmak, o dersin veri kaybına yol açar.
2. En muhafazakâr (düşük) düzeyi atamak, bilişsel yükü abartmaktan kaçınır.
3. Bu, "en kötü ihtimalle bu ders temel düzeydedir" demektir — güvenli bir varsayım.

Bu strateji, projenin en önemli bulgularından birini de ortaya çıkardı (aşağıda 8.6'da).

## 8.4 Ders Bazlı İstatistik Üretimi

Her kazanım sınıflandırıldıktan sonra, ders düzeyinde özet istatistikler üretilir:

```python
def analyze_course_bloom(kazanim_texts: list) -> dict:
    levels = [classify_kazanim(t) for t in kazanim_texts if pd.notna(t)]
    total = len(levels)

    counts = {f"bloom_l{i}_count": levels.count(i) for i in range(1, 7)}
    ratios = {f"bloom_l{i}_ratio": levels.count(i)/total for i in range(1, 7)}

    avg_lvl = sum(levels) / total
    max_lvl = max(levels)
    dominant = max(range(1, 7), key=lambda i: levels.count(i))

    k_bil = 1 + ((avg_lvl - 1) / 5) * 0.50

    return counts | ratios | {
        "bloom_avg_level": round(avg_lvl, 3),
        "bloom_max_level": max_lvl,
        "bloom_dominant_level": dominant,
        "K_bilissel": round(k_bil, 4),
        "bloom_justification": f"Dominant: L{dominant} | Ort: {avg_lvl:.2f} | Maks: L{max_lvl} | K={k_bil:.4f}"
    }
```

Üretilen sütunlar:
- **bloom_l1_count ... bloom_l6_count:** Her düzeyde kaç kazanım var.
- **bloom_l1_ratio ... bloom_l6_ratio:** Her düzeyin oranı (0-1).
- **bloom_avg_level:** Ortalama Bloom düzeyi.
- **bloom_max_level:** En yüksek Bloom düzeyi.
- **bloom_dominant_level:** En sık görülen düzey.
- **K_bilissel:** Bilişsel katsayı (aşağıda açıklanıyor).
- **bloom_justification:** İnsan tarafından okunabilir gerekçe metni.

## 8.5 K_bilissel Formülü — Kalbin Formülü

```
K_bilissel = 1 + ((bloom_avg_level − 1) / 5) × 0.50
```

Bu formülü adım adım çözelim:

- **bloom_avg_level:** 1 ile 6 arasında bir değer (dersin ortalama Bloom düzeyi).
- **(bloom_avg_level − 1):** 0 ile 5 arasına normalize eder. L1'de 0, L6'da 5.
- **/ 5:** 0 ile 1 arasına ölçekler. L1'de 0.0, L6'da 1.0.
- **× 0.50:** Maksimum %50'lik bir artış tanımlar. L1'de 0, L6'da 0.50.
- **1 +:** Taban katsayıyı 1.0 yapar.

**Sonuç aralığı:**
- Tamamen L1 (Hatırlama) bir ders → K_bilissel = 1.00 (hiç artış yok)
- Tamamen L6 (Yaratma) bir ders → K_bilissel = 1.50 (maksimum %50 artış)

**Neden %50 tavan?** Çünkü bilişsel zorluk önemli bir faktördür ama tek faktör değildir. %50'lik bir düzeltme, bilişsel derinliği hesaba katarken modeli aşırı çarpıtmamak için dengeli bir seçimdir. Bu, kural tabanlı düzeltmelerin "düşük genlikli" (low-amplitude) olması ilkesine uygundur.

## 8.6 İP3 Sonuç Özeti ve KRİTİK BULGU

### 8.6.1 Bloom Dominant Düzey Dağılımı

```
L1 Hatırlama     : 2.810 ders (%68.0)
L2 Anlama        :   579 ders (%14.0)
L3 Uygulama      :   491 ders (%11.9)
L4 Analiz        :   112 ders (%2.7)
L6 Yaratma       :   107 ders (%2.6)
L5 Değerlendirme :    34 ders (%0.8)
```

### 8.6.2 Fakülte Bazlı Ortalama Bloom Düzeyi

```
En yüksek: Siyasal Bilgiler (2.651), Teknoloji (2.337), Mühendislik (2.036)
En düşük : Güzel Sanatlar (1.686), Fen-Edebiyat (1.864)
```

### 8.6.3 K_bilissel İstatistikleri

```
Min : 1.000
Max : 1.500
Ort : 1.098
Std : 0.095
```

### 8.6.4 EN ÖNEMLİ BULGU: %68 L1 Baskınlığı

Derslerin **%68'i L1 (Hatırlama) düzeyinde dominant.** Bu, projenin en güçlü empirik bulgularından biridir ve iki farklı şekilde yorumlanabilir:

**Yorum 1 (Metodolojik):** Kural tabanlı fiil eşleştirme, kazanımların %57.2'sini net olarak sınıflandıramadı (aşağıda kazanimlar_etiketli.csv analizi). Bunlar güvenli taban stratejisiyle L1'e atandı. Yani bu yüksek L1 oranının bir kısmı, EBS'deki kazanımların Bloom fiilleriyle yazılmamış olmasından kaynaklanır.

**Yorum 2 (Empirik/Politika):** Bu bulgunun kendisi bir sonuçtur! Türkiye'deki EBS sistemine girilen öğrenme kazanımlarının çok büyük bir kısmı Bloom taksonomisine uygun, ölçülebilir fiillerle yazılmamıştır. Bu, kalite güvence açısından önemli bir tespittir. Öğrenme kazanımları belirsizse, o dersin gerçekten ne öğrettiği de belirsizdir.

Her iki yorum da makale için değerlidir. Özellikle **Yorum 2, projenin H4 hipotezini ve genel tezini destekler:** statik sistem bilişsel derinliği görmezden gelir, çünkü sistemin kendisi (kazanım yazımı dahil) bilişsel düzeyi ciddiye almaz.

## 8.7 Ek Çıktı: kazanimlar_etiketli.csv

İP3 sırasında, ders düzeyinden daha granüler bir çıktı da üretildi: **kazanım düzeyinde etiketleme.**

```
Toplam kazanım    : 32.861
Güvenli etiket    : 14.050 (%42.8)  ← net Bloom fiili tespit edildi
Belirsiz          : 18.811 (%57.2)  ← fiil eşleşmedi, L1'e atandı
```

Bu **%57.2 belirsizlik oranı**, makalenin metodoloji ve bulgular bölümünde ayrı bir başlık hak eder. Bu dosya modelde kullanılmaz (sadece ders düzeyi özet master_bloom.xlsx'e girer), ama makaledeki "EBS kazanım kalitesi" tartışması için altın değerindedir.

---

# 9. ARA AŞAMA — ONE-HOT ENCODING VE MODEL VERİ SETİ

**Sorumlu:** Sudenaz Güven
**Durum:** Tamamlandı
**Girdi:** `master_bloom.xlsx`
**Çıktı:** `model_egitim.xlsx` (43 sütun, tamamen sayısal)

## 9.1 Neden One-Hot Encoding Gerekli?

Makine öğrenmesi modelleri **sadece sayı okur, metin okuyamaz.** Ama veri setimizde metinsel kategorik değişkenler var:

- `fakulte`: "Mühendislik", "Eğitim", ...
- `alan_grubu`: "STEM", "Sosyal", ...
- `derstur`: "Teorik", "Teori+Uygulama", ...

Bu metinleri modele veremeyiz. Onları sayısallaştırmamız gerekir. Ama nasıl?

## 9.2 Neden Label Encoding Değil, One-Hot?

Naif bir yaklaşım, her kategoriye bir sayı vermek olurdu (Label Encoding):

```
Mühendislik → 1, Eğitim → 2, Teknoloji → 3, ...
```

Ama bu **yanlıştır!** Çünkü model bu sayıları sıralı/büyüklük ilişkisi olarak yorumlar. "Teknoloji (3) > Eğitim (2)" gibi anlamsız bir hiyerarşi öğrenir. Oysa fakülteler arasında böyle bir sıralama yoktur — bunlar nominal (sırasız) kategorilerdir.

**One-Hot Encoding** bu sorunu çözer. Her kategori için ayrı bir binary (0/1) sütun oluşturur:

```
fakulte="Mühendislik" →  fakulte_Mühendislik=1, fakulte_Eğitim=0, fakulte_Teknoloji=0, ...
alan_grubu="STEM"     →  alan_grubu_STEM=1, alan_grubu_Sosyal=0, ...
derstur="Teorik"      →  derstur_Teorik=1, derstur_TeoriUygulama=0, ...
```

Böylece hiçbir yapay hiyerarşi oluşmaz; her kategori bağımsız bir sinyal olur.

## 9.3 Uygulama

```python
df_encoded = pd.get_dummies(df, columns=["fakulte", "alan_grubu", "derstur"],
                            prefix_sep="_")
```

**Sonuç:**
```
Önceki : 105 sütun (master_bloom)
Eklenen:  28 One-Hot sütun
  ├─ fakulte_*    →  7 sütun
  ├─ alan_grubu_* →  5 sütun
  └─ derstur_*    → 16 sütun
```

## 9.4 Model İçin Sütun Seçimi (model_egitim.xlsx)

130 sütunlu tam One-Hot tablosundan, sadece model için gerekli 43 sütun seçilerek `model_egitim.xlsx` oluşturuldu:

```
Referans   : Katalogid, DersAdi
Hedef (y)  : AKTSKredi
Sayısal    : n_ogrenme_kazanim, n_etkinlik
Bayraklar  : has_lab, has_proje, has_uygulama, has_atolye, has_odev, has_sinav, has_sunum
Bloom      : bloom_avg_level, bloom_max_level, K_bilissel
One-Hot    : fakulte_* (7) + alan_grubu_* (5) + derstur_* (16) = 28 sütun
```

Ayrıca tüm True/False değerleri 1/0'a çevrildi, böylece dosya tamamen sayısal hale geldi. Bu, Random Forest'ın direkt okuyabileceği temiz bir eğitim tablosudur.

---

# 10. İŞ PAKETİ 4 — YAPISAL GRUPLAMA KATSAYISI (K_profil, K_etkinlik)

**Sorumlu:** Samet Koca
**Durum:** Tamamlandı
**Girdi:** `data/processed/master_bloom.xlsx` (Sudenaz'ın İP3 çıktısı)
**Çıktı:** Aynı dosyaya `K_profil` ve `K_etkinlik` sütunları eklendi (107 sütun)
**Kod:** `ip4-yapisal-gruplama/src/ip4_yapisal_gruplama.py` + `notebooks/ip4_yapisal_gruplama.ipynb`

## 10.1 İP4'ün Projedeki Rolü

İP3 dersin **bilişsel** zorluğunu (K_bilissel) ölçtü. İP4 ise dersin **yapısal/etkinlik** yoğunluğunu ölçer. Bu ikisi birbirini tamamlar:

- **K_bilissel:** "Bu ders ne kadar derin düşünme gerektiriyor?" (Bloom'dan)
- **K_profil:** "Bu dersin ne kadar pratik/uygulamalı bileşeni var?" (etkinliklerden)
- **K_etkinlik:** "Bu ders emsallerine göre ne kadar çeşitli etkinliğe sahip?" (etkinlik sayısından)

Bu üç katsayı birlikte, bir dersin toplam yük profilini üç farklı boyutta tarif eder. İP5'te bunlar kural tabanlı AKTS hesabında çarpım halinde kullanılacak.

## 10.2 K_profil — Formül ve Gerekçe

```
K_profil = 1 + 0.10 × has_lab + 0.15 × has_proje + 0.05 × has_uygulama
```

### 10.2.1 Ağırlıkların Gerekçesi

Her etkinlik türüne verilen ağırlık, o etkinliğin tipik iş yükü katkısını yansıtır:

**Proje (0.15) — En yüksek ağırlık:** Proje, öğrencinin en fazla bağımsız çalışma yaptığı etkinliktir. Literatür taraması, tasarım, uygulama, test, raporlama ve sunum içerir. Genellikle haftalar süren, teslim edilebilir çıktısı olan bir yüktür. Bu yüzden en yüksek katsayıyı alır.

**Laboratuvar (0.10) — Orta ağırlık:** Laboratuvar, ön hazırlık (deney föyü okuma), deney yapma, veri toplama ve rapor yazma gerektirir. Proje kadar açık uçlu değildir ama teorik dersten belirgin şekilde daha yüklüdür.

**Uygulama (0.05) — Düşük ek ağırlık:** Uygulama, genellikle ders içi veya ders bitişiğinde yapılan pratik çalışmadır. Ek yük getirir ama lab veya proje kadar ağır değildir.

### 10.2.2 Aralık Analizi

```
Minimum: 1.00  → sadece teorik ders (lab yok, proje yok, uygulama yok)
Maksimum: 1.30 → üçü de var (1 + 0.10 + 0.15 + 0.05)
```

Bu, maksimum %30'luk bir yapısal artış tanımlar. K_bilissel'in %50 tavanıyla birlikte düşünüldüğünde, kural tabanlı düzeltmelerin toplam etkisi kontrollü ve açıklanabilir kalır.

### 10.2.3 Neden Toplamsal (Additive), Çarpımsal Değil?

K_profil içinde etkinlikler toplanır (0.10 + 0.15 + 0.05), çarpılmaz. **Neden?** Çünkü bir dersin hem lab'ı hem projesi olması, yükün katlanarak artması değil, doğrusal olarak birikmesi demektir. Toplamsal model, "her ek etkinlik türü sabit bir yük ekler" varsayımına dayanır ki bu, elimizdeki varlık (0/1) verisiyle en savunulabilir yaklaşımdır. Çarpımsal bir model, saat verisi olmadan aşırı varsayımsal olurdu.

## 10.3 K_etkinlik — Formül ve Gerekçe

```
K_etkinlik = 1 + 0.03 × (n_etkinlik − ortalama_n_etkinlik)
```

### 10.3.1 Mantık: Ortalamadan Sapma

Bu formül, bir dersin etkinlik sayısının **veri setinin ortalamasından ne kadar saptığını** ölçer:

- Ortalama etkinlik sayısına sahip ders → K_etkinlik = 1.00 (nötr)
- Ortalamadan fazla etkinliği olan ders → K_etkinlik > 1.00 (yük artışı)
- Ortalamadan az etkinliği olan ders → K_etkinlik < 1.00 (yük azalışı)

Veri setinde ortalama n_etkinlik = 4.38 çıktı. Yani 4-5 etkinliği olan bir ders nötr sayılır; 8 etkinliği olan ders yük artışı, 2 etkinliği olan ders yük azalışı alır.

### 10.3.2 Neden 0.03 Katsayısı?

0.03, her ek etkinliğin %3'lük bir düzeltme getirmesini sağlar. Bu düşük genlikli bir değerdir — kasıtlı olarak. Amaç, etkinlik sayısındaki farkları hesaba katmak ama modeli aşırı çarpıtmamak. Örneğin ortalamadan 5 etkinlik fazla olan bir ders, sadece %15 yük artışı alır (5 × 0.03). Bu makul bir düzeltmedir.

### 10.3.3 Neden Bu Katsayı 1'den Küçük Olabilir?

K_profil her zaman ≥ 1.00'dir (çünkü bayraklar 0 veya pozitif). Ama K_etkinlik, ortalamanın altındaki dersler için 1'den küçük olabilir. Bu **kasıtlıdır** — çok az etkinliği olan bir ders (örneğin sadece ders + sınav), emsallerinden daha hafif olabilir ve bu, kredisine yansımalıdır. Yani K_etkinlik hem yukarı hem aşağı düzeltme yapabilen simetrik bir katsayıdır.

## 10.4 Uygulama Kodu

```python
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
IN_PATH = BASE / "data" / "processed" / "master_bloom.xlsx"

df = pd.read_excel(IN_PATH, dtype={"Katalogid": str})

# K_profil
df["K_profil"] = (
    1 + 0.10 * df["has_lab"]
      + 0.15 * df["has_proje"]
      + 0.05 * df["has_uygulama"]
).round(4)

# K_etkinlik
ort_etkinlik = df["n_etkinlik"].mean()
df["K_etkinlik"] = (
    1 + 0.03 * (df["n_etkinlik"] - ort_etkinlik)
).round(4)

df.to_excel(IN_PATH, index=False)
```

**Not (uygulama sırasında çıkan düzeltme):** Kodda başlangıçta `df.groupby("fakulte")` yazılmıştı, ama master_bloom.xlsx'te sütun adı büyük F ile `Fakulte`. Bu düzeltildi. Bu, veri sözlüğünün (data dictionary) neden önemli olduğunu gösteren küçük ama öğretici bir örnektir.

## 10.5 İP4 Sonuç Özeti

### 10.5.1 K_profil İstatistikleri

```
Min : 1.00
Max : 1.30
Ort : 1.019
Yüksek yoğunluk (K_profil > 1.20): 25 ders
```

### 10.5.2 K_etkinlik İstatistikleri

```
Min : 0.87
Max : 1.17
Ort : 1.00  (formül gereği ortalamada tam 1.00)
Ortalama n_etkinlik: 4.38
```

### 10.5.3 Fakülte Bazlı K_profil Sıralaması

```
Teknoloji       : 1.038  ← en yüksek
Mühendislik     : 1.032
Spor Bilimleri  : 1.018
Güzel Sanatlar  : 1.017
E�itim          : 1.012
Fen-Edebiyat    : 1.008
Siyasal Bilgiler: 1.002  ← en düşük
```

## 10.6 İP4 Bulgularının Yorumu ve Hipoteze Bağlanması

Bu sıralama **son derece anlamlıdır** ve H1 hipotezini destekler:

- **Teknoloji ve Mühendislik en yüksek K_profil'e sahip.** Bu beklenen bir sonuç — bu fakülteler laboratuvar ve proje yoğun mühendislik disiplinlerini barındırır. Yapısal olarak en fazla pratik bileşene sahiptirler.

- **Siyasal Bilgiler en düşük.** Yine beklenen — sosyal bilimler çoğunlukla teorik derslerden oluşur, laboratuvar veya proje nadir.

Bu, K_profil'in gerçekten anlamlı bir sinyal yakaladığını doğrular. Eğer sıralama rastgele olsaydı veya sosyal bilimler mühendislikten yüksek çıksaydı, formülde bir sorun olduğunu düşünürdük. Ama sonuç, alan bilgisiyle (domain knowledge) tam uyumlu.

**H1 bağlantısı:** H1 der ki "statik motor laboratuvar ve proje yoğun derslerde sistematik olarak düşük kredi eğilimindedir." K_profil, tam olarak bu lab/proje yoğunluğunu ölçen katsayıdır. İP5'te kural_akts hesabında kullanıldığında, yüksek K_profil'li dersler daha yüksek adaptif AKTS alacak — ve bunların mevcut AKTS'den ne kadar saptığı, H1'i doğrudan test edecek.

## 10.7 K_profil Ortalamasının Düşük Olması Ne Anlama Geliyor?

K_profil ortalaması 1.019 — yani çoğu ders 1.00'a yakın. Bu, veri setinde **teorik derslerin baskın olduğunu** gösterir. Sadece 25 ders yüksek yoğunluklu (K_profil > 1.20). Bu, has_lab oranının %3.4 olmasıyla tutarlıdır. Yani veri seti, az sayıda çok yoğun ders ve çok sayıda teorik dersten oluşur. Bu dağılım, adaptif modelin işini ilginç kılar: az sayıdaki yoğun dersleri doğru işaretleyebilmesi kritiktir.

---

# 11. ŞU ANA KADAR ÜRETİLEN TÜM KATSAYILARIN SENTEZİ

Bu noktada, üç bağımsız katsayımız var. Bunların nasıl birleşeceğini net görmek önemli.

## 11.1 Üç Katsayı, Üç Boyut

| Katsayı | Neyi Ölçer | Kaynak | Aralık | Ortalama |
|---------|-----------|--------|--------|----------|
| **K_bilissel** | Bilişsel zorluk | Bloom düzeyi (İP3) | 1.00–1.50 | 1.098 |
| **K_profil** | Yapısal yoğunluk | Etkinlik bayrakları (İP4) | 1.00–1.30 | 1.019 |
| **K_etkinlik** | Etkinlik çeşitliliği | Etkinlik sayısı (İP4) | 0.87–1.17 | 1.000 |

## 11.2 Bu Katsayılar İP5'te Nasıl Birleşecek?

İP5'te kural tabanlı AKTS şöyle hesaplanacak:

```
kural_akts = akts_mevcut × K_etkinlik × K_profil × K_bilissel
```

Örnek hesap — yüksek yoğunluklu bir mühendislik dersi:
```
akts_mevcut = 5
K_etkinlik  = 1.09  (ortalamadan fazla etkinlik)
K_profil    = 1.30  (lab + proje + uygulama)
K_bilissel  = 1.23  (üst düzey Bloom)

kural_akts = 5 × 1.09 × 1.30 × 1.23 = 8.72
```

Bu ders, mevcut 5 AKTS yerine kural tabanlı hesapta 8.72 "hak ediyor" görünüyor. Bu büyük bir sapma — muhtemelen "AKTS düşük olabilir, incelenmeli" uyarısı alacak.

Örnek hesap — teorik bir sosyal bilim dersi:
```
akts_mevcut = 3
K_etkinlik  = 1.00  (ortalama etkinlik)
K_profil    = 1.00  (sadece teorik)
K_bilissel  = 1.10  (L2 Anlama düzeyi)

kural_akts = 3 × 1.00 × 1.00 × 1.10 = 3.30
```

Bu ders, mevcut 3 AKTS'ye çok yakın (3.30) — muhtemelen "güçlü uyum" kararı alacak.

## 11.3 Neden Çarpımsal Birleşim?

Katsayılar birbiriyle **çarpılır**, toplanmaz. Neden? Çünkü bu katsayılar **bağımsız düzeltme faktörleridir.** Her biri mevcut AKTS'yi belirli bir oranda ölçekler. Çarpımsal model, "bilişsel zorluk %23 artırıyor VE yapısal yoğunluk %30 artırıyor" gibi etkilerin birleşik çarpan etkisini doğru yansıtır. Toplamsal olsaydı, bu bileşik etki kaybolurdu.

---

# 12. VERİ SETİNİN ANATOMİSİ: SÜTUN SÜTUN AÇIKLAMA

Bu bölüm, `master_bloom.xlsx` (107 sütun) içindeki tüm önemli sütunların ne olduğunu, hangi iş paketinde üretildiğini ve ne işe yaradığını belgeler. Bu, bir "veri sözlüğü" (data dictionary) görevi görür ve İP5'e devirde referans olarak kullanılmalıdır.

## 12.1 Kimlik ve Bağlam Sütunları (İP1'den gelir)

| Sütun | Tip | Açıklama |
|-------|-----|----------|
| Katalogid | metin | Dersin benzersiz katalog kimliği. İÖ tekilleştirmede anahtar. |
| DersAdi | metin | Dersin adı. |
| turid | sayı | Ders tür kimliği. |
| derstur | metin | Ders türü (Teorik, Teori+Uygulama, Laboratuvar vb.) |
| Bolumid | sayı | Bölüm kimliği. |
| BolumAd | metin | Bölüm adı. İÖ tespitinde "(İÖ)" etiketi burada aranır. |
| Fakulte | metin | Fakülte adı (7 fakülteden biri). |
| EgitimYili | sayı | Eğitim-öğretim yılı. |
| AKTSKredi | sayı | **HEDEF DEĞİŞKEN (y).** Mevcut AKTS kredisi. |

## 12.2 Temizlik ve Öznitelik Sütunları (İP2'de üretildi)

| Sütun | Tip | Açıklama |
|-------|-----|----------|
| fakulte | metin | Standartlaştırılmış fakülte adı. |
| alan_grubu | metin | STEM / Sosyal / Fen-Sosyal / Sanat / Spor. |
| n_ogrenme_kazanim | sayı | Dolu öğrenme kazanımı sayısı (0-25). |
| kazanim_concat | metin | Tüm kazanımların birleşik metni (Bloom NLP girdisi). |
| n_etkinlik | sayı | Dolu etkinlik sayısı (0-21). |
| has_lab | 0/1 | Laboratuvar var mı. |
| has_proje | 0/1 | Proje var mı. |
| has_uygulama | 0/1 | Uygulama var mı. |
| has_atolye | 0/1 | Atölye var mı. |
| has_odev | 0/1 | Ödev var mı. |
| has_sinav | 0/1 | Sınav/quiz var mı. |
| has_sunum | 0/1 | Sunum/seminer var mı. |

## 12.3 Bloom Sütunları (İP3'te üretildi)

| Sütun | Tip | Açıklama |
|-------|-----|----------|
| bloom_l1_count ... bloom_l6_count | sayı | Her Bloom düzeyindeki kazanım sayısı. |
| bloom_l1_ratio ... bloom_l6_ratio | ondalık | Her düzeyin oranı (0-1). |
| bloom_avg_level | ondalık | Ortalama Bloom düzeyi (1-6). |
| bloom_max_level | sayı | En yüksek Bloom düzeyi. |
| bloom_dominant_level | sayı | En sık görülen düzey. |
| K_bilissel | ondalık | Bilişsel katsayı (1.00-1.50). |
| bloom_justification | metin | İnsan-okunabilir gerekçe. |

## 12.4 Yapısal Katsayı Sütunları (İP4'te üretildi)

| Sütun | Tip | Açıklama |
|-------|-----|----------|
| K_profil | ondalık | Yapısal yoğunluk katsayısı (1.00-1.30). |
| K_etkinlik | ondalık | Etkinlik çeşitliliği katsayısı (0.87-1.17). |

## 12.5 Sütun Sayısı Muhasebesi

```
İP1 sonrası (ham)      : 76 sütun
İP2 sonrası (temiz)    : ~65 sütun (bazı ham sütunlar sadeleşti + öznitelikler eklendi)
İP3 sonrası (bloom)    : 105 sütun (+ 40 bloom/kazanım sütunu)
İP4 sonrası (yapısal)  : 107 sütun (+ K_profil, K_etkinlik)
```

Not: model_egitim.xlsx ise bunun One-Hot uygulanmış ve sadece 43 model sütununa indirgenmiş versiyonudur.

---

# 13. KRİTİK BULGULAR VE BUNLARIN MAKALEYE YANSIMASI

İP1-4 boyunca ortaya çıkan, makalede kullanılacak temel bulguları burada topluyoruz.

## 13.1 Bulgu 1 — Veri Gerçeği: Saat Verisi Yok

EBS dışa aktarımında etkinlik saat verisi bulunmuyor. Bu, metodolojiyi "saat × katsayı" modelinden "varlık öznitelikleri" modeline yönlendirdi. **Makaledeki yeri:** Metodoloji bölümünde dürüst bir kısıt (limitation) olarak belirtilmeli; aynı zamanda gelecek çalışma önerisi (anket ile saat verisi toplama) olarak sunulmalı.

## 13.2 Bulgu 2 — %57.2 Kazanım Belirsizliği

Öğrenme kazanımlarının %57.2'si Bloom fiilleriyle net sınıflandırılamadı. **Makaledeki yeri:** Hem bir metodolojik kısıt, hem de bağımsız bir bulgu. "EBS kazanım yazım kalitesi düşük" tespiti, kalite güvence açısından politika önerisi doğurur.

## 13.3 Bulgu 3 — %68 L1 Baskınlığı

Derslerin %68'i Hatırlama düzeyinde dominant. **Makaledeki yeri:** H4 hipotezinin bağlamını kurar. Sistemin bilişsel derinliği ciddiye almadığının göstergesi. Fakülteler arası Bloom farkı (Siyasal Bilgiler > Güzel Sanatlar) da ilginç bir alt bulgu.

## 13.4 Bulgu 4 — K_profil Fakülte Sıralaması H1'i Destekliyor

Teknoloji ve Mühendislik en yüksek yapısal yoğunluğa sahip. **Makaledeki yeri:** H1'in ("lab/proje yoğun dersler sistematik düşük kredi") ön kanıtı. İP5'te bu derslerin sapması hesaplanınca H1 doğrudan test edilecek.

## 13.5 Bulgu 5 — İÖ Duplikasyonu (1.605 satır)

Ham verinin ~%28'i ikinci öğretim tekrarıydı. **Makaledeki yeri:** Veri temizleme metodolojisinin titizliğini gösterir. Aynı zamanda EBS veri yapısının bir özelliği olarak not edilebilir.

## 13.6 Bulguların Hipotezlerle Eşleşme Matrisi

| Hipotez | İlgili Bulgu | Durum |
|---------|-------------|-------|
| H1 (lab/proje düşük kredi) | Bulgu 4 (K_profil sıralaması) | Ön kanıt hazır, İP5'te test edilecek |
| H2 (bölümler arası sapma) | — | İP6'da ayrı analiz gerekli |
| H3 (adaptif model üstünlüğü) | — | İP5 çıktısıyla test edilecek |
| H4 (üst Bloom yüksek yük) | Bulgu 3 (%68 L1), K_bilissel | Altyapı hazır, İP5'te test edilecek |

---

# 14. İP5'E DEVİR: NE HAZIR, NE EKSİK?

## 14.1 İP5 İçin Hazır Olan Dosyalar

**master_bloom.xlsx (107 sütun):** K_bilissel, K_profil, K_etkinlik hepsi içinde. Kural tabanlı AKTS hesabı için gereken her şey burada.

**model_egitim.xlsx (43 sütun):** One-Hot uygulanmış, tamamen sayısal. Random Forest'ın X (özellikler) ve y (AKTSKredi) olarak direkt kullanabileceği eğitim tablosu.

## 14.2 İP5'in Yapması Gerekenler (Pipeline Aşama 8-11)

**Aşama 8 — Random Forest Eğitimi:** model_egitim.xlsx üzerinde bir RF regresör eğitilir. X = tüm öznitelikler (AKTSKredi hariç), y = AKTSKredi. Model, "bu özelliklere sahip dersler genellikle kaç AKTS alır" örüntüsünü öğrenir.

**Aşama 9 — RF Tahmini:** Eğitilen model her derse uygulanır, rf_tahmin_akts üretilir.

**Aşama 10 — Kural Tabanlı AKTS:** kural_akts = akts_mevcut × K_etkinlik × K_profil × K_bilissel hesaplanır (katsayılar İP4'ten hazır).

**Aşama 11 — Adaptif AKTS:** adaptif_akts = 0.70 × rf_tahmin_akts + 0.30 × kural_akts.

## 14.3 İP5 İçin Netleştirilmesi Gereken Kararlar

Aşağıdaki noktalar İP5'e başlamadan karara bağlanmalı (bir sonraki bölümde tartışılıyor):

1. Random Forest hiperparametreleri (ağaç sayısı, derinlik).
2. Train/test bölünmesi stratejisi (fakülteye göre stratified mi?).
3. Model başarı metriği (MAE, RMSE, R²).
4. rf_tahmin ile kural_akts ağırlıkları (0.70/0.30 sabit mi, denenecek mi?).
5. Aşırı öğrenme (overfitting) kontrolü.

## 14.4 Önemli Uyarı: Hedef Sızıntısı (Target Leakage) Riski

Dikkat edilmesi gereken kritik bir nokta var. Random Forest'ın hedefi (y) AKTSKredi'dir. Ama kural_akts formülü de akts_mevcut (yani AKTSKredi) içerir. Eğer dikkatli olunmazsa, model dolaylı olarak cevabı "görebilir." İP5'te bu ayrım net tutulmalı: RF sadece ders özelliklerinden tahmin yapmalı, akts_mevcut'ı bir özellik olarak KULLANMAMALI. akts_mevcut sadece kural_akts formülünde ve sapma hesabında kullanılmalı.

---

# 15. İP5 BEYİN FIRTINASI: KARŞIMIZDAKİ KARARLAR

Bu bölüm, İP5'e geçmeden önce ekip olarak tartışmamız gereken açık soruları ve olası yaklaşımları listeler.

## 15.1 Karar 1 — Random Forest Nasıl Kurulmalı?

**Soru:** Kaç ağaç, ne derinlik, hangi parametreler?

**Öneri:** Başlangıç için makul varsayılanlar (n_estimators=200, max_depth=None, random_state=42). Sonra çapraz doğrulama (cross-validation) ile ayarlama. Veri seti 4.133 satır — küçük değil ama devasa da değil, bu yüzden RF ideal (aşırı öğrenmeye karşı dayanıklı).

**Tartışma noktası:** Fakülteler arası dağılım dengesiz (Mühendislik %26, Siyasal %8). Train/test bölünmesi fakülteye göre stratified yapılmalı mı? Bence evet — her fakülte hem eğitimde hem testte temsil edilmeli.

## 15.2 Karar 2 — Hangi Özellikler Modele Girmeli?

**Soru:** 43 sütunun hepsi mi, yoksa seçilmiş bir alt küme mi?

**Öneri:** İlk turda hepsi girsin, sonra feature importance'a bakıp gereksizleri ayıklayalım. Ama **akts_mevcut kesinlikle girmemeli** (hedef sızıntısı riski — bkz. 14.4).

**Tartışma noktası:** K_bilissel, K_profil, K_etkinlik modele özellik olarak girmeli mi, yoksa sadece kural_akts'ta mı kullanılmalı? İki seçenek var:
- (a) Katsayıları RF'e de ver → model onları da öğrensin.
- (b) Katsayıları sadece kural tarafında tut → RF ve kural birbirinden bağımsız kalsın.
Seçenek (b) daha temiz bir hibrit yapı sunar (iki bileşen gerçekten bağımsız olur). Bence (b) tercih edilmeli.

## 15.3 Karar 3 — Adaptif Ağırlıklar (0.70 / 0.30) Sabit mi?

**Soru:** adaptif_akts = 0.70 × rf + 0.30 × kural. Bu ağırlıklar nereden geldi?

**Öneri:** Şu an bunlar teorik/sezgisel değerler. Makale için bunları savunmak gerekir. İki yol var:
- (a) Sabit tut, "RF ana bileşen olduğu için ağırlığı yüksek" diye gerekçelendir.
- (b) Duyarlılık analizi (sensitivity analysis) yap — 0.5/0.5, 0.6/0.4, 0.8/0.2 dene, sonuçların nasıl değiştiğini göster.
Seçenek (b) akademik olarak daha güçlü ama daha çok iş. En azından birkaç ağırlık denenip raporlanmalı.

## 15.4 Karar 4 — Sapma Eşikleri Ne Olmalı?

**Soru:** sapma = adaptif_akts − akts_mevcut. Hangi sapma "işaretlenecek" kadar büyük?

**Öneri:** Eşikler kararı doğrudan etkiler. Örnek bir şema:
- |sapma| < 0.5 → "Güçlü uyum" (yeşil)
- 0.5 ≤ |sapma| < 1.5 → "Kabul edilebilir" (sarı)
- |sapma| ≥ 1.5 → "İncelenmeli" (kırmızı)
Bu eşikler veri dağılımına bakılarak (sapmaların yüzdelik dilimlerine göre) ayarlanmalı. Belki mutlak eşik yerine yüzdesel eşik (örneğin %30 sapma) daha adil olur.

## 15.5 Karar 5 — Model Başarısını Nasıl Ölçeceğiz?

**Soru:** RF ne kadar iyi tahmin ediyor, nasıl bileceğiz?

**Öneri:** Regresyon metrikleri:
- MAE (Mean Absolute Error): Ortalama kaç AKTS yanılıyoruz.
- RMSE: Büyük hataları cezalandıran metrik.
- R²: Modelin varyansın ne kadarını açıkladığı.
Ama dikkat: yüksek R² her zaman iyi değil! Çünkü amacımız mevcut AKTS'yi mükemmel taklit etmek değil, ondan anlamlı sapmaları yakalamak. Model çok iyi taklit ederse, hiç sapma bulamayız. Bu paradoksu makalede tartışmalıyız.

## 15.6 Karar 6 — Açıklanabilirlik (XAI) Nasıl Sunulacak?

**Soru:** Modelin kararlarını nasıl savunulabilir kılacağız?

**Öneri:** Random Forest feature_importances_ ile hangi özelliklerin tahminleri en çok etkilediğini gösterebiliriz. Beklenen baskın özellikler: n_etkinlik, has_proje, has_lab, K_bilissel, fakülte/alan bağlamı. Ayrıca birkaç örnek ders için "bu ders neden bu adaptif değeri aldı" şeklinde vaka analizi (case study) sunulabilir. Bu, makalenin XAI iddiasını somutlaştırır.

## 15.7 Özet: İP5 Öncesi Karar Tablosu

| # | Karar | Önerilen Yaklaşım |
|---|-------|-------------------|
| 1 | RF hiperparametreleri | Varsayılan + CV ayarı, stratified split |
| 2 | Özellik seçimi | Hepsi (akts_mevcut HARİÇ), katsayılar kural tarafında |
| 3 | Adaptif ağırlıklar | Birkaç ağırlık denenip raporlansın |
| 4 | Sapma eşikleri | Yüzdelik dilimlere göre ayarla |
| 5 | Başarı metriği | MAE + RMSE + R², "iyi taklit paradoksu"nu tartış |
| 6 | XAI | feature_importance + örnek vaka analizleri |

---

# 16. EKLER

## 16.1 Formül Kütüphanesi (Tek Sayfa Özet)

```
── BİLİŞSEL KATSAYI (İP3) ──────────────────────────────
K_bilissel = 1 + ((bloom_avg_level − 1) / 5) × 0.50
Aralık: [1.00, 1.50]

── YAPISAL KATSAYILAR (İP4) ────────────────────────────
K_profil = 1 + 0.10×has_lab + 0.15×has_proje + 0.05×has_uygulama
Aralık: [1.00, 1.30]

K_etkinlik = 1 + 0.03 × (n_etkinlik − ort_n_etkinlik)
Aralık: [0.87, 1.17], ortalama = 1.00

── KURAL TABANLI AKTS (İP5'te hesaplanacak) ────────────
kural_akts = akts_mevcut × K_etkinlik × K_profil × K_bilissel

── ADAPTİF AKTS (İP5'te hesaplanacak) ──────────────────
adaptif_akts = 0.70 × rf_tahmin_akts + 0.30 × kural_akts

── SAPMA (İP6'da hesaplanacak) ─────────────────────────
sapma = adaptif_akts − akts_mevcut
```

## 16.2 Dosya ve Klasör Haritası

```
course-credits-system/
├── ip1-ham-veri/              ← 7 fakülte ham xlsx (arşiv)
├── ip2-veri-temizleme/
│   ├── ip2_master_clean.py
│   └── notebooks/ip2_veri_temizleme.ipynb
├── ip3-bloom-analizi/
│   ├── ip3_bloom_nlp.py
│   └── notebooks/
│       ├── ip3_bloom_analizi.ipynb
│       └── bloom_duzey_tablo.ipynb
├── ip4-yapisal-gruplama/      ← Samet'in çalışma alanı
│   ├── src/ip4_yapisal_gruplama.py
│   └── notebooks/ip4_yapisal_gruplama.ipynb
├── ip5-random-forest/         ← Mevlüt için hazır (boş)
│   ├── src/
│   └── notebooks/
├── ip6-validasyon/            ← boş
├── data/
│   ├── raw/                   ← 7 fakülte xlsx (çalışma kopyası)
│   └── processed/
│       ├── master_clean.xlsx/csv     ← İP2 çıktısı (4.133 satır)
│       ├── master_bloom.xlsx/csv     ← İP3+İP4 çıktısı (107 sütun) ★
│       ├── model_egitim.xlsx         ← One-Hot (43 sütun) → Mevlüt ★
│       ├── kazanimlar_etiketli.csv   ← makale için (%57.2 bulgusu)
│       └── bloom_duzey_tablo.xlsx    ← gerekçeli Bloom tablosu
├── docs/
│   └── PROJE_DOKUMANTASYON.md
└── requirements.txt

★ = İP5 için kritik girdi dosyaları
```

## 16.3 İş Paketi Sorumluluk Özeti

| İP | Görev | Sorumlu | Durum |
|----|-------|---------|-------|
| 1 | Ham veri toplama (EBS) | Ayhan Gültekin | ✅ Bitti |
| 2 | Temizlik + İÖ + master tablo | Sudenaz Güven | ✅ Bitti |
| 3 | Bloom NLP + K_bilissel | Sudenaz Güven | ✅ Bitti |
| 4 | Yapısal gruplama (K_profil) | Samet Koca | ✅ Bitti |
| 5 | Random Forest + Adaptif AKTS | Mevlüt Alp Kılınç | ⏳ Sıradaki |
| 6 | Tutarsızlık + validasyon | Sudenaz + Mevlüt | ⏳ Bekliyor |
| 7 | Tam metin | Tüm Ekip | ⏳ Bekliyor |
| 8 | Revizyon + gönderim | Tüm Ekip | ⏳ Bekliyor |
| 9 | Sunum | Mevlüt Alp Kılınç | ⏳ Eylül |

## 16.4 Kullanılan Teknolojiler

```
Dil        : Python 3.12
Kütüphaneler: pandas (veri işleme), numpy (sayısal),
             openpyxl (xlsx), scikit-learn (İP5'te RF)
Ortam      : VS Code + Claude CLI
Veri formatı: xlsx (Excel) + csv (yedek)
Notebook   : Jupyter (.ipynb)
```

---

# SONUÇ

İş Paketi 1'den 4'e kadar olan süreçte, projenin veri hazırlama ve öznitelik mühendisliği omurgası eksiksiz kuruldu. 5.807 ham kayıttan başlayıp, temizlenmiş, zenginleştirilmiş, üç farklı katsayıyla (bilişsel, yapısal, etkinlik) donatılmış 4.133 satırlık bir master veri setine ulaştık.

Elimizde şimdi, her dersin bağlamını, bilişsel derinliğini ve yapısal yoğunluğunu sayısal olarak tarif eden zengin bir tablo var. İP5'te bu tablo, mevcut AKTS örüntüsünü öğrenecek bir Random Forest modeliyle buluşacak ve nihai adaptif AKTS değerlerini üretecek.

Bu rapor, hem yapılan işin teknik kaydı, hem İP5 öncesi bir karar rehberi, hem de makale yazımı için bir kaynak belge olarak hazırlandı. İP5'e sağlam bir zeminde giriyoruz.

**Bir sonraki adım:** Bölüm 15'teki altı kararı ekipçe netleştirip, Random Forest modelini kurmaya başlamak.

---

*Rapor sonu. Toplam kapsam: İş Paketi 1-4, tüm formüller, tüm bulgular, İP5 yol haritası.*