# Tahminler (4a)

> **Kural:** Her deney için iki cümle. Bu dosya deneyler çalıştırılmadan **önce** ayrı bir commit olarak yüklenir
> (`git commit -m "Tahminler (4a) — deneylerden önce"`). Tahmini olmayan deney puanlanmaz.
> Commit atıldıktan sonra bu dosya **değiştirilmez**; yanlış çıkan tahmin bireysel notta tartışılır.
>
> Yazarken: ölçülebilir bir şey söyleyin (hangi ölçü, hangi yönde, hangi görüntüde) ve nedenini bir cümleyle verin.
> Örnek biçim: *"Turuncu koni bulunan K-5'te renk maskesi koniyi de seçecek ve kural 'Yelek var, giyili değil' diyecek.
> Çünkü HSV aralığı yalnız rengi sınar, giysi biçimini ya da şeridi sınamaz."*

Sunum adı: **klasik yöntemler** — hazır dedektör (isteğe bağlı adım) yapılmıyor, tahmini de yok.

---

## 5. adım — Renk kuralı · B (Paket B Sorumlusu)
- Tahmin: Turuncu koni içeren K-5 ve sarı iş makinesi içeren G-4 görüntülerinde renk maskesi giysi dışı nesneleri de seçecek ve karar kuralı gövdeyle örtüşmeyen bu büyük parçalar nedeniyle hatalı biçimde "Yelek var, giyili değil" sınıfını üretecektir.
- Gerekçe: Çünkü dondurulan HSV renk aralıkları ve morfolojik bağlı bileşen analizi yalnızca piksel renk tonunu sınar; nesnenin dokusunu, giysi geometrisini veya şerit varlığını ayırt edemez.

## 6a — Kenar (Sobel, Canny) · C (Paket C Sorumlusu)
- Tahmin: G-1'deki yelekli işçinin gövdesinde yatay şeritlerden ötürü dikey gradyan toplamı yatay gradyandan belirgin derecede büyük çıkacak ($\Sigma|G_y| / \Sigma|G_x| > 1.2$), düz tişörtlü G-5'te ise bu oran 1.0 civarında kalıp Canny kenar yoğunluğu çok daha düşük olacaktır.
- Gerekçe: Çünkü yeleklerdeki retroreflektif şeritler ağırlıklı olarak yatay yönde uzanır ve floresan kumaşla birleştiği sınırlarda çok yüksek dikey parlaklık türevi ($G_y$) üretir.

## 6b — Şablon (döndürme / ölçek serileri ve kontrol araması) · C (Paket C Sorumlusu)
- Tahmin: G-1'den kesilen yelek şablonu 10 dereceden 30 dereceye döndürüldükçe ve 0.9'dan 0.7'ye küçültüldükçe korelasyon skoru (TM_CCOEFF_NORMED) 0.80'lerin üzerinden 0.40'ın altına düşecek ve tespit konumu kayacaktır.
- Gerekçe: Çünkü standart şablon eşleme piksel yoğunluklarının birebir örtüşmesine dayanır; dönme ve ölçek değişimleri şerit sınırlarının örtüşmesini tamamen bozarak sahte konumlara kaymasına yol açar.

## 7a — Bilinen dönüşüm (SIFT + oran testi + RANSAC) · D (Paket D Sorumlusu)
- Tahmin: G-1'den kırpılan A yeleği ile sentetik dönüştürülmüş B görüntüsü arasında SIFT 50'den fazla iç değer (inlier) bulacak ve RANSAC ile kestirilen köşe hatası 2 pikselin altında kalacaktır.
- Gerekçe: Çünkü SIFT öznitelikleri ölçek ve dönme dönüşümlerine karşı matematiksel olarak değişmez (invariant) tasarlanmıştır.

## 7b — En güçlü 50 SIFT noktası ve HOG · D (Paket D Sorumlusu)
- Tahmin: En güçlü 50 SIFT noktasının büyük çoğunluğu düz floresan kumaş yüzeyinde değil, retroreflektif şeritlerin köşelerinde, cep/fermuar kenarlarında toplanacak; HOG görselinde ise yatay yönelim hücreleri baskın çıkacaktır.
- Gerekçe: Çünkü DoG (Difference of Gaussians) algoritması homojen dokusuz düz alanları eler, yalnızca yüksek gradyan içeren iki boyutlu köşe ve kontrastlı doku sınırlarına kilitlenir.

---

## Tek değişkenli deneyler

### D1 — Küçültme oranı · A (Paket A Sorumlusu)
- Tahmin: G-1 görüntüsü 1.0'dan 0.125 oranına küçültüldükçe gövde içi Canny kenar oranı belirgin şekilde azalacak (yaklaşık %60'tan fazla düşüş gösterecek), 0.25 ölçeğinde INTER_NEAREST ise INTER_AREA'ya göre basamaklanma (aliasing) nedeniyle daha yüksek sahte kenar oranı üretecektir.
- Gerekçe: Çünkü küçültme oranı düştükçe ince retroreflektif şerit sınırları ve kumaş dokusu piksellerle ortalanarak silinir; INTER_NEAREST ise piksel atladığı için kenarlarda yapay tırtıklanmalar meydana getirir.

### D2 — Filtre türü · B (Paket B Sorumlusu)
- Tahmin: Medyan ve bilateral filtreleme Gauss filtresine kıyasla gövde maske oranını daha stabil tutacak ve şerit kenarlarını korurken, filtresiz durumda izole gürültü pikselleri nedeniyle maske alanı daha parçalı çıkacaktır.
- Gerekçe: Çünkü medyan filtre tuz-biber gürültüsünü kenarları eritmeden siler, bilateral filtre ise renk gradyanını koruyarak şerit ve floresan kumaş geçişlerini bulanıklaştırmadan homojenleştirir.

### D4 — Canny eşikleri · C (Paket C Sorumlusu)
- Tahmin: Canny eşikleri 20/60'tan 100/250'ye çıkarıldığında gövdedeki kenar piksel oranı sert biçimde düşecek; düşük eşikte kumaş kırışıklıkları sahte kenar verirken yüksek eşikte retroreflektif şeritlerin sınırları da kopacaktır.
- Gerekçe: Çünkü yüksek histeresis eşiği ($T_{high}$) zayıf gradyanlı şerit sınırlarını elerken, çok düşük eşik en ufak kumaş gölgesini bile kenar olarak algılar.

### D6 — Eşleştirme eşiği (oran testi ya da RANSAC — hangisi: oran testi) · D (Paket D Sorumlusu)
- Tahmin: Lowe oran testi eşiği 0.6'dan 0.9'a gevşetildiğinde oran testinden geçen eşleşme sayısı neredeyse iki katına çıkacak ancak RANSAC'ın hesapladığı nihai köşe piksel hatası artacaktır.
- Gerekçe: Çünkü 0.9 gibi yüksek bir oran eşiği benzer dokulardan (örneğin birbirine benzeyen şerit piksellerinden) gelen çok sayıda aykırı/yanlış eşleşmeyi (outlier) filtreleyemez.

### D8 — Difüzyon süresi · E (Paket E Sorumlusu)
- Tahmin: Doğrusal difüzyonda adım sayısı 0'dan 40'a çıkarıldıkça gövdedeki kenar oranı sürekli azalacak ve 40 adım sonucu $\sigma=4$ Gauss filtresiyle yaklaşık aynı yumuşatmayı ve maske oranını verecektir.
- Gerekçe: Çünkü doğrusal izotropik ısı difüzyon denkleminin çözümü analitik olarak Gauss çekirdeği ile evrişime denktir ($\sigma = \sqrt{2t} = \sqrt{2 \times 40 \times 0.20} = 4$).
