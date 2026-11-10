#!/usr/bin/env python3
"""Repack GrandProject with local native bootstrap and branding DEX."""
import argparse,hashlib,re,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from android16_compat import patch_manifest,SIGNATURE
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('original',type=Path);ap.add_argument('dex',type=Path);ap.add_argument('host',type=Path);ap.add_argument('payload',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
assert len({p.resolve() for p in [a.original,a.dex,a.host,a.payload,a.output]})==5
assert hashlib.file_digest(a.original.open('rb'),'sha256').hexdigest()=='5a7a7d388c0fb24578bf23c375abaeb4f175991e28c340ae323c0d34f157a2b2'
dex=a.dex.read_bytes();host=a.host.read_bytes();payload=a.payload.read_bytes()
assert dex.startswith(b'dex\n') and b'https://t.me/Icon_Crack' in dex and b'cracked by @Icon_Crack' in dex
assert host.startswith(b'\x7fELF') and payload.startswith(b'\x7fELF')
with zipfile.ZipFile(a.original) as src,zipfile.ZipFile(a.output,'w',allowZip64=True) as dst:
 for info in src.infolist():
  if SIGNATURE.fullmatch(info.filename):continue
  data=dex if info.filename=='classes6.dex' else host if info.filename=='lib/arm64-v8a/libgrnd.so' else src.read(info.filename)
  if info.filename=='AndroidManifest.xml':data=patch_manifest(data)
  if info.filename.startswith('lib/') and info.filename.endswith('.so'):info.compress_type=zipfile.ZIP_STORED
  info.extra=b'';info.comment=b'';dst.writestr(info,data,compresslevel=6)
 info=zipfile.ZipInfo('lib/arm64-v8a/libiconpayload.so');info.compress_type=zipfile.ZIP_STORED;info.external_attr=0o100644<<16;dst.writestr(info,payload)
print(a.output,a.output.stat().st_size)
