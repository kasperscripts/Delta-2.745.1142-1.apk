#!/usr/bin/env python3
"""Execute the packaged ARM64 constructors and bootstrap with mock Android JNI.

No network implementation exists in this probe. Background threads are recorded,
not scheduled. This tests native bootstrap and predicates, not Android rendering.
Requires unicorn==2.1.4 and pyelftools==0.33.
"""
import argparse,hashlib,io,json,struct,time,zipfile
from pathlib import Path
from unicorn import *
from unicorn.arm64_const import *
from elftools.elf.elffile import ELFFile
EXPECTED_HOST='5bcf3cc0f690308e249468c91acbdcd208fd3220a4ab0c853f0b2a89e0349224'
EXPECTED_PAYLOAD='094252b1622d90b2a0d4085a6742fa8da3e4d9cfaecbf601bc22660a0dae3ee5'
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('apk',type=Path);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
u=Uc(UC_ARCH_ARM64,UC_MODE_ARM)
for at,size in [(0x20000000,0x1000000),(0x30000000,0x400000),(0x2000000,0x2000000),(0x4000000,0x200000)]:u.mem_map(at,size)
HOST=0x20000000;PAYLOAD=0x30000000;STOP=0x401ff00;VM=0x4110000;ENV=0x4112000;heap=0x2100000
images=[];imports={};names={};files={};tls={};threads=[];once=[];jni_methods=[];key_count=0;handles={}
u.reg_write(UC_ARM64_REG_TPIDR_EL0,0x4100000);u.reg_write(UC_ARM64_REG_CPACR_EL1,3<<20)
def alloc(n):
 global heap
 at=heap;heap+=(n+15)&~15
 assert heap<0x3e00000
 return at
def cs(a):return bytes(u.mem_read(a,4096)).split(b'\0')[0].decode(errors='replace') if a else ''
def ptr(a):return struct.unpack('<Q',bytes(u.mem_read(a,8)))[0]
def ret(n=0):u.reg_write(UC_ARM64_REG_X0,n&0xffffffffffffffff);u.reg_write(UC_ARM64_REG_PC,u.reg_read(UC_ARM64_REG_LR))
def call(pc,params=()):
 for i,x in enumerate(params):u.reg_write(UC_ARM64_REG_X0+i,x)
 u.reg_write(UC_ARM64_REG_SP,0x3fff000);u.reg_write(UC_ARM64_REG_LR,STOP)
 u.emu_start(pc,STOP,timeout=30000000,count=0)
 assert u.reg_read(UC_ARM64_REG_PC)==STOP,hex(u.reg_read(UC_ARM64_REG_PC))
 return u.reg_read(UC_ARM64_REG_X0)
def proc_maps():
 lines=[]
 for index,(e,base,data,name,tags) in enumerate(images,1):
  for s in e.iter_segments():
   if s['p_type']!='PT_LOAD':continue
   start=(base+s['p_vaddr'])&~4095;end=(base+s['p_vaddr']+s['p_filesz']+4095)&~4095;memend=(base+s['p_vaddr']+s['p_memsz']+4095)&~4095
   lines.append(f'{start:08x}-{end:08x} rwxp {s["p_offset"]&~4095:08x} 00:00 {index} /data/app/com.grand.cr/lib/arm64/{name}\n')
   if memend>end:lines.append(f'{end:08x}-{memend:08x} rw-p 00000000 00:00 0\n')
 return ''.join(sorted(lines,key=lambda x:int(x.split('-')[0],16))).encode()
def open_file(path):
 data=proc_maps() if path=='/proc/self/maps' else next((data for _,_,data,name,_ in images if path.endswith(name)),None)
 if data is None:return -2
 fd=10+len(files);files[fd]=io.BytesIO(data);return fd
def syscall(n,a):
 if n==56:return open_file(cs(a[1]))
 if n==63:
  data=files[a[0]].read(a[2]);u.mem_write(a[1],data);return len(data)
 if n==67:
  files[a[0]].seek(a[3]);data=files[a[0]].read(a[2]);u.mem_write(a[1],data);return len(data)
 if n==62:return files[a[0]].seek(a[1],a[2])
 if n==226:u.mem_protect(a[0],a[1],a[2]);return 0
 if n in [57,101]:return 0
 if n==222:return alloc(a[1])
 if n in [172,178]:return 1000
 raise RuntimeError(('unimplemented syscall',n))
def intr(machine,no,_):
 assert no==2,(no,hex(u.reg_read(UC_ARM64_REG_PC)))
 a=[u.reg_read(UC_ARM64_REG_X0+i) for i in range(6)];u.reg_write(UC_ARM64_REG_X0,syscall(u.reg_read(UC_ARM64_REG_X8),a)&0xffffffffffffffff)
u.hook_add(UC_HOOK_INTR,intr)
def imported(machine,pc,size,_):
 global key_count
 n=names[pc];a=[u.reg_read(UC_ARM64_REG_X0+i) for i in range(8)]
 if n in ['memcpy','memmove','__memcpy_chk']:u.mem_write(a[0],bytes(u.mem_read(a[1],a[2])));ret(a[0])
 elif n in ['memset','__memset_chk']:u.mem_write(a[0],bytes([a[1]&255])*a[2]);ret(a[0])
 elif n in ['malloc','calloc']:ret(alloc(a[0]*(a[1] if n=='calloc' else 1)))
 elif n=='realloc':
  at=alloc(a[1]);u.mem_write(at,bytes(u.mem_read(a[0],a[1])) if a[0] else bytes(a[1]));ret(at)
 elif n=='strlen':ret(len(cs(a[0]).encode()))
 elif n in ['strcmp','strncmp','memcmp']:
  x,y=(bytes(u.mem_read(a[0],a[2])),bytes(u.mem_read(a[1],a[2]))) if n=='memcmp' else (cs(a[0]).encode(),cs(a[1]).encode())
  if n=='strncmp':x=x[:a[2]];y=y[:a[2]]
  ret((x>y)-(x<y))
 elif n=='mprotect':u.mem_protect(a[0],a[1],a[2]);u.ctl_remove_cache(a[0],a[0]+a[1]);ret()
 elif n=='pthread_create':threads.append((a[2],a[3]));u.mem_write(a[0],struct.pack('<Q',len(threads)));ret()
 elif n=='pthread_once':
  if not ptr(a[0])&0xffffffff:
   u.mem_write(a[0],struct.pack('<I',1));once.append(u.reg_read(UC_ARM64_REG_LR));u.reg_write(UC_ARM64_REG_LR,0x4017010);u.reg_write(UC_ARM64_REG_PC,a[1])
  else:ret()
 elif n=='pthread_key_create':key_count+=1;u.mem_write(a[0],struct.pack('<I',key_count));ret()
 elif n=='pthread_getspecific':ret(tls.get(a[0],0))
 elif n=='pthread_setspecific':tls[a[0]]=a[1];ret()
 elif n in ['__cxa_atexit','__cxa_finalize','__register_atfork','free','pthread_mutex_init','pthread_mutex_lock','pthread_mutex_unlock','pthread_mutex_destroy','pthread_attr_init','pthread_attr_setdetachstate','pthread_attr_destroy','sigaction','sigemptyset','getauxval','pthread_detach','__android_log_print']:ret()
 elif n=='__errno':ret(0x4100100)
 elif n=='__system_property_get':
  value=b'36' if 'sdk' in cs(a[0]) else b'';u.mem_write(a[1],value+b'\0');ret(len(value))
 elif n=='getenv':ret()
 elif n=='clock_gettime':now=time.time_ns();u.mem_write(a[1],struct.pack('<QQ',now//1000000000,now%1000000000));ret()
 elif n=='localeconv':
  at=alloc(128);q=alloc(16);u.mem_write(q,b'.\0');u.mem_write(at,struct.pack('<10Q',q,*([q+1]*9)));ret(at)
 elif n=='dlopen':assert cs(a[0])=='libgrnd.so';ret(HOST)
 elif n=='dlsym':assert cs(a[1])=='JNI_OnLoad';ret(HOST+0x482a0c)
 elif n=='syscall':ret(syscall(a[0],a[1:]))
 elif n in ['open','__open_2']:ret(open_file(cs(a[0])))
 else:raise RuntimeError(('unimplemented import',n,hex(u.reg_read(UC_ARM64_REG_LR))))
u.hook_add(UC_HOOK_CODE,imported,begin=0x4000000,end=0x400ffff)
def once_done(machine,pc,size,_):u.reg_write(UC_ARM64_REG_LR,once.pop());ret()
u.mem_write(0x4017010,bytes.fromhex('c0035fd6'));u.hook_add(UC_HOOK_CODE,once_done,begin=0x4017010,end=0x4017010)
def jni(machine,pc,size,_):
 index=(pc-0x4010000)//16;a=[u.reg_read(UC_ARM64_REG_X0+i) for i in range(8)]
 if index in [304,306,307]:u.mem_write(a[1],struct.pack('<Q',ENV));ret()
 elif index in [305,17,19,22,228,23,226]:ret()
 elif index in [20,21]:ret(a[1])
 elif index==6:
  name=cs(a[1]);ret(handles.setdefault(name,alloc(16)))
 elif index in [33,113,94,144]:ret(alloc(16))
 elif index==215:
  for i in range(a[3]):
   name,sig,fn=struct.unpack('<3Q',bytes(u.mem_read(a[2]+i*24,24)));jni_methods.append({'name':cs(name),'signature':cs(sig),'address':hex(fn)})
  ret()
 else:raise RuntimeError(('unimplemented JNI',index))
u.mem_write(VM,struct.pack('<Q',VM+0x1000));u.mem_write(ENV,struct.pack('<Q',ENV+0x1000))
for index in range(256):
 at=0x4010000+index*16;u.mem_write(at,bytes.fromhex('c0035fd6'));u.mem_write(ENV+0x1000+index*8,struct.pack('<Q',at))
for index in range(8):
 at=0x4010000+(300+index)*16;u.mem_write(at,bytes.fromhex('c0035fd6'));u.mem_write(VM+0x1000+index*8,struct.pack('<Q',at))
u.hook_add(UC_HOOK_CODE,jni,begin=0x4010000,end=0x4011400)
def load(data,base,name):
 e=ELFFile(io.BytesIO(data));d=next(p for p in e.iter_segments() if p['p_type']=='PT_DYNAMIC');t={x.entry.d_tag:x.entry.d_val for x in d.iter_tags()};symbols=list(d.iter_symbols())
 for s in symbols:
  if s.name and s['st_shndx']=='SHN_UNDEF' and s.name not in imports:
   at=0x4000000+len(imports)*16;imports[s.name]=at;names[at]=s.name;u.mem_write(at,bytes.fromhex('c0035fd6'))
 for p in e.iter_segments():
  if p['p_type']=='PT_LOAD':u.mem_write(base+p['p_vaddr'],p.data())
 for start,length in [(t['DT_RELA'],t['DT_RELASZ']),(t['DT_JMPREL'],t['DT_PLTRELSZ'])]:
  for a in range(start,start+length,24):
   target,info,v=struct.unpack('<QQq',bytes(u.mem_read(base+a,24)));kind=info&0xffffffff;i=info>>32
   if kind==1027:v+=base
   elif kind in [257,1025,1026]:v+=imports[symbols[i].name] if symbols[i]['st_shndx']=='SHN_UNDEF' else base+symbols[i]['st_value']
   else:raise RuntimeError(('relocation',kind))
   u.mem_write(base+target,struct.pack('<Q',v))
 images.append((e,base,data,name,t));return t
with zipfile.ZipFile(args.apk) as z:
 host=z.read('lib/arm64-v8a/libgrnd.so');payload=z.read('lib/arm64-v8a/libiconpayload.so')
assert hashlib.sha256(host).hexdigest()==EXPECTED_HOST,'Unexpected host library'
assert hashlib.sha256(payload).hexdigest()==EXPECTED_PAYLOAD,'Unexpected payload library'
ht=load(host,HOST,'libgrnd.so');pt=load(payload,PAYLOAD,'libiconpayload.so')
# Android applies segment permissions and GNU_RELRO after relocation, before constructors.
for e,base,data,name,tags in images:
 for seg in e.iter_segments():
  if seg['p_type']!='PT_LOAD':continue
  at=(base+seg['p_vaddr'])&~4095;end=(base+seg['p_vaddr']+seg['p_memsz']+4095)&~4095
  prot=(UC_PROT_READ if seg['p_flags']&4 else 0)|(UC_PROT_WRITE if seg['p_flags']&2 else 0)|(UC_PROT_EXEC if seg['p_flags']&1 else 0)
  u.mem_protect(at,end-at,prot)
 for seg in e.iter_segments():
  if seg['p_type']=='PT_GNU_RELRO':
   at=(base+seg['p_vaddr'])&~4095;end=(base+seg['p_vaddr']+seg['p_memsz']+4095)&~4095
   u.mem_protect(at,end-at,UC_PROT_READ)
ctors={}
for base,t in [(HOST,ht),(PAYLOAD,pt)]:
 for a in range(t['DT_INIT_ARRAY'],t['DT_INIT_ARRAY']+t['DT_INIT_ARRAYSZ'],8):call(ptr(base+a))
 ctors[hex(base)]=t['DT_INIT_ARRAYSZ']//8
assert call(HOST+0x482a0c,[VM,0])==0x10006
assert len(jni_methods)==21
assert threads==[(HOST+0x47a998,0)]
assert call(HOST+0x47a998)==0
assert call(HOST+0x483984)==1
assert ptr(HOST+0x882f68)==0,'Menu must not activate before the game libraries are ready'
pe=ELFFile(io.BytesIO(payload));pd=next(x for x in pe.iter_segments() if x['p_type']=='PT_DYNAMIC')
entry=next(x['st_value'] for x in pd.iter_symbols() if x.name=='JNI_OnLoad')
assert call(PAYLOAD+entry,[VM,0])==0x10006
state=call(HOST+0x483984);license_ok=call(PAYLOAD+0x19a6c4);feature_ok=call(PAYLOAD+0x193fb8);draw=ptr(HOST+0x882f68)
assert state==license_ok==1 and feature_ok==0 and draw==PAYLOAD+0x1ad55c
assert [call(PAYLOAD+0x1a2ae4,[i]) for i in range(60)]==[0]*60
rpc_out=alloc(16);error=alloc(64);u.mem_write(rpc_out,b'\xff'*16)
op=alloc(32);u.mem_write(op,b'premium.offsets\0')
assert call(HOST+0x50f174,[op,0,0,rpc_out,rpc_out+8,error,64])==0
assert bytes(u.mem_read(rpc_out,16))==bytes(16)
report={'apk_sha256':hashlib.file_digest(args.apk.open('rb'),'sha256').hexdigest(),'host_sha256':hashlib.sha256(host).hexdigest(),'payload_sha256':hashlib.sha256(payload).hexdigest(),'constructors_executed':ctors,'jni_registered':len(jni_methods),'native_startup_state':state,'deferred_activation_verified':True,'local_license_predicate':license_ok,'address_dependent_feature_predicate':feature_ok,'menu_callback':hex(draw),'missing_offsets':60,'gnu_relro_and_segment_permissions_enforced':True,'license_transport_disabled':True,'network_requests':0,'full_premium_unlocked':False,'android_device_tested':False,'limitations':['JNI and libc are mocked; background threads are not scheduled','No full Android lifecycle, graphics or gameplay tested','Premium address profile remains absent']}
args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
