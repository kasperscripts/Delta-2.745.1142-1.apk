Compile and run the helper extracted from the built DEX:

```sh
# JADX --no-res -d dex-review classes6.dex
mkdir -p grandproject/probes/telegram-jvm/com/iconcrack
cp dex-review/sources/com/iconcrack/Branding.java grandproject/probes/telegram-jvm/com/iconcrack/
java grandproject/probes/telegram-jvm/Compile.java grandproject/probes/telegram-jvm
java -cp grandproject/probes/telegram-jvm Probe
```

These Android stubs test the actual decompiled helper, not the full Android lifecycle.
