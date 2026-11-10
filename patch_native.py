import struct,re,ctypes,ctypes.util,json,zlib,base64
from pathlib import Path
R=Path(__file__).resolve().parent
def var(n):
 o=bytearray()
 while n>=128:o.append((n&127)|128);n>>=7
 return bytes(o)+bytes([n])
class Reader:
 def __init__(self,b,p=0):self.b=b;self.p=p
 def take(self,n):v=self.b[self.p:self.p+n];assert len(v)==n;self.p+=n;return v
 def u8(self):return self.take(1)[0]
 def vi(self):
  n=0;shift=0
  while True:
   v=self.u8();n|=(v&127)<<shift
   if v<128:return n
   shift+=7
 def u32(self):return struct.unpack('<I',self.take(4))[0]
class BC:
 def __init__(self,b):
  self.b=b;r=Reader(b,2);self.strings=[r.take(r.vi()) for _ in range(r.vi())];self.stringend=r.p
  while r.u8():r.vi()
  self.userdata=b[self.stringend:r.p];self.count=r.vi();self.fs=[]
  for i in range(self.count):
   st=r.p;header=r.take(5);ty=r.take(r.vi());codesize=r.vi();co=r.p;code=[r.u32() for _ in range(codesize)];nc=r.vi();kstart=r.p;ks=[]
   for _ in range(nc):
    t=r.u8();v=None
    if t==1:v=r.u8()
    elif t==2:v=r.take(8)
    elif t==3:v=r.vi()
    elif t==4:v=r.take(4)
    elif t==5:v=[r.vi() for _ in range(r.vi())]
    elif t==6:v=r.vi()
    elif t==7:v=r.take(16)
    elif t!=0:raise ValueError(t)
    ks.append((t,v))
   kend=r.p;ch=[r.vi() for _ in range(r.vi())];line=r.vi();name=r.vi();lio=r.p
   if r.u8():gap=r.u8();r.take(codesize);r.take((((codesize-1)>>gap)+1)*4)
   if r.u8():
    for _ in range(r.vi()):r.vi();r.vi();r.vi();r.u8()
    for _ in range(r.vi()):r.vi()
   self.fs.append(dict(raw=b[st:r.p],header=header,types=ty,code=code,ks=ks,kraw=b[kstart:kend],tail=b[kend:lio],children=ch,line=line,name=name))
  self.main=r.vi();assert r.p==len(b)
 def build(self,strings=None,overrides=None,extra=None,main=None):
  ss=self.strings if strings is None else strings;os=overrides or {};fs=[os.get(i,f['raw']) for i,f in enumerate(self.fs)]+(extra or [])
  return self.b[:2]+var(len(ss))+b''.join(var(len(x))+x for x in ss)+self.userdata+var(len(fs))+b''.join(fs)+var(self.main if main is None else main)

def op(name,a=0,b=0,c=0,d=None):
 oc={'JUMPXEQKS':80,'LOADB':3,'RETURN':22}[name]
 return oc*227%256 | (a<<8) | ((d&65535)<<16 if d is not None else b<<16|c<<24)
def packwords(xs):return struct.pack('<'+'I'*len(xs),*xs)
def patch(bc):
 ss=bc.strings[:];sid=len(ss)+1;ss.append(b'@Icon_Crack');over={}
 # 4 words: when the input differs, continue with the original validator.
 for i in [54,55]:
  f=bc.fs[i];kidx=len(f['ks']);guard=[op('JUMPXEQKS',a=0,d=3),0x80000000|kidx,op('LOADB',a=1,b=1),op('RETURN',a=1,b=2)]
  code=guard+f['code'];over[i]=f['header']+var(len(f['types']))+f['types']+var(len(code))+packwords(code)+var(kidx+1)+f['kraw']+b'\x03'+var(sid)+f['tail']+b'\0\0'
 for i,s in enumerate(ss):
  if s in [b'https://discord.gg/deltax',b'https://shop.deltaexploits.gg/?event=retard',b'https://deltaexploits.gg/delta-executor-android',b'https://deltaexploits.gg/delta-executor-ios']:ss[i]=b'https://t.me/Icon_Crack'
  elif s==b'KEY_example':ss[i]=b'@Icon_Crack'
  elif s.startswith(b'Thank you for using Delta <3'):ss[i]=b'cracked by @Icon_Crack\nhttps://t.me/Icon_Crack'
 return bc.build(strings=ss,overrides=over)

ORIGINAL_NATIVE_SHA256='fc3fd01754502ee1f001e190e7af2b760378bd20493c370a70f395d67484b554'
BLOB_OFFSET=0x2e08a9
BLOB_SIZE=56477

def cipher(data,encode=False):
 table=(R/'native_data/ui-cipher.bin').read_bytes();rots=table[:264];masks=table[264:]
 assert len(masks)==8448
 out=bytearray()
 for i,value in enumerate(data):
  n=rots[i%264]%8;m=masks[i%8448]
  if encode:
   value^=m;value=((value<<n)|(value>>((8-n)%8)))&255
  else:value=(((value>>n)|(value<<((8-n)%8)))&255)^m
  out.append(value)
 return bytes(out)

def zstd():
 lib=ctypes.CDLL(ctypes.util.find_library('zstd'))
 lib.ZSTD_getFrameContentSize.argtypes=[ctypes.c_void_p,ctypes.c_size_t];lib.ZSTD_getFrameContentSize.restype=ctypes.c_ulonglong
 lib.ZSTD_decompress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t];lib.ZSTD_decompress.restype=ctypes.c_size_t
 lib.ZSTD_compressBound.argtypes=[ctypes.c_size_t];lib.ZSTD_compressBound.restype=ctypes.c_size_t
 lib.ZSTD_compress.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_int];lib.ZSTD_compress.restype=ctypes.c_size_t
 return lib

def decompress(data):
 lib=zstd();n=lib.ZSTD_getFrameContentSize(data,len(data));assert 0<n<4000000
 out=ctypes.create_string_buffer(n);actual=lib.ZSTD_decompress(out,n,data,len(data));assert actual==n
 return out.raw

def decode_native(data):return decompress(cipher(data[BLOB_OFFSET:BLOB_OFFSET+BLOB_SIZE]))

def patch_native(data):
 import hashlib
 assert hashlib.sha256(data).hexdigest()==ORIGINAL_NATIVE_SHA256,'Unsupported original native library'
 original=decode_native(data);bc=BC(original);assert bc.build()==original
 patched=patch(bc);BC(patched)
 lib=zstd();out=ctypes.create_string_buffer(lib.ZSTD_compressBound(len(patched)))
 n=lib.ZSTD_compress(out,len(out),patched,len(patched),19)
 slack=BLOB_SIZE-n
 assert slack>=8,'Compressed data does not fit the original slot; use libzstd 1.5.7'
 compressed=out.raw[:n]+struct.pack('<II',0x184d2a50,slack-8)+bytes(slack-8)
 assert decompress(compressed)==patched
 encoded=cipher(compressed,encode=True);assert cipher(encoded)==compressed
 result=data[:BLOB_OFFSET]+encoded+data[BLOB_OFFSET+BLOB_SIZE:]
 assert decode_native(result)==patched and len(result)==len(data)
 return result

if __name__=='__main__':
 import argparse,hashlib
 ap=argparse.ArgumentParser(description='Patch the embedded Luau validators to accept @Icon_Crack locally.')
 ap.add_argument('original',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args()
 assert args.original.resolve()!=args.output.resolve()
 result=patch_native(args.original.read_bytes());args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_bytes(result)
 print(hashlib.sha256(result).hexdigest(),args.output)
