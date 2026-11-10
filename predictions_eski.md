# Tahminler (4a)

> **Kural:** Her deney için iki cümle. Bu dosya deneyler çalıştırılmadan **önce** doldurulur ve kaydı alınır:
> `A_veri_ve_etiket.ipynb` → *Faz 0* hücresinde `kayit_al('predictions.md', etiket='tahminler-4a')` (dosyanın o anki
> kopyası, zamanı ve SHA-256 özeti `kayitlar/` klasörüne yazılır). Tahmini olmayan deney puanlanmaz.
> Kayıt alındıktan sonra bu dosya **değiştirilmez** (`kayit_kontrol()` değişirse "DEĞİŞTİ" der); yanlış çıkan tahmin
> bireysel notta tartışılır. Drive'da bu dosyaya sağ tık → *Dosya bilgileri → Sürümleri yönet* → kayıt anındaki sürümde
> *Sonsuza kadar sakla* işaretlenirse Drive da ayrı bir zaman damgası tutar.
>
> Yazarken: ölçülebilir bir şey söyleyin (hangi ölçü, hangi yönde, hangi görüntüde) ve nedenini bir cümleyle verin.
> Örnek biçim: *"Turuncu koni bulunan K-5'te renk maskesi koniyi de seçecek ve kural 'Yelek var, giyili değil' diyecek.
> Çünkü HSV aralığı yalnız rengi sınar, giysi biçimini ya da şeridi sınamaz."*

Sunum adı: **klasik yöntemler** — hazır dedektör (isteğe bağlı adım) yapılmıyor, tahmini de yok.

---

## 5. adım — Renk kuralı · B (…………)
- Tahmin:
- Gerekçe:

## 6a — Kenar (Sobel, Canny) · C (…………)
- Tahmin:
- Gerekçe:

## 6b — Şablon (döndürme / ölçek serileri ve kontrol araması) · C (…………)
- Tahmin:
- Gerekçe:

## 7a — Bilinen dönüşüm (SIFT + oran testi + RANSAC) · D (…………)
- Tahmin:
- Gerekçe:

## 7b — En güçlü 50 SIFT noktası ve HOG · D (…………)
- Tahmin:
- Gerekçe:

---

## Tek değişkenli deneyler

### D1 — Küçültme oranı · A (…………)
- Tahmin:
- Gerekçe:

### D2 — Filtre türü · B (…………)
- Tahmin:
- Gerekçe:

### D4 — Canny eşikleri · C (…………)
- Tahmin:
- Gerekçe:

### D6 — Eşleştirme eşiği (oran testi ya da RANSAC — hangisi: ……) · D (…………)
- Tahmin:
- Gerekçe:

### D8 — Difüzyon süresi · E (…………)
- Tahmin:
- Gerekçe:
