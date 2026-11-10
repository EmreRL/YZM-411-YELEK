"""Paket B — 5. adım: renk tabanlı başlangıç yöntemi, filtre, parçalar, karar kuralı, TP/FP/FN.

Akış: filtre (5b) -> HSV -> iki aralık maskesi (5a) -> 3x3 açma (5b) -> bağlı bileşenler (5d)
      -> karar kuralı (5e, sıra değişmez) -> IoU eşleme (5f) -> doğru sınıf (5g)
"""
import cv2
import numpy as np
import pandas as pd

from common import (RES, CLASSES, check_ids_allowed, ensure_dirs, entries, intersects,
                    load_img, match_iou, selected_torso, show, torsos, tpfpfn_ids,
                    vest_boxes, draw_boxes)


# --------------------------------------------------------------------- 5b
def apply_filter(img, f):
    n = f['name']
    if n == 'none':
        return img
    if n == 'gauss':
        if f.get('sigma'):
            return cv2.GaussianBlur(img, (0, 0), f['sigma'])
        return cv2.GaussianBlur(img, (f['k'], f['k']), 0)
    if n == 'median':
        return cv2.medianBlur(img, f['k'])
    if n == 'bilateral':
        return cv2.bilateralFilter(img, f['d'], f['sc'], f['ss'])
    raise ValueError(f'bilinmeyen filtre: {n}')


# --------------------------------------------------------------------- 5a
def raw_mask(hsv, P):
    lo, hi = P['hsv_yellow']
    m = cv2.inRange(hsv, np.array(lo, np.uint8), np.array(hi, np.uint8))
    for lo, hi in P['hsv_orange']:                       # H = 0'ın iki yanı
        m |= cv2.inRange(hsv, np.array(lo, np.uint8), np.array(hi, np.uint8))
    return m


def color_mask(img, P, pre_filter=None):
    """Maske (0/255) döndürür. pre_filter verilirse params'takinin yerine kullanılır (D2)."""
    f = pre_filter if pre_filter is not None else P['pre_filter']
    hsv = cv2.cvtColor(apply_filter(img, f), cv2.COLOR_BGR2HSV)
    m = raw_mask(hsv, P)
    k = P['open_kernel']
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((k, k), np.uint8))   # 3x3 açma
    return m


# --------------------------------------------------------------------- 5d
def parts(m, min_pct):
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    A = m.shape[0] * m.shape[1]
    out = []
    for i in range(1, n):                                 # 0 = arka plan
        x, y, w, h, area = st[i]
        if 100.0 * area / A >= min_pct:
            out.append({'box': [int(x), int(y), int(x + w), int(y + h)], 'area': int(area)})
    return out


def keep_parts_mask(m, prt):
    """Yalnız eşik üstü parçalardan oluşan maske (oranlar bu maskeyle hesaplanır)."""
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    keep = np.zeros(n, bool)
    boxes = {tuple(p['box']) for p in prt}
    for i in range(1, n):
        x, y, w, h, _ = st[i]
        if (int(x), int(y), int(x + w), int(y + h)) in boxes:
            keep[i] = True
    return (keep[lab] * 255).astype(np.uint8)


# --------------------------------------------------------------------- 5e
def torso_ratio(m, torso):
    if torso is None:
        return None
    x1, y1, x2, y2 = torso
    roi = m[y1:y2, x1:x2]
    return float((roi > 0).mean()) if roi.size else None


def decide(m, v_channel, prt, g, R):
    """Kural sırası değişmez; ilk sağlanan koşulda durur. (sınıf, gövde oranı, gerekçe)"""
    torso = selected_torso(g)
    if torso is None:
        return CLASSES[3], None, 'i: seçilen kişinin gövde kutusu yok'
    x1, y1, x2, y2 = torso
    ratio = torso_ratio(m, torso)
    h = y2 - y1
    mean_v = float(v_channel[y1:y2, x1:x2].mean())
    if h < R['min_torso_h']:
        return CLASSES[3], ratio, f'i: gövde yüksekliği {h}px < {R["min_torso_h"]}'
    if mean_v < R['min_mean_v']:
        return CLASSES[3], ratio, f'i: gövde ortalama V {mean_v:.0f} < {R["min_mean_v"]}'
    if ratio >= R['worn_ratio']:
        return CLASSES[0], ratio, f'ii: gövde maske oranı {ratio:.3f} >= {R["worn_ratio"]}'
    all_t = [p['torso'] for _, p in torsos(g)]
    free = [p for p in prt if not any(intersects(p['box'], t) for t in all_t)]
    t_area = (x2 - x1) * h
    if free:
        big = max(p['area'] for p in free)
        if big > R['unworn_ratio'] * t_area:
            return CLASSES[1], ratio, f'iii: gövdesiz en büyük parça {big}px > {R["unworn_ratio"]}×{t_area}'
    return CLASSES[2], ratio, 'iv: hiçbiri'


# ---------------------------------------------------------------- bir görüntü
def run_one(img, g, P, pre_filter=None):
    m0 = color_mask(img, P, pre_filter)
    prt = parts(m0, P['min_part_area_pct'])
    # 5c oranları açmadan sonraki maskeden hesaplanır (5c, 5d'den önce gelir);
    # params'ta ratio_after_parts=true ise küçük parçalar atıldıktan sonraki maske kullanılır.
    m = keep_parts_mask(m0, prt) if P.get('ratio_after_parts', False) else m0
    v = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[..., 2]      # V filtresiz görüntüden
    cls, ratio, why = decide(m, v, prt, g, P['rule'])
    tp, fp, fn, matched = match_iou([p['box'] for p in prt], vest_boxes(g), P['iou_thr'])
    return {'mask': m, 'mask_raw': m0, 'parts': prt, 'class': cls, 'torso_ratio': ratio,
            'mask_ratio': float((m > 0).mean()), 'reason': why,
            'tp': tp, 'fp': fp, 'fn': fn, 'matched': matched}


def run(ids, gt, P, save=True, tag='color'):
    """5c–5g. Dondurmadan önce yalnız geliştirme görüntüleri çalışır."""
    check_ids_allowed(ids, P)
    ensure_dirs()
    E = entries(gt)
    count_set = set(tpfpfn_ids(gt))
    rows = []
    for img_id in ids:
        g, img = E[img_id], load_img(img_id)
        r = run_one(img, g, P)
        counted = img_id.startswith('G-') or img_id in count_set
        rows.append({'id': img_id, 'dogru_sinif': g['class'], 'kural_sinifi': r['class'],
                     'dogru_mu': g['class'] == r['class'],
                     'maske_alan_orani': r['mask_ratio'], 'govde_maske_orani': r['torso_ratio'],
                     'parca_sayisi': len(r['parts']), 'gerekce': r['reason'],
                     'tpfpfn_sayima_dahil': counted,
                     'tp': r['tp'], 'fp': r['fp'], 'fn': r['fn']})
        if save:
            cv2.imwrite(str(RES / 'masks' / f'{img_id}.png'), r['mask'])
            vis = draw_boxes(img, g, extra=[p['box'] for p in r['parts']])
            overlay = vis.copy()
            overlay[r['mask'] > 0] = (0.5 * overlay[r['mask'] > 0] + [0, 0, 127]).astype(np.uint8)
            cv2.imwrite(str(RES / 'masks' / f'{img_id}_overlay.jpg'), overlay)
    df = pd.DataFrame(rows)
    if save:
        df.to_csv(RES / f'{tag}.csv', index=False)
    return df


def summary(df):
    """5f toplamları yalnız sayıma dahil görüntülerde; 5g doğru sınıf sayısı."""
    c = df[df['tpfpfn_sayima_dahil']]
    out = {'gorsel': len(df), 'dogru_sinif': int(df['dogru_mu'].sum()),
           'TP': int(c['tp'].sum()), 'FP': int(c['fp'].sum()), 'FN': int(c['fn'].sum()),
           'sayilan_gorsel': list(c['id'])}
    print(f"Doğru sınıf: {out['dogru_sinif']}/{out['gorsel']} | "
          f"TP/FP/FN ({len(c)} görüntü): {out['TP']}/{out['FP']}/{out['FN']}")
    return out


def confusion(df):
    return pd.crosstab(pd.Categorical(df['dogru_sinif'], CLASSES), pd.Categorical(df['kural_sinifi'], CLASSES),
                       rownames=['doğru'], colnames=['kural'], dropna=False)


# ------------------------------------------------- 5a: eşik belirleme yardımı
def hsv_stats(ids, gt, s_min=80, v_min=80):
    """YALNIZ geliştirme görüntüleri: yelek kutuları içindeki doygun piksellerin H/S/V dağılımı.

    Yelek kutusunda şerit ve gölge de olduğu için yalnız S>=s_min ve V>=v_min pikseller alınır.
    Karşılaştırma için yeleksiz gövdelerin ve kutu dışının dağılımı da verilir.
    """
    assert all(i.startswith('G-') for i in ids), 'Eşikler yalnız geliştirme görüntülerinde belirlenir (5e)'
    E = entries(gt)
    rows, hists = [], {'yelek': [], 'yeleksiz_govde': [], 'arka_plan': []}
    for img_id in ids:
        g, img = E[img_id], load_img(img_id)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        inside = np.zeros(img.shape[:2], bool)
        for b in vest_boxes(g):
            inside[b[1]:b[3], b[0]:b[2]] = True
        bare = np.zeros_like(inside)
        for _, p in torsos(g):
            if not p.get('vest'):
                x1, y1, x2, y2 = p['torso']
                bare[y1:y2, x1:x2] = True
        bare &= ~inside
        sat = (hsv[..., 1] >= s_min) & (hsv[..., 2] >= v_min)
        for name, reg in [('yelek', inside), ('yeleksiz_govde', bare), ('arka_plan', ~inside & ~bare)]:
            px = hsv[reg & sat]
            hists[name].append(px)
            if len(px):
                q = np.percentile(px, [5, 50, 95], axis=0)
                rows.append({'id': img_id, 'bolge': name, 'n_px': len(px),
                             'H_p5': q[0, 0], 'H_p50': q[1, 0], 'H_p95': q[2, 0],
                             'S_p5': q[0, 1], 'S_p50': q[1, 1], 'V_p5': q[0, 2], 'V_p50': q[1, 2]})
    return pd.DataFrame(rows), {k: (np.concatenate(v) if v else np.zeros((0, 3))) for k, v in hists.items()}


def plot_hue(hists, P=None, path=None):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 3.2))
    for name, px in hists.items():
        if len(px):
            ax.hist(px[:, 0], bins=180, range=(0, 180), histtype='step', density=True, label=name)
    if P:
        lo, hi = P['hsv_yellow']
        ax.axvspan(lo[0], hi[0], color='gold', alpha=.2, label='sarı aralık')
        for lo, hi in P['hsv_orange']:
            ax.axvspan(lo[0], hi[0], color='orange', alpha=.2)
    ax.set_xlabel('H (OpenCV, 0–179)')
    ax.set_ylabel('yoğunluk')
    ax.legend()
    fig.tight_layout()
    if path:
        ensure_dirs()
        fig.savefig(path, dpi=110)
    return fig


def show_masks(ids, gt, P, path=None):
    E = entries(gt)
    imgs, titles = [], []
    for img_id in ids:
        img = load_img(img_id)
        r = run_one(img, E[img_id], P)
        imgs += [draw_boxes(img, E[img_id], [p['box'] for p in r['parts']]), r['mask']]
        tr = '—' if r['torso_ratio'] is None else f"{r['torso_ratio']:.2f}"
        titles += [f"{img_id} doğru: {E[img_id]['class']}", f"kural: {r['class']} | gövde {tr}"]
    return show(imgs, titles, cols=6, size=2.6, path=path)
