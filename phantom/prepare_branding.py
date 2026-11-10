#!/usr/bin/env python3
"""Replace Phantom attribution/key and update its pinned signing certificate."""
import argparse,re
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('smali_root',type=Path)
parser.add_argument('--certificate-sha256',default='5fe9cea48690773d6fe2d2b3234cdc5da67ebf2e6caddaba338755d0166fb0e3')
args=parser.parse_args();assert re.fullmatch('[0-9a-f]{64}',args.certificate_sha256)
p=args.smali_root/'dev/secret/oxide/MainActivity.smali';a=p.read_text()
for old,new in [('-crack by @DramaDLC','cracked by @Icon_Crack'),('@DramaDLC','@Icon_Crack'),('a7c95aa32be72dae2a9754c5b7e463719cd02b28a39ac1dd7f47abba1ac94004',args.certificate_sha256)]:
 assert a.count(old)==1,(old,a.count(old));a=a.replace(old,new)
start=a.index('.method private addLocalKey(');end=a.index('.end method',start)
part=a[start:end]
for text in ['Local key','Локальный ключ']:
 escaped=''.join('\\u%04x'%ord(c) if ord(c)>127 else c for c in text)
 old='const-string v2, "'+escaped+'"';assert part.count(old)==1
 part=part.replace(old,'const-string v2, "@Icon_Crack"')
p.write_text(a[:start]+part+a[end:]);print('Prepared Phantom key, hint, attribution and certificate pin.')
