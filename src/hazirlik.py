"""Paket A — 2d ve 3: ham görüntüleri hazırlar, kutu-cizer etiketlerini gt.json'a aktarır.

Drive'daki ham veri (takımın yüklediği):
    data/images/gelistirme/G_1.jpg …        data/images/kontrol/K_1.jpg …
    data/images/geliştirme-etiketli/        data/images/kontrol-etiketli/
        kutular.csv, goruntuler.csv          (data/docs/kutu-cizer.ipynb çıktısı; kutular HAM görüntü pikselinde)

Üretilen:
    data/images_1024/G-1.png …   uzun kenar ≤ 1024, INTER_AREA, küçükler büyütülmez (2d); PNG, ikinci bir
                                 JPEG sıkıştırması renkleri bozmasın diye
    data/image_sizes.csv         ham boyut, yeni boyut, ölçek
    data/gt.json                 kutular aynı ölçekle 1024'lük görüntüye taşınmış (3)

Klasör adlarında ş/s, ı/i, büyük/küçük harf ve sondaki boşluk farkı önemsenmez ('geliştirme ' = 'gelistirme').
"""
import copy
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

from common import (CLASSES, CTRL_IDS, DATA, DEV_IDS, GT_PATH, IMG_DIR, RAW_DIR, clip_box, entries,
                    imread_u, imwrite_u, kayit_al, resize_max1024)

PAT = re.compile(r'^([GK])[_\- ]?(\d+)\.(jpe?g|png|bmp|webp)$', re.I)
SIZES = DATA / 'image_sizes.csv'
SPLIT = {'G': 'geliştirme', 'K': 'kontrol'}


def _fold(s):
    s = unicodedata.normalize('NFKD', str(s).strip().replace('ı', 'i').replace('İ', 'I'))
    return ''.join(ch for ch in s if not unicodedata.combining(ch)).casefold()


def _child(parent, name):
    """parent içinde adı (Türkçe karakter/boşluk farkı gözetmeden) name olan klasör."""
    parent = Path(parent)
    if (parent / name).is_dir():
        return parent / name
    if parent.is_dir():
        for c in sorted(parent.iterdir()):
            if c.is_dir() and _fold(c.name) == _fold(name):
                return c
    return None


def ham_klasorler():
    """{'G': data/images/gelistirme, 'K': data/images/kontrol}"""
    out = {'G': _child(RAW_DIR, 'gelistirme'), 'K': _child(RAW_DIR, 'kontrol')}
    for k, v in out.items():
        if v is None:
            raise FileNotFoundError(f"{RAW_DIR} içinde '{'gelistirme' if k == 'G' else 'kontrol'}' klasörü yok")
    return out


def etiket_klasorleri():
    """{'G': data/images/geliştirme-etiketli, 'K': data/images/kontrol-etiketli} (olmayan atlanır)"""
    out = {'G': _child(RAW_DIR, 'gelistirme-etiketli'), 'K': _child(RAW_DIR, 'kontrol-etiketli')}
    return {k: v for k, v in out.items() if v is not None}


def dosya_kimligi(name):
    """'G_3.jpeg' -> 'G-3' (tanınmazsa None)."""
    m = PAT.match(name.strip())
    return f'{m.group(1).upper()}-{int(m.group(2))}' if m else None


def ham_dosyalar():
    """{'G-1': Path(.../gelistirme/G_1.jpg), …}"""
    files = {}
    for prefix, folder in ham_klasorler().items():
        for p in sorted(folder.iterdir()):
            if not p.is_file():
                continue
            img_id = dosya_kimligi(p.name)
            if img_id is None:
                print('  atlandı (ad tanınmadı):', p.name)
                continue
            if img_id[0] != prefix:
                print(f'  uyarı: {p.name} {folder.name} klasöründe ama öneki farklı')
            if img_id in files:
                raise ValueError(f'aynı kimlik iki kez: {img_id} ({files[img_id].name}, {p.name})')
            files[img_id] = p
    return files


def _order(img_id):
    return (img_id[0] != 'G', int(img_id.split('-')[1]))


# --------------------------------------------------------------------- 2d
def goruntuleri_hazirla(force=False, verbose=True):
    """Ham görüntüleri data/images_1024/<id>.png olarak yazar (uzun kenar ≤ 1024, INTER_AREA).
    Hedef dosya varsa ve ham dosyadan yeniyse atlanır; force=True hepsini yeniden yazar."""
    files = ham_dosyalar()
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for img_id in sorted(files, key=_order):
        src = files[img_id]
        img = imread_u(src)
        if img is None:
            raise IOError(f'{src} okunamadı')
        h, w = img.shape[:2]
        small, s = resize_max1024(img)
        out = IMG_DIR / f'{img_id}.png'
        if force or not out.exists() or out.stat().st_mtime < src.stat().st_mtime:
            imwrite_u(out, small)
            what = 'yazıldı'
        else:
            what = 'zaten var'
        rows.append({'id': img_id, 'kaynak_dosya': src.name, 'orj_w': w, 'orj_h': h,
                     'w': small.shape[1], 'h': small.shape[0], 'olcek': round(s, 6)})
        if verbose:
            print(f'{img_id:5s} {src.name:12s} {w}x{h} -> {small.shape[1]}x{small.shape[0]} (s={s:.3f}) {what}')
    df = pd.DataFrame(rows)
    df.to_csv(SIZES, index=False, encoding='utf-8')
    n_g, n_k = int(df.id.str.startswith('G').sum()), int(df.id.str.startswith('K').sum())
    print(f'Geliştirme: {n_g}/8, kontrol: {n_k}/12 -> {IMG_DIR.relative_to(DATA.parent)}')
    if (n_g, n_k) != (8, 12):
        print('UYARI: 2a 8 geliştirme + 12 kontrol istiyor.')
    return df


def boyutlar():
    """image_sizes.csv (yoksa üretir) -> {id: satır}"""
    if not SIZES.exists():
        goruntuleri_hazirla(verbose=False)
    return pd.read_csv(SIZES).set_index('id').to_dict('index')


# ---------------------------------------------------------------------- 3
def _read_csv(p):
    return pd.read_csv(p, encoding='utf-8-sig', dtype={'goruntu': str})


def _overlap_frac(v, t):
    """yelek kutusunun gövde kutusuyla örtüşen kesri"""
    ix = max(0, min(v[2], t[2]) - max(v[0], t[0]))
    iy = max(0, min(v[3], t[3]) - max(v[1], t[1]))
    a = max(1, (v[2] - v[0]) * (v[3] - v[1]))
    return ix * iy / a


def etiketleri_oku():
    """kutu-cizer çıktısını okur, kutuları 1024'lük görüntüye ölçekler. {id: {class, persons, vests, …}}"""
    sz = boyutlar()
    out = {}
    folders = etiket_klasorleri()
    if not folders:
        raise FileNotFoundError(f'{RAW_DIR} içinde *-etiketli klasörü yok (kutu-cizer.ipynb çıktısı)')
    for prefix, folder in folders.items():
        imgs = _read_csv(folder / 'goruntuler.csv')
        boxes = _read_csv(folder / 'kutular.csv')
        for _, r in imgs.iterrows():
            img_id = dosya_kimligi(r['goruntu'])
            if img_id is None or img_id not in sz:
                print(f'  atlandı: {r["goruntu"]} (ham görüntülerde karşılığı yok)')
                continue
            z = sz[img_id]
            lw, lh = int(r['genislik']), int(r['yukseklik'])
            # Kutular hangi görüntüde çizildiyse o boyuttan 1024'lük boyuta ölçeklenir.
            if (lw, lh) == (z['orj_w'], z['orj_h']) or (lw, lh) == (z['w'], z['h']):
                sx, sy = z['w'] / lw, z['h'] / lh
            else:
                raise ValueError(f'{img_id}: etiket boyutu {lw}x{lh}, ham görüntü {z["orj_w"]}x{z["orj_h"]}. '
                                 'Kutular başka bir görüntü üzerinde çizilmiş olabilir; kontrol edin.')
            shape = (z['h'], z['w'])

            def sc(b):
                return clip_box([round(b['x1'] * sx), round(b['y1'] * sy),
                                 round(b['x2'] * sx), round(b['y2'] * sy)], shape)

            b = boxes[boxes['goruntu'] == r['goruntu']]
            govde = [(sc(x), int(x['secilen_kisi'])) for _, x in b[b['etiket'] == 'govde'].iterrows()]
            yelek = [sc(x) for _, x in b[b['etiket'] == 'yelek'].iterrows()]
            cls = r['dogru_sinif'] if isinstance(r['dogru_sinif'], str) and r['dogru_sinif'].strip() else None
            sel_list = [i for i, (_, s) in enumerate(govde) if s]
            sel = sel_list[0] if sel_list else (0 if len(govde) == 1 else None)
            if len(sel_list) > 1:
                print(f'  uyarı: {img_id} birden fazla seçilen gövde; ilki alındı')
            persons = [{'torso': t, 'vest': False} for t, _ in govde]
            vests = [{'box': v, 'worn_by': None} for v in yelek]
            # 'Yelek giyili': seçilen kişinin gövdesiyle en çok örtüşen yelek o kişiye aittir.
            if cls == CLASSES[0] and sel is not None and vests:
                t = persons[sel]['torso']
                j = max(range(len(vests)), key=lambda k: _overlap_frac(vests[k]['box'], t))
                if _overlap_frac(vests[j]['box'], t) > 0:
                    vests[j]['worn_by'] = sel
                    persons[sel]['vest'] = True
            out[img_id] = {'split': SPLIT[img_id[0]], 'class': cls, 'selected': sel,
                           'persons': persons, 'vests': vests,
                           '_olcek': [round(sx, 6), round(sy, 6)], '_kaynak': f'{folder.name}/{r["goruntu"]}'}
    return out


def etiketleri_aktar(yaz=True):
    """kutu-cizer etiketlerini gt.json'a yazar. _meta ve görüntü başına secim_gerekcesi / serit / note korunur.
    gt.json'da önceden kutu varsa üzerine yazmadan önce kayitlar/ altına kopyası alınır."""
    lab = etiketleri_oku()
    with open(GT_PATH, encoding='utf-8') as f:
        gt = json.load(f)
    before = copy.deepcopy(gt)
    old = entries(before)
    meta = gt.setdefault('_meta', {})
    meta['durum'] = ('Kutular data/docs/kutu-cizer.ipynb ile HAM görüntülerde çizildi; hazirlik.etiketleri_aktar() '
                     'aynı ölçekle 1024 px görüntüye taşıdı (data/image_sizes.csv).')
    meta['kutu_bicimi'] = 'x1, y1, x2, y2; piksel; başlangıç sol üst köşe; data/images_1024 görüntüsüne göre'
    meta['aktarim'] = ("worn_by: sınıf 'Yelek giyili' ise seçilen kişinin gövdesiyle en çok örtüşen yelek o kişiye "
                       "atanır (vest=true); diğer yelekler worn_by=null (kimse giymiyor).")
    changed = []
    for img_id in sorted(set(lab) | set(old), key=_order):
        if img_id not in lab:
            print(f'  uyarı: {img_id} için etiket yok; gt.json kaydı olduğu gibi kaldı')
            continue
        L, g = lab[img_id], dict(old.get(img_id, {}))
        if L['class'] is None:
            L['class'] = g.get('class')
        elif g.get('class') and g['class'] != L['class']:
            changed.append(f"{img_id}: sınıf '{g['class']}' -> '{L['class']}' (etiket dosyasından)")
        g.update({k: v for k, v in L.items() if not k.startswith('_')})
        for k in ('secim_gerekcesi', 'serit', 'note'):
            g.setdefault(k, '')
        keys = ['split', 'class', 'selected', 'secim_gerekcesi', 'serit', 'persons', 'vests', 'note']
        gt[img_id] = {**{k: g[k] for k in keys if k in g}, **{k: v for k, v in g.items() if k not in keys}}
    missing = [i for i in DEV_IDS + CTRL_IDS if i not in lab]
    for c in changed:
        print('  ', c)
    print(f'Aktarılan: {len(lab)} görüntü; etiketi olmayan: {missing or "yok"}')
    if gt == before:
        print('gt.json zaten güncel; dosyaya dokunulmadı.')
        return gt
    if yaz:
        if any(g.get('persons') for g in old.values()):
            kayit_al(GT_PATH, etiket='gt-aktarim-oncesi', not_='etiketleri_aktar() üzerine yazmadan önce')
        with open(GT_PATH, 'w', encoding='utf-8') as f:
            json.dump(gt, f, ensure_ascii=False, indent=2)
        print('yazıldı:', GT_PATH.relative_to(DATA.parent))
    return gt


def ozet(gt):
    """Görüntü başına sınıf, seçilen kişi, gövde/yelek sayısı (gözle kontrol için)."""
    rows = []
    for img_id, g in sorted(entries(gt).items(), key=lambda kv: _order(kv[0])):
        t = g['persons'][g['selected']]['torso'] if g.get('selected') is not None and g.get('persons') else None
        rows.append({'id': img_id, 'sinif': g.get('class'), 'secilen': g.get('selected'),
                     'govde': len(g.get('persons', [])), 'yelek': len(g.get('vests', [])),
                     'secilen_govde': t, 'govde_h': None if t is None else t[3] - t[1],
                     'yelek_giyen': [v.get('worn_by') for v in g.get('vests', [])]})
    return pd.DataFrame(rows)
