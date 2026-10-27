# Renderiza construções/objetos (GLB, canto norte do tile na origem) como sprites 4x do OpenTTD, alinhados ao tile.
# Para cada sprite pedido: posiciona a câmera no canto norte do tile da peça, corta o modelo no shader à área
# dos tiles da peça e grava PNG + máscara vazia. A posição de referência (subtile) define o offset do sprite.
# Uso: python3 renderizar_objeto.py -- modelo.glb pasta_saida JSON
#   JSON = lista de {"nome", "tile": [tx, ty], "ref": [sx, sy], "clip": [ox0, ox1, oy0, oy1] | null,
#                    "chao": bool (sprite de chão 256x127, só objetos 'campo*', sem sombra)}
#   Coordenadas em unidades do OpenTTD (16 por tile) a partir do canto norte do objeto.
import bpy, math, os, sys, json
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
GLB, OUTDIR, SPEC = args[0], args[1], json.loads(args[2])
os.makedirs(OUTDIR, exist_ok=True)
U = 0.75
TILE_PX = 256
PPM = TILE_PX / (16 * U * math.sqrt(2))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 64
sc.cycles.use_denoising = True
sc.cycles.transparent_max_bounces = 16
sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'
bpy.ops.import_scene.gltf(filepath=GLB)
raiz = bpy.data.objects.new('raiz', None)
sc.collection.objects.link(raiz)
modelo = [o for o in sc.objects if o.type == 'MESH']
for o in sc.objects:
    if o is not raiz and o.parent is None:
        o.parent = raiz

CORTES = []


def cortar(m):
    nt = m.node_tree
    out = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if out is None or not out.inputs['Surface'].links:
        return
    src = out.inputs['Surface'].links[0].from_socket
    tc = nt.nodes.new('ShaderNodeTexCoord'); tc.object = raiz
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    nos = []
    fac = None
    for eixo in ('X', 'Y'):
        gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'
        lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'
        nt.links.new(sep.outputs[eixo], gt.inputs[0]); nt.links.new(sep.outputs[eixo], lt.inputs[0])
        mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
        nt.links.new(gt.outputs[0], mul.inputs[0]); nt.links.new(lt.outputs[0], mul.inputs[1])
        if fac is None:
            fac = mul
        else:
            m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'
            nt.links.new(fac.outputs[0], m2.inputs[0]); nt.links.new(mul.outputs[0], m2.inputs[1]); fac = m2
        nos.append((gt, lt))
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(fac.outputs[0], mix.inputs['Fac'])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(src, mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    CORTES.append(nos)


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import texturas
SEM_TEXTURA = os.environ.get('SEM_TEXTURA')
for m in list(bpy.data.materials):
    if m.use_nodes:
        if not SEM_TEXTURA:
            texturas.aplicar(m)
        cortar(m)

cam_data = bpy.data.cameras.new('cam')
cam_data.type = 'ORTHO'
cam = bpy.data.objects.new('cam', cam_data)
sc.collection.objects.link(cam)
sc.camera = cam
elev = math.radians(30)
dirh = Vector((1, 1, 0)).normalized()

sun = bpy.data.objects.new('sol', bpy.data.lights.new('sol', 'SUN'))
sun.data.energy = 3.2
sun.data.angle = math.radians(8)
sun.rotation_euler = (math.radians(40), 0, math.radians(-160))
sc.collection.objects.link(sun)
world = bpy.data.worlds.new('mundo')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.75, 0.82, 0.9, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
sc.world = world
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
chao = bpy.context.active_object
chao.is_shadow_catcher = True


def blender(ox, oy, z=0.0):
    return Vector((-ox * U, -oy * U, z))


def render(spec, prefixo=''):
    tx, ty = spec['tile']
    canto = blender(tx * 16, ty * 16)            # canto norte do tile desta peça
    if spec.get('chao'):
        W, H, Cx, Cy = 256, 191, 128, 64
    else:
        topo = spec.get('topo', 192)
        W, H, Cx, Cy = 296, topo + 148, 148, topo
    sc.render.resolution_x, sc.render.resolution_y = W, H
    cam_data.ortho_scale = max(W, H) / PPM
    d = 80
    cam.location = canto - dirh * d * math.cos(elev) + Vector((0, 0, d * math.sin(elev)))
    cam.rotation_euler = (math.radians(60), 0, math.radians(-45))
    S = max(W, H)
    cam_data.shift_x = (W / 2 - Cx) / S
    cam_data.shift_y = (Cy - H / 2) / S
    clip = spec.get('clip')
    if clip:
        ox0, ox1, oy0, oy1 = clip
        xs = sorted([-ox0 * U, -ox1 * U]); ys = sorted([-oy0 * U, -oy1 * U])
    else:
        xs, ys = [-1e3, 1e3], [-1e3, 1e3]
    for (gx, lx), (gy, ly) in CORTES:
        gx.inputs[1].default_value, lx.inputs[1].default_value = xs[0] - 1e-3, xs[1] + 1e-3
        gy.inputs[1].default_value, ly.inputs[1].default_value = ys[0] - 1e-3, ys[1] + 1e-3
    # sombra só dentro da área da peça
    cx = (xs[0] + xs[1]) / 2 if clip else canto.x - 6; cy = (ys[0] + ys[1]) / 2 if clip else canto.y - 6
    chao.location = (cx, cy, 0)
    chao.scale = ((xs[1] - xs[0]) if clip else 12, (ys[1] - ys[0]) if clip else 12, 1)
    so_campo = bool(spec.get('chao'))
    for o in modelo:
        o.hide_render = so_campo != o.name.startswith(('campo', 'chao'))
        if clip and not o.hide_render:
            cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
            fora = max(v.x for v in cs) < xs[0] or min(v.x for v in cs) > xs[1] or max(v.y for v in cs) < ys[0] or min(v.y for v in cs) > ys[1]
            o.hide_render = fora
    chao.hide_render = so_campo or prefixo == 'm'
    sc.render.filepath = os.path.join(OUTDIR, f"{prefixo}{spec['nome']}.png")
    bpy.ops.render.render(write_still=True)
    # offsets do sprite (4x): referência = ponto do subtile no chão; origem de desenho = geométrico - (4, 0)
    sx, sy = spec.get('ref', [tx * 16, ty * 16])
    rx = Cx + 8 * ((sy - ty * 16) - (sx - tx * 16))
    ry = Cy + 4 * ((sx - tx * 16) + (sy - ty * 16))
    return {'nome': spec['nome'], 'w': W, 'h': H, 'xofs': -(rx - 4), 'yofs': -ry}


meta = [render(s) for s in SPEC]
json.dump(meta, open(os.path.join(OUTDIR, 'offsets.json'), 'w'), indent=1)
print('ok', len(meta))
