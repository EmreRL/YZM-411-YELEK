"""Paket C — 6a: Sobel ve Canny ile şerit kanıtı.

Canny TÜM görüntüde hesaplanır, kenar pikselleri gövde kutusunda sayılır
(kırpıntıda hesaplanırsa kırpma sınırı sahte kenar verir).
Yatay bir şerit y yönünde yoğunluk değiştirir, bu yüzden Gy (Sobel y) güçlü yanıt verir.
"""
import cv2
import numpy as np
import pandas as pd

from common import RES, check_ids_allowed, ensure_dirs, entries, load_img, show


def gradients(img, canny=(50, 150), ksize=3):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=ksize)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=ksize)
    edges = cv2.Canny(gray, int(canny[0]), int(canny[1]))
    return gray, gx, gy, edges


def edge_stats(edges, gx, gy, t):
    x1, y1, x2, y2 = t
    area = (x2 - x1) * (y2 - y1)
    canny_ratio = float((edges[y1:y2, x1:x2] > 0).sum() / area)
    sx = float(np.abs(gx[y1:y2, x1:x2]).sum())
    sy = float(np.abs(gy[y1:y2, x1:x2]).sum())
    return canny_ratio, (sy / sx if sx > 0 else np.nan)


def run(ids, gt, P, canny=None, save=True, tag='edge'):
    """Görüntüdeki BÜTÜN gövdeler için satır; yelekli/yeleksiz ayrımı gt.json 'vest' alanından."""
    check_ids_allowed(ids, P)
    ensure_dirs()
    canny = canny or P['canny']
    E = entries(gt)
    rows = []
    for img_id in ids:
        g, img = E[img_id], load_img(img_id)
        _, gx, gy, edges = gradients(img, canny, P.get('sobel_ksize', 3))
        for i, p in enumerate(g.get('persons', [])):
            if not p.get('torso'):
                continue
            c, r = edge_stats(edges, gx, gy, p['torso'])
            rows.append({'id': img_id, 'ayirim': g['split'], 'kisi': i,
                         'secilen': i == g.get('selected'), 'yelek': bool(p.get('vest')),
                         'canny_orani': c, 'gy_gx': r, 'canny': f'{canny[0]}/{canny[1]}'})
        if save:
            cv2.imwrite(str(RES / 'fig' / f'{tag}_{img_id}.png'), edges)
    df = pd.DataFrame(rows)
    if save:
        df.to_csv(RES / f'{tag}.csv', index=False)
    return df


def side_by_side(df):
    """6a: yelekli ve yeleksiz kişiler yan yana (ortalama, medyan, sayı)."""
    return df.groupby('yelek')[['canny_orani', 'gy_gx']].agg(['count', 'mean', 'median']).round(3)


def show_sobel(img_id, gt, P, path=None):
    """Bir görüntüde |Gx|, |Gy| ve Canny; yatay şeritlerin hangi türevde güçlü olduğunu gösterir."""
    g, img = entries(gt)[img_id], load_img(img_id)
    gray, gx, gy, edges = gradients(img, P['canny'], P.get('sobel_ksize', 3))
    t = g['persons'][g['selected']]['torso']
    x1, y1, x2, y2 = t

    def crop(a):
        a = np.abs(a[y1:y2, x1:x2])
        return cv2.normalize(a, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    return show([img[y1:y2, x1:x2], crop(gx), crop(gy), edges[y1:y2, x1:x2]],
                [f'{img_id} gövde', '|Gx| (dikey kenarlar)', '|Gy| (yatay kenarlar)', 'Canny (tüm görüntüden)'],
                cols=4, size=3.2, path=path)
