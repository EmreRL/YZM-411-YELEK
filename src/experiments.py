"""Tek değişkenli deneyler (her üye bir tane): D1 (A), D2 (B), D4 (C), D6 (D), D8 (E).

Kural: yalnız seçilen ayar değişir; diğer bütün ayarlar params.json'daki (5–7. adım) gibi kalır.
Her deney results/<deney>.csv'ye yazar ve log_experiment ile results/experiments.csv'ye kaydedilir.
"""
import copy

import cv2
import numpy as np
import pandas as pd

import color
import edge
from common import (RES, check_ids_allowed, clip_box, ensure_dirs, entries, load_img,
                    log_experiment, scale_box, selected_torso, show)


def _scale_gt(g, r, shape):
    g = copy.deepcopy(g)
    for p in g.get('persons', []):
        if p.get('torso'):
            p['torso'] = clip_box(scale_box(p['torso'], r), shape)
    for v in g.get('vests', []):
        v['box'] = clip_box(scale_box(v['box'], r), shape)
    return g


def _metrics(img, g, P, canny=None):
    r = color.run_one(img, g, P)
    t = selected_torso(g)
    c = gy_gx = None
    if t and (t[2] - t[0]) > 0 and (t[3] - t[1]) > 0:
        _, gx, gy, e = edge.gradients(img, canny or P['canny'], P.get('sobel_ksize', 3))
        c, gy_gx = edge.edge_stats(e, gx, gy, t)
    return {'kural_sinifi': r['class'], 'dogru_mu': r['class'] == g['class'],
            'govde_maske_orani': r['torso_ratio'], 'maske_alan_orani': r['mask_ratio'],
            'parca_sayisi': len(r['parts']), 'canny_orani': c, 'gy_gx': gy_gx,
            'govde_h': None if not t else t[3] - t[1], 'gerekce': r['reason']}


# ------------------------------------------------------------------- D1 (A)
def d1(ids, gt, P, kisi='A', show_id=None):
    """Küçültme oranı. Kutular aynı oranla küçültülür. 0,25'te INTER_NEAREST ile INTER_AREA.
    Ek: 0,125'e küçültüp geri büyütmek şeridi geri getirir mi (S5)? Canny oranı karşılaştırılır."""
    check_ids_allowed(ids, P)
    ensure_dirs()
    X = P['experiments']['D1']
    E = entries(gt)
    rows, crops = [], []
    for img_id in ids:
        img, g = load_img(img_id), E[img_id]
        H, W = img.shape[:2]
        for r in X['ratios']:
            small = img if r == 1 else cv2.resize(img, None, fx=r, fy=r, interpolation=cv2.INTER_AREA)
            gr = _scale_gt(g, r, small.shape)
            rows.append({'id': img_id, 'yontem': 'INTER_AREA', 'oran': r,
                         'boyut': f'{small.shape[1]}x{small.shape[0]}', **_metrics(small, gr, P)})
            if img_id == show_id and selected_torso(gr):
                x1, y1, x2, y2 = selected_torso(gr)
                crops.append((cv2.resize(small[y1:y2, x1:x2], (200, int(200 * (y2 - y1) / max(1, x2 - x1))),
                                         interpolation=cv2.INTER_NEAREST), f'AREA {r}'))
        r = X['nearest_ratio']
        near = cv2.resize(img, None, fx=r, fy=r, interpolation=cv2.INTER_NEAREST)
        rows.append({'id': img_id, 'yontem': 'INTER_NEAREST', 'oran': r,
                     'boyut': f'{near.shape[1]}x{near.shape[0]}', **_metrics(near, _scale_gt(g, r, near.shape), P)})
        if img_id == show_id and selected_torso(_scale_gt(g, r, near.shape)):
            x1, y1, x2, y2 = selected_torso(_scale_gt(g, r, near.shape))
            crops.append((cv2.resize(near[y1:y2, x1:x2], (200, int(200 * (y2 - y1) / max(1, x2 - x1))),
                                     interpolation=cv2.INTER_NEAREST), f'NEAREST {r}'))
        # S5: küçük görüntüyü geri büyütmek kaybolan şeridi geri getirir mi?
        rmin = min(X['ratios'])
        tiny = cv2.resize(img, None, fx=rmin, fy=rmin, interpolation=cv2.INTER_AREA)
        back = cv2.resize(tiny, (W, H), interpolation=cv2.INTER_LINEAR)
        rows.append({'id': img_id, 'yontem': f'{rmin}→1 geri büyütme (LINEAR)', 'oran': 1.0,
                     'boyut': f'{W}x{H}', **_metrics(back, g, P)})
    df = pd.DataFrame(rows)
    df.to_csv(RES / 'd1_kucultme.csv', index=False)
    if crops:
        show([c[0] for c in crops], [c[1] for c in crops], cols=len(crops), size=2.6,
             path=RES / 'fig' / f'd1_{show_id}.png')
    log_experiment('D1 küçültme oranı', kisi, ','.join(ids), X,
                   df.groupby(['yontem', 'oran'])[['govde_maske_orani', 'canny_orani']].mean().round(3).to_dict(),
                   'YORUM: notta yazılacak')
    return df


# ------------------------------------------------------------------- D2 (B)
def d2(ids, gt, P, kisi='B', show_id=None):
    """Filtre türü: yok / Gauss / medyan / bilateral. Maske ve gövde maske oranı nasıl değişiyor?"""
    check_ids_allowed(ids, P)
    ensure_dirs()
    E = entries(gt)
    rows, vis = [], []
    for img_id in ids:
        img, g = load_img(img_id), E[img_id]
        for f in P['experiments']['D2']['filters']:
            r = color.run_one(img, g, P, pre_filter=f)
            name = f['name'] + (f"(k={f['k']})" if 'k' in f else '')
            rows.append({'id': img_id, 'filtre': name, 'kural_sinifi': r['class'],
                         'dogru_mu': r['class'] == g['class'], 'govde_maske_orani': r['torso_ratio'],
                         'maske_alan_orani': r['mask_ratio'], 'parca_sayisi': len(r['parts']),
                         'tp': r['tp'], 'fp': r['fp'], 'fn': r['fn']})
            if img_id == show_id:
                vis.append((r['mask'], name))
    df = pd.DataFrame(rows)
    df.to_csv(RES / 'd2_filtre.csv', index=False)
    if vis:
        show([v[0] for v in vis], [v[1] for v in vis], cols=len(vis), size=3, path=RES / 'fig' / f'd2_{show_id}.png')
    log_experiment('D2 filtre türü', kisi, ','.join(ids), P['experiments']['D2'],
                   df.groupby('filtre')[['govde_maske_orani', 'parca_sayisi', 'dogru_mu']].mean().round(3).to_dict(),
                   'YORUM: notta yazılacak')
    return df


# ------------------------------------------------------------------- D4 (C)
def d4(ids, gt, P, kisi='C', show_ids=()):
    """Canny eşikleri 20/60, 50/150, 100/250 (yine tüm görüntüde). Yelekli/yeleksiz gövdeler yan yana."""
    check_ids_allowed(ids, P)
    ensure_dirs()
    E = entries(gt)
    dfs, vis = [], []
    for lo, hi in P['experiments']['D4']['pairs']:
        d = edge.run(ids, gt, P, canny=(lo, hi), save=False)
        dfs.append(d)
        for img_id in show_ids:
            g = E[img_id]
            _, _, _, e = edge.gradients(load_img(img_id), (lo, hi))
            x1, y1, x2, y2 = selected_torso(g)
            vis.append((e[y1:y2, x1:x2], f'{img_id} {lo}/{hi}'))
    df = pd.concat(dfs, ignore_index=True)
    df.to_csv(RES / 'd4_canny.csv', index=False)
    if vis:
        show([v[0] for v in vis], [v[1] for v in vis], cols=len(show_ids) or 1, size=3,
             path=RES / 'fig' / 'd4_canny.png')
    summ = df.groupby(['canny', 'yelek'])['canny_orani'].mean().round(3)
    log_experiment('D4 Canny eşikleri', kisi, ','.join(ids), P['experiments']['D4'],
                   {f'{k[0]} yelek={k[1]}': v for k, v in summ.items()}, 'YORUM: notta yazılacak')
    return df


# ------------------------------------------------------------------- D6 (D)
def d6(P, gt, kisi='D'):
    """Eşleştirme eşiği: oran testi 0,6/0,75/0,9 YA DA RANSAC 1/3/5 px (params.experiments.D6.mode)."""
    import features
    F, X = P['features'], P['experiments']['D6']
    pair = features.sift_detect(features.make_pair(P, gt))
    rows = []
    if X['mode'] == 'ratio':
        for r in X['ratios']:
            rows.append(features.run_pair(pair, r, F['ransac_px'], F['model']))
    else:
        for px in X['ransac_px']:
            rows.append(features.run_pair(pair, F['sift_ratio'], px, F['model']))
    df = pd.DataFrame(rows)
    ensure_dirs()
    df.to_csv(RES / 'd6_eslestirme.csv', index=False)
    log_experiment('D6 eşleştirme eşiği', kisi, F['dev_id'], X,
                   df[['oran_testi', 'ransac_px', 'gecen_eslesme', 'ic_deger', 'kose_hatasi_px']].to_dict('records'),
                   'YORUM: notta yazılacak')
    return df


# ------------------------------------------------------------------- D8 (E)
def diffuse(img, steps, dt=0.20):
    """Doğrusal (ısı) difüzyonu, açık Euler: u <- u + dt * Laplace(u). Her renk kanalı ayrı.
    t = steps*dt birim süre; sürekli çözüm σ = sqrt(2t) olan Gauss ile aynıdır (40×0,20 = 8 -> σ = 4)."""
    out = []
    for c in range(3):
        u = img[..., c].astype(np.float32)
        for _ in range(steps):
            u = u + dt * cv2.Laplacian(u, cv2.CV_32F, ksize=1, borderType=cv2.BORDER_REFLECT)
        out.append(u)
    return np.clip(np.rint(np.dstack(out)), 0, 255).astype(np.uint8)   # HSV'den önce 0–255, tam sayı


def d8(ids, gt, P, kisi='E', show_id=None):
    """Difüzyon süresi 0/10/40 adım; gövde maske oranı ve gövdedeki kenar oranı. 40 adım vs Gauss σ=4."""
    check_ids_allowed(ids, P)
    ensure_dirs()
    X = P['experiments']['D8']
    E = entries(gt)
    rows, vis = [], []
    for img_id in ids:
        img, g = load_img(img_id), E[img_id]
        d40 = None
        for n in X['steps']:
            d = diffuse(img, n, X['dt'])
            if n == max(X['steps']):
                d40 = d
            rows.append({'id': img_id, 'islem': f'difüzyon {n} adım', 't': n * X['dt'], **_metrics(d, g, P)})
            if img_id == show_id:
                vis.append((d, f'difüzyon {n} adım'))
        gs = cv2.GaussianBlur(img, (0, 0), X['gauss_sigma'])
        m = _metrics(gs, g, P)
        m['fark_difuzyon40_mae'] = float(np.abs(gs.astype(np.int16) - d40.astype(np.int16)).mean())
        rows.append({'id': img_id, 'islem': f"Gauss σ={X['gauss_sigma']}", 't': None, **m})
        if img_id == show_id:
            vis.append((gs, f"Gauss σ={X['gauss_sigma']}"))
            t = selected_torso(g)
            if t:
                x1, y1, x2, y2 = t
                vis = [(v[y1:y2, x1:x2], ttl) for v, ttl in vis]
    df = pd.DataFrame(rows)
    df.to_csv(RES / 'd8_difuzyon.csv', index=False)
    if vis:
        show([v[0] for v in vis], [v[1] for v in vis], cols=len(vis), size=3, path=RES / 'fig' / f'd8_{show_id}.png')
    log_experiment('D8 difüzyon süresi', kisi, ','.join(ids), X,
                   df.groupby('islem')[['govde_maske_orani', 'canny_orani']].mean().round(3).to_dict(),
                   'YORUM: notta yazılacak')
    return df
