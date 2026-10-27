# Texturas procedurais aplicadas na hora do render, pelo nome do material (o GLB só guarda cor lisa).
# Escala pensada para o zoom 4x do OpenTTD (~15 px por metro): tijolos e telhas exagerados o suficiente para
# aparecerem, variação de cor, sujeira perto do chão e relevo (bump).
import bpy


def _rgb(base, f):
    return (min(1, base[0] * f), min(1, base[1] * f), min(1, base[2] * f), 1)


class N:
    """Atalho para montar nós num material."""

    def __init__(self, m):
        self.nt = m.node_tree
        self.b = next((n for n in self.nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)

    def no(self, tipo, **kw):
        n = self.nt.nodes.new(tipo)
        for k, v in kw.items():
            if k.startswith('i_'):
                n.inputs[k[2:].replace('_', ' ')].default_value = v
            else:
                setattr(n, k, v)
        return n

    def ln(self, a, b):
        self.nt.links.new(a, b)

    @staticmethod
    def sock(lista, nome, tipo):
        return next(s for s in lista if s.name == nome and s.type == tipo)

    def coords_parede(self, escala=1.0):
        """Vetor (u, v) para paredes: u = x + y (ao longo da parede, nos dois sentidos), v = z."""
        tc = self.no('ShaderNodeTexCoord')
        sep = self.no('ShaderNodeSeparateXYZ')
        self.ln(tc.outputs['Object'], sep.inputs[0])
        add = self.no('ShaderNodeMath', operation='ADD')
        self.ln(sep.outputs['X'], add.inputs[0]); self.ln(sep.outputs['Y'], add.inputs[1])
        comb = self.no('ShaderNodeCombineXYZ')
        self.ln(add.outputs[0], comb.inputs['X']); self.ln(sep.outputs['Z'], comb.inputs['Y'])
        sc = self.no('ShaderNodeVectorMath', operation='SCALE', i_Scale=escala)
        self.ln(comb.outputs[0], sc.inputs[0])
        return sc.outputs[0], sep.outputs['Z']

    def coords(self):
        tc = self.no('ShaderNodeTexCoord')
        return tc.outputs['Object']

    def ruido(self, vetor, escala, detalhe=4.0):
        n = self.no('ShaderNodeTexNoise', i_Scale=escala, i_Detail=detalhe)
        self.ln(vetor, n.inputs['Vector'])
        return n.outputs['Fac']

    def variar(self, cor, fator, a=0.82, b=1.15):
        """Multiplica a cor por um valor entre a e b conforme o fator (0..1)."""
        mr = self.no('ShaderNodeMapRange', i_To_Min=a, i_To_Max=b)
        self.ln(fator, mr.inputs['Value'])
        mix = self.no('ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY', i_Factor=1.0)
        self.ln(cor, self.sock(mix.inputs, 'A', 'RGBA'))
        comb = self.no('ShaderNodeCombineColor')
        for k in ('Red', 'Green', 'Blue'):
            self.ln(mr.outputs[0], comb.inputs[k])
        self.ln(comb.outputs[0], self.sock(mix.inputs, 'B', 'RGBA'))
        return self.sock(mix.outputs, 'Result', 'RGBA')

    def sujeira_base(self, cor, z, altura=1.6, forca=0.35):
        """Escurece perto do chão (respingo de terra), sumindo até 'altura' metros."""
        mr = self.no('ShaderNodeMapRange', i_From_Min=0.0, i_From_Max=altura, i_To_Min=1.0 - forca, i_To_Max=1.0)
        self.ln(z, mr.inputs['Value'])
        mix = self.no('ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY', i_Factor=1.0)
        self.ln(cor, self.sock(mix.inputs, 'A', 'RGBA'))
        comb = self.no('ShaderNodeCombineColor')
        for k in ('Red', 'Green', 'Blue'):
            self.ln(mr.outputs[0], comb.inputs[k])
        self.ln(comb.outputs[0], self.sock(mix.inputs, 'B', 'RGBA'))
        return self.sock(mix.outputs, 'Result', 'RGBA')

    def relevo(self, altura, forca=0.25, dist=0.05):
        bump = self.no('ShaderNodeBump', i_Strength=forca, i_Distance=dist)
        self.ln(altura, bump.inputs['Height'])
        self.ln(bump.outputs['Normal'], self.b.inputs['Normal'])

    def cor(self, saida):
        self.ln(saida, self.b.inputs['Base Color'])


def tijolo(m, base, argamassa=None, larg=0.46, alt=0.2):
    t = N(m)
    uv, z = t.coords_parede()
    br = t.no('ShaderNodeTexBrick', i_Scale=1.0, i_Mortar_Size=0.025, i_Brick_Width=larg, i_Row_Height=alt,
              offset=0.5, squash=1.0)
    br.inputs['Color1'].default_value = _rgb(base, 1.15)
    br.inputs['Color2'].default_value = _rgb(base, 0.82)
    br.inputs['Mortar'].default_value = argamassa or (base[0] * 0.5 + 0.02, base[1] * 0.55 + 0.02, base[2] * 0.6 + 0.02, 1)
    t.ln(uv, br.inputs['Vector'])
    c = t.variar(br.outputs['Color'], t.ruido(t.coords(), 1.6), 0.85, 1.12)
    c = t.sujeira_base(c, z)
    t.cor(c)
    t.relevo(br.outputs['Fac'], 0.35, 0.03)


def ardosia(m, base):
    t = N(m)
    tc = t.coords()
    sep = t.no('ShaderNodeSeparateXYZ'); t.ln(tc, sep.inputs[0])
    add = t.no('ShaderNodeMath', operation='ADD'); t.ln(sep.outputs['X'], add.inputs[0]); t.ln(sep.outputs['Y'], add.inputs[1])
    comb = t.no('ShaderNodeCombineXYZ'); t.ln(add.outputs[0], comb.inputs['X']); t.ln(sep.outputs['Z'], comb.inputs['Y'])
    br = t.no('ShaderNodeTexBrick', i_Scale=1.0, i_Mortar_Size=0.02, i_Brick_Width=0.45, i_Row_Height=0.22, offset=0.5)
    br.inputs['Color1'].default_value = _rgb(base, 1.12)
    br.inputs['Color2'].default_value = _rgb(base, 0.88)
    br.inputs['Mortar'].default_value = _rgb(base, 0.55)
    t.ln(comb.outputs[0], br.inputs['Vector'])
    c = t.variar(br.outputs['Color'], t.ruido(tc, 2.5), 0.85, 1.15)
    t.cor(c)
    t.relevo(br.outputs['Fac'], 0.3, 0.03)


def ondulado(m, base):
    t = N(m)
    uv, z = t.coords_parede()
    w = t.no('ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', i_Scale=1.0)
    w.inputs['Scale'].default_value = 3.2
    t.ln(uv, w.inputs['Vector'])
    ferrugem = t.ruido(t.coords(), 1.2, 6)
    c = t.variar(_socket_cor(t, base), ferrugem, 0.78, 1.12)
    t.cor(c)
    t.relevo(w.outputs['Fac'], 0.45, 0.04)


def _socket_cor(t, base):
    rgb = t.no('ShaderNodeRGB')
    rgb.outputs[0].default_value = base
    return rgb.outputs[0]


def concreto(m, base, manchas=True):
    t = N(m)
    tc = t.coords()
    c = t.variar(_socket_cor(t, base), t.ruido(tc, 3.0, 8), 0.86, 1.08)
    if manchas:
        sep = t.no('ShaderNodeSeparateXYZ'); t.ln(tc, sep.inputs[0])
        w = t.no('ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', i_Scale=1.6, i_Distortion=6.0)
        t.ln(tc, w.inputs['Vector'])
        c = t.variar(c, w.outputs['Fac'], 0.9, 1.04)
        c = t.sujeira_base(c, sep.outputs['Z'], 2.5, 0.25)
    t.cor(c)
    t.relevo(t.ruido(tc, 12.0, 3), 0.12, 0.02)


def terra(m, base, pedras=True):
    t = N(m)
    tc = t.coords()
    c = t.variar(_socket_cor(t, base), t.ruido(tc, 0.7, 8), 0.65, 1.25)
    if pedras:
        v = t.no('ShaderNodeTexVoronoi', i_Scale=4.5)
        t.ln(tc, v.inputs['Vector'])
        c = t.variar(c, v.outputs['Distance'], 0.85, 1.12)
        t.relevo(v.outputs['Distance'], 0.3, 0.05)
    t.cor(c)


def carvao(m, base):
    t = N(m)
    tc = t.coords()
    v = t.no('ShaderNodeTexVoronoi', i_Scale=5.0)
    t.ln(tc, v.inputs['Vector'])
    c = t.variar(_socket_cor(t, base), v.outputs['Distance'], 0.75, 1.25)
    t.cor(c)
    t.relevo(v.outputs['Distance'], 0.8, 0.12)
    t.b.inputs['Roughness'].default_value = 0.85
    t.b.inputs['Specular IOR Level'].default_value = 0.2


def folhagem(m, base):
    t = N(m)
    tc = t.coords()
    v = t.no('ShaderNodeTexVoronoi', i_Scale=6.0)
    t.ln(tc, v.inputs['Vector'])
    c = t.variar(_socket_cor(t, base), v.outputs['Distance'], 0.6, 1.3)
    c = t.variar(c, t.ruido(tc, 1.5), 0.85, 1.15)
    t.cor(c)
    t.relevo(v.outputs['Distance'], 0.9, 0.25)


def grama(m, base):
    t = N(m)
    tc = t.coords()
    c = t.variar(_socket_cor(t, base), t.ruido(tc, 2.0, 8), 0.85, 1.12)
    c = t.variar(c, t.ruido(tc, 18.0, 2), 0.9, 1.08)
    t.cor(c)
    t.relevo(t.ruido(tc, 25.0, 2), 0.2, 0.02)


def madeira(m, base):
    t = N(m)
    tc = t.coords()
    w = t.no('ShaderNodeTexWave', wave_type='BANDS', bands_direction='Z', i_Scale=4.0, i_Distortion=2.0)
    t.ln(tc, w.inputs['Vector'])
    c = t.variar(_socket_cor(t, base), w.outputs['Fac'], 0.82, 1.1)
    t.cor(c)
    t.relevo(w.outputs['Fac'], 0.15, 0.02)


def pedra(m, base):
    t = N(m)
    uv, z = t.coords_parede()
    br = t.no('ShaderNodeTexBrick', i_Scale=1.0, i_Mortar_Size=0.02, i_Brick_Width=0.9, i_Row_Height=0.45, offset=0.5)
    br.inputs['Color1'].default_value = _rgb(base, 1.05)
    br.inputs['Color2'].default_value = _rgb(base, 0.92)
    br.inputs['Mortar'].default_value = _rgb(base, 0.7)
    t.ln(uv, br.inputs['Vector'])
    c = t.variar(br.outputs['Color'], t.ruido(t.coords(), 3.0), 0.9, 1.08)
    t.cor(c)
    t.relevo(br.outputs['Fac'], 0.2, 0.02)


def aco(m, base):
    t = N(m)
    tc = t.coords()
    c = t.variar(_socket_cor(t, base), t.ruido(tc, 2.0, 6), 0.8, 1.1)
    t.cor(c)


# nome do material (prefixo) -> função
REGRAS = [
    ('Tijolo', tijolo), ('Telhado ardósia', ardosia), ('Zinco ondulado', ondulado), ('Telhado verde', ardosia),
    ('Concreto sujo', concreto), ('Concreto', concreto), ('Terra', terra), ('Carvão', carvao),
    ('Folhagem', folhagem), ('Grama', grama), ('Campo', grama), ('Madeira', madeira),
    ('Pedra', pedra), ('Granito', pedra), ('Cascalho', terra), ('Aço pintado', aco), ('Aço claro', aco),
    ('Minério', carvao),
]


def aplicar(m):
    if not m.use_nodes:
        return False
    b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if b is None or b.inputs['Base Color'].links:
        return False
    for prefixo, f in REGRAS:
        if m.name.startswith(prefixo):
            base = tuple(b.inputs['Base Color'].default_value)
            f(m, base)
            return True
    return False
