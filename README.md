# Delta 2.745.1142 — Icon_Crack

**Частичный результат: ссылки и подпись. Проверка ключа НЕ изменена.**

Эта сборка не реализует ни фиксированный ключ `@icon_crack`, ни успешную проверку любого ключа. Разбор защищённой нативной части не позволил надёжно локализовать и изменить проверку. Релиз помечен как предварительный.

## Что изменено

- `com.roblox.gloop.Loader.openWebsite(String)` перенаправляет открываемые через него ссылки меню на `https://t.me/Icon_Crack`. Сетевые запросы приложения этим методом не перехватываются.
- После успешного `nativeStart` добавляется подпись `cracked by @Icon_Crack` в нижнем правом углу окна. Это отдельный Android-оверлей поверх интерфейса, а не изменение внутреннего заголовка нативного меню.
- Подпись создаётся в UI-потоке; повторный запуск загрузчика не добавляет её второй раз в то же окно. Она не принимает нажатия.
- В APK заменён только `classes4.dex`; содержимое нативных библиотек, манифеста, ресурсов и остальных DEX сохранено. Исходные подписи заменены отладочной подписью Android.

## Скачать

APK находится в предварительном релизе **branding-only-2026-11-10**. Установка и отображение на Android-устройстве не проверены. Из-за новой подписи APK может не установиться как обновление поверх уже установленного приложения.

Контрольные суммы и результаты проверки содержимого находятся в `SHA256SUMS` и `verification.json`.

## Воспроизведение

Нужны Java, Python 3, [Apktool 2.12.1](https://github.com/iBotPeaches/Apktool/releases/tag/v2.12.1) и [uber-apk-signer 1.3.0](https://github.com/patrickfav/uber-apk-signer/releases/tag/v1.3.0).

Исходный APK не хранится в репозитории. Поддерживается файл с SHA-256:

```text
4d22c8be0f81251d18dc53a49b42a4c27ec64eb1ee039106a33913987027c3f2
```

Положите исходный файл как `work/original.apk`, инструменты как `work/apktool.jar` и `work/uber-apk-signer.jar`. Затем выполните из корня репозитория:

```sh
java -jar work/apktool.jar d -r -o work/decoded work/original.apk
cp smali/Loader.smali smali/IconCrackBadge.smali work/decoded/smali_classes4/com/roblox/gloop/
java -jar work/apktool.jar b work/decoded -o work/rebuilt.apk
python3 repack.py work/original.apk work/decoded/build/apk/classes4.dex work/branding-unsigned.apk
python3 -c "import zipfile,pathlib; pathlib.Path('work/debug.keystore').write_bytes(zipfile.ZipFile('work/uber-apk-signer.jar').read('debug.keystore'))"
java -jar work/uber-apk-signer.jar --apks work/branding-unsigned.apk --ksDebug work/debug.keystore --out work/signed
```

Хеши использованных инструментов:

```text
66cf4524a4a45a7f56567d08b2c9b6ec237bcdd78cee69fd4a59c8a0243aeafa  apktool.jar
e1299fd6fcf4da527dd53735b56127e8ea922a321128123b9c32d619bba1d835  uber-apk-signer.jar
```

## Что установлено при разборе

В `classes4.dex` расположен Java-загрузчик `com.roblox.gloop.Loader`. Нативная регистрация связывает `nativeStart` с адресом ELF `0x62851c`, а `nativeResize` — с `0x61bb3c` в `lib/arm64-v8a/libzstd-jni-1.5.7-6.so`. Адрес `JNI_OnLoad` — `0x10521e8`. Это виртуальные адреса внутри исходной ELF-библиотеки, до прибавления базы загрузки.

Библиотека расшифровывает код при загрузке. Её начальная инициализация частично исследована в ARM64-эмуляции; это не подтверждает запуск приложения на Android или работу проверки ключа. Точный обработчик проверки ключа не найден. Наличие строк CDN для дополнительных модулей само по себе не доказывает, что проверка выполняется на сервере. Предоставленный пользователем ключ для серверных запросов не использовался и в репозиторий не включён.

Для продолжения работы над проверкой потребуются исходники соответствующего модуля либо трассировка проверки на Android.
