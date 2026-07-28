import os
import struct
import zlib

out_path = os.path.join(os.path.dirname(__file__), 'dino.png')
W = H = 64
pixels = bytearray()

for y in range(H):
    for x in range(W):
        pixels.extend((0, 0, 0, 0))


def fill_rect(x0, y0, x1, y1, color):
    for y in range(max(0, y0), min(H, y1)):
        for x in range(max(0, x0), min(W, x1)):
            idx = (y * W + x) * 4
            pixels[idx:idx + 4] = bytes(color)


def fill_circle(cx, cy, radius, color):
    for y in range(max(0, cy - radius), min(H, cy + radius + 1)):
        for x in range(max(0, cx - radius), min(W, cx + radius + 1)):
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius * radius:
                idx = (y * W + x) * 4
                pixels[idx:idx + 4] = bytes(color)

# body
fill_rect(10, 20, 56, 54, (64, 178, 112, 255))
fill_rect(14, 12, 44, 24, (64, 178, 112, 255))
fill_rect(44, 18, 58, 42, (64, 178, 112, 255))
fill_rect(18, 34, 34, 44, (245, 240, 205, 255))
fill_rect(42, 20, 50, 28, (245, 240, 205, 255))

# head/eye
fill_circle(48, 20, 10, (64, 178, 112, 255))
fill_circle(48, 20, 5, (248, 248, 248, 255))
fill_circle(49, 20, 2, (20, 20, 20, 255))

# tail and legs
fill_rect(10, 36, 18, 46, (25, 114, 64, 255))
fill_rect(24, 46, 30, 56, (25, 114, 64, 255))
fill_rect(38, 46, 44, 56, (25, 114, 64, 255))
fill_rect(52, 46, 58, 56, (25, 114, 64, 255))

# border accents
for y in range(18, 56):
    for x in range(12, 18):
        if (x + y) % 2 == 0:
            idx = (y * W + x) * 4
            pixels[idx:idx + 4] = bytes((34, 110, 66, 255))


def chunk(chunk_type, data):
    return struct.pack('!I', len(data)) + chunk_type + data + struct.pack('!I', zlib.crc32(chunk_type + data) & 0xffffffff)

png = bytearray(b'\x89PNG\r\n\x1a\n')
png.extend(chunk(b'IHDR', struct.pack('!IIBBBBB', W, H, 8, 6, 0, 0, 0)))
png.extend(chunk(b'IDAT', zlib.compress(bytes(pixels), 9)))
png.extend(chunk(b'IEND', b''))

with open(out_path, 'wb') as f:
    f.write(png)

print(f'Created {out_path}')
