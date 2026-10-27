# Modela os veículos rodoviários de 1950 (clima temperado) do OpenTTD,
# fiéis aos tipos reais que representam, e exporta cada um em GLB.
# Eixos: X = frente, Y = esquerda, Z = cima. Origem no chão, centro do veículo. Unidades em metros.
import bpy, bmesh, math, os, sys
from mathutils import Vector

OUT = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else '/home/claude/garagem/glb'
os.makedirs(OUT, exist_ok=True)

# ---------------- utilidades ----------------
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

MATS = {}
def mat(name, color, metal=0.0, rough=0.5, coat=0.0, alpha=1.0):
    key = name
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*srgb(color), 1)
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
        m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None
    MATS[key] = m
    return m

def srgb(hexstr):
    h = hexstr.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)

def finish(obj, m, bevel=0.0, segs=2, smooth=False):
    obj.data.materials.clear()
    obj.data.materials.append(m)
    if bevel > 0:
        bm = obj.modifiers.new('bevel', 'BEVEL')
        bm.width = bevel
        bm.segments = segs
        bm.limit_method = 'ANGLE'
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj

def new_obj(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob

def box(name, sx, sy, sz, x, y, z, m, bevel=0.0, segs=2):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * sx + x, v.co.y * sy + y, v.co.z * sz + z))
    return finish(new_obj(name, bm), m, bevel, segs)

def cyl(name, r, depth, x, y, z, m, axis='Y', segs=24, r2=None, bevel=0.0, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=depth)
    ob = new_obj(name, bm)
    if axis == 'Y':
        ob.rotation_euler = (math.pi / 2, 0, 0)
    elif axis == 'X':
        ob.rotation_euler = (0, math.pi / 2, 0)
    ob.location = (x, y, z)
    return finish(ob, m, bevel, 2, smooth)

def sphere(name, r, x, y, z, m, sx=1, sy=1, sz=1):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=r)
    ob = new_obj(name, bm)
    ob.location = (x, y, z)
    ob.scale = (sx, sy, sz)
    return finish(ob, m, smooth=True)

def prism(name, pts, w, offset, m, plane='XZ', bevel=0.0, segs=2):
    """Extrude um polígono 2D. plane XZ: pts=(x,z), extrude em Y; YZ: pts=(y,z), extrude em X."""
    bm = bmesh.new()
    a, b = offset - w / 2, offset + w / 2
    def P(p, t):
        return (p[0], t, p[1]) if plane == 'XZ' else (t, p[0], p[1])
    f1 = [bm.verts.new(P(p, a)) for p in pts]
    f2 = [bm.verts.new(P(p, b)) for p in pts]
    bm.faces.new(f1[::-1])
    bm.faces.new(f2)
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((f1[i], f1[j], f2[j], f2[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return finish(new_obj(name, bm), m, bevel, segs)

def asa(name, path, width, yc, m, crown=0.05, skirt=0.07, thick=0.025, nw=8):
    """Para-lama em chapa curva: segue o caminho (x,z) visto de lado, com abaulamento na largura
    e as bordas viradas para baixo; espessura por solidify; sombreamento suave."""
    bm = bmesh.new()
    rows = []
    n = len(path)
    for i, (x, z) in enumerate(path):
        a = path[max(i - 1, 0)]
        b = path[min(i + 1, n - 1)]
        tx, tz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, tz) or 1
        nx, nz = -tz / L, tx / L  # normal "para fora/para cima"
        if nz < 0:
            nx, nz = -nx, -nz
        row = []
        for j in range(nw + 1):
            t = j / nw * 2 - 1
            lift = crown * (1 - t * t)
            if abs(t) > 0.85:
                lift -= skirt * (abs(t) - 0.85) / 0.15
            row.append(bm.verts.new((x + nx * lift, yc + t * width / 2, z + nz * lift)))
        rows.append(row)
    for i in range(n - 1):
        for j in range(nw):
            bm.faces.new((rows[i][j], rows[i + 1][j], rows[i + 1][j + 1], rows[i][j + 1]))
    ob = new_obj(name, bm)
    finish(ob, m, smooth=True)
    so = ob.modifiers.new('esp', 'SOLIDIFY')
    so.thickness = thick
    return ob

def arc(cx, cz, r, a0, a1, n):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cz + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

# ---------------- materiais ----------------
def materiais(company):
    return {
        'paint': mat('Pintura empresa', company, 0.0, 0.32),
        'black': mat('Preto esmaltado', '#16181a', 0.0, 0.35),
        'chrome': mat('Cromado', '#d8dadc', 1.0, 0.12),
        'rubber': mat('Pneu', '#1b1b1b', 0.0, 0.85),
        'steelwheel': mat('Roda de aço', '#2a2c2e', 0.6, 0.45),
        'glass': mat('Vidro', '#1d2a33', 0.2, 0.05),
        'lamp': mat('Lente do farol', '#f3f1e6', 0.0, 0.08),
        'red_lamp': mat('Lanterna', '#a51c12', 0.0, 0.2),
        'chassis': mat('Chassi', '#1f2021', 0.3, 0.6),
        'wood': mat('Madeira', '#8a6a46', 0.0, 0.8),
        'wood_dark': mat('Madeira escura', '#5f4630', 0.0, 0.85),
        'cream': mat('Creme', '#e9dfc4', 0.0, 0.4),
        'grey': mat('Cinza', '#7d8287', 0.3, 0.5),
        'steel': mat('Aço', '#8e9499', 0.8, 0.35),
        'coal': mat('Carvão', '#121214', 0.0, 0.7),
        'ore': mat('Minério de ferro', '#7a3e26', 0.0, 0.9),
        'grain': mat('Grão', '#d4b25e', 0.0, 0.9),
        'canvas': mat('Lona', '#5f6b4e', 0.0, 0.9),
        'gpo': mat('Vermelho GPO', '#b0181b', 0.0, 0.3),
        'gold': mat('Dourado', '#c9a24a', 0.8, 0.3),
        'tank': mat('Tanque', '#c8ccce', 0.6, 0.3),
        'log': mat('Tora', '#7b5a3a', 0.0, 0.9),
        'logend': mat('Topo da tora', '#c9a77a', 0.0, 0.9),
        'cow': mat('Gado', '#5a3b28', 0.0, 0.9),
    }

# ---------------- peças comuns ----------------
def roda(name, x, y, r, w, M, dual=False):
    parts = []
    for k, dy in enumerate([0] if not dual else [-w * 0.55, w * 0.55]):
        yy = y + dy
        t = cyl(f'{name}_pneu{k}', r, w, x, yy, r, M['rubber'], 'Y', 32, bevel=w * 0.28)
        parts.append(t)
        side = 1 if y > 0 else -1
        disc = cyl(f'{name}_disco{k}', r * 0.62, w + 0.012, x, yy, r, M['steelwheel'], 'Y', 28)
        parts.append(disc)
        hub = cyl(f'{name}_cubo{k}', r * 0.2, w + 0.06, x, yy, r, M['chrome'] if not dual else M['steelwheel'], 'Y', 16)
        parts.append(hub)
        # porcas
        for i in range(8):
            a = 2 * math.pi * i / 8
            parts.append(cyl(f'{name}_porca{k}{i}', 0.018, w + 0.04, x + math.cos(a) * r * 0.32, yy, r + math.sin(a) * r * 0.32, M['chrome'], 'Y', 6, smooth=False))
    return parts

def farol(name, x, y, z, M, r=0.11):
    sphere(f'{name}_corpo', r, x, y, z, M['chrome'], 1.0, 1.0, 1.0)
    cyl(f'{name}_lente', r * 0.86, 0.02, x + r * 0.78, y, z, M['lamp'], 'X', 20)
    box(f'{name}_haste', 0.03, 0.03, 0.16, x - 0.02, y, z - r - 0.07, M['black'])

# ---------------- caminhão de capô britânico, anos 1930 (tipo Bedford WT / Leyland Cub) ----------------
TRUCK = dict(front_axle=1.95, rear_axle=-1.25, r_front=0.44, r_rear=0.44, frame_z=0.74, cab_back=0.45, cab_front=1.45, bed_front=0.35, bed_back=-2.55)

def caminhao_1930(M, cab_color_key='paint'):
    T = TRUCK
    P = M[cab_color_key]
    # chassi
    for s in (1, -1):
        box('longarina', 5.2, 0.08, 0.16, -0.25, s * 0.42, T['frame_z'], M['chassis'], 0.01)
    for x in (2.45, 0.9, -0.6, -2.4):
        box('travessa', 0.08, 0.92, 0.1, x, 0, T['frame_z'], M['chassis'])
    # eixos e rodas
    cyl('eixo_d', 0.05, 1.62, T['front_axle'], 0, T['r_front'], M['chassis'], 'Y', 10)
    cyl('eixo_t', 0.07, 1.6, T['rear_axle'], 0, T['r_rear'], M['chassis'], 'Y', 10)
    box('diferencial', 0.34, 0.3, 0.3, T['rear_axle'], 0, T['r_rear'], M['chassis'], 0.05, 3)
    for s in (1, -1):
        roda('roda_d', T['front_axle'], s * 0.82, T['r_front'], 0.19, M)
        roda('roda_t', T['rear_axle'], s * 0.86, T['r_rear'], 0.19, M, dual=True)
        # feixes de mola
        box('mola_d', 0.9, 0.07, 0.06, T['front_axle'], s * 0.42, T['frame_z'] - 0.14, M['chassis'], 0.02)
        box('mola_t', 1.15, 0.08, 0.07, T['rear_axle'], s * 0.42, T['frame_z'] - 0.14, M['chassis'], 0.02)
    # radiador: moldura cromada com grade de barras verticais
    rx = 2.62
    box('radiador_moldura', 0.1, 0.66, 0.78, rx, 0, 1.2, M['chrome'], 0.035, 3)
    box('radiador_colmeia', 0.04, 0.54, 0.64, rx + 0.04, 0, 1.19, M['black'])
    for i in range(13):
        y = -0.25 + i * (0.5 / 12)
        box('grade', 0.03, 0.012, 0.6, rx + 0.065, y, 1.19, M['chrome'])
    box('radiador_tampa', 0.06, 0.06, 0.07, rx - 0.02, 0, 1.63, M['chrome'], 0.02)
    sphere('emblema', 0.035, rx + 0.07, 0, 1.47, M['gold'], 0.5, 1, 1)
    # capô arredondado (perfil em Y-Z extrudado em X)
    hood = [(-0.35, 0.86), (0.35, 0.86)] + [(0.35 * math.cos(math.radians(a)), 1.38 + 0.2 * math.sin(math.radians(a))) for a in range(0, 181, 15)]
    hood = [(-0.35, 0.86), (0.35, 0.86), (0.35, 1.38)] + [(0.35 * math.cos(math.radians(a)), 1.38 + 0.2 * math.sin(math.radians(a))) for a in range(15, 166, 15)] + [(-0.35, 1.38)]
    prism('capo', hood, rx - 0.05 - T['cab_front'], (rx - 0.05 + T['cab_front']) / 2, P, 'YZ', 0.02)
    box('capo_dobradica', rx - 0.05 - T['cab_front'], 0.02, 0.02, (rx - 0.05 + T['cab_front']) / 2, 0, 1.585, M['chrome'])
    for s in (1, -1):
        for i in range(6):
            box('veneziana', 0.06, 0.012, 0.22, T['cab_front'] + 0.3 + i * 0.1, s * 0.355, 1.17, M['black'])
    # para-lamas dianteiros (perfil lateral em X-Z, chapa curva) + estribo
    for s in (1, -1):
        fx, fr = T['front_axle'], T['r_front'] + 0.09
        path = [(2.78, 0.66), (2.7, 0.76)] + arc(fx, T['r_front'], fr, 25, 160, 20)[1:] + [(T['cab_front'] - 0.12, 0.66), (T['cab_front'] - 0.3, 0.6), (T['cab_back'] - 0.08, 0.6)]
        asa('paralama_d', path, 0.42, s * 0.83, M['black'], crown=0.06, skirt=0.08)
        box('suporte_estribo', 0.05, 0.4, 0.05, T['cab_back'] + 0.1, s * 0.62, 0.56, M['chassis'])
        farol(f'farol{s}', 2.48, s * 0.58, 1.28, M, 0.12)
        box('barra_farois', 0.04, 1.1, 0.04, 2.5, 0, 1.08, M['black'])
        box('lanterna_lateral', 0.07, 0.05, 0.05, 2.15, s * 0.92, 1.07, M['chrome'], 0.015)
    box('para_choque', 0.08, 1.86, 0.1, 2.8, 0, 0.66, M['black'], 0.02)
    for s in (1, -1):
        box('suporte_pc', 0.22, 0.06, 0.06, 2.68, s * 0.42, 0.7, M['chassis'])
    # cabine fechada (perfil lateral)
    cb, cf = T['cab_back'], T['cab_front']
    # perfil lateral: frente quase vertical com para-brisa levemente inclinado, teto abaulado com cantos redondos
    roof = 2.3
    cab = [(cb, 0.74), (cf, 0.74), (cf, 1.52), (cf - 0.06, 2.12)]
    cab += [(cf - 0.06 - 0.14 * (1 - math.cos(math.radians(a))), 2.12 + (roof - 2.12) * math.sin(math.radians(a))) for a in (25, 50, 75, 90)]
    cab += [(cb + 0.14 - 0.14 * math.sin(math.radians(a)), roof - 0.14 * (1 - math.cos(math.radians(a)))) for a in (20, 45, 70, 90)]
    cab += [(cb, 1.0)]
    ob = prism('cabine', cab, 1.86, 0, P, 'XZ', 0.07, 4)
    # abaulamento lateral do teto: uma capa arredondada sobre o teto
    capa = [(-0.93, 0.0), (0.93, 0.0)] + [(0.93 * math.cos(math.radians(a)), 0.07 * math.sin(math.radians(a))) for a in range(15, 166, 15)]
    prism('teto_abaulado', [(p[0], p[1] + roof - 0.035) for p in capa], cf - cb - 0.3, (cf + cb) / 2 - 0.03, P, 'YZ', 0.03)
    box('pala', 0.12, 1.8, 0.03, cf - 0.04, 0, 2.2, P, 0.012)
    # para-brisa em duas folhas com moldura
    for s in (1, -1):
        box('moldura_parabrisa', 0.02, 0.82, 0.58, cf - 0.055, s * 0.44, 1.83, M['black'])
        box('parabrisa', 0.02, 0.76, 0.52, cf - 0.045, s * 0.44, 1.83, M['glass'])
    for s in (1, -1):
        box('moldura_janela', 0.6, 0.02, 0.52, cb + 0.43, s * 0.94, 1.82, M['black'])
        box('janela_lateral', 0.54, 0.02, 0.46, cb + 0.43, s * 0.946, 1.82, M['glass'])
        box('porta_contorno_f', 0.012, 0.012, 1.0, cf - 0.1, s * 0.94, 1.45, M['black'])
        box('porta_contorno_t', 0.012, 0.012, 1.0, cb + 0.1, s * 0.94, 1.45, M['black'])
        box('porta_contorno_b', cf - cb - 0.2, 0.012, 0.012, (cf + cb) / 2, s * 0.94, 0.95, M['black'])
        box('macaneta', 0.1, 0.03, 0.02, cb + 0.22, s * 0.955, 1.5, M['chrome'])
        box('retrovisor_braco', 0.02, 0.24, 0.02, cf - 0.08, s * 1.05, 1.78, M['black'])
        box('retrovisor', 0.02, 0.11, 0.15, cf - 0.08, s * 1.17, 1.78, M['chrome'], 0.01)
    box('janela_traseira', 0.02, 0.72, 0.3, cb - 0.01, 0, 1.92, M['glass'])
    # tanque de combustível e escapamento
    cyl('tanque_comb', 0.17, 0.6, cb - 0.05, -0.68, 0.55, M['chassis'], 'X', 16)
    cyl('escapamento', 0.035, 1.6, -0.7, 0.62, 0.48, M['chassis'], 'X', 8)

def para_lamas_traseiros(M, z=1.0, width=0.55):
    for s in (1, -1):
        rr = TRUCK['r_rear'] + 0.1
        path = arc(TRUCK['rear_axle'], TRUCK['r_rear'], rr, 10, 170, 18)
        asa('paralama_t', path, width, s * 0.87, M['black'], crown=0.03, skirt=0.05, thick=0.02)

def lanternas_traseiras(M, x):
    for s in (1, -1):
        box('lanterna_t', 0.04, 0.09, 0.07, x, s * 0.82, 0.78, M['red_lamp'], 0.01)

# ---------------- carrocerias ----------------
BF, BB = TRUCK['bed_front'], TRUCK['bed_back']
BL, BX = BF - BB, (BF + BB) / 2
FLOOR = 0.92

def piso(M, m='wood_dark'):
    box('piso', BL, 2.12, 0.08, BX, 0, FLOOR, M[m], 0.01)
    for s in (1, -1):
        box('longarina_piso', BL, 0.09, 0.12, BX, s * 0.44, FLOOR - 0.1, M['chassis'])

def cacamba(M, h, carga=None, cor='steel'):
    piso(M)
    W = 2.12
    for s in (1, -1):
        box('lateral', BL, 0.05, h, BX, s * (W / 2 - 0.025), FLOOR + h / 2, M[cor], 0.01)
        for i in range(5):
            box('reforco', 0.05, 0.06, h, BB + 0.15 + i * (BL - 0.3) / 4, s * (W / 2), FLOOR + h / 2, M['chassis'], 0.008)
    box('frente_cac', 0.05, W, h + 0.25, BF - 0.025, 0, FLOOR + (h + 0.25) / 2, M[cor], 0.01)
    box('tampa', 0.05, W, h, BB + 0.025, 0, FLOOR + h / 2, M[cor], 0.01)
    box('protetor_cabine', 0.4, W, 0.05, BF + 0.15, 0, FLOOR + h + 0.25, M[cor], 0.01)
    box('pistao', 0.12, 0.12, 0.5, BF - 0.4, 0, FLOOR - 0.1, M['chassis'])
    if carga:
        monte(M, carga, FLOOR + h - 0.12, W - 0.14)

def monte(M, m, z, w):
    bm = bmesh.new()
    nx, ny = 16, 9
    vs = []
    for i in range(nx + 1):
        row = []
        for j in range(ny + 1):
            u, v = i / nx, j / ny
            hgt = 0.28 * math.sin(math.pi * u) * math.sin(math.pi * v) + 0.03 * math.sin(u * 37 + v * 23)
            row.append(bm.verts.new((BB + 0.05 + u * (BL - 0.1), -w / 2 + v * w, z + hgt)))
        vs.append(row)
    for i in range(nx):
        for j in range(ny):
            bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
    finish(new_obj('monte_carga', bm), M[m], smooth=True)

def bau(M, h, cor_key, ripas=False, janelas=False, lona=False):
    piso(M)
    W = 2.1
    if lona:
        prof = [(-W / 2, 0), (W / 2, 0), (W / 2, h - 0.25)] + [((W / 2) * math.cos(math.radians(a)), h - 0.25 + 0.25 * math.sin(math.radians(a))) for a in range(20, 161, 20)] + [(-W / 2, h - 0.25)]
        prof = [(p[0], p[1] + FLOOR + 0.04) for p in prof]
        prism('lona', prof, BL, BX, M['canvas'], 'YZ', 0.03)
        for i in range(5):
            box('cinta', 0.03, W + 0.02, 0.02, BB + 0.2 + i * (BL - 0.4) / 4, 0, FLOOR + 0.5, M['chassis'])
        for s in (1, -1):
            box('guarda_lateral', BL, 0.05, 0.4, BX, s * (W / 2 + 0.01), FLOOR + 0.24, M['wood'], 0.01)
        return
    prof = [(-W / 2, FLOOR + 0.04), (W / 2, FLOOR + 0.04), (W / 2, FLOOR + h - 0.08), (W / 2 - 0.08, FLOOR + h), (-W / 2 + 0.08, FLOOR + h), (-W / 2, FLOOR + h - 0.08)]
    prism('bau', prof, BL, BX, M[cor_key], 'YZ', 0.02)
    box('teto_bau', BL + 0.04, W - 0.1, 0.03, BX, 0, FLOOR + h + 0.005, M['cream'], 0.01)
    for s in (1, -1):
        if ripas:
            for i in range(6):
                box('nervura', 0.04, 0.03, h - 0.1, BB + 0.1 + i * (BL - 0.2) / 5, s * (W / 2 + 0.012), FLOOR + h / 2, M['chassis'])
        if janelas:
            for i in range(2):
                box('visor', 0.22, 0.02, 0.1, BX - 0.5 + i * 1.0, s * (W / 2 + 0.01), FLOOR + h - 0.35, M['glass'])
                box('grade_visor', 0.24, 0.025, 0.012, BX - 0.5 + i * 1.0, s * (W / 2 + 0.014), FLOOR + h - 0.35, M['chrome'])
        box('friso', BL, 0.02, 0.06, BX, s * (W / 2 + 0.01), FLOOR + 0.45, M['cream'])
    box('porta_t_e', 0.02, W / 2 - 0.06, h - 0.2, BB - 0.005, 0.5, FLOOR + h / 2, M['chassis'])
    box('porta_t_d', 0.02, W / 2 - 0.06, h - 0.2, BB - 0.005, -0.5, FLOOR + h / 2, M['chassis'])
    for s in (1, -1):
        box('dobradica', 0.03, 0.04, 0.1, BB - 0.02, s * 0.95, FLOOR + h * 0.3, M['chrome'])
        box('dobradica2', 0.03, 0.04, 0.1, BB - 0.02, s * 0.95, FLOOR + h * 0.75, M['chrome'])

def boiadeiro(M):
    piso(M, 'wood')
    W, h = 2.12, 1.15
    for s in (1, -1):
        for k in range(5):
            box('ripa', BL, 0.04, 0.09, BX, s * (W / 2 - 0.02), FLOOR + 0.12 + k * 0.24, M['wood'], 0.008)
        for i in range(7):
            box('montante', 0.07, 0.06, h, BB + 0.05 + i * (BL - 0.1) / 6, s * (W / 2), FLOOR + h / 2, M['wood_dark'])
    for k in range(5):
        box('ripa_f', 0.04, W, 0.09, BF - 0.02, 0, FLOOR + 0.12 + k * 0.24, M['wood'], 0.008)
        box('ripa_t', 0.04, W, 0.09, BB + 0.02, 0, FLOOR + 0.12 + k * 0.24, M['wood'], 0.008)
    # gado (silhuetas simples, visíveis entre as ripas)
    for i, (x, y) in enumerate([(-0.3, 0.45), (-1.3, -0.4), (-2.0, 0.42), (0.0, -0.45)]):
        box('boi', 0.95, 0.42, 0.5, x, y, FLOOR + 0.62, M['cow'], 0.12, 3)
        box('cabeca', 0.3, 0.26, 0.28, x + 0.55, y, FLOOR + 0.82, M['cow'], 0.08, 3)

def tanque(M):
    for s in (1, -1):
        box('berco', BL - 0.3, 0.08, 0.14, BX, s * 0.5, FLOOR + 0.02, M['chassis'])
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=36, radius1=1.0, radius2=1.0, depth=BL - 0.1)
    for v in bm.verts:
        v.co = Vector((v.co.z + BX, v.co.x * 1.0, v.co.y * 0.62 + FLOOR + 0.66))
    ob = new_obj('tanque', bm)
    finish(ob, M['tank'], 0.08, 4, smooth=True)
    for i in range(3):
        cyl('domo', 0.2, 0.14, BB + 0.55 + i * (BL - 1.1) / 2, 0, FLOOR + 1.32, M['tank'], 'Z', 20)
        cyl('tampa_domo', 0.21, 0.03, BB + 0.55 + i * (BL - 1.1) / 2, 0, FLOOR + 1.4, M['chrome'], 'Z', 20)
    for s in (1, -1):
        box('passarela', BL - 0.4, 0.12, 0.02, BX, s * 0.32, FLOOR + 1.29, M['steel'])
        box('cinta_tanque', 0.05, 2.04, 0.02, BB + 0.3, 0, FLOOR + 0.66, M['chassis'])
    box('escada', 0.03, 0.4, 0.9, BB - 0.02, 0.6, FLOOR + 0.7, M['steel'])
    cyl('valvula', 0.06, 0.25, BB - 0.08, -0.4, FLOOR + 0.15, M['chrome'], 'X', 12)

def toras(M):
    piso(M, 'wood')
    for s in (1, -1):
        for i in range(3):
            box('estaca', 0.08, 0.08, 1.0, BB + 0.3 + i * (BL - 0.6) / 2, s * 1.0, FLOOR + 0.5, M['chassis'])
    rows = [(-0.62, 0.22), (-0.2, 0.22), (0.2, 0.22), (0.62, 0.22), (-0.41, 0.6), (0.0, 0.6), (0.41, 0.6), (-0.2, 0.95), (0.2, 0.95)]
    for k, (y, z) in enumerate(rows):
        r = 0.2 + 0.015 * ((k * 7) % 3)
        cyl('tora', r, BL + 0.35, BX - 0.15, y, FLOOR + z, M['log'], 'X', 14)
        cyl('topo_tora', r - 0.01, 0.01, BB - 0.33, y, FLOOR + z, M['logend'], 'X', 14)
    for i in range(2):
        box('corrente', 0.03, 2.05, 0.03, BB + 0.8 + i * 1.2, 0, FLOOR + 1.12, M['steel'])

def aco(M):
    piso(M, 'wood_dark')
    for s in (1, -1):
        box('borda', BL, 0.05, 0.18, BX, s * 1.04, FLOOR + 0.1, M['wood'])
    for i in range(3):
        box('chapa', BL - 0.3, 1.5, 0.05, BX, 0, FLOOR + 0.08 + i * 0.055, M['steel'], 0.005)
    for k in range(3):
        y = -0.5 + k * 0.5
        box('viga_alma', BL - 0.5, 0.025, 0.28, BX, y, FLOOR + 0.39, M['steel'])
        box('viga_mesa_s', BL - 0.5, 0.2, 0.025, BX, y, FLOOR + 0.53, M['steel'])
        box('viga_mesa_i', BL - 0.5, 0.2, 0.025, BX, y, FLOOR + 0.25, M['steel'])
    for i in range(2):
        box('amarra', 0.04, 2.08, 0.03, BB + 0.7 + i * 1.4, 0, FLOOR + 0.56, M['chassis'])

def correio(M):
    bau(M, 1.55, 'gpo')
    # brasão real (GPO) e friso preto
    for s in (1, -1):
        cyl('brasao', 0.13, 0.015, BX + 0.6, s * 1.062, FLOOR + 1.0, M['gold'], 'Y', 20)
        box('friso_preto', BL, 0.02, 0.06, BX, s * 1.06, FLOOR + 0.12, M['black'])

# ---------------- ônibus AEC Regal (1929), meia-cabine, um andar ----------------
def onibus_regal(M):
    red, cream = mat('Vermelho London General', '#9c1c1c', 0.0, 0.3), M['cream']
    roofm = mat('Teto prata', '#b9bbb6', 0.3, 0.45)
    W = 2.29
    rx = 4.2                      # frente do radiador
    cx1 = rx - 0.3                # frente da meia-cabine (quase alinhada ao radiador)
    L1 = 2.95                     # anteparo dianteiro do salão
    L0 = -4.15                    # traseira
    fa, ra, r = 3.45, -1.5, 0.5
    for s in (1, -1):
        box('longarina', 7.9, 0.08, 0.16, -0.05, s * 0.45, 0.72, M['chassis'], 0.01)
    cyl('eixo_d', 0.05, 1.7, fa, 0, r, M['chassis'], 'Y', 10)
    cyl('eixo_t', 0.07, 1.68, ra, 0, r, M['chassis'], 'Y', 10)
    for s in (1, -1):
        roda('roda_d', fa, s * 0.88, r, 0.2, M)
        roda('roda_t', ra, s * 0.9, r, 0.2, M, dual=True)
    # salão em três faixas: painel inferior vermelho, faixa das janelas creme, teto prateado abaulado
    def faixa(nome, z0, z1, m, x0=L0, x1=L1, w=W, bev=0.04):
        prof = [(-w / 2, z0), (w / 2, z0), (w / 2, z1), (-w / 2, z1)]
        return prism(nome, prof, x1 - x0, (x0 + x1) / 2, m, 'YZ', bev, 2)
    faixa('painel_inferior', 0.78, 1.52, red)
    faixa('faixa_janelas', 1.52, 2.5, cream)
    faixa('faixa_superior', 2.5, 2.62, red)
    arco = [(-W / 2, 2.62), (W / 2, 2.62)] + [((W / 2) * math.cos(math.radians(a)), 2.62 + 0.26 * math.sin(math.radians(a))) for a in range(15, 166, 15)]
    prism('teto', arco, L1 - L0, (L0 + L1) / 2, roofm, 'YZ', 0.03)
    # traseira arredondada (meia-cápsula vertical)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=W / 2, radius2=W / 2, depth=1.84)
    for v in bm.verts:
        v.co = Vector((L0 + min(v.co.x, 0) * 0.32, v.co.y, v.co.z + 0.78 + 0.92))
    finish(new_obj('traseira', bm), red, smooth=True)
    box('vidro_traseiro', 0.02, 1.2, 0.5, L0 - 0.31, 0, 2.05, M['glass'])
    # janelas com colunas
    n = 7
    span = (L1 - 0.2) - (L0 + 0.3)
    for s in (1, -1):
        for i in range(n):
            xc = L0 + 0.3 + span * (i + 0.5) / n
            w = span / n - 0.1
            box('janela', w, 0.02, 0.62, xc, s * (W / 2 + 0.012), 2.0, M['glass'])
            box('ventilacao', w, 0.022, 0.13, xc, s * (W / 2 + 0.014), 2.4, M['glass'])
        box('friso_cintura', L1 - L0, 0.03, 0.05, (L0 + L1) / 2, s * (W / 2 + 0.01), 1.53, M['black'])
        box('friso_baixo', L1 - L0, 0.03, 0.04, (L0 + L1) / 2, s * (W / 2 + 0.01), 0.82, M['black'])
    # porta de entrada (lado da calçada, +Y) logo atrás do anteparo
    box('porta', 0.72, 0.03, 1.55, L1 - 0.45, W / 2 + 0.02, 1.6, M['glass'])
    box('degrau', 0.72, 0.3, 0.06, L1 - 0.45, W / 2 - 0.05, 0.62, M['black'])
    # meia-cabine do motorista (lado direito, -Y)
    cw = 0.95
    box('cabine_motorista', cx1 - L1, cw, 1.1, (cx1 + L1) / 2, -(W / 2 - cw / 2), 1.33, red, 0.03)
    box('cabine_janelas', cx1 - L1, cw, 0.78, (cx1 + L1) / 2, -(W / 2 - cw / 2), 2.27, cream, 0.03)
    box('parabrisa_motorista', 0.02, cw - 0.12, 0.6, cx1 + 0.005, -(W / 2 - cw / 2), 2.2, M['glass'])
    box('janela_motorista', cx1 - L1 - 0.2, 0.02, 0.55, (cx1 + L1) / 2, -(W / 2 + 0.005), 2.2, M['glass'])
    # teto da cabine continua o do salão e avança como pala sobre o capô
    prism('teto_cabine', arco, cx1 - L1 + 0.05, (cx1 + L1) / 2, roofm, 'YZ', 0.03)
    box('faixa_sup_cabine', cx1 - L1 + 0.05, W, 0.12, (cx1 + L1) / 2, 0, 2.62, red, 0.02)
    box('destino_caixa', 0.1, 1.0, 0.2, cx1 - 0.02, 0.5, 2.45, M['black'], 0.01)
    box('destino', 0.02, 0.9, 0.13, cx1 + 0.035, 0.5, 2.45, M['cream'])
    box('anteparo_vidro', 0.02, 1.0, 0.6, L1 + 0.01, 0.55, 2.15, M['glass'])
    # capô central (à esquerda da cabine) e radiador
    hood = [(-0.36, 0.95), (0.36, 0.95), (0.36, 1.42)] + [(0.36 * math.cos(math.radians(a)), 1.42 + 0.16 * math.sin(math.radians(a))) for a in range(15, 166, 15)] + [(-0.36, 1.42)]
    prism('capo', hood, rx - 0.05 - L1, (rx - 0.05 + L1) / 2, red, 'YZ', 0.02)
    box('radiador_moldura', 0.1, 0.68, 0.82, rx, 0, 1.24, M['chrome'], 0.035, 3)
    box('radiador_colmeia', 0.04, 0.56, 0.68, rx + 0.04, 0, 1.23, M['black'])
    for i in range(13):
        box('grade', 0.03, 0.012, 0.64, rx + 0.065, -0.26 + i * 0.52 / 12, 1.23, M['chrome'])
    sphere('emblema', 0.04, rx + 0.07, 0, 1.54, M['gold'], 0.5, 1, 1)
    # para-lamas dianteiros curvos só em volta das rodas
    for s in (1, -1):
        path = [(fa + r + 0.32, 0.72)] + arc(fa, r, r + 0.1, 20, 165, 18)[1:] + [(fa - r - 0.2, 0.74)]
        asa('paralama_d', path, 0.4, s * 0.88, M['black'], crown=0.05, skirt=0.07)
        farol(f'farol{s}', rx - 0.12, s * 0.6, 1.32, M, 0.12)
        arco_roda = [(ra + r + 0.12, 0.78)] + arc(ra, 0.78, r + 0.12, 0, 180, 18)[1:-1] + [(ra - r - 0.12, 0.78)]
        prism('caixa_roda', arco_roda, 0.02, s * (W / 2 + 0.006), M['chassis'], 'XZ')
    box('barra_farois', 0.04, 1.1, 0.04, rx - 0.1, 0, 1.1, M['black'])
    box('para_choque', 0.08, 2.0, 0.1, rx + 0.2, 0, 0.68, M['black'], 0.02)
    lanternas_traseiras(M, L0 - 0.33)

# ---------------- catálogo ----------------
COMPANY = '#7a1f1f'  # cor da empresa (vermelho escuro) — pode ser trocada no jogo
VEICULOS = [
    ('mps_regal_bus', 'MPS Regal Bus', lambda M: onibus_regal(M)),
    ('balogh_coal_truck', 'Balogh Coal Truck', lambda M: (caminhao_1930(M), cacamba(M, 0.6, 'coal'), para_lamas_traseiros(M), lanternas_traseiras(M, BB - 0.05))),
    ('mps_mail_truck', 'MPS Mail Truck', lambda M: (caminhao_1930(M, 'gpo'), correio(M), para_lamas_traseiros(M), lanternas_traseiras(M, BB - 0.05))),
    ('witcombe_oil_tanker', 'Witcombe Oil Tanker', lambda M: (caminhao_1930(M), tanque(M), para_lamas_traseiros(M), lanternas_traseiras(M, BB - 0.05))),
    ('talbott_livestock_van', 'Talbott Livestock Van', lambda M: (caminhao_1930(M), boiadeiro(M), para_lamas_traseiros(M), lanternas_traseiras(M, BB - 0.05))),
    ('balogh_goods_truck', 'Balogh Goods Truck', lambda M: (caminhao_1930(M), bau(M, 1.5, 'cream', lona=True), para_lamas_traseiros(M), lanternas_traseiras(M, BB - 0.05))),
    ('hereford_grain_truck', 'Hereford Grain Truck', lambda M: (caminhao_1930(M), cacamba(M, 0.7, 'grain', 'wood'), para_lamas_traseiros(M), lanternas_traseiras(M, BB - 0.05))),
    ('witcombe_wood_truck', 'Witcombe Wood Truck', lambda M: (caminhao_1930(M), toras(M), para_lamas_traseiros(M), lanternas_traseiras(M, BB - 0.05))),
    ('mps_iron_ore_truck', 'MPS Iron Ore Truck', lambda M: (caminhao_1930(M), cacamba(M, 0.6, 'ore'), para_lamas_traseiros(M), lanternas_traseiras(M, BB - 0.05))),
    ('balogh_steel_truck', 'Balogh Steel Truck', lambda M: (caminhao_1930(M), aco(M), para_lamas_traseiros(M), lanternas_traseiras(M, BB - 0.05))),
    ('balogh_armoured_truck', 'Balogh Armoured Truck', lambda M: (caminhao_1930(M), bau(M, 1.55, 'grey', ripas=True, janelas=True), para_lamas_traseiros(M), lanternas_traseiras(M, BB - 0.05))),
]

def exportar(slug, build):
    reset()
    MATS.clear()
    M = materiais(COMPANY)
    build(M)
    for ob in bpy.context.collection.objects:
        ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, slug + '.glb'), use_selection=True, export_apply=True, export_format='GLB')
    print('OK', slug, len(bpy.context.collection.objects), 'peças')


if __name__ == '__main__':
  only = os.environ.get('ONLY')
  for slug, nome, build in VEICULOS:
    if only and slug != only:
        continue
    exportar(slug, build)
