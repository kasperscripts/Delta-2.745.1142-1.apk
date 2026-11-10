import sys,argparse,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from patch_native import BC,decode_native,packwords,var
ap=argparse.ArgumentParser();ap.add_argument('native',type=Path);ap.add_argument('luau_dir',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args()
LUAU_DIR=args.luau_dir;R=args.output;R.mkdir(parents=True,exist_ok=True)
NAMES=re.findall(r'^\s*(LOP_[A-Z0-9_]+)\s*,',(LUAU_DIR/'Common/include/Luau/Bytecode.h').read_text(),re.M)
def op(name,a=0,b=0,c=0,d=None):return NAMES.index('LOP_'+name)*227%256|(a<<8)|((d&65535)<<16 if d is not None else b<<16|c<<24)
AUX={'GETGLOBAL','SETGLOBAL','GETIMPORT','GETTABLEKS','SETTABLEKS','NAMECALL','JUMPIFEQ','JUMPIFLE','JUMPIFLT','JUMPIFNOTEQ','JUMPIFNOTLE','JUMPIFNOTLT','NEWTABLE','SETLIST','FORGLOOP','LOADKX','FASTCALL2','FASTCALL2K','FASTCALL3','JUMPXEQKNIL','JUMPXEQKB','JUMPXEQKN','JUMPXEQKS','GETUDATAKS','SETUDATAKS','NAMECALLUDATA'}
def vm_test_blob(bc,target):
 names=[s[4:] for s in re.findall(r'^\s*(LOP_[A-Z0-9_]+)\s*,',(LUAU_DIR/'Common/include/Luau/Bytecode.h').read_text(),re.M)];over={}
 for i,f in enumerate(bc.fs):
  code=f['code'][:];pc=0
  while pc<len(code):
   oc=(code[pc]&255)*203%256;name=names[oc];code[pc]=(code[pc]&~255)|oc;pc+=2 if name in AUX else 1
  over[i]=f['header']+var(len(f['types']))+f['types']+var(len(code))+packwords(code)+var(len(f['ks']))+f['kraw']+f['tail']+b'\0\0'
 f=bc.fs[target];ups=f['header'][2];code=[op('LOADNIL',a=j) for j in range(ups)]+[op('NEWCLOSURE',a=ups,d=0)]+[op('CAPTURE',a=1,b=j) for j in range(ups)]+[op('CLOSEUPVALS',a=0),op('RETURN',a=ups,b=2)]
 code=[(w&~255)|((w&255)*203%256) for w in code];wrapper=bytes([ups+1,0,0,0,0])+b'\0'+var(len(code))+packwords(code)+b'\0'+var(1)+var(target)+b'\0\0\0\0'
 return bc.build(overrides=over,extra=[wrapper],main=bc.count)

bc=BC(decode_native(args.native.read_bytes()))
for i in [54,55,107]:(R/f'test-proto-{i}.luauc').write_bytes(vm_test_blob(bc,i))
print('Prepared VM fixtures from the patched native library.')
