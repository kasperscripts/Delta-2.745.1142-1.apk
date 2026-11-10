#!/usr/bin/env python3
"""Repack the v1 Icon APK with the corrected internal UI and matching trust data."""
import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android16_compat import SIGNATURE

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('v1_apk', type=Path)
parser.add_argument('outer_dex', type=Path)
parser.add_argument('bootstrap', type=Path)
parser.add_argument('auth_library', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
paths = [args.v1_apk, args.outer_dex, args.bootstrap, args.auth_library, args.output]
assert len({p.resolve() for p in paths}) == len(paths)
sha = lambda data: hashlib.sha256(data).hexdigest()
assert sha(args.v1_apk.read_bytes()) == 'ad55f0478e63b2044ec4e461df826a7a8e44664c3aa632413a7a6f96e540d84c'
dex = args.outer_dex.read_bytes()
bundle = args.bootstrap.read_bytes()
auth = args.auth_library.read_bytes()
assert dex.startswith(b'dex\n') and b'@Icon_Crack' in dex and b'DramaDLC' not in dex
assert len(bundle) == 3502384
assert sha(bundle) == '63940b2d5b45bc39bbe19eb191a6e0a27d7cb9a6a72f3e973b32a7c804ed1b18'
assert sha(bundle).encode() in dex
assert sha(auth) == '7b7a4c3a0982bbf6a359febde3e3bf18c9668a9265a8c27cbedb22631db9173a'
replacement = {
    'classes.dex': dex,
    'assets/bootstrap.bin': bundle,
    'lib/arm64-v8a/liboxide_auth_bootstrap.so': auth,
}
with zipfile.ZipFile(args.v1_apk) as src, zipfile.ZipFile(args.output, 'w') as dst:
    assert set(replacement) <= set(src.namelist())
    for info in src.infolist():
        if SIGNATURE.fullmatch(info.filename):
            continue
        data = replacement.get(info.filename)
        if data is None:
            data = src.read(info)
        info.extra = b''
        info.comment = b''
        dst.writestr(info, data, compresslevel=6)
print(args.output)
