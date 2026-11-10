#!/usr/bin/env python3
"""Try forced launch success and synthetic premium replies using only the APK.

Requires unicorn==2.1.4 and pyelftools==0.33. No Android device or network is used.
This is a native consumer experiment, not an installable APK or premium unlock.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('apk', type=Path)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
original_hash = hashlib.file_digest(args.apk.open('rb'), 'sha256').hexdigest()
assert original_hash == '5a7a7d388c0fb24578bf23c375abaeb4f175991e28c340ae323c0d34f157a2b2'
os.environ['GRANDPROJECT_APK'] = str(args.apk.resolve())
import native_harness as h
from unicorn import UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0, UC_ARM64_REG_SP, UC_ARM64_REG_LR, UC_ARM64_REG_PC

ctors = h.initialize()
u = h.u
baseline = [(a, bytes(u.mem_read(a, n))) for a, n in [(0, 0x1000000), (0x2000000, 0x2000000), (0x4000000, 0x200000)]]
baseline_heap = h.heap


def reset():
    for a, value in baseline:
        u.mem_write(a, value)
    u.ctl_remove_cache(0, 0x1000000)
    h.heap = baseline_heap


def ptr(a):
    return struct.unpack('<Q', bytes(u.mem_read(a, 8)))[0]


def put_string(value):
    data = value.encode() + b'\0'
    a = h.alloc(len(data))
    u.mem_write(a, data)
    return a


def prepare_rpc():
    op, request, out, error = put_string('premium.offsets'), put_string('{}'), h.alloc(16), h.alloc(1024)
    # Model a cached grant so that the native consumer reaches the transport.
    # No real token is used, and no server is contacted.
    value = b'offline-test-token'
    u.mem_write(0x883160, bytes([len(value) * 2]) + value + bytes(23 - len(value)))
    u.mem_write(0x883150, struct.pack('<Q', 0x7fffffffffffffff))
    return [op, request, 2, out, out + 8, error, 1024]


def run_rpc(response=None):
    reset()
    params = prepare_rpc()
    transport_calls = []
    handle = None
    if response is not None:
        # Construct a genuine native JSON object with the original parser.
        data = json.dumps(response, separators=(',', ':'))
        setup = params.copy()
        setup[1:3] = [put_string(data), len(data.encode())]
        for i, value in enumerate(setup):
            u.reg_write(UC_ARM64_REG_X0 + i, value)
        u.reg_write(UC_ARM64_REG_SP, 0x3fff000)
        u.reg_write(UC_ARM64_REG_LR, h.STOP)
        u.emu_start(0x50f174, 0x50f204, count=10000000)
        assert u.reg_read(UC_ARM64_REG_PC) == 0x50f204
        obj = bytes(u.mem_read(u.reg_read(UC_ARM64_REG_SP) + 0x170, 16))
        assert obj[0] == 1

        def simulated_transport(machine, pc, size, user):
            a = [machine.reg_read(UC_ARM64_REG_X0 + i) for i in range(7)]
            transport_calls.append(h.s(a[1]))
            machine.mem_write(a[3], obj)
            machine.mem_write(a[6], b'\1')  # Simulated authenticated reply.
            h.ret(1)

        handle = u.hook_add(UC_HOOK_CODE, simulated_transport, begin=0x514280, end=0x514280)
    try:
        result = h.call(0x50f174, params)
        return {'response': response, 'native_return': result, 'output_pointer': hex(ptr(params[3])),
                'output_bytes': ptr(params[4]), 'error': h.s(params[5]),
                'simulated_transport_calls': transport_calls}
    finally:
        if handle is not None:
            u.hook_del(handle)


initial = h.call(0x483984)
h.call(0x4a087c)  # Original setup of the loader drawing callback.
callback = ptr(0x882ac8)
original = bytes(u.mem_read(0x483984, 8))
u.mem_write(0x483984, bytes.fromhex('20008052c0035fd6'))  # mov w0,1; ret
u.ctl_remove_cache(0x483984, 0x483990)
forced = h.call(0x483984)
callback_forced = ptr(0x882ac8)
u.mem_write(0x483984, original)
u.ctl_remove_cache(0x483984, 0x483990)
u.mem_write(0x87a8d0, struct.pack('<I', 1))
state_override = h.call(0x483984)
callback_override = ptr(0x882ac8)
assert initial == 0 and forced == state_override == 1
assert callback == callback_forced == callback_override == 0x49fb70

cases = [run_rpc(), run_rpc({}), run_rpc({'enabled': True, 'premium': True}),
         run_rpc({'profile': '', 'signature': ''})]
assert all(c['native_return'] == 0 and c['output_bytes'] == 0 and c['output_pointer'] == '0x0' for c in cases)
assert cases[0]['error'] == 'Dev HTTP session required'
assert all(c['error'] == 'invalid signed Grand+ offset profile' for c in cases[1:])
report = {'apk_sha256': original_hash, 'original_constructors_executed': ctors,
          'experiment': 'isolated ARM64 emulation; original JSON parser and RPC response consumer',
          'initial_native_state': initial, 'patched_native_state': forced,
          'global_state_override': state_override,
          'original_draw_callback': hex(callback), 'callback_after_both_overrides': hex(callback_override),
          'rpc_cases': cases, 'network_access_performed': False, 'premium_unlocked': False,
          'limitations': ['No Android device or complete app lifecycle tested',
                          'Synthetic replies do not model every possible server response',
                          'Experiments do not prove that all other bypasses are impossible']}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
