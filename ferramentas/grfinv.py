# Inventário de um GRF container v2: para cada sprite real (na ordem), quais zooms/profundidades existem.
# Uso: python3 grfinv.py arquivo.grf > saida.tsv   (colunas: indice_real  zooms)
import struct, sys

ZOOM = {0: '1x', 1: '4x', 2: '2x', 3: 'out2', 4: 'out4', 5: 'out8'}


def ler(path):
    f = open(path, 'rb')
    magic = f.read(10)
    assert magic == b'\x00\x00GRF\x82\r\n\x1a\n', magic
    off_sprites = struct.unpack('<I', f.read(4))[0]
    base = f.tell()
    f.read(1)  # compressão
    # seção de dados: ordem dos sprites
    ordem = []   # ('pseudo', size) ou ('real', id)
    while True:
        size = struct.unpack('<I', f.read(4))[0]
        if size == 0:
            break
        tipo = f.read(1)[0]
        if tipo == 0xFF:
            dados = f.read(size)
            ordem.append(('pseudo', dados))
        elif tipo == 0xFD:
            sid = struct.unpack('<I', f.read(4))[0]
            ordem.append(('real', sid))
        else:
            f.read(size)
            ordem.append(('outro', tipo))
    # seção de sprites
    f.seek(base + off_sprites)
    info = {}
    while True:
        b = f.read(4)
        if len(b) < 4:
            break
        sid = struct.unpack('<I', b)[0]
        if sid == 0:
            break
        size = struct.unpack('<I', f.read(4))[0]
        tipo = f.read(1)[0]
        zoom = f.read(1)[0]
        f.seek(size - 2, 1)
        prof = '32' if tipo & 0x03 else '8'
        info.setdefault(sid, set()).add(ZOOM.get(zoom, str(zoom)) + '/' + prof)
    return ordem, info


if __name__ == '__main__':
    ordem, info = ler(sys.argv[1])
    n = 0
    for k, v in ordem:
        if k == 'real':
            print(n, v, ','.join(sorted(info.get(v, []))), sep='\t')
        else:
            print(n, k, len(v) if isinstance(v, bytes) else v, sep='\t')
        n += 1
