"""Paket A — 2d: görüntüleri küçültür ve (isteğe bağlı) kutu-cizer etiketlerini gt.json'a aktarır.

Asıl kod src/hazirlik.py'dedir; defterlerden doğrudan çağrılır:
    import hazirlik
    hazirlik.goruntuleri_hazirla()      # data/images/{gelistirme,kontrol} -> data/images_1024/G-1.png …
    hazirlik.etiketleri_aktar()         # data/images/*-etiketli/kutular.csv -> data/gt.json (1024 px'e ölçekli)

Bu betik aynı işi komut satırından yapar (proje kökünde):
    python scripts/prepare_images.py            # yalnız görüntüler
    python scripts/prepare_images.py --etiket   # görüntüler + etiket aktarımı
    python scripts/prepare_images.py --force    # bütün görüntüleri yeniden yaz
"""
import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import hazirlik  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--etiket', action='store_true', help='kutu-cizer etiketlerini gt.json\'a da aktar')
    ap.add_argument('--force', action='store_true', help='var olan küçültülmüş görüntüleri de yeniden yaz')
    a = ap.parse_args()
    hazirlik.goruntuleri_hazirla(force=a.force)
    if a.etiket:
        hazirlik.etiketleri_aktar()


if __name__ == '__main__':
    main()
