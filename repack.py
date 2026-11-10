#!/usr/bin/env python3
"""Replace classes4.dex while preserving all other APK entry contents."""
import argparse
import hashlib
import re
import zipfile
from pathlib import Path

ORIGINAL_SHA256 = '4d22c8be0f81251d18dc53a49b42a4c27ec64eb1ee039106a33913987027c3f2'
SIGNATURE = re.compile(r'META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))', re.I)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('dex', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if len({p.resolve() for p in [args.original, args.dex, args.output]}) != 3:
        parser.error('Input and output paths must be different.')
    if hashlib.file_digest(args.original.open('rb'), 'sha256').hexdigest() != ORIGINAL_SHA256:
        parser.error('This patch supports only the original APK hash documented in README.md.')
    dex = args.dex.read_bytes()
    if not dex.startswith(b'dex\n'):
        parser.error('The replacement is not a DEX file.')
    for required in [b'https://t.me/Icon_Crack', b'cracked by @Icon_Crack']:
        if required not in dex:
            parser.error('The replacement DEX is missing a required branding string.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.original) as src, zipfile.ZipFile(args.output, 'w') as dst:
        for info in src.infolist():
            if SIGNATURE.fullmatch(info.filename):
                continue
            data = dex if info.filename == 'classes4.dex' else src.read(info.filename)
            dst.writestr(info, data, compresslevel=1)
    print(args.output)


if __name__ == '__main__':
    main()
