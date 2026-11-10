"""Create a local module bootstrap and bypass the license predicate for one exact build; keep the address-profile guard."""
import io,struct,hashlib,ctypes,ctypes.util,json,sys
from pathlib import Path
from elftools.elf.elffile import ELFFile
from keystone import Ks,KS_ARCH_ARM64,KS_MODE_LITTLE_ENDIAN
R=Path(__file__).resolve().parent;ks=Ks(KS_ARCH_ARM64,KS_MODE_LITTLE_ENDIAN)
xx=ctypes.CDLL(ctypes.util.find_library('xxhash'));xx.XXH32.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_uint];xx.XXH32.restype=ctypes.c_uint
A=lambda code,pc:bytes(ks.asm(code,addr=pc)[0])
def sso(value):
 b=value.encode();assert len(b)<=22;return bytes([len(b)*2])+b+bytes(23-len(b))
def patch(raw,kind):
 expected={'host':'23db7a5e36f3b560f6804f9f7aa4a44c0855d39b6d2b5d4de89daebdd9fdba42','payload':'df0c6703838a3e4eb3676108b054e89e1c3183d3148a861ec219454fdfa5c1a4'}[kind]
 assert hashlib.sha256(raw).hexdigest()==expected
 e=ELFFile(io.BytesIO(raw));segs=list(e.iter_segments());dyn=next(s for s in segs if s['p_type']=='PT_DYNAMIC');tags={t.entry.d_tag:t.entry.d_val for t in dyn.iter_tags()};sy=list(dyn.iter_symbols())
 conv=lambda a:next(a-s['p_vaddr']+s['p_offset'] for s in segs if s['p_type']=='PT_LOAD' and s['p_vaddr']<=a<s['p_vaddr']+s['p_filesz'])
 rels=[]
 for start,size in [(tags['DT_RELA'],tags['DT_RELASZ']),(tags['DT_JMPREL'],tags['DT_PLTRELSZ'])]:
  for a in range(conv(start),conv(start)+size,24):
   target,info,v=struct.unpack_from('<QQq',raw,a);rels.append((a,target,info,v))
 first_slot=tags['DT_INIT_ARRAY'];last_slot=first_slot+tags['DT_INIT_ARRAYSZ']-8
 first=next(x for x in rels if x[1]==first_slot);last=next(x for x in rels if x[1]==last_slot)
 addr=(max(s['p_vaddr']+s['p_memsz'] for s in segs if s['p_type']=='PT_LOAD')+16383)&~16383
 off=(len(raw)+16383)&~16383
 post=addr+0x100;worker=addr+0x800;rpc=addr+0xa00;table=addr+0x1000
 plt={'host':{'mprotect':0x742210,'dlopen':0x742a20,'dlsym':0x7421f0},'payload':{'mprotect':0x212260}}[kind]
 # Resolve mprotect directly from the PLT relocations to avoid assumptions about its index.
 from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
 cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM);cs.detail=True
 got={target:sy[info>>32].name for _,target,info,v in rels if (info&0xffffffff)==1026}
 for s in segs:
  if s['p_type']=='PT_LOAD' and s['p_flags']&1:
   start=s['p_vaddr'];data=s.data()
   for i in range(0,len(data)-16,4):
    w=struct.unpack_from('<I',data,i)[0]
    if w&0x9f00001f !=0x90000010:continue
    ins=list(cs.disasm(data[i:i+16],start+i))
    if len(ins)>1 and ins[0].mnemonic=='adrp' and ins[1].mnemonic=='ldr' and ins[1].op_str.startswith('x17, [x16'):
     target=ins[0].operands[1].imm+ins[1].operands[1].mem.disp
     if target in got:plt[got[target]]=start+i
 assert 'mprotect' in plt
 # Change the final constructor relocation; GNU_RELRO is never written at runtime.
 pre=b''
 patches=[]
 def put(a,b):patches.append((a,bytes(b)))
 def asm(a,c):put(a,A(c,a))
 def string(a,old,new):
  assert len(new.encode())<=len(old.encode());put(a,new.encode()+bytes(len(old.encode())+1-len(new.encode())))
 if kind=='host':
  asm(0x47a998,f'b {worker}')
  asm(0x50f174,f'b {rpc}')
  # Loader's visible Telegram link (decrypted constructor data).
  for at in [0x7fd9a0,0x8783d0]:string(at,'https://t.me/grndproject','https://t.me/Icon_Crack')
  loadername=addr+0xc00;exportname=addr+0xc30
  worker_code=A(f'''
   stp x29,x30,[sp,#-64]!
   stp x19,x20,[sp,#16]
   stp x21,x22,[sp,#32]
   mov x29,sp
   sub sp,sp,#0x800
   bl 0x49a514
   mov x1,x0
   adrp x19,0x87a000
   ldr x0,[x19,#0x8d8]
   add x8,x19,#0x8f8
   bl 0x4f7c1c
   adrp x0,{loadername&~4095}
   add x0,x0,#{loadername&4095}
   mov w1,#2
   bl {plt['dlopen']}
   cbz x0,fail
   adrp x1,{exportname&~4095}
   add x1,x1,#{exportname&4095}
   bl {plt['dlsym']}
   cbz x0,fail
   mov x20,x0
   add x0,x19,#0x8f8
   mov x1,sp
   mov w2,#0x800
   blr x20
   cbnz w0,fail
   mov w8,#1
   b finished
   fail: mov w8,#-1
   finished:
   add x19,x19,#0x8d0
   stlr w8,[x19]
   mov x0,xzr
   add sp,sp,#0x800
   ldp x21,x22,[sp,#32]
   ldp x19,x20,[sp,#16]
   ldp x29,x30,[sp],#64
   ret
  ''',worker)
  assert len(worker_code)<0x200
  # No license service transport in the local build. Output buffers are initialized.
  rpc_code=A('cbz x3,skip1;str xzr,[x3];skip1:cbz x4,skip2;str xzr,[x4];skip2:cbz x5,done;cbz x6,done;strb wzr,[x5];done:mov w0,wzr;ret',rpc)
 else:
  worker_code=b'';rpc_code=b''
  # Stop license polling and Telegram account activation workers.
  for a in [0x189938,0x198dc4,0x198f74]:asm(a,'ret')
  # Local license predicate used by the menu. The address-profile predicate is retained.
  for a in [0x19a6c4]:asm(a,'mov w0,#1;ret')
  # Local profile uses no server token. Offsets are left absent, not fabricated.
  profile=bytearray(0x8d)
  for i,value in enumerate(['@Icon_Crack','@Icon_Crack','','','']):profile[i*24:(i+1)*24]=sso(value)
  struct.pack_into('<Q',profile,0x78,4102444800000)
  profile[0x88]=1
  put(0x2cda80,profile)
  for a in [0x2cd990,0x2cd998]:put(a,struct.pack('<Q',0x7fffffffffffffff))
  string(0x26cdb0,'t.me/grndproject','@Icon_Crack')
  string(0x26d1a6,'grand project!','@Icon_Crack')
  string(0x26a355,'GRAND PROJECT / 62.30 / Android arm64 / Developer log','cracked by @Icon_Crack / Developer log')
  string(0x26ae58,'Grand Project developer log','cracked by @Icon_Crack')
  string(0x283fa2,'Grand Project logs','@Icon_Crack logs')
  # Reuse a long visible label, preserving addresses and terminating its new text.
  string(0x28fe48,'Лицензия активна','cracked by @Icon_Crack')
  string(0x290ffd,'Лицензия активна','cracked by @Icon_Crack')
 records=bytearray();data=bytearray();data_start=table+24*(len(patches)+1)
 for a,b in patches:
  records+=struct.pack('<QQQ',a,len(b),data_start+len(data));data+=b
 records+=bytes(24)
 text_end=(segs[1]['p_memsz']+16383)&~16383
 post_code=A(f'''
  stp x29,x30,[sp,#-64]!
  stp x19,x20,[sp,#16]
  stp x21,x22,[sp,#32]
  stp x23,x24,[sp,#48]
  mov x29,sp
  bl {last[3]}
  adrp x19,{addr&~4095}
  add x19,x19,#{addr&4095}
  movz x20,#{addr&65535}
  movk x20,#{addr>>16},lsl #16
  sub x19,x19,x20
  mov x0,x19
  movz x1,#{text_end&65535}
  movk x1,#{text_end>>16},lsl #16
  mov w2,#7
  bl {plt['mprotect']}
  cbnz w0,finish
  adrp x20,{table&~4095}
  add x20,x20,#{table&4095}
  next_patch:
  ldp x21,x22,[x20]
  ldr x23,[x20,#16]
  add x20,x20,#24
  cbz x22,flush
  add x21,x21,x19
  add x23,x23,x19
  copy:
  ldrb w24,[x23],#1
  strb w24,[x21],#1
  subs x22,x22,#1
  b.ne copy
  b next_patch
  flush:
  mov x20,x19
  movz x21,#{text_end&65535}
  movk x21,#{text_end>>16},lsl #16
  add x21,x21,x19
  flush_data:
  dc cvau,x20
  add x20,x20,#64
  cmp x20,x21
  b.lo flush_data
  dsb ish
  mov x20,x19
  flush_instruction:
  ic ivau,x20
  add x20,x20,#64
  cmp x20,x21
  b.lo flush_instruction
  dsb ish
  isb
  mov x0,x19
  movz x1,#{text_end&65535}
  movk x1,#{text_end>>16},lsl #16
  mov w2,#5
  bl {plt['mprotect']}
  finish:
  ldp x23,x24,[sp,#48]
  ldp x21,x22,[sp,#32]
  ldp x19,x20,[sp,#16]
  ldp x29,x30,[sp],#64
  ret
 ''',post)
 assert len(post_code)<0x700
 block=bytearray(0x1000);block[:len(pre)]=pre;block[0x100:0x100+len(post_code)]=post_code
 block[0x800:0x800+len(worker_code)]=worker_code;block[0xa00:0xa00+len(rpc_code)]=rpc_code
 if kind=='host':
  for offset,value in [(0xc00,b'libiconpayload.so\0'),(0xc30,b'grand_payload_activate\0')]:block[offset:offset+len(value)]=value
 block+=records+data
 out=bytearray(raw);note=next(i for i,s in enumerate(segs) if s['p_type']=='PT_NOTE')
 struct.pack_into('<IIQQQQQQ',out,e['e_phoff']+note*56,1,5,off,addr,addr,len(block),len(block),16384)
 struct.pack_into('<Q',out,last[0]+16,post)
 # Protector binds a seeded XXH32 to its metadata and normalized program headers.
 ph=e['e_phoff'];meta=ph-88;hash_value=xx.XXH32(bytes(out[meta:ph-8]),80,0xe00cb63a)
 for i,s in enumerate(segs):
  item=bytearray(out[ph+i*56:ph+(i+1)*56])
  if i==9 or s['p_type']=='PT_PHDR':item[8:16]=bytes(8)
  hash_value=xx.XXH32(bytes(item),56,hash_value)
 struct.pack_into('<I',out,ph-4,hash_value)
 out+=bytes(off-len(out))+block
 return bytes(out),{'kind':kind,'new_segment':hex(addr),'offset':hex(off),'first_ctor_original':hex(first[3]),'last_ctor_wrapper':hex(post),'post':hex(post),'worker':hex(worker),'rpc':hex(rpc),'mprotect':hex(plt['mprotect']),'patches':[{'address':hex(a),'size':len(b),'sha256':hashlib.sha256(b).hexdigest()} for a,b in patches]}
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('host_original',type=Path);ap.add_argument('payload_original',type=Path);ap.add_argument('output_directory',type=Path)
 args=ap.parse_args();args.output_directory.mkdir(parents=True,exist_ok=True);report=[]
 for kind,source,dest in [('host',args.host_original,'libgrnd.so'),('payload',args.payload_original,'libiconpayload.so')]:
  out,meta=patch(source.read_bytes(),kind);(args.output_directory/dest).write_bytes(out);meta['sha256']=hashlib.sha256(out).hexdigest();report.append(meta)
 (args.output_directory/'local-patches.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
