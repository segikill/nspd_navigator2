# NSPD Navigator for QGIS Kolba

Модифицированный webscript для QGIS Kolba: подложки НСПД, базовые карты, выгрузка тайлов ортофото в переносимый VRT и служебные metadata.json.

## Kolba URL

После загрузки основного скрипта raw-ссылка для установки и обновления будет:

```text
https://raw.githubusercontent.com/segikill/nspd_navigator2/main/qgis_tools/nspd_navigator.py
```

В шапке `nspd_navigator.py` поле `original_url` должно указывать на эту ссылку, чтобы Kolba могла проверять обновления.

## Структура

```text
qgis_tools/
  nspd_navigator.py
README.md
CHANGELOG.md
```

## Обновление версии

При каждом изменении скрипта нужно:

1. Обновить `qgis_tools/nspd_navigator.py`.
2. Повысить поле `version:` в первом docstring.
3. Проверить, что raw-ссылка открывает чистый Python-код, а не HTML-страницу GitHub.
4. В Kolba выбрать скрипт и нажать Update, если версия отличается.
