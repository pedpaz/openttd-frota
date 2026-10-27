#!/usr/bin/env python3
"""Monta o NewGRF "Frota" a partir dos renders em sprites/<slug>/.

Para cada veículo listado em VEICULOS que tenha renders, gera em build/:
  <slug>_4x.png, <slug>_2x.png, <slug>_1x.png  (32 bits, RGBA)
  <slug>_8bpp.png                              (paleta do TTD, obrigatória como base)
e escreve build/frota.nml. Depois é só rodar: nmlc -c --grf build/frota.grf build/frota.nml

Uso: python3 ferramentas/montar.py
"""
import os, sys, shutil
from PIL import Image
import nml.palette

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPRITES = os.path.join(RAIZ, 'sprites')
BUILD = os.path.join(RAIZ, 'build')

# slug -> (id local do veículo rodoviário no TTD original = EngineID - 116, nome)
VEICULOS = {
    'mps_regal_bus':          (0,  'MPS Regal Bus'),
    'balogh_coal_truck':      (7,  'Balogh Coal Truck'),
    'mps_mail_truck':         (10, 'MPS Mail Truck'),
    'witcombe_oil_tanker':    (16, 'Witcombe Oil Tanker'),
    'talbott_livestock_van':  (19, 'Talbott Livestock Van'),
    'balogh_goods_truck':     (22, 'Balogh Goods Truck'),
    'hereford_grain_truck':   (25, 'Hereford Grain Truck'),
    'witcombe_wood_truck':    (28, 'Witcombe Wood Truck'),
    'mps_iron_ore_truck':     (31, 'MPS Iron Ore Truck'),
    'balogh_steel_truck':     (34, 'Balogh Steel Truck'),
    'balogh_armoured_truck':  (37, 'Balogh Armoured Truck'),
}

DIRS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']   # ordem dos sprites no OpenTTD
W4, H4 = 200, 160                                      # quadro no zoom 4x
PAD = 2
ESCALAS = {'4x': 4, '2x': 2, '1x': 1}


def paleta_ttd():
    """Paleta DOS do TTD, restrita às cores 'normais' (sem transparente, cor da empresa e cores animadas)."""
    raw = nml.palette.raw_palette_data[0]
    permitidos = list(range(1, 198)) + list(range(206, 215))
    return raw, permitidos


def quantizar(rgba, raw, permitidos):
    """Converte RGBA para 8bpp com a paleta do TTD (índice 0 = transparente)."""
    # imagem-paleta só com as cores permitidas, para o PIL escolher a mais próxima
    pal = []
    for i in permitidos:
        pal += raw[i * 3:i * 3 + 3]
    pal += pal[-3:] * (256 - len(permitidos))
    ref = Image.new('P', (1, 1)); ref.putpalette(pal)
    q = rgba.convert('RGB').quantize(palette=ref, dither=Image.Dither.NONE)
    mapa = permitidos + [permitidos[-1]] * (256 - len(permitidos))
    q = q.point(lambda v: mapa[v])
    alfa = rgba.getchannel('A')
    q.paste(0, mask=alfa.point(lambda a: 255 if a < 128 else 0))
    out = Image.new('P', rgba.size); out.putpalette(raw); out.paste(q)
    return out


def folha(quadros, k):
    w, h = W4 * k // 4, H4 * k // 4
    img = Image.new('RGBA', (PAD + len(quadros) * (w + PAD), h + 2 * PAD), (0, 0, 0, 0))
    for i, q in enumerate(quadros):
        if k != 4:
            q = q.resize((w, h), Image.LANCZOS)
        img.paste(q, (PAD + i * (w + PAD), PAD))
    return img, w, h


def bloco(nome_set, zoom, arquivo, w, h, n):
    linhas = [f'    [{PAD + i * (w + PAD)}, {PAD}, {w}, {h}, {-w // 2}, {-h // 2}]' for i in range(n)]
    if zoom is None:
        cab = f'spriteset({nome_set}, "{arquivo}") {{'
    else:
        cab = f'alternative_sprites({nome_set}, {zoom}, BIT_DEPTH_32BPP, "{arquivo}") {{'
    return cab + '\n' + '\n'.join(linhas) + '\n}\n'


def main():
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(os.path.join(BUILD, 'lang'), exist_ok=True)
    raw, permitidos = paleta_ttd()
    nml_txt = [
        'grf {\n    grfid: "PH\\01\\01";\n    name: string(STR_GRF_NAME);\n    desc: string(STR_GRF_DESC);\n'
        '    version: 2;\n    min_compatible_version: 1;\n}\n'
    ]
    feitos = []
    for slug, (vid, nome) in VEICULOS.items():
        pasta = os.path.join(SPRITES, slug)
        arqs = [os.path.join(pasta, f'{i}_{d}.png') for i, d in enumerate(DIRS)]
        if not all(os.path.exists(a) for a in arqs):
            print(f'  -- {nome}: sem renders, mantém o gráfico original')
            continue
        quadros = [Image.open(a).convert('RGBA') for a in arqs]
        for nome_esc, k in ESCALAS.items():
            img, w, h = folha(quadros, k)
            img.save(os.path.join(BUILD, f'{slug}_{nome_esc}.png'))
            if k == 1:
                quantizar(img, raw, permitidos).save(os.path.join(BUILD, f'{slug}_8bpp.png'))
        s = f'{slug}_set'
        nml_txt.append(bloco(s, None, f'{slug}_8bpp.png', W4 // 4, H4 // 4, 8))
        nml_txt.append(bloco(s, 'ZOOM_LEVEL_NORMAL', f'{slug}_1x.png', W4 // 4, H4 // 4, 8))
        nml_txt.append(bloco(s, 'ZOOM_LEVEL_IN_2X', f'{slug}_2x.png', W4 // 2, H4 // 2, 8))
        nml_txt.append(bloco(s, 'ZOOM_LEVEL_IN_4X', f'{slug}_4x.png', W4, H4, 8))
        nml_txt.append(
            f'item(FEAT_ROADVEHS, {slug}_item, {vid}) {{\n'
            f'    property {{ sprite_id: SPRITE_ID_NEW_ROADVEH; }}\n'
            f'    graphics {{ default: {s}; }}\n}}\n'
        )
        feitos.append(nome)
        print(f'  ok {nome}')
    with open(os.path.join(BUILD, 'frota.nml'), 'w') as f:
        f.write('\n'.join(nml_txt))
    shutil.copy(os.path.join(RAIZ, 'src', 'lang', 'english.lng'), os.path.join(BUILD, 'lang', 'english.lng'))
    print(f'{len(feitos)} veículos montados em build/frota.nml')
    if not feitos:
        sys.exit(1)


if __name__ == '__main__':
    main()
