# Bireysel not (10d) — Ad Soyad, Paket D, Deney D6

**Çalıştırdığım deney ve dosya:** D6 — `notebooks/D_oznitelik.ipynb`, çıktı `results/d6_eslestirme.csv`, görsel `results/fig/sift_matches.png`.
Değiştirdiğim tek ayar: Lowe oran testi eşiği (0,6 / 0,75 / 0,9). Sabit kalanlar: params.json (dondurma tarihi 2026-11-10T21:09:21) — G-1 yelek kırpıntısı, bilinen dönüşüm 20° ve 0,7 ölçek, RANSAC 3 px, homografi modeli.

**Önceki tahminim:** Lowe oran testi eşiği 0.6'dan 0.9'a gevşetildiğinde oran testinden geçen eşleşme sayısı neredeyse iki katına çıkacak ancak RANSAC'ın hesapladığı nihai köşe piksel hatası artacaktır.

**Ölçtüğüm sonuç:** Geçen eşleşme 64 → 73 → 102 (1,6 kat), RANSAC iç değeri 60 → 64 → 68. İç değer oranı %94 → %88 → %67'ye düştü. Ortalama köşe hatası 0,12 → 0,48 → 0,56 px.

**Açıklama:** Tahminin yönü doğru, büyüklüğü abartılı: eşleşme iki katına değil 1,6 katına çıktı; köşe hatası arttı ama her üç eşikte de 1 pikselin altında kaldı. 0,75'ten 0,9'a geçerken eklenen 29 eşleşmenin yalnız 4'ü iç değer oldu. Yani gevşek eşik aykırıları içeri aldı, ama RANSAC onları ayıkladığı için model bozulmadı. Hatadaki küçük artış, 3 px tolerans içinde kalan ama tam doğru olmayan eşleşmelerin son en küçük kareler kestirimine girmesinden kaynaklanıyor. Dönüşüm sentetik ve gürültüsüz olduğu için doğru eşleşme zaten bol; gerçek bir ikinci fotoğrafta fark daha büyük olabilir.

**Sonraki kontrol:** RANSAC eşiğini (1 / 3 / 5 px) değiştirmek ya da aynı yeleğin başka açıdan çekilmiş gerçek bir fotoğrafıyla denemek; homografi yerine `estimateAffinePartial2D` (bilinen dönüşümle aynı model) kullanmak. (Ayrı "sonraki kontrol" satırı.)
