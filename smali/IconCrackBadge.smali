.class public final Lcom/roblox/gloop/IconCrackBadge;
.super Ljava/lang/Object;
.implements Ljava/lang/Runnable;

.field private final activity:Landroid/app/Activity;

.method private constructor <init>(Landroid/app/Activity;)V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/roblox/gloop/IconCrackBadge;->activity:Landroid/app/Activity;
    return-void
.end method

.method public static attach(Landroid/app/Activity;)V
    .locals 1
    :try_start
    new-instance v0, Lcom/roblox/gloop/IconCrackBadge;
    invoke-direct {v0, p0}, Lcom/roblox/gloop/IconCrackBadge;-><init>(Landroid/app/Activity;)V
    invoke-virtual {p0, v0}, Landroid/app/Activity;->runOnUiThread(Ljava/lang/Runnable;)V
    :try_end
    .catch Ljava/lang/RuntimeException; {:try_start .. :try_end} :failed
    return-void
    :failed
    move-exception v0
    return-void
.end method

.method public run()V
    .locals 6
    :try_start
    iget-object v0, p0, Lcom/roblox/gloop/IconCrackBadge;->activity:Landroid/app/Activity;
    invoke-virtual {v0}, Landroid/app/Activity;->getWindow()Landroid/view/Window;
    move-result-object v1
    invoke-virtual {v1}, Landroid/view/Window;->getDecorView()Landroid/view/View;
    move-result-object v1
    instance-of v2, v1, Landroid/widget/FrameLayout;
    if-eqz v2, :done
    check-cast v1, Landroid/widget/FrameLayout;
    const-string v2, "icon_crack_badge"
    invoke-virtual {v1, v2}, Landroid/view/View;->findViewWithTag(Ljava/lang/Object;)Landroid/view/View;
    move-result-object v3
    if-nez v3, :done
    new-instance v4, Landroid/widget/TextView;
    invoke-direct {v4, v0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V
    invoke-virtual {v4, v2}, Landroid/view/View;->setTag(Ljava/lang/Object;)V
    const-string v2, "cracked by @Icon_Crack"
    invoke-virtual {v4, v2}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V
    const/4 v2, -0x1
    invoke-virtual {v4, v2}, Landroid/widget/TextView;->setTextColor(I)V
    const v2, 0xcc161621
    invoke-virtual {v4, v2}, Landroid/view/View;->setBackgroundColor(I)V
    const/high16 v2, 0x41400000
    invoke-virtual {v4, v2}, Landroid/widget/TextView;->setTextSize(F)V
    invoke-virtual {v4, v2}, Landroid/view/View;->setElevation(F)V
    const/16 v2, 0x8
    const/4 v3, 0x4
    invoke-virtual {v4, v2, v3, v2, v3}, Landroid/view/View;->setPadding(IIII)V
    const/4 v2, 0x0
    invoke-virtual {v4, v2}, Landroid/view/View;->setClickable(Z)V
    invoke-virtual {v4, v2}, Landroid/view/View;->setFocusable(Z)V
    new-instance v0, Landroid/widget/FrameLayout$LayoutParams;
    const/4 v2, -0x2
    const/16 v3, 0x55
    invoke-direct {v0, v2, v2, v3}, Landroid/widget/FrameLayout$LayoutParams;-><init>(III)V
    const/16 v2, 0x10
    iput v2, v0, Landroid/view/ViewGroup$MarginLayoutParams;->rightMargin:I
    iput v2, v0, Landroid/view/ViewGroup$MarginLayoutParams;->bottomMargin:I
    invoke-virtual {v1, v4, v0}, Landroid/view/ViewGroup;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V
    :try_end
    .catch Ljava/lang/RuntimeException; {:try_start .. :try_end} :failed
    :done
    return-void
    :failed
    move-exception v0
    return-void
.end method
