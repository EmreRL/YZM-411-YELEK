"""Ortak fonksiyonlar (Paket E).

Bütün paketler veriyi, kutuları ve dondurulmuş ayarları buradan okur.
Böylece herkes aynı görüntü kimliklerini, aynı gt.json'u ve aynı params.json'u kullanır.

Proje yalnız Google Drive'da yaşar (GitHub yok). Git commit'inin yerini kayit_al() tutar:
dosyanın zaman damgalı kopyası ve SHA-256 özeti kayitlar/ klasörüne yazılır.
"""
import csv
import hashlib
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
RAW_DIR = DATA / 'images'          # takımın Drive'a yüklediği ham görüntüler: gelistirme/, kontrol/ (+ *-etiketli/)
IMG_DIR = DATA / 'images_1024'     # küçültülmüş görüntüler G-1.png … (hazirlik.goruntuleri_hazirla üretir)
RES = ROOT / 'results'
CFG = ROOT / 'config' / 'params.json'
GT_PATH = DATA / 'gt.json'
KAYIT = ROOT / 'kayitlar'          # dondurma ve tahmin kayıtları (commit yerine)

CLASSES = ['Yelek giyili', 'Yelek var, giyili değil', 'Yelek yok', 'Belirsiz']
DEV_IDS = [f'G-{i}' for i in range(1, 9)]
CTRL_IDS = [f'K-{i}' for i in range(1, 13)]


# ----------------------------------------------------------------- dosyalar
def ensure_dirs():
    for d in [RES, RES / 'masks', RES / 'fig']:
        d.mkdir(parents=True, exist_ok=True)


def imread_u(path):
    """Türkçe karakterli yollarda da çalışan imread (data/docs/kutu-cizer.ipynb ile aynı okuma)."""
    data = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR) if data.size else None


def imwrite_u(path, img):
    ok, buf = cv2.imencode(Path(path).suffix.lower(), img)
    if not ok:
        raise IOError(f'yazılamadı: {path}')
    buf.tofile(str(path))


def load_img(img_id):
    """Küçültülmüş görüntüyü (BGR) okur. Görüntüler hazirlik.goruntuleri_hazirla() ile üretilir."""
    for ext in ('.png', '.jpg', '.jpeg'):
        p = IMG_DIR / f'{img_id}{ext}'
        if p.exists():
            img = imread_u(p)
            if img is None:
                raise IOError(f'{p} okunamadı')
            if max(img.shape[:2]) > 1024:
                raise ValueError(f'{img_id}: uzun kenar 1024 pikseli geçiyor (2d); '
                                 'hazirlik.goruntuleri_hazirla(force=True) çalıştırın')
            return img
    raise FileNotFoundError(f'{img_id} için data/images_1024 içinde görüntü yok; '
                            'önce: import hazirlik; hazirlik.goruntuleri_hazirla()')


def load_gt(path=GT_PATH):
    with open(path, encoding='utf-8') as f:
        gt = json.load(f)
    return gt


def entries(gt):
    """'_meta' dışındaki görüntü kayıtları."""
    return {k: v for k, v in gt.items() if not k.startswith('_')}


def load_params(path=CFG):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def save_params(P, path=CFG):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(P, f, ensure_ascii=False, indent=2)


def freeze_params(path=CFG):
    """Dondurma 2: B eşikleri belirledikten sonra çağırır (5e).
    params.json'un o anki hâli kayitlar/ altına kopyalanır; commit'e gerek yoktur."""
    P = load_params(path)
    if P.get('_frozen'):
        print('params.json zaten dondurulmuş:', P.get('_frozen_at'))
        return P
    P['_frozen'] = True
    P['_frozen_at'] = datetime.now().isoformat(timespec='seconds')
    save_params(P, path)
    kayit_al(path, etiket='dondurma-2', not_='params.json donduruldu (5e)')
    print('params.json donduruldu:', P['_frozen_at'], '-> bundan sonra eşik değişmez.')
    return P


def _frozen_snapshot():
    """Dondurma 2'de alınan params.json kopyası (yoksa None)."""
    for r in reversed(kayitlar()):
        if r['etiket'] == 'dondurma-2' and r['dosya'] == 'config/params.json':
            p = ROOT / r['kopya']
            if p.exists():
                with open(p, encoding='utf-8') as f:
                    return json.load(f)
    return None


def check_ids_allowed(ids, P):
    """Dondurmadan önce kontrol görüntüsü çalıştırılmasını engeller (5e).
    Dondurmadan sonra params, kayitlar/'daki dondurma kopyasından farklıysa uyarır."""
    ctrl = [i for i in ids if i.startswith('K-')]
    if not ctrl:
        return
    if not P.get('_frozen', False):
        raise RuntimeError(
            'params.json dondurulmadı (_frozen=false). Kontrol görüntüleri ancak '
            'Dondurma 2 sonrasında çalıştırılır (5e). Şu an yalnız G-1…G-8 kullanın.')
    snap = _frozen_snapshot()
    if snap is not None and snap != P:
        fark = sorted(k for k in set(snap) | set(P) if snap.get(k) != P.get(k))
        print('UYARI: kullanılan ayarlar Dondurma 2 kopyasından farklı (5e):', ', '.join(fark),
              '\n  Bu bir "sonraki kontrol"dür; sonucu merge.add_followup() ile ayrı satır yapın (9b).')


# ----------------------------------------------------------- gt yardımcıları
def selected_person(g):
    sel = g.get('selected')
    if sel is None or sel >= len(g.get('persons', [])):
        return None
    return g['persons'][sel]


def selected_torso(g):
    p = selected_person(g)
    return None if p is None else p.get('torso')


def vest_boxes(g):
    out = []
    for v in g.get('vests', []):
        out.append(v['box'] if isinstance(v, dict) else v)
    return out


def torsos(g):
    """(indeks, kişi) çiftleri, yalnız gövde kutusu olan kişiler."""
    return [(i, p) for i, p in enumerate(g.get('persons', [])) if p.get('torso')]


def validate_gt(gt, check_images=True):
    """Dondurma 1'den önce A çalıştırır: eksik kutu, ters kutu, sınır dışı kutu, seçim hatası."""
    problems = []
    ents = entries(gt)
    for img_id in DEV_IDS + CTRL_IDS:
        if img_id not in ents:
            problems.append(f'{img_id}: gt.json içinde yok')
    for img_id, g in ents.items():
        if g.get('class') not in CLASSES:
            problems.append(f'{img_id}: sınıf geçersiz: {g.get("class")!r}')
        persons = g.get('persons', [])
        if not persons:
            problems.append(f'{img_id}: kişi yok (2b: her görüntüde en az bir kişi)')
        sel = g.get('selected')
        if sel is None or not (0 <= sel < len(persons)):
            if g.get('class') != 'Belirsiz':
                problems.append(f'{img_id}: seçilen kişi geçersiz ({sel})')
        shape = None
        if check_images:
            try:
                shape = load_img(img_id).shape
            except Exception as e:  # noqa: BLE001
                problems.append(f'{img_id}: görüntü okunamadı ({e})')
        boxes = [('gövde', i, p.get('torso')) for i, p in enumerate(persons)] + \
                [('yelek', j, b) for j, b in enumerate(vest_boxes(g))]
        for kind, k, b in boxes:
            if b is None:
                continue
            x1, y1, x2, y2 = b
            if not (x2 > x1 and y2 > y1):
                problems.append(f'{img_id}: {kind}{k} ters/boş kutu {b}')
            if shape is not None and (x1 < 0 or y1 < 0 or x2 > shape[1] or y2 > shape[0]):
                problems.append(f'{img_id}: {kind}{k} görüntü dışına taşıyor {b} / {shape[1]}x{shape[0]}')
        for j, v in enumerate(g.get('vests', [])):
            wb = v.get('worn_by') if isinstance(v, dict) else None
            if wb is not None and not (0 <= wb < len(persons) and persons[wb].get('vest')):
                problems.append(f'{img_id}: yelek{j} worn_by={wb} ama o kişinin vest alanı true değil')
        if g.get('class') == 'Yelek giyili' and sel is not None and 0 <= sel < len(persons) \
                and not persons[sel].get('vest'):
            problems.append(f'{img_id}: sınıf "Yelek giyili" ama seçilen kişinin vest=false')
        if g.get('class') == 'Yelek var, giyili değil':
            free = [v for v in g.get('vests', []) if isinstance(v, dict) and v.get('worn_by') is None]
            if not free:
                problems.append(f'{img_id}: sınıf "Yelek var, giyili değil" ama worn_by=null yelek kutusu yok')
    ids = gt.get('_meta', {}).get('tpfpfn_ids') or []
    if len(ids) not in (0, 6):
        problems.append(f'_meta.tpfpfn_ids {len(ids)} görüntü içeriyor; 5f altı görüntü diyor')
    print('gt.json kontrolü:', 'sorun yok' if not problems else f'{len(problems)} sorun')
    for p in problems:
        print('  -', p)
    return problems


def tpfpfn_ids(gt):
    """5f: TP/FP/FN sayımına dahil kontrol görüntüleri. Boşsa bütün kontrol seti."""
    ids = gt.get('_meta', {}).get('tpfpfn_ids') or []
    return ids if ids else CTRL_IDS


# ------------------------------------------------------------------ geometri
def resize_max1024(img):
    """Uzun kenar 1024'ü geçmesin; küçükler büyütülmez (2d)."""
    h, w = img.shape[:2]
    s = 1024 / max(h, w)
    if s >= 1:
        return img, 1.0
    out = cv2.resize(img, (round(w * s), round(h * s)), interpolation=cv2.INTER_AREA)
    return out, s


def yolo_to_xyxy(cx, cy, bw, bh, W, H):
    """YOLO (merkez, göreli boyut) -> piksel x1,y1,x2,y2. W,H küçültülmüş görüntünün boyutu."""
    return [round((cx - bw / 2) * W), round((cy - bh / 2) * H),
            round((cx + bw / 2) * W), round((cy + bh / 2) * H)]


def torso_from_person(p, h_rng=(0.20, 0.55), w_rng=(0.15, 0.85)):
    """Kişi kutusundan gövde (omuzdan bele) türetme kuralı (3c)."""
    x1, y1, x2, y2 = p
    w, h = x2 - x1, y2 - y1
    return [round(x1 + w_rng[0] * w), round(y1 + h_rng[0] * h),
            round(x1 + w_rng[1] * w), round(y1 + h_rng[1] * h)]


def scale_box(b, r):
    return None if b is None else [round(v * r) for v in b]


def clip_box(b, shape):
    H, W = shape[:2]
    x1, y1, x2, y2 = b
    return [max(0, min(W, x1)), max(0, min(H, y1)), max(0, min(W, x2)), max(0, min(H, y2))]


def box_area(b):
    return max(0, b[2] - b[0]) * max(0, b[3] - b[1])


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = box_area(a) + box_area(b) - inter
    return inter / union if union > 0 else 0.0


def intersects(a, b):
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def match_iou(preds, gts, thr=0.5):
    """5f: IoU >= thr çiftler en yüksekten başlanarak eşlenir; her kutu en fazla bir kez."""
    pairs = sorted(((iou(p, g), i, j) for i, p in enumerate(preds)
                    for j, g in enumerate(gts)), reverse=True)
    used_p, used_g, matched = set(), set(), []
    for v, i, j in pairs:
        if v < thr:
            break
        if i in used_p or j in used_g:
            continue
        used_p.add(i)
        used_g.add(j)
        matched.append((i, j, v))
    tp = len(matched)
    return tp, len(preds) - tp, len(gts) - tp, matched


# ----------------------------------------------------------------- kayıtlar
def _jsonable(x):
    if isinstance(x, dict):
        return {(' / '.join(map(str, k)) if isinstance(k, tuple) else str(k)): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if isinstance(x, (np.floating, float)):
        return None if np.isnan(x) else round(float(x), 4)
    if isinstance(x, np.integer):
        return int(x)
    return x


def log_experiment(deney, kisi, girdi, parametre, cikti, yorum,
                   path=None):
    """4b: girdi + parametre + çıktı + yorum. Herkes aynı sütunlarla yazar.
    Drive'da iki kişi aynı dosyaya aynı anda yazınca satır kaybolabileceği için her kişi kendi
    dosyasına yazar (results/experiments_<kişi>.csv); deney_kayitlari() hepsini experiments.csv'de birleştirir."""
    path = Path(path) if path else RES / f"experiments_{re.sub(r'[^0-9A-Za-z_-]+', '_', str(kisi))}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with open(path, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if new:
            w.writerow(['zaman', 'deney', 'kisi', 'girdi', 'parametre', 'cikti', 'yorum'])
        w.writerow([datetime.now().isoformat(timespec='seconds'), deney, kisi,
                    girdi,
                    parametre if isinstance(parametre, str) else json.dumps(_jsonable(parametre), ensure_ascii=False, default=str),
                    cikti if isinstance(cikti, str) else json.dumps(_jsonable(cikti), ensure_ascii=False, default=str),
                    yorum])


def deney_kayitlari(save=True):
    """results/experiments_*.csv dosyalarını zamana göre sıralı tek tabloda birleştirir (4b)."""
    import pandas as pd
    parts = [pd.read_csv(p, dtype=str) for p in sorted(RES.glob('experiments_*.csv'))]
    df = pd.concat(parts, ignore_index=True).sort_values('zaman', kind='stable').reset_index(drop=True) if parts else \
        pd.DataFrame(columns=['zaman', 'deney', 'kisi', 'girdi', 'parametre', 'cikti', 'yorum'])
    if save and parts:
        df.to_csv(RES / 'experiments.csv', index=False, encoding='utf-8')
    return df


# ------------------------------------------------- kayıtlar (git commit yerine)
KAYIT_DEFTERI = KAYIT / 'kayit_defteri.csv'
_KAYIT_COLS = ['zaman', 'etiket', 'dosya', 'sha256', 'kopya', 'not']


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def kayit_al(*yollar, etiket='kayit', not_=''):
    """Commit'in yerini tutar: dosyaların o anki kopyası kayitlar/<zaman>_<etiket>/ altına,
    zamanı ve SHA-256 özeti kayitlar/kayit_defteri.csv'ye yazılır. Sonradan değişiklik kayit_kontrol() ile görülür.

    Örnek: kayit_al('predictions.md', etiket='tahminler-4a')
           kayit_al('data/gt.json', 'data/sources.csv', etiket='dondurma-1')
    """
    now = datetime.now()
    etiket = re.sub(r'[^0-9A-Za-z_.-]+', '-', etiket)
    hedef = KAYIT / f"{now.strftime('%Y%m%d-%H%M%S')}_{etiket}"
    hedef.mkdir(parents=True, exist_ok=True)
    new = not KAYIT_DEFTERI.exists()
    rows = []
    for y in yollar:
        p = Path(y)
        p = p if p.is_absolute() else ROOT / p
        if not p.exists():
            raise FileNotFoundError(p)
        shutil.copyfile(p, hedef / p.name)
        rows.append([now.isoformat(timespec='seconds'), etiket, p.relative_to(ROOT).as_posix(), sha256(p),
                     (hedef / p.name).relative_to(ROOT).as_posix(), not_])
    with open(KAYIT_DEFTERI, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if new:
            w.writerow(_KAYIT_COLS)
        w.writerows(rows)
    for r in rows:
        print(f'kayıt: {r[1]} | {r[2]} | {r[0]} | sha256 {r[3][:12]}…')
    return hedef


def kayitlar():
    if not KAYIT_DEFTERI.exists():
        return []
    with open(KAYIT_DEFTERI, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def kayit_kontrol():
    """Her kaydı listeler ve dosyanın kayıttan sonra değişip değişmediğini söyler
    (ör. predictions.md tahmin kaydından sonra değişmemeli, 4a)."""
    import pandas as pd
    rows = []
    for r in kayitlar():
        p = ROOT / r['dosya']
        now = sha256(p) if p.exists() else None
        rows.append({'zaman': r['zaman'], 'etiket': r['etiket'], 'dosya': r['dosya'],
                     'su_an': 'aynı' if now == r['sha256'] else ('dosya yok' if now is None else 'DEĞİŞTİ')})
    df = pd.DataFrame(rows, columns=['zaman', 'etiket', 'dosya', 'su_an'])
    if df.empty:
        print('Henüz kayıt yok (kayitlar/kayit_defteri.csv).')
    return df


# ------------------------------------------------------------- Drive / durum
def durum(hazirla=True):
    """Kurulum hücresinin sonunda çalışır: proje yolu, görüntüler, kutular, dondurma, kayıtlar."""
    print('Proje klasörü :', ROOT)
    n_img = sum(any((IMG_DIR / f'{i}{e}').exists() for e in ('.png', '.jpg', '.jpeg')) for i in DEV_IDS + CTRL_IDS)
    if n_img < 20 and hazirla:
        import hazirlik
        try:
            print('Küçültülmüş görüntüler eksik; ham görüntülerden hazırlanıyor (2d)…')
            hazirlik.goruntuleri_hazirla(verbose=False)
            n_img = sum(any((IMG_DIR / f'{i}{e}').exists() for e in ('.png', '.jpg', '.jpeg'))
                        for i in DEV_IDS + CTRL_IDS)
        except Exception as e:  # noqa: BLE001
            print('  hazırlanamadı:', e)
    print(f'Görüntüler    : {n_img}/20 hazır (data/images_1024)')
    try:
        E = entries(load_gt())
        kutulu = sum(bool(g.get('persons')) for g in E.values())
        print(f'gt.json       : {len(E)} görüntü, {kutulu} tanesinde kutu var'
              + ('' if kutulu else ' -> import hazirlik; hazirlik.etiketleri_aktar()'))
    except FileNotFoundError:
        print('gt.json       : YOK')
    P = load_params()
    print('params dondu mu:', P.get('_frozen'), P.get('_frozen_at') or '')
    k = kayitlar()
    print('Kayıtlar      :', f"{len(k)} dosya kaydı, son: {k[-1]['etiket']} ({k[-1]['zaman']})" if k else 'yok')


def drive_kaydet():
    """Oturumu kapatmadan önce: Colab'ın Drive'a bekleyen yazmalarını bitirir (bağlantıyı da keser)."""
    try:
        from google.colab import drive
    except ImportError:
        print('Colab dışında çalışıyor; gerek yok.')
        return
    drive.flush_and_unmount()
    print("Drive'a yazıldı ve bağlantı kesildi. Devam etmek için kurulum hücresini yeniden çalıştırın.")


def tr_num(x, nd=2):
    """0.03 -> '0,03' (sonuç tablosu Türkçe ondalık virgül kullanır)."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return '—'
    if isinstance(x, str):
        return x
    return f'{x:.{nd}f}'.replace('.', ',')


def tr_pct(x, nd=1):
    """0.004 -> '%0,4'."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return '—'
    return '%' + f'{100 * x:.{nd}f}'.replace('.', ',')


# ------------------------------------------------------------- görselleştirme
def draw_boxes(img, g, extra=None):
    """Gövde (mavi, seçilen kalın), yelek (yeşil) ve isteğe bağlı ek kutular (kırmızı)."""
    vis = img.copy()
    for i, p in enumerate(g.get('persons', [])):
        if p.get('torso'):
            x1, y1, x2, y2 = p['torso']
            th = 3 if i == g.get('selected') else 1
            cv2.rectangle(vis, (x1, y1), (x2, y2), (255, 120, 0), th)
            cv2.putText(vis, f'P{i}', (x1, max(12, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 120, 0), 1)
    for b in vest_boxes(g):
        cv2.rectangle(vis, (b[0], b[1]), (b[2], b[3]), (0, 200, 0), 2)
    for b in (extra or []):
        cv2.rectangle(vis, (b[0], b[1]), (b[2], b[3]), (0, 0, 255), 1)
    return vis


def show(imgs, titles=None, cols=4, size=4, path=None):
    """BGR ya da gri görüntüleri ızgarada gösterir; path verilirse kaydeder."""
    import matplotlib.pyplot as plt
    if not isinstance(imgs, (list, tuple)):
        imgs = [imgs]
    n = len(imgs)
    cols = min(cols, n)
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(size * cols, size * rows), squeeze=False)
    for k, ax in enumerate(axes.ravel()):
        ax.axis('off')
        if k < n:
            im = imgs[k]
            if im.ndim == 3:
                ax.imshow(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
            else:
                ax.imshow(im, cmap='gray')
            if titles:
                ax.set_title(titles[k], fontsize=9)
    fig.tight_layout()
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=110)
    return fig
