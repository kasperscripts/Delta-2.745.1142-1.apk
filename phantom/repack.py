#!/usr/bin/env python3
"""Replace only Phantom classes.dex and page compatibility attributes; preserve native/assets."""
import argparse,hashlib,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from android16_compat import patch_manifest,SIGNATURE
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('original',type=Path);p.add_argument('dex',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();assert len({x.resolve() for x in [a.original,a.dex,a.output]})==3
assert hashlib.file_digest(a.original.open('rb'),'sha256').hexdigest()=='5d9cb8cb27b5e1f41b1b570003429dcfa467f713e5e9c974442ec9d89959423f'
dex=a.dex.read_bytes();assert dex.startswith(b'dex\n') and b'@Icon_Crack' in dex and b'DramaDLC' not in dex
with zipfile.ZipFile(a.original) as src,zipfile.ZipFile(a.output,'w') as dst:
 for info in src.infolist():
  if SIGNATURE.fullmatch(info.filename):continue
  b=dex if info.filename=='classes.dex' else src.read(info)
  if info.filename=='AndroidManifest.xml':b=patch_manifest(b)
  if info.filename.startswith('lib/') and info.filename.endswith('.so'):info.compress_type=zipfile.ZIP_STORED
  info.extra=b'';info.comment=b'';dst.writestr(info,b,compresslevel=6)
print(a.output)
