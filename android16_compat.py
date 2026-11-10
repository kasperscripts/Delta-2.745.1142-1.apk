#!/usr/bin/env python3
"""Repack with stored native libraries and explicit Android page-size compatibility."""
import argparse
import re
import struct
import zipfile
from pathlib import Path

ATTRS = {'extractNativeLibs': 0x010104EA, 'pageSizeCompat': 0x010106AB}
ANDROID_NS = 'http://schemas.android.com/apk/res/android'
SIGNATURE = re.compile(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))', re.I)


def chunks(data):
    offset = 8
    while offset < len(data):
        kind, header, size = struct.unpack_from('<HHI', data, offset)
        assert size >= header >= 8 and offset + size <= len(data)
        yield kind, data[offset:offset + size]
        offset += size
    assert offset == len(data)


def len8(data, pos):
    n = data[pos]
    return (((n & 127) << 8) | data[pos + 1], pos + 2) if n & 128 else (n, pos + 1)


def strings(pool):
    count, styles, flags, start, _ = struct.unpack_from('<IIIII', pool, 8)
    assert styles == 0, 'Styled manifest string pools are unsupported'
    result = []
    raw = []
    for i in range(count):
        pos = start + struct.unpack_from('<I', pool, 28 + i * 4)[0]
        begin = pos
        if flags & 0x100:
            _, pos = len8(pool, pos)
            n, pos = len8(pool, pos)
            result.append(pool[pos:pos + n].decode('utf-8'))
            raw.append(pool[begin:pos + n + 1])
        else:
            n = struct.unpack_from('<H', pool, pos)[0]
            pos += 2
            if n & 0x8000:
                n = ((n & 0x7FFF) << 16) | struct.unpack_from('<H', pool, pos)[0]
                pos += 2
            result.append(pool[pos:pos + n * 2].decode('utf-16le'))
            raw.append(pool[begin:pos + n * 2 + 2])
    return result, raw, flags


def patch_manifest(data):
    assert data[:4] == b'\x03\x00\x08\x00'
    parts = list(chunks(data))
    pool = next(chunk for kind, chunk in parts if kind == 1)
    names, raw, flags = strings(pool)
    resmap = next(chunk for kind, chunk in parts if kind == 0x180)
    ids = list(struct.unpack('<' + 'I' * ((len(resmap) - 8) // 4), resmap[8:]))
    ids.extend([0] * (len(names) - len(ids)))
    for name, res_id in ATTRS.items():
        if name not in names:
            names.append(name)
            raw.append(bytes([len(name), len(name)]) + name.encode() + b'\0' if flags & 0x100 else struct.pack('<H', len(name)) + name.encode('utf-16le') + b'\0\0')
            ids.append(res_id)
        else:
            ids[names.index(name)] = res_id
    offsets, payload = [], b''
    for value in raw:
        offsets.append(len(payload))
        payload += value
    payload += bytes((-len(payload)) % 4)
    start = 28 + 4 * len(names)
    new_pool = struct.pack('<HHIIIIII', 1, 28, start + len(payload), len(names), 0, flags & ~1, start, 0) + struct.pack('<' + 'I' * len(offsets), *offsets) + payload
    new_map = struct.pack('<HHI', 0x180, 8, 8 + 4 * len(ids)) + struct.pack('<' + 'I' * len(ids), *ids)
    output = []
    patched = False
    for kind, chunk in parts:
        if kind == 1:
            output.append(new_pool)
        elif kind == 0x180:
            output.append(new_map)
        elif kind == 0x102 and names[struct.unpack_from('<I', chunk, 20)[0]] == 'application':
            attr_start, attr_size, count, id_idx, cls_idx, style_idx = struct.unpack_from('<HHHHHH', chunk, 24)
            assert attr_size == 20 and id_idx == cls_idx == style_idx == 0
            begin = 16 + attr_start
            records = [chunk[begin + i * 20:begin + (i + 1) * 20] for i in range(count)]
            wanted = {names.index(name) for name in ATTRS}
            records = [r for r in records if struct.unpack_from('<I', r, 4)[0] not in wanted]
            for index in wanted:
                records.append(struct.pack('<IIIHBBI', names.index(ANDROID_NS), index, 0xFFFFFFFF, 8, 0, 0x12, 0xFFFFFFFF))
            records.sort(key=lambda r: ids[struct.unpack_from('<I', r, 4)[0]])
            header = bytearray(chunk[:begin])
            struct.pack_into('<I', header, 4, begin + len(records) * 20)
            struct.pack_into('<H', header, 28, len(records))
            output.append(bytes(header) + b''.join(records))
            patched = True
        else:
            output.append(chunk)
    assert patched
    body = b''.join(output)
    result = struct.pack('<HHI', 3, 8, 8 + len(body)) + body
    list(chunks(result))
    return result


def repack(source, output):
    assert source.resolve() != output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(output, 'w') as dst:
        for info in src.infolist():
            if SIGNATURE.fullmatch(info.filename):
                continue
            content = src.read(info.filename)
            if info.filename == 'AndroidManifest.xml':
                content = patch_manifest(content)
            if info.filename.startswith('lib/') and info.filename.endswith('.so'):
                info.compress_type = zipfile.ZIP_STORED
            info.extra = b''
            info.comment = b''
            dst.writestr(info, content, compresslevel=6)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    repack(args.source, args.output)
    print(args.output)
