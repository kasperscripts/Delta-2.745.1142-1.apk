#!/usr/bin/env python3
"""Install a constructor trampoline that selects the embedded UI before file overrides."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import struct
from elftools.elf.elffile import ELFFile
from keystone import Ks, KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN

INPUT_SHA = '6d32e5290644e65f8f6722c6c924471aa7fce8ae2cc472273e591966694866d7'
PATCH_SITE = 0x849210
EMBEDDED_PATH = 0x849EB0
ORIGINAL_CTOR = 0x105CAC8
FIRST_INIT_SLOT = 0x1194860


def patch(data):
    assert hashlib.sha256(data).hexdigest() == INPUT_SHA, 'Unexpected fixed-key library'
    elf = ELFFile(io.BytesIO(data))
    segments = list(elf.iter_segments())
    load = [s for s in segments if s['p_type'] == 'PT_LOAD']
    address = (max(s['p_vaddr'] + s['p_memsz'] for s in load) + 16383) & ~16383
    offset = (len(data) + 16383) & ~16383
    trampoline = address + 0x100
    branch = 0x14000000 | (((trampoline - PATCH_SITE) >> 2) & 0x3FFFFFF)
    symbols = elf.get_section_by_name('.dynsym')
    plt = elf.get_section_by_name('.plt')['sh_addr'] + 32
    mprotect = next(plt + i * 16 for i, r in enumerate(elf.get_section_by_name('.rela.plt').iter_relocations()) if symbols.get_symbol(r['r_info_sym']).name == 'mprotect')
    asm = f'''
        stp x29, x30, [sp, #-32]!
        stp x19, x20, [sp, #16]
        mov x29, sp
        bl {ORIGINAL_CTOR}
        adrp x0, {PATCH_SITE & ~16383}
        mov x1, #16384
        mov w2, #7
        bl {mprotect}
        adrp x19, {PATCH_SITE & ~4095}
        add x19, x19, #{PATCH_SITE & 4095}
        movz w20, #{branch & 65535}
        movk w20, #{branch >> 16}, lsl #16
        str w20, [x19]
        dc cvau, x19
        dsb ish
        ic ivau, x19
        dsb ish
        isb
        adrp x0, {PATCH_SITE & ~16383}
        mov x1, #16384
        mov w2, #5
        bl {mprotect}
        ldp x19, x20, [sp, #16]
        ldp x29, x30, [sp], #32
        ret
    '''
    ks = Ks(KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN)
    code = bytes(ks.asm(asm, addr=address)[0])
    assert len(code) <= 0x100
    stub = bytes(ks.asm(f'str x25, [sp, #0x38]; stp xzr, xzr, [sp, #0xd0]; b {EMBEDDED_PATH}', addr=trampoline)[0])
    block = bytearray(4096)
    block[:len(code)] = code
    block[0x100:0x100 + len(stub)] = stub
    out = bytearray(data)
    note_index = next(i for i, s in enumerate(segments) if s['p_type'] == 'PT_NOTE')
    ph = elf['e_phoff'] + note_index * elf['e_phentsize']
    # The note bytes remain in the first LOAD. Its program-header slot becomes the new RX LOAD.
    struct.pack_into('<IIQQQQQQ', out, ph, 1, 5, offset, address, address, len(block), len(block), 16384)
    reloc = elf.get_section_by_name('.rela.dyn')
    found = False
    for i, r in enumerate(reloc.iter_relocations()):
        if r['r_offset'] == FIRST_INIT_SLOT:
            assert r['r_info_type'] == 1027 and r['r_addend'] == ORIGINAL_CTOR
            struct.pack_into('<Q', out, reloc['sh_offset'] + i * 24 + 16, address)
            found = True
    assert found
    out.extend(bytes(offset - len(out)))
    out.extend(block)
    meta = dict(entry=hex(address), file_offset=hex(offset), trampoline=hex(trampoline), patch_site=hex(PATCH_SITE), branch_word=hex(branch), embedded_path=hex(EMBEDDED_PATH), mprotect_plt=hex(mprotect))
    return bytes(out), meta


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--metadata', type=Path)
    args = ap.parse_args()
    assert args.source.resolve() != args.output.resolve()
    result, meta = patch(args.source.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    if args.metadata:
        args.metadata.write_text(json.dumps(meta, indent=2) + '\n')
    print(hashlib.sha256(result).hexdigest(), json.dumps(meta))
