#!/usr/bin/env python3
"""Patch the exact original classes6 smali: persistent Telegram mark and deferred native activation."""
from pathlib import Path
import argparse, shutil
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('smali_root',type=Path)
ROOT=parser.parse_args().smali_root
startup=ROOT/'com/grand/loader/LdrStartupActivity.smali'
a=startup.read_text();assert 'iconCrack' not in a
for name in ['iconCrackRedirectPending','iconCrackWasPaused','iconCrackNativeStarted']:
 a=a.replace('.field private launched:Z','.field private '+name+':Z\n\n.field private launched:Z',1)
start=a.index('.method public onCreate(Landroid/os/Bundle;)V');end=a.index('.end method',start)+len('.end method')
body=a[start:end].replace('.method public onCreate(Landroid/os/Bundle;)V','.method private startNativeGate(Landroid/os/Bundle;)V',1)
body=body.replace('    invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V','''    iget-boolean v0, p0, Lcom/grand/loader/LdrStartupActivity;->iconCrackNativeStarted:Z
    if-nez v0, :icon_gate_return
    const/4 v0, 0x1
    iput-boolean v0, p0, Lcom/grand/loader/LdrStartupActivity;->iconCrackNativeStarted:Z''',1)
assert body.count('    return-void')==1
body=body.replace('    return-void','    :icon_gate_return\n    return-void')
new='''.method public onCreate(Landroid/os/Bundle;)V
    .locals 3
    invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V
    new-instance v0, Landroid/widget/TextView;
    invoke-direct {v0, p0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V
    const-string v1, "GrandProject\\ncracked by @Icon_Crack"
    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V
    const/4 v1, -0x1
    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setTextColor(I)V
    const/high16 v1, -0x1000000
    invoke-virtual {v0, v1}, Landroid/view/View;->setBackgroundColor(I)V
    const/high16 v1, 0x41900000
    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setTextSize(F)V
    const/16 v1, 0x18
    invoke-virtual {v0, v1, v1, v1, v1}, Landroid/view/View;->setPadding(IIII)V
    invoke-virtual {p0, v0}, Lcom/grand/loader/LdrStartupActivity;->setContentView(Landroid/view/View;)V
    invoke-static {p0}, Lcom/iconcrack/Branding;->openTelegramOnce(Landroid/app/Activity;)Z
    move-result v0
    iput-boolean v0, p0, Lcom/grand/loader/LdrStartupActivity;->iconCrackRedirectPending:Z
    return-void
.end method

'''
a=a[:start]+new+body+a[end:]
pause='.method protected onPause()V\n    .locals 1'
assert a.count(pause)==1
a=a.replace(pause,pause+'''
    const/4 v0, 0x1
    iput-boolean v0, p0, Lcom/grand/loader/LdrStartupActivity;->iconCrackWasPaused:Z
''')
a+='''
.method protected onPostResume()V
    .locals 1
    invoke-super {p0}, Landroid/app/Activity;->onPostResume()V
    invoke-virtual {p0}, Landroid/app/Activity;->isFinishing()Z
    move-result v0
    if-nez v0, :done
    invoke-virtual {p0}, Landroid/app/Activity;->isDestroyed()Z
    move-result v0
    if-nez v0, :done
    iget-boolean v0, p0, Lcom/grand/loader/LdrStartupActivity;->iconCrackRedirectPending:Z
    if-eqz v0, :start_gate
    iget-boolean v0, p0, Lcom/grand/loader/LdrStartupActivity;->iconCrackWasPaused:Z
    if-eqz v0, :done
    const/4 v0, 0x0
    iput-boolean v0, p0, Lcom/grand/loader/LdrStartupActivity;->iconCrackRedirectPending:Z
    :start_gate
    const/4 v0, 0x0
    invoke-direct {p0, v0}, Lcom/grand/loader/LdrStartupActivity;->startNativeGate(Landroid/os/Bundle;)V
    invoke-static {p0}, Lcom/iconcrack/Branding;->attachCaption(Landroid/app/Activity;)V
    :done
    return-void
.end method
'''
startup.write_text(a)
app=ROOT/'com/grand/flutter/GrandMobileApp.smali';a=app.read_text();marker='''    const-string v0, "grnd"

    invoke-static {v0}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V
''';assert a.count(marker)==1;a=a.replace(marker,'',1);app.write_text(a)
main=ROOT/'com/grand/flutter/MainActivity.smali';a=main.read_text();marker='    invoke-static {p0}, Lcom/grand/flutter/ImGuiOverlay;->start(Landroid/app/Activity;)V';assert a.count(marker)==1;main.write_text(a.replace(marker,marker+'\n    invoke-static {p0}, Lcom/iconcrack/Branding;->attachCaption(Landroid/app/Activity;)V'))

marker='    const-string v0, "grand"\n\n    invoke-static {v0}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V'
a=main.read_text();assert a.count(marker)==1
main.write_text(a.replace(marker,marker+'\n\n    const-string v0, "iconpayload"\n\n    invoke-static {v0}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V',1))
helper=ROOT/'com/iconcrack/Branding.smali';helper.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(Path(__file__).resolve().parent/'smali/com/iconcrack/Branding.smali',helper)
print('Prepared persistent Telegram mark and deferred native activation.')
