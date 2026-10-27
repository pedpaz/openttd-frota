# Extrai sprites 8bpp (zoom 1x) de um GRF container v2 para PNG, para referência visual.
# Uso: python3 grfsprite.py arquivo.grf saida_dir N1 N2 ...   (N = índice do sprite = SpriteID no conjunto base)
import struct, sys, os
from PIL import Image
import nml.palette

PAL = nml.palette.raw_palette_data[0]


def decomp(f, n):
    out = bytearray()
    while len(out) < n:
        code = struct.unpack('<b', f.read(1))[0]
        if code >= 0:
            size = 0x80 if code == 0 else code
            out += f.read(size)
        else:
            off = ((code & 7) << 8) | f.read(1)[0]
            size = -(code >> 3)
            for _ in range(size):
                out.append(out[-off])
    return bytes(out[:n])


def main():
    grf, outdir, ids = sys.argv[1], sys.argv[2], [int(v) for v in sys.argv[3:]]
    os.makedirs(outdir, exist_ok=True)
    f = open(grf, 'rb'); f.read(10)
    off = struct.unpack('<I', f.read(4))[0]; base = f.tell(); f.read(1)
    order = []
    while True:
        size = struct.unpack('<I', f.read(4))[0]
        if size == 0:
            break
        t = f.read(1)[0]
        if t == 0xFD:
            order.append(struct.unpack('<I', f.read(4))[0])
        else:
            f.read(size); order.append(None)
    want = {order[i]: i for i in ids}
    f.seek(base + off)
    while True:
        b = f.read(4)
        if len(b) < 4:
            break
        sid = struct.unpack('<I', b)[0]
        if sid == 0:
            break
        size = struct.unpack('<I', f.read(4))[0]
        t = f.read(1)[0]; z = f.read(1)[0]
        h, w, x, y = struct.unpack('<HHhh', f.read(8))
        fim = f.tell() + size - 10
        if sid in want and z == 0 and t in (0x04, 0x0C):
            if t == 0x04:
                px = decomp(f, w * h)
            else:
                n = struct.unpack('<I', f.read(4))[0]
                d = decomp(f, n)
                big = w > 256
                buf = bytearray(w * h)
                for yy in range(h):
                    pos = struct.unpack_from('<I' if big else '<H', d, yy * (4 if big else 2))[0]
                    while True:
                        if big:
                            ln, sk = struct.unpack_from('<HH', d, pos); pos += 4; last = ln & 0x8000; ln &= 0x7FFF
                        else:
                            ln, sk = d[pos], d[pos + 1]; pos += 2; last = ln & 0x80; ln &= 0x7F
                        buf[yy * w + sk: yy * w + sk + ln] = d[pos:pos + ln]; pos += ln
                        if last:
                            break
                px = bytes(buf)
            im = Image.frombytes('P', (w, h), px)
            im.putpalette(PAL)
            rgba = im.convert('RGBA')
            a = [0 if p == 0 else 255 for p in px]
            rgba.putalpha(Image.frombytes('L', (w, h), bytes(a)))
            rgba.save(os.path.join(outdir, f'{want[sid]}.png'))
            print(want[sid], w, h, x, y)
        f.seek(fim)


main()
