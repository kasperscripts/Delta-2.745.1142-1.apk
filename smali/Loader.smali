.class public Lcom/roblox/gloop/Loader;
.super Ljava/lang/Object;
.source "Loader.java"

# interfaces
.implements Landroid/view/View$OnLayoutChangeListener;


# static fields
.field private static instance:Lcom/roblox/gloop/Loader;


# instance fields
.field private activity:Landroid/app/Activity;


# direct methods
.method static constructor <clinit>()V
    .locals 0

    return-void
.end method

.method private constructor <init>()V
    .locals 0

    .line 26
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method public static declared-synchronized get()Lcom/roblox/gloop/Loader;
    .locals 2

    const-class v0, Lcom/roblox/gloop/Loader;

    monitor-enter v0

    .line 33
    :try_start_0
    sget-object v1, Lcom/roblox/gloop/Loader;->instance:Lcom/roblox/gloop/Loader;

    if-nez v1, :cond_0

    .line 34
    new-instance v1, Lcom/roblox/gloop/Loader;

    invoke-direct {v1}, Lcom/roblox/gloop/Loader;-><init>()V

    sput-object v1, Lcom/roblox/gloop/Loader;->instance:Lcom/roblox/gloop/Loader;

    .line 36
    :cond_0
    sget-object v1, Lcom/roblox/gloop/Loader;->instance:Lcom/roblox/gloop/Loader;
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    monitor-exit v0

    return-object v1

    .line 32
    :catchall_0
    move-exception v1

    monitor-exit v0

    throw v1
.end method

.method public static native getDownloadUrl()Ljava/lang/String;
.end method

.method static synthetic lambda$openWebsite$0(Lcom/roblox/gloop/Loader;Ljava/lang/String;)V
    .locals 4
    .param p0, "this_"    # Lcom/roblox/gloop/Loader;
    .param p1, "url"    # Ljava/lang/String;

    .line 17
    iget-object v0, p0, Lcom/roblox/gloop/Loader;->activity:Landroid/app/Activity;

    new-instance v1, Landroid/content/Intent;

    .line 20
    invoke-static {p1}, Landroid/net/Uri;->parse(Ljava/lang/String;)Landroid/net/Uri;

    move-result-object v2

    const-string v3, "android.intent.action.VIEW"

    invoke-direct {v1, v3, v2}, Landroid/content/Intent;-><init>(Ljava/lang/String;Landroid/net/Uri;)V

    .line 17
    invoke-virtual {v0, v1}, Landroid/app/Activity;->startActivity(Landroid/content/Intent;)V

    .line 23
    return-void
.end method

.method private native nativeContext(Landroid/content/Context;)Z
.end method

.method private native nativeResize(II)V
.end method

.method public static native nativeStart(Landroid/app/Activity;Lcom/roblox/gloop/Loader;)I
.end method


# virtual methods
.method public declared-synchronized attachContext(Landroid/content/Context;)V
    .locals 2
    .param p1, "_context"    # Landroid/content/Context;

    monitor-enter p0

    .line 13
    :try_start_0
    invoke-direct {p0, p1}, Lcom/roblox/gloop/Loader;->nativeContext(Landroid/content/Context;)Z

    move-result v0
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    if-eqz v0, :cond_0

    .line 16
    monitor-exit p0

    return-void

    .line 14
    :cond_0
    :try_start_1
    new-instance v0, Ljava/lang/RuntimeException;

    const-string v1, "context returned false."

    invoke-direct {v0, v1}, Ljava/lang/RuntimeException;-><init>(Ljava/lang/String;)V

    throw v0

    .line 12
    .end local p0    # "this":Lcom/roblox/gloop/Loader;
    .end local p1    # "_context":Landroid/content/Context;
    :catchall_0
    move-exception p1

    monitor-exit p0
    :try_end_1
    .catchall {:try_start_1 .. :try_end_1} :catchall_0

    throw p1
.end method

.method public getClipboard()Ljava/lang/String;
    .locals 4

    .line 78
    :try_start_0
    new-instance v0, Ljava/util/concurrent/FutureTask;

    new-instance v1, Lcom/roblox/gloop/Loader$$ExternalSyntheticLambda0;

    invoke-direct {v1, p0}, Lcom/roblox/gloop/Loader$$ExternalSyntheticLambda0;-><init>(Lcom/roblox/gloop/Loader;)V

    invoke-direct {v0, v1}, Ljava/util/concurrent/FutureTask;-><init>(Ljava/util/concurrent/Callable;)V

    .line 86
    .local v0, "futureTask":Ljava/util/concurrent/FutureTask;, "Ljava/util/concurrent/FutureTask<Ljava/lang/String;>;"
    iget-object v1, p0, Lcom/roblox/gloop/Loader;->activity:Landroid/app/Activity;

    invoke-virtual {v1, v0}, Landroid/app/Activity;->runOnUiThread(Ljava/lang/Runnable;)V

    .line 88
    invoke-virtual {v0}, Ljava/util/concurrent/FutureTask;->get()Ljava/lang/Object;

    move-result-object v1

    check-cast v1, Ljava/lang/String;
    :try_end_0
    .catch Ljava/lang/InterruptedException; {:try_start_0 .. :try_end_0} :catch_1
    .catch Ljava/util/concurrent/ExecutionException; {:try_start_0 .. :try_end_0} :catch_0

    return-object v1

    .line 89
    .end local v0    # "futureTask":Ljava/util/concurrent/FutureTask;, "Ljava/util/concurrent/FutureTask<Ljava/lang/String;>;"
    :catch_0
    move-exception v0

    goto :goto_0

    :catch_1
    move-exception v0

    .line 90
    .local v0, "e":Ljava/lang/Exception;
    :goto_0
    const-string v1, "Failed to get clipboard."

    invoke-virtual {p0, v1}, Lcom/roblox/gloop/Loader;->showToast(Ljava/lang/String;)V

    .line 91
    const-string v1, "Failed to get clipboard: "

    invoke-virtual {v0}, Ljava/lang/Exception;->getCause()Ljava/lang/Throwable;

    move-result-object v2

    const-string v3, "Loader"

    invoke-static {v3, v1, v2}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    .line 92
    const-string v1, ""

    return-object v1
.end method

.method synthetic lambda$getClipboard$2$com-roblox-gloop-Loader()Ljava/lang/String;
    .locals 5
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 82
    iget-object v0, p0, Lcom/roblox/gloop/Loader;->activity:Landroid/app/Activity;

    const-string v1, "clipboard"

    invoke-virtual {v0, v1}, Landroid/app/Activity;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;

    move-result-object v0

    check-cast v0, Landroid/content/ClipboardManager;

    .line 83
    .local v0, "clipboardManager":Landroid/content/ClipboardManager;
    if-eqz v0, :cond_1

    invoke-virtual {v0}, Landroid/content/ClipboardManager;->hasPrimaryClip()Z

    move-result v1

    if-eqz v1, :cond_1

    invoke-virtual {v0}, Landroid/content/ClipboardManager;->getPrimaryClipDescription()Landroid/content/ClipDescription;

    move-result-object v1

    move-object v2, v1

    .local v2, "primaryClipDescription":Landroid/content/ClipDescription;
    if-eqz v1, :cond_1

    const-string v1, "text/plain"

    invoke-virtual {v2, v1}, Landroid/content/ClipDescription;->hasMimeType(Ljava/lang/String;)Z

    move-result v1

    if-eqz v1, :cond_1

    invoke-virtual {v0}, Landroid/content/ClipboardManager;->getPrimaryClip()Landroid/content/ClipData;

    move-result-object v1

    move-object v3, v1

    .local v3, "primaryClip":Landroid/content/ClipData;
    if-eqz v1, :cond_1

    invoke-virtual {v3}, Landroid/content/ClipData;->getItemCount()I

    move-result v1

    if-lez v1, :cond_1

    const/4 v1, 0x0

    invoke-virtual {v3, v1}, Landroid/content/ClipData;->getItemAt(I)Landroid/content/ClipData$Item;

    move-result-object v1

    invoke-virtual {v1}, Landroid/content/ClipData$Item;->getText()Ljava/lang/CharSequence;

    move-result-object v1

    move-object v4, v1

    .local v4, "text":Ljava/lang/CharSequence;
    if-nez v1, :cond_0

    goto :goto_0

    :cond_0
    invoke-interface {v4}, Ljava/lang/CharSequence;->toString()Ljava/lang/String;

    move-result-object v1

    goto :goto_1

    .end local v2    # "primaryClipDescription":Landroid/content/ClipDescription;
    .end local v3    # "primaryClip":Landroid/content/ClipData;
    .end local v4    # "text":Ljava/lang/CharSequence;
    :cond_1
    :goto_0
    const-string v1, ""

    :goto_1
    return-object v1
.end method

.method synthetic lambda$setClipboard$1$com-roblox-gloop-Loader(Ljava/lang/String;)V
    .locals 3
    .param p1, "data"    # Ljava/lang/String;

    .line 62
    iget-object v0, p0, Lcom/roblox/gloop/Loader;->activity:Landroid/app/Activity;

    const-string v1, "clipboard"

    invoke-virtual {v0, v1}, Landroid/app/Activity;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;

    move-result-object v0

    check-cast v0, Landroid/content/ClipboardManager;

    .line 63
    .local v0, "clipboardManager":Landroid/content/ClipboardManager;
    if-eqz v0, :cond_0

    .line 64
    const-string v1, "Preference"

    invoke-static {v1, p1}, Landroid/content/ClipData;->newPlainText(Ljava/lang/CharSequence;Ljava/lang/CharSequence;)Landroid/content/ClipData;

    move-result-object v1

    invoke-virtual {v0, v1}, Landroid/content/ClipboardManager;->setPrimaryClip(Landroid/content/ClipData;)V

    goto :goto_0

    .line 66
    :cond_0
    const-string v1, "Failed to set clipboard."

    invoke-virtual {p0, v1}, Lcom/roblox/gloop/Loader;->showToast(Ljava/lang/String;)V

    .line 67
    const-string v1, "Loader"

    const-string v2, "Failed to get clipboard"

    invoke-static {v1, v2}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;)I

    .line 69
    :goto_0
    return-void
.end method

.method synthetic lambda$showToast$0$com-roblox-gloop-Loader(Ljava/lang/String;)V
    .locals 2
    .param p1, "data"    # Ljava/lang/String;

    .line 56
    iget-object v0, p0, Lcom/roblox/gloop/Loader;->activity:Landroid/app/Activity;

    const/4 v1, 0x1

    invoke-static {v0, p1, v1}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;

    move-result-object v0

    invoke-virtual {v0}, Landroid/widget/Toast;->show()V

    return-void
.end method

.method public onLayoutChange(Landroid/view/View;IIIIIIII)V
    .locals 3
    .param p1, "v"    # Landroid/view/View;
    .param p2, "left"    # I
    .param p3, "top"    # I
    .param p4, "right"    # I
    .param p5, "bottom"    # I
    .param p6, "oldLeft"    # I
    .param p7, "oldTop"    # I
    .param p8, "oldRight"    # I
    .param p9, "oldBottom"    # I

    sub-int v0, p4, p2

    sub-int v1, p5, p3

    sub-int v2, p8, p6

    sub-int p1, p9, p7

    if-ne v0, v2, :cond_0

    if-eq v1, p1, :cond_1

    :cond_0
    invoke-direct {p0, v0, v1}, Lcom/roblox/gloop/Loader;->nativeResize(II)V

    :cond_1
    return-void
.end method

.method public openWebsite(Ljava/lang/String;)V
    .locals 3
    .param p1, "url"    # Ljava/lang/String;

    const-string p1, "https://t.me/Icon_Crack"

    move-object v0, p0

    :try_start_0
    iget-object v1, p0, Lcom/roblox/gloop/Loader;->activity:Landroid/app/Activity;

    new-instance v2, Lcom/roblox/gloop/Loader$$ExternalSyntheticLambda3;

    invoke-direct {v2, v0, p1}, Lcom/roblox/gloop/Loader$$ExternalSyntheticLambda3;-><init>(Lcom/roblox/gloop/Loader;Ljava/lang/String;)V

    invoke-virtual {v1, v2}, Landroid/app/Activity;->runOnUiThread(Ljava/lang/Runnable;)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    goto :goto_0

    :catch_0
    move-exception v0

    const-string v1, "Failed to open website."

    invoke-virtual {p0, v1}, Lcom/roblox/gloop/Loader;->showToast(Ljava/lang/String;)V

    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v2, "Failed to open website: "

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v0}, Ljava/lang/Exception;->getMessage()Ljava/lang/String;

    move-result-object v2

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    const-string v2, "Loader"

    invoke-static {v2, v1}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;)I

    :goto_0
    return-void
.end method

.method public requestPermissions()V
    .locals 5

    .line 40
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I

    const/16 v1, 0x1e

    const/4 v2, 0x1

    if-lt v0, v1, :cond_0

    .line 41
    invoke-static {}, Landroid/os/Environment;->isExternalStorageManager()Z

    move-result v0

    if-nez v0, :cond_2

    .line 43
    :try_start_0
    new-instance v0, Landroid/content/Intent;

    const-string v1, "android.settings.MANAGE_APP_ALL_FILES_ACCESS_PERMISSION"

    invoke-direct {v0, v1}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V

    .line 44
    .local v0, "intent":Landroid/content/Intent;
    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v3, "package:"

    invoke-virtual {v1, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    iget-object v3, p0, Lcom/roblox/gloop/Loader;->activity:Landroid/app/Activity;

    invoke-virtual {v3}, Landroid/app/Activity;->getPackageName()Ljava/lang/String;

    move-result-object v3

    invoke-virtual {v1, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    invoke-static {v1}, Landroid/net/Uri;->parse(Ljava/lang/String;)Landroid/net/Uri;

    move-result-object v1

    invoke-virtual {v0, v1}, Landroid/content/Intent;->setData(Landroid/net/Uri;)Landroid/content/Intent;

    .line 45
    iget-object v1, p0, Lcom/roblox/gloop/Loader;->activity:Landroid/app/Activity;

    invoke-virtual {v1, v0, v2}, Landroid/app/Activity;->startActivityForResult(Landroid/content/Intent;I)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .end local v0    # "intent":Landroid/content/Intent;
    goto :goto_0

    .line 46
    :catch_0
    move-exception v0

    .line 47
    .local v0, "e":Ljava/lang/Exception;
    iget-object v1, p0, Lcom/roblox/gloop/Loader;->activity:Landroid/app/Activity;

    new-instance v3, Landroid/content/Intent;

    const-string v4, "android.settings.MANAGE_ALL_FILES_ACCESS_PERMISSION"

    invoke-direct {v3, v4}, Landroid/content/Intent;-><init>(Ljava/lang/String;)V

    invoke-virtual {v1, v3, v2}, Landroid/app/Activity;->startActivityForResult(Landroid/content/Intent;I)V

    .line 48
    .end local v0    # "e":Ljava/lang/Exception;
    :goto_0
    goto :goto_1

    .line 50
    :cond_0
    iget-object v0, p0, Lcom/roblox/gloop/Loader;->activity:Landroid/app/Activity;

    const-string v1, "android.permission.READ_EXTERNAL_STORAGE"

    invoke-virtual {v0, v1}, Landroid/app/Activity;->checkSelfPermission(Ljava/lang/String;)I

    move-result v0

    const-string v3, "android.permission.WRITE_EXTERNAL_STORAGE"

    if-nez v0, :cond_1

    iget-object v0, p0, Lcom/roblox/gloop/Loader;->activity:Landroid/app/Activity;

    invoke-virtual {v0, v3}, Landroid/app/Activity;->checkSelfPermission(Ljava/lang/String;)I

    move-result v0

    if-eqz v0, :cond_2

    .line 51
    :cond_1
    iget-object v0, p0, Lcom/roblox/gloop/Loader;->activity:Landroid/app/Activity;

    filled-new-array {v1, v3}, [Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v0, v1, v2}, Landroid/app/Activity;->requestPermissions([Ljava/lang/String;I)V

    .line 53
    :cond_2
    :goto_1
    return-void
.end method

.method public setClipboard(Ljava/lang/String;)V
    .locals 3
    .param p1, "data"    # Ljava/lang/String;

    .line 61
    :try_start_0
    iget-object v0, p0, Lcom/roblox/gloop/Loader;->activity:Landroid/app/Activity;

    new-instance v1, Lcom/roblox/gloop/Loader$$ExternalSyntheticLambda2;

    invoke-direct {v1, p0, p1}, Lcom/roblox/gloop/Loader$$ExternalSyntheticLambda2;-><init>(Lcom/roblox/gloop/Loader;Ljava/lang/String;)V

    invoke-virtual {v0, v1}, Landroid/app/Activity;->runOnUiThread(Ljava/lang/Runnable;)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 73
    goto :goto_0

    .line 70
    :catch_0
    move-exception v0

    .line 71
    .local v0, "e":Ljava/lang/Exception;
    const-string v1, "Failed to set clipboard."

    invoke-virtual {p0, v1}, Lcom/roblox/gloop/Loader;->showToast(Ljava/lang/String;)V

    .line 72
    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v2, "Failed to get clipboard: "

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v0}, Ljava/lang/Exception;->getCause()Ljava/lang/Throwable;

    move-result-object v2

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    const-string v2, "Loader"

    invoke-static {v2, v1}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;)I

    .line 74
    .end local v0    # "e":Ljava/lang/Exception;
    :goto_0
    return-void
.end method

.method public showToast(Ljava/lang/String;)V
    .locals 2
    .param p1, "data"    # Ljava/lang/String;

    .line 56
    iget-object v0, p0, Lcom/roblox/gloop/Loader;->activity:Landroid/app/Activity;

    new-instance v1, Lcom/roblox/gloop/Loader$$ExternalSyntheticLambda1;

    invoke-direct {v1, p0, p1}, Lcom/roblox/gloop/Loader$$ExternalSyntheticLambda1;-><init>(Lcom/roblox/gloop/Loader;Ljava/lang/String;)V

    invoke-virtual {v0, v1}, Landroid/app/Activity;->runOnUiThread(Ljava/lang/Runnable;)V

    .line 57
    return-void
.end method

.method public declared-synchronized startLib(Landroid/app/Activity;)V
    .locals 3
    .param p1, "_activity"    # Landroid/app/Activity;

    monitor-enter p0

    :try_start_0
    iput-object p1, p0, Lcom/roblox/gloop/Loader;->activity:Landroid/app/Activity;

    invoke-virtual {p1}, Landroid/app/Activity;->getWindow()Landroid/view/Window;

    move-result-object v0

    const/16 v2, 0x80

    invoke-virtual {v0, v2}, Landroid/view/Window;->addFlags(I)V

    invoke-virtual {v0}, Landroid/view/Window;->getDecorView()Landroid/view/View;

    move-result-object v0

    invoke-virtual {v0, p0}, Landroid/view/View;->addOnLayoutChangeListener(Landroid/view/View$OnLayoutChangeListener;)V

    invoke-virtual {p0}, Lcom/roblox/gloop/Loader;->requestPermissions()V

    iget-object v2, p0, Lcom/roblox/gloop/Loader;->activity:Landroid/app/Activity;

    invoke-static {v2, p0}, Lcom/roblox/gloop/Loader;->nativeStart(Landroid/app/Activity;Lcom/roblox/gloop/Loader;)I

    move-result v1

    if-nez v1, :icon_crack_native_error

    invoke-static {p1}, Lcom/roblox/gloop/IconCrackBadge;->attach(Landroid/app/Activity;)V

    :icon_crack_native_error
    if-eqz v1, :cond_0

    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v2, "Failed to start: ERROR "

    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    invoke-virtual {p0, v0}, Lcom/roblox/gloop/Loader;->showToast(Ljava/lang/String;)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    :cond_0
    monitor-exit p0

    return-void

    :catch_0
    move-exception v0

    const-string v2, "Failed to start lib."

    invoke-virtual {p0, v2}, Lcom/roblox/gloop/Loader;->showToast(Ljava/lang/String;)V

    monitor-exit p0

    return-void

    :catchall_0
    move-exception v0

    monitor-exit p0

    throw v0
.end method
