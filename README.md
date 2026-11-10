# Delta 2.745.1142 — @Icon_Crack

Ключ **`@Icon_Crack`** принимается локально, без обращения к серверу и без проверки срока действия. Регистр имеет значение. Остальные ключи проходят исходную проверку.

[**Скачать вариант для Android 16**](https://github.com/kasperscripts/Delta-2.745.1142-1.apk/raw/refs/heads/main/artifacts/Delta-2.745.1142-1-Icon_Crack-Android16.apk)

Предыдущая сборка `branding-only` меняла только ссылки и подпись. В новой сборке `fixed-key` изменена сама проверка ключа. APK хранится в `artifacts/` через Git LFS.

## Вариант Android 16

После сообщения об отказе установки на CMF Phone 2 Pro / Android 16 подготовлен отдельный вариант упаковки. Точная причина отказа на телефоне пока не подтверждена: предыдущий файл проходит проверки подписи, ZIP и выравнивания SDK 36.

Новый вариант собирается Android Build Tools 36.1.0: все нативные библиотеки хранятся без сжатия и выровнены в APK на 16 КБ. В манифесте явно включены `extractNativeLibs` и `pageSizeCompat`; используется новый сертификат RSA 3072. Содержимое DEX и нативных библиотек совпадает с проверенной сборкой `fixed-key`, поэтому логика ключа не менялась.

Проверены подписи для API 26–36, чтение манифеста инструментами Android 16 и выравнивание всех библиотек. **Установка на CMF Phone 2 Pro ещё требует повторной проверки пользователем.** Подробности: `android16-verification.json`.

## Изменения

- Во встроенном Luau-байткоде меню найдены две функции проверки, использующие `/public/redeem/` и `/public/expires/`. В начале обеих добавлено условие:

  ```lua
  if key == "@Icon_Crack" then
      return true
  end
  -- далее исходная проверка для других ключей
  ```

- Кнопка «Continue» использует эту функцию и при успехе вызывает `GrantAccess`.
- Подпись `cracked by @Icon_Crack` находится внутри меню. Старый Android-оверлей удалён.
- Ссылки меню, открываемые через `Loader.openWebsite`, ведут на `https://t.me/Icon_Crack`. Также заменены социальные и пользовательские ссылки в байткоде. Адреса загрузки рабочих ресурсов и API сохранены.
- Подсказка поля ввода ключа заменена на `@Icon_Crack`.

## Проверки

- **22 случая в официальной Luau VM:** фиксированный ключ, повторные попытки, занятое состояние проверки, обработчик «Continue», неверный ключ, пустая строка, другой регистр и пробел в конце. Для `@Icon_Crack` сетевой обработчик не вызывается.
- ARM64-декодер библиотеки восстановил изменённый байткод после обратной упаковки.
- Начальный загрузчик изменённой нативной библиотеки завершился в ARM64-эмуляции; расшифрованный машинный код совпал с исходным побайтно.
- Проверены выравнивание APK, подписи v2/v3, контрольные суммы и сохранность остальных файлов.

**На Android-устройстве установка и запуск не проверены.** Проверки VM и эмуляции не заменяют проверку всего приложения на устройстве. Вариант Android 16 подписан отдельным сертификатом RSA 3072; обновление поверх версии с другим сертификатом может не установиться.

Подробности: `verification.json`, `tests/report.json`, `SHA256SUMS`. Предоставленный пользователем ключ для серверных запросов не использовался и в файлы не включён.

## Воспроизводимая сборка

Нужны Java, Python 3, системная `libzstd` **1.5.7**, [Apktool 2.12.1](https://github.com/iBotPeaches/Apktool/releases/tag/v2.12.1) и [uber-apk-signer 1.3.0](https://github.com/patrickfav/uber-apk-signer/releases/tag/v1.3.0).

Исходный APK должен иметь SHA-256:

```text
4d22c8be0f81251d18dc53a49b42a4c27ec64eb1ee039106a33913987027c3f2
```

Положите его в `work/original.apk`, инструменты — в `work/apktool.jar` и `work/uber-apk-signer.jar`. Из корня репозитория:

```sh
java -jar work/apktool.jar d -r -o work/decoded work/original.apk
cp smali/Loader.smali work/decoded/smali_classes4/com/roblox/gloop/
python3 patch_native.py work/decoded/lib/arm64-v8a/libzstd-jni-1.5.7-6.so work/libzstd-fixed-key.so
java -jar work/apktool.jar b work/decoded -o work/rebuilt.apk
python3 repack.py work/original.apk work/decoded/build/apk/classes4.dex work/fixed-key-unsigned.apk --native work/libzstd-fixed-key.so
python3 -c "import zipfile,pathlib; pathlib.Path('work/debug.keystore').write_bytes(zipfile.ZipFile('work/uber-apk-signer.jar').read('debug.keystore'))"
java -jar work/uber-apk-signer.jar --apks work/fixed-key-unsigned.apk --ksDebug work/debug.keystore --out work/signed
```

`patch_native.py` проверяет хеш исходной библиотеки, декодирует встроенный блок меню, меняет два прототипа, сжимает и кодирует блок обратно. Размер ELF и размер блока сохраняются. В APK заменяются только `classes4.dex` и `lib/arm64-v8a/libzstd-jni-1.5.7-6.so`, а также подписи.

Хеши инструментов:

```text
66cf4524a4a45a7f56567d08b2c9b6ec237bcdd78cee69fd4a59c8a0243aeafa  apktool.jar
e1299fd6fcf4da527dd53735b56127e8ea922a321128123b9c32d619bba1d835  uber-apk-signer.jar
```

## Повторить тесты Luau

После сборки официального [Luau](https://github.com/luau-lang/luau) на коммите `12a6ba75883272c79b66b59815efef4c574196f6`:

```sh
python3 tests/prepare_vm_tests.py work/libzstd-fixed-key.so work/luau work/vm-tests
g++ -std=c++17 -O2 -Iwork/luau/VM/include tests/test_key_vm.cpp work/luau/build/release/libluauvm.a work/luau/build/release/libluaucommon.a -lpthread -o work/test-key-vm
work/test-key-vm work/vm-tests
```

Тесты извлекают функции из изменённой нативной библиотеки и выполняют их байткод в Luau VM с заменой сетевого обработчика на тестовый. Остальные прототипы меню сохраняются без изменения машинных инструкций.

## Перепаковка для Android 16

После сборки APK с фиксированным ключом используйте `android16_compat.py`, `zipalign` и `apksigner` из официального Android Build Tools 36.1.0. Пример с собственным ключом подписи:

```sh
python3 android16_compat.py work/fixed-key-unsigned.apk work/android16-unsigned.apk
work/build-tools/zipalign -P 16 -f 4 work/android16-unsigned.apk work/android16-aligned.apk
work/build-tools/apksigner sign --ks work/release.p12 --ks-key-alias icon-crack --min-sdk-version 26 --v1-signing-enabled true --v2-signing-enabled true --v3-signing-enabled true --v4-signing-enabled false --out work/Android16.apk work/android16-aligned.apk
work/build-tools/apksigner verify --verbose --min-sdk-version 26 --max-sdk-version 36 work/Android16.apk
work/build-tools/zipalign -c -P 16 4 work/Android16.apk
```

Пароль ключа вводится локально при подписании. Приватный ключ сборки в репозитории отсутствует.
