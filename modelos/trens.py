# Modela os trens de 1950 (clima temperado) do OpenTTD em tamanho real e exporta em GLB.
# Locomotivas: Kirby Paul Tank (GWR 5700), Chaney 'Jubilee' (LMS Jubilee), Ginzu 'A4' (LNER A4),
# SH '8P' (BR Standard 8P 71000). Vagões: os 11 vagões temperados, tipos britânicos de 4 rodas.
# Eixos: X = frente, Y = esquerda, Z = cima. Origem no topo do trilho, centro do veículo. Metros.
# Uso: python3 trens.py -- <pasta_saida>   (ONLY=slug para um só)
import bpy, bmesh, math, os, sys
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modelar import (reset, MATS, mat, box, cyl, sphere, prism, arc, new_obj, finish, OUT)

BITOLA = 0.75   # metade da distância entre as faces das rodas (bitola 1,435 m)


def materiais_trem():
    return {
        'paint': mat('Pintura empresa', '#7a1f1f', 0.0, 0.3),
        'black': mat('Preto fosco', '#141516', 0.0, 0.55),
        'gloss': mat('Preto esmaltado', '#16181a', 0.0, 0.3),
        'smoke': mat('Caixa de fumaça', '#1c1d1e', 0.2, 0.6),
        'steel': mat('Aço polido', '#9aa0a6', 0.9, 0.3),
        'brass': mat('Latão', '#c9a24a', 0.9, 0.25),
        'copper': mat('Cobre', '#b8693a', 0.9, 0.3),
        'glass': mat('Vidro', '#1d2a33', 0.2, 0.05),
        'lamp': mat('Lente', '#f3f1e6', 0.0, 0.1),
        'white': mat('Branco', '#e8e6df', 0.0, 0.5),
        'red': mat('Vermelho', '#9a1a14', 0.0, 0.4),
        'roof': mat('Teto cinza', '#55585b', 0.1, 0.7),
        'wood': mat('Madeira', '#7d5c3c', 0.0, 0.85),
        'bauxite': mat('Bauxita', '#6e3524', 0.0, 0.7),
        'grey': mat('Cinza vagão', '#6c7176', 0.3, 0.6),
        'cream': mat('Creme', '#e2d6b6', 0.0, 0.45),
        'coal': mat('Carvão', '#101012', 0.0, 0.8),
        'ore': mat('Minério de ferro', '#7a3e26', 0.0, 0.9),
        'grain': mat('Grão', '#d4b25e', 0.0, 0.9),
        'log': mat('Tora', '#7b5a3a', 0.0, 0.9),
        'logend': mat('Topo da tora', '#c9a77a', 0.0, 0.9),
        'tank': mat('Tanque', '#2a2b2d', 0.3, 0.45),
        'plate': mat('Chapa de aço', '#5b6066', 0.7, 0.45),
    }


# ---------------- utilidades ----------------
def bx(name, sx, sy, sz, loc, m, rot=(0, 0, 0), bevel=0.0):
    """Caixa com rotação própria (centro em loc)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz))
    ob = new_obj(name, bm)
    ob.location = loc
    ob.rotation_euler = rot
    return finish(ob, m, bevel)


def toro(name, R, r, x, y, z, m):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=40, minor_segments=8,
                                     location=(x, y, z), rotation=(math.pi / 2, 0, 0))
    ob = bpy.context.active_object
    ob.name = name
    return finish(ob, m, smooth=True)


def loft(name, secoes, m, n=24):
    """Casco por seções transversais: (x, meia_largura, z_baixo, z_alto, expoente). Expoente 2 = elipse,
    maior = mais quadrado. Fecha as pontas."""
    bm = bmesh.new()
    rings = []
    for (x, hw, zb, zt, e) in secoes:
        zc, hh = (zb + zt) / 2, (zt - zb) / 2
        ring = []
        for i in range(n):
            t = 2 * math.pi * i / n
            c, s = math.cos(t), math.sin(t)
            y = hw * math.copysign(abs(c) ** (2 / e), c)
            z = zc + hh * math.copysign(abs(s) ** (2 / e), s)
            ring.append(bm.verts.new((x, y, z)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(rings[0])
    bm.faces.new(rings[-1][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = new_obj(name, bm)
    return finish(ob, m, smooth=True)


# ---------------- peças de material rodante ----------------
def rodeiro(name, x, r, M, raios=True, cor='black'):
    """Par de rodas com eixo. Rodas grandes têm raios, aro e contrapeso."""
    for s in (1, -1):
        y = s * (BITOLA - 0.07)
        if raios and r > 0.55:
            toro(f'{name}_aro{s}', r - 0.06, 0.06, x, y, r, M['steel'])
            cyl(f'{name}_fundo{s}', r - 0.1, 0.03, x, y - s * 0.05, r, M['black'], 'Y', 32)
            cyl(f'{name}_cubo{s}', r * 0.17, 0.16, x, y, r, M[cor], 'Y', 16)
            nr = 16 if r > 0.9 else 12
            for i in range(nr):
                a = 2 * math.pi * i / nr
                bx(f'{name}_raio{s}{i}', 0.045, 0.05, r * 0.82, (x + math.sin(a) * r * 0.45, y, r + math.cos(a) * r * 0.45), M[cor], (0, a, 0))
            # contrapeso em crescente
            bx(f'{name}_contrapeso{s}', r * 0.55, 0.07, r * 0.22, (x, y + s * 0.01, r - r * 0.62), M[cor])
        else:
            cyl(f'{name}_roda{s}', r, 0.13, x, y, r, M['black'], 'Y', 28)
            cyl(f'{name}_face{s}', r * 0.94, 0.135, x, y, r, M['steel'] if r < 0.55 else M[cor], 'Y', 28)
            cyl(f'{name}_disco{s}', r * 0.7, 0.14, x, y, r, M['black'], 'Y', 24)
            cyl(f'{name}_cubo{s}', r * 0.2, 0.18, x, y, r, M['steel'], 'Y', 12)
        cyl(f'{name}_friso{s}', r + 0.03, 0.025, x, y - s * 0.075, r, M['black'], 'Y', 28)
    cyl(f'{name}_eixo', 0.08, 2 * BITOLA, x, 0, r, M['black'], 'Y', 10)


def bielas(xs, r, M, cor='steel', fase=0.0):
    """Bielas de acoplamento ligando as rodas motrizes de cada lado."""
    for s in (1, -1):
        y = s * (BITOLA + 0.04)
        a = fase + (0 if s > 0 else math.pi / 2)
        dx, dz = math.cos(a) * r * 0.4, math.sin(a) * r * 0.4
        for x in xs:
            cyl(f'pino{s}{x:.1f}', 0.06, 0.12, x + dx, y, r + dz, M['steel'], 'Y', 10)
        x0, x1 = min(xs), max(xs)
        bx(f'biela{s}', x1 - x0 + 0.24, 0.05, 0.09, ((x0 + x1) / 2 + dx, y + s * 0.05, r + dz), M[cor], bevel=0.02)


def para_choques(x, M, sentido):
    """Viga de para-choque e dois amortecedores (buffers) apontando no sentido dado (+1 frente)."""
    bx('viga', 0.16, 2.6, 0.42, (x, 0, 1.05), M['red'])
    for s in (1, -1):
        cyl('buffer_corpo', 0.11, 0.32, x + sentido * 0.24, s * 0.87, 1.05, M['black'], 'X', 14)
        cyl('buffer_haste', 0.05, 0.2, x + sentido * 0.45, s * 0.87, 1.05, M['steel'], 'X', 10)
        cyl('buffer_cabeca', 0.19, 0.05, x + sentido * 0.56, s * 0.87, 1.05, M['steel'], 'X', 18)
    bx('engate', 0.3, 0.06, 0.06, (x + sentido * 0.3, 0, 1.0), M['black'])


def lampiao(x, y, z, M):
    bx('lampiao', 0.14, 0.16, 0.2, (x, y, z), M['white'])
    cyl('lampiao_lente', 0.055, 0.02, x + 0.08, y, z, M['lamp'], 'X', 12)


def chamine(x, zbase, h, r, M, topo='black'):
    cyl('chamine', r, h, x, 0, zbase + h / 2, M['black'], 'Z', 20)
    cyl('chamine_borda', r * 1.18, 0.1, x, 0, zbase + h - 0.05, M[topo], 'Z', 20)
    cyl('chamine_base', r * 1.35, 0.14, x, 0, zbase + 0.04, M['black'], 'Z', 20)


def domo(x, zc, rcald, r, h, M, cor):
    cyl('domo', r, h + rcald * 0.3, x, 0, zc + rcald + h / 2 - rcald * 0.15, M[cor], 'Z', 20)
    sphere('domo_topo', r, x, 0, zc + rcald + h, M[cor], 1, 1, 0.45)


def cabine(x0, x1, zpiso, ztopo, larg, M, janela_lateral=True, cor='paint'):
    """Cabine de locomotiva a vapor: frente com janelas redondas, laterais com abertura e teto curvo."""
    hw = larg / 2
    bx('cab_frente', 0.06, larg, ztopo - zpiso - 0.15, (x0, 0, (zpiso + ztopo - 0.15) / 2), M[cor])
    for s in (1, -1):
        cyl('cab_vidro_frente', 0.17, 0.04, x0 + 0.03, s * 0.65, ztopo - 0.75, M['glass'], 'X', 16)
        cyl('cab_aro_frente', 0.2, 0.03, x0 + 0.02, s * 0.65, ztopo - 0.75, M['brass'], 'X', 16)
        # lateral: painel baixo inteiro + coluna da frente + abertura de acesso
        bx('cab_lado_baixo', x0 - x1, 0.06, 1.0, ((x0 + x1) / 2, s * hw, zpiso + 0.5), M[cor])
        bx('cab_lado_coluna', 0.5, 0.06, ztopo - zpiso - 1.0, (x0 - 0.25, s * hw, zpiso + 1.0 + (ztopo - zpiso - 1.0) / 2), M[cor])
        if janela_lateral:
            bx('cab_janela', 0.42, 0.065, 0.42, (x0 - 0.25, s * hw, ztopo - 0.6), M['glass'])
        bx('cab_interior', x0 - x1 - 0.5, 0.02, ztopo - zpiso - 1.0, ((x0 + x1) / 2 - 0.25, s * (hw - 0.3), zpiso + 1.0 + (ztopo - zpiso - 1.0) / 2), M['black'])
        bx('cab_corrimao', 0.04, 0.04, 1.0, (x1 + 0.08, s * (hw + 0.03), zpiso + 1.2), M['brass'])
    teto = [(hw + 0.08, ztopo - 0.2)] + [(hw * 1.02 * math.cos(math.radians(a)), ztopo - 0.18 + 0.22 * math.sin(math.radians(a))) for a in range(0, 181, 15)] + [(-hw - 0.08, ztopo - 0.2)]
    prism('cab_teto', teto, x0 - x1 + 0.2, (x0 + x1) / 2 - 0.05, M['roof'], 'YZ', 0.02)
    bx('cab_piso', x0 - x1, larg, 0.08, ((x0 + x1) / 2, 0, zpiso), M['black'])


def truque(x, r, M, entre=1.9):
    """Truque de 2 eixos (bogie dianteiro ou do tênder)."""
    for dx in (entre / 2, -entre / 2):
        rodeiro('truque', x + dx, r, M, raios=False)
    for s in (1, -1):
        bx('truque_lado', entre + 0.6, 0.08, 0.32, (x, s * (BITOLA + 0.12), r + 0.05), M['black'], bevel=0.03)


# ---------------- tênderes ----------------
def tender(x0, x1, ztopo, M, rodas, r, larg=2.55, tipo='fowler'):
    """Tênder de 6 ou 8 rodas. x0 = frente (lado da locomotiva)."""
    hw = larg / 2
    zb = 1.3
    bx('tender_quadro', x0 - x1, 2.2, 0.32, ((x0 + x1) / 2, 0, zb - 0.2), M['black'])
    for s in (1, -1):
        bx('tender_longarina', x0 - x1 - 0.3, 0.08, 0.55, ((x0 + x1) / 2, s * (BITOLA + 0.2), r + 0.1), M['black'])
    for xr in rodas:
        rodeiro('tender_roda', xr, r, M, raios=False)
        for s in (1, -1):
            bx('tender_mancal', 0.3, 0.14, 0.28, (xr, s * (BITOLA + 0.24), r), M['black'])
    if tipo == 'corredor':  # tênder do A4: laterais lisas e altas, cantos arredondados
        loft('tender_corpo', [(x0, hw, zb, ztopo, 6), (x1, hw, zb, ztopo, 6)], M['paint'])
        bx('tender_porta_corredor', 0.02, 0.6, 1.6, (x1 - 0.01, 0, zb + 0.95), M['black'])
        bx('tender_frisa', x0 - x1, 0.02, 0.05, ((x0 + x1) / 2, hw + 0.01, zb + 0.15), M['steel'])
        bx('tender_carvao', 2.6, larg - 0.5, 0.25, (x0 - 1.6, 0, ztopo - 0.05), M['coal'])
    else:
        bx('tender_corpo', x0 - x1, larg, ztopo - zb, ((x0 + x1) / 2, 0, (zb + ztopo) / 2), M['paint'], bevel=0.04)
        # bordas superiores viradas para fora (flare) e carvão aparente
        for s in (1, -1):
            bx('tender_aba', x0 - x1 - 0.6, 0.1, 0.18, ((x0 + x1) / 2 + 0.3, s * (hw + 0.03), ztopo + 0.05), M['paint'])
        bx('tender_carvao', (x0 - x1) * 0.62, larg - 0.3, 0.45, (x0 - (x0 - x1) * 0.33, 0, ztopo + 0.1), M['coal'], bevel=0.12)
        bx('tender_tanque_tampa', 0.5, 0.5, 0.12, (x1 + 0.7, 0, ztopo + 0.06), M['black'])
        bx('tender_frisa', x0 - x1, 0.02, 0.04, ((x0 + x1) / 2, hw + 0.01, zb + 0.12), M['black'])
    para_choques(x1 - 0.08, M, -1)
    lampiao(x1 - 0.2, 0.85, 1.55, M)


# ---------------- locomotivas ----------------
def kirby_paul_tank(M):
    """GWR 5700 (pannier tank 0-6-0PT), 9,6 m reduzida para 9,0 m."""
    L = 9.0
    xf, xr = L / 2 - 0.56, -L / 2 + 0.56          # vigas de para-choque
    R = 0.7
    eixos = [1.95, -0.3, -2.55]
    # quadro e estrado
    for s in (1, -1):
        bx('quadro', xf - xr, 0.08, 0.75, ((xf + xr) / 2, s * (BITOLA - 0.2), 0.95), M['black'])
    bx('estrado', xf - xr, 2.6, 0.08, ((xf + xr) / 2, 0, 1.32), M['black'])
    for s in (1, -1):
        bx('estrado_borda', xf - xr, 0.04, 0.16, ((xf + xr) / 2, s * 1.3, 1.26), M['paint'])
    for x in eixos:
        rodeiro('roda', x, R, M)
        for s in (1, -1):  # paralamas sobre as rodas
            bx('paralama', 1.45, 0.4, 0.06, (x, s * 0.95, 1.38), M['black'])
    bielas(eixos, R, M)
    para_choques(xf, M, 1)
    para_choques(xr, M, -1)
    # caixa de fumaça, caldeira, fornalha Belpaire
    zc = 2.2
    cyl('caixa_fumaca', 0.8, 0.85, xf - 0.5, 0, zc, M['smoke'], 'X', 36)
    cyl('porta_fumaca', 0.68, 0.08, xf - 0.06, 0, zc, M['smoke'], 'X', 36)
    cyl('porta_trinco', 0.06, 0.12, xf + 0.0, 0, zc, M['steel'], 'X', 10)
    bx('selim', 0.8, 1.2, 0.5, (xf - 0.5, 0, 1.55), M['smoke'])
    cyl('caldeira', 0.74, 3.1, xf - 0.9 - 1.55, 0, zc, M['paint'], 'X', 36)
    for xb in (xf - 1.0, xf - 2.0, xf - 3.0, xf - 3.9):
        cyl('cinta', 0.755, 0.05, xb, 0, zc, M['brass'], 'X', 36)
    fx0, fx1 = xf - 4.0, xf - 5.3
    bx('fornalha', fx0 - fx1, 1.55, 1.45, ((fx0 + fx1) / 2, 0, 2.27), M['paint'], bevel=0.12)
    chamine(xf - 0.5, zc + 0.6, 0.85, 0.24, M, 'copper')
    # tanques em sela lateral (pannier)
    t0, t1 = xf - 0.95, fx1 - 0.05
    for s in (1, -1):
        bx('tanque', t0 - t1, 0.64, 1.15, ((t0 + t1) / 2, s * 0.86, 2.55), M['paint'], bevel=0.1)
        bx('tanque_tampa', 0.35, 0.3, 0.08, (t0 - 0.9, s * 0.86, 3.16), M['brass'])
        bx('tanque_friso', t0 - t1, 0.02, 0.04, ((t0 + t1) / 2, s * 1.18, 2.05), M['black'])
    # válvula de segurança em capa de latão
    cyl('valvula', 0.2, 0.4, xf - 3.3, 0, 3.15, M['brass'], 'Z', 20)
    sphere('valvula_topo', 0.2, xf - 3.3, 0, 3.35, M['brass'], 1, 1, 0.5)
    cyl('apito', 0.04, 0.35, fx1 + 0.1, 0.3, 3.2, M['brass'], 'Z', 8)
    # cabine e carvoeira
    c0, c1 = fx1, fx1 - 1.9
    cabine(c0, c1, 1.36, 3.75, 2.55, M)
    bx('carvoeira', c1 - xr, 2.4, 1.3, ((c1 + xr) / 2, 0, 2.0), M['paint'], bevel=0.04)
    bx('carvao', c1 - xr - 0.2, 2.0, 0.25, ((c1 + xr) / 2, 0, 2.7), M['coal'], bevel=0.08)
    bx('carvoeira_traseira', 0.06, 2.4, 1.2, (xr + 0.03, 0, 2.6), M['paint'])
    for s in (1, -1):
        lampiao(xf + 0.05, s * 0.7, 1.55, M)
        bx('degrau', 0.3, 0.2, 0.04, (xf - 0.3, s * 1.32, 0.75), M['black'])
        cyl('caixa_areia', 0.18, 0.5, eixos[0] + 0.9, s * 0.9, 1.6, M['black'], 'Z', 12)
    lampiao(xr - 0.05, 0.7, 1.55, M)


def caldeira_classica(xf, x_cald1, rf, rt, zc, M, cor='paint'):
    """Caixa de fumaça + caldeira cônica (de rf a rt) até x_cald1."""
    cyl('caixa_fumaca', rf + 0.06, 1.25, xf - 0.62, 0, zc, M['smoke'], 'X', 40)
    cyl('porta_fumaca', rf - 0.08, 0.1, xf - 0.02, 0, zc, M['smoke'], 'X', 40)
    cyl('porta_trinco', 0.07, 0.14, xf + 0.05, 0, zc, M['steel'], 'X', 10)
    L = xf - 1.25 - x_cald1
    # cone: raio cresce para trás
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=40, radius1=rt, radius2=rf, depth=L)
    ob = new_obj('caldeira', bm)
    ob.rotation_euler = (0, math.pi / 2, 0)
    ob.location = (x_cald1 + L / 2, 0, zc)
    finish(ob, M[cor], smooth=True)
    n = 4
    for i in range(1, n + 1):
        x = xf - 1.25 - L * i / (n + 1)
        rr = rf + (rt - rf) * (i / (n + 1))
        cyl('cinta', rr + 0.015, 0.05, x, 0, zc, M['brass'], 'X', 40)


def estrado_alto(x0, x1, z, larg, M, cor='black'):
    bx('estrado', x0 - x1, larg, 0.07, ((x0 + x1) / 2, 0, z), M[cor])
    for s in (1, -1):
        bx('estrado_borda', x0 - x1, 0.04, 0.2, ((x0 + x1) / 2, s * larg / 2, z - 0.07), M['paint'])


def cilindro_externo(x, z, r, M, cor='black'):
    for s in (1, -1):
        cyl('cilindro', r, 1.2, x, s * 1.12, z, M[cor], 'X', 24)
        cyl('cilindro_tampa', r * 1.06, 0.08, x + 0.62, s * 1.12, z, M['steel'], 'X', 24)
        bx('cruzeta_guia', 1.6, 0.06, 0.1, (x - 1.3, s * 1.12, z), M['steel'])
        bx('biela_motriz', 2.4, 0.05, 0.1, (x - 2.0, s * (BITOLA + 0.1), z - 0.15), M['steel'], (0, 0.12, 0))


def chaney_jubilee(M):
    """LMS Jubilee (4-6-0) com tênder Fowler de 3.500 galões; 19,5 m."""
    L = 19.5
    xf = L / 2 - 0.56
    xr = -L / 2 + 0.56
    Rd, Rb = 1.03, 0.48
    motrizes = [3.6, 1.45, -0.75]
    estr_z = 1.62
    for s in (1, -1):
        bx('quadro', xf - (-3.4), 0.08, 0.8, ((xf - 3.4) / 2, s * (BITOLA - 0.2), 1.05), M['black'])
    truque(7.6, Rb, M, 1.95)
    for x in motrizes:
        rodeiro('motriz', x, Rd, M)
    bielas(motrizes, Rd, M)
    cilindro_externo(7.0, 1.05, 0.34, M)
    estrado_alto(xf, -3.4, estr_z, 2.7, M)
    for s in (1, -1):  # paralamas das motrizes (splashers)
        for x in motrizes:
            arco = arc(x, Rd, Rd + 0.08, 15, 165, 12)
            prism('paralama', arco + [(x - Rd, estr_z), (x + Rd, estr_z)], 0.08, s * 1.0, M['paint'], 'XZ')
    para_choques(xf, M, 1)
    zc = 2.85
    caldeira_classica(xf, 0.4, 0.82, 0.92, zc, M)
    bx('selim', 1.2, 1.4, 0.8, (xf - 0.62, 0, 2.0), M['smoke'])
    # Belpaire
    bx('fornalha', 2.0, 1.75, 1.75, (-0.6, 0, 2.95), M['paint'], bevel=0.14)
    chamine(xf - 0.7, zc + 0.7, 0.55, 0.26, M)
    domo(4.4, zc, 0.86, 0.32, 0.25, M, 'paint')
    cyl('alimentador', 0.14, 0.2, 6.0, 0, zc + 0.95, M['brass'], 'Z', 12)
    cyl('valvulas', 0.1, 0.3, -0.6, 0, 3.95, M['brass'], 'Z', 10)
    cabine(-1.6, -3.3, estr_z + 0.05, 4.05, 2.6, M)
    for s in (1, -1):
        lampiao(xf + 0.05, s * 0.75, estr_z + 0.25, M)
        bx('degrau', 0.3, 0.25, 0.04, (-3.0, s * 1.35, 0.9), M['black'])
    lampiao(xf + 0.05, 0, zc + 0.95, M)
    tender(-3.55, xr, 3.0, M, [-4.6, -6.6, -8.6], 0.64, tipo='fowler')


def ginzu_a4(M):
    """LNER A4 (4-6-2) aerodinâmica com tênder de corredor; 21,0 m. Em 1950 já sem as saias sobre as rodas."""
    L = 21.0
    xf = L / 2 - 0.3
    xr = -L / 2 + 0.56
    Rd, Rb, Rt = 1.02, 0.48, 0.6
    motrizes = [4.3, 2.25, 0.2]
    for s in (1, -1):
        bx('quadro', xf - 0.4 + 2.9, 0.08, 0.8, ((xf - 0.4 - 2.9) / 2, s * (BITOLA - 0.2), 1.05), M['black'])
    truque(8.0, Rb, M, 2.0)
    for x in motrizes:
        rodeiro('motriz', x, Rd, M)
    bielas(motrizes, Rd, M)
    rodeiro('traseira', -2.1, Rt, M, raios=False)
    cilindro_externo(7.2, 1.05, 0.33, M)
    # casco aerodinâmico em cunha: seções de frente para trás
    sec = [
        (xf + 0.05, 0.25, 1.15, 1.45, 2.2),
        (xf - 0.35, 0.95, 1.05, 2.05, 2.6),
        (xf - 0.9, 1.22, 1.05, 2.75, 3.2),
        (xf - 1.6, 1.32, 1.1, 3.35, 3.6),
        (xf - 2.4, 1.36, 1.6, 3.8, 4.0),
        (xf - 3.0, 1.36, 1.9, 3.98, 4.4),
        (-1.0, 1.36, 1.9, 4.0, 4.4),
    ]
    loft('casco', sec, M['paint'])
    estrado_alto(xf - 2.8, -1.0, 1.95, 2.7, M)
    bx('frente_baixa', 0.5, 1.6, 0.35, (xf - 0.25, 0, 1.0), M['black'])
    cyl('chamine_dupla', 0.22, 0.12, xf - 3.2, 0.25, 4.0, M['black'], 'Z', 16)
    cyl('chamine_dupla2', 0.22, 0.12, xf - 3.2, -0.25, 4.0, M['black'], 'Z', 16)
    for s in (1, -1):
        bx('friso_casco', xf - 1.0, 0.02, 0.06, ((xf - 1.0 - 1.0) / 2, s * 1.37, 2.05), M['steel'])
        lampiao(xf - 0.6, s * 0.7, 1.9, M)
    # cabine com frente em cunha
    for s in (1, -1):
        prism('cab_lado', [(-1.0, 1.65), (-1.0, 4.0), (-1.6, 4.2), (-3.4, 4.2), (-3.4, 1.65)], 0.06, s * 1.33, M['paint'], 'XZ')
        bx('cab_janela', 0.6, 0.065, 0.5, (-2.0, s * 1.33, 3.45), M['glass'])
        bx('cab_janela2', 0.5, 0.065, 0.45, (-2.8, s * 1.33, 3.45), M['glass'])
    prism('cab_teto', [(1.4, 4.05)] + [(1.35 * math.cos(math.radians(a)), 4.05 + 0.22 * math.sin(math.radians(a))) for a in range(0, 181, 15)] + [(-1.4, 4.05)], 2.4, -2.3, M['roof'], 'YZ')
    para_choques(xf - 0.6, M, 1)
    tender(-3.65, xr, 3.85, M, [-4.7, -6.3, -7.9, -9.3], 0.55, larg=2.7, tipo='corredor')


def sh_8p(M):
    """BR Standard Class 8 nº 71000 'Duke of Gloucester' (4-6-2) com tênder BR1J; 21,0 m."""
    L = 21.0
    xf = L / 2 - 0.56
    xr = -L / 2 + 0.56
    Rd, Rb, Rt = 0.94, 0.48, 0.5
    motrizes = [4.6, 2.55, 0.5]
    estr_z = 2.08
    for s in (1, -1):
        bx('quadro', xf + 2.6, 0.08, 0.9, ((xf - 2.6) / 2, s * (BITOLA - 0.2), 1.1), M['black'])
    truque(8.3, Rb, M, 1.95)
    for x in motrizes:
        rodeiro('motriz', x, Rd, M)
    bielas(motrizes, Rd, M)
    rodeiro('traseira', -1.6, Rt, M, raios=False)
    cilindro_externo(7.7, 1.15, 0.38, M)
    estrado_alto(xf, -2.6, estr_z, 2.75, M)
    para_choques(xf, M, 1)
    zc = 3.1
    caldeira_classica(xf, 0.2, 0.92, 1.0, zc, M)
    bx('selim', 1.25, 1.5, 0.6, (xf - 0.62, 0, 2.4), M['smoke'])
    cyl('fornalha', 1.04, 2.3, -0.95, 0, zc, M['paint'], 'X', 40)
    chamine(xf - 0.8, zc + 0.85, 0.35, 0.34, M)
    domo(5.0, zc, 0.96, 0.33, 0.2, M, 'paint')
    for s in (1, -1):
        # defletores de fumaça
        prism('defletor', [(xf - 0.15, estr_z + 0.05), (xf - 0.15, 3.55), (xf - 0.5, 3.75), (xf - 2.0, 3.75), (xf - 2.0, estr_z + 0.05)], 0.05, s * 1.3, M['black'], 'XZ')
        bx('defletor_alca', 0.4, 0.06, 0.06, (xf - 1.1, s * 1.33, 3.3), M['steel'])
        lampiao(xf + 0.05, s * 0.75, estr_z + 0.25, M)
    lampiao(xf + 0.05, 0, zc + 1.05, M)
    cabine(-2.1, -3.7, estr_z + 0.05, 4.2, 2.75, M)
    tender(-3.95, xr, 3.45, M, [-5.0, -7.0, -9.0], 0.53, larg=2.7, tipo='fowler')


# ---------------- vagões de 4 rodas (6,0 m) ----------------
LV = 6.0


def chassi_vagao(M, R=0.47, entre=3.0):
    xb = LV / 2 - 0.56
    for s in (1, -1):
        bx('longarina', 2 * xb, 0.1, 0.32, (0, s * 0.95, 1.0), M['black'])
    bx('estrado', 2 * xb, 2.0, 0.08, (0, 0, 1.12), M['black'])
    for x in (entre / 2, -entre / 2):
        rodeiro('roda', x, R, M, raios=False)
        for s in (1, -1):
            bx('mancal', 0.26, 0.14, 0.28, (x, s * (BITOLA + 0.2), R), M['black'])
            bx('mola', 1.0, 0.08, 0.08, (x, s * (BITOLA + 0.2), R + 0.25), M['black'])
            bx('w_iron', 0.5, 0.05, 0.4, (x, s * (BITOLA + 0.12), R + 0.2), M['black'])
    para_choques(xb, M, 1)
    para_choques(-xb, M, -1)
    for s in (1, -1):
        bx('freio', 0.08, 0.06, 0.6, (0, s * 1.0, 0.75), M['black'])


def caixa(cor, z0, z1, M, larg=2.45, comp=None, bevel=0.03):
    comp = comp or (LV - 1.3)
    bx('caixa', comp, larg, z1 - z0, (0, 0, (z0 + z1) / 2), M[cor], bevel=bevel)
    return comp


def teto_arco(z, comp, larg, M, flecha=0.28, cor='roof'):
    hw = larg / 2 + 0.05
    pts = [(hw, z)] + [(hw * math.cos(math.radians(a)), z + flecha * math.sin(math.radians(a))) for a in range(0, 181, 15)] + [(-hw, z)]
    prism('teto', pts, comp + 0.12, 0, M[cor], 'YZ', 0.01)


def carro_passageiros(M):
    chassi_vagao(M)
    comp = caixa('paint', 1.2, 3.3, M, 2.6)
    teto_arco(3.3, comp, 2.6, M, 0.32)
    n = 4
    for s in (1, -1):
        for i in range(n):
            x = -comp / 2 + comp * (i + 0.5) / n
            bx('porta', 0.62, 0.02, 1.7, (x, s * 1.31, 2.15), M['paint'])
            bx('janela_porta', 0.4, 0.03, 0.55, (x, s * 1.31, 2.7), M['glass'])
            bx('macaneta', 0.05, 0.04, 0.05, (x + 0.24, s * 1.33, 2.2), M['brass'])
            for dx in (-0.47, 0.47):
                if abs(x + dx) < comp / 2 - 0.1:
                    bx('janela', 0.3, 0.03, 0.5, (x + dx, s * 1.31, 2.72), M['glass'])
        bx('friso_creme', comp, 0.025, 0.08, (0, s * 1.315, 2.35), M['cream'])
        bx('friso_creme2', comp, 0.025, 0.06, (0, s * 1.315, 3.12), M['cream'])
        bx('estribo', comp - 0.2, 0.18, 0.04, (0, s * 1.4, 1.05), M['black'])
    for x in (-1.2, 0, 1.2):
        cyl('lampiao_teto', 0.1, 0.12, x, 0, 3.66, M['black'], 'Z', 10)


def furgao_correio(M):
    chassi_vagao(M)
    comp = caixa('paint', 1.2, 3.25, M, 2.6)
    teto_arco(3.25, comp, 2.6, M, 0.3)
    for s in (1, -1):
        bx('porta_correr', 1.3, 0.03, 1.7, (0, s * 1.31, 2.15), M['paint'])
        bx('porta_trilho', 1.6, 0.04, 0.05, (0, s * 1.33, 3.05), M['black'])
        for x in (-1.7, 1.7):
            bx('janela', 0.35, 0.03, 0.35, (x, s * 1.31, 2.75), M['glass'])
        bx('caixa_cartas', 0.18, 0.04, 0.12, (1.0, s * 1.33, 2.2), M['brass'])
        bx('friso', comp, 0.025, 0.06, (0, s * 1.315, 2.5), M['cream'])


def vagao_carvao(M):
    chassi_vagao(M)
    comp = LV - 1.3
    hw = 1.2
    for s in (1, -1):
        bx('lateral', comp, 0.06, 1.35, (0, s * hw, 1.85), M['grey'])
        bx('porta_lateral', 1.1, 0.03, 1.1, (0, s * (hw + 0.035), 1.75), M['grey'])
        for x in (-1.7, -0.75, 0.75, 1.7):
            bx('reforco', 0.08, 0.05, 1.35, (x, s * (hw + 0.04), 1.85), M['grey'])
    for x in (comp / 2, -comp / 2):
        bx('cabeceira', 0.06, 2 * hw, 1.35, (x, 0, 1.85), M['grey'])
    bx('fundo', comp, 2 * hw, 0.06, (0, 0, 1.2), M['grey'])
    # carga de carvão: monte
    loft('carvao', [(comp / 2 - 0.1, hw - 0.1, 2.3, 2.75, 3), (0, hw - 0.1, 2.3, 2.95, 3), (-comp / 2 + 0.1, hw - 0.1, 2.3, 2.75, 3)], M['coal'])


def vagao_tanque(M):
    chassi_vagao(M)
    cyl('tanque', 1.0, LV - 1.1, 0, 0, 2.3, M['tank'], 'X', 40)
    for x in (LV / 2 - 0.55, -LV / 2 + 0.55):
        sphere('tampo', 1.0, x, 0, 2.3, M['tank'], 0.12, 1, 1)
    cyl('domo', 0.45, 0.5, 0, 0, 3.35, M['tank'], 'Z', 24)
    cyl('domo_tampa', 0.5, 0.06, 0, 0, 3.62, M['tank'], 'Z', 24)
    for x in (-1.7, 1.7):
        for s in (1, -1):
            bx('cinta_tanque', 0.06, 0.04, 2.0, (x, s * 0.75, 2.3), M['black'], (math.radians(48 * s), 0, 0))
        bx('apoio', 0.25, 2.0, 0.3, (x, 0, 1.3), M['black'])
    for s in (1, -1):
        bx('escada', 0.04, 0.04, 1.6, (0.4, s * 1.05, 2.2), M['steel'])
    bx('placa', 0.8, 0.02, 0.35, (-1.0, 1.0, 2.35), M['white'])
    bx('placa2', 0.8, 0.02, 0.35, (-1.0, -1.0, 2.35), M['white'])


def furgao_tabuas(M, cor, frestas=False):
    chassi_vagao(M)
    comp = LV - 1.3
    hw = 1.25
    if frestas:  # vagão de gado: tábuas com frestas, metade de baixo caiada
        bx('miolo', comp - 0.1, 2 * hw - 0.12, 2.05, (0, 0, 2.2), M['black'])
        for s in (1, -1):
            for i in range(9):
                z = 1.3 + i * 0.23
                bx('tabua', comp, 0.05, 0.15, (0, s * hw, z), M['white' if i < 3 else cor])
            for x in (-comp / 2 + 0.05, -0.8, 0.8, comp / 2 - 0.05):
                bx('montante', 0.1, 0.07, 2.1, (x, s * (hw + 0.02), 2.25), M[cor])
            bx('porta', 1.4, 0.04, 1.9, (0, s * (hw + 0.03), 2.15), M[cor])
        for x in (comp / 2, -comp / 2):
            bx('cabeceira', 0.06, 2 * hw, 2.1, (x, 0, 2.25), M[cor])
    else:
        bx('corpo', comp, 2 * hw, 2.1, (0, 0, 2.25), M[cor], bevel=0.02)
        for s in (1, -1):
            for x in (-comp / 2 + 0.05, -0.85, 0.85, comp / 2 - 0.05):
                bx('montante', 0.1, 0.05, 2.1, (x, s * (hw + 0.02), 2.25), M['black'])
            bx('porta_correr', 1.5, 0.04, 1.8, (0, s * (hw + 0.03), 2.15), M[cor])
            bx('trilho_porta', 3.0, 0.05, 0.05, (0, s * (hw + 0.04), 3.1), M['black'])
            for x in (-comp / 2 + 0.25, comp / 2 - 0.25):
                bx('ventilacao', 0.3, 0.03, 0.18, (x, s * (hw + 0.025), 3.05), M['black'])
    teto_arco(3.3, comp, 2 * hw, M, 0.28)


def vagao_graos(M):
    chassi_vagao(M)
    comp = LV - 1.3
    hw = 1.25
    # graneleiro coberto: laterais retas em cima, fundo em funil
    for s in (1, -1):
        prism('lateral', [(comp / 2, 1.7), (comp / 2, 3.3), (-comp / 2, 3.3), (-comp / 2, 1.7)], 0.06, s * hw, M['grey'], 'XZ')
        for x in (-1.6, 0, 1.6):
            bx('reforco', 0.1, 0.05, 1.6, (x, s * (hw + 0.03), 2.5), M['grey'])
    for x in (comp / 2, -comp / 2):
        bx('cabeceira', 0.06, 2 * hw, 1.6, (x, 0, 2.5), M['grey'])
    for x in (1.2, -1.2):
        loft('funil', [(x + 0.9, hw - 0.05, 1.1, 1.75, 6), (x, 0.4, 1.0, 1.7, 6), (x - 0.9, hw - 0.05, 1.1, 1.75, 6)], M['grey'])
    bx('teto', comp, 2 * hw, 0.12, (0, 0, 3.36), M['grey'])
    for x in (-1.5, -0.5, 0.5, 1.5):
        bx('escotilha', 0.5, 0.6, 0.08, (x, 0, 3.46), M['roof'])
    bx('passarela', comp, 0.4, 0.04, (0, 0, 3.52), M['black'])


def vagao_madeira(M):
    chassi_vagao(M)
    comp = LV - 1.1
    bx('assoalho', comp, 2.4, 0.1, (0, 0, 1.25), M['wood'])
    for x in (1.6, -1.6):
        bx('travessa', 0.25, 2.5, 0.18, (x, 0, 1.4), M['black'])
        for s in (1, -1):
            bx('fueiro', 0.1, 0.1, 1.25, (x, s * 1.2, 2.0), M['black'])
    for i, (y, z) in enumerate([(-0.75, 1.75), (0, 1.75), (0.75, 1.75), (-0.38, 2.3), (0.38, 2.3), (0, 2.82)]):
        r = 0.3
        cyl(f'tora{i}', r, comp - 0.1 - 0.15 * (i % 2), 0.05 * (i % 3), y, z, M['log'], 'X', 14)
        for sx in (1, -1):
            cyl(f'tora_topo{i}', r * 0.92, 0.02, sx * ((comp - 0.1 - 0.15 * (i % 2)) / 2 + 0.01) + 0.05 * (i % 3), y, z, M['logend'], 'X', 14)
    for x in (1.6, -1.6):
        bx('corrente', 0.04, 1.6, 0.04, (x, 0, 3.15), M['steel'])


def vagao_minerio(M):
    chassi_vagao(M)
    comp = LV - 1.6
    hw = 1.15
    # hopper de minério: laterais baixas, cabeceiras inclinadas
    for s in (1, -1):
        prism('lateral', [(comp / 2, 1.25), (comp / 2 + 0.25, 2.45), (-comp / 2 - 0.25, 2.45), (-comp / 2, 1.25)], 0.08, s * hw, M['grey'], 'XZ')
        for x in (-1.4, 0, 1.4):
            bx('reforco', 0.1, 0.05, 1.2, (x, s * (hw + 0.04), 1.85), M['grey'])
    for sx in (1, -1):
        bx('cabeceira', 0.08, 2 * hw, 1.25, (sx * (comp / 2 + 0.12), 0, 1.85), M['grey'], (0, sx * math.radians(-12), 0))
    bx('fundo', comp, 2 * hw, 0.08, (0, 0, 1.25), M['grey'])
    loft('minerio', [(comp / 2, hw - 0.1, 2.0, 2.35, 3), (0, hw - 0.1, 2.0, 2.65, 3), (-comp / 2, hw - 0.1, 2.0, 2.35, 3)], M['ore'])
    for x in (-1.0, 1.0):
        bx('bica', 0.6, 0.8, 0.3, (x, 0, 0.95), M['grey'])


def vagao_aco(M):
    chassi_vagao(M)
    comp = LV - 1.1
    hw = 1.25
    bx('assoalho', comp, 2 * hw, 0.1, (0, 0, 1.25), M['wood'])
    for s in (1, -1):
        bx('borda', comp, 0.06, 0.4, (0, s * hw, 1.5), M['bauxite'])
        for x in (-1.7, -0.6, 0.6, 1.7):
            bx('dobradica', 0.1, 0.05, 0.4, (x, s * (hw + 0.03), 1.5), M['black'])
    for x in (comp / 2, -comp / 2):
        bx('cabeceira', 0.06, 2 * hw, 0.4, (x, 0, 1.5), M['bauxite'])
    # carga: chapas empilhadas e perfis I
    for i in range(5):
        bx('chapa', comp - 0.5, 1.6, 0.07, (0, -0.2, 1.36 + i * 0.08), M['plate'])
    for j, y in enumerate((0.85, 0.55)):
        bx('perfil_alma', comp - 0.3, 0.04, 0.3, (0, y, 1.5 + 0.0), M['plate'])
        bx('perfil_mesa', comp - 0.3, 0.24, 0.04, (0, y, 1.67), M['plate'])
        bx('perfil_mesa2', comp - 0.3, 0.24, 0.04, (0, y, 1.33), M['plate'])
    for x in (-1.2, 1.2):
        bx('amarra', 0.05, 2.2, 0.03, (x, 0, 1.78), M['black'])


def furgao_blindado(M):
    chassi_vagao(M)
    comp = LV - 1.3
    hw = 1.25
    bx('corpo', comp, 2 * hw, 2.1, (0, 0, 2.25), M['paint'], bevel=0.03)
    for s in (1, -1):
        for x in (-comp / 2 + 0.1, comp / 2 - 0.1):
            for k in range(6):
                bx('rebite', 0.04, 0.03, 0.04, (x, s * (hw + 0.01), 1.45 + k * 0.3), M['steel'])
        bx('porta_blindada', 1.1, 0.04, 1.75, (0, s * (hw + 0.02), 2.15), M['grey'])
        for x in (-1.5, 1.5):
            bx('janela_grade', 0.4, 0.03, 0.3, (x, s * (hw + 0.01), 2.85), M['glass'])
            for k in range(4):
                bx('grade', 0.03, 0.04, 0.3, (x - 0.15 + k * 0.1, s * (hw + 0.03), 2.85), M['steel'])
        bx('friso_ouro', comp, 0.02, 0.05, (0, s * (hw + 0.012), 2.55), M['brass'])
    teto_arco(3.3, comp, 2 * hw, M, 0.24)


# ---------------- catálogo ----------------
# slug, nome, id original, comprimento real (m), comprimento no jogo (unidades de 0,75 m, pares), construtor
TRENS = [
    ('kirby_paul_tank', 'Kirby Paul Tank (Steam)', 0, 9.0, 12, kirby_paul_tank),
    ('chaney_jubilee', "Chaney 'Jubilee' (Steam)", 8, 19.5, 26, chaney_jubilee),
    ('ginzu_a4', "Ginzu 'A4' (Steam)", 9, 21.0, 28, ginzu_a4),
    ('sh_8p', "SH '8P' (Steam)", 10, 21.0, 28, sh_8p),
    ('passenger_carriage', 'Passenger Carriage', 27, 6.0, 8, carro_passageiros),
    ('mail_van', 'Mail Van', 28, 6.0, 8, furgao_correio),
    ('coal_truck', 'Coal Truck', 29, 6.0, 8, vagao_carvao),
    ('oil_tanker', 'Oil Tanker', 30, 6.0, 8, vagao_tanque),
    ('livestock_van', 'Livestock Van', 31, 6.0, 8, lambda M: furgao_tabuas(M, 'bauxite', frestas=True)),
    ('goods_van', 'Goods Van', 32, 6.0, 8, lambda M: furgao_tabuas(M, 'bauxite')),
    ('grain_hopper', 'Grain Hopper', 33, 6.0, 8, vagao_graos),
    ('wood_truck', 'Wood Truck', 34, 6.0, 8, vagao_madeira),
    ('iron_ore_hopper', 'Iron Ore Hopper', 35, 6.0, 8, vagao_minerio),
    ('steel_truck', 'Steel Truck', 36, 6.0, 8, vagao_aco),
    ('armoured_van', 'Armoured Van', 37, 6.0, 8, furgao_blindado),
]


def exportar(slug, build):
    reset()
    MATS.clear()
    M = materiais_trem()
    build(M)
    for ob in bpy.context.collection.objects:
        ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, slug + '.glb'), use_selection=True, export_apply=True, export_format='GLB')
    print('OK', slug, len(bpy.context.collection.objects), 'peças')


if __name__ == '__main__':
    only = os.environ.get('ONLY')
    for slug, nome, vid, Lm, Lu, build in TRENS:
        if only and slug not in only.split(','):
            continue
        exportar(slug, build)
