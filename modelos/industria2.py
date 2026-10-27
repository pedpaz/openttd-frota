# Mais indústrias de 1950 (temperado): fazenda, fábrica, serraria e poços de petróleo.
# Mesma convenção do industria.py: peça k no tile (k, 0); objetos de chão começam com 'chao'.
# Peças que formam um bloco 2x2 (fábrica) ocupam os tiles (k, 0), (k, 1), (k+1, 0), (k+1, 1).
# Uso: python3 industria2.py -- <pasta_saida>
import bpy, bmesh, math, os, sys, random
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modelar import reset, MATS, mat, box, cyl, sphere, prism, new_obj, finish, OUT
from trens import bx, loft, toro
from industria import P, materiais as materiais_base, telhado_duas_aguas, janelas, trelica_pernas


def materiais():
    M = materiais_base()
    M.update({
        'reboco': mat('Reboco branco', '#e4dfd2', 0.0, 0.85),
        'madeira_esc': mat('Madeira tábuas', '#4a3220', 0.0, 0.85),
        'madeira_clara': mat('Madeira serrada', '#cfae7a', 0.0, 0.8),
        'tora': mat('Tora', '#6d4a2c', 0.0, 0.9),
        'tora_topo': mat('Topo da tora', '#c9a473', 0.0, 0.9),
        'feno': mat('Feno', '#cdb062', 0.0, 0.95),
        'grama': mat('Grama', '#4f7f34', 0.0, 0.9),
        'agua': mat('Água', '#2f5f86', 0.1, 0.08),
        'telha_azul': mat('Telhado azul', '#3f5f8f', 0.3, 0.5),
        'porta_verde': mat('Porta verde', '#2f5132', 0.0, 0.6),
        'preto': mat('Preto fosco', '#18191a', 0.0, 0.7),
        'caixas': mat('Madeira caixote', '#9a7448', 0.0, 0.85),
    })
    return M


def piso(k, M, mat_='terra', ox=0, oy=0, tiles=1):
    x0, y0, _ = P(k, ox, oy)
    s = 12.0 * tiles
    bx('chao_piso', s, s, 0.02, (x0 - s / 2, y0 - s / 2, 0.01), M[mat_])


# ---------------- fazenda ----------------
def casa_fazenda(k, M):
    """Sede da fazenda (gfx 33): casa de dois andares rebocada de branco, telhado de ardósia, chaminés."""
    piso(k, M, 'terra')
    for (ox, oy, r) in [(3, 13, 1.6), (13, 3, 1.4), (12, 13, 2.0)]:
        x, y, _ = P(k, ox, oy)
        bx('chao_grama', r * 2, r * 1.6, 0.02, (x, y, 0.025), M['grama'], (0, 0, 0.4))
    cx, cy, _ = P(k, 7, 7)
    bx('casa', 7.0, 5.0, 5.4, (cx, cy, 2.7), M['reboco'], bevel=0.04)
    telhado_duas_aguas(cx - 3.5, cx + 3.5, cy - 2.5, cy + 2.5, 5.4, 2.4, M['telha'], 'X')
    for sx in (-1, 1):
        bx('chamine', 0.7, 0.9, 2.6, (cx + sx * 3.2, cy, 6.6), M['tijolo'])
    janelas(cx - 3.0, cx + 3.0, cy - 2.5, 1.6, 3, M, alt=1.1, larg=0.8, lado=-1)
    janelas(cx - 3.0, cx + 3.0, cy - 2.5, 4.0, 3, M, alt=1.0, larg=0.8, lado=-1)
    janelas(cy - 2.0, cy + 2.0, cx - 3.5, 4.0, 2, M, alt=1.0, larg=0.8, lado=-1, eixo='Y')
    bx('porta', 1.0, 0.05, 2.1, (cx, cy - 2.52, 1.05), M['porta_verde'])
    # anexo baixo de tijolo
    ax, ay, _ = P(k, 11.5, 9.5)
    bx('anexo', 3.4, 4.0, 2.8, (ax, ay, 1.4), M['tijolo'], bevel=0.03)
    telhado_duas_aguas(ax - 1.7, ax + 1.7, ay - 2.0, ay + 2.0, 2.8, 1.2, M['telha'], 'Y')
    # cerca de madeira na frente
    for i in range(9):
        x, y, _ = P(k, 1 + i * 1.6, 14.5)
        bx('cerca_poste', 0.12, 0.12, 1.0, (x, y, 0.5), M['madeira_esc'])
    x0, y0, _ = P(k, 1, 14.5); x1, y1, _ = P(k, 15, 14.5)
    for z in (0.45, 0.85):
        bx('cerca_trave', abs(x1 - x0), 0.06, 0.08, ((x0 + x1) / 2, y0, z), M['madeira_esc'])


def casa_pedra(k, M):
    """Casa de pedra pequena com muretas (gfx 34)."""
    piso(k, M, 'terra')
    cx, cy, _ = P(k, 6, 8)
    bx('casa', 5.0, 4.0, 3.2, (cx, cy, 1.6), M['pedra'], bevel=0.04)
    telhado_duas_aguas(cx - 2.5, cx + 2.5, cy - 2.0, cy + 2.0, 3.2, 1.8, M['telha'], 'X')
    bx('chamine', 0.6, 0.6, 1.8, (cx + 2.0, cy, 4.6), M['pedra'])
    janelas(cx - 2.0, cx + 2.0, cy - 2.0, 1.6, 2, M, alt=0.9, larg=0.7, lado=-1)
    bx('porta', 0.9, 0.05, 1.9, (cx + 0.2, cy - 2.02, 0.95), M['porta_verde'])
    for (ox0, oy0, ox1, oy1) in [(1, 1, 15, 1), (1, 1, 1, 15), (10, 6, 15, 6), (10, 6, 10, 15)]:
        x0, y0, _ = P(k, ox0, oy0); x1, y1, _ = P(k, ox1, oy1)
        L = math.hypot(x1 - x0, y1 - y0)
        bx('mureta', L, 0.45, 0.9, ((x0 + x1) / 2, (y0 + y1) / 2, 0.45), M['pedra'], (0, 0, math.atan2(y1 - y0, x1 - x0)))
    for (ox, oy) in [(12, 10), (13.5, 12.5), (11.5, 13.5)]:
        x, y, _ = P(k, ox, oy)
        sphere('chao_horta', 0.5, x, y, 0.15, M['grama'], 1.4, 0.8, 0.5)


def galpoes_feno(k, M):
    """Dois galpões abertos de feno (gfx 35) e medas de feno no chão."""
    piso(k, M, 'terra')
    for (ox, oy) in [(4, 4), (7, 3.5)]:
        x, y, _ = P(k, ox, oy)
        sphere('chao_meda', 1.0, x, y, 0.0, M['feno'], 1.6, 1.4, 1.5)
    for (ox, oy) in [(5, 10), (11.5, 7)]:
        cx, cy, _ = P(k, ox, oy)
        for sx in (-1, 1):
            for sy in (-1, 0, 1):
                bx('pilar', 0.2, 0.2, 3.6, (cx + sx * 2.0, cy + sy * 2.0, 1.8), M['madeira_esc'])
        # telhado curvo (holandês) de chapa
        pts = [(2.4 * math.cos(math.radians(a)), 3.6 + 1.2 * math.sin(math.radians(a))) for a in range(0, 181, 15)]
        prism('telhado_curvo', [(2.4, 3.55)] + pts + [(-2.4, 3.55)], 4.6, cy, M['zinco'], 'XZ').location = (cx, 0, 0)
        bx('feno_dentro', 3.6, 4.0, 2.6, (cx, cy, 1.3), M['feno'])


def celeiro(k, M):
    """Celeiro grande (gfx 36)."""
    piso(k, M, 'terra')
    cx, cy, _ = P(k, 8, 8)
    bx('celeiro', 9.0, 6.0, 4.2, (cx, cy, 2.1), M['reboco'], bevel=0.04)
    bx('rodape', 9.05, 6.05, 0.8, (cx, cy, 0.4), M['pedra'])
    telhado_duas_aguas(cx - 4.5, cx + 4.5, cy - 3.0, cy + 3.0, 4.2, 2.6, M['telha'], 'X')
    bx('portao', 3.0, 0.06, 3.2, (cx + 1.0, cy - 3.02, 1.6), M['madeira_esc'])
    for i in range(3):
        bx('ripa', 0.08, 0.07, 3.2, (cx + 1.0 - 1.0 + i, cy - 3.05, 1.6), M['preto'])
    janelas(cy - 2.0, cy + 2.0, cx - 4.5, 3.0, 2, M, alt=0.7, larg=0.6, lado=-1, eixo='Y')


def silos(k, M):
    """Dois silos altos de concreto com galpão de ração (gfx 37)."""
    piso(k, M, 'terra')
    for (ox, oy) in [(6, 5), (6, 10)]:
        x, y, _ = P(k, ox, oy)
        cyl('silo', 1.7, 11.0, x, y, 5.5, M['concreto'], 'Z', 32)
        sphere('silo_topo', 1.7, x, y, 11.0, M['zinco'], 1, 1, 0.45)
        for z in range(1, 11, 2):
            cyl('silo_anel', 1.76, 0.12, x, y, z, M['aco_claro'], 'Z', 32)
    cx, cy, _ = P(k, 11.5, 8)
    bx('galpao', 4.0, 6.0, 3.0, (cx, cy, 1.5), M['madeira_esc'])
    telhado_duas_aguas(cx - 2.0, cx + 2.0, cy - 3.0, cy + 3.0, 3.0, 1.2, M['zinco'], 'Y')
    x, y, _ = P(k, 3, 13)
    bx('chao_cocho', 2.5, 0.8, 0.5, (x, y, 0.25), M['madeira_esc'])


def chiqueiro(k, M):
    """Curral com cercado e abrigo comprido baixo (gfx 38)."""
    piso(k, M, 'terra2')
    cx, cy, _ = P(k, 11, 8)
    bx('abrigo', 3.0, 9.0, 2.0, (cx, cy, 1.0), M['tijolo'], bevel=0.03)
    telhado_duas_aguas(cx - 1.5, cx + 1.5, cy - 4.5, cy + 4.5, 2.0, 0.9, M['telha'], 'Y')
    for (ox0, oy0, ox1, oy1) in [(1.5, 1.5, 14.5, 1.5), (1.5, 1.5, 1.5, 14.5), (1.5, 14.5, 14.5, 14.5)]:
        x0, y0, _ = P(k, ox0, oy0); x1, y1, _ = P(k, ox1, oy1)
        L = math.hypot(x1 - x0, y1 - y0); n = int(L / 1.5)
        a = math.atan2(y1 - y0, x1 - x0)
        for i in range(n + 1):
            bx('cerca_poste', 0.12, 0.12, 1.1, (x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n, 0.55), M['madeira_esc'])
        for z in (0.5, 0.95):
            bx('cerca_trave', L, 0.06, 0.08, ((x0 + x1) / 2, (y0 + y1) / 2, z), M['madeira_esc'], (0, 0, a))
    rnd = random.Random(4)
    for i in range(5):
        x, y, _ = P(k, rnd.uniform(3, 8), rnd.uniform(3, 13))
        sphere('porco', 0.35, x, y, 0.35, M['reboco'], 1.6, 0.9, 0.9)


# ---------------- fábrica (bloco 2x2) ----------------
def fabrica(k, M):
    """Fábrica de tijolo com telhado em dente de serra azul e chaminés (bloco 2x2: N, E, W com prédio; S pátio)."""
    # chão: pátio de concreto com marcas nos quatro tiles
    for (tx, ty) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        x0, y0, _ = P(k + tx, 0, ty * 16)
        bx('chao_patio', 12, 12, 0.02, (x0 - 6, y0 - 6, 0.01), M['concreto_esc'])
    xs, ys, _ = P(k + 1, 8, 24)
    for i in range(4):
        bx('chao_caixas', 1.1, 1.1, 1.0 + (i % 2) * 0.6, (xs + i * 1.4 - 1.5, ys + (i % 2) * 1.3, 0.5), M['caixas'])
    # tile N: galpão de tecelagem, dente de serra
    nx, ny, _ = P(k, 8, 8)
    bx('galpao', 10.5, 10.5, 4.5, (nx, ny, 2.25), M['tijolo'], bevel=0.04)
    for i in range(4):
        y = ny - 5.25 + 1.3 + i * 2.62
        prism('dente', [(-1.31, 0), (1.31, 0), (-1.31, 1.8)], 10.5, nx, M['telha_azul'], 'YZ').location = (0, y, 4.5)
        bx('vidro_dente', 10.4, 0.05, 1.7, (nx, y - 1.31 - 0.03, 5.35), M['vidro'])
    janelas(nx - 4.5, nx + 4.5, ny - 5.25, 2.4, 5, M, alt=2.0, larg=1.0, lado=-1)
    janelas(ny - 4.5, ny + 4.5, nx - 5.25, 2.4, 5, M, alt=2.0, larg=1.0, lado=-1, eixo='Y')
    # tile E (0,1): escritório de dois andares com relógio
    ex, ey, _ = P(k, 8, 24)
    bx('escritorio', 9.0, 7.0, 7.0, (ex, ey, 3.5), M['tijolo'], bevel=0.04)
    telhado_duas_aguas(ex - 4.5, ex + 4.5, ey - 3.5, ey + 3.5, 7.0, 2.2, M['telha'], 'X')
    janelas(ex - 4.0, ex + 4.0, ey - 3.5, 2.0, 5, M, alt=1.4, larg=0.9, lado=-1)
    janelas(ex - 4.0, ex + 4.0, ey - 3.5, 5.0, 5, M, alt=1.4, larg=0.9, lado=-1)
    janelas(ey - 3.0, ey + 3.0, ex - 4.5, 2.0, 3, M, alt=1.4, larg=0.9, lado=-1, eixo='Y')
    janelas(ey - 3.0, ey + 3.0, ex - 4.5, 5.0, 3, M, alt=1.4, larg=0.9, lado=-1, eixo='Y')
    cyl('relogio', 0.55, 0.06, ex - 4.53, ey, 8.0, M['reboco'], 'X', 24)
    bx('frontao', 0.3, 2.0, 1.4, (ex - 4.5, ey, 7.6), M['tijolo'])
    # tile W (1,0): casa de força com chaminés e caixa d'água
    wx, wy, _ = P(k + 1, 8, 8)
    bx('casa_forca', 9.0, 9.0, 6.0, (wx, wy, 3.0), M['tijolo'], bevel=0.04)
    for i in range(3):
        y = wy - 4.5 + 1.5 + i * 3.0
        prism('dente', [(-1.5, 0), (1.5, 0), (-1.5, 1.9)], 9.0, wx, M['telha_azul'], 'YZ').location = (0, y, 6.0)
    janelas(wy - 4.0, wy + 4.0, wx - 4.5, 2.8, 4, M, alt=2.4, larg=1.0, lado=-1, eixo='Y')
    for (dx, dy, h) in [(2.5, -2.5, 17.0), (2.5, 2.0, 15.0), (-2.5, 2.5, 13.0)]:
        cyl('chamine', 0.75, h, wx + dx, wy + dy, h / 2, M['tijolo'], 'Z', 20, r2=0.6)
        cyl('chamine_topo', 0.7, 0.4, wx + dx, wy + dy, h + 0.1, M['aco'], 'Z', 20)


# ---------------- serraria ----------------
def galpao_madeira(cx, cy, comp, larg, alt, M, aberto=True, eixo='X'):
    sx, sy = (comp, larg) if eixo == 'X' else (larg, comp)
    bx('galpao', sx, sy, alt, (cx, cy, alt / 2), M['madeira_esc'], bevel=0.03)
    if eixo == 'X':
        telhado_duas_aguas(cx - comp / 2, cx + comp / 2, cy - larg / 2, cy + larg / 2, alt, larg * 0.35, M['telha'], 'X')
        for i in range(int(comp / 1.2)):
            bx('tabua', 0.05, 0.04, alt, (cx - comp / 2 + 0.6 + i * 1.2, cy - larg / 2 - 0.01, alt / 2), M['preto'])
        if aberto:
            bx('abertura', comp * 0.4, 0.06, alt * 0.75, (cx + comp * 0.2, cy - larg / 2 - 0.02, alt * 0.37), M['interior'])
    else:
        telhado_duas_aguas(cx - larg / 2, cx + larg / 2, cy - comp / 2, cy + comp / 2, alt, larg * 0.35, M['telha'], 'Y')
        for i in range(int(comp / 1.2)):
            bx('tabua', 0.04, 0.05, alt, (cx - larg / 2 - 0.01 + 0 * i, cy - comp / 2 + 0.6 + i * 1.2, alt / 2), M['preto'])
        if aberto:
            bx('abertura', 0.06, comp * 0.4, alt * 0.75, (cx - larg / 2 - 0.02, cy, alt * 0.37), M['interior'])


def pilha_tabuas(cx, cy, M, n=3, comp=4.5):
    for j in range(n):
        for z in range(4):
            bx('tabuas', comp, 1.0, 0.25, (cx, cy + j * 1.2, 0.15 + z * 0.3), M['madeira_clara'])
            bx('separador', 0.12, 1.05, 0.05, (cx - comp / 2 + 0.4, cy + j * 1.2, 0.3 + z * 0.3), M['madeira_esc'])
            bx('separador', 0.12, 1.05, 0.05, (cx + comp / 2 - 0.4, cy + j * 1.2, 0.3 + z * 0.3), M['madeira_esc'])


def pilha_toras(cx, cy, M, linhas=3, comp=6.0, eixo='X'):
    r = 0.35
    for lin in range(linhas):
        n = 5 - lin
        for i in range(n):
            off = (i - (n - 1) / 2) * 2 * r
            z = r + lin * r * 1.7
            if eixo == 'X':
                cyl('tora', r, comp, cx, cy + off, z, M['tora'], 'X', 14)
                for s in (-1, 1):
                    cyl('tora_topo', r * 0.9, 0.02, cx + s * (comp / 2 + 0.01), cy + off, z, M['tora_topo'], 'X', 14)
            else:
                cyl('tora', r, comp, cx + off, cy, z, M['tora'], 'Y', 14)
                for s in (-1, 1):
                    cyl('tora_topo', r * 0.9, 0.02, cx + off, cy + s * (comp / 2 + 0.01), z, M['tora_topo'], 'Y', 14)


def serraria(k, M):
    """Peças da serraria: k galpão (gfx 11), k+1 galpão com tábuas (12), k+2 galpão grande (13),
    k+3 pilha de toras (14), k+4 pilhas de tábuas (15)."""
    cx, cy, _ = P(k, 7.5, 8); galpao_madeira(cx, cy, 9.0, 6.5, 4.0, M, eixo='Y')
    cx, cy, _ = P(k + 1, 7, 6); galpao_madeira(cx, cy, 8.0, 5.0, 3.6, M)
    cx, cy, _ = P(k + 1, 8, 12.5); pilha_tabuas(cx, cy, M, n=1, comp=5)
    cx, cy, _ = P(k + 2, 8, 8); galpao_madeira(cx, cy, 10.0, 7.5, 4.6, M)
    cx, cy, _ = P(k + 3, 8, 5); pilha_toras(cx, cy, M, 3, 7.0)
    cx, cy, _ = P(k + 3, 8, 11); pilha_toras(cx, cy, M, 2, 6.0)
    cx, cy, _ = P(k + 4, 5, 3); pilha_tabuas(cx, cy, M, n=2)
    cx, cy, _ = P(k + 4, 11, 7); pilha_tabuas(cx, cy, M, n=3, comp=4.0)


# ---------------- poços de petróleo ----------------
def chao_poco(k, M):
    """Chão do poço: grama com terra batida e mancha de óleo em volta da bomba."""
    x0, y0, _ = P(k, 0, 0)
    cx, cy, _ = P(k, 8, 8)
    rnd = random.Random(k + 11)
    for i in range(7):  # terra batida irregular em volta da bomba
        r = rnd.uniform(1.6, 2.8)
        cyl('chao_terra', r, 0.02, cx + rnd.uniform(-2.8, 2.8), cy + rnd.uniform(-1.6, 1.6), 0.02 + i * 0.001,
            M['terra'] if i % 3 else M['terra2'], 'Z', 24, smooth=False)
    cyl('chao_oleo', 0.8, 0.02, cx + 1.8, cy - 0.2, 0.03, mat('Mancha de óleo', '#2a2622', 0.1, 0.4), 'Z', 16, smooth=False).scale = (1.4, 1.0, 1)


def cavalo_de_pau(k, ang, M):
    """Bomba de petróleo (cavalo-mecânico); ang = inclinação do balancim (animação)."""
    cx, cy, _ = P(k, 8, 8)
    bx('base', 6.0, 1.8, 0.4, (cx, cy, 0.2), M['concreto_esc'])
    # torre em A (samson post)
    for s in (-1, 1):
        bx('poste', 0.22, 0.22, 4.4, (cx + 0.2, cy + s * 0.6, 2.4), M['aco'], (s * math.radians(-8), 0, 0))
    hx, hz = cx + 0.2, 4.6
    bx('mancal', 0.4, 1.4, 0.3, (hx, cy, hz), M['aco'])
    # balancim girando em torno do mancal
    L = 6.0
    a = ang
    bx('balancim', L, 0.4, 0.45, (hx, cy, hz + 0.3), M['aco_claro'], (0, a, 0))
    # cabeça de cavalo na ponta (lado -X)
    xh = hx - (L / 2) * math.cos(a); zh = hz + 0.3 + (L / 2) * math.sin(a)
    prism('cabeca', [(0, -0.9), (0.9, -0.9), (0.9, 0.5), (0.2, 0.9), (0, 0.4)], 0.5, cy, M['aco_claro'], 'XZ').location = (xh - 0.9, 0, zh)
    bx('haste_bomba', 0.08, 0.08, max(0.3, zh - 1.2), (xh - 0.85, cy, (zh - 0.9) / 2 + 0.3), M['aco'])
    # contrapeso e biela no outro lado
    xc = hx + (L / 2) * math.cos(a); zc = hz + 0.3 - (L / 2) * math.sin(a)
    bx('biela', 0.15, 0.15, max(0.3, zc - 1.0), (xc - 0.1, cy + 0.5, (zc + 1.0) / 2), M['aco'])
    bx('manivela', 1.4, 0.3, 1.6, (cx + 2.6, cy + 0.7, 1.2), M['roda'], (0, a * 3, 0))
    bx('motor', 1.4, 1.0, 1.0, (cx + 2.6, cy - 0.3, 0.9), M['aco'])
    cyl('cabeca_poco', 0.3, 1.0, xh - 0.85, cy, 0.5, M['aco_claro'], 'Z', 12)


def pocos(k, M):
    from mathutils import Matrix
    chao_poco(k, M)
    for i, ang in enumerate([-0.2, -0.08, 0.06, 0.2, 0.08, -0.06]):
        antes = set(bpy.context.collection.objects)
        cavalo_de_pau(k + 1 + i, ang, M)
        c = Vector(P(k + 1 + i, 8, 8))
        T = Matrix.Translation(c) @ Matrix.Scale(1.3, 4) @ Matrix.Translation(-c)
        bpy.context.view_layer.update()
        for o in set(bpy.context.collection.objects) - antes:
            o.matrix_world = T @ o.matrix_world


INDUSTRIAS = [
    ('fazenda', [lambda M: casa_fazenda(0, M), lambda M: casa_pedra(1, M), lambda M: galpoes_feno(2, M),
                 lambda M: celeiro(3, M), lambda M: silos(4, M), lambda M: chiqueiro(5, M)]),
    ('fabrica', [lambda M: fabrica(0, M)]),
    ('serraria', [lambda M: serraria(0, M)]),
    ('pocos', [lambda M: pocos(0, M)]),
]


def exportar(slug, pecas):
    reset()
    MATS.clear()
    M = materiais()
    for p in pecas:
        p(M)
    for ob in bpy.context.collection.objects:
        ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, slug + '.glb'), use_selection=True, export_apply=True, export_format='GLB')
    print('OK', slug, len(bpy.context.collection.objects), 'peças')


if __name__ == '__main__':
    only = os.environ.get('ONLY')
    for slug, pecas in INDUSTRIAS:
        if only and slug not in only.split(','):
            continue
        exportar(slug, pecas)
