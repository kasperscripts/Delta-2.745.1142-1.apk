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
EXPECTED_PAYLOAD='3e5695a16276269605451e0e9fd2ab7b869096f7387011fe858ec357ed1fb707'
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('apk',type=Path);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--cache',type=Path);args=ap.parse_args()
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
 lines=[];regions=list(u.mem_regions())
 def append_region(start,end,offset,path,ident):
  for lo,hi,prot in regions:
   lo=max(start,lo);hi=min(end,hi+1)
   if lo>=hi:continue
   perm=('r' if prot&UC_PROT_READ else '-')+('w' if prot&UC_PROT_WRITE else '-')+('x' if prot&UC_PROT_EXEC else '-')+'p'
   lines.append(f'{lo:08x}-{hi:08x} {perm} {offset+lo-start:08x} 00:00 {ident} {path}\n')
 for index,(e,base,data,name,tags) in enumerate(images,1):
  for s in e.iter_segments():
   if s['p_type']!='PT_LOAD':continue
   start=(base+s['p_vaddr'])&~4095;end=(base+s['p_vaddr']+s['p_filesz']+4095)&~4095;memend=(base+s['p_vaddr']+s['p_memsz']+4095)&~4095
   append_region(start,end,s['p_offset']&~4095,f'/data/app/com.grand.cr/lib/arm64/{name}',index)
   if memend>end:append_region(end,memend,0,'',0)
 append_region(0x2000000,0x4000000,0,'',0)
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
 elif n in ['_Znwm','_Znam']:ret(alloc(a[0]))
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
 elif n in ['__cxa_atexit','__cxa_finalize','__register_atfork','free','pthread_mutex_init','pthread_mutex_lock','pthread_mutex_unlock','pthread_mutex_destroy','pthread_attr_init','pthread_attr_setdetachstate','pthread_attr_destroy','sigaction','sigemptyset','getauxval','__cxa_guard_release','pthread_detach','__android_log_vprint','__android_log_print']:ret()
 elif n=='__cxa_guard_acquire':ret(1)
 elif n=='sysconf':ret(4096)
 elif n=='mmap':
  at=(alloc(a[1]+8192)+4095)&~4095;ret(at)
 elif n in ['munmap','__clear_cache']:ret()
 elif n=='fopen':ret(max(0,open_file(cs(a[0]))))
 elif n=='fclose':ret()
 elif n=='fgets':
  data=files[a[2]].readline(a[1]-1)
  if data:u.mem_write(a[0],data+b'\0')
  ret(a[0] if data else 0)
 elif n in ['sscanf','__sscanf_chk']:
  line=cs(a[0]);fields=line.split();lo,hi=fields[0].split('-')
  u.mem_write(a[2],struct.pack('<Q',int(lo,16)));u.mem_write(a[3],struct.pack('<Q',int(hi,16)))
  u.mem_write(a[4],fields[1].encode()+b'\0');ret(3)
 elif n=='__errno':ret(0x4100100)
 elif n=='__system_property_get':
  value=b'36' if 'sdk' in cs(a[0]) else b'';u.mem_write(a[1],value+b'\0');ret(len(value))
 elif n=='getenv':ret()
 elif n=='clock_gettime':now=time.time_ns();u.mem_write(a[1],struct.pack('<QQ',now//1000000000,now%1000000000));ret()
 elif n=='localeconv':
  at=alloc(128);q=alloc(16);u.mem_write(q,b'.\0');u.mem_write(at,struct.pack('<10Q',q,*([q+1]*9)));ret(at)
 elif n=='dladdr':
  target=next((base for e,base,data,name,tags in images if base<=a[0]<base+0x2800000),None)
  assert target is not None
  path=alloc(64);u.mem_write(path,b'/data/app/libgrand.so\0');u.mem_write(a[1],struct.pack('<4Q',path,target,0,0));ret(1)
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
assert state==license_ok==1 and feature_ok==1 and draw==PAYLOAD+0x1ad55c
expected=json.loads((Path(__file__).resolve().parents[1]/'offset-profile.json').read_text())['entries']
assert [call(PAYLOAD+0x1a2ae4,[i]) for i in range(60)]==[int(e['value'],16) for e in expected]

def invalid(machine,access,address,size,value,_):
 print('INVALID',access,hex(address),size,hex(u.reg_read(UC_ARM64_REG_PC)),flush=True);return False
u.hook_add(UC_HOOK_MEM_INVALID,invalid)
GAME=0x40000000
u.mem_map(GAME,0x2800000)
with zipfile.ZipFile(args.apk) as z:game=z.read('lib/arm64-v8a/libgrand.so')
assert hashlib.sha256(game).hexdigest()=='eab24307e5dc0dbb714420ebb1131a6eb2aaecd05aab88fa9b891bd1835a85fa'
gt=load(game,GAME,'libgrand.so')
print('GAME_LOADED',flush=True)
cache=args.cache
for seg in images[-1][0].iter_segments():
 if seg['p_type']=='PT_LOAD':
  at=(GAME+seg['p_vaddr'])&~4095;end=(GAME+seg['p_vaddr']+seg['p_memsz']+4095)&~4095
  prot=(UC_PROT_READ if seg['p_flags']&4 else 0)|(UC_PROT_WRITE if seg['p_flags']&2 else 0)|(UC_PROT_EXEC if seg['p_flags']&1 else 0)
  u.mem_protect(at,end-at,prot)
if cache is not None and cache.exists():
 u.mem_write(GAME,cache.read_bytes())
else:
 for offset in range(gt['DT_INIT_ARRAY'],gt['DT_INIT_ARRAY']+8,8):call(ptr(GAME+offset))
 if cache is not None:cache.write_bytes(bytes(u.mem_read(GAME,0x2300000)))
print('GAME_PROTECTOR_CTOR_DONE',flush=True)
u.mem_write(PAYLOAD+0x2a1350,struct.pack('<Q',GAME))
u.mem_write(PAYLOAD+0x2a2370,struct.pack('<Q',0xac6000))
print('BASE_RESOLVED',hex(call(PAYLOAD+0x10bfdc,[0])),flush=True)
ge=images[-1][0]
u.mem_write(PAYLOAD+0x2a1358,struct.pack('<QH',GAME+ge['e_phoff'],ge['e_phnum']))

# Validate profile address extent and intended permissions against actual game ELF segments.
for e in expected:
 value=int(e['value'],16)+(0xac6000 if e['relative_to_libgame'] else 0)
 assert any(s['p_type']=='PT_LOAD' and s['p_vaddr']<=value and value+e['min_bytes']<=s['p_vaddr']+s['p_memsz'] and s['p_flags']&e['flags']==e['flags'] for s in images[-1][0].iter_segments()),e
print('PROFILE_RANGES_PASS',flush=True)
# Exercise actual native glue: owner setter, data setter/getter, player and vehicle pool singletons.
owner=alloc(0x800);data=alloc(48);pattern=bytes(range(44));u.mem_write(data,pattern)
call(GAME+0x490848,[owner]);assert ptr(GAME+0x1f17ea8)==owner
call(GAME+0x49081c,[data]);assert bytes(u.mem_read(GAME+0x1f17eb0,44))==pattern
assert call(GAME+0x490864)==owner and call(GAME+0x490810)==GAME+0x1f17eb0
print('BULLET_DATA_PASS',flush=True)

# Verify the serializers send the expected struct length and preserve the data pointer.
writes=[]
def bits(machine,pc,size,_):
 vals=[u.reg_read(UC_ARM64_REG_X0+i) for i in range(4)];writes.append(vals);ret()
u.hook_add(UC_HOOK_CODE,bits,begin=GAME+0x8a3af4,end=GAME+0x8a3af4)
stream=alloc(1024);packet=alloc(128);u.mem_write(packet,bytes(range(128)))
for index,bits_count in [(28,504),(29,544)]:
 target=GAME+int(expected[index]['value'],16)
 call(target,[stream,packet]);assert writes[-1]==[stream,packet,bits_count,1],writes[-1]
print('PACKET_SERIALIZERS_PASS',flush=True)
# Execute the real module installers, retaining their actual callbacks and original slots.
assert call(PAYLOAD+0x1538b8)==1
for index,slot,bits_count in [(28,0x2ccb78,504),(29,0x2ccb80,544)]:
 trampoline=ptr(PAYLOAD+slot);assert trampoline
 call(trampoline,[stream,packet]);assert writes[-1]==[stream,packet,bits_count,1]
print('PACKET_MODULE_INSTALLER_PASS',flush=True)
assert call(PAYLOAD+0x134874)==1
assert bytes(u.mem_read(PAYLOAD+0x2cb800,1))==b'\x01'
print('COMBAT_MODULE_INSTALLER_PASS',flush=True)
call(PAYLOAD+0x11a354)
assert bytes(u.mem_read(PAYLOAD+0x2a3478,1))==b'\x01'
print('NAMETAG_MODULE_INSTALLER_PASS',flush=True)
# Test the actual scale callback and ABI offsets on the scale state used by the game.
context=alloc(1024);original=alloc(16);backup=alloc(16);tls_record=alloc(32)
u.mem_write(original,struct.pack('<fB',0.25,0));u.mem_write(backup,struct.pack('<fB',0.75,1))
u.mem_write(tls_record,struct.pack('<QQf',original,backup,2.0));u.mem_write(context+0x58,struct.pack('<Q',backup))
slot=call(PAYLOAD+0x208098,[PAYLOAD+0x283298]);u.mem_write(slot,struct.pack('<Q',tls_record))
call(PAYLOAD+0x11a2bc,[context])
assert bytes(u.mem_read(original,5))==struct.pack('<fB',0.75,1)
assert bytes(u.mem_read(backup,4))==struct.pack('<f',1.5)
print('NAMETAG_SCALE_CALLBACK_PASS',flush=True)

# Exercise Dobby's instrumentation bridge at the recovered scale instruction.
scale_target=GAME+int(expected[59]['value'],16)
assert ptr(PAYLOAD+0x2a3488)
u.mem_write(original,struct.pack('<fB',0.25,0));u.mem_write(backup,struct.pack('<fB',0.75,1))
u.reg_write(UC_ARM64_REG_X8,backup);u.reg_write(UC_ARM64_REG_SP,0x3fff000);u.reg_write(UC_ARM64_REG_LR,STOP)
u.emu_start(scale_target,scale_target+16,timeout=10000000,count=0)
assert u.reg_read(UC_ARM64_REG_PC)==scale_target+16,hex(u.reg_read(UC_ARM64_REG_PC))
assert bytes(u.mem_read(original,5))==struct.pack('<fB',0.75,1)
assert bytes(u.mem_read(backup,4))==struct.pack('<f',1.5)
assert struct.pack('<I',u.reg_read(UC_ARM64_REG_S0))==struct.pack('<f',60.0)
print('NAMETAG_REAL_INSTRUMENTATION_PASS',flush=True)
installed=[]
for index in list(range(30,40)):
 e=expected[index];target=GAME+int(e['value'],16)+(0xac6000 if e['relative_to_libgame'] else 0)
 out=alloc(16);before=bytes(u.mem_read(target,16))
 result=call(PAYLOAD+0x1084f0,[target,PAYLOAD+0x153774,out])
 assert result==0 and ptr(out),(index,result)
 assert bytes(u.mem_read(target,16))!=before
 installed.append(index)
print('ALL_RECOVERED_FUNCTION_HOOKS_PASS',installed,flush=True)

# Execute the recovered distance instruction through the real instrumentation bridge.
u.mem_write(PAYLOAD+0x2a3670,b'\x01')
u.mem_write(PAYLOAD+0x283e74,struct.pack('<f',500.0))
distance_target=GAME+int(expected[56]['value'],16)
u.reg_write(UC_ARM64_REG_S0,struct.unpack('<I',struct.pack('<f',200.0))[0]);u.reg_write(UC_ARM64_REG_S1,struct.unpack('<I',struct.pack('<f',50.0))[0])
u.reg_write(UC_ARM64_REG_SP,0x3fff000);u.reg_write(UC_ARM64_REG_LR,STOP)
u.emu_start(distance_target,GAME+0x759d70,timeout=10000000,count=0)
assert u.reg_read(UC_ARM64_REG_PC)==GAME+0x759d70,hex(u.reg_read(UC_ARM64_REG_PC))
assert struct.pack('<I',u.reg_read(UC_ARM64_REG_S1))==struct.pack('<f',500.0)
print('NAMETAG_DISTANCE_INSTRUMENTATION_PASS',flush=True)

report={
 'apk_sha256':hashlib.file_digest(args.apk.open('rb'),'sha256').hexdigest(),
 'libgrand_sha256':hashlib.sha256(game).hexdigest(),
 'host_sha256':hashlib.sha256(host).hexdigest(),'payload_sha256':hashlib.sha256(payload).hexdigest(),
 'constructors_executed':ctors,'game_protector_constructor_executed':True,
 'recovered_offsets':60,'address_extents_and_elf_permissions_verified':True,
 'bullet_owner_and_data_setters_verified':True,'packet_serializers_bits':[504,544],
 'packet_module_installer_succeeded':True,'combat_module_installer_succeeded':True,
 'nametag_module_installer_succeeded':True,'nametag_scale_callback_verified':True,
 'nametag_real_scale_and_distance_instrumentation_verified':True,
 'additional_function_hooks_installed':installed,
 'license_predicate':license_ok,'profile_predicate':feature_ok,
 'android_device_tested':False,
 'limitations':['JNI/libc are mocked; background threads are recorded, not scheduled',
 'Only the game protector constructor is run; game JNI initialization and gameplay are not emulated',
 'The game load base and ELF metadata are supplied from the actual mapped ELF',
 'Additional rendering function hooks are installed with a probe callback; only relocation is verified for them']}
args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
