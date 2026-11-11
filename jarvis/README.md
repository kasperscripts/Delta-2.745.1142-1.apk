# Jarvis — @Icon_Crack

Ключ заменён на **`@Icon_Crack`**. Подписи и адрес канала во внешнем загрузчике и встроенном меню заменены на `@Icon_Crack` / `t.me/Icon_Crack`. Название приложения: `Jarvis @Icon_Crack`.

- [Скачать Jarvis_Icon_Crack.apk](https://github.com/kasperscripts/Delta-2.745.1142-1.apk/raw/refs/tags/jarvis-icon-crack-v1/artifacts/Jarvis_Icon_Crack.apk)
- [Выпуск на GitHub](https://github.com/kasperscripts/Delta-2.745.1142-1.apk/releases/tag/jarvis-icon-crack-v1)
- [Отчёт проверки](verification.json), [изменённые строки](changes.json), [SHA256SUMS](SHA256SUMS).

Проверка локальная: точное сравнение с `@Icon_Crack`, с учётом регистра и без удаления пробелов. Старый ключ не принимается. Параметры срока действия и механизм локальной активации сохранены.

**Сертификат отличается от исходного APK.** При установке поверх исходного Jarvis Android может потребовать удалить прежнее приложение, включая установленную внутри виртуальной среды копию. Удаление приложения удаляет его данные.

## Изменения

В APK изменены три записи:

- `classes2.dex`: шесть закодированных текстовых строк и три внутренних имени классов.
- `assets/jarvis-local.so`: те же изменения во встроенном DEX интерфейса, расположенном по смещению `0x220584` и закодированном XOR `0x5a`.
- `AndroidManifest.xml`: название приложения и `versionName`.

Размеры обоих DEX, индексы и смещения строк сохранены. Упорядоченность таблиц строк проверена, SHA-1 и Adler-32 пересчитаны. Кроме данных строк и контрольных сумм DEX байты совпадают с исходными. Размер ELF и все его байты вне встроенного DEX сохранены. Иконки, изображения и остальные ресурсы не менялись.

Контактный адрес в строках интерфейса: `t.me/Icon_Crack`, канал: <https://t.me/Icon_Crack>. Служебные адреса загрузки и API не подменялись адресом Telegram.

## Проверки

- Подписи APK v2/v3 проверены официальным `apksigner`; CRC ZIP и `zipalign -P 16` корректны.
- Фактические внешний и внутренний DEX из готового APK распакованы: методы проверки ключа и декодирования строк совпадают.
- Метод проверки ключа, декомпилированный из готового DEX, исполнен в JVM: семь случаев. Принимается новый ключ; старый ключ, другой регистр, пробелы по краям, пустая и случайная строки, `null` отклоняются. Проверено также соответствующее регулярное выражение входного экрана.
- Проверены все восемь декодированных строк локального помощника. В тексте APK и расшифрованного внутреннего DEX упоминаний `faust` не осталось. Дополнительно декодированы 223 строки LSParanoid внешнего загрузчика и 82 строки внутреннего UI: они сохранены.
- На JVM Android Base64 заменён стандартным декодером; для компиляции восстановлено только объявление checked exception у декомпилированного метода, без изменения его тела.

**На Android-устройстве запуск и отображение в игре не проверены.**

## Повторная сборка

Нужны Python 3 и Android Build Tools. Исходный APK SHA-256: `1bac23dc8aacfbef28f066842216ce3a68b3fa0f29e874fa9c29fb3a225f5001`.

```sh
python3 jarvis/rebrand.py original.apk unsigned.apk --report changes.json
zipalign -P 16 -f 4 unsigned.apk aligned.apk
apksigner sign --ks YOUR_KEYSTORE --min-sdk-version 24 --v2-signing-enabled true --v3-signing-enabled true --out Jarvis_Icon_Crack.apk aligned.apk
apksigner verify --verbose Jarvis_Icon_Crack.apk
zipalign -c -P 16 4 Jarvis_Icon_Crack.apk
```

Проверка фактического валидатора через JADX и Java с компилятором:

```sh
unzip -p Jarvis_Icon_Crack.apk classes2.dex > classes2.dex
jadx --single-class com.x.icon_crack_.io.q.b --single-class-output validator.java classes2.dex
java jarvis/VerifyKey.java validator.java
```

Пакет: `com.jarvis.oxide.loader.local`, versionCode 70, versionName `3.5.42-Icon_Crack`, minSdk 24, targetSdk 34. Нативный модуль: arm64-v8a. Приватный ключ подписи и пароль не публикуются.
