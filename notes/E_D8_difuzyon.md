# Bireysel not (10d) — Osman Acar, Paket E, Deney D8

**Çalıştırdığım deney ve dosya:** D8 — `notebooks/E_D8_difuzyon.ipynb`, çıktı `results/d8_difuzyon.csv`, görsel `results/fig/d8_K-1.png`.
Değiştirdiğim tek ayar: renk maskesinden önceki doğrusal difüzyonun adım sayısı (0 / 10 / 40, dt = 0,20, her kanal ayrı); karşılaştırma için Gauss σ = 4. Sabit kalanlar: params.json (dondurma tarihi 2026-11-10T21:09:21), B'nin medyan filtresi ve Canny 50/150 dahil.

**Önceki tahminim:** Doğrusal difüzyonda adım sayısı 0'dan 40'a çıkarıldıkça gövdedeki kenar oranı sürekli azalacak ve 40 adım sonucu σ=4 Gauss filtresiyle yaklaşık aynı yumuşatmayı ve maske oranını verecektir.

**Ölçtüğüm sonuç:** 12 kontrol görüntüsünde gövdedeki Canny oranı 0 → 10 → 40 adım için 0,115 → 0,039 → 0,007 oldu (%94 düşüş); Gauss σ = 4 de 0,007 verdi. Ortalama gövde maske oranı %17,4 → %18,1 → %17,5, Gauss %17,6. 40 adım ile Gauss σ = 4 arasındaki ortalama mutlak fark 0,03–0,20 gri düzey (en büyük K-8). Maske oranı görüntü bazında tek yönlü değil: K-6'da %19,6 → %14,9 düştü, K-4'te %35,6 → %43,8 → %40,5 oldu.

**Açıklama:** İki tahmin de tuttu. Isı denkleminin çözümü σ = √(2t) olan Gauss'tur: 10 adımda t = 2 ve σ = 2, 40 adımda t = 8 ve σ = 4. Basamak biçimli şerit kenarı σ genişliğinde bir rampaya dönüşür, gradyan tepesi düşer ve Canny eşiğini geçemez. Farkın 0,2 gri düzeyin altında kalması, dt = 0,20'nin açık Euler kararlılık sınırının (4 komşulu Laplace için 0,25) altında olmasıyla açıklanır. Maske oranı ortalamada sabit, çünkü yelek düşük frekanslı geniş bir renk bölgesidir. Sınırda ise renkler karışır ve etkisi sınır/alan oranı büyük olan gövdelerde görünür: küçük K-4'te maske dalgalanıyor; açık yeşil yelekli ve beyaz tişörtlü K-6'da karışan piksellerin doygunluğu muhtemelen eşiğin altına düşüyor.

**Sonraki kontrol:** Kenar koruyan Perona–Malik (anizotropik) difüzyonla aynı deneyi tekrarlamak: şerit kenarları korunursa Canny oranı 0 adıma yakın kalmalı. (Ayrı "sonraki kontrol" satırı.)
