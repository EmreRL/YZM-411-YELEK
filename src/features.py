"""Paket D — 7. adım: öznitelikler.

7a (bilinen dönüşüm): yelek kırpıntısı A, belirli açı/ölçekle B'ye dönüştürülür; dönüşüm baştan bilinir.
    SIFT -> oran testi (0,75) -> RANSAC (3 px) -> üç sonuç: geçen eşleşme, iç değer, köşe hatası.
7b: A'da en güçlü 50 SIFT noktası (düz / kenar / köşe ayrımı), isteğe bağlı Shi–Tomasi, gövdede HOG.
Nokta sayısının çok olması tek başına başarı göstermez.
"""
import json

import cv2
import numpy as np

from common import RES, check_ids_allowed, ensure_dirs, entries, load_img, show, vest_boxes


# --------------------------------------------------------------------- 7a
def make_pair(P, gt):
    F = P['features']
    g = entries(gt)[F['dev_id']]
    x1, y1, x2, y2 = vest_boxes(g)[F['vest_idx']]
    A = load_img(F['dev_id'])[y1:y2, x1:x2].copy()
    h, w = A.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), F['angle_deg'], F['scale'])
    c, s = abs(M[0, 0]), abs(M[0, 1])
    nw, nh = int(h * s + w * c) + 1, int(h * c + w * s) + 1
    M[0, 2] += nw / 2 - w / 2                              # B kesilmesin diye tuval kaydırılır
    M[1, 2] += nh / 2 - h / 2
    B = cv2.warpAffine(A, M, (nw, nh))
    corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
    return {'A': A, 'B': B, 'M': M, 'corners': corners, 'known': cv2.transform(corners, M),
            'box': [x1, y1, x2, y2]}


def sift_detect(pair):
    sift = cv2.SIFT_create()
    ka, da = sift.detectAndCompute(cv2.cvtColor(pair['A'], cv2.COLOR_BGR2GRAY), None)
    kb, db = sift.detectAndCompute(cv2.cvtColor(pair['B'], cv2.COLOR_BGR2GRAY), None)
    knn = cv2.BFMatcher(cv2.NORM_L2).knnMatch(da, db, k=2) if da is not None and db is not None else []
    pair.update(ka=ka, kb=kb, knn=knn)
    return pair


def run_pair(pair, ratio=0.75, ransac_px=3.0, model='homography'):
    """Üç sonuç (7a): oran testinden geçen, RANSAC iç değeri, ortalama köşe hatası (px)."""
    ka, kb = pair['ka'], pair['kb']
    good = [p[0] for p in pair['knn'] if len(p) == 2 and p[0].distance < ratio * p[1].distance]
    out = {'oran_testi': ratio, 'ransac_px': ransac_px, 'model': model,
           'kp_A': len(ka), 'kp_B': len(kb), 'gecen_eslesme': len(good),
           'ic_deger': 0, 'kose_hatasi_px': None}
    need = 4 if model == 'homography' else 2
    if len(good) < need:
        return out
    src = np.float32([ka[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst = np.float32([kb[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    if model == 'homography':
        H, inl = cv2.findHomography(src, dst, cv2.RANSAC, ransac_px)
        if H is None:
            return out
        est = cv2.perspectiveTransform(pair['corners'], H)
    else:
        Me, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=ransac_px)
        if Me is None:
            return out
        est = cv2.transform(pair['corners'], Me)
        out['kestirilen_aci'] = float(np.degrees(np.arctan2(Me[0, 1], Me[0, 0])))  # OpenCV açısıyla aynı işaret
        out['kestirilen_olcek'] = float(np.hypot(Me[0, 0], Me[0, 1]))
    err = np.linalg.norm(pair['known'].reshape(-1, 2) - est.reshape(-1, 2), axis=1)
    out.update(ic_deger=int(inl.sum()), kose_hatasi_px=float(err.mean()),
               kose_hatalari_px=[round(float(e), 2) for e in err])
    pair['last_good'], pair['last_inl'] = good, inl
    return out


def draw_matches(pair, path=None):
    good, inl = pair.get('last_good', []), pair.get('last_inl')
    mask = inl.ravel().tolist() if inl is not None else None
    vis = cv2.drawMatches(pair['A'], pair['ka'], pair['B'], pair['kb'], good, None,
                          matchesMask=mask, matchColor=(0, 255, 0), singlePointColor=(120, 120, 120),
                          flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    est_poly = pair['known'].reshape(-1, 2) + [pair['A'].shape[1], 0]
    cv2.polylines(vis, [est_poly.astype(np.int32)], True, (255, 0, 0), 2)  # bilinen köşeler (mavi)
    return show([vis], ['iç değer eşleşmeleri (yeşil), B\'de bilinen köşeler (mavi)'], cols=1, size=8, path=path)


# --------------------------------------------------------------------- 7b
def structure_eigs(gray, pt, sigma=2.0):
    """Noktanın çevresinde yapı tensörünün özdeğerleri (l1 >= l2): düz / kenar / köşe ayrımına yardım eder."""
    x, y = int(round(pt[0])), int(round(pt[1]))
    r = int(3 * sigma) + 2
    patch = gray[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1].astype(np.float32)
    if patch.shape[0] < 5 or patch.shape[1] < 5:
        return 0.0, 0.0
    gx = cv2.Sobel(patch, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(patch, cv2.CV_32F, 0, 1, ksize=3)
    w = cv2.getGaussianKernel(patch.shape[0], sigma) @ cv2.getGaussianKernel(patch.shape[1], sigma).T
    a, b, c = (w * gx * gx).sum(), (w * gx * gy).sum(), (w * gy * gy).sum()
    tr, det = a + c, a * c - b * b
    disc = np.sqrt(max(tr * tr / 4 - det, 0))
    l1, l2 = tr / 2 + disc, tr / 2 - disc
    return float(l1), float(l2)


def top_keypoints(P, gt, pair=None, path=None):
    """A üzerinde en güçlü K SIFT noktası; her nokta için yapı tensörü oranı ve renk maskesi üstünde mi."""
    from color import color_mask
    F = P['features']
    pair = pair or sift_detect(make_pair(P, gt))
    A = pair['A']
    gray = cv2.cvtColor(A, cv2.COLOR_BGR2GRAY)
    top = sorted(pair['ka'], key=lambda k: k.response, reverse=True)[:F.get('top_k', 50)]
    cm = color_mask(A, P)
    l1s = []
    stats = []
    for k in top:
        l1, l2 = structure_eigs(gray, k.pt)
        l1s.append(l1)
        stats.append((k, l1, l2))
    hi = np.percentile(l1s, 50) if l1s else 0      # göreli eşik: bu kırpıntıdaki medyan
    counts = {'düz': 0, 'kenar': 0, 'köşe': 0}
    on_mask = 0
    for k, l1, l2 in stats:
        if l1 < 0.1 * hi:
            t = 'düz'
        elif l2 / (l1 + 1e-9) < 0.15:
            t = 'kenar'
        else:
            t = 'köşe'
        counts[t] += 1
        x, y = int(k.pt[0]), int(k.pt[1])
        on_mask += int(cm[min(y, cm.shape[0] - 1), min(x, cm.shape[1] - 1)] > 0)
    vis = cv2.drawKeypoints(A, top, None, flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
    pts = cv2.goodFeaturesToTrack(gray, F.get('top_k', 50), 0.01, 10)
    st = A.copy()
    if pts is not None:
        for p in pts.reshape(-1, 2):
            cv2.circle(st, (int(p[0]), int(p[1])), 3, (0, 0, 255), -1)
    ensure_dirs()
    cv2.imwrite(str(RES / 'fig' / 'sift_top50.png'), vis)
    cv2.imwrite(str(RES / 'fig' / 'shi_tomasi.png'), st)
    show([vis, st, cm], [f'en güçlü {len(top)} SIFT', 'Shi–Tomasi (isteğe bağlı)', 'renk maskesi (yalnız yorum için)'],
         cols=3, size=4, path=path)
    return {'top_k': len(top), 'yapi_tensoru': counts, 'renk_maskesi_ustunde': on_mask,
            '_not': 'Düz/kenar/köşe ayrımı yapı tensörü özdeğerleriyle yardımcı ölçüdür; görsel yorumla birlikte yazın.'}


def hog_torso(img, torso, P):
    from skimage.feature import hog
    H = P['features']['hog']
    x1, y1, x2, y2 = torso
    crop = cv2.cvtColor(img[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
    fd, hog_img = hog(crop, orientations=H['orientations'], pixels_per_cell=tuple(H['pixels_per_cell']),
                      cells_per_block=tuple(H['cells_per_block']), visualize=True, feature_vector=False)
    energy = fd.reshape(-1, H['orientations']).sum(axis=0)
    energy = energy / energy.sum() if energy.sum() > 0 else energy
    centers = [(i + 0.5) * 180 / H['orientations'] for i in range(H['orientations'])]
    return crop, hog_img, dict(zip([round(c, 1) for c in centers], [round(float(e), 3) for e in energy]))


def hog_compare(items, gt, P, path=None):
    """items = [(img_id, kisi_indeksi), ...]. Gradyan yönü 90° civarı = yatay kenar (yatay şerit)."""
    import matplotlib.pyplot as plt
    check_ids_allowed([i for i, _ in items], P)
    E = entries(gt)
    out = {}
    fig, axes = plt.subplots(len(items), 3, figsize=(11, 3.2 * len(items)), squeeze=False)
    for r, (img_id, k) in enumerate(items):
        g = E[img_id]
        p = g['persons'][k]
        crop, hv, energy = hog_torso(load_img(img_id), p['torso'], P)
        out[f'{img_id}/P{k}'] = {'yelek': bool(p.get('vest')), 'yon_enerjisi': energy}
        axes[r, 0].imshow(crop, cmap='gray'); axes[r, 0].set_title(f'{img_id} P{k} yelek={p.get("vest")}')
        axes[r, 1].imshow(hv, cmap='magma'); axes[r, 1].set_title('HOG')
        axes[r, 2].bar(list(energy.keys()), list(energy.values()), width=15)
        axes[r, 2].set_xlabel('gradyan yönü (°), 90° = yatay kenar'); axes[r, 2].set_ylim(0, max(0.35, max(energy.values())))
        for a in axes[r, :2]:
            a.axis('off')
    fig.tight_layout()
    if path:
        ensure_dirs()
        fig.savefig(path, dpi=110)
    return out


def run_all(P, gt, hog_items=None, save=True):
    """7a + 7b'nin sayısal sonuçlarını results/features.json'a yazar."""
    ensure_dirs()
    F = P['features']
    pair = sift_detect(make_pair(P, gt))
    res = {'dev_id': F['dev_id'], 'yelek_kutusu': pair['box'], 'aci_deg': F['angle_deg'], 'olcek': F['scale'],
           '7a': run_pair(pair, F['sift_ratio'], F['ransac_px'], F['model'])}
    draw_matches(pair, path=RES / 'fig' / 'sift_matches.png')
    res['7b_sift'] = top_keypoints(P, gt, pair, path=RES / 'fig' / 'sift_top50_panel.png')
    if hog_items:
        res['7b_hog'] = hog_compare(hog_items, gt, P, path=RES / 'fig' / 'hog.png')
    if save:
        with open(RES / 'features.json', 'w', encoding='utf-8') as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
    return res, pair
