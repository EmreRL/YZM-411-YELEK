"""Paket C — 6b: şablon eşleştirme (TM_CCOEFF_NORMED = ZNCC).

Şablon: bir geliştirme görüntüsündeki yelekten şerit içeren KARE parça;
kenarı = yelek kutusunun kısa kenarının yarısı.
Seriler aynı geliştirme görüntüsünde: yalnız döndürme (10/20/30°) ve yalnız ölçekleme (0,9/0,8/0,7).
Skor bir benzerlik ölçüsüdür; olasılık ya da başarı yüzdesi DEĞİLDİR (H3, S3).
"""
import cv2
import numpy as np
import pandas as pd

from common import RES, check_ids_allowed, ensure_dirs, entries, load_img, show, vest_boxes

METHODS = {'TM_CCOEFF_NORMED': cv2.TM_CCOEFF_NORMED, 'TM_SQDIFF': cv2.TM_SQDIFF,
           'TM_SQDIFF_NORMED': cv2.TM_SQDIFF_NORMED, 'TM_CCORR_NORMED': cv2.TM_CCORR_NORMED}


def _gray(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def template_info(P, gt):
    tp = P['template']
    E = entries(gt)
    g = E[tp['dev_id']]
    v = g['vests'][tp['vest_idx']]
    vx1, vy1, vx2, vy2 = v['box'] if isinstance(v, dict) else v
    s = min(vx2 - vx1, vy2 - vy1) // 2
    if tp.get('cut_xy'):
        tx, ty = tp['cut_xy']
    else:                                                  # varsayılan: yelek kutusunun ortası
        tx, ty = vx1 + (vx2 - vx1 - s) // 2, vy1 + (vy2 - vy1 - s) // 2
    wb = v.get('worn_by') if isinstance(v, dict) else None
    owner = wb if wb is not None else g['selected']
    t = g['persons'][owner]['torso']
    return {'dev_id': tp['dev_id'], 'vest_box': [vx1, vy1, vx2, vy2], 's': int(s),
            'cut_xy': [int(tx), int(ty)], 'cut_center': (tx + s / 2, ty + s / 2),
            'dev_torso_h': t[3] - t[1]}


def make_template(P, gt):
    info = template_info(P, gt)
    gray = _gray(load_img(info['dev_id']))
    tx, ty, s = *info['cut_xy'], info['s']
    tpl = gray[ty:ty + s, tx:tx + s]
    assert tpl.shape == (s, s), f'şablon görüntü dışına taşıyor: {tpl.shape} != {(s, s)}'
    return tpl, gray, info


def best(search, tpl, method='TM_CCOEFF_NORMED'):
    r = cv2.matchTemplate(search, tpl, METHODS[method])
    mn, mx, mnl, mxl = cv2.minMaxLoc(r)
    if method.startswith('TM_SQDIFF'):
        return mn, mnl                                     # SQDIFF'te en iyi = en küçük
    return mx, mxl


def _dist(loc, t, center):
    h, w = t.shape[:2]
    return float(np.hypot(loc[0] + w / 2 - center[0], loc[1] + h / 2 - center[1]))


def series(P, gt, save=True):
    """6b: aynı görüntüde döndürme ve ölçekleme serileri; skor ve kesilen konuma uzaklık (px)."""
    ensure_dirs()
    tpl, gray, info = make_template(P, gt)
    s, c = info['s'], info['cut_center']
    method = P['template'].get('method', 'TM_CCOEFF_NORMED')
    rows, vis = [], []
    sc, loc = best(gray, tpl, method)
    rows.append({'seri': 'referans', 'deger': '0° / 1,0', 'skor': sc, 'uzaklik_px': _dist(loc, tpl, c),
                 'dolgu_orani': 0.0})
    vis.append((tpl, 'şablon (referans)'))
    for ang in P['template']['rot_deg']:                   # yalnız döndürme
        M = cv2.getRotationMatrix2D((s / 2, s / 2), ang, 1.0)
        t = cv2.warpAffine(tpl, M, (s, s), borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        pad = 1 - cv2.warpAffine(np.ones_like(tpl), M, (s, s), borderValue=0).mean()  # köşelerdeki siyah dolgu
        sc, loc = best(gray, t, method)
        rows.append({'seri': 'döndürme', 'deger': f'{ang}°', 'skor': sc,
                     'uzaklik_px': _dist(loc, t, c), 'dolgu_orani': float(pad)})
        vis.append((t, f'{ang}° (dolgu %{100 * pad:.0f})'))
    for k in P['template']['scale']:                       # yalnız ölçekleme
        t = cv2.resize(tpl, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
        sc, loc = best(gray, t, method)
        rows.append({'seri': 'ölçek', 'deger': f'{k}', 'skor': sc,
                     'uzaklik_px': _dist(loc, t, c), 'dolgu_orani': 0.0})
        vis.append((t, f'ölçek {k}'))
    df = pd.DataFrame(rows)
    if save:
        df.to_csv(RES / 'template.csv', index=False)
        show([v[0] for v in vis], [v[1] for v in vis], cols=7, size=2.2, path=RES / 'fig' / 'template_series.png')
    return df


def control_scores(ids, gt, P, save=True, tag='template_control'):
    """Şablon 'kontrol gövde yüksekliği / geliştirme gövde yüksekliği' oranıyla boyutlanır ve
    yalnız gövde kutusunda aranır. Şablon gövdeden büyükse ya da gövde yoksa: 'ölçülemedi'."""
    check_ids_allowed(ids, P)
    tpl, _, info = make_template(P, gt)
    method = P['template'].get('method', 'TM_CCOEFF_NORMED')
    E = entries(gt)
    rows = []
    for img_id in ids:
        g = E[img_id]
        gray = _gray(load_img(img_id))
        persons = g.get('persons', [])
        if not persons:
            rows.append({'id': img_id, 'kisi': None, 'secilen': True, 'yelek': None, 'olcek': None,
                         'skor': 'ölçülemedi', 'neden': 'kişi yok'})
        for i, p in enumerate(persons):
            base = {'id': img_id, 'kisi': i, 'secilen': i == g.get('selected'), 'yelek': bool(p.get('vest'))}
            t_box = p.get('torso')
            if not t_box:
                rows.append({**base, 'olcek': None, 'skor': 'ölçülemedi', 'neden': 'gövde kutusu yok'})
                continue
            x1, y1, x2, y2 = t_box
            k = (y2 - y1) / info['dev_torso_h']
            t = cv2.resize(tpl, None, fx=k, fy=k,
                           interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_LINEAR)
            roi = gray[y1:y2, x1:x2]
            if t.shape[0] > roi.shape[0] or t.shape[1] > roi.shape[1] or min(t.shape) < 2:
                rows.append({**base, 'olcek': k, 'skor': 'ölçülemedi', 'neden': 'şablon gövdeden büyük'})
                continue
            sc, loc = best(roi, t, method)
            rows.append({**base, 'olcek': k, 'skor': float(sc), 'neden': ''})
    df = pd.DataFrame(rows)
    if save:
        df.to_csv(RES / f'{tag}.csv', index=False)
    return df


def side_by_side(df):
    d = df[pd.to_numeric(df['skor'], errors='coerce').notna()].copy()
    d['skor'] = d['skor'].astype(float)
    return d.groupby('yelek')['skor'].agg(['count', 'mean', 'median', 'max']).round(3)


def preview_cut(P, gt, path=None):
    """C, şerit içeren konumu seçerken kullanır; seçilen sol üst köşe params.template.cut_xy'ye yazılır."""
    info = template_info(P, gt)
    img = load_img(info['dev_id']).copy()
    vx1, vy1, vx2, vy2 = info['vest_box']
    tx, ty, s = *info['cut_xy'], info['s']
    crop = img[vy1:vy2, vx1:vx2].copy()
    for y in range(0, crop.shape[0], 20):
        cv2.line(crop, (0, y), (crop.shape[1], y), (200, 200, 200), 1)
        cv2.putText(crop, str(vy1 + y), (1, y + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
    cv2.rectangle(crop, (tx - vx1, ty - vy1), (tx - vx1 + s, ty - vy1 + s), (0, 0, 255), 2)
    print(f"kare kenarı {s}px, sol üst köşe {info['cut_xy']} (görüntü koordinatı); yelek kutusu {info['vest_box']}")
    return show([crop], [f"{info['dev_id']} yelek kırpıntısı, kırmızı = şablon"], cols=1, size=5, path=path)
