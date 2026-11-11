#!/usr/bin/env python3
"""Rebrand the supported Jarvis APK, including its XOR-encoded embedded UI DEX.

Only string data and DEX checksums change inside either DEX. Their sizes,
string IDs, code, and the native ELF layout are preserved.
"""
import argparse
import base64
import hashlib
import json
import re
import struct
import sys
import zipfile
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android16_compat import SIGNATURE, chunks, strings

ORIGINAL_SHA256 = '1bac23dc8aacfbef28f066842216ce3a68b3fa0f29e874fa9c29fb3a225f5001'
XOR_KEYS = [67, 45, 191, 77, 193, 27, 121, 239]
OLD = 'faustgenius'
NEW = 'Icon_Crack'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def dex_strings(data):
    assert data[:4] == b'dex\n' and data[4:8] in [b'035\0', b'037\0', b'038\0', b'039\0', b'040\0']
    assert struct.unpack_from('<I', data, 32)[0] == len(data)
    count, table = struct.unpack_from('<II', data, 56)
    result = []
    for index in range(count):
        pos = struct.unpack_from('<I', data, table + index * 4)[0]
        length = shift = 0
        while True:
            c = data[pos]
            pos += 1
            length |= (c & 127) << shift
            if c < 128:
                break
            shift += 7
        end = data.index(0, pos)
        value = data[pos:end].replace(b'\xc0\x80', b'\0').decode('utf-8', 'surrogatepass')
        assert len(value.encode('utf-16le', 'surrogatepass')) // 2 == length
        result.append((pos, end, value))
    return result


def patch_dex(data):
    assert data[12:32] == hashlib.sha1(data[32:]).digest()
    assert struct.unpack_from('<I', data, 8)[0] == zlib.adler32(data[12:])
    output = bytearray(data)
    replacements = []
    entries = dex_strings(data)
    new_values = []
    for start, end, value in entries:
        new = value.replace(OLD, 'icon_crack_')
        decoded = None
        if re.fullmatch(r'[A-Za-z0-9+/= \t]+', value):
            for key in XOR_KEYS:
                try:
                    cipher = base64.b64decode(value)
                    plain = bytes(c ^ ((i * 29 + key) & 255) for i, c in enumerate(cipher)).decode('utf-8')
                except (ValueError, UnicodeDecodeError):
                    continue
                if OLD in plain:
                    decoded = plain
                    changed = plain.replace(OLD, NEW)
                    cipher = bytes(c ^ ((i * 29 + key) & 255) for i, c in enumerate(changed.encode('utf-8')))
                    encoded = base64.b64encode(cipher).decode('ascii')
                    assert len(encoded) <= len(value)
                    new = encoded.ljust(len(value))
                    break
        new_values.append(new)
        if new != value:
            encoded = new.encode('utf-8', 'surrogatepass')
            assert len(encoded) == end - start
            output[start:end] = encoded
            replacements.append({'offset': start, 'kind': 'encoded_text' if decoded else 'class_namespace',
                                 'old': decoded or value, 'new': decoded.replace(OLD, NEW) if decoded else new})
    # Changing a string must not violate DEX string-ID ordering.
    units = lambda value: tuple(struct.unpack('<' + 'H' * (len(value.encode('utf-16le', 'surrogatepass')) // 2), value.encode('utf-16le', 'surrogatepass')))
    assert all(units(a) < units(b) for a, b in zip(new_values, new_values[1:]))
    assert len(replacements) == 9, len(replacements)
    output[12:32] = hashlib.sha1(output[32:]).digest()
    struct.pack_into('<I', output, 8, zlib.adler32(output[12:]))
    assert len(output) == len(data) and OLD.encode() not in output
    assert all(a[:2] == b[:2] for a, b in zip(entries, dex_strings(output)))
    return bytes(output), replacements


def patch_manifest(data):
    result = []
    changes = {'faustgenius': 'Jarvis @Icon_Crack',
               '3.5.42-faustgenius-title': '3.5.42-Icon_Crack'}
    found = set()
    for kind, chunk in chunks(data):
        if kind != 1:
            result.append(chunk)
            continue
        names, raw, flags = strings(chunk)
        for index, name in enumerate(names):
            if name not in changes:
                continue
            found.add(name)
            value = changes[name]
            assert len(value) < 128
            raw[index] = (bytes([len(value), len(value)]) + value.encode() + b'\0'
                          if flags & 0x100 else struct.pack('<H', len(value)) + value.encode('utf-16le') + b'\0\0')
        offsets, payload = [], b''
        for value in raw:
            offsets.append(len(payload))
            payload += value
        payload += bytes((-len(payload)) % 4)
        start = 28 + 4 * len(names)
        result.append(struct.pack('<HHIIIIII', 1, 28, start + len(payload), len(names), 0,
                                  flags & ~1, start, 0) + struct.pack('<' + 'I' * len(offsets), *offsets) + payload)
    assert found == changes.keys()
    body = b''.join(result)
    output = struct.pack('<HHI', 3, 8, len(body) + 8) + body
    list(chunks(output))
    return output


def rebrand(source, output, report_path):
    assert len({p.resolve() for p in [source, output, report_path]}) == 3
    assert sha256(source.read_bytes()) == ORIGINAL_SHA256
    with zipfile.ZipFile(source) as src:
        outer, outer_changes = patch_dex(src.read('classes2.dex'))
        native = src.read('assets/jarvis-local.so')
        marker = bytes(c ^ 0x5A for c in b'dex\n035\0')
        assert native.count(marker) == 1
        offset = native.index(marker)
        head = bytes(c ^ 0x5A for c in native[offset:offset + 112])
        size = struct.unpack_from('<I', head, 32)[0]
        inner_original = bytes(c ^ 0x5A for c in native[offset:offset + size])
        inner, inner_changes = patch_dex(inner_original)
        native_new = native[:offset] + bytes(c ^ 0x5A for c in inner) + native[offset + size:]
        assert len(native_new) == len(native)
        replacements = {'classes2.dex': outer, 'assets/jarvis-local.so': native_new,
                        'AndroidManifest.xml': patch_manifest(src.read('AndroidManifest.xml'))}
        with zipfile.ZipFile(output, 'w') as dst:
            for info in src.infolist():
                if SIGNATURE.fullmatch(info.filename):
                    continue
                data = replacements.get(info.filename)
                if data is None:
                    data = src.read(info)
                info.extra = b''
                info.comment = b''
                dst.writestr(info, data, compresslevel=6)
    report_path.write_text(json.dumps({'original_sha256': ORIGINAL_SHA256,
        'key': '@Icon_Crack', 'telegram': 'https://t.me/Icon_Crack',
        'displayed_telegram': 't.me/Icon_Crack',
        'outer_dex_sha256': sha256(outer), 'embedded_dex_sha256': sha256(inner),
        'embedded_dex_offset': offset, 'embedded_dex_size': size,
        'native_sha256': sha256(native_new), 'native_size': len(native_new),
        'outer_replacements': outer_changes, 'inner_replacements': inner_changes,
        'dex_sizes_and_string_offsets_preserved': True,
        'dex_string_id_order_checked': True,
        'native_bytes_outside_embedded_dex_unchanged': True}, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    rebrand(args.original, args.output, args.report)
    print(args.output)
