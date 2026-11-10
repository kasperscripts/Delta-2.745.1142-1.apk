# GrandProject 62.31 — @Icon_Crack IC3

В IC3 встроен локальный профиль из **60 игровых адресов**. Проверка лицензии и проверка готовности премиум-профиля возвращают успех; покупка и активация ключа в боте для этого пути не нужны. Модуль находится внутри APK.

[**Скачать IC3 APK**](https://github.com/kasperscripts/Delta-2.745.1142-1.apk/raw/refs/tags/grandproject-6231-icon-crack-ic3-test/artifacts/GrandProject_6231_Icon_Crack_IC3_test.apk) · [Выпуск](https://github.com/kasperscripts/Delta-2.745.1142-1.apk/releases/tag/grandproject-6231-icon-crack-ic3-test)

Это тестовая сборка. **Полный запуск на Android, работа всех функций в игре и устранение вылета на CMF Phone 2 Pro ещё не подтверждены устройством.** Проверки ниже выполнялись в JVM и Unicorn ARM64.

## Изменения

- Telegram `https://t.me/Icon_Crack` открывается один раз после установки или очистки данных. Отметка синхронно сохраняется до перехода и переживает пересоздание Activity, перезапуск процесса и вылет. При ошибке Intent или сохранения приложение продолжает запуск.
- До возврата из Telegram нативный загрузчик и его GL-поверхность не запускаются. Ранняя загрузка из `Application.onCreate` удалена. `MainActivity` загружает `libiconpayload.so` после завершения загрузки `libgrand.so`; экспорт `JNI_OnLoad` вызывает настоящую `grand_payload_activate`.
- Лицензионный транспорт и фоновые вход/проверка в боте отключены. Статическая таблица профиля встроена для одной точной версии APK. Оригинальные функции разрешения адресов и проверки срока действия профиля сохранены; локальные сроки установлены без практического ограничения.
- В меню, Android Activity и журнале добавлены `@Icon_Crack` и `cracked by @Icon_Crack`, две видимые ссылки загрузчика заменены на канал пользователя.

IC1 и IC2 не содержали таблицы адресов и не включали зависящие от неё функции. **IC3 содержит все 60 записей**; в опубликованный профиль не подставлены нулевые адреса.

## Проверено

| Проверка | Результат |
| --- | --- |
| Подписи APK | v2 и v3, официальный apksigner |
| ZIP / DEX / native | CRC корректны; содержимое совпадает с исходниками сборки |
| Упаковка Android 16 | Native ZIP_STORED, zipalign `-P 16`, `extractNativeLibs=true`, `pageSizeCompat=true` |
| Telegram helper из собранного DEX | JVM: сохранение до Intent, повтор в процессе, пересоздание Activity, перезапуск процесса, ошибки сохранения/Intent/SharedPreferences |
| Конструкторы загрузчика и модуля | Исполнены 646 + 3335; PT_LOAD и GNU_RELRO применены до конструкторов |
| Отложенная активация | Callback отсутствует до `JNI_OnLoad` модуля и появляется после |
| JNI загрузчика | 21 метод зарегистрирован |
| Проверка лицензии / профиля | 1 / 1 |
| Резолвер таблицы | Все 60 значений совпадают с встроенным профилем |
| Адреса в игре | Диапазоны и требуемые флаги проверены по оригинальному ELF `libgrand.so` |
| Данные пули | Исполнены настоящие setter/getter; проверена копия 44 байт |
| Сетевые сериализаторы | Исполнены; 504 и 544 бита, сохранён указатель данных |
| Штатные установщики модуля | Успешно установлены перехваты сетевых пакетов, боевых функций и имён |
| Перехваты имён | Исполнены реальные мосты инструментирования расстояния и масштаба; проверены регистры и сохранение исходного состояния |
| Дополнительные функции отрисовки | Проверена установка/релокация 10 перехватов; сами функции отрисовки не исполнялись |
| Лицензионный RPC | Отключён, выходные буферы обнуляются |

В нативных тестах JNI и libc моделируются, фоновые потоки регистрируются без исполнения. Для игры исполняется конструктор распаковщика; её JNI-инициализация и игровой процесс не моделируются. База загрузки и ELF-метаданные берутся из фактически отображённой оригинальной библиотеки. Карта `/proc/self/maps` в расширенном тесте отражает текущие права памяти, включая изменения через `mprotect`.

Отчёты IC3: [verification-ic3.json](verification-ic3.json), [local-bootstrap-results.json](probes/local-bootstrap-results.json), [game-profile-results.json](probes/game-profile-results.json). Отчёты `verification.json` и `verification-ic2.json` относятся к предыдущим сборкам.

## Файл

`GrandProject_6231_Icon_Crack_IC3_test.apk`: **407 625 789 байт**, около 388,74 MiB.

SHA-256:

```text
b539753ca745950905f27f2dbbcf4c8508f56d276d4c6ccfabc00faa035a921a
```

Пакет `com.grand.cr`, versionCode `6643`, versionName `62.30-apk`, minSdk 24, targetSdk 36, arm64-v8a. Версия manifest сохранена из исходной APK; имя исходного файла содержит 6231. Сертификат тот же, что у IC1/IC2; данные при обновлении сохраняются.

## Профиль и воспроизведение

[Профиль 60 адресов](offset-profile.json) привязан к SHA исходной APK и `libgrand.so`. Большинство функций сопоставлены с экспортированными символами и машинным кодом публичной ARM64 `libGTASA.so`; отдельные адреса восстановлены по вызовам и ABI в этой версии игры. Сведения о совпадении байтов и назначении указаны для каждой записи. Исходный материал сопоставления: [AhmadYGG/samp-all-new](https://github.com/AhmadYGG/samp-all-new/blob/main/app/src/main/jniLibs/arm64-v8a/libGTASA.so). Этот файл не требуется для повторной сборки.

Исходная APK: `GrandProject_6231_fix.apk`, SHA-256 `5a7a7d388c0fb24578bf23c375abaeb4f175991e28c340ae323c0d34f157a2b2`.

Исходный модуль: `native_data/payload-original.so`, SHA-256 `df0c6703838a3e4eb3676108b054e89e1c3183d3148a861ec219454fdfa5c1a4`. Он получен обычным протоколом бесплатного исходного клиента. Сессионные ключи, заголовки запросов, подписанные URL и материалы аттестации не публикуются.

Нужны зависимости из `requirements-local.txt`, системная `libxxhash`, Java, Apktool 2.12.1 и Android Build Tools 36.1.0.

1. Извлечь `lib/arm64-v8a/libgrnd.so` из исходной APK.
2. `python3 grandproject/patch_local.py libgrnd-original.so grandproject/native_data/payload-original.so native-out`
3. Извлечь `classes6.dex` в отдельный ZIP как `classes.dex`, декодировать Apktool с `-r --no-assets`, выполнить `prepare_branding.py` для каталога smali, собрать и извлечь новый DEX. DEX-контейнер не является устанавливаемым приложением.
4. `python3 grandproject/repack_local.py original.apk classes6-patched.dex native-out/libgrnd.so native-out/libiconpayload.so unsigned.apk`
5. `zipalign -P 16 -f 4 unsigned.apk aligned.apk`, подписать своим ключом через apksigner. Проверить `apksigner verify --verbose` и `zipalign -c -P 16 4 signed.apk`.
6. `python3 grandproject/probes/local_bootstrap_probe.py signed.apk --output local-results.json`
7. `python3 grandproject/probes/game_profile_probe.py signed.apk --output game-results.json`

Локальные библиотеки воспроизводятся побайтно, итоговый SHA APK зависит от ключа подписи и ZIP-метаданных. Скрипты проверяют исходные хеши; переносить эти адреса на другие APK нельзя.
