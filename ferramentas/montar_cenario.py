#!/usr/bin/env python3
"""Monta o NewGRF "Cenário" a partir de sprites-cenario/<modelo>/<SpriteID>.png + offsets.json.

Cada PNG é um sprite base do TTD em zoom 4x (32 bits). O script recorta o espaço vazio (em múltiplos de 4 para
manter o alinhamento exato), gera 2x, 1x e a base 8 bits na paleta do TTD, e escreve build/cenario.nml com um
bloco `replace` por sprite. Compilar: cd build && nmlc -c --grf cenario.grf cenario.nml
"""
import os, sys, json, glob, shutil
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from montar import paleta_ttd, quantizar, limpar_sombra

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTE = os.path.join(RAIZ, 'sprites-cenario')
BUILD = os.path.join(RAIZ, 'build')


def recorte4(img, xofs, yofs):
    """Recorta o vazio mantendo origem e tamanho múltiplos de 4 (para 2x e 1x saírem exatos)."""
    bb = img.getchannel('A').point(lambda a: 255 if a > 8 else 0).getbbox()
    if not bb:
        return None
    # a origem do sprite (−xofs, −yofs) precisa cair em múltiplo de 4 depois do corte
    ox, oy = -xofs, -yofs
    l = bb[0] - ((bb[0] - ox) % 4)
    t = bb[1] - ((bb[1] - oy) % 4)
    r = bb[2] + (-(bb[2] - l) % 4)
    b = bb[3] + (-(bb[3] - t) % 4)
    W, H = img.size
    if r > W or b > H or l < 0 or t < 0:
        novo = Image.new('RGBA', (max(r, W) - min(l, 0), max(b, H) - min(t, 0)), (0, 0, 0, 0))
        novo.paste(img, (-min(l, 0), -min(t, 0)))
        img, l, r, t, b = novo, l - min(l, 0), r - min(l, 0), t - min(t, 0), b - min(t, 0)
    return img.crop((l, t, r, b)), xofs + l, yofs + t


def main():
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(os.path.join(BUILD, 'lang'), exist_ok=True)
    raw, permitidos = paleta_ttd()
    txt = ['grf {\n    grfid: "PH\\01\\02";\n    name: string(STR_GRF_NAME_CENARIO);\n    desc: string(STR_GRF_DESC_CENARIO);\n'
           '    version: 1;\n    min_compatible_version: 1;\n}\n']
    n = 0
    for meta in sorted(glob.glob(os.path.join(FONTE, '*', 'offsets.json'))):
        pasta = os.path.dirname(meta)
        for d in json.load(open(meta)):
            sid = int(d['nome'])
            img = limpar_sombra(Image.open(os.path.join(pasta, f"{d['nome']}.png")).convert('RGBA'))
            r = recorte4(img, d['xofs'], d['yofs'])
            if r is None:
                continue
            img4, x4, y4 = r
            w4, h4 = img4.size
            base = f'c{sid}'
            img4.save(os.path.join(BUILD, f'{base}_4x.png'))
            img4.resize((w4 // 2, h4 // 2), Image.LANCZOS).save(os.path.join(BUILD, f'{base}_2x.png'))
            img1 = img4.resize((w4 // 4, h4 // 4), Image.LANCZOS)
            img1.save(os.path.join(BUILD, f'{base}_1x.png'))
            quantizar(img1, raw, permitidos).save(os.path.join(BUILD, f'{base}_8bpp.png'))
            txt.append(f'replace {base}({sid}, "{base}_8bpp.png") {{ [0, 0, {w4 // 4}, {h4 // 4}, {x4 // 4}, {y4 // 4}] }}\n')
            for z, k in (('ZOOM_LEVEL_NORMAL', 4), ('ZOOM_LEVEL_IN_2X', 2), ('ZOOM_LEVEL_IN_4X', 1)):
                nome = {4: '1x', 2: '2x', 1: '4x'}[k]
                txt.append(f'alternative_sprites({base}, {z}, BIT_DEPTH_32BPP, "{base}_{nome}.png") '
                           f'{{ [0, 0, {w4 // k}, {h4 // k}, {x4 // k}, {y4 // k}] }}\n')
            n += 1
    open(os.path.join(BUILD, 'cenario.nml'), 'w').write('\n'.join(txt))
    shutil.copy(os.path.join(RAIZ, 'src', 'lang', 'english.lng'), os.path.join(BUILD, 'lang', 'english.lng'))
    print(n, 'sprites de cenário em build/cenario.nml')


if __name__ == '__main__':
    main()
