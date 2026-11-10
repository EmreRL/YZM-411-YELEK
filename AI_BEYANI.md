# Yapay zekâ beyanı (10e)

Her üye kendi kullanımını bu tabloya ekler. Kullanmayan üye kendi satırına "Üretici yapay zekâ kullanmadım" yazar.

| Üye | Araç | Kullanım amacı | Etkilediği dosya / hücre | Nasıl doğrulandı |
|---|---|---|---|---|
| (Osman) | Claude (Anthropic) | Ödev belgesine göre iş bölümü; ortak kod iskeleti; kutu çizme aracı; defter iskeletleri; tahmin ve not şablonları; projenin GitHub'sız, yalnız Google Drive'da çalışacak biçimde uyarlanması (Drive kurulum hücresi, görüntü küçültme ve kutu-cizer etiketlerinin gt.json'a ölçekli aktarımı, commit yerine `kayitlar/` kaydı) | `src/*.py` (`src/hazirlik.py` dahil), `scripts/*.py`, `notebooks/*.ipynb`, `main.ipynb`, `tools/kutu_cizer.html`, `data/docs/kutu-cizer.ipynb` yol hücresi, `README.md`, `predictions.md` ve `notes/_sablon.md` şablonları | Kod önce sentetik görüntülerle uçtan uca çalıştırıldı (sentetik çıktılar depoya konmadı). Ardından grup kendi 20 görüntüsüyle çalıştırdı; formüller ödev maddeleriyle (5c–5g, 6a–6c, 7, D1–D8) tek tek karşılaştırıldı: …… |
| | | | | |
| | | | | |
| | | | | |
| | | | | |

Yapay zekâ **ölçüm üretmedi**: tablolardaki bütün sayılar grubun kendi görüntüleri üzerinde `main.ipynb` çalıştırılarak elde edildi.
Eşikler (HSV, filtre, parça alanı) ve tahminler grup üyelerince belirlendi.
