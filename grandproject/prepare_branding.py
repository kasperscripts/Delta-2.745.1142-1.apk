#!/usr/bin/env python3
"""Apply the branding draft to an unpacked classes6.dex smali directory.

Input: directory containing com/grand/{loader,flutter} from this exact APK.
This prepares source only. Premium and integrity checks remain unresolved.
"""
import argparse
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
STARTUP = 'com/grand/loader/LdrStartupActivity.smali'
MAIN = 'com/grand/flutter/MainActivity.smali'
HELPER = 'com/iconcrack/Branding.smali'


def patch(root):
    startup = root / STARTUP
    main = root / MAIN
    a, b = startup.read_text(), main.read_text()
    if 'iconCrackTelegramShown' in a or 'Lcom/iconcrack/Branding;' in b:
        raise ValueError('Branding is already present; use a fresh disassembly')
    marker = '.field private launched:Z'
    assert a.count(marker) == 1
    a = a.replace(marker, marker + '\n\n.field private iconCrackTelegramShown:Z')
    marker = '    invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V'
    assert a.count(marker) == 1
    a = a.replace(marker, marker + '''

    if-eqz p1, :icon_crack_restore_done
    const-string v0, "icon_crack.telegram_shown"
    const/4 v1, 0x0
    invoke-virtual {p1, v0, v1}, Landroid/os/Bundle;->getBoolean(Ljava/lang/String;Z)Z
    move-result v0
    iput-boolean v0, p0, Lcom/grand/loader/LdrStartupActivity;->iconCrackTelegramShown:Z
    :icon_crack_restore_done
''')
    assert '.method protected onPostResume()V' not in a
    assert 'onSaveInstanceState(' not in a
    a += '''
.method protected onPostResume()V
    .locals 1
    invoke-super {p0}, Landroid/app/Activity;->onPostResume()V
    invoke-static {p0}, Lcom/iconcrack/Branding;->attachCaption(Landroid/app/Activity;)V
    iget-boolean v0, p0, Lcom/grand/loader/LdrStartupActivity;->iconCrackTelegramShown:Z
    if-nez v0, :done
    const/4 v0, 0x1
    iput-boolean v0, p0, Lcom/grand/loader/LdrStartupActivity;->iconCrackTelegramShown:Z
    invoke-static {p0}, Lcom/iconcrack/Branding;->openTelegram(Landroid/app/Activity;)V
    :done
    return-void
.end method

.method protected onSaveInstanceState(Landroid/os/Bundle;)V
    .locals 2
    const-string v0, "icon_crack.telegram_shown"
    iget-boolean v1, p0, Lcom/grand/loader/LdrStartupActivity;->iconCrackTelegramShown:Z
    invoke-virtual {p1, v0, v1}, Landroid/os/Bundle;->putBoolean(Ljava/lang/String;Z)V
    invoke-super {p0, p1}, Landroid/app/Activity;->onSaveInstanceState(Landroid/os/Bundle;)V
    return-void
.end method
'''
    marker = '    invoke-static {p0}, Lcom/grand/flutter/ImGuiOverlay;->start(Landroid/app/Activity;)V'
    assert b.count(marker) == 1
    b = b.replace(marker, marker + '\n\n    invoke-static {p0}, Lcom/iconcrack/Branding;->attachCaption(Landroid/app/Activity;)V')
    # Validate all anchors before writing any input file.
    (root / HELPER).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HERE / 'smali' / HELPER, root / HELPER)
    startup.write_text(a)
    main.write_text(b)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('smali_root', type=Path)
    args = parser.parse_args()
    patch(args.smali_root)
    print('Prepared Telegram launch and attribution draft; premium is unresolved.')
