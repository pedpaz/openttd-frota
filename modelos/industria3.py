# Indústrias pesadas de 1950 (temperado): refinaria de petróleo, siderúrgica e mina de ferro.
# Mesma convenção do industria.py: peça k no tile (k, 0); objetos de chão começam com 'chao'.
# Uso: python3 industria3.py -- <pasta_saida>
import bpy, bmesh, math, os, sys, random
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modelar import reset, MATS, mat, box, cyl, sphere, prism, new_obj, finish, OUT
from trens import bx
from industria import P, telhado_duas_aguas, janelas, trelica_pernas
from industria2 import materiais as materiais2


def emissivo(nome, cor, forca):
    m = mat(nome, cor, 0.0, 0.6)
    b = m.node_tree.nodes.get('Principled BSDF')
    c = tuple(int(cor[i:i + 2], 16) / 255 for i in (1, 3, 5))
    b.inputs['Emission Color'].default_value = (*[x ** 2.2 for x in c], 1)
    b.inputs['Emission Strength'].default_value = forca
    return m


def materiais():
    M = materiais2()
    M.update({
        'tanque': mat('Tanque pintado', '#d8d6cf', 0.2, 0.45),
        'azul': mat('Pintura azul', '#2f5d9a', 0.3, 0.45),
        'vermelho': mat('Tubulação vermelha', '#a3271c', 0.3, 0.5),
        'amarelo': mat('Tubulação amarela', '#c99a1f', 0.3, 0.5),
        'ferrugem': mat('Aço ferrugem', '#6a3a24', 0.4, 0.7),
        'chama': emissivo('Chama', '#ff8a1c', 30.0),
        'chama2': emissivo('Chama núcleo', '#ffd75a', 40.0),
        'gusa': emissivo('Ferro fundido', '#ff6a10', 12.0),
        'escoria': mat('Escória', '#3b3631', 0.1, 0.9),
        'minerio': mat('Minério de ferro', '#8a4a2e', 0.0, 0.92),
        'minerio2': mat('Minério bancada', '#a15d3a', 0.0, 0.92),
        'grama_m': mat('Grama mina', '#4f7f34', 0.0, 0.9),
        'cerca': mat('Cerca branca', '#e8e6df', 0.0, 0.6),
    })
    return M


def tubo(nome, a, b, r, m, segs=12):
    """Cilindro entre dois pontos."""
    a, b = Vector(a), Vector(b)
    d = b - a
    ob = cyl(nome, r, d.length, 0, 0, 0, m, 'Z', segs)
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = d.to_track_quat('Z', 'Y')
    ob.location = (a + b) / 2
    return ob


def plataforma(x, y, z, r, M):
    cyl('plataforma', r, 0.12, x, y, z, M['aco'], 'Z', 24)
    for i in range(12):
        a = 2 * math.pi * i / 12
        bx('guarda', 0.05, 0.05, 1.0, (x + r * math.cos(a), y + r * math.sin(a), z + 0.5), M['amarelo'])


# ---------------- refinaria ----------------
def tanque(k, M):
    """gfx18 (2080): tanque de armazenamento de teto flutuante, sub (1,1) 14x14."""
    cx, cy, _ = P(k, 8, 8)
    r, h = 4.9, 6.5
    cyl('tanque', r, h, cx, cy, h / 2, M['tanque'], 'Z', 48)
    cyl('faixa', r + 0.02, 1.4, cx, cy, 1.4, M['azul'], 'Z', 48)
    cyl('teto', r - 0.15, 0.2, cx, cy, h - 0.5, M['aco_claro'], 'Z', 48)
    cyl('borda', r + 0.06, 0.15, cx, cy, h, M['aco'], 'Z', 48)
    for i in range(10):  # escada em espiral na face visível
        a = math.radians(200 + i * 7)
        bx('degrau', 0.6, 0.25, 0.08, (cx + (r + 0.3) * math.cos(a), cy + (r + 0.3) * math.sin(a), 0.6 + i * 0.6), M['aco'], (0, 0, a))
    tubo('cano', (cx - r, cy - 1.0, 0.6), (cx - r - 0.9, cy - 1.0, 0.6), 0.25, M['vermelho'])


def coluna(k, M):
    """gfx19 (2083): coluna de destilação listrada com plataformas, sub (3,3) 10x9."""
    cx, cy, _ = P(k, 8, 7.5)
    h = 18.0
    cyl('coluna', 2.0, h, cx, cy, h / 2, M['tanque'], 'Z', 32)
    sphere('coluna_topo', 2.0, cx, cy, h, M['tanque'], 1, 1, 0.5)
    for z in range(2, int(h) - 1, 4):
        cyl('faixa', 2.03, 1.2, cx, cy, z, M['azul'], 'Z', 32)
    for z in (6.0, 12.0, 17.0):
        plataforma(cx, cy, z, 2.6, M)
    tubo('cano_sobe', (cx - 2.3, cy + 0.8, 0.0), (cx - 2.3, cy + 0.8, h + 0.5), 0.22, M['amarelo'])
    tubo('cano_curva', (cx - 2.3, cy + 0.8, h + 0.5), (cx, cy + 0.8, h + 1.3), 0.22, M['amarelo'])
    tubo('cano2', (cx + 0.3, cy - 2.2, 0.0), (cx + 0.3, cy - 2.2, 12.0), 0.18, M['vermelho'])
    bx('base', 5.0, 5.0, 0.4, (cx, cy, 0.2), M['concreto'])


def tocha(k, M):
    """gfx20 (2086): coluna alta com tocha acesa no topo, sub (4,4) 7x7."""
    cx, cy, _ = P(k, 7.5, 7.5)
    h = 20.0
    cyl('coluna', 1.1, h, cx, cy, h / 2, M['aco_claro'], 'Z', 24, r2=0.8)
    for z in (5.0, 10.0, 15.0):
        plataforma(cx, cy, z, 1.7, M)
    for (dx, dy) in [(-1.3, 0.0), (0.0, -1.3)]:
        tubo('cano', (cx + dx, cy + dy, 0.0), (cx + dx, cy + dy, h - 1.0), 0.15, M['vermelho'])
        tubo('cano_braco', (cx + dx, cy + dy, h - 1.0), (cx + dx * 0.3, cy + dy * 0.3, h + 0.3), 0.15, M['vermelho'])
    cyl('bico', 0.35, 0.8, cx, cy, h + 0.4, M['aco'], 'Z', 12)
    # chama: gotas emissivas
    sphere('chama', 0.9, cx, cy, h + 1.6, M['chama'], 1, 1, 1.8)
    sphere('chama', 0.6, cx + 0.3, cy - 0.2, h + 3.0, M['chama'], 1, 1, 1.6)
    sphere('chama', 0.5, cx, cy, h + 1.3, M['chama2'], 1, 1, 1.4)
    bx('base', 3.6, 3.6, 0.4, (cx, cy, 0.2), M['concreto'])


def unidade(k, M):
    """gfx21 (2089): unidade de processo em estrutura de aço com vasos e tubos, sub (2,0) 12x16."""
    cx, cy, _ = P(k, 8, 8)
    sx, sy = 8.0, 10.5
    for z in (4.0, 8.0):
        bx('piso_grade', sx, sy, 0.15, (cx, cy, z), M['aco'])
    for i in range(3):
        for j in range(3):
            x = cx - sx / 2 + sx * i / 2; y = cy - sy / 2 + sy * j / 2
            bx('coluna_aco', 0.3, 0.3, 11.0, (x, y, 5.5), M['ferrugem'])
    for z in (2.0, 6.0, 10.0):
        bx('viga', sx, 0.2, 0.25, (cx, cy - sy / 2, z), M['ferrugem'])
        bx('viga', 0.2, sy, 0.25, (cx - sx / 2, cy, z), M['ferrugem'])
    cyl('vaso', 1.1, 5.0, cx - 1.0, cy + 1.5, 6.5, M['azul'], 'Y', 24)
    cyl('vaso', 0.9, 4.0, cx + 1.5, cy - 2.0, 2.4, M['azul'], 'X', 24)
    cyl('vaso_v', 0.9, 6.0, cx + 2.0, cy + 3.0, 7.0, M['tanque'], 'Z', 24)
    for i in range(5):
        y = cy - sy / 2 + 1.0 + i * 2.1
        tubo('cano', (cx - sx / 2 - 0.4, y, 0.3), (cx - sx / 2 - 0.4, y, 4.0 + (i % 3) * 3.0), 0.16, M['vermelho'])
        tubo('cano_h', (cx - sx / 2 - 0.4, y, 4.0 + (i % 3) * 3.0), (cx + 1.0, y, 4.0 + (i % 3) * 3.0), 0.16, M['vermelho'])
    for i in range(4):
        x = cx - sx / 2 + 1.0 + i * 2.0
        tubo('cano', (x, cy - sy / 2 - 0.4, 0.3), (x, cy - sy / 2 - 0.4, 3.0), 0.14, M['amarelo'])
    bx('base', sx + 1, sy + 1, 0.3, (cx, cy, 0.15), M['concreto'])


def caixa_dagua(k, M):
    """gfx22 (2092): reservatório elevado em estrutura, com vasos verticais embaixo."""
    cx, cy, _ = P(k, 8, 8)
    trelica_pernas(cx, cy, 5.5, 5.5, 8.0, M, n=3)
    for i in range(3):
        bx('perna_meio', 0.22, 0.22, 8.0, (cx - 2.75 + 2.75 * i, cy, 4.0), M['aco'])
    bx('reservatorio', 6.5, 6.5, 3.2, (cx, cy, 9.6), M['aco_claro'], bevel=0.05)
    bx('borda', 6.7, 6.7, 0.25, (cx, cy, 11.25), M['aco'])
    tubo('escada', (cx - 3.25, cy - 3.6, 0), (cx - 3.25, cy - 3.6, 11), 0.06, M['amarelo'])
    for i in range(4):
        x = cx - 2.4 + i * 1.6
        cyl('vaso_v', 0.55, 3.0, x, cy - 4.3, 1.5, M['azul'], 'Z', 16)
        tubo('cano', (x, cy - 4.3, 3.0), (x, cy - 3.0, 8.0), 0.12, M['azul'])
    bx('base', 8, 10, 0.3, (cx, cy - 0.5, 0.15), M['concreto'])


def sala_controle(k, M):
    """gfx23 (2095): sala de controle baixa em L, sub (3,1) 10x13."""
    a, b, _ = P(k, 8, 4.5)
    bx('bloco', 7.0, 3.6, 3.0, (a, b, 1.5), M['concreto'], bevel=0.03)
    c, d, _ = P(k, 4.8, 9.5)
    bx('bloco', 2.6, 6.0, 3.0, (c, d, 1.5), M['concreto'], bevel=0.03)
    for (x, y, sx, sy) in [(a, b, 7.0, 3.6), (c, d, 2.6, 6.0)]:
        bx('platibanda', sx + 0.1, sy + 0.1, 0.3, (x, y, 3.15), M['reboco'])
        bx('laje', sx - 0.2, sy - 0.2, 0.1, (x, y, 3.05), M['escoria'])
    janelas(a - 3.0, a + 3.0, b - 1.8, 1.7, 5, M, alt=1.0, larg=0.8, lado=-1)
    janelas(d - 2.5, d + 2.5, c - 1.3, 1.7, 3, M, alt=1.0, larg=0.8, lado=-1, eixo='Y')


REFINARIA = [tanque, coluna, tocha, unidade, caixa_dagua, sala_controle]


# ---------------- siderúrgica ----------------
def galpao_alto(cx, cy, comp, larg, alt, M, telha='telha', eixo='X', lanternim=True):
    sx, sy = (comp, larg) if eixo == 'X' else (larg, comp)
    bx('galpao', sx, sy, alt, (cx, cy, alt / 2), M['tijolo'], bevel=0.04)
    if eixo == 'X':
        telhado_duas_aguas(cx - comp / 2, cx + comp / 2, cy - larg / 2, cy + larg / 2, alt, larg * 0.22, M[telha], 'X')
        if lanternim:
            bx('lanternim', comp, larg * 0.25, 1.0, (cx, cy, alt + larg * 0.22 - 0.2), M['vidro'])
            telhado_duas_aguas(cx - comp / 2, cx + comp / 2, cy - larg * 0.16, cy + larg * 0.16, alt + larg * 0.22 + 0.3, 0.6, M[telha], 'X', beiral=0.1)
        n = max(2, int(comp / 2.4))
        for i in range(n):
            x = cx - comp / 2 + (i + 0.5) * comp / n
            bx('pilastra', 0.5, 0.1, alt, (x, cy - larg / 2 - 0.04, alt / 2), M['tijolo_escuro'])
        janelas(cx - comp / 2 + 0.8, cx + comp / 2 - 0.8, cy - larg / 2, alt * 0.62, n - 1, M, alt=alt * 0.35, larg=1.0, lado=-1)
    else:
        telhado_duas_aguas(cx - larg / 2, cx + larg / 2, cy - comp / 2, cy + comp / 2, alt, larg * 0.22, M[telha], 'Y')
        n = max(2, int(comp / 2.4))
        janelas(cy - comp / 2 + 0.8, cy + comp / 2 - 0.8, cx - larg / 2, alt * 0.62, n - 1, M, alt=alt * 0.35, larg=1.0, lado=-1, eixo='Y')


def siderurgica(M):
    # bloco 2x2 nos tiles (0,0) alto-forno, (0,1) casa de corrida, (1,0) silos de minério, (1,1) pátio de escória
    for (tx, ty) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        x0, y0, _ = P(tx, 0, ty * 16)
        bx('chao_patio', 12, 12, 0.02, (x0 - 6, y0 - 6, 0.01), M['escoria'])
    # alto-forno
    fx, fy, _ = P(0, 7, 7)
    cyl('base_forno', 3.2, 3.0, fx, fy, 1.5, M['concreto_esc'], 'Z', 32)
    cyl('forno', 2.8, 11.0, fx, fy, 8.5, M['ferrugem'], 'Z', 32, r2=2.0)
    for z in (5.0, 8.0, 11.0):
        cyl('cinta', 2.9 - (z - 3) * 0.07, 0.25, fx, fy, z, M['aco'], 'Z', 32)
    cyl('goela', 1.6, 2.5, fx, fy, 15.2, M['aco'], 'Z', 24)
    plataforma(fx, fy, 14.0, 3.0, M)
    for s in (-1, 1):
        tubo('descendente', (fx + s * 0.8, fy, 16.4), (fx + s * 0.8, fy + 0.6, 19.0), 0.4, M['aco'])
    tubo('descendente', (fx, fy + 0.6, 19.0), (fx + 3.5, fy + 4.5, 12.0), 0.5, M['aco'])
    # glendões (regeneradores) atrás
    for i, (dx, dy) in enumerate([(3.4, -3.5), (3.4, 0.0), (3.4, 3.5)]):
        cyl('regenerador', 1.5, 12.0, fx + dx, fy + dy, 6.0, M['aco_claro'], 'Z', 24)
        sphere('regenerador_topo', 1.5, fx + dx, fy + dy, 12.0, M['aco_claro'], 1, 1, 0.6)
    # correia inclinada do silo (tile 1,0) até o topo do forno
    sx_, sy_, _ = P(1, 10, 7)
    a = Vector((sx_, sy_, 2.0)); b = Vector((fx - 1.5, fy, 15.5))
    d = b - a
    gal = bx('correia', d.length, 1.6, 1.6, tuple((a + b) / 2), M['zinco'])
    gal.rotation_mode = 'QUATERNION'
    gal.rotation_quaternion = d.to_track_quat('X', 'Z')
    for t in (0.35, 0.7):
        p = a + d * t
        bx('cavalete', 0.3, 1.2, p.z, (p.x, p.y, p.z / 2), M['aco'])
    # silos de minério e carvão (tile 1,0)
    for j, oy in enumerate((3.5, 8.0, 12.5)):
        x, y, _ = P(1, 11, oy)
        bx('silo', 4.0, 3.0, 5.0, (x, y, 3.5), M['concreto'])
        prism('funil', [(-2.0, 0), (2.0, 0), (0.6, -1.2), (-0.6, -1.2)], 3.0, y, M['concreto_esc'], 'XZ').location = (x, 0, 1.0)
        for s in (-1, 1):
            bx('pe', 0.4, 0.4, 1.2, (x + s * 1.6, y, 0.6), M['concreto_esc'])
        sphere('minerio_topo', 1.0, x, y, 6.0, M['minerio'], 1.8, 1.3, 0.5)
    hx, hy, _ = P(1, 4, 12)
    cyl('chamine', 0.8, 16.0, hx, hy, 8.0, M['tijolo'], 'Z', 20, r2=0.6)
    cyl('chamine_topo', 0.66, 0.4, hx, hy, 16.1, M['aco'], 'Z', 20)
    # casa de corrida (tile 0,1): galpão com abertura incandescente
    cx, cy, _ = P(0, 8, 24)
    galpao_alto(cx, cy, 10.0, 8.0, 6.5, M, eixo='Y', lanternim=False)
    bx('boca', 0.06, 3.0, 2.2, (cx - 4.03, cy + 1.0, 1.1), M['gusa'])
    bx('canal', 2.5, 0.5, 0.1, (cx - 5.3, cy + 1.0, 0.06), M['gusa'])
    # pátio de escória (tile 1,1): panelas sobre trilhos (chão)
    tx, ty, _ = P(1, 8, 24)
    for s in (-1, 1):
        bx('chao_trilho', 0.1, 11.5, 0.12, (tx + s * 0.7, ty, 0.06), M['trilho'])
    for j in range(3):
        y = ty - 4.0 + j * 3.6
        bx('chao_vagao', 1.8, 2.4, 0.5, (tx, y, 0.45), M['aco'])
        cyl('chao_panela', 1.0, 1.1, tx, y, 1.2, M['ferrugem'], 'Z', 20, r2=1.25)
        cyl('chao_escoria_quente', 1.15, 0.1, tx, y, 1.72, M['gusa'], 'Z', 20)
    for (ox, oy, r) in [(3, 18, 1.4), (4, 29, 1.0)]:
        x, y, _ = P(1, ox, oy)
        sphere('chao_monte', r, x, y, 0, M['escoria'], 1.5, 1.2, 0.6)


def laminacao(k, M):
    """gfx56 (2126): galpão de laminação, comprido em X, emenda com o vizinho."""
    cx, cy, _ = P(k, 8, 8)
    galpao_alto(cx, cy, 12.0, 8.4, 7.5, M)
    x, y, _ = P(k, 0, 0)
    bx('chao_patio', 12, 12, 0.02, (x - 6, y - 6, 0.01), M['concreto_esc'])
    for i in range(3):
        bx('chao_tarugos', 2.4, 0.3, 0.3, (cx - 3.5 + i * 3.0, cy - 5.3, 0.15), M['ferrugem'])


def aciaria(k, M):
    """gfx57 (2128): aciaria Siemens-Martin, mesmo galpão com chaminés altas."""
    cx, cy, _ = P(k, 8, 8)
    galpao_alto(cx, cy, 12.0, 8.4, 7.5, M, telha='zinco')
    for dx in (-3.5, 0.0, 3.5):
        cyl('chamine', 0.7, 17.0, cx + dx, cy + 2.6, 8.5, M['tijolo'], 'Z', 20, r2=0.55)
        cyl('chamine_topo', 0.6, 0.4, cx + dx, cy + 2.6, 17.1, M['aco'], 'Z', 20)
    x, y, _ = P(k, 0, 0)
    bx('chao_patio', 12, 12, 0.02, (x - 6, y - 6, 0.01), M['concreto_esc'])
    bx('chao_lingoteira', 1.0, 1.0, 0.8, (cx - 2.0, cy - 5.4, 0.4), M['aco'])
    bx('chao_lingoteira', 1.0, 1.0, 0.8, (cx - 0.6, cy - 5.4, 0.4), M['aco'])


# ---------------- mina de ferro (16 tiles de chão, 4x4) ----------------
def mina_ferro(M):
    U = 0.75
    n = 192
    L = 48.0
    rnd = random.Random(7)
    bm = bmesh.new()
    vs = []
    # centro da cava e profundidade (rasa: o desenho por tile não aguenta buraco fundo)
    def raio(ox, oy):
        return math.hypot((ox - 30) / 21.0, (oy - 30) / 19.0)

    def altura(ox, oy):
        r = raio(ox, oy)
        prof = 0.9 * max(0.0, 1 - r) ** 0.5
        # O desenho é por tile: um buraco de verdade deixa frestas na borda de cada tile. A cava fica no nível
        # do chão e as bancadas saem pela cor (abaixo); só um relevo leve.
        return 0.03 + 0.03 * math.sin(ox * 1.7) * math.sin(oy * 1.3)

    def prof(ox, oy):
        return 0.9 * max(0.0, 1 - raio(ox, oy)) ** 0.5
    for i in range(n + 1):
        row = []
        for j in range(n + 1):
            ox, oy = 64.0 * i / n, 64.0 * j / n
            row.append(bm.verts.new((-ox * U, -oy * U, altura(ox, oy))))
        vs.append(row)
    ob_faces = []
    for i in range(n):
        for j in range(n):
            ox, oy = 64.0 * (i + 0.5) / n, 64.0 * (j + 0.5) / n
            if min(ox, oy, 64 - ox, 64 - oy) < 3.0:
                continue  # margem de grama: fica a grama do conjunto base (fundo)
            ob_faces.append(bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1])))
    me = bpy.data.meshes.new('chao_cava')
    bm.to_mesh(me)
    ob = bpy.data.objects.new('chao_cava', me)
    bpy.context.collection.objects.link(ob)
    for m_ in ('minerio', 'minerio2', 'grama_m'):
        me.materials.append(M[m_])
    me.materials.append(mat('Minério talude', '#5a2c1a', 0.0, 0.95))
    me.materials.append(mat('Minério fundo', '#6b3a26', 0.0, 0.95))
    for p in me.polygons:
        c = p.center
        ox, oy = -c.x / U, -c.y / U
        borda = min(ox, oy, 64 - ox, 64 - oy)
        if borda < 3.0:
            p.material_index = 2
        else:
            q = prof(ox, oy) / 0.3
            nivel, frac = int(q), q - int(q)
            if nivel > 0 and frac < 0.3:
                p.material_index = 3  # talude (degrau) escuro
            else:
                p.material_index = [0, 1, 4, 4][min(nivel, 3)]
    # cerca branca em volta (o original tem cerca)
    for lado in range(4):
        for t in range(0, 64, 3):
            ox, oy = [(t, 1.5), (62.5, t), (t, 62.5), (1.5, t)][lado]
            bx('chao_cerca', 0.1, 0.1, 1.1, (-ox * U, -oy * U, 0.55), M['cerca'])
        a = [(0, 1.5), (62.5, 0), (0, 62.5), (1.5, 0)][lado]
        b = [(64, 1.5), (62.5, 64), (64, 62.5), (1.5, 64)][lado]
        for z in (0.5, 0.95):
            p0 = Vector((-a[0] * U, -a[1] * U, z)); p1 = Vector((-b[0] * U, -b[1] * U, z))
            bx('chao_cerca_trave', (p1 - p0).length, 0.05, 0.06, tuple((p0 + p1) / 2), M['cerca'],
               (0, 0, math.atan2(p1.y - p0.y, p1.x - p0.x)))
    # britador e carregamento (baixos, ficam no chão do tile 0..1)
    x, y, _ = P(0, 9, 22)
    bx('chao_britador', 4.0, 3.0, 3.2, (x, y, 1.6), M['zinco'])
    telhado_duas_aguas(x - 2.0, x + 2.0, y - 1.5, y + 1.5, 3.2, 0.7, M['telha'])
    a = Vector(P(1, 2, 24)) + Vector((0, 0, 0.3)); b = Vector((x - 2.0, y, 2.6))
    d = b - a
    c = bx('chao_correia', d.length, 0.9, 0.5, tuple((a + b) / 2), M['ferrugem'])
    c.rotation_mode = 'QUATERNION'; c.rotation_quaternion = d.to_track_quat('X', 'Z')
    for (ox, oy, r) in [(6, 40, 1.6), (9, 44, 1.2), (52, 10, 1.4), (22, 56, 1.5)]:
        x, y, _ = P(0, ox, oy)
        sphere('chao_pilha', r, x, y, 0.0, M['minerio2'], 1.6, 1.3, 0.55)
    # caminhão basculante na bancada
    x, y, _ = P(1, 12, 30, )
    z = altura(28, 30)
    bx('chao_cacamba', 2.6, 2.0, 1.0, (x, y, z + 1.3), M['amarelo'])
    bx('chao_cabine', 1.2, 2.0, 1.2, (x - 1.9, y, z + 1.2), M['amarelo'])
    for s in (-1, 1):
        for dx in (-1.6, 0.6):
            cyl('chao_roda', 0.45, 0.35, x + dx, y + s * 1.0, z + 0.45, M['preto'], 'Y', 12)
    for o in bpy.context.collection.objects:
        if not o.name.startswith('chao'):
            o.name = 'chao_' + o.name


INDUSTRIAS = [
    ('refinaria', [lambda M, f=f, k=k: f(k, M) for k, f in enumerate(REFINARIA)]),
    ('siderurgica', [siderurgica, lambda M: laminacao(3, M), lambda M: aciaria(5, M)]),
    ('mina_ferro', [mina_ferro]),
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
