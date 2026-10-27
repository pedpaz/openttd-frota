# Objetos de cidade de 1950 (clima temperado) para substituir sprites base sem versão 4x no OpenGFX2 High Def:
# estátua equestre, chafariz, duas praças e o estádio (2x2). Exporta GLB.
# Coordenadas: canto norte do tile na origem; o tile ocupa X em [-12, 0] e Y em [-12, 0] (metros).
# Eixo OpenTTD x (desce para a esquerda na tela) = -X do Blender; eixo y (desce para a direita) = -Y.
# Uso: python3 cidade.py -- <pasta_saida>
import bpy, bmesh, math, os, sys, random
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modelar import reset, MATS, mat, box, cyl, sphere, prism, new_obj, finish, OUT
from trens import bx, loft, toro

U = 0.75  # metros por unidade do OpenTTD (tile = 16 unidades = 12 m)


def P(ox, oy, z=0.0):
    """Ponto em coordenadas do OpenTTD (unidades) -> Blender (metros)."""
    return (-ox * U, -oy * U, z)


def materiais():
    return {
        'bronze': mat('Bronze', '#3b3a2c', 0.85, 0.42),
        'granito': mat('Granito vermelho', '#9a5642', 0.0, 0.55),
        'pedra': mat('Pedra clara', '#b9b2a2', 0.0, 0.7),
        'pedra2': mat('Pedra cinza', '#8f8b84', 0.0, 0.75),
        'agua': mat('Água', '#2f5f86', 0.1, 0.08),
        'jato': mat('Jato de água', '#dfeef7', 0.0, 0.2),
        'ferro': mat('Ferro', '#26282a', 0.6, 0.45),
        'grama': mat('Grama', '#4f7f34', 0.0, 0.9),
        'grama2': mat('Grama clara', '#5f9140', 0.0, 0.9),
        'cascalho': mat('Cascalho', '#a69a82', 0.0, 0.95),
        'tronco': mat('Tronco', '#4a3424', 0.0, 0.9),
        'folha1': mat('Folhagem 1', '#2f5e24', 0.0, 0.85),
        'folha2': mat('Folhagem 2', '#3f7330', 0.0, 0.85),
        'folha3': mat('Folhagem 3', '#567f2c', 0.0, 0.85),
        'folha_outono': mat('Folhagem outono', '#7a7a2e', 0.0, 0.85),
        'flor_v': mat('Flores vermelhas', '#b8332b', 0.0, 0.8),
        'flor_a': mat('Flores amarelas', '#d9b23a', 0.0, 0.8),
        'madeira': mat('Madeira banco', '#7a5434', 0.0, 0.8),
        'tijolo': mat('Tijolo', '#9b4a35', 0.0, 0.85),
        'telhado': mat('Telhado verde', '#2e5a3a', 0.2, 0.6),
        'concreto': mat('Concreto', '#a9a69e', 0.0, 0.8),
        'branco': mat('Linha branca', '#eeeeea', 0.0, 0.6),
        'campo': mat('Campo', '#4c8a32', 0.0, 0.9),
        'campo2': mat('Campo faixa', '#56973a', 0.0, 0.9),
    }


CORES_TORCIDA = ['#2b2b33', '#8a2d24', '#d8d2c0', '#2d4a7a', '#6b5a3a', '#c9a24a', '#3d5a35', '#5a5a60']


def multidao(caixas, semente=7):
    """Gente na arquibancada: caixinhas (x, y, z) agrupadas em uma malha por cor (sobrevive ao glTF)."""
    rnd = random.Random(semente)
    bms = {c: bmesh.new() for c in CORES_TORCIDA}
    for (x, y, z, ang) in caixas:
        c = rnd.choice(CORES_TORCIDA)
        bm = bms[c]
        ca, sa = math.cos(ang), math.sin(ang)
        h = rnd.uniform(0.32, 0.42)
        pts = []
        for dx, dy, dz in [(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]:
            lx, ly = dx * 0.11, dy * 0.13
            pts.append(bm.verts.new((x + lx * ca - ly * sa, y + lx * sa + ly * ca, z + dz * h)))
        for f in [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]:
            bm.faces.new([pts[k] for k in f])
    obs = []
    for c, bm in bms.items():
        if not bm.verts:
            continue
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        ob = new_obj('torcida', bm)
        finish(ob, mat('Torcida ' + c, c, 0.0, 0.8))
        obs.append(ob)
    return obs


# ---------------- árvores ----------------
def arvore(x, y, h, r, M, folhas=('folha1', 'folha2', 'folha3'), semente=1):
    """Árvore de copa cheia: tronco curto + aglomerado de esferas de folhagem em camadas."""
    rnd = random.Random(semente)
    cyl('tronco', r * 0.11, h * 0.45, x, y, h * 0.22, M['tronco'], 'Z', 10)
    for camada, (zf, df, rf, n) in enumerate([(0.5, 0.62, 0.42, 8), (0.68, 0.5, 0.45, 7), (0.84, 0.3, 0.42, 5)]):
        for k in range(n):
            a = 2 * math.pi * k / n + rnd.uniform(-0.4, 0.4) + camada
            d = df * r * rnd.uniform(0.7, 1.05)
            rr = r * rf * rnd.uniform(0.85, 1.15)
            sphere('copa', rr, x + math.cos(a) * d, y + math.sin(a) * d, h * zf + rnd.uniform(-0.05, 0.05) * h,
                   M[rnd.choice(folhas)], 1, 1, 0.82)
    sphere('copa_topo', r * 0.45, x, y, h * 0.95, M[folhas[1]], 1, 1, 0.8)


def banco(x, y, ang, M):
    bx('banco_assento', 1.4, 0.4, 0.06, (x, y, 0.45), M['madeira'], (0, 0, ang))
    bx('banco_encosto', 1.4, 0.06, 0.35, (x - math.sin(ang) * 0.2, y + math.cos(ang) * 0.2, 0.7), M['madeira'], (0, 0, ang))
    for s in (-0.6, 0.6):
        bx('banco_pe', 0.06, 0.4, 0.45, (x + math.cos(ang) * s, y + math.sin(ang) * s, 0.22), M['ferro'], (0, 0, ang))


def caminho(pontos, larg, M, z=0.03, mat_='cascalho'):
    """Caminho de cascalho seguindo uma polilinha (x, y) em metros."""
    bm = bmesh.new()
    esq, dir_ = [], []
    for i, (x, y) in enumerate(pontos):
        a = pontos[max(i - 1, 0)]; b = pontos[min(i + 1, len(pontos) - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]; L = math.hypot(tx, ty) or 1
        nx, ny = -ty / L, tx / L
        esq.append(bm.verts.new((x + nx * larg / 2, y + ny * larg / 2, z)))
        dir_.append(bm.verts.new((x - nx * larg / 2, y - ny * larg / 2, z)))
    for i in range(len(pontos) - 1):
        bm.faces.new((esq[i], dir_[i], dir_[i + 1], esq[i + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = new_obj('caminho', bm)
    for f in ob.data.polygons:
        f.use_smooth = True
    return finish(ob, M[mat_])


def lago(cx, cy, rx, ry, M):
    cyl('lago_margem', 1.0, 0.1, cx, cy, 0.04, M['pedra2'], 'Z', 40).scale = (rx + 0.25, ry + 0.25, 1)
    cyl('lago_agua', 1.0, 0.1, cx, cy, 0.07, M['agua'], 'Z', 40).scale = (rx, ry, 1)


# ---------------- objetos ----------------
def estatua(M):
    """Estátua equestre (sprite 1454): pedestal de granito no subtile (6,5) 3x6, cercado de frades de ferro."""
    cx, cy, _ = P(7.5, 8.0)
    bx('base', 2.4, 4.2, 0.35, (cx, cy, 0.17), M['pedra2'], bevel=0.03)
    bx('pedestal', 1.7, 3.4, 1.9, (cx, cy, 1.3), M['granito'], bevel=0.05)
    bx('cornija', 1.95, 3.65, 0.18, (cx, cy, 2.32), M['pedra'], bevel=0.04)
    bx('placa', 0.03, 1.2, 0.5, (cx + 0.86, cy, 1.3), M['bronze'])
    z0 = 2.41
    # cavalo ao longo de Y (cabeça para +Y), empinando levemente
    corpo = loft('cavalo_corpo', [(-0.95, 0.30, -0.33, 0.33, 2.3), (-0.4, 0.38, -0.42, 0.42, 2.2), (0.35, 0.36, -0.40, 0.40, 2.2), (0.95, 0.28, -0.32, 0.30, 2.3)], M['bronze'])
    corpo.rotation_euler = (0, 0, math.pi / 2)
    corpo.location = (cx, cy, z0 + 1.55)
    pesc = loft('cavalo_pescoco', [(0, 0.2, -0.28, 0.28, 2), (0.85, 0.15, -0.2, 0.2, 2)], M['bronze'])
    pesc.rotation_euler = (0, -math.radians(55), math.pi / 2)
    pesc.location = (cx, cy + 0.85, z0 + 1.75)
    cab = loft('cavalo_cabeca', [(0, 0.14, -0.17, 0.17, 2), (0.6, 0.1, -0.11, 0.11, 2)], M['bronze'])
    cab.rotation_euler = (0, math.radians(35), math.pi / 2)
    cab.location = (cx, cy + 1.25, z0 + 2.4)
    for s in (1, -1):
        sphere('orelha', 0.06, cx + s * 0.08, cy + 1.2, z0 + 2.6, M['bronze'], 0.6, 0.6, 1.6)
    # pernas: traseiras apoiadas, uma dianteira erguida
    for s, dy, erguida in [(1, -0.75, False), (-1, -0.75, False), (1, 0.7, True), (-1, 0.7, False)]:
        if erguida:
            bx('perna', 0.12, 0.12, 0.7, (cx + s * 0.18, cy + dy + 0.3, z0 + 1.15), M['bronze'], (math.radians(-60), 0, 0))
        else:
            cyl('perna', 0.07, 1.25, cx + s * 0.18, cy + dy, z0 + 0.62, M['bronze'], 'Z', 10)
            cyl('casco', 0.09, 0.1, cx + s * 0.18, cy + dy, z0 + 0.05, M['bronze'], 'Z', 10)
    rabo = loft('cauda', [(0, 0.08, -0.08, 0.08, 2), (0.7, 0.05, -0.05, 0.05, 2)], M['bronze'])
    rabo.rotation_euler = (0, math.radians(60), -math.pi / 2)
    rabo.location = (cx, cy - 0.95, z0 + 1.7)
    # cavaleiro
    cyl('cavaleiro_tronco', 0.22, 0.85, cx, cy + 0.1, z0 + 2.35, M['bronze'], 'Z', 14)
    sphere('cavaleiro_cabeca', 0.16, cx, cy + 0.12, z0 + 2.95, M['bronze'])
    cyl('chapeu', 0.2, 0.08, cx, cy + 0.12, z0 + 3.08, M['bronze'], 'Z', 14)
    for s in (1, -1):
        bx('coxa', 0.14, 0.5, 0.16, (cx + s * 0.3, cy + 0.2, z0 + 1.95), M['bronze'])
        bx('canela', 0.12, 0.12, 0.55, (cx + s * 0.38, cy + 0.42, z0 + 1.6), M['bronze'])
    bx('braco_erguido', 0.1, 0.1, 0.8, (cx - 0.28, cy + 0.35, z0 + 3.0), M['bronze'], (math.radians(-35), 0, 0))
    bx('espada', 0.04, 0.04, 0.9, (cx - 0.28, cy + 0.75, z0 + 3.65), M['bronze'], (math.radians(-35), 0, 0))
    # tudo acima em escala 1,5 em torno do centro (no TTD a estátua é grande no tile)
    from mathutils import Matrix
    T = Matrix.Translation((cx, cy, 0)) @ Matrix.Scale(1.5, 4) @ Matrix.Translation((-cx, -cy, 0))
    bpy.context.view_layer.update()
    for o in list(bpy.context.collection.objects):
        o.matrix_world = T @ o.matrix_world
    # frades (postes baixos) com corrente em volta
    pts = []
    for k in range(18):
        a = 2 * math.pi * k / 18
        x, y = cx + math.cos(a) * 4.6, cy + math.sin(a) * 5.0
        cyl('frade', 0.07, 0.75, x, y, 0.37, M['ferro'], 'Z', 8)
        sphere('frade_topo', 0.08, x, y, 0.78, M['ferro'])
        pts.append((x, y))
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        L = math.hypot(x1 - x0, y1 - y0)
        bx('corrente', L, 0.02, 0.02, ((x0 + x1) / 2, (y0 + y1) / 2, 0.6), M['ferro'], (0, 0, math.atan2(y1 - y0, x1 - x0)))


def chafariz(M):
    """Chafariz (sprite 1455): bacia redonda com taça central e jato, no subtile (3,3) 9x9."""
    cx, cy, _ = P(7.5, 7.5)
    cyl('bacia_borda', 3.0, 0.55, cx, cy, 0.27, M['pedra'], 'Z', 48)
    cyl('bacia_agua', 2.75, 0.56, cx, cy, 0.29, M['agua'], 'Z', 48)
    toro('bacia_aro', 2.9, 0.14, cx, cy, 0.58, M['pedra']).rotation_euler = (0, 0, 0)
    cyl('coluna', 0.28, 1.6, cx, cy, 1.1, M['pedra'], 'Z', 20)
    cyl('taca', 1.1, 0.25, cx, cy, 1.9, M['pedra'], 'Z', 32, r2=0.5)
    cyl('taca_agua', 0.95, 0.05, cx, cy, 2.03, M['agua'], 'Z', 32)
    cyl('coluna2', 0.14, 0.7, cx, cy, 2.35, M['pedra'], 'Z', 14)
    cyl('taca2', 0.45, 0.15, cx, cy, 2.75, M['pedra'], 'Z', 24, r2=0.2)
    cyl('jato', 0.07, 1.1, cx, cy, 3.35, M['jato'], 'Z', 10)
    for k in range(8):
        a = 2 * math.pi * k / 8
        x, y = cx + math.cos(a) * 0.65, cy + math.sin(a) * 0.65
        bx('cortina', 0.04, 0.04, 1.6, (x, y, 1.5), M['jato'], (math.cos(a + math.pi / 2) * 0.35, math.sin(a + math.pi / 2) * -0.35, 0))


def praca1(M):
    """Praça com lago e duas árvores (sprite 1456), tile inteiro."""
    lago(*P(9.5, 10.0)[:2], 2.6, 2.0, M)
    caminho([P(16, 3.5)[:2], P(11, 4.5)[:2], P(6.5, 7.5)[:2], P(5, 12)[:2], P(4.5, 16)[:2]], 1.3, M)
    arvore(*P(4.5, 4.0)[:2], 8.5, 3.1, M, semente=3)
    arvore(*P(12.5, 13.5)[:2], 6.0, 2.0, M, semente=5)
    banco(*P(7.2, 5.6)[:2], math.radians(40), M)
    for k in range(10):
        x, y, _ = P(2 + k * 0.5, 13.5 + (k % 3) * 0.4)
        sphere('flor', 0.22, x, y, 0.12, M['flor_v' if k % 2 else 'flor_a'], 1, 1, 0.6)


def praca2(M):
    """Praça com árvore grande e caminho (sprite 1457), tile inteiro."""
    caminho([P(16, 9)[:2], P(11, 10)[:2], P(7.5, 12.5)[:2], P(6.5, 16)[:2]], 1.3, M)
    arvore(*P(8, 6)[:2], 10.0, 4.0, M, folhas=('folha_outono', 'folha3', 'folha2'), semente=9)
    sphere('morrinho', 1.0, *P(12.5, 4)[:2], 0.0, M['grama2'], 2.8, 2.2, 0.55)
    banco(*P(11.5, 11.5)[:2], math.radians(-30), M)
    for k in range(7):
        x, y, _ = P(2.5 + k * 0.45, 3 + (k % 2) * 0.5)
        sphere('arbusto', 0.45, x, y, 0.3, M['folha2'], 1, 1, 0.8)


def estadio(M):
    """Estádio 2x2 (casas 20-23): campo com linhas e arquibancadas cobertas nos quatro lados."""
    L = 24.0
    # campo (vai para os sprites de chão 1479-1482)
    for i in range(8):
        bx(f'campo_faixa{i}', L / 8, L - 2, 0.02, (-L / 16 - i * L / 8, -L / 2, 0.01), M['campo' if i % 2 else 'campo2'])
    def linha(x0, y0, x1, y1):
        Lg = math.hypot(x1 - x0, y1 - y0)
        bx('campo_linha', Lg + 0.12, 0.12, 0.03, ((x0 + x1) / 2, (y0 + y1) / 2, 0.025), M['branco'], (0, 0, math.atan2(y1 - y0, x1 - x0)))
    a, b = -5.0, -19.0  # limites do gramado de jogo
    for (x0, y0, x1, y1) in [(a, a, b, a), (b, a, b, b), (b, b, a, b), (a, b, a, a), (a, -12, b, -12)]:
        linha(x0, y0, x1, y1)
    toro('campo_circulo', 2.2, 0.06, -12, -12, 0.03, M['branco']).rotation_euler = (0, 0, 0)
    for y in (a, b):
        s = 1 if y == a else -1
        linha(-9.5, y, -9.5, y - s * 2.5); linha(-14.5, y, -14.5, y - s * 2.5); linha(-9.5, y - s * 2.5, -14.5, y - s * 2.5)
        bx('trave', 0.08, 0.08, 1.2, (-10.9, y + s * 0.05, 0.6), M['branco']); bx('trave', 0.08, 0.08, 1.2, (-13.1, y + s * 0.05, 0.6), M['branco'])
        bx('travessao', 2.3, 0.08, 0.08, (-12, y + s * 0.05, 1.2), M['branco'])
    # arquibancadas: em cada lado, degraus com torcida, muro de tijolo atrás e telhado verde
    def arquibancada(ang):
        # lado NE (X = 0), degraus descendo para o campo (-X); depois girado para os outros lados
        grupo = []
        pessoas = []
        prof, comp = 4.0, L - 8.4
        for k in range(5):
            dk = prof - k * 0.75
            grupo.append(bx('degrau', dk, comp, 0.45, (-dk / 2 - 0.4, -L / 2, 0.22 + k * 0.45), M['concreto']))
            n = int((comp - 0.6) / 0.34)
            for q in range(n):
                if random.Random(k * 1000 + q + int(ang * 10)).random() < 0.82:
                    pessoas.append((-dk - 0.4 + 0.22, -L / 2 - (comp - 0.6) / 2 + q * 0.34, 0.45 + k * 0.45, ang))
        grupo.append(bx('muro', 0.4, comp, 3.4, (-0.2, -L / 2, 1.7), M['tijolo']))
        grupo.append(bx('faixa_muro', 0.42, comp, 0.18, (-0.2, -L / 2, 3.3), M['concreto']))
        for j in range(5):
            grupo.append(bx('pilar', 0.14, 0.14, 1.2, (-2.4, -L / 2 - comp / 2 + 0.6 + j * (comp - 1.2) / 4, 3.6), M['ferro']))
        grupo.append(bx('telhado', 2.8, comp + 0.2, 0.12, (-1.3, -L / 2, 4.25), M['telhado'], (0, math.radians(-10), 0)))
        c = Vector((-L / 2, -L / 2, 0))
        for o in grupo:
            d = o.location - c
            o.location = c + Vector((d.x * math.cos(ang) - d.y * math.sin(ang), d.x * math.sin(ang) + d.y * math.cos(ang), d.z))
            o.rotation_euler.z += ang
        rot = []
        for (x, y, z, a) in pessoas:
            dx, dy = x - c.x, y - c.y
            rot.append((c.x + dx * math.cos(a) - dy * math.sin(a), c.y + dx * math.sin(a) + dy * math.cos(a), z, a))
        multidao(rot, semente=int(ang * 100) + 3)
    for ang in (0, math.pi / 2, math.pi, -math.pi / 2):
        arquibancada(ang)
    for (x, y) in [(-2.1, -2.1), (-21.9, -2.1), (-2.1, -21.9), (-21.9, -21.9)]:
        # cantos: bloco de tijolo com bilheteria, torre de iluminação em cima
        bx('canto', 4.2, 4.2, 3.0, (x, y, 1.5), M['tijolo'], bevel=0.05)
        bx('canto_teto', 4.4, 4.4, 0.15, (x, y, 3.05), M['concreto'])
        cyl('torre_luz', 0.15, 5.5, x, y, 5.8, M['ferro'], 'Z', 8)
        bx('refletor', 1.0, 1.0, 0.5, (x, y, 8.6), M['concreto'])


OBJETOS = [
    ('estatua', estatua),
    ('chafariz', chafariz),
    ('praca1', praca1),
    ('praca2', praca2),
    ('estadio', estadio),
]


def exportar(slug, build):
    reset()
    MATS.clear()
    M = materiais()
    build(M)
    for ob in bpy.context.collection.objects:
        ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, slug + '.glb'), use_selection=True, export_apply=True, export_format='GLB')
    print('OK', slug, len(bpy.context.collection.objects), 'peças')


if __name__ == '__main__':
    only = os.environ.get('ONLY')
    for slug, build in OBJETOS:
        if only and slug not in only.split(','):
            continue
        exportar(slug, build)
