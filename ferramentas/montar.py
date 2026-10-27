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

SPRITES_TRENS = os.path.join(RAIZ, 'sprites-trens')

# Física dos rodoviários (peso vazio real do tipo, potência, aderência e arrasto pelo formato da carroceria).
# A capacidade e o preço continuam os do jogo original. Ver README, seção "Física".
FISICA = {
    #                        peso t, potência hp, coef. tração, arrasto
    'mps_regal_bus':         (6.4, 90, 0.42, 0.13),
    'balogh_coal_truck':     (6.0, 120, 0.45, 0.09),
    'mps_mail_truck':        (4.2, 120, 0.42, 0.11),
    'witcombe_oil_tanker':   (6.3, 120, 0.45, 0.08),
    'talbott_livestock_van': (5.6, 120, 0.45, 0.11),
    'balogh_goods_truck':    (5.4, 120, 0.45, 0.11),
    'hereford_grain_truck':  (5.8, 120, 0.45, 0.09),
    'witcombe_wood_truck':   (5.5, 120, 0.45, 0.10),
    'mps_iron_ore_truck':    (6.2, 120, 0.45, 0.09),
    'balogh_steel_truck':    (5.6, 120, 0.45, 0.09),
    'balogh_armoured_truck': (6.8, 120, 0.42, 0.11),
}

# Trens de 1950: slug -> (id original, nome, partes em unidades de comprimento; a 1ª é a própria locomotiva/vagão)
TRENS = {
    'kirby_paul_tank':    (0, 'Kirby Paul Tank', [8, 4]),
    'chaney_jubilee':     (8, "Chaney 'Jubilee'", [8, 8, 8, 2]),
    'ginzu_a4':           (9, "Ginzu 'A4'", [8, 8, 8, 4]),
    'sh_8p':              (10, "SH '8P'", [8, 8, 8, 4]),
    'passenger_carriage': (27, 'Passenger Carriage', [8]),
    'mail_van':           (28, 'Mail Van', [8]),
    'coal_truck':         (29, 'Coal Truck', [8]),
    'oil_tanker':         (30, 'Oil Tanker', [8]),
    'livestock_van':      (31, 'Livestock Van', [8]),
    'goods_van':          (32, 'Goods Van', [8]),
    'grain_hopper':       (33, 'Grain Hopper', [8]),
    'wood_truck':         (34, 'Wood Truck', [8]),
    'iron_ore_hopper':    (35, 'Iron Ore Hopper', [8]),
    'steel_truck':        (36, 'Steel Truck', [8]),
    'armoured_van':       (37, 'Armoured Van', [8]),
}
# posição da fumaça (chaminé) em relação ao centro da 1ª parte: negativo = para a frente (unidades de comprimento)
FUMACA = {'kirby_paul_tank': -3, 'chaney_jubilee': -2, 'ginzu_a4': 1, 'sh_8p': -2}
ID_PARTES = 200   # ids novos para as partes articuladas (tênder e trechos da locomotiva)

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


CC_MEIO = 202          # tom do meio da faixa de cor da empresa (198..205) na paleta do TTD


def folha(quadros, k, modo='RGBA'):
    W4q, H4q = quadros[0].size
    w, h = W4q * k // 4, H4q * k // 4
    img = Image.new(modo, (PAD + len(quadros) * (w + PAD), h + 2 * PAD), 0)
    for i, q in enumerate(quadros):
        if k != 4:
            q = q.resize((w, h), Image.LANCZOS if modo == 'RGBA' else Image.BOX)
        img.paste(q, (PAD + i * (w + PAD), PAD))
    return img, w, h


def limpar_sombra(q):
    """Tira pontinhos soltos da sombra (ruído do render no chão): mediana só na parte de sombra pura."""
    import numpy as np
    from PIL import ImageFilter
    a = np.array(q)
    rgbmax = a[..., :3].max(axis=2)
    sombra = (rgbmax < 40) & (a[..., 3] < 235)
    alfa_s = np.where(sombra, a[..., 3], 0).astype('uint8')
    filt = np.array(Image.fromarray(alfa_s).filter(ImageFilter.MedianFilter(5)))
    a[..., 3] = np.where(sombra, filt, a[..., 3])
    return Image.fromarray(a)


def normalizar_pintura(quadros, mascaras):
    """A pintura vem cinza do render. O jogo usa só o brilho (o maior canal RGB, 128 = tom da paleta),
    então reescalamos o cinza para que o brilho típico da pintura fique em 128."""
    vals = []
    for q, m in zip(quadros, mascaras):
        for (r, g, b, a), mv in zip(getattr(q, 'get_flattened_data', q.getdata)(), getattr(m, 'get_flattened_data', m.getdata)()):
            if mv > 127 and a > 127:
                vals.append(max(r, g, b))
    if not vals:
        return quadros
    vals.sort()
    fator = 128.0 / max(1, vals[len(vals) // 2])
    saida = []
    for q, m in zip(quadros, mascaras):
        esc = q.point(lambda v: min(255, int(v * fator + 0.5)))
        r, g, b, a = esc.split()
        q2 = Image.merge('RGBA', (r, g, b, q.getchannel('A')))
        q = q.copy(); q.paste(q2, mask=m.point(lambda v: 255 if v > 127 else 0))
        saida.append(q)
    return saida


def mascara_8bpp(rgba, masc, raw):
    """Máscara de cor da empresa: índice CC_MEIO onde há pintura, 0 no resto."""
    sel = Image.eval(masc, lambda v: 255 if v > 127 else 0)
    alfa = rgba.getchannel('A').point(lambda a: 255 if a > 127 else 0)
    sel = Image.composite(sel, Image.new('L', sel.size, 0), alfa)
    out = Image.new('P', rgba.size, 0); out.putpalette(raw)
    out.paste(CC_MEIO, mask=sel)
    return out, sel


def pintura_na_base(base8, rgba, sel):
    """Na base 8 bits, a pintura usa os 8 tons de cor da empresa conforme o brilho."""
    px = base8.load(); w, h = base8.size
    sel_px = sel.load(); src = rgba.load()
    for y in range(h):
        for x in range(w):
            if sel_px[x, y]:
                r, g, b, a = src[x, y]
                px[x, y] = 198 + max(0, min(7, int(max(r, g, b) / 256 * 8)))
    return base8


def bloco(nome_set, zoom, arquivo, w, h, n, mascara=None):
    linhas = [f'    [{PAD + i * (w + PAD)}, {PAD}, {w}, {h}, {-w // 2}, {-h // 2}]' for i in range(n)]
    if zoom is None:
        cab = f'spriteset({nome_set}, "{arquivo}") {{'
    else:
        extra = f', "{mascara}"' if mascara else ''
        cab = f'alternative_sprites({nome_set}, {zoom}, BIT_DEPTH_32BPP, "{arquivo}"{extra}) {{'
    return cab + '\n' + '\n'.join(linhas) + '\n}\n'


def conjunto(pasta, base, raw, permitidos):
    """Monta as folhas (1x, 2x, 4x, máscaras e base 8 bits) de um conjunto de 8 direções e devolve o NML
    do spriteset, ou None se faltam renders."""
    arqs = [os.path.join(pasta, f'{i}_{d}.png') for i, d in enumerate(DIRS)]
    if not all(os.path.exists(a) for a in arqs):
        return None
    quadros = [limpar_sombra(Image.open(a).convert('RGBA')) for a in arqs]
    W4q, H4q = quadros[0].size
    arqs_m = [os.path.join(pasta, f'm{i}_{d}.png') for i, d in enumerate(DIRS)]
    tem_mascara = all(os.path.exists(a) for a in arqs_m)
    if tem_mascara:
        mascaras = [Image.open(a).convert('L') for a in arqs_m]
        quadros = normalizar_pintura(quadros, mascaras)
    for nome_esc, k in ESCALAS.items():
        img, w, h = folha(quadros, k)
        img.save(os.path.join(BUILD, f'{base}_{nome_esc}.png'))
        sel = None
        if tem_mascara:
            mimg, _, _ = folha(mascaras, k, 'L')
            m8, sel = mascara_8bpp(img, mimg, raw)
            m8.save(os.path.join(BUILD, f'{base}_{nome_esc}_mask.png'))
        if k == 1:
            base8 = quantizar(img, raw, permitidos)
            if sel is not None:
                base8 = pintura_na_base(base8, img, sel)
            base8.save(os.path.join(BUILD, f'{base}_8bpp.png'))
    s = f'{base}_set'
    mk = (lambda e: f'{base}_{e}_mask.png') if tem_mascara else (lambda e: None)
    return ''.join([
        bloco(s, None, f'{base}_8bpp.png', W4q // 4, H4q // 4, 8),
        bloco(s, 'ZOOM_LEVEL_NORMAL', f'{base}_1x.png', W4q // 4, H4q // 4, 8, mk('1x')),
        bloco(s, 'ZOOM_LEVEL_IN_2X', f'{base}_2x.png', W4q // 2, H4q // 2, 8, mk('2x')),
        bloco(s, 'ZOOM_LEVEL_IN_4X', f'{base}_4x.png', W4q, H4q, 8, mk('4x')),
    ])


def main():
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(os.path.join(BUILD, 'lang'), exist_ok=True)
    raw, permitidos = paleta_ttd()
    nml_txt = [
        'grf {\n    grfid: "PH\\01\\01";\n    name: string(STR_GRF_NAME);\n    desc: string(STR_GRF_DESC);\n'
        '    version: 3;\n    min_compatible_version: 1;\n}\n'
    ]
    feitos = []
    # ---- rodoviários ----
    for slug, (vid, nome) in VEICULOS.items():
        blocos = conjunto(os.path.join(SPRITES, slug), slug, raw, permitidos)
        if blocos is None:
            print(f'  -- {nome}: sem renders, mantém o gráfico original')
            continue
        nml_txt.append(blocos)
        fis = ''
        if slug in FISICA:
            peso, pot, te, ar = FISICA[slug]
            fis = (f' weight: {peso} ton; power: {pot} hp;'
                   f' tractive_effort_coefficient: {te}; air_drag_coefficient: {ar};')
        nml_txt.append(
            f'item(FEAT_ROADVEHS, {slug}_item, {vid}) {{\n'
            f'    property {{ sprite_id: SPRITE_ID_NEW_ROADVEH;{fis} }}\n'
            f'    graphics {{ default: {slug}_set; }}\n}}\n'
        )
        feitos.append(nome)
        print(f'  ok {nome}')
    # ---- trens (com partes articuladas no comprimento real) ----
    prox = ID_PARTES
    for slug, (vid, nome, partes) in TRENS.items():
        pastas = [os.path.join(SPRITES_TRENS, slug, f'p{p}') for p in range(len(partes))]
        blocos = [conjunto(pa, f'{slug}_p{p}', raw, permitidos) for p, pa in enumerate(pastas)]
        if any(b is None for b in blocos):
            print(f'  -- {nome}: sem renders, mantém o gráfico original')
            continue
        nml_txt.extend(blocos)
        ids = []
        for p in range(1, len(partes)):
            pid = prox; prox += 1
            ids.append(pid)
            nml_txt.append(
                f'item(FEAT_TRAINS, {slug}_parte{p}, {pid}) {{\n'
                f'    property {{\n'
                f'        sprite_id: SPRITE_ID_NEW_TRAIN; climates_available: NO_CLIMATE;\n'
                f'        introduction_date: date(1920, 1, 1); model_life: VEHICLE_NEVER_EXPIRES; vehicle_life: 30;\n'
                f'        length: {partes[p]}; weight: 0 ton; power: 0 hp; cost_factor: 0; running_cost_factor: 0;\n'
                f'        refittable_cargo_classes: NO_CARGO_CLASS; default_cargo_type: 0; cargo_capacity: 0;\n'
                f'    }}\n'
                f'    graphics {{ default: {slug}_p{p}_set; }}\n}}\n'
            )
        fum = f' visual_effect_and_powered: visual_effect_and_powered(VISUAL_EFFECT_STEAM, {FUMACA[slug]}, DISABLE_WAGON_POWER);' if slug in FUMACA else ''
        artic = ''
        if ids:
            casos = ' '.join(f'{p}: return {slug}_parte{p};' for p in range(1, len(partes)))
            nml_txt.append(
                f'switch(FEAT_TRAINS, SELF, {slug}_artic, extra_callback_info1) {{ {casos} return CB_RESULT_NO_MORE_ARTICULATED_PARTS; }}\n'
            )
            artic = f' articulated_part: {slug}_artic;'
        nml_txt.append(
            f'item(FEAT_TRAINS, {slug}_item, {vid}) {{\n'
            f'    property {{ sprite_id: SPRITE_ID_NEW_TRAIN; length: {partes[0]};{fum} }}\n'
            f'    graphics {{{artic} default: {slug}_p0_set; }}\n}}\n'
        )
        feitos.append(nome)
        print(f'  ok {nome} ({sum(partes)} unidades, {len(partes)} partes)')
    with open(os.path.join(BUILD, 'frota.nml'), 'w') as f:
        f.write('\n'.join(nml_txt))
    shutil.copy(os.path.join(RAIZ, 'src', 'lang', 'english.lng'), os.path.join(BUILD, 'lang', 'english.lng'))
    print(f'{len(feitos)} veículos montados em build/frota.nml')
    if not feitos:
        sys.exit(1)


if __name__ == '__main__':
    main()
