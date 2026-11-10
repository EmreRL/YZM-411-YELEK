# Bireysel not (10d) — Ad Soyad, Paket C, Deney D4

**Çalıştırdığım deney ve dosya:** D4 — `notebooks/C_kenar_sablon.ipynb`, çıktı `results/d4_canny.csv`, görsel `results/fig/d4_canny.png` (K-1 yelekli, K-7 yeleksiz).
Değiştirdiğim tek ayar: Canny eşik çifti (20/60, 50/150, 100/250); kenarlar tüm görüntüde hesaplanıp gövde kutusunda sayıldı. Sabit kalanlar: params.json (dondurma tarihi 2026-11-10T21:09:21), Sobel ksize = 3.

**Önceki tahminim:** Canny eşikleri 20/60'tan 100/250'ye çıkarıldığında gövdedeki kenar piksel oranı sert biçimde düşecek; düşük eşikte kumaş kırışıklıkları sahte kenar verirken yüksek eşikte retroreflektif şeritlerin sınırları da kopacaktır.

**Ölçtüğüm sonuç:** Yelekli 6 gövdede ortalama Canny oranı 20/60 → 50/150 → 100/250 için 0,142 → 0,103 → 0,081 oldu (medyan 0,119 → 0,075 → 0,051). Yeleksiz 6 gövdede 0,199 → 0,127 → 0,077. Yeleksizler ilk iki eşikte yeleklilerden fazla kenar verdi; en yüksek değer kareli gömlekli K-9'da (0,258 → 0,195 → 0,082). 100/250'de iki grup neredeyse eşitlendi (0,081 ve 0,077). Eşikten bağımsız Gy/Gx oranı yeleklilerde 0,80, yeleksizlerde 0,94 (çizgili gömlekli K-8'de 1,65).

**Açıklama:** Düşüş tahmini tuttu (yelekli yaklaşık %43, yeleksiz %61 azaldı). Ama Canny oranı sınıfları ayırmıyor: Canny yalnız yoğunluk değişimini ölçer; kareli ya da çizgili gömlek, iskele ve kırışıklık her eşikte kenar üretir. Floresan kumaş ise geniş, düz bir bölgedir. Histerezis nedeniyle düşük eşik zayıf doku kenarlarını tutar, yüksek eşikte ise yalnız güçlü kontrast kalır; bu yüzden fark 100/250'de kapanıyor. "Şerit sınırları kopacak" kısmı sayıyla değil, `d4_canny.png`'de K-1'in 100/250 karesine bakarak doğrulanmalı: [görsel gözleminizi buraya yazın]. Gy/Gx'in yeleklilerde 1'in altında kalması, yatay şerit beklentisine karşın dikey askı şeritlerinin ve fermuarın da güçlü Gx ürettiğini gösteriyor.

**Sonraki kontrol:** Kenar piksellerini yalnız renk maskesi içinde ya da yalnız yatay yönelimli olanları (|Gy| > 2|Gx|) saymak. (Ayrı "sonraki kontrol" satırı.)
