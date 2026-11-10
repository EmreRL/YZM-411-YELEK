# Bireysel not (10d) — Ad Soyad, Paket B, Deney D2

**Çalıştırdığım deney ve dosya:** D2 — `notebooks/B_renk.ipynb`, çıktı `results/d2_filtre.csv`, görsel `results/fig/d2_K-1.png`.
Değiştirdiğim tek ayar: maskeden önceki filtre (yok / Gauss k=5 / medyan k=5 / bilateral d=9, σ_renk = σ_uzay = 75). Sabit kalanlar: params.json (dondurma tarihi 2026-11-10T21:09:21) — HSV aralıkları, 3×3 açma, parça eşiği %0,05, karar kuralı.

**Önceki tahminim:** Medyan ve bilateral filtreleme Gauss filtresine kıyasla gövde maske oranını daha stabil tutacak ve şerit kenarlarını korurken, filtresiz durumda izole gürültü pikselleri nedeniyle maske alanı daha parçalı çıkacaktır.

**Ölçtüğüm sonuç:** 12 kontrol görüntüsünde ortalama gövde maske oranı: filtresiz %16,5, Gauss %17,3, medyan %17,4, bilateral %17,3. Ortalama parça sayısı 8,67 / 8,08 / 8,00 / 8,08, görüntü başına FP 8,33 / 7,75 / 7,67 / 7,75. Doğru sınıf dördünde de 8/12. En büyük fark uzak ve küçük K-4'te (gövde 42 px): filtresiz %29,2, filtrelilerde %35,5–36,2.

**Açıklama:** Tahminin "filtresiz daha parçalı" kısmı tuttu: en çok parça ve FP filtresiz durumda. Medyan ve bilateral ile Gauss arasındaki fark ise 0,1 puanın altında, yani tahmin edilen ayrım ölçülemedi. Nedeni, filtreden sonra gelen 3×3 morfolojik açmanın izole pikselleri zaten silmesi ve yeleklerin geniş, homojen renk bölgeleri olması. Filtre yalnız bölge sınırındaki pikselleri değiştirir; büyük gövdede sınır/alan oranı küçük olduğu için oran değişmez, küçük gövdede (K-4) ise görünür. Görüntü başına 8 civarındaki FP filtreden değil, çok düşük parça eşiğinden (%0,05) geliyor; filtre bunu çözmüyor.

**Sonraki kontrol:** Açmayı kapatıp (`open_kernel = 1`) filtreleri yeniden karşılaştırmak ya da parça eşiğini yükseltip FP'nin nasıl değiştiğine bakmak. (Ayrı "sonraki kontrol" satırı.)
