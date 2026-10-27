# Renderiza veículos (GLB) como sprites do OpenTTD: projeção dimétrica 2:1 (câmera ortográfica a 30° de elevação),
# 8 direções, zoom 4x (tile = 256 px de largura). Saída: PNG RGBA por direção.
import bpy, math, os, sys
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
GLB, OUTDIR = args[0], args[1]
os.makedirs(OUTDIR, exist_ok=True)

TILE_M = 12.0            # metros por tile (vê o veículo com ~meio tile, como no TTD)
TILE_PX = 256            # largura do tile em pixels no zoom 4x
W, H = 200, 160          # tela do sprite (4x)
PPM = TILE_PX / (TILE_M * math.sqrt(2))   # pixels por metro na horizontal da tela

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 64
sc.cycles.use_denoising = True
sc.render.film_transparent = True
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'Standard'

bpy.ops.import_scene.gltf(filepath=GLB)

# Pintura da empresa: vira cinza neutro (o jogo troca pela cor de cada companhia usando a máscara;
# do render só aproveita o brilho). Guardamos quais materiais são pintura.
NOMES_PINTURA = ('Pintura empresa', 'Vermelho London General', 'Vermelho GPO')
PINTURA = [m for m in bpy.data.materials if m.name.startswith(NOMES_PINTURA)]
for m in PINTURA:
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.30, 0.30, 0.30, 1)
veic = bpy.data.objects.new('veiculo', None)
sc.collection.objects.link(veic)
for o in list(sc.objects):
    if o is not veic and o.parent is None and o.type in ('MESH', 'EMPTY'):
        o.parent = veic

# câmera ortográfica: olha na direção (+1,+1) horizontal, 30° abaixo do horizonte
cam_data = bpy.data.cameras.new('cam')
cam_data.type = 'ORTHO'
cam_data.ortho_scale = W / PPM
cam = bpy.data.objects.new('cam', cam_data)
sc.collection.objects.link(cam)
elev = math.radians(30)
d = 60
dirh = Vector((1, 1, 0)).normalized()
cam.location = Vector((0, 0, 0)) - dirh * d * math.cos(elev) + Vector((0, 0, d * math.sin(elev)))
cam.rotation_euler = (math.radians(60), 0, math.radians(-45))
sc.camera = cam

# luz: sol vindo do alto à esquerda da tela (como nos gráficos do TTD) + céu suave
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

# sombra suave no chão (só a sombra, chão invisível)
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
chao = bpy.context.active_object
chao.is_shadow_catcher = True

# direções do OpenTTD na ordem dos sprites: N, NE, E, SE, S, SW, W, NW
# Na tela: NE = acima-direita (= +X do mundo), NW = acima-esquerda (= +Y).
yaw = {'N': 45, 'NE': 0, 'E': -45, 'SE': -90, 'S': -135, 'SW': 180, 'W': 135, 'NW': 90}
DIRS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
for i, k in enumerate(DIRS):
    veic.rotation_euler = (0, 0, math.radians(yaw[k]))
    sc.render.filepath = os.path.join(OUTDIR, f'{i}_{k}.png')
    bpy.ops.render.render(write_still=True)
    print('render', k)

# ---- passe da máscara: pintura em branco, resto em preto, sem sombra nem luz ----
def emissao(nome, cor):
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*cor, 1); em.inputs['Strength'].default_value = 1
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
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
for i, k in enumerate(DIRS):
    veic.rotation_euler = (0, 0, math.radians(yaw[k]))
    sc.render.filepath = os.path.join(OUTDIR, f'm{i}_{k}.png')
    bpy.ops.render.render(write_still=True)
    print('mascara', k)
