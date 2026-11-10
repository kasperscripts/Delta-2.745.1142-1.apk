# Phantom — @Icon_Crack

В Phantom заменены подпись и локальный ключ `@DramaDLC` на **`@Icon_Crack`**. Подпись интерфейса: `cracked by @Icon_Crack`. Поле ввода показывает новый ключ.

- [Скачать Phantom_Icon_Crack.apk](https://github.com/kasperscripts/Delta-2.745.1142-1.apk/raw/refs/tags/phantom-icon-crack-v1/artifacts/Phantom_Icon_Crack.apk)
- [Скачать LuluBoxSuper_2.1.2.apk](https://github.com/kasperscripts/Delta-2.745.1142-1.apk/raw/refs/tags/phantom-icon-crack-v1/artifacts/LuluBoxSuper_2.1.2.apk)
- [Выпуск на GitHub](https://github.com/kasperscripts/Delta-2.745.1142-1.apk/releases/tag/phantom-icon-crack-v1)

В Phantom обнаружена настоящая локальная проверка ключа: сравнение строки после `trim()`. Теперь `@Icon_Crack` проходит, старый ключ не проходит; регистр учитывается. Ожидаемый SHA-256 сертификата в проверке запуска обновлён под сертификат новой APK. Сама проверка сертификата сохранена.

Из-за смены сертификата **перед установкой новой версии нужно удалить старый Phantom**, в том числе его старую установленную копию внутри виртуальной среды, если она используется. При удалении приложения Android удаляет его данные.

В LuluBox упоминаний DramaDLC не обнаружено: проверены все 992 записи APK и 19 659 распакованных smali-файлов. Этот APK опубликован побайтно без изменений, с исходной подписью.

## Проверки

- В подписанном Phantom нет прямых упоминаний Drama в UTF-8 и UTF-16, без учёта регистра. Подпись и новый ключ подтверждены декомпиляцией фактически собранного DEX.
- Изменённый метод проверки ключа извлечён из DEX через JADX и исполнен в JVM с заглушкой EditText: **7 случаев**. Проверены новый/старый ключ, пробелы по краям, другой регистр, пустая/случайная строка и отсутствие поля.
- Встроенный отпечаток сертификата совпадает с реальным сертификатом подписанной APK.
- Подписи Phantom v2/v3 и LuluBox v1/v2/v3 проверены официальным apksigner. CRC обоих ZIP корректны.
- Только `classes.dex` и параметры совместимости `AndroidManifest.xml` Phantom изменены среди исходных записей, кроме подписей. Все пять native-библиотек, `assets/bootstrap.bin` и ресурсы сохранены побайтно.
- Native-библиотеки Phantom упакованы без сжатия, APK выровнен `zipalign -P 16`; включены `extractNativeLibs` и `pageSizeCompat`.

**На Android-устройстве запуск, Root/LuluBox/PHvirtual и игровой процесс не проверены.** Нативный модуль и формат bootstrap не менялись. Сканирование содержимого не заменяет проверку интерфейса загружаемого модуля во время игры.

Отчёт с размерами и SHA-256: [verification.json](verification.json). Контрольные суммы: [SHA256SUMS](SHA256SUMS).

Phantom: пакет `dev.secret.oxide`, versionCode 86, versionName `3.5.66-hardened`, minSdk 24, targetSdk 35, arm64-v8a. LuluBox: пакет `com.lulu.luluboxsuper`, versionCode 212, versionName `2.1.2`, minSdk 21, targetSdk 28, arm64-v8a / armeabi-v7a.

## Повторная сборка

Исходный Phantom SHA-256: `5d9cb8cb27b5e1f41b1b570003429dcfa467f713e5e9c974442ec9d89959423f`.

Нужны Java, Python 3, Apktool 2.12.1 и Android Build Tools 36.1.0. Из корня репозитория:

```sh
java -jar apktool.jar d -o work/phantom original.apk
python3 phantom/prepare_branding.py work/phantom/smali --certificate-sha256 YOUR_CERTIFICATE_SHA256
java -jar apktool.jar b work/phantom -o work/rebuilt.apk
python3 phantom/repack.py original.apk work/phantom/build/apk/classes.dex work/unsigned.apk
zipalign -P 16 -f 4 work/unsigned.apk work/aligned.apk
apksigner sign --ks YOUR_KEYSTORE --min-sdk-version 24 --v2-signing-enabled true --v3-signing-enabled true --out work/Phantom_Icon_Crack.apk work/aligned.apk
apksigner verify --verbose work/Phantom_Icon_Crack.apk
zipalign -c -P 16 4 work/Phantom_Icon_Crack.apk
```

Укажите SHA-256 именно сертификата выбранного ключа подписи. Приватный ключ и пароль сборки не публикуются. Скрипт подготовки проверен на свежей распаковке: он воспроизводит smali, из которого собран опубликованный DEX.
