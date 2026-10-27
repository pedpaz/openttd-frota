# Renderiza um veículo ferroviário (GLB) como sprites do OpenTTD, dividido em partes articuladas.
# Cada parte tem um comprimento em unidades do jogo (8 = meio tile = 6 m nesta escala). O modelo inteiro
# fica na cena, mas cada render mostra só o trecho da parte (corte no shader), centrado na parte, para
# que as partes encaixem no jogo. Mesma câmera, luz e passe de máscara de cor da empresa dos rodoviários.
# Uso: python3 renderizar_trem.py -- modelo.glb pasta_saida 8,8,8,2
import bpy, math, os, sys
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
GLB, OUTDIR = args[0], args[1]
PARTES = [int(v) for v in args[2].split(',')]
UNID = 0.75                      # metros por unidade de comprimento (tile de 12 m = 16 unidades)
L = sum(PARTES) * UNID

TILE_M = 12.0
TILE_PX = 256
W, H = 240, 200
PPM = TILE_PX / (TILE_M * math.sqrt(2))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 64
sc.cycles.use_denoising = True
sc.cycles.transparent_max_bounces = 16
sc.render.film_transparent = True
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'Standard'

bpy.ops.import_scene.gltf(filepath=GLB)
NOMES_PINTURA = ('Pintura empresa',)
PINTURA = [m for m in bpy.data.materials if m.name.startswith(NOMES_PINTURA)]
for m in PINTURA:
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.30, 0.30, 0.30, 1)

pivo = bpy.data.objects.new('pivo', None)
raiz = bpy.data.objects.new('raiz', None)
sc.collection.objects.link(pivo)
sc.collection.objects.link(raiz)
raiz.parent = pivo
for o in list(sc.objects):
    if o not in (pivo, raiz) and o.parent is None and o.type in ('MESH', 'EMPTY'):
        o.parent = raiz

# ---- corte por trecho: em cada material, fora de [lo, hi] (x do modelo) vira transparente ----
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
    gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'
    lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'
    nt.links.new(sep.outputs['X'], gt.inputs[0])
    nt.links.new(sep.outputs['X'], lt.inputs[0])
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    nt.links.new(gt.outputs[0], mul.inputs[0])
    nt.links.new(lt.outputs[0], mul.inputs[1])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(mul.outputs[0], mix.inputs['Fac'])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(src, mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    CORTES.append((gt, lt))


for m in list(bpy.data.materials):
    if m.use_nodes:
        cortar(m)

cam_data = bpy.data.cameras.new('cam')
cam_data.type = 'ORTHO'
cam_data.ortho_scale = W / PPM
cam = bpy.data.objects.new('cam', cam_data)
sc.collection.objects.link(cam)
elev = math.radians(30)
d = 60
dirh = Vector((1, 1, 0)).normalized()
cam.location = -dirh * d * math.cos(elev) + Vector((0, 0, d * math.sin(elev)))
cam.rotation_euler = (math.radians(60), 0, math.radians(-45))
sc.camera = cam

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
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
chao = bpy.context.active_object
chao.is_shadow_catcher = True

yaw = {'N': 45, 'NE': 0, 'E': -45, 'SE': -90, 'S': -135, 'SW': 180, 'W': 135, 'NW': 90}
DIRS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']

# trechos de cada parte, da frente (x = +L/2) para trás
trechos = []
x = L / 2
for n in PARTES:
    hi, lo = x, x - n * UNID
    trechos.append((hi, lo))
    x = lo


def passe(prefixo):
    for p, (hi, lo) in enumerate(trechos):
        # a primeira e a última parte não cortam as pontas (para-choques que passam do comprimento)
        h = hi if p > 0 else 1e3
        l = lo if p < len(trechos) - 1 else -1e3
        for gt, lt in CORTES:
            gt.inputs[1].default_value = l
            lt.inputs[1].default_value = h
        raiz.location = (-(hi + lo) / 2, 0, 0)
        pasta = os.path.join(OUTDIR, f'p{p}')
        os.makedirs(pasta, exist_ok=True)
        for i, k in enumerate(DIRS):
            pivo.rotation_euler = (0, 0, math.radians(yaw[k]))
            sc.render.filepath = os.path.join(pasta, f'{prefixo}{i}_{k}.png')
            bpy.ops.render.render(write_still=True)
        print(prefixo or 'cor', 'parte', p, 'ok')


passe('')


# ---- máscara de cor da empresa ----
def emissao(nome, cor):
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*cor, 1); em.inputs['Strength'].default_value = 1
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    cortar(m)
    return m


branco, preto = emissao('mask_branco', (1, 1, 1)), emissao('mask_preto', (0, 0, 0))
for o in sc.objects:
    if o.type != 'MESH' or o is chao:
        continue
    for slot in o.material_slots:
        slot.material = branco if slot.material in PINTURA else preto
chao.hide_render = True
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0
sc.cycles.samples = 8
sc.cycles.use_denoising = False
passe('m')
