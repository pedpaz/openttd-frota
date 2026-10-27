# Extrai sprites 32bpp em zoom 4x de um GRF container v2 para PNG (com offsets no nome do log).
# Uso: python3 grfsprite32.py arquivo.grf saida_dir N1 N2 ...   (N = SpriteID no conjunto base)
import struct, sys, os
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grfsprite import decomp


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
        if sid in want and z == 1 and (t & 0x03) == 0x03:
            bpp = 4 + (1 if t & 0x04 else 0)
            if not t & 0x08:
                px = decomp(f, w * h * bpp)
            else:
                n = struct.unpack('<I', f.read(4))[0]
                d = decomp(f, n)
                big = w > 256          # cabeçalho de trecho com 2+2 bytes
                longo = n > 0xFFFF     # deslocamento de linha com 4 bytes
                px = bytearray(w * h * bpp)
                for yy in range(h):
                    pos = struct.unpack_from('<I' if longo else '<H', d, yy * (4 if longo else 2))[0]
                    while True:
                        if big:
                            ln, sk = struct.unpack_from('<HH', d, pos); pos += 4; last = ln & 0x8000; ln &= 0x7FFF
                        else:
                            ln, sk = d[pos], d[pos + 1]; pos += 2; last = ln & 0x80; ln &= 0x7F
                        a = (yy * w + sk) * bpp
                        px[a:a + ln * bpp] = d[pos:pos + ln * bpp]; pos += ln * bpp
                        if last:
                            break
            rgba = bytes(b for i in range(w * h) for b in px[i * bpp:i * bpp + 4])
            Image.frombytes('RGBA', (w, h), rgba).save(os.path.join(outdir, f'{want[sid]}.png'))
            print(want[sid], w, h, x, y)
        f.seek(fim)


main()
