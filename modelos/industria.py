# Indústrias de 1950 (clima temperado) para substituir sprites base sem versão 4x no OpenGFX2 High Def.
# Cada peça (gfx de tile de indústria) fica num tile próprio, em fila: peça k no tile (k, 0), ou seja,
# X em [-12(k+1), -12k] e Y em [-12, 0]. Objetos de chão (montes, terra) começam com 'chao'.
# Uso: python3 industria.py -- <pasta_saida>
import bpy, bmesh, math, os, sys, random
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modelar import reset, MATS, mat, box, cyl, sphere, prism, new_obj, finish, OUT
from trens import bx, loft, toro

U = 0.75


def P(k, ox, oy, z=0.0):
    """Ponto em unidades do OpenTTD dentro do tile da peça k -> Blender."""
    return (-(16 * k + ox) * U, -oy * U, z)


def materiais():
    return {
        'tijolo': mat('Tijolo', '#8d4532', 0.0, 0.85),
        'tijolo_escuro': mat('Tijolo escuro', '#6e3527', 0.0, 0.85),
        'telha': mat('Telhado ardósia', '#3a3d42', 0.2, 0.6),
        'zinco': mat('Zinco ondulado', '#7a7f84', 0.6, 0.45),
        'aco': mat('Aço pintado', '#2f3337', 0.5, 0.5),
        'aco_claro': mat('Aço claro', '#6d7378', 0.6, 0.45),
        'roda': mat('Roda polia', '#c43d2b', 0.4, 0.45),
        'madeira': mat('Madeira escura', '#5a4129', 0.0, 0.85),
        'concreto': mat('Concreto', '#b3ada2', 0.0, 0.8),
        'concreto_esc': mat('Concreto sujo', '#8a857c', 0.0, 0.85),
        'vidro': mat('Vidro', '#24323b', 0.3, 0.1),
        'pedra': mat('Pedra', '#a69d8c', 0.0, 0.8),
        'terra': mat('Terra', '#6b4a2f', 0.0, 0.95),
        'terra2': mat('Terra escura', '#4f3826', 0.0, 0.95),
        'carvao': mat('Carvão', '#141416', 0.1, 0.75),
        'carvao2': mat('Carvão brilho', '#232327', 0.3, 0.5),
        'trilho': mat('Trilho', '#5c5650', 0.7, 0.4),
        'interior': mat('Interior escuro', '#141414', 0.0, 1.0),
        'cobre': mat('Cobre isolador', '#9a6a3a', 0.6, 0.4),
        'porcelana': mat('Porcelana', '#d9d4c8', 0.0, 0.3),
    }


def telhado_duas_aguas(x0, x1, y0, y1, z, h, m, eixo='X', beiral=0.25):
    """Telhado de duas águas com cumeeira ao longo do eixo dado."""
    if eixo == 'X':
        w = abs(y1 - y0) / 2 + beiral
        yc = (y0 + y1) / 2
        prism('telhado', [(-w, 0), (w, 0), (0, h)], abs(x1 - x0) + 2 * beiral, (x0 + x1) / 2, m, 'YZ') .location = (0, yc, z)
    else:
        w = abs(x1 - x0) / 2 + beiral
        xc = (x0 + x1) / 2
        prism('telhado', [(-w, 0), (w, 0), (0, h)], abs(y1 - y0) + 2 * beiral, (y0 + y1) / 2, m, 'XZ').location = (xc, 0, z)


def janelas(xa, xb, y, z0, n, M, alt=1.0, larg=0.6, lado=1, eixo='X'):
    for i in range(n):
        t = (i + 0.5) / n
        x = xa + (xb - xa) * t
        if eixo == 'X':
            bx('janela', larg, 0.04, alt, (x, y + lado * 0.02, z0), M['vidro'])
            bx('verga', larg + 0.15, 0.06, 0.12, (x, y + lado * 0.03, z0 + alt / 2 + 0.08), M['pedra'])
        else:
            bx('janela', 0.04, larg, alt, (y + lado * 0.02, x, z0), M['vidro'])
            bx('verga', 0.06, larg + 0.15, 0.12, (y + lado * 0.03, x, z0 + alt / 2 + 0.08), M['pedra'])


def trelica_pernas(xc, yc, sx, sy, h, M, n=3):
    """Pernas de aço com contraventamento sob uma construção elevada."""
    for i in range(n):
        for j in range(2):
            x = xc - sx / 2 + sx * i / (n - 1)
            y = yc - sy / 2 + sy * j
            bx('perna', 0.22, 0.22, h, (x, y, h / 2), M['aco'])
    for j in range(2):
        y = yc - sy / 2 + sy * j
        for i in range(n - 1):
            x0 = xc - sx / 2 + sx * i / (n - 1); x1 = xc - sx / 2 + sx * (i + 1) / (n - 1)
            L = math.hypot(x1 - x0, h)
            bx('diagonal', L, 0.08, 0.1, ((x0 + x1) / 2, y, h / 2), M['aco'], (0, math.atan2(h, x1 - x0), 0))


# ---------------- mina de carvão ----------------
def castelete(k, ang, M):
    """Torre de extração (castelete) de aço com duas polias e casa do poço de tijolo; ang = giro das polias."""
    cx, cy, _ = P(k, 11.5, 4.5)
    # casa do poço, elevada sobre estrutura
    trelica_pernas(cx, cy, 4.8, 4.4, 2.0, M)
    bx('casa_poco', 5.2, 4.8, 3.2, (cx, cy, 3.6), M['tijolo'], bevel=0.04)
    telhado_duas_aguas(cx - 2.6, cx + 2.6, cy - 2.4, cy + 2.4, 5.2, 1.4, M['zinco'], 'X')
    janelas(cx - 2.2, cx + 2.2, cy - 2.4, 3.8, 3, M, lado=-1)
    # castelete: 4 pernas verticais + 2 escoras inclinadas para a casa de máquinas
    H = 13.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            bx('castelete_perna', 0.3, 0.3, H - 1.0, (cx + sx * 1.2, cy + sy * 1.3, (H - 1.0) / 2 + 0.5), M['aco'])
    for z in (4.0, 7.0, 10.0):
        for sy in (-1, 1):
            bx('travessa', 2.7, 0.18, 0.18, (cx, cy + sy * 1.3, z), M['aco'])
        for sx in (-1, 1):
            bx('travessa', 0.18, 2.9, 0.18, (cx + sx * 1.2, cy, z), M['aco'])
    bx('plataforma', 3.2, 3.4, 0.2, (cx, cy, H - 0.4), M['aco_claro'])
    # escoras para trás (direção +X do Blender = para o canto norte), como no TTD
    for sy in (-1, 1):
        x0, z0 = cx + 1.2, H - 1.0
        x1, z1 = cx + 6.0, 0.3
        L = math.hypot(x1 - x0, z0 - z1)
        bx('escora', L, 0.32, 0.32, ((x0 + x1) / 2, cy + sy * 1.1, (z0 + z1) / 2), M['aco'], (0, math.atan2(z0 - z1, x1 - x0), 0))
    # polias (rodas) lado a lado, com raios girados por ang
    for sy in (-0.75, 0.75):
        y = cy + sy
        toro('polia_aro', 1.4, 0.1, cx, y, H + 0.9, M['roda'])
        cyl('polia_cubo', 0.18, 0.3, cx, y, H + 0.9, M['aco'], 'Y', 12)
        for i in range(8):
            a = ang + math.pi * i / 8
            bx('polia_raio', 0.07, 0.06, 2.7, (cx, y, H + 0.9), M['roda'], (0, a, 0))
        bx('mancal', 0.5, 0.4, 0.5, (cx, y, H + 0.25), M['aco'])
    # cabos descendo para a casa de máquinas
    for sy in (-0.75, 0.75):
        x0, z0 = cx + 1.4, H + 0.9
        x1, z1 = cx + 6.5, 4.0
        L = math.hypot(x1 - x0, z0 - z1)
        bx('cabo', L, 0.04, 0.04, ((x0 + x1) / 2, cy + sy, (z0 + z1) / 2), M['aco'], (0, math.atan2(z0 - z1, x1 - x0), 0))


def peneiramento(k, M):
    """Prédio de peneiramento/lavagem do carvão, comprido, sobre pilares (gfx 2, sub (1,2) 15x9)."""
    cx, cy, _ = P(k, 8.5, 6.5)
    trelica_pernas(cx, cy, 9.5, 5.2, 2.6, M, n=4)
    bx('corpo', 10.5, 6.0, 4.4, (cx, cy, 4.8), M['tijolo'], bevel=0.04)
    telhado_duas_aguas(cx - 5.25, cx + 5.25, cy - 3.0, cy + 3.0, 7.0, 1.8, M['telha'], 'X')
    janelas(cx - 4.8, cx + 4.8, cy - 3.0, 5.2, 6, M, lado=-1)
    janelas(cx - 4.8, cx + 4.8, cy + 3.0, 5.2, 6, M, lado=1)
    for i in range(4):
        x = cx - 4.2 + i * 2.8
        bx('lanternim', 0.9, 1.0, 0.6, (x, cy, 8.6), M['zinco'])
    # bica de descarga
    bx('bica', 1.2, 0.8, 1.0, (cx - 3.0, cy, 2.1), M['aco_claro'])


def silo_carvao(k, M):
    """Silo/casa de carregamento alta sobre pernas (gfx 3, sub (4,4) 9x9)."""
    cx, cy, _ = P(k, 8.5, 8.5)
    trelica_pernas(cx, cy, 5.2, 5.2, 3.2, M)
    bx('corpo', 6.0, 6.0, 6.0, (cx, cy, 6.2), M['tijolo'], bevel=0.04)
    telhado_duas_aguas(cx - 3.0, cx + 3.0, cy - 3.0, cy + 3.0, 9.2, 2.0, M['telha'], 'Y')
    janelas(cy - 2.5, cy + 2.5, cx - 3.0, 6.5, 3, M, lado=1, eixo='Y')
    janelas(cx - 2.5, cx + 2.5, cy - 3.0, 6.5, 3, M, lado=-1)
    janelas(cx - 2.5, cx + 2.5, cy - 3.0, 8.2, 3, M, lado=-1, alt=0.7)
    bx('funil', 3.2, 3.2, 1.0, (cx, cy, 2.7), M['aco_claro'])
    # esteira inclinada saindo do silo
    L = 6.5
    bx('esteira', L, 1.2, 0.5, (cx + 3.4, cy, 5.8), M['zinco'], (0, math.radians(25), 0))


def chao_terra(k, M, monte=None, semente=1):
    """Chão de mina (terra) com, opcionalmente, montes de carvão. Objetos 'chao*' vão para o sprite de chão."""
    x0, y0, _ = P(k, 0, 0)
    bx('chao_terra', 12.0, 12.0, 0.02, (x0 - 6, y0 - 6, 0.01), M['terra'])
    rnd = random.Random(semente)
    for i in range(14):
        x = x0 - rnd.uniform(1, 11); y = y0 - rnd.uniform(1, 11)
        bx('chao_mancha', rnd.uniform(1, 2.5), rnd.uniform(0.6, 1.5), 0.02, (x, y, 0.035 + i * 0.002), M['terra2'], (0, 0, rnd.uniform(0, 3)))
    if monte:
        for (ox, oy, r, h) in monte:
            x, y, _ = P(k, ox, oy)
            sphere('chao_monte', 1.0, x, y, 0.0, M['carvao'], r, r * 0.85, h)
            for j in range(6):
                a = rnd.uniform(0, 2 * math.pi); d = rnd.uniform(0.3, 0.8) * r
                sphere('chao_monte_pedra', 1.0, x + math.cos(a) * d, y + math.sin(a) * d, h * 0.25, M['carvao2'], r * 0.25, r * 0.22, h * 0.35)


# ---------------- usina termelétrica ----------------
def torre_resfriamento(k, M):
    """Torre de resfriamento hiperbólica de concreto (gfx 7, sub (1,1) 14x14)."""
    cx, cy, _ = P(k, 8, 8)
    perfil = [(0.0, 5.0), (2.0, 4.5), (5.0, 3.9), (8.5, 3.45), (11.0, 3.5), (13.5, 3.8)]
    bm = bmesh.new()
    n = 48
    aneis = []
    for (z, r) in perfil:
        aneis.append([bm.verts.new((cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n), z)) for i in range(n)])
    for a, b in zip(aneis, aneis[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = new_obj('torre', bm)
    finish(ob, M['concreto'], smooth=True)
    so = ob.modifiers.new('esp', 'SOLIDIFY'); so.thickness = 0.25
    cyl('torre_interior', 3.6, 0.1, cx, cy, 11.5, M['interior'], 'Z', 48)
    # pilares em V da base
    for i in range(24):
        a = 2 * math.pi * i / 24
        bx('pilar_base', 0.25, 0.25, 1.4, (cx + 5.0 * math.cos(a), cy + 5.0 * math.sin(a), 0.7), M['concreto_esc'], (0, 0, a))
    toro('anel_topo', 3.8, 0.12, cx, cy, 13.5, M['concreto_esc']).rotation_euler = (0, 0, 0)
    # manchas de umidade: faixas mais escuras
    for z in (3.0, 6.5):
        r = 4.3 if z < 5 else 3.6
        toro('mancha', r + 0.02, 0.35, cx, cy, z, M['concreto_esc']).rotation_euler = (0, 0, 0)


def casa_caldeiras(k, M):
    """Casa de caldeiras de tijolo com chaminé alta (gfx 8, sub (0,2) 16x12)."""
    cx, cy, _ = P(k, 8, 8)
    bx('corpo', 11.0, 8.0, 7.5, (cx, cy, 3.75), M['tijolo'], bevel=0.04)
    telhado_duas_aguas(cx - 5.5, cx + 5.5, cy - 4.0, cy + 4.0, 7.5, 2.0, M['telha'], 'X')
    for lado in (-1, 1):
        for i in range(5):
            x = cx - 4.4 + i * 2.2
            bx('janela_alta', 1.1, 0.04, 4.2, (x, cy + lado * 4.02, 3.9), M['vidro'])
            bx('arco', 1.3, 0.06, 0.25, (x, cy + lado * 4.03, 6.1), M['pedra'])
            bx('pilastra', 0.35, 0.12, 7.5, (x + 1.1, cy + lado * 4.05, 3.75), M['tijolo_escuro'])
    # chaminé
    hx, hy = cx - 3.5, cy + 0.0
    cyl('chamine_base', 1.4, 2.0, hx, hy, 8.5, M['tijolo_escuro'], 'Z', 24)
    cyl('chamine', 1.15, 16.0, hx, hy, 17.0, M['tijolo'], 'Z', 24, r2=0.85)
    for z in (12.0, 18.0, 24.5):
        cyl('chamine_anel', 1.25 - (z - 9) * 0.018, 0.25, hx, hy, z, M['aco'], 'Z', 24)
    cyl('chamine_topo', 0.95, 0.5, hx, hy, 25.2, M['aco'], 'Z', 24)
    cyl('chamine_boca', 0.75, 0.1, hx, hy, 25.46, M['interior'], 'Z', 24)


def sala_turbinas(k, M):
    """Sala das turbinas/administração, prédio mais baixo (gfx 9, sub (1,0) 14x15)."""
    cx, cy, _ = P(k, 8, 7.5)
    bx('corpo', 9.5, 10.0, 5.0, (cx, cy, 2.5), M['tijolo'], bevel=0.04)
    telhado_duas_aguas(cx - 4.75, cx + 4.75, cy - 5.0, cy + 5.0, 5.0, 1.8, M['telha'], 'Y')
    janelas(cy - 4.2, cy + 4.2, cx - 4.75, 3.0, 5, M, alt=2.2, larg=0.9, lado=1, eixo='Y')
    janelas(cx - 4.0, cx + 4.0, cy - 5.0, 3.0, 4, M, alt=2.2, larg=0.9, lado=-1)
    bx('porta', 1.8, 0.05, 2.4, (cx, cy - 5.02, 1.2), M['madeira'])
    bx('marquise', 2.6, 0.9, 0.12, (cx, cy - 5.4, 2.6), M['concreto'])


def subestacao(k, M):
    """Pátio de transformadores com pórticos (gfx 10, sub (1,2) 14x11)."""
    cx, cy, _ = P(k, 8, 7.5)
    bx('base', 10.0, 8.0, 0.25, (cx, cy, 0.12), M['concreto_esc'])
    for i, x in enumerate((cx - 3, cx + 0, cx + 3)):
        bx('trafo', 1.8, 2.2, 2.2, (x, cy + 1.0, 1.35), M['aco_claro'], bevel=0.05)
        for j in range(4):
            bx('aleta', 0.06, 2.4, 1.6, (x - 0.9 - 0.04, cy + 1.0, 1.3 - 0 * j), M['aco'])
        for j in (-0.5, 0, 0.5):
            cyl('bucha', 0.12, 0.9, x + j, cy + 1.0, 2.9, M['porcelana'], 'Z', 10)
    for x in (cx - 4.5, cx + 4.5):
        for y in (cy - 2.5, cy + 3.0):
            bx('portico_coluna', 0.3, 0.3, 6.0, (x, y, 3.0), M['aco'])
    for y in (cy - 2.5, cy + 3.0):
        bx('portico_viga', 9.3, 0.3, 0.4, (cx, y, 6.0), M['aco'])
        for x in (cx - 3, cx, cx + 3):
            cyl('isolador', 0.1, 0.8, x, y, 5.4, M['porcelana'], 'Z', 8)
    for x in (cx - 3, cx, cx + 3):
        bx('cabo', 0.04, 5.5, 0.04, (x, cy + 0.25, 5.0), M['cobre'])
    # cerca
    for y in (cy - 4.0, cy + 4.0):
        bx('cerca', 10.0, 0.03, 1.6, (cx, y, 0.8), M['aco_claro'])


MINA = [  # (peça, construtor) — peça k fica no tile (k, 0)
    lambda M: castelete(0, 0.0, M),
    lambda M: castelete(1, math.pi / 24, M),
    lambda M: castelete(2, math.pi / 12, M),
    lambda M: peneiramento(3, M),
    lambda M: silo_carvao(4, M),
    lambda M: chao_terra(5, M, semente=2),
    lambda M: chao_terra(6, M, [(8, 8, 4.0, 2.2)], semente=3),
    lambda M: chao_terra(7, M, [(6, 6, 3.0, 1.6), (11, 10, 2.6, 1.3)], semente=4),
    lambda M: chao_terra(8, M, [(9, 7, 3.4, 1.9), (4, 11, 2.0, 1.0)], semente=5),
]
USINA = [
    lambda M: torre_resfriamento(0, M),
    lambda M: casa_caldeiras(1, M),
    lambda M: sala_turbinas(2, M),
    lambda M: subestacao(3, M),
]
INDUSTRIAS = [('mina_carvao', MINA), ('usina', USINA)]


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
