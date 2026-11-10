# YZM 411 — İşçi Yeleği Tespiti ve Sınıflandırması (klasik yöntemler)

8 geliştirme + 12 kontrol görüntüsünde renk tabanlı başlangıç yöntemi; üzerine filtre/difüzyon, kenar, şablon ve öznitelik
kanıtı. Her yöntemin hangi soruyu yanıtlayıp hangisini yanıtlayamadığı ölçülür. Model eğitimi yok; hazır dedektör yok.

## İş bölümü

| Paket | Kişi | Ödev adımları | Deney | Ana çıktı | Sunum (slayt / soru) |
|---|---|---|---|---|---|
| **A** Veri, doğru sınıf, hata | ……… | 2, 3, 9 | D1 küçültme | `data/images`, `sources.csv`, `gt.json`, hata incelemesi | 2, 15 / S5, S7 |
| **B** Renk + filtre | Emre | 5 | D2 filtre | `params.json` (dondurma), `color.csv`, maskeler | 3–4 / S1, S6 |
| **C** Kenar + şablon | ……… | 6 | D4 Canny | `edge.csv`, `template*.csv` | 5–6 / S2, S3 |
| **D** Öznitelik | ……… | 7 | D6 eşleştirme | `features.json`, SIFT/HOG görselleri | 7–8 / S4 |
| **E** Araştırma + birleştirme | Osman | 1, ortak kod, sonuç tablosu | D8 difüzyon | 1. slayt, `main.ipynb`, `final_table.csv` | 1, 14 / S6 |

Herkes ayrıca: kendi tahminleri (`predictions.md`), yarım sayfalık not (`notes/`), yapay zekâ beyanına kendi satırı,
kendi deney slaytı (9–13).

**Kutular darboğazdır:** 20 görüntünün kutularını beş kişi bölüşür (kişi başı 4 görüntü), araç dosyaları birleştirir.

## Drive'da kurulum ve çalıştırma (GitHub yok)

Proje yalnız Google Drive'daki `yelek-tespiti` klasöründe yaşar; kod, veri, sonuçlar ve kayıtlar orada. Klon, commit, push yok.

1. **Klasörü Drive'a koyun (bir kez, grup lideri):** `yelek-tespiti` klasörünü Drive'a yükleyin ve grupla
   *Düzenleyen* yetkisiyle paylaşın.
2. **Herkes (bir kez):** *Benimle paylaşılanlar*'da klasöre sağ tık → *Düzenle → Kısayol ekle* → *Drive'ım*.
   (Colab yalnız *Drive'ım* altını görür; kısayol olmadan klasör bulunamaz.)
3. **Defteri açın:** Drive'da `notebooks/<kendi defteriniz>.ipynb`'ye çift tık → *Birlikte aç → Google Colaboratory*.
4. **İlk hücreyi çalıştırın:** Drive'ı bağlar, proje klasörünü *Drive'ım* ve ortak drive'larda kendisi bulur ve durumu yazar
   (görüntüler, kutular, dondurma, kayıtlar). Bulamazsa hücrenin başındaki `PROJE = '...'` satırına yolu yazın; yolu soldaki
   dosya panelinde klasöre sağ tık → *Yolu kopyala* ile alabilirsiniz.

Defterde yaptığınız değişiklik doğrudan Drive'daki dosyaya kaydedilir. *Dosya → Drive'a kopya kaydet* **kullanmayın**: kopya
kişisel "Colab Notebooks" klasörüne gider ve grup görmez. Kurulum hücresi `autoreload` açar; `src/*.py` dosyasını Drive'da
düzenlerseniz defteri yeniden başlatmanız gerekmez.

**Drive'da birlikte çalışma kuralları** (Git'in birleştirme yapmadığı yerde çakışma olmasın diye):
- Herkes yalnız kendi defterinde çalışır; aynı defteri iki kişi aynı anda açmaz.
- `params.json`'a yazan tek kişi B'dir; C (`template.cut_xy`) ve D (açı/ölçek) seçimlerini B'ye iletir ya da sırayla yazar.
- `main.ipynb`'yi aynı anda tek kişi (E) çalıştırır; `results/` dosyalarının üzerine yazar.
- Deney kayıtları kişi başına ayrı dosyaya yazılır (`results/experiments_A.csv` …); `deney_kayitlari()` hepsini
  `results/experiments.csv`'de birleştirir (4b).
- Oturumu hemen kapatacaksanız son hücrede `drive_kaydet()` bekleyen yazmaları tamamlar.

## Akış ve iki dondurma noktası

Git commit'inin yerini **kayıt** tutar: `kayit_al(dosya…, etiket=…)` dosyanın o anki kopyasını
`kayitlar/<zaman>_<etiket>/` altına, zamanını ve SHA-256 özetini `kayitlar/kayit_defteri.csv`'ye yazar.
`kayit_kontrol()` her kaydı listeler ve dosyanın kayıttan sonra değişip değişmediğini gösterir. `kayitlar/` klasörüne elle
dokunmayın.

1. **Faz 0 — birlikte:** kişi seçme kuralı, gövde kuralı, 5f'deki altı görüntü → `gt.json/_meta`. Tahminler yazılır →
   **kayıt** `kayit_al('predictions.md', etiket='tahminler-4a')` (deney kodu çalıştırılmadan önce; A defteri, Faz 0 hücresi).
2. **Faz 1:** Kutular `data/docs/kutu-cizer.ipynb` ile ham görüntülerde çizildi. A, `A_veri_ve_etiket.ipynb`'de görüntüleri
   küçültür (`hazirlik.goruntuleri_hazirla()`), kutuları aynı ölçekle `gt.json`'a aktarır (`hazirlik.etiketleri_aktar()`)
   ve `validate_gt()` temiz çıkana kadar düzeltir.
   → **Dondurma 1:** `kayit_al('data/gt.json', 'data/sources.csv', etiket='dondurma-1')`.
3. **Faz 2:** B yalnız G-1…G-8 ile HSV aralıklarını, filtreyi, parça eşiğini belirler; C şablonun kesileceği yeri
   (`template.cut_xy`), D açı/ölçeği seçer → `params.json`'a yazılır → `freeze_params()` → **Dondurma 2** (kayıt otomatik).
   Kod, dondurmadan önce kontrol görüntüsü çalıştırmayı reddeder; dondurmadan sonra ayarlar kayıttan farklıysa uyarır.
4. **Faz 3 — paralel:** B/C/D kontrol görüntülerinde çalıştırır; herkes kendi D deneyini yapar; A hata incelemesi;
   E `main.ipynb` + `merge.build()` ile sonuç tablosu.
5. **Faz 4 — birlikte:** en fazla 15 slayt, notlar, yapay zekâ beyanı, kısa ekran kaydı (yedek).

Kontrol görüntüleri gördükten sonra eşik değişmez (5e). Sonradan denenen her şey `merge.add_followup()` ile
sonuç tablosunda ayrı **"sonraki kontrol"** satırı olur (9b).

## Klasör yapısı

```
data/images/gelistirme/   G_1.jpg … (ham, Drive'a yüklenen)      data/images/kontrol/   K_1.jpg … (ham)
data/images/geliştirme-etiketli/, kontrol-etiketli/   kutu-cizer çıktısı: kutular.csv, goruntuler.csv, etiketler.json
data/images_1024/  G-1.png … K-12.png (uzun kenar ≤ 1024, INTER_AREA) — hazirlik.goruntuleri_hazirla() üretir
data/image_sizes.csv  ham boyut → 1024 boyutu, ölçek
data/sources.csv   id, ayırım, kaynak, lisans, atıf, koşul (H6, 10a) — 20 görüntünün hepsi
data/gt.json       doğru sınıf, seçilen kişi, gövde ve yelek kutuları (x1,y1,x2,y2 piksel, 1024'lük görüntüde)
data/docs/         sınıf/gövde belgesi, kutu-cizer.ipynb (etiketleme defteri)
config/params.json dondurulmuş ayarlar
predictions.md     tahminler (deneylerden önce kayıt, 4a)
kayitlar/          tahmin ve dondurma kayıtları + kayit_defteri.csv (commit yerine)
src/common.py      ortak fonksiyonlar (okuma, IoU, eşleme, kayıt, doğrulama, durum)
src/hazirlik.py    2d küçültme + kutu-cizer etiketlerini gt.json'a aktarma (A)
src/color.py       5. adım (B)        src/edge.py      6a (C)        src/template.py  6b (C)
src/features.py    7. adım (D)        src/experiments.py  D1 D2 D4 D6 D8   src/merge.py  sonuç tablosu (E)
notebooks/         A_…, B_…, C_…, D_…, E_D8_… (herkes yalnız kendi defterinde çalışır)
main.ipynb         çalışan defter, baştan sona (10a)
results/           csv'ler, maskeler, şekiller, final_table.csv / .md, experiments.csv (4b)
scripts/           build_notebooks.py (defterleri üretir), prepare_images.py (hazirlik'in komut satırı hâli)
tools/kutu_cizer.html   yedek kutu çizme aracı (tarayıcıda açılır)
notes/             yarım sayfalık bireysel notlar (10d)
AI_BEYANI.md       yapay zekâ beyanı (10e)
```

## Kutular

Kutular `data/docs/kutu-cizer.ipynb` ile Colab'da, **ham** görüntüler üzerinde çizildi (yol hücresindeki `KOK`'u kendi
Drive yolunuza göre düzeltin). Çıktı `data/images/*-etiketli/kutular.csv`'dir. `hazirlik.etiketleri_aktar()` bunları
küçültme ölçeğiyle 1024'lük görüntüye taşır ve `gt.json`'a yazar; `_meta`, `secim_gerekcesi`, `serit`, `note` korunur.
Sınıfı "Yelek giyili" olan görüntüde seçilen kişinin gövdesiyle en çok örtüşen yelek o kişiye atanır; diğer yelekler
"kimse giymiyor" sayılır. Kutuları yeniden çizerseniz aktarımı yeniden çalıştırın (değişiklik yoksa dosyaya dokunmaz;
varsa eski `gt.json`'un kaydını alıp yazar).

Yedek araç: `tools/kutu_cizer.html` (Drive'dan indirip tarayıcıda açın) → `data/images_1024` içindeki PNG'leri seçin →
`data/gt.json`'u yükleyin. **G** = gövde, **Y** = yelek, **K** = kişi kutusu. Bitince **gt.json indir** ve Drive'daki
`data/gt.json`'un yerine koyun.

## Açık sorular (hocaya)

- 5f "TP/FP/FN'yi yalnız altı kontrol görüntüsünde sayın": hangi altı? Cevap gelene kadar: A, yöntemlerden önce 2b'deki
  koşullardan birer görüntü seçip `_meta.tpfpfn_ids`'e yazar; tabloda diğerleri "—".
- 10a "sekiz görüntünün kaynak ve lisans tablosu": H6 her görüntüyü istediği için tablo 20 görüntüyü kapsar.

## Kişisel veri

Kendi çektiğiniz fotoğraflarda kişilerin izni gerekir; yüzleri bulanıklaştırmak gerekirse küçültmeden önce yapın ve
`sources.csv/kisisel_veri_notu`'na yazın. Başkasının görselini kendi çekiminiz gibi sunmayın.
