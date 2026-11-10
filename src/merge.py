"""Paket E — sonuç tablosu (10b). A, B ve C'nin dosyaları görüntü kimliği üzerinden birleşir.

Sütunlar: Görüntü | Koşul | Doğru sınıf | Kuralın sınıfı | Gövde maske oranı |
          Şerit kanıtı (Canny kenar oranı / şablon skoru) | TP / FP / FN
'Sonraki kontrol' satırları (9b) dondurulmuş satırların YERİNE değil, ayrı satır olarak eklenir.
"""
import csv
from datetime import datetime

import pandas as pd

from common import CTRL_IDS, DATA, RES, entries, load_gt, tpfpfn_ids, tr_num, tr_pct

COLS = ['Görüntü', 'Koşul', 'Doğru sınıf', 'Kuralın sınıfı', 'Gövde maske oranı',
        'Şerit kanıtı (Canny kenar oranı / şablon skoru)', 'TP / FP / FN']
FOLLOWUP = RES / 'sonraki_kontrol.csv'


def add_followup(img_id, kisi, ne_degisti, kuralin_sinifi='', govde_orani='', serit='', tpfpfn='', yorum=''):
    """9b: sonraki kontrolün sonucu ayrı satır olur; dondurulmuş sonuç değişmez."""
    new = not FOLLOWUP.exists()
    with open(FOLLOWUP, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if new:
            w.writerow(['zaman', 'id', 'kisi', 'ne_degisti', 'kural_sinifi', 'govde_orani', 'serit', 'tpfpfn', 'yorum'])
        w.writerow([datetime.now().isoformat(timespec='seconds'), img_id, kisi, ne_degisti,
                    kuralin_sinifi, govde_orani, serit, tpfpfn, yorum])


def build(gt=None, save=True):
    gt = gt or load_gt()
    E = entries(gt)
    src = pd.read_csv(DATA / 'sources.csv', dtype=str).fillna('')
    kosul = dict(zip(src['id'], src['kosul']))
    col = pd.read_csv(RES / 'color.csv').set_index('id')
    edge = pd.read_csv(RES / 'edge.csv')
    edge = edge[edge['secilen'] == True].set_index('id')  # noqa: E712
    tmc = pd.read_csv(RES / 'template_control.csv')
    tmc = tmc[tmc['secilen'] == True].set_index('id')  # noqa: E712
    counted = set(tpfpfn_ids(gt))

    rows = []
    for img_id in CTRL_IDS:
        c = col.loc[img_id] if img_id in col.index else None
        cr = edge.loc[img_id, 'canny_orani'] if img_id in edge.index else None
        sk = tmc.loc[img_id, 'skor'] if img_id in tmc.index else 'ölçülemedi'
        try:
            sk = tr_num(float(sk))
        except (TypeError, ValueError):
            sk = str(sk)
        tpfpfn = '—'
        if c is not None and img_id in counted:
            tpfpfn = f"{int(c['tp'])} / {int(c['fp'])} / {int(c['fn'])}"
        rows.append({
            'Görüntü': img_id,
            'Koşul': kosul.get(img_id, ''),
            'Doğru sınıf': E[img_id]['class'],
            'Kuralın sınıfı': '' if c is None else c['kural_sinifi'],
            'Gövde maske oranı': '—' if c is None or pd.isna(c['govde_maske_orani']) else tr_pct(c['govde_maske_orani']),
            'Şerit kanıtı (Canny kenar oranı / şablon skoru)': f"{tr_num(cr) if cr is not None else '—'} / {sk}",
            'TP / FP / FN': tpfpfn,
        })
    t = pd.DataFrame(rows, columns=COLS)
    n_ok = int((t['Doğru sınıf'] == t['Kuralın sınıfı']).sum())
    cc = col.loc[[i for i in CTRL_IDS if i in col.index and i in counted]]
    total = {'Görüntü': 'TOPLAM', 'Koşul': f'TP/FP/FN yalnız {len(cc)} görüntüde (5f)',
             'Doğru sınıf': '', 'Kuralın sınıfı': f'doğru sınıf {n_ok}/{len(t)} (5g)',
             'Gövde maske oranı': '', 'Şerit kanıtı (Canny kenar oranı / şablon skoru)': '',
             'TP / FP / FN': f"{int(cc['tp'].sum())} / {int(cc['fp'].sum())} / {int(cc['fn'].sum())}"}
    t = pd.concat([t, pd.DataFrame([total])], ignore_index=True)
    if FOLLOWUP.exists():
        fu = pd.read_csv(FOLLOWUP, dtype=str).fillna('')
        for _, r in fu.iterrows():
            t.loc[len(t)] = {'Görüntü': f"{r['id']} (sonraki kontrol)", 'Koşul': r['ne_degisti'],
                             'Doğru sınıf': E.get(r['id'], {}).get('class', ''), 'Kuralın sınıfı': r['kural_sinifi'],
                             'Gövde maske oranı': r['govde_orani'],
                             'Şerit kanıtı (Canny kenar oranı / şablon skoru)': r['serit'], 'TP / FP / FN': r['tpfpfn']}
    if save:
        t.to_csv(RES / 'final_table.csv', index=False, encoding='utf-8')
        with open(RES / 'final_table.md', 'w', encoding='utf-8') as f:
            try:
                f.write(t.to_markdown(index=False))
            except ImportError:          # tabulate yoksa
                f.write(t.to_string(index=False))
    print(f'Doğru sınıf: {n_ok}/{len(rows)}')
    return t
