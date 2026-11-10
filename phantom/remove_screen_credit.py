#!/usr/bin/env python3
"""Remove Phantom's center credit from decoded internal UI, update menu and cache pin."""
import argparse
import hashlib
import re
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('ui_smali_root', type=Path)
parser.add_argument('outer_smali_root', type=Path)
parser.add_argument('new_bootstrap', type=Path)
args = parser.parse_args()

path = args.ui_smali_root / 'dev/phantom/i/Y.smali'
text = path.read_text()
pattern = r'(?ms)^\.method private addScreenCredit\(\)V\n.*?^\.end method'
method = re.findall(pattern, text)
assert len(method) == 1 and '-crack by @DramaDLC' in method[0]
text = re.sub(pattern, '.method private addScreenCredit()V\n    .locals 0\n\n    return-void\n.end method', text)
assert text.count('-crack by @DramaDLC') == 1
text = text.replace('-crack by @DramaDLC', 'cracked by @Icon_Crack')
assert 'DramaDLC' not in text
path.write_text(text)

path = args.outer_smali_root / 'dev/phantom/l/z.smali'
text = path.read_text()
bundle = args.new_bootstrap.read_bytes()
old_hash = '7c2e59824144085ccf75b411f4222dd41c0756ed28b92126aa9854fd4f529c19'
old_size = 'const-wide/32 v4, 0x3571f8'
assert text.count(old_hash) == text.count(old_size) == 1
text = text.replace(old_hash, hashlib.sha256(bundle).hexdigest())
text = text.replace(old_size, f'const-wide/32 v4, {hex(len(bundle))}')
path.write_text(text)
print('Removed center credit; updated menu attribution and bootstrap cache checks.')
