.class public final Lcom/iconcrack/Branding;
.super Ljava/lang/Object;

.field private static telegramAttempted:Z

# Telegram launch and Android caption; native licensing is handled separately.
.method private static tryOpenTelegram(Landroid/app/Activity;)Z
    .locals 3

    :try_start
    const-string v0, "https://t.me/Icon_Crack"
    invoke-static {v0}, Landroid/net/Uri;->parse(Ljava/lang/String;)Landroid/net/Uri;
    move-result-object v0
    new-instance v1, Landroid/content/Intent;
    const-string v2, "android.intent.action.VIEW"
    invoke-direct {v1, v2, v0}, Landroid/content/Intent;-><init>(Ljava/lang/String;Landroid/net/Uri;)V
    invoke-virtual {p0, v1}, Landroid/app/Activity;->startActivity(Landroid/content/Intent;)V
    :try_end
    .catch Ljava/lang/RuntimeException; {:try_start .. :try_end} :unavailable
    const/4 v0, 0x1
    return v0

    :unavailable
    move-exception v0
    const-string v0, "@Icon_Crack: https://t.me/Icon_Crack"
    const/4 v1, 0x1
    invoke-static {p0, v0, v1}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v0
    invoke-virtual {v0}, Landroid/widget/Toast;->show()V
    const/4 v0, 0x0
    return v0
.end method

.method public static attachCaption(Landroid/app/Activity;)V
    .locals 5

    invoke-virtual {p0}, Landroid/app/Activity;->getWindow()Landroid/view/Window;
    move-result-object v0
    invoke-virtual {v0}, Landroid/view/Window;->getDecorView()Landroid/view/View;
    move-result-object v0
    const-string v1, "icon_crack_attribution"
    invoke-virtual {v0, v1}, Landroid/view/View;->findViewWithTag(Ljava/lang/Object;)Landroid/view/View;
    move-result-object v0
    if-nez v0, :done

    new-instance v0, Landroid/widget/TextView;
    invoke-direct {v0, p0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V
    invoke-virtual {v0, v1}, Landroid/view/View;->setTag(Ljava/lang/Object;)V
    const-string v1, "cracked by @Icon_Crack"
    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V
    const/4 v1, -0x1
    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setTextColor(I)V
    const v1, 0x99000000
    invoke-virtual {v0, v1}, Landroid/view/View;->setBackgroundColor(I)V
    const/high16 v1, 0x41600000
    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setTextSize(F)V
    const/16 v1, 0xc
    invoke-virtual {v0, v1, v1, v1, v1}, Landroid/view/View;->setPadding(IIII)V
    const/4 v1, 0x0
    invoke-virtual {v0, v1}, Landroid/view/View;->setClickable(Z)V
    invoke-virtual {v0, v1}, Landroid/view/View;->setFocusable(Z)V
    new-instance v1, Landroid/widget/FrameLayout$LayoutParams;
    const/4 v2, -0x2
    const/16 v3, 0x55
    invoke-direct {v1, v2, v2, v3}, Landroid/widget/FrameLayout$LayoutParams;-><init>(III)V
    invoke-virtual {p0, v0, v1}, Landroid/app/Activity;->addContentView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V
    :done
    return-void
.end method

.method public static openTelegramOnce(Landroid/app/Activity;)Z
    .locals 4
    sget-boolean v0, Lcom/iconcrack/Branding;->telegramAttempted:Z
    if-nez v0, :skip
    const/4 v0, 0x1
    sput-boolean v0, Lcom/iconcrack/Branding;->telegramAttempted:Z
    :try_start_preferences
    const-string v0, "icon_crack_entry"
    const/4 v1, 0x0
    invoke-virtual {p0, v0, v1}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;
    move-result-object v0
    const-string v1, "telegram_opened"
    const/4 v2, 0x0
    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences;->getBoolean(Ljava/lang/String;Z)Z
    move-result v2
    if-nez v2, :skip
    invoke-interface {v0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v0
    const/4 v2, 0x1
    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;
    move-result-object v0
    invoke-interface {v0}, Landroid/content/SharedPreferences$Editor;->commit()Z
    move-result v0
    :try_end_preferences
    .catch Ljava/lang/RuntimeException; {:try_start_preferences .. :try_end_preferences} :preferences_failed
    if-eqz v0, :skip
    invoke-static {p0}, Lcom/iconcrack/Branding;->tryOpenTelegram(Landroid/app/Activity;)Z
    move-result v0
    return v0
    :preferences_failed
    move-exception v0
    :skip
    const/4 v0, 0x0
    return v0
.end method
