"""Defterleri üretir (bir kez çalıştırılır; sonra defterler elle düzenlenebilir).

Kurulum hücresi GitHub kullanmaz: Colab'da Google Drive'ı bağlar ve proje klasörünü Drive'da kendisi bulur.
Kullanım (proje kökünde):  python scripts/build_notebooks.py
"""
import nbformat as nbf
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SETUP = r'''# --- Kurulum: Google Drive'ı bağlar ve proje klasörünü bulur (GitHub gerekmez) ---
PROJE = ''   # boş bırakın, otomatik bulunur; bulunamazsa Drive'daki yolu yazın: '/content/drive/MyDrive/.../yelek-tespiti'
import os, sys, glob, unicodedata
sys.dont_write_bytecode = True                      # Drive'daki src/ klasörüne __pycache__ yazılmasın

def _proje_mi(p):
    return os.path.isfile(os.path.join(p, 'src', 'common.py')) and os.path.isfile(os.path.join(p, 'config', 'params.json'))

if 'google.colab' in sys.modules:
    from google.colab import drive
    drive.mount('/content/drive')
    PROJE = PROJE.strip().rstrip('/')
    if PROJE and not _proje_mi(PROJE):               # Türkçe harf kodlaması farkı (ör. 'Ödevler')
        PROJE = next((unicodedata.normalize(f, PROJE) for f in ('NFC', 'NFD')
                      if _proje_mi(unicodedata.normalize(f, PROJE))), PROJE)
    if not PROJE:                                    # Drive'ım ve ortak drive'larda 4 klasör derinliğe kadar ara
        for d in range(5):
            bulunan = sorted({os.path.dirname(os.path.dirname(p))
                              for k in ('/content/drive/MyDrive', '/content/drive/Shareddrives')
                              for p in glob.glob(os.path.join(k, *['*'] * d, 'src', 'common.py'))})
            bulunan = [p for p in bulunan if _proje_mi(p)]
            if bulunan:
                PROJE = bulunan[0]
                if len(bulunan) > 1:
                    print('Birden fazla proje klasörü bulundu, ilki kullanılıyor:', *bulunan, sep='\n  ')
                break
    if not PROJE or not _proje_mi(PROJE):
        raise FileNotFoundError("Proje klasörü bulunamadı. Drive'da paylaşılan 'yelek-tespiti' klasörüne sağ tık -> "
                                "Düzenle -> Kısayol ekle -> Drive'ım; sonra bu hücreyi yeniden çalıştırın "
                                "(ya da yukarıda PROJE = '/content/drive/MyDrive/...' yazın).")
    os.chdir(PROJE)
elif os.path.basename(os.getcwd()) == 'notebooks':  # Colab dışında (Jupyter / VS Code)
    os.chdir('..')
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
%reload_ext autoreload
%autoreload 2
import warnings; warnings.filterwarnings('ignore')
%matplotlib inline
%config InlineBackend.figure_format = 'jpeg'   # defter boyutu küçük kalsın
from common import *
gt, P = load_gt(), load_params()
durum()'''

COLAB_NOTU = ('\n\n> Colab: defteri Drive\'da açın (çift tık → *Birlikte aç → Google Colaboratory*). İlk hücre Drive\'ı bağlar '
              've proje klasörünü kendisi bulur. Defterde yaptığınız değişiklik doğrudan Drive\'daki dosyaya kaydedilir; '
              '*Drive\'a kopya kaydet* **kullanmayın** (kopya "Colab Notebooks" klasörüne gider, grup göremez).')


def md(s):
    return nbf.v4.new_markdown_cell(s.strip())


def code(s):
    return nbf.v4.new_code_cell(s.strip())


def save(name, cells):
    nb = nbf.v4.new_notebook()
    nb['cells'] = cells
    nb['metadata'] = {'kernelspec': {'name': 'python3', 'display_name': 'Python 3'},
                      'language_info': {'name': 'python'}, 'colab': {'provenance': []}}
    nbf.write(nb, ROOT / name)
    print('yazıldı:', name)


# ------------------------------------------------------------------ A
save('notebooks/A_veri_ve_etiket.ipynb', [
    md('''# Paket A — Veri, doğru sınıf, kutular, hata incelemesi, D1
Adımlar: 2 (veri), 3 (doğru sınıf ve kutular, **yöntemlerden önce**), 9 (hata incelemesi), D1.''' + COLAB_NOTU),
    code(SETUP),
    md('''## Faz 0 — Tahminler (4a)
`predictions.md` deney kodu çalıştırılmadan **önce** doldurulur ve kaydedilir. Kayıt commit'in yerini tutar:
dosyanın o anki kopyası ve SHA-256 özeti `kayitlar/` altına yazılır. Sonradan dosya değişirse `kayit_kontrol()` "DEĞİŞTİ" der.'''),
    code(r'''# kayit_al('predictions.md', etiket='tahminler-4a')     # <- herkes tahminini yazınca yorumu kaldırıp BİR KEZ çalıştırın
kayit_kontrol()'''),
    md('''## 2d — Görüntüleri küçült (uzun kenar ≤ 1024, INTER_AREA, küçükler büyütülmez)
Ham görüntüler Drive'da `data/images/gelistirme` ve `data/images/kontrol` klasörlerinde; yol yazmaya gerek yok.
Çıktı: `data/images_1024/G-1.png …` ve `data/image_sizes.csv`. Ham görüntü değişirse yeniden çalıştırın (yalnız değişenler yazılır).'''),
    code(r'''import hazirlik
boyut = hazirlik.goruntuleri_hazirla()'''),
    md('''## 3 — Kutular
Kutular `data/docs/kutu-cizer.ipynb` ile **ham** görüntülerde çizildi (`data/images/*-etiketli/kutular.csv`).
Bu hücre onları aynı ölçekle 1024'lük görüntüye taşır ve `data/gt.json`'a yazar; `_meta`, `secim_gerekcesi`, `serit`, `note` korunur.
Kutuları yeniden çizerseniz bu hücreyi yeniden çalıştırın.'''),
    code(r'''gt = hazirlik.etiketleri_aktar()
hazirlik.ozet(gt)'''),
    md('''Kontrol: eksik kişi, ters kutu, sınır dışı kutu, sınıf/vest çelişkisi.'''),
    code(r'''problems = validate_gt(gt)'''),
    code(r'''# Her görüntüde kutuları gözle kontrol (3c: "her görüntüde gözle kontrol edin")
E = entries(gt)
ids = DEV_IDS + CTRL_IDS
show([draw_boxes(load_img(i), E[i]) for i in ids],
     [f"{i} | {E[i]['class']} | seçilen P{E[i]['selected']}" for i in ids], cols=4, size=3.5,
     path=RES / 'fig' / 'kutular.png');'''),
    code(r'''# 2b koşul kapsaması (sources.csv 'kosul' sütunundan)
import pandas as pd
src = pd.read_csv(DATA / 'sources.csv', dtype=str).fillna('')
need = ['normal ışık', 'gölge', 'uzak', 'koni', 'yeleksiz', 'giyili değil']
for n in need:
    hits = src[(src.ayirim == 'kontrol') & src.kosul.str.contains(n, case=False)].id.tolist()
    print(f'{n:14s}', hits if hits else 'EKSİK')
print(pd.Series({i: E[i]['class'] for i in ids}).groupby(lambda i: i[0]).value_counts())'''),
    md('''## Dondurma 1
`gt.json/_meta` (seçim kuralı, `tpfpfn_ids` — 5f, altı görüntü, yöntemler çalışmadan önce), her görüntünün `serit` alanı (3b)
ve `sources.csv` doldurulduktan sonra kayıt alınır.'''),
    code(r'''# kayit_al('data/gt.json', 'data/sources.csv', etiket='dondurma-1')     # <- hazır olunca yorumu kaldırıp BİR KEZ çalıştırın'''),
    md('''## D1 — Küçültme oranı (Dondurma 2'den sonra)
Ölçü: gövde maske oranı ve gövdedeki Canny oranı. Ek: 0,125'e küçültüp geri büyütmek şeridi geri getirir mi (S5)?
Piksel cinsinden eşikler (gövde ≥ 40 px) sabit kaldığı için küçük oranlarda "Belirsiz" görmeniz beklenir; bunu yorumda yazın.'''),
    code(r'''import experiments
P = load_params()
d1 = experiments.d1(CTRL_IDS, gt, P, kisi='A', show_id='K-1')   # show_id: slayt görseli için bir görüntü
d1.pivot_table(index='id', columns=['yontem', 'oran'], values='govde_maske_orani').round(3)'''),
    code(r'''d1.pivot_table(index='id', columns=['yontem', 'oran'], values='canny_orani').round(3)'''),
    md('''## 9 — Hata incelemesi (B'nin dondurulmuş sonuçları üzerinde)
Bir yanlış alarm (FP) ve bir kaçırma (FN) seçin. Sonraki kontrol, dondurulmuş sonucun yerine yazılmaz.'''),
    code(r'''import pandas as pd
col = pd.read_csv(RES / 'color.csv')
col[(col.fp > 0) | (col.fn > 0) | (~col.dogru_mu)][['id', 'dogru_sinif', 'kural_sinifi', 'govde_maske_orani', 'tp', 'fp', 'fn', 'gerekce']]'''),
    code(r'''# Sonraki kontrol örneği (yalnız ayrı satır olarak eklenir):
# import merge
# merge.add_followup('K-5', 'A', 'ne değişti: ...', kuralin_sinifi='...', govde_orani='...', serit='...', tpfpfn='...', yorum='...')'''),
])

# ------------------------------------------------------------------ B
save('notebooks/B_renk.ipynb', [
    md('''# Paket B — Renk yöntemi ve filtre (5. adım), D2
Önce **yalnız G-1…G-8** ile eşikler belirlenir, `freeze_params()` ile dondurulur (Dondurma 2; params.json'un kopyası
otomatik olarak `kayitlar/` altına alınır). Kontrol görüntüleri bundan önce çalıştırılamaz (kod engeller).''' + COLAB_NOTU),
    code(SETUP),
    code(r'''import color
stats, hists = color.hsv_stats(DEV_IDS, gt)
display(stats.round(0))
color.plot_hue(hists, P, path=RES / 'fig' / 'hue_dev.png');'''),
    md('''## 5a — İki HSV aralığını belirle (sarı/sarı-yeşil, turuncu-kırmızı)
H 0–179; turuncu-kırmızı 0'ın iki yanına düşebilir (iki aralık). Ödev 1 bulgularını kullanın. Yalnız `P` sözlüğünü değiştirip aşağıdaki hücreyle bakın.'''),
    code(r'''P['hsv_yellow'] = [[22, 100, 100], [45, 255, 255]]
P['hsv_orange'] = [[[0, 120, 100], [18, 255, 255]], [[170, 120, 100], [179, 255, 255]]]
P['pre_filter'] = {'name': 'median', 'k': 5}        # 5b: none / gauss / median / bilateral
P['min_part_area_pct'] = 0.05                        # 5d: görüntü alanının yüzdesi
color.show_masks(DEV_IDS, gt, P, path=RES / 'fig' / 'masks_dev.png');'''),
    code(r'''dev = color.run(DEV_IDS, gt, P, tag='color_dev')
display(dev[['id', 'dogru_sinif', 'kural_sinifi', 'govde_maske_orani', 'maske_alan_orani', 'parca_sayisi', 'tp', 'fp', 'fn', 'gerekce']])
color.summary(dev);'''),
    md('''## Dondurma 2
Gerekçeleri doldurun (`filtre_gerekcesi`, `min_part_area_gerekcesi`, `hsv_durumu`), C'nin `template.cut_xy` ve D'nin açı/ölçek
seçimi de params.json'a yazılmış olsun; sonra kaydedip dondurun. Bundan sonra eşik değişmez (5e).'''),
    code(r'''P['hsv_durumu'] = 'G-1…G-8 hue histogramına bakılarak belirlendi (…)'
P['filtre_gerekcesi'] = '…'
P['min_part_area_gerekcesi'] = '…'
# save_params(P); freeze_params()      # <- hazır olunca yorumu kaldırıp BİR KEZ çalıştırın (kayitlar/ altına kopya alınır)'''),
    md('''## 5c–5g — 12 kontrol görüntüsü (dondurmadan sonra)'''),
    code(r'''P = load_params()
ctrl = color.run(CTRL_IDS, gt, P)
display(ctrl[['id', 'dogru_sinif', 'kural_sinifi', 'maske_alan_orani', 'govde_maske_orani', 'tp', 'fp', 'fn', 'tpfpfn_sayima_dahil', 'gerekce']])
color.summary(ctrl)
color.confusion(ctrl)'''),
    code(r'''color.show_masks(CTRL_IDS, gt, P, path=RES / 'fig' / 'masks_control.png');'''),
    md('''**H1 / S1:** yelek renginde nesne içeren görüntülerin (koni, forklift, sarı baret) maskesini ve FP'sini slayta koyun: "renk ≠ yelek".'''),
    md('''## D2 — Filtre türü (yalnız filtre değişir)'''),
    code(r'''import experiments
d2 = experiments.d2(CTRL_IDS, gt, P, kisi='B', show_id='K-1')
d2.pivot_table(index='id', columns='filtre', values='govde_maske_orani').round(3)'''),
    code(r'''d2.groupby('filtre')[['govde_maske_orani', 'maske_alan_orani', 'parca_sayisi', 'dogru_mu', 'fp']].mean().round(3)'''),
])

# ------------------------------------------------------------------ C
save('notebooks/C_kenar_sablon.ipynb', [
    md('''# Paket C — Kenar ve şablon (6. adım), D4
Kenar haritası ve şablon skoru "bu bir yelek" sonucunu tek başına vermez. Şablon skoru başarı yüzdesi ya da olasılık değildir (H3, S3).''' + COLAB_NOTU),
    code(SETUP),
    md('''## 6a — Sobel ve Canny (geliştirme görüntüsünde göz atma)'''),
    code(r'''import edge
edge.show_sobel('G-1', gt, P, path=RES / 'fig' / 'sobel_G-1.png');'''),
    md('''## 6b — Şablonun kesileceği yeri seç (yalnız geliştirme görüntüsü)
Kenar = yelek kutusunun kısa kenarının yarısı. Şerit içeren sol üst köşeyi `P['template']['cut_xy']`'e yazın ve B dondurmadan önce
params.json'a kaydedin (`save_params(P)`; B'ye haber verin — aynı anda iki kişi params.json'a yazmasın).'''),
    code(r'''import template
P['template']['dev_id'] = 'G-1'
P['template']['cut_xy'] = None          # örn. [x, y]
template.preview_cut(P, gt, path=RES / 'fig' / 'template_cut.png');'''),
    code(r'''ser = template.series(P, gt)      # aynı görüntüde: yalnız döndürme, yalnız ölçekleme
ser'''),
    md('''## Dondurmadan sonra: bütün görüntülerde kenar oranları ve kontrol araması'''),
    code(r'''P = load_params()
ed = edge.run(DEV_IDS + CTRL_IDS, gt, P)
edge.side_by_side(ed[ed.ayirim == 'kontrol'])'''),
    code(r'''ed[ed.ayirim == 'kontrol'].sort_values(['yelek', 'id'])'''),
    code(r'''tc = template.control_scores(CTRL_IDS, gt, P)
display(tc)
template.side_by_side(tc)'''),
    md('''## 6c — Kanıtın değeri (ölçüme dayalı tek cümle)
`color.csv` ile yan yana koyun: renk kuralının yanlış verdiği görüntülerde kenar/şablon farklı bir şey söylüyor mu?'''),
    code(r'''import pandas as pd
col = pd.read_csv(RES / 'color.csv')
sel = ed[(ed.secilen) & (ed.ayirim == 'kontrol')][['id', 'yelek', 'canny_orani', 'gy_gx']]
tsel = tc[tc.secilen][['id', 'skor']]
col[['id', 'dogru_sinif', 'kural_sinifi', 'govde_maske_orani']].merge(sel, on='id').merge(tsel, on='id')'''),
    md('''## D4 — Canny eşikleri (yalnız eşik çifti değişir)'''),
    code(r'''import experiments
d4 = experiments.d4(CTRL_IDS, gt, P, kisi='C', show_ids=['K-1', 'K-7'])   # bir yelekli, bir yeleksiz
d4.groupby(['canny', 'yelek'])[['canny_orani', 'gy_gx']].agg(['mean', 'median']).round(3)'''),
])

# ------------------------------------------------------------------ D
save('notebooks/D_oznitelik.ipynb', [
    md('''# Paket D — Öznitelik (7. adım), D6
7a: aynı yelek bilinen dönüşüm altında bulunuyor mu? 7b: SIFT noktaları nerede toplanıyor, HOG'da kenar yönleri yoğunlaşıyor mu?
Nokta sayısının çok olması tek başına başarı göstermez.''' + COLAB_NOTU),
    code(SETUP),
    code(r'''import features, json
P['features'].update(dev_id='G-1', vest_idx=0, angle_deg=20, scale=0.7, model='homography')
res, pair = features.run_all(P, gt, save=False)
print(json.dumps(res['7a'], ensure_ascii=False, indent=1))'''),
    code(r'''features.draw_matches(pair, path=RES / 'fig' / 'sift_matches.png');'''),
    md('''## 7b — En güçlü 50 SIFT noktası ve HOG
Noktalar floresan kumaşta mı, şerit kenarlarında mı, fermuar/cep/yazıda mı? Düz bölge / kenar / köşe ayrımıyla açıklayın.
HOG çubuk grafiğinde 90° = yatay kenar (yatay şerit).'''),
    code(r'''res['7b_sift']'''),
    code(r'''# Bir yelekli ve bir yeleksiz geliştirme gövdesi (G-4 yeleksiz)
hog = features.hog_compare([('G-1', 0), ('G-4', 0)], gt, P, path=RES / 'fig' / 'hog_dev.png')
hog'''),
    md('''Açı/ölçek seçimi B dondurmadan önce `params.json`'a yazılır (`save_params(P)`; B'ye haber verin). Sonra features.json kaydedilir:'''),
    code(r'''P = load_params()
res, pair = features.run_all(P, gt, hog_items=[('G-1', 0), ('G-4', 0)])
res['7a']'''),
    md('''## D6 — Eşleştirme eşiği (oran testi 0,6/0,75/0,9 **ya da** RANSAC 1/3/5 px)
`params.experiments.D6.mode` = `"ratio"` ya da `"ransac"`.'''),
    code(r'''import experiments
d6 = experiments.d6(P, gt, kisi='D')
d6[['oran_testi', 'ransac_px', 'gecen_eslesme', 'ic_deger', 'kose_hatasi_px']]'''),
])

# ------------------------------------------------------------------ E (D8)
save('notebooks/E_D8_difuzyon.ipynb', [
    md('''# Paket E — D8 Difüzyon süresi
Maskeden önce doğrusal difüzyon: 0, 10, 40 adım, adım büyüklüğü 0,20, her renk kanalı ayrı.
t = adım × 0,20; sürekli çözüm σ = √(2t) olan Gauss'tur → 40 adım (t = 8) ≈ Gauss σ = 4.
Yalnız difüzyon adım sayısı değişir; B'nin filtresi dahil diğer ayarlar aynıdır.''' + COLAB_NOTU),
    code(SETUP),
    code(r'''import experiments
d8 = experiments.d8(CTRL_IDS, gt, P, kisi='E', show_id='K-1')
d8.groupby('islem')[['govde_maske_orani', 'canny_orani']].mean().round(3)'''),
    code(r'''d8.pivot_table(index='id', columns='islem', values=['govde_maske_orani', 'canny_orani']).round(3)'''),
    code(r'''# 40 adım ile Gauss σ=4 arasındaki ortalama mutlak piksel farkı (0–255 ölçeğinde)
d8[d8.islem.str.startswith('Gauss')][['id', 'fark_difuzyon40_mae']]'''),
    md('''**Neden kenarlar yayılıyor?** Isı denklemi u_t = Δu her pikseli komşularının ortalamasına çeker; t arttıkça
etkin Gauss genişliği σ = √(2t) büyür ve basamak biçimli şerit kenarı σ genişliğinde bir rampaya dönüşür. Gradyan
tepesi düşer, Canny'nin yüksek eşiğini geçemez ya da kenar kayar. Doğrusal difüzyon yön gözetmez (izotropik);
kenarı koruyan bilateral/medyan filtreden bu yüzden ayrılır (S6).'''),
])

# ------------------------------------------------------------------ main
save('main.ipynb', [
    md('''# YZM 411 — Yelek tespiti ve sınıflandırması (klasik yöntemler)
Çalışan defter (10a): baştan sona, **dondurulmuş** `params.json` ve `gt.json` ile bütün sonuçları yeniden üretir.
Bu defter sunum değildir; slaytlar ve sonuç tablosu Drive'daki proje klasöründe ayrıca durur.

Sıra: veri ve kutular (A) → renk (B) → kenar ve şablon (C) → öznitelik (D) → tek değişkenli deneyler → sonuç tablosu (E).
`results/` dosyalarının üzerine yazdığı için bu defteri **aynı anda tek kişi** çalıştırsın (E).''' + COLAB_NOTU),
    code(SETUP),
    code(r'''assert P['_frozen'], ("params.json dondurulmadan main.ipynb çalıştırılmaz (5e): "
                      "B, B_renk.ipynb'deki Dondurma 2 hücresini çalıştırmalı")
validate_gt(gt)
kayit_kontrol()          # tahminler (4a) ve dondurma kayıtları; "DEĞİŞTİ" görmemelisiniz'''),
    md('## 5 — Renk yöntemi'),
    code(r'''import color
col = color.run(CTRL_IDS, gt, P)
color.summary(col)
display(color.confusion(col))
color.show_masks(CTRL_IDS, gt, P, path=RES / 'fig' / 'masks_control.png');'''),
    md('## 6 — Kenar ve şablon'),
    code(r'''import edge, template
ed = edge.run(DEV_IDS + CTRL_IDS, gt, P)
display(edge.side_by_side(ed[ed.ayirim == 'kontrol']))
display(template.series(P, gt))
tc = template.control_scores(CTRL_IDS, gt, P)
template.side_by_side(tc)'''),
    md('## 7 — Öznitelik'),
    code(r'''import features
res, pair = features.run_all(P, gt, hog_items=[(P['features']['dev_id'], 0)])
res['7a']'''),
    md('## Tek değişkenli deneyler (D1, D2, D4, D6, D8)'),
    code(r'''import experiments
d1 = experiments.d1(CTRL_IDS, gt, P, kisi='A')
d2 = experiments.d2(CTRL_IDS, gt, P, kisi='B')
d4 = experiments.d4(CTRL_IDS, gt, P, kisi='C')
d6 = experiments.d6(P, gt, kisi='D')
d8 = experiments.d8(CTRL_IDS, gt, P, kisi='E')
print('kaydedildi: results/d1_kucultme.csv, d2_filtre.csv, d4_canny.csv, d6_eslestirme.csv, d8_difuzyon.csv')'''),
    md('## 10b — Sonuç tablosu'),
    code(r'''import merge
final = merge.build()
final'''),
    code(r'''deney_kayitlari()        # herkesin results/experiments_<kişi>.csv dosyası -> results/experiments.csv (4b)'''),
    md('''**Bitirirken (isteğe bağlı):** Colab, Drive'a yazmayı arka planda bitirir. Oturumu hemen kapatacaksanız aşağıdaki hücre
bekleyen yazmaları tamamlar (Drive bağlantısını da keser).'''),
    code(r'''# drive_kaydet()'''),
])
