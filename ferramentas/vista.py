# Vista grande de conferência de um modelo GLB (3/4 na projeção do jogo + lateral), para revisão visual.
# Uso: python3 vista.py -- modelo.glb saida.png
import bpy, math, sys
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
GLB, OUT = args[0], args[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 24
sc.cycles.use_denoising = True
sc.render.film_transparent = False
sc.view_settings.view_transform = 'Standard'
bpy.ops.import_scene.gltf(filepath=GLB)
objs = [o for o in sc.objects if o.type == 'MESH']
mn = Vector((min(min((o.matrix_world @ Vector(c)).x for c in o.bound_box) for o in objs), 0, 0))
xs = [(o.matrix_world @ Vector(c)) for o in objs for c in o.bound_box]
L = max(v.x for v in xs) - min(v.x for v in xs)
H = max(v.z for v in xs)
sun = bpy.data.objects.new('sol', bpy.data.lights.new('sol', 'SUN'))
sun.data.energy = 3.2
sun.rotation_euler = (math.radians(40), 0, math.radians(-160))
sc.collection.objects.link(sun)
w = bpy.data.worlds.new('m'); w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.62, 0.5, 1)
w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
sc.world = w
bpy.ops.mesh.primitive_plane_add(size=80)
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 1400, 520
import os
base, ext = os.path.splitext(OUT)
# 3/4 (ângulo do jogo, de frente-esquerda)
d = 60
dirh = Vector((1, 1, 0)).normalized()
for nome, loc, rot, esc in [
    ('34', -dirh * d * math.cos(math.radians(30)) + Vector((0, 0, d * math.sin(math.radians(30)))), (math.radians(60), 0, math.radians(-45)), L * 0.78 + 1),
    ('lado', Vector((0, -d, H / 2)), (math.radians(90), 0, 0), L * 1.04 + 0.5),
]:
    cam.location = loc
    cam.rotation_euler = rot
    cd.ortho_scale = esc
    if nome == '34':
        for o in objs:
            pass
        # gira o veículo para a frente apontar para baixo-direita da tela (como o SE do jogo)
    sc.render.filepath = f'{base}_{nome}{ext}'
    bpy.ops.render.render(write_still=True)
