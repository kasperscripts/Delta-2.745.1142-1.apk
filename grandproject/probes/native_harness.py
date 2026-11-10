"""Isolated ARM64 harness for the exact GrandProject APK; all networking is blocked."""
import io,struct,pathlib,os,zipfile,hashlib
from unicorn import *
from unicorn.arm64_const import *
from elftools.elf.elffile import ELFFile
APK=pathlib.Path(os.environ['GRANDPROJECT_APK'])
with zipfile.ZipFile(APK) as source:
 raw=source.read('lib/arm64-v8a/libgrnd.so')
assert hashlib.sha256(raw).hexdigest()=='23db7a5e36f3b560f6804f9f7aa4a44c0855d39b6d2b5d4de89daebdd9fdba42', 'Unexpected native library; offsets must not be reused'
elf=ELFFile(io.BytesIO(raw))
u=Uc(UC_ARCH_ARM64,UC_MODE_ARM)
u.mem_map(0,0x1000000);u.mem_map(0x2000000,0x2000000);u.mem_map(0x4000000,0x200000)
for p in elf.iter_segments():
 if p['p_type']=='PT_LOAD':u.mem_write(p['p_vaddr'],p.data())
dyn=next(p for p in elf.iter_segments() if p['p_type']=='PT_DYNAMIC')
tags={t.entry.d_tag:t.entry.d_val for t in dyn.iter_tags()}
syms=list(dyn.iter_symbols());imports={};names={}
for s in syms:
 if s.name and s['st_shndx']=='SHN_UNDEF':
  a=0x4000000+len(imports)*16;imports[s.name]=a;names[a]=s.name;u.mem_write(a,bytes.fromhex('c0035fd6'))
for start,sz in [(tags['DT_RELA'],tags['DT_RELASZ']),(tags['DT_JMPREL'],tags['DT_PLTRELSZ'])]:
 for off in range(start,start+sz,24):
  a,info,v=struct.unpack('<QQq',bytes(u.mem_read(off,24)));ty=info&0xffffffff;ix=info>>32
  if ty==1027:pass
  elif ty in [257,1025,1026]:v+=imports.get(syms[ix].name,syms[ix]['st_value'])
  else:raise RuntimeError(('reloc',ty))
  u.mem_write(a,struct.pack('<Q',v))
STOP=0x401ff00;heap=0x2100000;files={};tls={}
u.reg_write(UC_ARM64_REG_SP,0x3fff000);u.reg_write(UC_ARM64_REG_TPIDR_EL0,0x4100000)
u.reg_write(UC_ARM64_REG_CPACR_EL1,3<<20)
def alloc(n):
 global heap
 a=heap;heap+=(n+15)&~15
 if heap>=0x3e00000:raise RuntimeError('heap full')
 return a
def s(a):return bytes(u.mem_read(a,4096)).split(b'\0')[0].decode(errors='replace') if a else ''
def ret(v=0):u.reg_write(UC_ARM64_REG_X0,v&0xffffffffffffffff);u.reg_write(UC_ARM64_REG_PC,u.reg_read(UC_ARM64_REG_LR))
def maps():
 return b''.join(f'{p["p_vaddr"]&~4095:08x}-{(p["p_vaddr"]+p["p_filesz"]+4095)&~4095:08x} {"rwxp"} {p["p_offset"]&~4095:08x} 00:00 1 /data/app/lib/arm64/libgrnd.so\n'.encode() for p in elf.iter_segments() if p['p_type']=='PT_LOAD')
def openfile(path):
 if path=='/proc/self/maps':b=maps()
 elif path.endswith('libgrnd.so'):b=raw
 else:print('FILE_MISSING',path,flush=True);return -2
 fd=10+len(files);files[fd]=io.BytesIO(b);return fd
def system(n,a):
 if n==56:return openfile(s(a[1]))
 if n==63:
  b=files[a[0]].read(a[2]);u.mem_write(a[1],b);return len(b)
 if n==67:
  files[a[0]].seek(a[3]);b=files[a[0]].read(a[2]);u.mem_write(a[1],b);return len(b)
 if n==62:return files[a[0]].seek(a[1],a[2])
 if n in [57,226,101]:return 0
 if n==222:return alloc(a[1])
 if n in [172,178]:return 1000
 raise RuntimeError(('syscall',n,[hex(v) for v in a]))
def intr(u,no,data):
 n=u.reg_read(UC_ARM64_REG_X8);a=[u.reg_read(UC_ARM64_REG_X0+i) for i in range(6)]
 if no!=2:raise RuntimeError(('interrupt',no,hex(u.reg_read(UC_ARM64_REG_PC)),n))
 v=system(n,a);u.reg_write(UC_ARM64_REG_X0,v&0xffffffffffffffff)
u.hook_add(UC_HOOK_INTR,intr)
def imp(u,addr,size,data):
 n=names[addr];a=[u.reg_read(UC_ARM64_REG_X0+i) for i in range(8)]
 if n in ['memcpy','memmove','__memcpy_chk']:u.mem_write(a[0],bytes(u.mem_read(a[1],a[2])));ret(a[0])
 elif n in ['memset','__memset_chk']:u.mem_write(a[0],bytes([a[1]&255])*a[2]);ret(a[0])
 elif n in ['malloc','calloc']:ret(alloc(a[0]*(a[1] if n=='calloc' else 1)))
 elif n=='realloc':
  p=alloc(a[1]);u.mem_write(p,bytes(u.mem_read(a[0],a[1])) if a[0] else bytes(a[1]));ret(p)
 elif n in ['strlen']:ret(len(s(a[0]).encode()))
 elif n in ['strcmp','strncmp','memcmp']:
  x=bytes(u.mem_read(a[0],a[2])) if n=='memcmp' else s(a[0]).encode();y=bytes(u.mem_read(a[1],a[2])) if n=='memcmp' else s(a[1]).encode()
  if n=='strncmp':x=x[:a[2]];y=y[:a[2]]
  ret((x>y)-(x<y))
 elif n in ['__cxa_atexit','__cxa_finalize','__register_atfork','free','mprotect','pthread_mutex_init','pthread_mutex_lock','pthread_mutex_unlock','pthread_attr_init','pthread_attr_setdetachstate','pthread_attr_destroy','sigaction','sigemptyset','getauxval']:ret()
 elif n=='pthread_create':print('THREAD',hex(a[2]),hex(a[3]),flush=True);ret()
 elif n=='__errno':ret(0x4100100)
 elif n=='__system_property_get':
  v=b'36' if 'sdk' in s(a[0]) else b'';u.mem_write(a[1],v+b'\0');ret(len(v))
 elif n=='getenv':ret(0)
 elif n=='clock_gettime':u.mem_write(a[1],bytes(16));ret(0)
 elif n=='localeconv':
  p=alloc(128);v=alloc(16);u.mem_write(v,b'.\0');u.mem_write(p,struct.pack('<10Q',v,*([v+1]*9)));ret(p)
 elif n in ['open','__open_2']:ret(openfile(s(a[0])))
 elif n=='syscall':ret(system(a[0],a[1:]))
 elif n=='__android_log_print':print('LOG',s(a[1]),s(a[2]),flush=True);ret()
 else:raise RuntimeError(('import',n,[hex(v) for v in a[:4]],hex(u.reg_read(UC_ARM64_REG_LR))))
import_hook=u.hook_add(UC_HOOK_CODE,imp,begin=0x4000000,end=0x400ffff)
def invalid(u,access,addr,size,val,data):print('INVALID',access,hex(addr),size,'PC',hex(u.reg_read(UC_ARM64_REG_PC)),flush=True);return False
u.hook_add(UC_HOOK_MEM_INVALID,invalid)
def call(a,args=(),count=500000000):
 for i,v in enumerate(args):u.reg_write(UC_ARM64_REG_X0+i,v)
 u.reg_write(UC_ARM64_REG_SP,0x3fff000);u.reg_write(UC_ARM64_REG_LR,STOP)
 u.emu_start(a,STOP,count=count)
 if u.reg_read(UC_ARM64_REG_PC)!=STOP:raise RuntimeError(('incomplete',hex(u.reg_read(UC_ARM64_REG_PC))))
 return u.reg_read(UC_ARM64_REG_X0)
def initialize():
 """Run original unpacking and all constructors without changing APK bytes."""
 call(0x740000)
 count=0
 for a in range(tags['DT_INIT_ARRAY']+8,tags['DT_INIT_ARRAY']+tags['DT_INIT_ARRAYSZ'],8):
  f=struct.unpack('<Q',bytes(u.mem_read(a,8)))[0]
  call(f);count+=1
 return count+1
