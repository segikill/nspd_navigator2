
"""
description: Инструмент для добавления подложек <a href="https://nspd.gov.ru/map">карты НСПД</a>
version: 1.3.1-v19.11-ortho-first
reference: 
author: 
author_mail: 
original_url: https://raw.githubusercontent.com/segikill/nspd_navigator2/refs/heads/main/nspd_navigator.py
"""

from qgis.utils import iface
from qgis.core import *
from qgis._core import *
from qgis.core import Qgis
from qgis.utils import iface
from qgis._gui import *

from qgis.PyQt import QtCore
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtWidgets import QDockWidget,  QWidget, QPushButton, QTreeWidget, QTreeWidgetItem, QMainWindow, QVBoxLayout, QLineEdit, QSizePolicy, QHBoxLayout, QMessageBox, QProgressBar, QLabel, QAbstractItemView, QFileDialog, QInputDialog
from qgis.PyQt.QtGui import QIcon, QColor, QGuiApplication, QDrag, QImage, QPainter
try:
    from qgis.PyQt.QtNetwork import QSslConfiguration, QSslSocket
except Exception:
    QSslConfiguration = None
    QSslSocket = None

import requests
import urllib
import time 
import json 
import processing
import re
import random
import copy
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import os
import tempfile
from xml.sax.saxutils import escape as xml_escape

QGIS_V = Qgis.version()
referer_header = 'referer'

if QGIS_V.startswith('3.22'):
    referer_header = 'referer'
    wms_keys = [
        'qgis/WMS/{}/authcfg', 'qgis/WMS/{}/password', 'qgis/WMS/{}/username', 
        'qgis/connections-wms/{}/dpiMode', 
        'qgis/connections-wms/{}/ignoreAxisOrientation', 
        'qgis/connections-wms/{}/ignoreGetFeatureInfoURI',
        'qgis/connections-wms/{}/ignoreGetMapURI', 
        'qgis/connections-wms/{}/ignoreReportedLayerExtents',
        'qgis/connections-wms/{}/invertAxisOrientation', 
        'qgis/connections-wms/{}/referer',
        'qgis/connections-wms/{}/smoothPixmapTransform', 
        'qgis/connections-wms/{}/url'
    ]
elif QGIS_V.startswith('3.28'):
    referer_header = 'http-header:referer'
    wms_keys = [
        'qgis/WMS/{}/authcfg', 'qgis/WMS/{}/password', 'qgis/WMS/{}/username', 
        'qgis/connections-wms/{}/dpiMode', 
        'qgis/connections-wms/{}/ignoreAxisOrientation', 
        'qgis/connections-wms/{}/ignoreGetFeatureInfoURI',
        'qgis/connections-wms/{}/ignoreGetMapURI', 
        'qgis/connections-wms/{}/ignoreReportedLayerExtents',
        'qgis/connections-wms/{}/invertAxisOrientation', 
        'qgis/connections-wms/{}/referer',
        'qgis/connections-wms/{}/smoothPixmapTransform', 
        'qgis/connections-wms/{}/url'
    ]
elif QGIS_V.startswith('3.3'):
    referer_header = 'http-header:referer'
    wms_keys = [
        'connections/ows/items/wms/connections/items/{}/authcfg',
        'connections/ows/items/wms/connections/items/{}/dpi-mode',
        'connections/ows/items/wms/connections/items/{}/http-header',
        'connections/ows/items/wms/connections/items/{}/ignore-axis-orientation',
        'connections/ows/items/wms/connections/items/{}/ignore-get-feature-info-uri',
        'connections/ows/items/wms/connections/items/{}/ignore-get-map-uri',
        'connections/ows/items/wms/connections/items/{}/invert-axis-orientation',
        'connections/ows/items/wms/connections/items/{}/password',
        'connections/ows/items/wms/connections/items/{}/reported-layer-extents',
        'connections/ows/items/wms/connections/items/{}/smooth-pixmap-transform',
        'connections/ows/items/wms/connections/items/{}/tile-pixel-ratio',
        'connections/ows/items/wms/connections/items/{}/url',
        'connections/ows/items/wms/connections/items/{}/username',
    ]
elif QGIS_V.startswith('3.4'):
    referer_header = 'http-header:referer'
    wms_keys = [
        'connections/ows/items/wms/connections/items/{}/authcfg',
        'connections/ows/items/wms/connections/items/{}/dpi-mode',
        'connections/ows/items/wms/connections/items/{}/http-header',
        'connections/ows/items/wms/connections/items/{}/ignore-axis-orientation',
        'connections/ows/items/wms/connections/items/{}/ignore-get-feature-info-uri',
        'connections/ows/items/wms/connections/items/{}/ignore-get-map-uri',
        'connections/ows/items/wms/connections/items/{}/invert-axis-orientation',
        'connections/ows/items/wms/connections/items/{}/password',
        'connections/ows/items/wms/connections/items/{}/reported-layer-extents',
        'connections/ows/items/wms/connections/items/{}/smooth-pixmap-transform',
        'connections/ows/items/wms/connections/items/{}/tile-pixel-ratio',
        'connections/ows/items/wms/connections/items/{}/url',
        'connections/ows/items/wms/connections/items/{}/username',
    ]

wms_url_template = 'https://nspd.gov.ru/api/aeggis/v3/{}/wms'
wmts_url_template = 'https://nspd.gov.ru/api/aeggis/v4/{}/wmts/{{z}}/{{x}}/{{y}}.png'
nspd_layer_metadata_url_template = 'https://nspd.gov.ru/api/geoportal/v1/layers/{}'
nspd_base_layers_url = 'https://nspd.gov.ru/api/geoportal/v1/baselayers'

XYZ_REFERRER = 'https://nspd.gov.ru/map'
XYZ_ORIGIN = 'https://nspd.gov.ru'
XYZ_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'

NSPD_ORTHO_LAYER_IDS = {36067, 36344, 36345, 36346}
NSPD_XYZ_Z_MIN_DEFAULT = 0
NSPD_XYZ_Z_MAX_DEFAULT = 20
NSPD_ORTHO_Z_MIN_FALLBACK = 14
NSPD_ORTHO_Z_MAX_FALLBACK = 18
NSPD_ORTHO_Z_PROBE_MIN = 8
NSPD_ORTHO_Z_PROBE_MAX = 22
NSPD_ORTHO_TILE_PROBE_TIMEOUT = 1.5
NSPD_ORTHO_PROBE_ZOOM_ON_ADD = False
WEB_MERCATOR_HALF_WORLD = 20037508.342789244

# Защита от случайного рендера НСПД на масштабе страны/мира.
# Слой будет видим только на 1:250 000 и ближе. Это ставится до addMapLayer,
# чтобы QGIS не начал массово запрашивать тайлы/картинки сразу после добавления.
NSPD_RASTER_MIN_VISIBLE_SCALE = 250000
NSPD_ORTHO_MIN_VISIBLE_SCALE = 180000
NSPD_RASTER_WARN_SCALE = 500000
NSPD_XYZ_TILE_SIZE_PX = 256
NSPD_WEB_MERCATOR_INITIAL_RESOLUTION = 156543.03392804097
NSPD_RASTER_EXPORT_TIMEOUT = 20
NSPD_RASTER_TILE_RETRY_COUNT = 3
NSPD_RASTER_TILE_RETRY_DELAY_MIN = 0.8
NSPD_RASTER_TILE_RETRY_DELAY_MAX = 2.5
NSPD_RASTER_METADATA_FILE_NAME = 'metadata.json'
NSPD_RASTER_METADATA_LAST_MODIFIED_LIMIT = 10
NSPD_LAYER_METADATA_TIMEOUT = 8
NSPD_RASTER_EXPORT_Z_MAX = 25

# Если сервер начнёт требовать Authorization (Bearer/Token), задай токен здесь.
# Пример: NSPD_AUTH_TOKEN = 'eyJhbGciOi...'
NSPD_AUTH_TOKEN = ''

nspd_url = 'https://nspd.gov.ru/api/geoportal/v1/intersects?typeIntersect=fullObject'

# Настройки пакетного скачивания объектов по охвату.
# Один тайл повторяет старый допустимый охват: dd = 1500 -> квадрат 3000 x 3000 м в EPSG:3857.
NSPD_TILE_SIZE = 3000
NSPD_DELAY_MIN = 1.2
NSPD_DELAY_MAX = 3.5

# Повторы для временных сбоев сервера / таймаутов / 429 / 5xx.
NSPD_RETRY_COUNT = 3
NSPD_RETRY_DELAY_MIN = 3.0
NSPD_RETRY_DELAY_MAX = 8.0

# Сколько объектов держать во временном пакете перед сбросом в слой QGIS.
NSPD_BATCH_FEATURES_LIMIT = 1500

# Дополнительный сброс в слой QGIS после каждых N обработанных тайлов.
# Работает вместе с NSPD_BATCH_FEATURES_LIMIT: что наступило раньше, то и сбрасывает пакет.
NSPD_BATCH_TILES_LIMIT = 50

# Жёсткий лимит тайлов снят. На больших охватах ограничение фактическое:
# время выполнения, стабильность сервера и объём памяти QGIS.
NSPD_MAX_TILES = None

# Многопоточная версия без автодробления тайлов.
# Начинать с 2; после стабильного теста можно поднять до 3.
NSPD_WORKERS = 4

# QGIS 3.40/3.44 иногда падает на SSL handshake НСПД:
# "Корневой сертификат цепочки сертификатов самоподписанный и не является заверенным".
# Этот режим игнорирует SSL-ошибки только для nspd.gov.ru и его поддоменов.
NSPD_IGNORE_SSL_ERRORS = True
NSPD_SSL_ALLOWED_HOSTS = {
    'nspd.gov.ru'
}
_NSPD_SSL_HANDLER_INSTALLED = False
_NSPD_SSL_HANDLER_REF = None
_NSPD_REQUEST_PREPROCESSOR_INSTALLED = False
_NSPD_REQUEST_PREPROCESSOR_ID = None
_NSPD_REQUEST_PREPROCESSOR_REF = None
_NSPD_XYZ_ZOOM_CACHE = {}


def install_nspd_ssl_ignore_handler():
    """Подключает обработчик SSL-ошибок QGIS/Qt только для НСПД.

    Важно: это влияет на сетевой стек QGIS/Qt (WMS/WMTS/XYZ),
    а не на requests. Для requests в коде уже используется verify=False.
    """
    global _NSPD_SSL_HANDLER_INSTALLED, _NSPD_SSL_HANDLER_REF

    if not NSPD_IGNORE_SSL_ERRORS:
        return False

    if _NSPD_SSL_HANDLER_INSTALLED:
        return True

    try:
        nam = QgsNetworkAccessManager.instance()
    except Exception:
        return False

    def _handle_ssl_errors(reply, errors):
        try:
            url = reply.url()
            host = url.host().lower()

            allowed = False
            for allowed_host in NSPD_SSL_ALLOWED_HOSTS:
                allowed_host = allowed_host.lower()
                if host == allowed_host or host.endswith('.' + allowed_host):
                    allowed = True
                    break

            if not allowed:
                return

            try:
                reply.ignoreSslErrors(errors)
            except TypeError:
                reply.ignoreSslErrors()

            try:
                QgsMessageLog.logMessage(
                    'Игнорированы SSL-ошибки для НСПД: {}'.format(url.toString()),
                    'NSPD Navigator',
                    Qgis.MessageLevel.Warning
                )
            except Exception:
                pass

        except Exception:
            pass

    try:
        nam.sslErrors.connect(_handle_ssl_errors)
        _NSPD_SSL_HANDLER_REF = _handle_ssl_errors
        _NSPD_SSL_HANDLER_INSTALLED = True
        return True
    except Exception as e:
        try:
            QgsMessageLog.logMessage(
                'Не удалось подключить SSL handler НСПД: {}'.format(e),
                'NSPD Navigator',
                Qgis.MessageLevel.Warning
            )
        except Exception:
            pass
        return False


def is_nspd_host(host):
    host = str(host or '').lower()
    for allowed_host in NSPD_SSL_ALLOWED_HOSTS:
        allowed_host = allowed_host.lower()
        if host == allowed_host or host.endswith('.' + allowed_host):
            return True
    return False


def get_nspd_http_headers(for_tiles=False):
    """Единый набор публичных заголовков для запросов к НСПД."""
    headers = {
        'Referer': XYZ_REFERRER,
        'Origin': XYZ_ORIGIN,
        'User-Agent': XYZ_UA,
    }
    if for_tiles:
        headers['Accept'] = 'image/avif,image/webp,image/apng,image/png,image/*,*/*;q=0.8'
    else:
        headers['Accept'] = '*/*'

    if NSPD_AUTH_TOKEN:
        headers['Authorization'] = 'Bearer {}'.format(NSPD_AUTH_TOKEN)

    return headers


def fetch_nspd_layer_metadata(layer_id):
    url = nspd_layer_metadata_url_template.format(int(layer_id))
    try:
        response = requests.get(
            url,
            headers=get_nspd_http_headers(for_tiles=False),
            verify=False,
            timeout=NSPD_LAYER_METADATA_TIMEOUT
        )
        if response.status_code != 200:
            return {
                'fetch_error': 'HTTP {}'.format(response.status_code),
                'url': url
            }
        return response.json()
    except Exception as e:
        return {
            'fetch_error': str(e),
            'url': url
        }


def extract_yyyymmdd_date_candidates(value):
    result = []
    text = str(value or '')
    for token in re.findall(r'20\d{6}', text):
        try:
            parsed = time.strptime(token, '%Y%m%d')
            formatted = time.strftime('%Y-%m-%d', parsed)
        except Exception:
            continue
        if formatted not in result:
            result.append(formatted)
    return result


def summarize_nspd_layer_metadata(layer_metadata):
    if not isinstance(layer_metadata, dict):
        return {}

    options = layer_metadata.get('options') or {}
    if not isinstance(options, dict):
        options = {}
    system_info = layer_metadata.get('systemInfo') or {}
    if not isinstance(system_info, dict):
        system_info = {}
    external = options.get('external') or {}
    if not isinstance(external, dict):
        external = {}
    coverage = layer_metadata.get('coverage') or {}
    if not isinstance(coverage, dict):
        coverage = {}
    grouped_layers = options.get('groupedLayers') or []
    if not isinstance(grouped_layers, list):
        grouped_layers = []
    external_url = (
        external.get('url')
        or options.get('externalUrl')
        or options.get('external_url')
    )
    source_date_candidates = []
    for value in [external_url, layer_metadata.get('url'), layer_metadata.get('name')]:
        for candidate in extract_yyyymmdd_date_candidates(value):
            if candidate not in source_date_candidates:
                source_date_candidates.append(candidate)
    summary = {
        'id': layer_metadata.get('id'),
        'name': layer_metadata.get('name'),
        'type': layer_metadata.get('type'),
        'source': layer_metadata.get('source'),
        'system_updated': system_info.get('updated'),
        'url': layer_metadata.get('url') or options.get('url'),
        'external_url': external_url,
        'cache': options.get('cache'),
        'grids_levels': options.get('grids_levels'),
        'coverage_bbox': coverage.get('bbox'),
        'grouped_layer_count': len(grouped_layers) if grouped_layers else None,
        'source_date_candidates': source_date_candidates
    }
    return dict((k, v) for k, v in summary.items() if v not in [None, '', []])


def write_raster_export_metadata(metadata_path, metadata):
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    return metadata_path


def format_metadata_date_value(value):
    value = str(value or '').strip()
    if not value:
        return ''
    return xml_escape(value.replace('T', ' '))


def format_raster_metadata_dates_for_message(metadata):
    if not isinstance(metadata, dict):
        return ''

    lines = ['Даты из metadata.json:']
    started = format_metadata_date_value(metadata.get('download_started'))
    finished = format_metadata_date_value(metadata.get('download_finished'))
    if started or finished:
        lines.append('выгрузка: {} - {}'.format(started or 'не указано', finished or 'не указано'))

    layer_metadata = metadata.get('layer_metadata') or {}
    if isinstance(layer_metadata, dict):
        system_updated = format_metadata_date_value(layer_metadata.get('system_updated'))
        if system_updated:
            lines.append('обновление слоя НСПД: {}'.format(system_updated))

    tile_dates = metadata.get('tile_last_modified_examples') or []
    tile_dates = [format_metadata_date_value(v) for v in tile_dates[:3] if format_metadata_date_value(v)]
    if tile_dates:
        lines.append('Last-Modified тайлов: {}'.format('; '.join(tile_dates)))

    source_date_candidates = []
    if isinstance(layer_metadata, dict):
        source_date_candidates = layer_metadata.get('source_date_candidates') or []
    source_date_candidates = [format_metadata_date_value(v) for v in source_date_candidates[:4] if format_metadata_date_value(v)]
    if source_date_candidates:
        lines.append('кандидаты дат из URL источника: {}'.format('; '.join(source_date_candidates)))

    capture_date = format_metadata_date_value(metadata.get('capture_date'))
    lines.append('дата съемки: {}'.format(capture_date or 'не найдена в тайлах/публичном API'))
    return '<br>'.join(lines)


def get_qssl_verify_none_value():
    if QSslSocket is None:
        return None
    value = getattr(QSslSocket, 'VerifyNone', None)
    if value is not None:
        return value
    try:
        return QSslSocket.PeerVerifyMode.VerifyNone
    except Exception:
        return None


def relax_nspd_ssl_for_request(request):
    """Отключает проверку SSL только для уже отфильтрованного запроса НСПД.

    В QGIS 3.44 sslErrors/ignoreSslErrors иногда не успевает сработать для
    QgsWmsTiledImageDownloadHandler. Поэтому на 3.44 делаем более ранний scoped
    обход: меняем QSslConfiguration прямо в QNetworkRequest перед отправкой.
    """
    if not NSPD_IGNORE_SSL_ERRORS:
        return False
    if QSslConfiguration is None or QSslSocket is None:
        return False
    if not hasattr(request, 'setSslConfiguration'):
        return False

    verify_none = get_qssl_verify_none_value()
    if verify_none is None:
        return False

    try:
        if hasattr(request, 'sslConfiguration'):
            ssl_config = request.sslConfiguration()
        else:
            ssl_config = QSslConfiguration.defaultConfiguration()
        ssl_config.setPeerVerifyMode(verify_none)
        request.setSslConfiguration(ssl_config)
        return True
    except Exception:
        return False


def install_nspd_network_headers_handler():
    """Добавляет HTTP-заголовки к QGIS/Qt-запросам на nspd.gov.ru.

    В разных версиях QGIS inline-параметры вида http-header:* для XYZ/WMS
    читаются по-разному. Препроцессор работает ниже уровнем и применяется к
    запросу прямо перед отправкой через QgsNetworkAccessManager.
    """
    global _NSPD_REQUEST_PREPROCESSOR_INSTALLED
    global _NSPD_REQUEST_PREPROCESSOR_ID
    global _NSPD_REQUEST_PREPROCESSOR_REF

    if _NSPD_REQUEST_PREPROCESSOR_INSTALLED:
        return True

    if not hasattr(QgsNetworkAccessManager, 'setRequestPreprocessor'):
        return False

    def _preprocess_request(request):
        try:
            url = request.url()
            if not is_nspd_host(url.host()):
                return

            for key, value in get_nspd_http_headers(for_tiles=False).items():
                request.setRawHeader(key.encode('utf-8'), str(value).encode('utf-8'))
            relax_nspd_ssl_for_request(request)
        except Exception:
            pass

    try:
        _NSPD_REQUEST_PREPROCESSOR_ID = QgsNetworkAccessManager.setRequestPreprocessor(_preprocess_request)
        _NSPD_REQUEST_PREPROCESSOR_REF = _preprocess_request
        _NSPD_REQUEST_PREPROCESSOR_INSTALLED = True
        return True
    except Exception as e:
        try:
            QgsMessageLog.logMessage(
                'Не удалось подключить сетевой preprocessor НСПД: {}'.format(e),
                'NSPD Navigator',
                Qgis.MessageLevel.Warning
            )
        except Exception:
            pass
        return False


# Ставим обработчик как можно раньше, до добавления WMS/WMTS-слоёв.
install_nspd_ssl_ignore_handler()
install_nspd_network_headers_handler()


nspd_headers = {
    "accept":"*/*",
    "accept-encoding":"identity",
    "accept-language":"ru-RU,ru;q=0.9",
    "cache-control":"no-cache",
    "connection":"keep-alive",
    "content-length":"410",
    "content-type":"application/json",
    "cookie":"_ym_uid=1731913107516103711; _ym_d=1731913107; webchat-webchat_nspd_noauth-uuid=ef6f562f-7c4d-4d85-a6c4-b5c3b0107e0d; JSESSIONID=da323884-0e90-4365-9e1d-70c4885a0fec; _ym_isad=1; _ym_visorc=b",
    "host":"nspd.gov.ru",
    "origin":"https://nspd.gov.ru",
    "pragma":"no-cache",
    "referer":"https://nspd.gov.ru/map",
    "sec-ch-ua":'"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile":"?0",
    "sec-ch-ua-platform":"Windows",
    "sec-fetch-dest":"empty",
    "sec-fetch-mode":"cors",
    "sec-fetch-site":"same-origin",
    "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}

nspd_headers_search = {
    "Accept": "*/*",
    "Accept-Encoding": "identity",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,uk;q=0.6",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Cookie": "_ym_uid=1731913107516103711; _ym_d=1731913107; _ym_isad=1; _ym_visorc=b",
    "Host": "nspd.gov.ru",
    "Pragma": "no-cache",
    "Referer": "https://nspd.gov.ru/map?zoom=10.652339771207421&coordinate_x=4190415.174867105&coordinate_y=7500396.669767046&theme_id=1&is_copy_url=true",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows"
}

dct_field_types = {
    "text": [QVariant.String, 'text'],
    "number": [QVariant.Int, 'int'],
    "date": [QVariant.Date, 'datetime'],
    "href": [QVariant.List, 'stringlist']
}

dct_field_types_rev = {
    QVariant.String: ['text', 2000],
    QVariant.Int: ['integer', -1],
    QVariant.Date: ['datetime', -1],
    QVariant.List: ['stringlist', -1]
}

data_pass = {
    "geom":{
        "type":"FeatureCollection",
        "features":[
            {
                "type":"Feature",
                "geometry":{
                    "crs":{
                        "properties":{
                            "name":"EPSG:3857"
                        },
                        "type":"name"
                    },
                    "type":"Polygon",
                    "coordinates":[
                        [
                            [
                                5342364.414602018,
                                5839061.4937124755
                            ],
                            [
                                5342350.112845775,
                                5838403.612925322
                            ],
                            [
                                5343270.192497375,
                                5838379.776664917
                            ],
                            [
                                5343274.9597494565,
                                5839133.002493689
                            ],
                            [
                                5342364.414602018,
                                5839061.4937124755
                            ]
                        ]
                    ]
                },
                "properties":{
                }
            }
        ]
    },
    "categories":[
        {
            "id":36369
        }
    ]
}

nspd_zouit_categories = {
    "ЗОУИТ объектов культурного наследия": [3, 4, 10, 12 , 13, 20],
    "ЗОУИТ объектов энергетики, связи, транспорта": [14, 15, 16, 17, 18, 19, 21, 28],
    "ЗОУИТ природных территорий": [2,5,6,7,8,24, 25, 33, 35, 38],
    "ЗОУИТ охраняемых объектов и безопасности": [9,22, 23, 26, 27, 34, 37],
    "Иные ЗОУИТ": [1, 11, 29, 30, 31, 32, 36, 39, 40, 41]
}

crs_mercator = QgsCoordinateReferenceSystem("EPSG:3857")


def fetch_nspd_base_layers(session=None):
    session = session or requests.Session()
    response = session.get(
        nspd_base_layers_url,
        headers=get_nspd_http_headers(for_tiles=False),
        verify=False,
        timeout=10
    )
    if response.status_code != 200:
        return []

    raw_layers = response.json()
    if not isinstance(raw_layers, list):
        return []

    preferred_order = {
        36346: 0,
        36347: 1,
        36067: 2,
        235: 3,
        36344: 4,
        36345: 5
    }
    result = []
    for item in raw_layers:
        if not isinstance(item, dict):
            continue
        layer_id = item.get('id')
        if layer_id is None or item.get('type') != 'wmts':
            continue
        result.append({
            'title': item.get('name') or str(layer_id),
            'layerId': int(layer_id),
            'layerType': 'wmts',
            'layerName': item.get('name') or str(layer_id),
            'layerVisibleByDefault': False,
            'categoryId': None,
            'options': item.get('options') or {},
            'favorites': False,
            'buttons': ['favorites'],
            'code': 'base',
            '_sort': preferred_order.get(int(layer_id), 1000 + len(result))
        })

    result.sort(key=lambda row: row.get('_sort', 1000))
    for row in result:
        row.pop('_sort', None)
    return result


def get_tms_list():
    """
    Загружает дерево слоёв НСПД (themeId=1) и дополняет его базовыми картами (WMTS/XYZ),
    которые не входят в layers-theme-tree.
    Возвращает:
      - data: исходное дерево + добавленные базовые карты
      - layers_meta: dict[layerId] -> {title, categoryId, layerType}
    """
    try:
        s = requests.Session()
        u = s.get(
            'https://nspd.gov.ru/api/geoportal/v1/layers-theme-tree?themeId=1',
            verify=False,
            timeout=10
        )
        data = u.json()

        layers = list(data.get('layers', []))
        layers_meta = {
            f['layerId']: {
                'title': f.get('title', str(f.get('layerId'))),
                'categoryId': f.get('categoryId', None),
                'layerType': f.get('layerType', 'wms')
            }
            for f in layers
            if isinstance(f, dict) and 'layerId' in f
        }

        # Базовые карты (не всегда попадают в theme tree). Ортофото ЕЭКО найдено как WMTS tiles:
        # /api/aeggis/v4/36346/wmts/{z}/{x}/{y}.png
        base_layers = [
            {
                'title': 'ЕЭКО (ортофото) (основной слой)',
                'layerId': 36346,
                'layerType': 'wmts',
                'layerName': 'ЕЭКО (ортофото) (основной слой)',
                'layerVisibleByDefault': False,
                'categoryId': None,
                'options': {
                    'format': {'transparent': False, 'type_tile': 'image/png'}
                },
                'favorites': False,
                'buttons': ['favorites'],
                'code': 'base'
            }
        ]

        try:
            dynamic_base_layers = fetch_nspd_base_layers(s)
        except Exception:
            dynamic_base_layers = []
        if dynamic_base_layers:
            base_layers = dynamic_base_layers

        for bl in base_layers:
            if bl['layerId'] not in layers_meta:
                layers.append(bl)
                layers_meta[bl['layerId']] = {
                    'title': bl['title'],
                    'categoryId': bl.get('categoryId', None),
                    'layerType': bl.get('layerType', 'wmts')
                }

        # Вставляем папку "Базовые карты" в дерево
        tree = data.setdefault('tree', {})
        folders = tree.setdefault('folders', [])
        base_layer_ids = [bl['layerId'] for bl in base_layers]
        base_folder = {
            'title': 'Базовые карты',
            'folderId': 900000,
            'layers': base_layer_ids,
            'folders': None
        }
        existing_base_folder = None
        for folder in folders:
            if isinstance(folder, dict) and folder.get('folderId') == 900000:
                existing_base_folder = folder
                break

        if existing_base_folder is None:
            folders.insert(0, base_folder)
        else:
            existing_base_folder['title'] = 'Базовые карты'
            existing_base_folder['layers'] = base_layer_ids
            existing_base_folder['folders'] = None

        data['layers'] = layers
        return data, layers_meta
    except Exception:
        return {}, {}



def get_layer_error_text(layer):
    """Короткая диагностика ошибки провайдера QGIS."""
    try:
        err = layer.error()
        if err:
            summary = err.summary()
            if summary:
                return summary
    except Exception:
        pass
    return "invalid layer"


def qgis_version_int():
    """Возвращает версию QGIS числом вида 34012 для 3.40.12."""
    try:
        v = getattr(Qgis, 'QGIS_VERSION_INT', None)
        if v:
            return int(v)
    except Exception:
        pass
    try:
        parts = re.findall(r'\d+', QGIS_V)[:3]
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        return major * 10000 + minor * 100 + patch
    except Exception:
        return 0


def current_canvas_scale():
    try:
        return float(iface.mapCanvas().scale())
    except Exception:
        return 0.0


def apply_nspd_raster_scale_guard(layer, min_visible_scale=NSPD_RASTER_MIN_VISIBLE_SCALE):
    """Запрещает рендер НСПД на слишком мелких масштабах.

    В QGIS denominator больше означает более дальний масштаб: 1:1 000 000 дальше,
    чем 1:100 000. minimumScale задаёт самый дальний допустимый масштаб.
    """
    try:
        layer.setScaleBasedVisibility(True)
        layer.setMinimumScale(float(min_visible_scale))
        layer.setMaximumScale(0)
        layer.setCustomProperty('nspd_scale_guard_min_visible_scale', int(min_visible_scale))
    except Exception:
        pass
    return layer


def warn_if_canvas_scale_is_too_small(layer_name, min_visible_scale):
    try:
        scale = current_canvas_scale()
        if scale <= float(NSPD_RASTER_WARN_SCALE):
            return

        msg = QMessageBox(iface.mainWindow())
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setWindowTitle("НСПД: слой добавлен с ограничением масштаба")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setText(
            "Слой <b>{}</b> добавлен, но на текущем масштабе 1:{:,.0f} он не будет рендериться.<br><br>"
            "Это защита от массовой загрузки тайлов на масштабе страны/мира. "
            "Приблизьтесь до 1:{:,.0f} или ближе.".format(
                layer_name,
                scale,
                float(min_visible_scale)
            ).replace(',', ' ')
        )
        msg.exec()
    except Exception:
        pass


def build_wms_uri(layer_id, api_version=3, simple=False, with_headers=True, encode_url=False):
    """Собирает WMS URI.

    Для QGIS 3.40+ inline http-header:* часто ломает provider 'wms',
    поэтому новые ветки должны вызывать эту функцию с with_headers=False.
    """
    base_url = 'https://nspd.gov.ru/api/aeggis/v{}/{}/wms'.format(api_version, layer_id)
    final_url = urllib.parse.quote(base_url, safe='') if encode_url else base_url

    params = [
        ('crs', 'EPSG:3857'),
        ('format', 'image/png'),
        ('layers', str(layer_id)),
        ('styles', ''),
        ('url', final_url),
    ]

    if not simple:
        params.extend([
            ('dpiMode', '0'),
            ('maxHeight', '512'),
            ('maxWidth', '512'),
            ('transparent', 'true'),
        ])

    if with_headers:
        params.append((referer_header, 'https://nspd.gov.ru/map'))
        if referer_header != 'http-header:referer':
            params.append(('http-header:referer', 'https://nspd.gov.ru/map'))
        params.append(('http-header:origin', XYZ_ORIGIN))
        params.append(('http-header:user-agent', XYZ_UA))
        if NSPD_AUTH_TOKEN:
            params.append(('http-header:authorization', 'Bearer {}'.format(NSPD_AUTH_TOKEN)))

    # Важно: если url уже закодирован вручную, не раскодировать его через safe.
    safe = '/:?=&' if not encode_url else '=&'
    return urllib.parse.urlencode(params, doseq=True, safe=safe)


def build_wms_uri_provider_registry(layer_id, api_version=3):
    """Пробует собрать URI через QgsProviderRegistry.encodeUri.
    На QGIS 3.40/3.44 это безопаснее ручной склейки строки.
    """
    try:
        base_url = 'https://nspd.gov.ru/api/aeggis/v{}/{}/wms'.format(api_version, layer_id)
        params = {
            'url': base_url,
            'layers': str(layer_id),
            'styles': '',
            'format': 'image/png',
            'crs': 'EPSG:3857',
            'dpiMode': 0,
            'transparent': True,
        }
        reg = QgsProviderRegistry.instance()
        if hasattr(reg, 'encodeUri'):
            uri = reg.encodeUri('wms', params)
            if uri:
                return uri
    except Exception:
        pass
    return None


def build_wms_uri_legacy(layer_id, api_version=3):
    """Старый URI-формат, который стабильно работал в QGIS 3.28/3.34."""
    wms_url = (
        'crs=EPSG:3857&dpiMode=0&format=image/png&layers={}&styles'
        '&maxHeight=512&maxWidth=512&url=https://nspd.gov.ru/api/aeggis/v{}/{}/wms'
        '&{}=https://nspd.gov.ru/map?active_layers%3D%E9%8B%8B'
    ).format(layer_id, api_version, layer_id, referer_header)
    return urllib.parse.quote(wms_url, safe='/?=:&')


def save_wms_connection_compat(layer_id, layer_name, api_version=3):
    """Сохраняет WMS-соединение в настройки QGIS сразу в старой и новой ветке.

    Для QGIS 3.40+ это основной путь совместимости: Browser/Connections
    часто принимает WMS-соединение корректнее, чем прямой inline URI.
    """
    conn_name = 'НСПД: ' + layer_name
    src_url = 'https://nspd.gov.ru/api/aeggis/v{}/{}/wms'.format(api_version, layer_id)
    s = QSettings()

    old_keys = [
        ('qgis/connections-wms/{}/url', src_url),
        ('qgis/connections-wms/{}/referer', 'https://nspd.gov.ru/map'),
        ('qgis/connections-wms/{}/ignoreGetMapURI', False),
        ('qgis/connections-wms/{}/ignoreGetFeatureInfoURI', False),
        ('qgis/connections-wms/{}/ignoreAxisOrientation', False),
        ('qgis/connections-wms/{}/invertAxisOrientation', False),
        ('qgis/connections-wms/{}/dpiMode', 0),
        ('qgis/connections-wms/{}/smoothPixmapTransform', False),
    ]

    # Пишем несколько вариантов ключей заголовков: разные сборки QGIS читают разные ветки.
    old_header_keys = [
        ('qgis/connections-wms/{}/http-header', build_xyz_http_header()),
        ('qgis/connections-wms/{}/http-header:referer', XYZ_REFERRER),
        ('qgis/connections-wms/{}/http-header:origin', XYZ_ORIGIN),
        ('qgis/connections-wms/{}/http-header:user-agent', XYZ_UA),
    ]

    new_keys = [
        ('connections/ows/items/wms/connections/items/{}/url', src_url),
        ('connections/ows/items/wms/connections/items/{}/http-header', build_xyz_http_header()),
        ('connections/ows/items/wms/connections/items/{}/ignore-axis-orientation', False),
        ('connections/ows/items/wms/connections/items/{}/ignore-get-map-uri', False),
        ('connections/ows/items/wms/connections/items/{}/ignore-get-feature-info-uri', False),
        ('connections/ows/items/wms/connections/items/{}/invert-axis-orientation', False),
        ('connections/ows/items/wms/connections/items/{}/dpi-mode', 0),
        ('connections/ows/items/wms/connections/items/{}/smooth-pixmap-transform', False),
        ('connections/ows/items/wms/connections/items/{}/tile-pixel-ratio', 0),
        ('connections/ows/items/wms/connections/items/{}/reported-layer-extents', ''),
    ]

    for k, v in old_keys + old_header_keys + new_keys:
        s.setValue(k.format(conn_name), v)

    try:
        iface.reloadConnections()
    except Exception:
        pass

    return conn_name


def try_add_wms_attempts(layer_id, name, attempts):
    errors = []
    for label, uri in attempts:
        if not uri:
            continue
        try:
            layer = QgsRasterLayer(uri, 'НСПД: ' + name, 'wms')
            if layer.isValid():
                apply_nspd_raster_scale_guard(layer, NSPD_RASTER_MIN_VISIBLE_SCALE)
                layer.setCustomProperty('nspd_wms_attempt', label)
                layer.setCustomProperty('nspd_layer_id', layer_id)
                QgsProject.instance().addMapLayer(layer)
                warn_if_canvas_scale_is_too_small('НСПД: ' + name, NSPD_RASTER_MIN_VISIBLE_SCALE)
                return layer, errors
            errors.append('{}: {}'.format(label, get_layer_error_text(layer)))
        except Exception as e:
            errors.append('{}: {}'.format(label, str(e)))
    return None, errors


def add_wms_layer(num, name):
    """WMS fallback v12.

    3.28/3.34: direct-uri-first, потому что это уже подтверждённо работает.
    3.40/3.44+: connection-first + provider-registry/no-header URI.
    """
    layer_id = int(num)
    qv = qgis_version_int()
    api_versions = [3, 4]

    if any(f in name.lower() for f in ['зоуит']):
        api_versions = [4, 3]

    # QGIS 3.40+ строже валидирует provider URI. Сначала сохраняем соединения.
    if qv >= 34000:
        for api_version in api_versions:
            save_wms_connection_compat(layer_id, name, api_version)

        attempts = []
        for api_version in api_versions:
            attempts.append(('provider_registry_v{}'.format(api_version), build_wms_uri_provider_registry(layer_id, api_version)))
            attempts.append(('strict_encoded_url_v{}'.format(api_version), build_wms_uri(layer_id, api_version, simple=False, with_headers=False, encode_url=True)))
            attempts.append(('strict_simple_encoded_url_v{}'.format(api_version), build_wms_uri(layer_id, api_version, simple=True, with_headers=False, encode_url=True)))
            attempts.append(('plain_no_headers_v{}'.format(api_version), build_wms_uri(layer_id, api_version, simple=True, with_headers=False, encode_url=False)))

        layer, errors = try_add_wms_attempts(layer_id, name, attempts)
        if layer:
            return layer

        msg = QMessageBox(iface.mainWindow())
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setWindowTitle("НСПД: WMS сохранён как соединение")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setText(
            "Прямое добавление WMS в QGIS 3.40+ не сработало, но соединение сохранено в Browser/Connections.<br><br>"
            "<b>Слой:</b> {}<br>"
            "<b>ID:</b> {}<br>"
            "<b>QGIS:</b> {}<br><br>"
            "Откройте Browser → WMS/WMTS или WMS/OGC API → <b>НСПД: {}</b>.<br><br>"
            "<b>Попытки прямого добавления:</b><br>{}".format(
                name,
                layer_id,
                QGIS_V,
                name,
                '<br>'.join(errors[:12]) if errors else 'нет подробностей'
            )
        )
        msg.exec()
        return None

    # Старые/рабочие версии: оставляем direct-uri-first.
    attempts = []
    for api_version in api_versions:
        attempts.append(('legacy_v{}'.format(api_version), build_wms_uri_legacy(layer_id, api_version)))
        attempts.append(('full_v{}'.format(api_version), build_wms_uri(layer_id, api_version, simple=False, with_headers=True)))
        attempts.append(('simple_v{}'.format(api_version), build_wms_uri(layer_id, api_version, simple=True, with_headers=True)))
        attempts.append(('simple_no_headers_v{}'.format(api_version), build_wms_uri(layer_id, api_version, simple=True, with_headers=False)))

    layer, errors = try_add_wms_attempts(layer_id, name, attempts)
    if layer:
        return layer

    save_wms_connection_compat(layer_id, name, api_versions[0])

    msg = QMessageBox(iface.mainWindow())
    msg.setTextFormat(Qt.TextFormat.RichText)
    msg.setWindowTitle("НСПД: ошибка рендера WMS")
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.setText(
        "Подложка не добавилась напрямую, но WMS-соединение сохранено в Browser/Connections.<br><br>"
        "<b>Слой:</b> {}<br>"
        "<b>ID:</b> {}<br>"
        "<b>QGIS:</b> {}<br><br>"
        "<b>Попытки:</b><br>{}".format(
            name,
            layer_id,
            QGIS_V,
            '<br>'.join(errors[:12])
        )
    )
    msg.exec()
    return None
    

def get_canvas_center_mercator():
    """Возвращает центр текущего canvas в EPSG:3857 для проверки XYZ-тайла."""
    try:
        canvas = iface.mapCanvas()
        center = canvas.extent().center()
        src_crs = canvas.mapSettings().destinationCrs()
        if not src_crs or not src_crs.isValid():
            src_crs = QgsProject.instance().crs()
        if src_crs and src_crs.isValid() and src_crs.authid() != crs_mercator.authid():
            transform = QgsCoordinateTransform(src_crs, crs_mercator, QgsProject.instance())
            center = transform.transform(center)
        return center
    except Exception:
        return QgsPointXY(0, 0)


def get_canvas_extent_mercator():
    """Возвращает текущий охват canvas в EPSG:3857."""
    try:
        canvas = iface.mapCanvas()
        extent = QgsRectangle(canvas.extent())
        src_crs = canvas.mapSettings().destinationCrs()
        if not src_crs or not src_crs.isValid():
            src_crs = QgsProject.instance().crs()
        if src_crs and src_crs.isValid() and src_crs.authid() != crs_mercator.authid():
            transform = QgsCoordinateTransform(src_crs, crs_mercator, QgsProject.instance())
            extent = transform.transformBoundingBox(extent)
        return extent
    except Exception:
        return QgsRectangle(-WEB_MERCATOR_HALF_WORLD, -WEB_MERCATOR_HALF_WORLD, WEB_MERCATOR_HALF_WORLD, WEB_MERCATOR_HALF_WORLD)


def get_canvas_resolution_mercator():
    try:
        canvas = iface.mapCanvas()
        size = canvas.mapSettings().outputSize()
        width_px = max(1, int(size.width()))
        extent = get_canvas_extent_mercator()
        return abs(float(extent.width()) / float(width_px))
    except Exception:
        scale = current_canvas_scale() or 1.0
        return scale / 3779.527559055118


def get_canvas_xyz_zoom():
    try:
        resolution = max(get_canvas_resolution_mercator(), 0.000001)
        z = int(round(math.log(NSPD_WEB_MERCATOR_INITIAL_RESOLUTION / resolution, 2)))
        return max(NSPD_XYZ_Z_MIN_DEFAULT, min(NSPD_ORTHO_Z_PROBE_MAX, z))
    except Exception:
        return NSPD_ORTHO_Z_MIN_FALLBACK


def mercator_point_to_xyz_tile(point, z):
    """Преобразует точку EPSG:3857 в номер XYZ-тайла."""
    tiles_per_axis = 2 ** int(z)
    x = max(-WEB_MERCATOR_HALF_WORLD, min(WEB_MERCATOR_HALF_WORLD, float(point.x())))
    y = max(-WEB_MERCATOR_HALF_WORLD, min(WEB_MERCATOR_HALF_WORLD, float(point.y())))
    tile_x = int((x + WEB_MERCATOR_HALF_WORLD) / (2 * WEB_MERCATOR_HALF_WORLD) * tiles_per_axis)
    tile_y = int((WEB_MERCATOR_HALF_WORLD - y) / (2 * WEB_MERCATOR_HALF_WORLD) * tiles_per_axis)
    tile_x = max(0, min(tiles_per_axis - 1, tile_x))
    tile_y = max(0, min(tiles_per_axis - 1, tile_y))
    return tile_x, tile_y


def build_xyz_tile_url(layer_id, z, x, y):
    return wmts_url_template.format(int(layer_id)).format(z=int(z), x=int(x), y=int(y))


def xyz_tile_bounds_mercator(x, y, z):
    tiles_per_axis = 2 ** int(z)
    tile_size = (2 * WEB_MERCATOR_HALF_WORLD) / tiles_per_axis
    min_x = -WEB_MERCATOR_HALF_WORLD + int(x) * tile_size
    max_x = min_x + tile_size
    max_y = WEB_MERCATOR_HALF_WORLD - int(y) * tile_size
    min_y = max_y - tile_size
    return min_x, min_y, max_x, max_y


def get_canvas_xyz_tile_range(z):
    extent = get_canvas_extent_mercator()
    return get_extent_xyz_tile_range(extent, z)


def get_extent_xyz_tile_range(extent, z):
    p1 = QgsPointXY(extent.xMinimum(), extent.yMaximum())
    p2 = QgsPointXY(extent.xMaximum(), extent.yMinimum())
    x_min, y_min = mercator_point_to_xyz_tile(p1, z)
    x_max, y_max = mercator_point_to_xyz_tile(p2, z)
    if x_min > x_max:
        x_min, x_max = x_max, x_min
    if y_min > y_max:
        y_min, y_max = y_max, y_min
    return x_min, x_max, y_min, y_max


def tile_range_count(x_min, x_max, y_min, y_max):
    return max(0, int(x_max) - int(x_min) + 1) * max(0, int(y_max) - int(y_min) + 1)


def write_png_world_files(png_path, x_min, y_min, x_max, y_max, width_px, height_px):
    pixel_x = (float(x_max) - float(x_min)) / float(width_px)
    pixel_y = (float(y_max) - float(y_min)) / float(height_px)
    pgw_path = os.path.splitext(png_path)[0] + '.pgw'
    prj_path = os.path.splitext(png_path)[0] + '.prj'
    with open(pgw_path, 'w', encoding='ascii') as f:
        f.write('{:.12f}\n'.format(pixel_x))
        f.write('0.0\n')
        f.write('0.0\n')
        f.write('{:.12f}\n'.format(-pixel_y))
        f.write('{:.12f}\n'.format(float(x_min) + pixel_x / 2.0))
        f.write('{:.12f}\n'.format(float(y_max) - pixel_y / 2.0))
    with open(prj_path, 'w', encoding='utf-8') as f:
        f.write(crs_mercator.toWkt())
    return pgw_path, prj_path


def make_unique_export_folder(base_dir, layer_name, z):
    safe_name = raster_export_folder_alias(layer_name)
    stamp = time.strftime('%Y%m%d_%H%M%S')
    folder_name = 'nspd_{}_z{}_{}'.format(safe_name, int(z), stamp)
    candidate = os.path.join(base_dir, folder_name)
    counter = 2
    while os.path.exists(candidate):
        candidate = os.path.join(base_dir, '{}_{}'.format(folder_name, counter))
        counter += 1
    os.makedirs(candidate, exist_ok=False)
    os.makedirs(os.path.join(candidate, 'tiles'), exist_ok=True)
    return candidate


def get_qstandard_path(location_name):
    try:
        location = getattr(QStandardPaths, location_name, None)
        if location is None and hasattr(QStandardPaths, 'StandardLocation'):
            location = getattr(QStandardPaths.StandardLocation, location_name, None)
        if location is None:
            return ''
        path = QStandardPaths.writableLocation(location)
        return path if path and os.path.isdir(path) else ''
    except Exception:
        return ''


def get_default_raster_export_dir():
    settings = QSettings()
    remembered = str(settings.value('nspd_navigator/last_raster_export_dir', '') or '')
    if remembered and os.path.isdir(remembered):
        return remembered

    project_dir = ''
    try:
        project_dir = QgsProject.instance().homePath() or ''
    except Exception:
        project_dir = ''
    if project_dir and os.path.isdir(project_dir):
        return project_dir

    downloads_dir = get_qstandard_path('DownloadLocation')
    if downloads_dir:
        return downloads_dir

    home_dir = get_qstandard_path('HomeLocation')
    if home_dir:
        return home_dir

    return os.path.expanduser('~')


def remember_raster_export_dir(path):
    if path and os.path.isdir(path):
        QSettings().setValue('nspd_navigator/last_raster_export_dir', path)


def qimage_rgba_format():
    fmt = getattr(QImage, 'Format_RGBA8888', None)
    if fmt is not None:
        return fmt
    fmt = getattr(QImage, 'Format_ARGB32', None)
    if fmt is not None:
        return fmt
    return QImage.Format.Format_ARGB32


def make_transparent_tile(path):
    image = QImage(NSPD_XYZ_TILE_SIZE_PX, NSPD_XYZ_TILE_SIZE_PX, qimage_rgba_format())
    image.fill(QColor(0, 0, 0, 0))
    image.save(path, 'PNG')


def raster_export_folder_alias(layer_name):
    name = safe_layer_name(layer_name).replace(' ', '_')
    name_lower = name.lower()
    if 'дзз' in name_lower:
        return 'dzz'
    if 'цифровая_объектовая_схема' in name_lower:
        return 'scheme'
    if 'ортофотопланы_2000' in name_lower:
        return 'ortho2000'
    if 'ортофотопланы_10000' in name_lower:
        return 'ortho10000'
    if (
        'основной_слой' in name_lower
        and 'ортофото' not in name_lower
        and ('еэко' in name_lower or 'единая_электронная_картографическая_основа' in name_lower)
    ):
        return 'eeko'
    if 'ортофото' in name_lower or 'еэко' in name_lower:
        return 'ortho'
    if 'топограф' in name_lower:
        return 'topo'
    return name[:32] if name else 'layer'


def write_xyz_vrt(vrt_path, tile_dir, z, x_min, x_max, y_min, y_max, srs_wkt):
    cols = int(x_max) - int(x_min) + 1
    rows = int(y_max) - int(y_min) + 1
    width = cols * NSPD_XYZ_TILE_SIZE_PX
    height = rows * NSPD_XYZ_TILE_SIZE_PX
    min_x, _, _, max_y = xyz_tile_bounds_mercator(x_min, y_min, z)
    _, min_y, max_x, _ = xyz_tile_bounds_mercator(x_max, y_max, z)
    pixel_x = (float(max_x) - float(min_x)) / float(width)
    pixel_y = (float(max_y) - float(min_y)) / float(height)

    rel_tile_dir = os.path.relpath(tile_dir, os.path.dirname(vrt_path)).replace('\\', '/')
    srs = xml_escape(srs_wkt)
    color_names = ['Red', 'Green', 'Blue', 'Alpha']

    lines = [
        '<VRTDataset rasterXSize="{}" rasterYSize="{}">'.format(width, height),
        '  <SRS>{}</SRS>'.format(srs),
        '  <GeoTransform>{:.12f}, {:.12f}, 0.0, {:.12f}, 0.0, {:.12f}</GeoTransform>'.format(
            float(min_x),
            pixel_x,
            float(max_y),
            -pixel_y
        )
    ]

    for band_index, color_name in enumerate(color_names, start=1):
        lines.append('  <VRTRasterBand dataType="Byte" band="{}">'.format(band_index))
        lines.append('    <ColorInterp>{}</ColorInterp>'.format(color_name))
        for ty in range(int(y_min), int(y_max) + 1):
            for tx in range(int(x_min), int(x_max) + 1):
                tile_name = 'tile_{}_{}_{}.png'.format(int(z), tx, ty)
                source_path = xml_escape('{}/{}'.format(rel_tile_dir, tile_name))
                dst_x = (tx - int(x_min)) * NSPD_XYZ_TILE_SIZE_PX
                dst_y = (ty - int(y_min)) * NSPD_XYZ_TILE_SIZE_PX
                lines.extend([
                    '    <SimpleSource>',
                    '      <SourceFilename relativeToVRT="1">{}</SourceFilename>'.format(source_path),
                    '      <SourceBand>{}</SourceBand>'.format(band_index),
                    '      <SrcRect xOff="0" yOff="0" xSize="{0}" ySize="{0}"/>'.format(NSPD_XYZ_TILE_SIZE_PX),
                    '      <DstRect xOff="{0}" yOff="{1}" xSize="{2}" ySize="{2}"/>'.format(dst_x, dst_y, NSPD_XYZ_TILE_SIZE_PX),
                    '    </SimpleSource>'
                ])
        lines.append('  </VRTRasterBand>')

    lines.append('</VRTDataset>')
    with open(vrt_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return vrt_path


def export_xyz_canvas_to_png(layer_id, layer_name, output_png_path=None):
    z = get_canvas_xyz_zoom()
    zoom_info = get_xyz_zoom_info(layer_id)
    if int(layer_id) in NSPD_ORTHO_LAYER_IDS:
        z = max(int(zoom_info['zmin']), min(int(zoom_info['zmax']), int(z)))

    x_min, x_max, y_min, y_max = get_canvas_xyz_tile_range(z)
    tile_count = (x_max - x_min + 1) * (y_max - y_min + 1)
    if tile_count <= 0:
        return False, 'Не удалось определить тайлы текущего охвата.', None

    if not output_png_path:
        project_dir = QgsProject.instance().homePath() or tempfile.gettempdir()
        safe_name = safe_layer_name(layer_name).replace(' ', '_')[:60]
        default_path = os.path.join(project_dir, 'nspd_{}_z{}.png'.format(safe_name, z))
        output_png_path, _ = QFileDialog.getSaveFileName(
            iface.mainWindow(),
            'Сохранить фрагмент растра НСПД',
            default_path,
            'PNG (*.png)'
        )
        if not output_png_path:
            return False, 'Выгрузка отменена.', None
        if not output_png_path.lower().endswith('.png'):
            output_png_path += '.png'

    width = (x_max - x_min + 1) * NSPD_XYZ_TILE_SIZE_PX
    height = (y_max - y_min + 1) * NSPD_XYZ_TILE_SIZE_PX
    image_format = getattr(QImage, 'Format_ARGB32', None)
    if image_format is None:
        image_format = QImage.Format.Format_ARGB32
    mosaic = QImage(width, height, image_format)
    mosaic.fill(QColor(0, 0, 0, 0))

    painter = QPainter(mosaic)
    downloaded = 0
    errors = []
    headers = get_nspd_http_headers(for_tiles=True)

    try:
        for ty in range(y_min, y_max + 1):
            for tx in range(x_min, x_max + 1):
                url = build_xyz_tile_url(layer_id, z, tx, ty)
                try:
                    response = requests.get(
                        url,
                        headers=headers,
                        verify=False,
                        timeout=NSPD_RASTER_EXPORT_TIMEOUT
                    )
                    if response.status_code != 200:
                        errors.append('HTTP {}: {}/{}/{}'.format(response.status_code, z, tx, ty))
                        continue
                    tile = QImage()
                    if not tile.loadFromData(response.content):
                        errors.append('not image: {}/{}/{}'.format(z, tx, ty))
                        continue
                    painter.drawImage((tx - x_min) * NSPD_XYZ_TILE_SIZE_PX, (ty - y_min) * NSPD_XYZ_TILE_SIZE_PX, tile)
                    downloaded += 1
                except Exception as e:
                    errors.append('{}: {}/{}/{}'.format(str(e), z, tx, ty))
    finally:
        painter.end()

    if downloaded == 0:
        return False, 'Не скачан ни один тайл. Первые ошибки:<br>{}'.format('<br>'.join(errors[:8])), None

    if not mosaic.save(output_png_path, 'PNG'):
        return False, 'Не удалось сохранить PNG: {}'.format(output_png_path), None

    min_x, _, _, max_y = xyz_tile_bounds_mercator(x_min, y_min, z)
    _, min_y, max_x, _ = xyz_tile_bounds_mercator(x_max, y_max, z)
    write_png_world_files(output_png_path, min_x, min_y, max_x, max_y, width, height)

    layer = QgsRasterLayer(output_png_path, 'НСПД_выгрузка_{}_z{}'.format(layer_name, z))
    if layer.isValid():
        layer.setCrs(crs_mercator)
        QgsProject.instance().addMapLayer(layer)

    msg = 'Скачано тайлов: {} из {}.<br>z={}<br>{}'.format(downloaded, tile_count, z, output_png_path)
    if errors:
        msg += '<br><br>Ошибки первых тайлов:<br>{}'.format('<br>'.join(errors[:8]))
    return True, msg, output_png_path


class NSPDRasterExportThread(QThread):
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    export_completed = pyqtSignal(dict)

    def __init__(self, layer_id, layer_name, extent_mercator, z, output_vrt_path):
        super().__init__()
        self.layer_id = int(layer_id)
        self.layer_name = str(layer_name)
        self.extent_mercator = QgsRectangle(extent_mercator)
        self.z = int(z)
        self.output_vrt_path = str(output_vrt_path)
        self._cancel_requested = False
        self.srs_wkt = crs_mercator.toWkt()

        self.x_min, self.x_max, self.y_min, self.y_max = get_extent_xyz_tile_range(self.extent_mercator, self.z)
        self.total_tiles = tile_range_count(self.x_min, self.x_max, self.y_min, self.y_max)
        self.tile_last_modified_examples = []

    def cancel(self):
        self._cancel_requested = True

    def tile_path(self, tx, ty):
        return os.path.join(self.tile_dir, 'tile_{}_{}_{}.png'.format(self.z, int(tx), int(ty)))

    def add_tile_last_modified_example(self, value):
        value = str(value or '').strip()
        if not value:
            return
        if value in self.tile_last_modified_examples:
            return
        if len(self.tile_last_modified_examples) >= NSPD_RASTER_METADATA_LAST_MODIFIED_LIMIT:
            return
        self.tile_last_modified_examples.append(value)

    def write_export_metadata(self, base_dir, downloaded, errors, retries, started_at, finished_at):
        layer_metadata = fetch_nspd_layer_metadata(self.layer_id)
        layer_metadata_summary = summarize_nspd_layer_metadata(layer_metadata)
        source_date_candidates = layer_metadata_summary.get('source_date_candidates') or []
        metadata = {
            'schema': 'nspd_raster_export_metadata_v1',
            'layer_id': self.layer_id,
            'layer_name': self.layer_name,
            'z': self.z,
            'download_started': started_at,
            'download_finished': finished_at,
            'qgis_version': QGIS_V,
            'source_url_template': wmts_url_template.format(self.layer_id),
            'vrt_path': self.output_vrt_path,
            'tile_dir': self.tile_dir,
            'tile_range': {
                'x_min': int(self.x_min),
                'x_max': int(self.x_max),
                'y_min': int(self.y_min),
                'y_max': int(self.y_max)
            },
            'total_tiles': int(self.total_tiles),
            'downloaded_tiles': int(downloaded),
            'error_tiles': int(errors),
            'retries': int(retries),
            'tile_last_modified_examples': list(self.tile_last_modified_examples),
            'layer_metadata': layer_metadata_summary,
            'capture_date': None,
            'capture_date_source': 'not_found_in_tile_png_or_public_layer_api',
            'capture_date_candidate_source': 'source_url_or_layer_name' if source_date_candidates else None,
            'notes': [
                'tile_last_modified_examples are HTTP server/cache dates, not confirmed imagery acquisition dates',
                'layer_metadata.system_updated is an NSPD layer/service update date, not confirmed imagery acquisition date',
                'layer_metadata.source_date_candidates are parsed from source URL/name and are not confirmed imagery acquisition dates'
            ]
        }
        if isinstance(layer_metadata, dict) and layer_metadata.get('fetch_error'):
            metadata['layer_metadata_fetch_error'] = layer_metadata.get('fetch_error')
            metadata['layer_metadata_url'] = layer_metadata.get('url')

        metadata_path = os.path.join(base_dir, NSPD_RASTER_METADATA_FILE_NAME)
        write_raster_export_metadata(metadata_path, metadata)
        return metadata_path, metadata

    def download_tile(self, tx, ty):
        path = self.tile_path(tx, ty)
        url = build_xyz_tile_url(self.layer_id, self.z, tx, ty)
        headers = get_nspd_http_headers(for_tiles=True)
        last_error = ''
        retries_used = 0

        for attempt in range(1, NSPD_RASTER_TILE_RETRY_COUNT + 1):
            if self._cancel_requested:
                return False, retries_used, 'cancelled'

            try:
                response = requests.get(
                    url,
                    headers=headers,
                    verify=False,
                    timeout=NSPD_RASTER_EXPORT_TIMEOUT
                )

                if response.status_code == 200:
                    image = QImage()
                    if image.loadFromData(response.content):
                        image = image.convertToFormat(qimage_rgba_format())
                        if image.save(path, 'PNG'):
                            self.add_tile_last_modified_example(response.headers.get('Last-Modified'))
                            return True, retries_used, ''
                        last_error = 'save failed'
                    else:
                        last_error = 'not image'
                else:
                    last_error = 'HTTP {}'.format(response.status_code)
                    if response.status_code not in [408, 429, 500, 502, 503, 504]:
                        break

            except Exception as e:
                last_error = str(e)

            if attempt < NSPD_RASTER_TILE_RETRY_COUNT:
                retries_used += 1
                time.sleep(random.uniform(NSPD_RASTER_TILE_RETRY_DELAY_MIN, NSPD_RASTER_TILE_RETRY_DELAY_MAX))

        make_transparent_tile(path)
        return False, retries_used, last_error

    def run(self):
        result = {
            'ok': False,
            'cancelled': False,
            'layer_name': self.layer_name,
            'vrt_path': self.output_vrt_path,
            'tile_dir': '',
            'z': self.z,
            'total': self.total_tiles,
            'downloaded': 0,
            'errors': 0,
            'retries': 0,
            'metadata_path': '',
            'metadata_error': '',
            'metadata_dates_message': '',
            'message': ''
        }

        if self.total_tiles <= 0:
            result['message'] = 'Не удалось определить тайлы выбранного охвата.'
            self.export_completed.emit(result)
            return

        base_dir = os.path.dirname(self.output_vrt_path) or tempfile.gettempdir()
        self.tile_dir = os.path.join(base_dir, 'tiles')
        os.makedirs(self.tile_dir, exist_ok=True)
        result['tile_dir'] = self.tile_dir
        result['metadata_path'] = os.path.join(base_dir, NSPD_RASTER_METADATA_FILE_NAME)

        done = 0
        downloaded = 0
        errors = 0
        retries = 0
        started_at = time.strftime('%Y-%m-%dT%H:%M:%S')

        for ty in range(int(self.y_min), int(self.y_max) + 1):
            for tx in range(int(self.x_min), int(self.x_max) + 1):
                if self._cancel_requested:
                    result['cancelled'] = True
                    result['message'] = 'Выгрузка отменена.'
                    self.export_completed.emit(result)
                    return

                ok, tile_retries, error_text = self.download_tile(tx, ty)
                retries += int(tile_retries or 0)
                if ok:
                    downloaded += 1
                else:
                    errors += 1

                done += 1
                self.progress_updated.emit(int((done / max(1, self.total_tiles)) * 100))
                self.status_updated.emit(
                    'Статус: тайлы {}/{} · {:.1f}% · повторы {} · ошибки {} · z={}'.format(
                        done,
                        self.total_tiles,
                        (done / max(1, self.total_tiles)) * 100.0,
                        retries,
                        errors,
                        self.z
                    )
                )

        result['downloaded'] = downloaded
        result['errors'] = errors
        result['retries'] = retries
        finished_at = time.strftime('%Y-%m-%dT%H:%M:%S')
        try:
            metadata_path, metadata = self.write_export_metadata(
                base_dir,
                downloaded,
                errors,
                retries,
                started_at,
                finished_at
            )
            result['metadata_path'] = metadata_path
            result['metadata_dates_message'] = format_raster_metadata_dates_for_message(metadata)
        except Exception as e:
            result['metadata_error'] = str(e)

        try:
            write_xyz_vrt(
                self.output_vrt_path,
                self.tile_dir,
                self.z,
                self.x_min,
                self.x_max,
                self.y_min,
                self.y_max,
                self.srs_wkt
            )
            result['ok'] = True
            result['downloaded'] = downloaded
            result['errors'] = errors
            result['retries'] = retries
            result['message'] = (
                'Выгрузка завершена.<br>'
                'Тайлы: {} из {}<br>'
                'Повторов: {}<br>'
                'Ошибок: {}<br>'
                'z={}<br>{}'
            ).format(downloaded, self.total_tiles, retries, errors, self.z, self.output_vrt_path)
        except Exception as e:
            result['message'] = 'Тайлы скачаны, но VRT не создан: {}'.format(e)

        if result.get('metadata_dates_message'):
            result['message'] += '<br><br>{}'.format(result.get('metadata_dates_message'))
        if result.get('metadata_error'):
            result['message'] += '<br>metadata.json error: {}'.format(result.get('metadata_error'))
        elif result.get('metadata_path'):
            result['message'] += '<br>metadata.json: {}'.format(result.get('metadata_path'))

        self.export_completed.emit(result)


def probe_xyz_tile(layer_id, z, center_mercator=None):
    """Проверяет один XYZ-тайл через requests. Нужна только для подбора native zoom."""
    if center_mercator is None:
        center_mercator = get_canvas_center_mercator()

    x, y = mercator_point_to_xyz_tile(center_mercator, z)
    url = build_xyz_tile_url(layer_id, z, x, y)

    try:
        response = requests.get(
            url,
            headers=get_nspd_http_headers(for_tiles=True),
            verify=False,
            timeout=NSPD_ORTHO_TILE_PROBE_TIMEOUT
        )
        content_type = response.headers.get('content-type', '').lower()
        content = response.content or b''
        is_png = content.startswith(b'\x89PNG') or 'image/png' in content_type
        if response.status_code == 200 and is_png and len(content) > 64:
            return True, 'HTTP 200 PNG {} bytes'.format(len(content))
        return False, 'HTTP {} {} {} bytes'.format(response.status_code, content_type or 'unknown', len(content))
    except Exception as e:
        return False, str(e)


def detect_ortho_native_zoom_range(layer_id):
    """Определяет рабочий диапазон zoom для ортофото НСПД в текущей области карты."""
    layer_id = int(layer_id)
    cache_key = layer_id
    if cache_key in _NSPD_XYZ_ZOOM_CACHE:
        return _NSPD_XYZ_ZOOM_CACHE[cache_key]

    if not NSPD_ORTHO_PROBE_ZOOM_ON_ADD:
        result = {
            'zmin': NSPD_ORTHO_Z_MIN_FALLBACK,
            'zmax': NSPD_ORTHO_Z_MAX_FALLBACK,
            'detected': False,
            'details': {'probe': 'disabled'}
        }
        _NSPD_XYZ_ZOOM_CACHE[cache_key] = result
        return result

    center = get_canvas_center_mercator()
    checked = {}
    ok_zooms = set()

    def check_zoom(z):
        if z in checked:
            return checked[z][0]
        ok, detail = probe_xyz_tile(layer_id, z, center)
        checked[z] = (ok, detail)
        if ok:
            ok_zooms.add(z)
        return ok

    # Сначала проверяем типичный диапазон ортофото, чтобы не задерживать UI лишними запросами.
    for z in range(NSPD_ORTHO_Z_MIN_FALLBACK, NSPD_ORTHO_Z_MAX_FALLBACK + 1):
        check_zoom(z)

    if ok_zooms:
        zmin = min(ok_zooms)
        while zmin > NSPD_ORTHO_Z_PROBE_MIN and check_zoom(zmin - 1):
            zmin -= 1

        zmax = max(ok_zooms)
        while zmax < NSPD_ORTHO_Z_PROBE_MAX and check_zoom(zmax + 1):
            zmax += 1

        result = {
            'zmin': int(zmin),
            'zmax': int(zmax),
            'detected': True,
            'details': checked
        }
    else:
        result = {
            'zmin': NSPD_ORTHO_Z_MIN_FALLBACK,
            'zmax': NSPD_ORTHO_Z_MAX_FALLBACK,
            'detected': False,
            'details': checked
        }

    _NSPD_XYZ_ZOOM_CACHE[cache_key] = result
    return result


def get_xyz_zoom_info(layer_id):
    layer_id = int(layer_id)
    if layer_id in NSPD_ORTHO_LAYER_IDS:
        return detect_ortho_native_zoom_range(layer_id)
    return {
        'zmin': NSPD_XYZ_Z_MIN_DEFAULT,
        'zmax': NSPD_XYZ_Z_MAX_DEFAULT,
        'detected': False,
        'details': {}
    }


def build_xyz_layer_uri(layer_id, zmin=None, zmax=None, with_headers=True):
    url = wmts_url_template.format(int(layer_id))
    zmin = NSPD_XYZ_Z_MIN_DEFAULT if zmin is None else int(zmin)
    zmax = NSPD_XYZ_Z_MAX_DEFAULT if zmax is None else int(zmax)

    uri_parts = [
        "type=xyz",
        "url={}".format(urllib.parse.quote(url, safe='/:?=&{}')),
        "zmin={}".format(zmin),
        "zmax={}".format(zmax),
    ]

    if with_headers:
        headers = get_nspd_http_headers(for_tiles=True)
        uri_parts.append("{}={}".format(referer_header, urllib.parse.quote(headers['Referer'], safe='/:?=&')))
        uri_parts.append("http-header:referer={}".format(urllib.parse.quote(headers['Referer'], safe='/:?=&')))
        uri_parts.append("http-header:origin={}".format(urllib.parse.quote(headers['Origin'], safe='/:?=&')))
        uri_parts.append("http-header:user-agent={}".format(urllib.parse.quote(headers['User-Agent'], safe='/:?=&')))
        if 'Authorization' in headers:
            uri_parts.append("http-header:authorization={}".format(urllib.parse.quote(headers['Authorization'], safe='/:?=&')))

    return "&".join(uri_parts)


def add_xyz_layer(layer_id, name):
    zoom_info = get_xyz_zoom_info(layer_id)
    uri = build_xyz_layer_uri(layer_id, zoom_info['zmin'], zoom_info['zmax'], with_headers=True)
    min_visible_scale = NSPD_ORTHO_MIN_VISIBLE_SCALE if int(layer_id) in NSPD_ORTHO_LAYER_IDS else NSPD_RASTER_MIN_VISIBLE_SCALE

    layer = QgsRasterLayer(uri, 'НСПД: ' + name, 'wms')
    if layer.isValid():
        apply_nspd_raster_scale_guard(layer, min_visible_scale)
        layer.setCustomProperty('nspd_layer_id', int(layer_id))
        layer.setCustomProperty('nspd_xyz_zmin', int(zoom_info['zmin']))
        layer.setCustomProperty('nspd_xyz_zmax', int(zoom_info['zmax']))
        layer.setCustomProperty('nspd_xyz_zoom_detected', bool(zoom_info.get('detected')))
        QgsProject.instance().addMapLayer(layer)
        warn_if_canvas_scale_is_too_small('НСПД: ' + name, min_visible_scale)
        return

    # Вариант 2: если URI-заголовки не поддержались — сохраняем XYZ connection в настройках
    save_xyz_connection(layer_id, name, zoom_info['zmin'], zoom_info['zmax'])

    # Сообщение о типовой причине (403/Authorization). QGIS не отдаёт код ошибки сюда,
    # но на практике это либо отсутствие заголовков, либо требование Authorization.
    msg = QMessageBox(iface.mainWindow())
    msg.setTextFormat(Qt.TextFormat.RichText)
    msg.setWindowTitle("НСПД: WMTS")
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.setText(
        "Слой WMTS сохранён в соединениях (Browser → XYZ Tiles), но напрямую не добавился.<br>"
        "Если при открытии тайлов будет <b>403 Forbidden</b>, причина — отсутствующие HTTP-заголовки "
        "(Referer/UA) или требование <b>Authorization</b>.<br>"
        "В случае Authorization задай <b>NSPD_AUTH_TOKEN</b> в начале скрипта."
    )
    msg.exec()



def fill_items(parent_obj, folder_row, layers_meta):
    parent = QTreeWidgetItem(parent_obj)
    parent.setText(0, folder_row.get("title", ""))
    parent.setFlags(parent.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
    parent.setFlags(parent.flags() | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)

    layer_ids = folder_row.get("layers") or []
    for layer_id in layer_ids:
        meta = layers_meta.get(layer_id)
        if not meta:
            continue
        child = QTreeWidgetItem(parent)
        child.setData(0, Qt.ItemDataRole.UserRole, layer_id)
        child.setData(1, Qt.ItemDataRole.UserRole, meta.get('categoryId', None))
        child.setData(2, Qt.ItemDataRole.UserRole, meta.get('layerType', 'wms'))
        child.setText(0, meta.get('title', str(layer_id)))
        child.setFlags(child.flags() | Qt.ItemFlag.ItemIsDragEnabled)

    subfolders = folder_row.get("folders") or []
    for folder in subfolders:
        fill_items(parent, folder, layers_meta)


class MyDropHandler(QgsCustomDropHandler):
    """Drag and drop для конечных точек DraggableTree"""

    MIME = "application/x-nspd-layer"

    def canHandleMimeData(self, data):
        return data.hasFormat(self.MIME)

    def handleMimeData(self, data, *args):
        if not data.hasFormat(self.MIME):
            return

        raw = bytes(data.data(self.MIME)).decode("utf-8")
        parts = raw.split("|")
        if len(parts) < 2:
            return

        item_num = parts[0]
        item_name = parts[1]
        item_type = parts[2] if len(parts) >= 3 else "wms"

        if item_type == "wmts":
            add_xyz_layer(int(item_num), item_name)
        else:
            add_wms_layer(item_num, item_name)


class DraggableTree(QTreeWidget):
    """Кастомный QTreeWidget"""

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item or item.childCount() != 0:
            return

        item_num = item.data(0, Qt.ItemDataRole.UserRole)
        item_name = item.text(0)

        drag = QDrag(self)
        mime = QMimeData()

        item_type = item.data(2, Qt.ItemDataRole.UserRole) or "wms"
        payload = f"{item_num}|{item_name}|{item_type}"
        mime.setData(
            MyDropHandler.MIME,
            payload.encode("utf-8")
        )

        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)


class NSPDCadFinder(QThread):
    progress_updated = pyqtSignal(int)
    data_nspd_loaded = pyqtSignal(dict)  

    def __init__(self, cad_nums):
        self.cad_nums = cad_nums
        super().__init__()
    
    def run(self):
        num_split = len(self.cad_nums)
        step_layer = 100/num_split if num_split else 1
        step_counter = 0

        sample_geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        for cad_num in self.cad_nums:
            cad_num = cad_num.replace(':',  '%3A')
            nspd_url_search = 'https://nspd.gov.ru/api/geoportal/v2/search/geoportal?thematicSearchId=1&query={}'
            url = nspd_url_search.format(cad_num)
            s = requests.Session()
            attempt = 0
            data = {}
            while True:
                try:
                    if attempt==5:
                        break
                    r = s.get(url, verify=False, headers=nspd_headers_search)
                    if r.json():
                        data = r.json()
                        for f in data.get('data', {}).get('features', []):

                            f["properties"]['id'] = f['id']
                            f["properties"].update(f["properties"]["options"])
                            del f["properties"]["options"]
                            sample_geojson["features"].append(f)
                        step_counter+=step_layer
                        self.progress_updated.emit(int(step_counter))
                        time.sleep(1)
                        break
                except Exception as e:
                    attempt+=1
                    time.sleep(1)
                    pass 
        self.data_nspd_loaded.emit(sample_geojson)
        return 


def safe_layer_name(value):
    """Безопасное имя слоя QGIS для служебных слоёв процесса."""
    value = str(value).strip()
    value = re.sub(r'[\\/:*?"<>|]+', '_', value)
    value = re.sub(r'\s+', ' ', value)
    return value[:80] if value else 'layer'




def geom_bbox_hash_qgs(geom, precision=2):
    """Грубый пространственный отпечаток геометрии по типу и bbox.
    Нужен как дешёвая защита от дублей, когда НСПД отдаёт одну геометрию с разными id.
    """
    try:
        if geom is None or geom.isEmpty():
            return None
        bbox = geom.boundingBox()
        return (
            int(geom.type()),
            round(bbox.xMinimum(), precision),
            round(bbox.yMinimum(), precision),
            round(bbox.xMaximum(), precision),
            round(bbox.yMaximum(), precision)
        )
    except Exception:
        return None

def make_tile_items_from_bbox(left_x, bottom_y, right_x, top_y, tile_size=NSPD_TILE_SIZE):
    """
    Делит bbox EPSG:3857 на стабильную глобальную сетку тайлов.

    Важно: сетка привязана не к текущему выделению, а к координатной
    системе EPSG:3857 через кратность tile_size. Поэтому повторные
    допарсинги не создают смещённые тайлы, а попадают в те же tile_key.
    """
    tiles = []
    tile_id = 1

    if right_x <= left_x or top_y <= bottom_y:
        return tiles

    # Привязка к централизованной глобальной сетке.
    # Например при tile_size=3000 границы тайлов всегда кратны 3000 м.
    grid_left = math.floor(left_x / tile_size) * tile_size
    grid_bottom = math.floor(bottom_y / tile_size) * tile_size
    grid_right = math.ceil(right_x / tile_size) * tile_size
    grid_top = math.ceil(top_y / tile_size) * tile_size

    x = grid_left
    while x < grid_right:
        x2 = x + tile_size

        y = grid_bottom
        while y < grid_top:
            y2 = y + tile_size

            tile_key = "{}_{}_{}_{}".format(
                round(x, 2),
                round(y, 2),
                round(x2, 2),
                round(y2, 2)
            )

            coords = [
                [x, y],
                [x, y2],
                [x2, y2],
                [x2, y],
                [x, y]
            ]

            tiles.append({
                "tile_id": tile_id,
                "tile_key": tile_key,
                "coords": coords[::-1],
                "bbox": (x, y, x2, y2)
            })

            tile_id += 1
            y += tile_size

        x += tile_size

    return tiles


class NSPDGeomExtractTiled(QThread):
    """
    Пакетная многопоточная выгрузка объектов НСПД по большому охвату.
    Ветка v9: фиксированная глобальная сетка + динамическая очередь тайлов.

    Пользователь может добавлять новые охваты во время текущего сбора:
    новые тайлы добавляются в общую очередь, поток не перезапускается.
    QGIS-слои не трогаются из worker-потоков: worker возвращает только plain dict/list.
    """
    data_nspd_loaded = pyqtSignal(dict)
    batch_features_loaded = pyqtSignal(dict)
    progress_updated = pyqtSignal(int)
    tile_status_updated = pyqtSignal(str, str, int, int, int, float, str)

    def __init__(self, headers, base_data_pass, tiles, item_category):
        self.headers = headers.copy()
        self.base_data_pass = copy.deepcopy(base_data_pass)
        self.item_category = item_category
        self._cancel_requested = False

        self.queue_lock = threading.Lock()
        self.queue_counter = 0
        self.tiles_queue = []
        self.queued_tile_keys = set()
        self.total_tiles = 0
        self.completed_tiles = 0

        # Начальная очередь получает стабильный порядковый номер обработки.
        self.add_tiles(tiles)

        super().__init__()

    def cancel(self):
        """Мягкая отмена: новые тайлы больше не запускаются, текущие HTTP-запросы завершаются штатно."""
        self._cancel_requested = True

    def add_tiles(self, new_tiles):
        """Добавляет новые тайлы в живую очередь без перезапуска потока.
        Дубли по tile_key игнорируются.
        Возвращает количество реально добавленных тайлов.
        """
        if self._cancel_requested:
            return 0

        added = 0
        with self.queue_lock:
            for tile in new_tiles:
                tile_key = str(tile.get("tile_key"))
                if not tile_key or tile_key in self.queued_tile_keys:
                    continue

                self.queue_counter += 1
                tile["queue_order"] = self.queue_counter
                tile["worker_id"] = 0
                tile["attempts"] = 0
                tile["response_time"] = 0.0
                tile["updated"] = ""

                self.tiles_queue.append(copy.deepcopy(tile))
                self.queued_tile_keys.add(tile_key)
                added += 1

            if added:
                self.total_tiles += added

        return added

    def pop_next_tile(self):
        """Берёт следующий тайл из очереди потокобезопасно."""
        if self._cancel_requested:
            return None
        with self.queue_lock:
            if not self.tiles_queue:
                return None
            return self.tiles_queue.pop(0)

    def has_waiting_tiles(self):
        with self.queue_lock:
            return bool(self.tiles_queue)

    def emit_batch(self, batch_features):
        if not batch_features:
            return

        self.batch_features_loaded.emit({
            "type": "FeatureCollection",
            "features": batch_features
        })

    def build_payload_and_headers(self, tile):
        payload = copy.deepcopy(self.base_data_pass)
        payload["geom"]["features"][0]["geometry"]["coordinates"] = [tile["coords"]]
        payload["categories"][0]["id"] = self.item_category

        headers = self.headers.copy()
        headers["content-length"] = str(len(json.dumps(payload, ensure_ascii=False)))
        return payload, headers

    def request_tile(self, tile, worker_id):
        """Worker-функция. Не использует QGIS API."""
        tile_key = str(tile["tile_key"])
        payload, headers = self.build_payload_and_headers(tile)
        started_at = time.perf_counter()
        attempts_used = 0

        def make_result(status, features=None, returned_count=0, error=None):
            return {
                "tile_key": tile_key,
                "status": status,
                "features": features or [],
                "returned_count": returned_count,
                "error": error,
                "worker_id": worker_id,
                "attempts": attempts_used,
                "response_time": round(time.perf_counter() - started_at, 3),
                "updated": time.strftime("%Y-%m-%d %H:%M:%S")
            }

        if self._cancel_requested:
            return make_result("cancelled", error="cancelled before request")

        # Небольшой джиттер перед запросом, чтобы workers не били в сервер строго одновременно.
        time.sleep(random.uniform(NSPD_DELAY_MIN, NSPD_DELAY_MAX))

        if self._cancel_requested:
            return make_result("cancelled", error="cancelled before request")

        last_error = None

        for attempt in range(1, NSPD_RETRY_COUNT + 1):
            attempts_used = attempt
            if self._cancel_requested:
                return make_result("cancelled", error="cancelled during retry loop")
            try:
                response = requests.post(
                    nspd_url,
                    headers=headers,
                    verify=False,
                    json=payload,
                    timeout=20
                )

                if response.status_code in [429, 500, 502, 503, 504]:
                    last_error = "HTTP {}".format(response.status_code)
                    if attempt < NSPD_RETRY_COUNT and not self._cancel_requested:
                        time.sleep(random.uniform(NSPD_RETRY_DELAY_MIN, NSPD_RETRY_DELAY_MAX))
                    continue

                if response.status_code != 200:
                    last_error = "HTTP {}".format(response.status_code)
                    if attempt < NSPD_RETRY_COUNT and not self._cancel_requested:
                        time.sleep(random.uniform(NSPD_RETRY_DELAY_MIN, NSPD_RETRY_DELAY_MAX))
                    continue

                data = response.json()
                features = data.get("features", [])

                if features:
                    return make_result("success", features=features, returned_count=len(features))

                return make_result("empty", returned_count=0)

            except Exception as e:
                last_error = str(e)
                if attempt < NSPD_RETRY_COUNT and not self._cancel_requested:
                    time.sleep(random.uniform(NSPD_RETRY_DELAY_MIN, NSPD_RETRY_DELAY_MAX))

        return make_result("error", error=last_error)

    def run(self):
        seen_ids = set()
        batch_features = []
        tiles_since_last_batch = 0

        if self.total_tiles == 0:
            self.data_nspd_loaded.emit({"type": "FeatureCollection", "features": []})
            return

        max_workers = max(1, int(NSPD_WORKERS))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_tile = {}

            def submit_next(worker_id):
                tile = self.pop_next_tile()
                if not tile:
                    return False

                tile_key = str(tile["tile_key"])
                self.tile_status_updated.emit(
                    tile_key,
                    "processing",
                    0,
                    int(worker_id),
                    0,
                    0.0,
                    time.strftime("%Y-%m-%d %H:%M:%S")
                )
                future = executor.submit(self.request_tile, tile, worker_id)
                future_to_tile[future] = (tile, worker_id)
                return True

            # Первичное заполнение worker-слотов.
            for worker_id in range(1, max_workers + 1):
                if not submit_next(worker_id):
                    break

            while future_to_tile:
                for future in as_completed(list(future_to_tile.keys())):
                    tile, worker_id = future_to_tile.pop(future)
                    tile_key = str(tile["tile_key"])

                    try:
                        result = future.result()
                    except Exception:
                        result = {
                            "tile_key": tile_key,
                            "status": "error",
                            "features": [],
                            "returned_count": 0,
                            "error": "future failed",
                            "worker_id": worker_id,
                            "attempts": 0,
                            "response_time": 0.0,
                            "updated": time.strftime("%Y-%m-%d %H:%M:%S")
                        }

                    status = result.get("status", "error")
                    features = result.get("features", []) or []
                    result_worker_id = int(result.get("worker_id", worker_id) or 0)
                    result_attempts = int(result.get("attempts", 0) or 0)
                    result_response_time = float(result.get("response_time", 0.0) or 0.0)
                    result_updated = result.get("updated") or time.strftime("%Y-%m-%d %H:%M:%S")
                    added_count = 0

                    if status == "success":
                        for f in features:
                            fid = f.get("id")
                            if fid is None:
                                fid = json.dumps(f.get("geometry", {}), ensure_ascii=False)

                            if fid in seen_ids:
                                continue

                            seen_ids.add(fid)
                            batch_features.append(f)
                            added_count += 1

                            if len(batch_features) >= NSPD_BATCH_FEATURES_LIMIT:
                                self.emit_batch(batch_features)
                                batch_features = []

                        self.tile_status_updated.emit(tile_key, "success", added_count, result_worker_id, result_attempts, result_response_time, result_updated)

                    elif status == "empty":
                        self.tile_status_updated.emit(tile_key, "empty", 0, result_worker_id, result_attempts, result_response_time, result_updated)

                    elif status == "cancelled":
                        # Не красим тайл в ошибку: он останется queued/pending и попадёт в следующий запуск.
                        self.tile_status_updated.emit(tile_key, "queued", 0, 0, result_attempts, result_response_time, result_updated)

                    else:
                        self.tile_status_updated.emit(tile_key, "error", 0, result_worker_id, result_attempts, result_response_time, result_updated)

                    self.completed_tiles += 1
                    tiles_since_last_batch += 1

                    if tiles_since_last_batch >= NSPD_BATCH_TILES_LIMIT:
                        self.emit_batch(batch_features)
                        batch_features = []
                        tiles_since_last_batch = 0

                    total = max(1, self.total_tiles)
                    self.progress_updated.emit(int((self.completed_tiles / total) * 100))

                    # После завершения одного запроса пробуем занять освободившийся worker-слот.
                    if not self._cancel_requested:
                        submit_next(worker_id)

                    break

        self.emit_batch(batch_features)
        self.data_nspd_loaded.emit({"type": "FeatureCollection", "features": []})

class DrawExtent(QgsMapToolEmitPoint):
    """  """
    def __init__(self, iface, app, item_name, item_num, item_category):
        # init
        self.main_app = app
        self.canvas = iface.mapCanvas()
        self.isPressed = False
        self.item_name = item_name
        self.item_num = item_num
        self.item_category = item_category
        self.dd = 1500 # будете делать число больше - забанят
        self.nspd_geom_thread = None
        self.tile_debug_layer = None
        self.is_working = False
        
        QgsMapToolIdentify.__init__(self, self.canvas)
        
        # настройка отрисовки графики
        self.rubberBand = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.rubberBand.setColor(QColor(150,150,200,150))
        self.rubberBand.setWidth(3)
        self.rubberBand.reset()
       
    
    def canvasPressEvent(self, e):
        # Даже во время активного сбора разрешаем выделять новый охват.
        # Новые тайлы будут добавлены в живую очередь, а не запустят второй поток.
        self.isPressed = True
        self.start_point = self.toMapCoordinates(e.pos())
        self.end_point = self.start_point
        self.check_shape = QgsGeometry.fromPolygonXY([[
            QgsPointXY(self.start_point.x()-self.dd, self.start_point.y()+self.dd),
            QgsPointXY(self.start_point.x()+self.dd, self.start_point.y()+self.dd),
            QgsPointXY(self.start_point.x()+self.dd, self.start_point.y()-self.dd),
            QgsPointXY(self.start_point.x()-self.dd, self.start_point.y()-self.dd),
            QgsPointXY(self.start_point.x()-self.dd, self.start_point.y()+self.dd),
        ]])
        
    
    def canvasMoveEvent(self, e):
        if self.isPressed:
            self.end_point = self.toMapCoordinates(e.pos())
            self.showRect(self.start_point, self.end_point)
        
    
    def showPoint(self, end_point):
        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
        geom_polygon = QgsGeometry().fromPointXY(end_point)
        self.rubberBand.setToGeometry(geom_polygon)

    
    def showRect(self, startPoint, endPoint):
        # draw rectangle 
        if startPoint.x() == endPoint.x() or startPoint.y() == endPoint.y():
            return
        pnts = [
            (startPoint.x(), startPoint.y()),
            (startPoint.x(), endPoint.y()),
            (endPoint.x(), endPoint.y()),
            (endPoint.x(), startPoint.y()),
            (startPoint.x(), startPoint.y())
        ]

        polygon_coors = [QgsPointXY(p[0], p[1]) for p in pnts]
        geom_polygon = QgsGeometry().fromPolygonXY([polygon_coors])
        # Старое ограничение dd=1500 отключено: большой охват будет разбит на допустимые тайлы.
        # geom_polygon = geom_polygon.intersection(self.check_shape)

        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
        self.rubberBand.setToGeometry(geom_polygon)
    
    
    def canvasReleaseEvent(self, e):
        self.isPressed = False
        self.get_data(self.toMapCoordinates(e.pos()))
        
    
    def deactivate(self):
        self.rubberBand.reset()
        QGuiApplication.restoreOverrideCursor()
        QgsMapTool.deactivate(self)
        self.deactivated.emit()

    
    def get_symbol(self, layer):
        symbol = None 
        if layer.geometryType() == QgsWkbTypes.LineGeometry:
            symbol = QgsLineSymbol.createSimple({'color':'blue', 'width':'1.5'})
        elif layer.geometryType() == QgsWkbTypes.PointGeometry:
            symbol = QgsMarkerSymbol.createSimple({'color': 'blue'})  
        else:
            symbol = QgsFillSymbol.createSimple({'color':"#3e51ff81", 'outline_width': '0.26', 'outline_color': '#707070'})
        return symbol

    


    def get_completed_tile_keys(self):
        """Возвращает tile_key уже полностью обработанных тайлов для текущего слоя НСПД.
        success и empty считаются завершёнными; error/retry/pending будут перезапрашиваться.
        """
        layer_name = "НСПД_процесс_тайлы_{}".format(safe_layer_name(self.item_name))
        existing = QgsProject.instance().mapLayersByName(layer_name)
        if not existing:
            return set()

        layer = existing[0]
        if not layer or not layer.isValid():
            return set()

        field_names = layer.fields().names()
        if "tile_key" not in field_names or "status" not in field_names:
            return set()

        completed = set()
        for feat in layer.getFeatures():
            status = str(feat["status"])
            tile_key = feat["tile_key"]
            if tile_key in [None, NULL, ""]:
                continue
            if status in ["success", "empty"]:
                completed.add(str(tile_key))

        return completed

    def apply_tile_debug_style(self, layer):
        """Единый стиль слоя тайлов: статус цветом, очередь/поток/результат подписью."""
        style_map = {
            "queued": ("В очереди", "#BDBDBD"),
            "pending": ("Ожидает", "#D0D0D0"),
            "processing": ("Обрабатывается", "#FFB300"),
            "retry": ("Повтор запроса", "#FB8C00"),
            "success": ("Успешно", "#2E7D32"),
            "empty": ("Пусто", "#90CAF9"),
            "error": ("Ошибка", "#C62828")
        }
        opacity_map = {
            "queued": 0.12,
            "pending": 0.12,
            "processing": 0.45,
            "retry": 0.55,
            "success": 0.18,
            "empty": 0.06,
            "error": 0.65
        }

        categories = []
        for status, (label, color) in style_map.items():
            symbol = QgsFillSymbol.createSimple({
                "color": color,
                "outline_color": "#333333",
                "outline_width": "0.25"
            })
            symbol.setOpacity(opacity_map.get(status, 0.25))
            categories.append(QgsRendererCategory(status, symbol, label))

        layer.setRenderer(QgsCategorizedSymbolRenderer("status", categories))

        label_settings = QgsPalLayerSettings()
        label_settings.fieldName = 'CASE\nWHEN "status" = \'queued\' THEN \'Q\' || to_string("queue_order")\nWHEN "status" = \'processing\' THEN \'P\' || to_string("worker_id")\nWHEN "status" = \'success\' THEN to_string("count")\nWHEN "status" = \'retry\' THEN \'R\' || to_string("attempts")\nWHEN "status" = \'error\' THEN \'ERR\'\nELSE \'\'\nEND'
        label_settings.isExpression = True
        label_settings.enabled = True
        layer.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
        layer.setLabelsEnabled(True)
        layer.triggerRepaint()

    def create_tile_debug_layer(self, tiles):
        """
        Создаёт или переиспользует слой-индикатор процесса для конкретного слоя НСПД.
        Пример: НСПД_процесс_тайлы_Здания.
        Повторные допарсинги по тому же типу объектов дополняют этот же слой.
        """
        layer_name = "НСПД_процесс_тайлы_{}".format(safe_layer_name(self.item_name))
        existing = QgsProject.instance().mapLayersByName(layer_name)

        required_fields = {
            "tile_id": QVariant.Int,
            "tile_key": QVariant.String,
            "status": QVariant.String,
            "count": QVariant.Int,
            "layer_name": QVariant.String,
            "queue_order": QVariant.Int,
            "worker_id": QVariant.Int,
            "attempts": QVariant.Int,
            "response_time": QVariant.Double,
            "updated": QVariant.String
        }

        if existing:
            layer = existing[0]
            provider = layer.dataProvider()

            existing_field_names = layer.fields().names()
            fields_to_add = []
            for field_name, field_type in required_fields.items():
                if field_name not in existing_field_names:
                    fields_to_add.append(QgsField(field_name, field_type))

            if fields_to_add:
                provider.addAttributes(fields_to_add)
                layer.updateFields()
        else:
            layer = QgsVectorLayer("Polygon?crs=EPSG:3857", layer_name, "memory")
            provider = layer.dataProvider()
            provider.addAttributes([
                QgsField("tile_id", QVariant.Int),
                QgsField("tile_key", QVariant.String),
                QgsField("status", QVariant.String),
                QgsField("count", QVariant.Int),
                QgsField("layer_name", QVariant.String),
                QgsField("queue_order", QVariant.Int),
                QgsField("worker_id", QVariant.Int),
                QgsField("attempts", QVariant.Int),
                QgsField("response_time", QVariant.Double),
                QgsField("updated", QVariant.String)
            ])
            layer.updateFields()

            style_map = {
                "queued": ("В очереди", "#BDBDBD"),
                "pending": ("Ожидает", "#D0D0D0"),
                "processing": ("Обрабатывается", "#FFB300"),
                "retry": ("Повтор запроса", "#FB8C00"),
                "success": ("Успешно", "#2E7D32"),
                "empty": ("Пусто", "#90CAF9"),
                "error": ("Ошибка", "#C62828")
            }

            categories = []
            for status, (label, color) in style_map.items():
                symbol = QgsFillSymbol.createSimple({
                    "color": color,
                    "outline_color": "#333333",
                    "outline_width": "0.25"
                })
                categories.append(QgsRendererCategory(status, symbol, label))

            layer.setRenderer(QgsCategorizedSymbolRenderer("status", categories))
            QgsProject.instance().addMapLayer(layer)

        self.apply_tile_debug_style(layer)

        provider = layer.dataProvider()

        existing_keys = set()
        if "tile_key" in layer.fields().names():
            for feat in layer.getFeatures():
                val = feat["tile_key"]
                if val not in [None, NULL, ""]:
                    existing_keys.add(str(val))

        new_features = []
        for tile in tiles:
            tile_key = str(tile["tile_key"])

            if tile_key in existing_keys:
                continue

            points = [QgsPointXY(x, y) for x, y in tile["coords"]]
            feat = QgsFeature(layer.fields())
            feat.setGeometry(QgsGeometry.fromPolygonXY([points]))
            feat["tile_id"] = int(tile["tile_id"])
            feat["tile_key"] = tile_key
            feat["status"] = "queued"
            feat["count"] = 0
            feat["layer_name"] = self.item_name
            feat["queue_order"] = int(tile.get("queue_order", 0) or 0)
            feat["worker_id"] = 0
            feat["attempts"] = 0
            feat["response_time"] = 0.0
            feat["updated"] = ""
            new_features.append(feat)

        if new_features:
            provider.addFeatures(new_features)
            layer.updateExtents()

        self.tile_debug_layer = layer
        layer.triggerRepaint()
        return layer


    def update_tile_status(self, tile_key, status, count, worker_id=0, attempts=0, response_time=0.0, updated=""):
        """Обновляет статус конкретного тайла в слое-индикаторе."""
        if not self.tile_debug_layer or not self.tile_debug_layer.isValid():
            return

        layer = self.tile_debug_layer
        field_names = layer.fields().names()
        idx = {name: layer.fields().indexFromName(name) for name in field_names}

        if idx.get("status", -1) == -1 or idx.get("count", -1) == -1:
            return

        changes = {}
        for feat in layer.getFeatures():
            if str(feat["tile_key"]) == str(tile_key):
                attr_changes = {
                    idx["status"]: status,
                    idx["count"]: int(count)
                }

                if idx.get("worker_id", -1) != -1:
                    attr_changes[idx["worker_id"]] = int(worker_id or 0)
                if idx.get("attempts", -1) != -1:
                    attr_changes[idx["attempts"]] = int(attempts or 0)
                if idx.get("response_time", -1) != -1:
                    attr_changes[idx["response_time"]] = float(response_time or 0.0)
                if idx.get("updated", -1) != -1:
                    attr_changes[idx["updated"]] = updated or time.strftime("%Y-%m-%d %H:%M:%S")

                changes[feat.id()] = attr_changes
                break

        if changes:
            layer.dataProvider().changeAttributeValues(changes)
            layer.triggerRepaint()

    def get_data(self, geom):
        crs_default = QgsProject.instance().crs()
        crs_transform = QgsCoordinateTransform(crs_default, crs_mercator, QgsProject.instance())

        bbox_geom = self.rubberBand.asGeometry()
        bbox_geom.transform(crs_transform)
        bbox = bbox_geom.boundingBox()
        left_x = bbox.xMinimum()
        bottom_y = bbox.yMinimum()
        right_x = bbox.xMaximum()
        top_y = bbox.yMaximum()

        tiles = make_tile_items_from_bbox(
            left_x,
            bottom_y,
            right_x,
            top_y,
            NSPD_TILE_SIZE
        )

        # Лимит тайлов снят: большой охват будет обработан полностью по сетке тайлов.
        # Но уже завершённые тайлы (success/empty) не запрашиваем повторно.
        completed_tile_keys = self.get_completed_tile_keys()
        if completed_tile_keys:
            tiles = [t for t in tiles if str(t.get("tile_key")) not in completed_tile_keys]

        if not tiles:
            self.main_app.warning_message(
                "В выбранном охвате нет новых тайлов для сбора.<br>"
                "Все тайлы уже имеют статус success или empty."
            )
            self.is_working = False
            return

        # Если сбор уже идёт, не запускаем второй поток, а докидываем тайлы в живую очередь.
        if self.nspd_geom_thread and self.nspd_geom_thread.isRunning():
            added = self.nspd_geom_thread.add_tiles(tiles)
            # add_tiles проставляет queue_order прямо в tile, поэтому слой сразу получает номера очереди.
            self.create_tile_debug_layer(tiles)
            self.is_working = True
            self.main_app.pbar.setDisabled(False)
            self.main_app.pbar.setFormat("В очереди добавлено: {} тайлов".format(added))
            if hasattr(self.main_app, "btn_cancel_object"):
                self.main_app.btn_cancel_object.setDisabled(False)
            return

        self.nspd_geom_thread = NSPDGeomExtractTiled(
            nspd_headers,
            data_pass,
            tiles,
            self.item_category
        )

        # После создания потока начальные тайлы уже получили queue_order.
        self.create_tile_debug_layer(tiles)

        self.nspd_geom_thread.progress_updated.connect(self.main_app.prbar_upd)
        self.nspd_geom_thread.tile_status_updated.connect(self.update_tile_status)
        self.nspd_geom_thread.batch_features_loaded.connect(self.geom_batch_loaded)
        self.nspd_geom_thread.data_nspd_loaded.connect(self.geom_loaded)

        self.main_app.pbar.setDisabled(False)
        self.main_app.pbar.setValue(0)
        self.main_app.pbar.setFormat("Скачивание: %p%")
        if hasattr(self.main_app, "btn_cancel_object"):
            self.main_app.btn_cancel_object.setDisabled(False)

        self.nspd_geom_thread.start()
        self.is_working = True
    
    
    def geom_batch_loaded(self, response):
        """Принимает очередной пакет объектов из рабочего потока и сразу добавляет его в слой QGIS."""
        self.append_nspd_response(response)


    def geom_loaded(self, response):
        """Финализация после завершения всех тайлов. Основные данные уже сброшены пакетами."""
        if response and response.get('features'):
            self.append_nspd_response(response)

        self.nspd_geom_thread.quit()
        self.nspd_geom_thread.wait()
        self.is_working = False
        if hasattr(self.main_app, "btn_cancel_object"):
            self.main_app.btn_cancel_object.setDisabled(True)
        self.main_app.pbar.setValue(0)
        self.main_app.pbar.setFormat("%p%")
        self.main_app.pbar.setDisabled(True)


    def append_nspd_response(self, response):
        """Добавляет пакет объектов НСПД в существующие слои QGIS без ожидания конца всего сбора."""
        geometry_types = {}
        dict_num_geom = {
            "polygons" : 0,
            "polylines" : 0,
            "points" : 0
        }
        fids = {}
        sample_geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        field_types = {}
        for f in response.get('features', []):
            if not fids.get(f['id'], 0):
                f["properties"]['id'] = f['id']
                f["properties"].update(f["properties"]["options"])
                f["properties"].update(f["properties"]["systemInfo"])
                for prop in f["properties"]:
                    if str(f["properties"][prop]).strip() == '':
                        f["properties"][prop] = None
                    if type(f["properties"][prop]) == str and len(f["properties"][prop])>2000:
                        f["properties"][prop] = f["properties"][prop][:2000]
                    prop_type = type(f["properties"][prop]).__name__
                    prop_type = 'text' if prop_type in ['str', 'NoneType'] else prop_type
                    field_types[prop]=prop_type


                del f["properties"]["options"]
                del f["properties"]["systemInfo"]
                g_type = f['geometry']['type'].lower()
                if g_type in geometry_types:
                    geometry_types[g_type]+=1
                else:
                    geometry_types[g_type] = 1
                if self.item_name in nspd_zouit_categories:
                    zouit_types = nspd_zouit_categories.get(self.item_name, [])
                    category = f["properties"].get('subcategory', False)
                    if category in zouit_types:
                        sample_geojson['features'].append(f)
                else:
                    sample_geojson['features'].append(f)
                fids[f['id']] = 1
        categories = []
        for i, feature in enumerate(sample_geojson['features']):
            props = feature['properties']
            category = props.get('category', None)
            if category and category not in categories:
                categories.append(category)

            geom = feature['geometry']
            if not geom:
                continue
            geom_type = geom['type']
            if geom_type.lower() in ['polygon', 'multipolygon']:
                dict_num_geom['polygons']+=1
            if geom_type.lower() in ['linestring', 'multilinestring']:
                dict_num_geom['polylines']+=1
            if geom_type.lower() in ['point', 'multipoint']:
                dict_num_geom['points']+=1
        
        if not sample_geojson["features"]:
            return

        project_layers = [l for l in QgsProject.instance().mapLayers().values() if type(l) == QgsVectorLayer and l.isValid()]
        for geom_item, item_nums in dict_num_geom.items():
            if item_nums:
                nspd_layer_name = "НСПД_{}_{}".format(self.item_name, geom_item)
                layer_nspd_vector = QgsVectorLayer(json.dumps(sample_geojson), nspd_layer_name, 'ogr')
                layer_nspd_vector = layer_nspd_vector.materialize(QgsFeatureRequest())
                layer_nspd_vector.setCrs(crs_mercator)

                if nspd_layer_name in [l.metadata().abstract() for l in project_layers]:
                    ex_layer = QgsProject.instance().mapLayersByName(nspd_layer_name)
                    if ex_layer:
                        ex_layer = ex_layer[0]
                        ex_ids = {}
                        ex_geom_hashes = set()
                        for ex_feat in ex_layer.getFeatures():
                            ex_ids[ex_feat.__geo_interface__.get('properties', {}).get('id', None)] = 1
                            h = geom_bbox_hash_qgs(ex_feat.geometry())
                            if h:
                                ex_geom_hashes.add(h)
                        ex_layer_fields_types = {f.name(): f.typeName() for f in ex_layer.fields()}
                        new_layer_fields_types = {f.name(): f.typeName() for f in layer_nspd_vector.fields()}
                        ex_missing = [f for f in list(new_layer_fields_types.keys()) if f not in list(ex_layer_fields_types.keys())]
                        if ex_missing:
                            ex_sample_geojson = {
                                "type": "FeatureCollection",
                                "features": []
                            }
                            ex_ids = {}
                            ex_geom_hashes = set()
                            exporter = QgsJsonExporter(ex_layer)
                            exporter.setSourceCrs(ex_layer.crs())
                            exporter.setDestinationCrs(ex_layer.crs())

                            for frow in ex_layer.getFeatures():
                                f_json = json.loads(exporter.exportFeature(frow))
                                del f_json['bbox']
                                del f_json['id']
                                ex_ids[f_json.get('properties', {}).get('id', None)] = 1
                                h = geom_bbox_hash_qgs(frow.geometry())
                                if h:
                                    ex_geom_hashes.add(h)
                                ex_sample_geojson['features'].append(f_json)

                            tmp_new_layer = QgsVectorLayer(json.dumps(sample_geojson), nspd_layer_name + "_tmp", 'ogr')
                            tmp_new_layer = tmp_new_layer.materialize(QgsFeatureRequest())
                            tmp_new_layer.setCrs(crs_mercator)
                            new_hash_by_id = {}
                            for tmp_feat in tmp_new_layer.getFeatures():
                                new_hash_by_id[tmp_feat['id']] = geom_bbox_hash_qgs(tmp_feat.geometry())

                            for new_feature in sample_geojson["features"]:
                                new_id = new_feature.get("properties", {}).get("id", None)
                                if ex_ids.get(new_id, None):
                                    continue
                                new_hash = new_hash_by_id.get(new_id)
                                if new_hash and new_hash in ex_geom_hashes:
                                    continue
                                if new_hash:
                                    ex_geom_hashes.add(new_hash)
                                ex_sample_geojson["features"].append(new_feature)

                            new_ds = json.dumps(ex_sample_geojson)
                            
                            QgsProject.instance().removeMapLayer(ex_layer)

                            layer_nspd_vector = QgsVectorLayer(new_ds, nspd_layer_name, 'ogr')
                            layer_nspd_vector = layer_nspd_vector.materialize(QgsFeatureRequest())
                            layer_nspd_vector.setCrs(crs_mercator)
                            self.add_nspd_layer(layer_nspd_vector, nspd_layer_name)

                        else:
                            new_features = []
                            for f in layer_nspd_vector.getFeatures():
                                if f['id'] in ex_ids:
                                    continue
                                new_hash = geom_bbox_hash_qgs(f.geometry())
                                if new_hash and new_hash in ex_geom_hashes:
                                    continue
                                if new_hash:
                                    ex_geom_hashes.add(new_hash)
                                new_f = QgsFeature(ex_layer.fields())
                                for fld in ex_layer.fields().names():
                                    if fld not in new_layer_fields_types:
                                        continue
                                    new_f[fld] = f[fld]
                                new_f.setGeometry(f.geometry())
                                new_features.append(new_f)
                            ex_layer.dataProvider().addFeatures(new_features)
                            ex_layer.triggerRepaint()
                    else:
                        self.add_nspd_layer(layer_nspd_vector, nspd_layer_name)
                else:
                    self.add_nspd_layer(layer_nspd_vector, nspd_layer_name)
                    

    def add_nspd_layer(self, nspd_layer, layer_name):
        layer_meta = nspd_layer.metadata()
        layer_meta.setAbstract(layer_name)
        nspd_layer.setMetadata(layer_meta)
        symbol = self.get_symbol(nspd_layer)
        nspd_layer.renderer().setSymbol(symbol)
        QgsProject.instance().addMapLayer(nspd_layer)
     

class DrawRasterExtent(QgsMapToolEmitPoint):
    """Выбор охвата для выгрузки XYZ/WMTS-растра."""

    def __init__(self, iface, app, layer_id, layer_name):
        self.main_app = app
        self.canvas = iface.mapCanvas()
        self.layer_id = int(layer_id)
        self.layer_name = str(layer_name)
        self.isPressed = False
        self.start_point = None
        self.end_point = None

        QgsMapToolIdentify.__init__(self, self.canvas)

        self.rubberBand = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.rubberBand.setColor(QColor(0, 170, 255, 90))
        self.rubberBand.setWidth(3)
        self.rubberBand.reset()

    def canvasPressEvent(self, e):
        self.isPressed = True
        self.start_point = self.toMapCoordinates(e.pos())
        self.end_point = self.start_point

    def canvasMoveEvent(self, e):
        if self.isPressed:
            self.end_point = self.toMapCoordinates(e.pos())
            self.showRect(self.start_point, self.end_point)

    def showRect(self, startPoint, endPoint):
        if not startPoint or not endPoint:
            return
        if startPoint.x() == endPoint.x() or startPoint.y() == endPoint.y():
            return
        pnts = [
            (startPoint.x(), startPoint.y()),
            (startPoint.x(), endPoint.y()),
            (endPoint.x(), endPoint.y()),
            (endPoint.x(), startPoint.y()),
            (startPoint.x(), startPoint.y())
        ]
        polygon_coors = [QgsPointXY(p[0], p[1]) for p in pnts]
        geom_polygon = QgsGeometry().fromPolygonXY([polygon_coors])
        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
        self.rubberBand.setToGeometry(geom_polygon)

    def canvasReleaseEvent(self, e):
        self.isPressed = False
        self.end_point = self.toMapCoordinates(e.pos())
        self.showRect(self.start_point, self.end_point)
        geom = self.rubberBand.asGeometry()
        if geom and not geom.isEmpty():
            self.main_app.start_raster_export_from_geometry(geom)

    def deactivate(self):
        self.rubberBand.reset()
        QGuiApplication.restoreOverrideCursor()
        QgsMapTool.deactivate(self)
        self.deactivated.emit()


class NSPD_DockWidget(QDockWidget):
    # dockwidget
    def __init__(self, wrapper, data, layers_meta):
        QDockWidget.__init__(self)
        self.setWindowTitle("Подложки НСПД")
        self.gv = NSPD_Navigator(self, data, layers_meta)
        self.setWidget(self.gv)
        self.dropHandler = MyDropHandler()
        iface.registerCustomDropHandler(self.dropHandler)
        (script_name:=globals().get("script_name")) and hasattr(iface,"kolba_plugin") and iface.kolba_plugin.__setitem__(script_name, self)
    

    def closeEvent(self, e):
        if self.gv.raster_export_thread and self.gv.raster_export_thread.isRunning():
            self.gv.raster_export_thread.cancel()
            self.gv.raster_export_thread.wait(3000)

        if self.gv.raster_draw_tool:
            iface.mapCanvas().unsetMapTool(self.gv.raster_draw_tool)
            self.gv.raster_draw_tool.rubberBand.reset()
            self.gv.raster_draw_tool = None

        if self.gv.draw_tool:
            iface.mapCanvas().unsetMapTool(self.gv.draw_tool)
            self.gv.draw_tool.rubberBand.reset()
            self.gv.draw_tool = None
            
        (script_name:=globals().get("script_name")) and hasattr(iface,"kolba_plugin") and iface.kolba_plugin.__setitem__(script_name, None)
        iface.removeDockWidget(self)
        iface.unregisterCustomDropHandler(self.dropHandler)
        return


class NSPD_Navigator(QMainWindow):
    # main interface
    def __init__(self, parent, data, layers_meta):
        QMainWindow.__init__(self, parent=iface.mainWindow())
        self.setWindowTitle('NSPD Navigator')
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

        self.draw_tool = None 
        self.raster_draw_tool = None
        self.raster_export_thread = None
        self.selected_item_num = None
        self.selected_item_name = ''
        self.selected_item_category = None
        self.selected_item_type = None

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.lt = QVBoxLayout()
        self.central_widget.setLayout(self.lt)

        self.tree = DraggableTree()
        self.tree.header().setVisible(False)
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(False)
        self.tree.setDropIndicatorShown(False)
        self.tree.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)

        
        
        for row in data['tree']['folders']:
            if type(row) == dict:
                row = [row]
            for folder_row in row:
                fill_items(self.tree, folder_row, layers_meta)

        self.label_active_layer = QLabel("Выбранный слой: ")
        self.label_active_layer.setWordWrap(True)
        self.label_active_layer.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label_active_layer.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)

        self.label_progress_status = QLabel("Статус: ожидание")
        self.label_progress_status.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.label_progress_status.setVisible(False)

        self.search_line = QLineEdit()
        self.search_line.setPlaceholderText("Поиск...")

        self.btn_get_object = QPushButton()
        self.btn_get_object.setToolTip("Скачать объекты по охвату")
        self.btn_get_object.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.btn_get_object.setIcon(QIcon(":images/themes/default/algorithms/mAlgorithmExtractLayerExtent.svg")) 
        self.btn_get_object.setDisabled(True)

        self.btn_cancel_object = QPushButton()
        self.btn_cancel_object.setToolTip("Остановить сбор объектов")
        self.btn_cancel_object.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.btn_cancel_object.setIcon(QIcon(":images/themes/default/mActionCancel.svg"))
        self.btn_cancel_object.setText("×")
        self.btn_cancel_object.setDisabled(True)

        self.btn_search = QPushButton()
        self.btn_search.setToolTip("Поиск по номерам")
        self.btn_search.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.btn_search.setIcon(QIcon(":images/themes/default/console/iconSearchEditorConsole.svg")) 

        self.layout_header = QHBoxLayout()
        self.layout_header.addWidget(self.label_active_layer)
        self.layout_header.addWidget(self.btn_get_object)
        self.layout_header.addWidget(self.btn_cancel_object)

        self.layout_search = QHBoxLayout()
        self.layout_search.addWidget(self.search_line)
        self.layout_search.addWidget(self.btn_search)

        self.add_to_project = QPushButton('Добавить в проект')
        
        self.pbar = QProgressBar()
        self.pbar.setDisabled(True)
        
        self.lt.addLayout(self.layout_search)
        self.lt.addLayout(self.layout_header)
        self.lt.addWidget(self.label_progress_status)
        self.lt.addWidget(self.pbar)
        self.lt.addWidget(self.tree)
        self.lt.setStretchFactor(self.tree, 1)
        
        self.btn_get_object.clicked.connect(self.get_object)
        self.btn_cancel_object.clicked.connect(self.cancel_object_loading)
        self.tree.clicked.connect(self.onItemClickedSingle)
        self.tree.doubleClicked.connect(self.onItemClicked)
        self.add_to_project.clicked.connect(self.add_layer)
        self.search_line.returnPressed.connect(self.find_cad_num)
        self.btn_search.clicked.connect(self.find_cad_num)

        try:
            iface.mapCanvas().scaleChanged.connect(self.update_active_layer_label)
        except Exception:
            pass
        try:
            iface.mapCanvas().extentsChanged.connect(self.update_active_layer_label)
        except Exception:
            pass
        self.update_active_layer_label()
    

    def cancel_object_loading(self):
        if self.raster_export_thread and self.raster_export_thread.isRunning():
            self.raster_export_thread.cancel()
            self.btn_cancel_object.setDisabled(True)
            self.pbar.setFormat("Остановка выгрузки растра...")
            return

        if self.draw_tool and self.draw_tool.nspd_geom_thread:
            self.draw_tool.nspd_geom_thread.cancel()
            self.draw_tool.is_working = False
            self.btn_cancel_object.setDisabled(True)
            self.pbar.setFormat("Остановка после текущих запросов...")


    def find_cad_num(self):
        value = self.search_line.text().replace('\n', '').strip()
        check_word = self.is_valid_string(value)

        if not value:
            self.warning_message('Введите кадастровые номера')
            return 

        if not check_word:
            self.warning_message('В перечне кадастровых номеров могут быть только числа и знаки , :')
            return 
        
        splitted_value = [w.strip() for w in value.split(',')]

        if len(splitted_value)>50:
            self.warning_message('Максимальное количество кадастровых номеров для поиска - 50.')
            return 

        self.find_cad_thread = NSPDCadFinder(splitted_value)
        self.find_cad_thread.data_nspd_loaded.connect(self.data_found)
        self.find_cad_thread.progress_updated.connect(self.prbar_upd)
        self.pbar.setDisabled(False)
        self.find_cad_thread.start()
    

    def prbar_upd(self, pbar_value):
        self.pbar.setValue(int(pbar_value))
        
    
    def data_found(self, data):
        self.find_cad_thread.quit()
        self.find_cad_thread.wait()
        self.pbar.setValue(0)
        self.pbar.setFormat("%p%")
        self.pbar.setDisabled(True)
        value = self.search_line.text().replace('\n', '').strip()[:100]
        layer = QgsVectorLayer(json.dumps(data), 'Результат_поиска_{}'.format(value), 'ogr')
        if layer.geometryType() == QgsWkbTypes.LineGeometry:
            symbol = QgsLineSymbol.createSimple({'color':'blue', 'width':'1.5'})
        elif layer.geometryType() == QgsWkbTypes.PointGeometry:
            symbol = QgsMarkerSymbol.createSimple({'color': 'blue'}) 
        else:
            symbol = QgsFillSymbol.createSimple({'color':"#3e51ff81", 'outline_width': '0.26', 'outline_color': '#707070'})
        layer.renderer().setSymbol(symbol)
        layer.setCrs(crs_mercator)
        QgsProject.instance().addMapLayer(layer)
        
    
    def is_valid_string(self, input_string):
        pattern = r'^[0-9 :,-]+$'
        return bool(re.fullmatch(pattern, input_string))


    def warning_message(self, err_text):
        msg = QMessageBox()
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setWindowTitle("Уведомление")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setText(err_text)
        msg.exec()
        return


    def get_scale_zoom_text(self):
        scale = current_canvas_scale()
        z = get_canvas_xyz_zoom()
        if scale > 0:
            return "1:{:,.0f}, z≈{}".format(scale, z).replace(',', ' ')
        return "z≈{}".format(z)


    def update_active_layer_label(self, *args):
        if self.selected_item_name:
            self.label_active_layer.setText(
                "Выбранный слой: {}\nМасштаб: {}".format(self.selected_item_name, self.get_scale_zoom_text())
            )
        else:
            self.label_active_layer.setText("Выбранный слой:\nМасштаб: {}".format(self.get_scale_zoom_text()))


    def configure_download_button(self):
        is_leaf = self.selected_item_num is not None
        if not is_leaf:
            self.btn_get_object.setDisabled(True)
            self.btn_get_object.setToolTip("Сначала выберите слой")
            return

        if self.selected_item_type == 'wmts':
            self.btn_get_object.setDisabled(False)
            self.btn_get_object.setToolTip("Выбрать охват и выгрузить растр")
            return

        self.btn_get_object.setDisabled(self.selected_item_category is None)
        self.btn_get_object.setToolTip("Скачать объекты по охвату")


    def export_selected_raster(self):
        if self.selected_item_type != 'wmts' or self.selected_item_num is None:
            self.warning_message("Выгрузка растра сейчас доступна только для WMTS/XYZ слоёв.")
            return

        if self.raster_export_thread and self.raster_export_thread.isRunning():
            self.warning_message("Выгрузка растра уже выполняется.")
            return

        if self.raster_draw_tool:
            self.raster_draw_tool.rubberBand.reset()
            self.raster_draw_tool = None

        self.raster_draw_tool = DrawRasterExtent(
            iface,
            self,
            int(self.selected_item_num),
            self.selected_item_name
        )
        iface.mapCanvas().setMapTool(self.raster_draw_tool)
        self.pbar.setDisabled(False)
        self.pbar.setFormat("Выберите охват растра на карте")
        self.label_progress_status.setText("Статус: выберите охват растра на карте")
        self.label_progress_status.setVisible(True)


    def start_raster_export_from_geometry(self, geom):
        if self.selected_item_type != 'wmts' or self.selected_item_num is None:
            return

        try:
            bbox_geom = QgsGeometry(geom)
            src_crs = iface.mapCanvas().mapSettings().destinationCrs()
            if not src_crs or not src_crs.isValid():
                src_crs = QgsProject.instance().crs()
            if src_crs and src_crs.isValid() and src_crs.authid() != crs_mercator.authid():
                transform = QgsCoordinateTransform(src_crs, crs_mercator, QgsProject.instance())
                bbox_geom.transform(transform)
            extent = bbox_geom.boundingBox()
        except Exception as e:
            self.warning_message("Не удалось преобразовать охват: {}".format(e))
            return

        zoom_info = get_xyz_zoom_info(int(self.selected_item_num))
        current_z = get_canvas_xyz_zoom()
        z_min = int(zoom_info.get('zmin', NSPD_XYZ_Z_MIN_DEFAULT))
        z_max = int(zoom_info.get('zmax', NSPD_XYZ_Z_MAX_DEFAULT))
        z_dialog_max = max(z_max, NSPD_RASTER_EXPORT_Z_MAX)
        if int(self.selected_item_num) in NSPD_ORTHO_LAYER_IDS:
            current_z = max(z_min, min(z_max, current_z))

        z, ok = QInputDialog.getInt(
            iface.mainWindow(),
            "Масштаб выгрузки НСПД",
            "Zoom-уровень тайлов (z):",
            int(current_z),
            int(z_min),
            int(z_dialog_max),
            1
        )
        if not ok:
            self.pbar.setValue(0)
            self.pbar.setFormat("%p%")
            self.pbar.setDisabled(True)
            return

        x_min, x_max, y_min, y_max = get_extent_xyz_tile_range(extent, z)
        tile_count = tile_range_count(x_min, x_max, y_min, y_max)

        reply = QMessageBox.question(
            iface.mainWindow(),
            "НСПД: выгрузка растра",
            "Будет выгружено тайлов: {}<br>z={}<br><br>Начать?".format(tile_count, z),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply != QMessageBox.StandardButton.Yes:
            self.pbar.setValue(0)
            self.pbar.setFormat("%p%")
            self.pbar.setDisabled(True)
            return

        default_export_dir = get_default_raster_export_dir()
        base_export_dir = QFileDialog.getExistingDirectory(
            iface.mainWindow(),
            'Выберите папку для выгрузки НСПД',
            default_export_dir
        )
        if not base_export_dir:
            self.pbar.setValue(0)
            self.pbar.setFormat("%p%")
            self.pbar.setDisabled(True)
            return
        remember_raster_export_dir(base_export_dir)

        try:
            export_dir = make_unique_export_folder(base_export_dir, self.selected_item_name, z)
        except Exception as e:
            self.warning_message("Не удалось создать папку выгрузки: {}".format(e))
            self.pbar.setValue(0)
            self.pbar.setFormat("%p%")
            self.pbar.setDisabled(True)
            return

        output_vrt_name = 'Ортофотоплан_(z-{})({}).vrt'.format(
            int(z),
            time.strftime('%d_%m_%Y')
        )
        output_vrt_path = os.path.join(export_dir, output_vrt_name)

        self.raster_export_thread = NSPDRasterExportThread(
            int(self.selected_item_num),
            self.selected_item_name,
            extent,
            int(z),
            output_vrt_path
        )
        self.raster_export_thread.progress_updated.connect(self.prbar_upd)
        self.raster_export_thread.status_updated.connect(self.raster_export_status)
        self.raster_export_thread.export_completed.connect(self.raster_export_finished)

        self.pbar.setDisabled(False)
        self.pbar.setValue(0)
        self.pbar.setFormat("%p%")
        self.label_progress_status.setText(
            "Статус: тайлы 0/{} · 0.0% · повторы 0 · ошибки 0 · z={}".format(tile_count, z)
        )
        self.label_progress_status.setVisible(True)
        self.btn_cancel_object.setDisabled(False)
        self.raster_export_thread.start()


    def raster_export_status(self, text):
        self.label_progress_status.setText(text)
        self.label_progress_status.setVisible(True)


    def raster_export_finished(self, result):
        self.pbar.setValue(0)
        self.pbar.setFormat("%p%")
        self.pbar.setDisabled(True)
        self.btn_cancel_object.setDisabled(True)

        if self.raster_draw_tool:
            try:
                iface.mapCanvas().unsetMapTool(self.raster_draw_tool)
                self.raster_draw_tool.rubberBand.reset()
            except Exception:
                pass
            self.raster_draw_tool = None

        try:
            self.raster_export_thread.quit()
            self.raster_export_thread.wait()
        except Exception:
            pass

        if result.get('ok'):
            layer_name = result.get('layer_name') or self.selected_item_name
            layer = QgsRasterLayer(result.get('vrt_path', ''), 'НСПД_выгрузка_{}_z{}'.format(layer_name, result.get('z')))
            if layer.isValid():
                layer.setCrs(crs_mercator)
                QgsProject.instance().addMapLayer(layer)
            total = max(1, int(result.get('total', 0) or 0))
            downloaded = int(result.get('downloaded', 0) or 0)
            retries = int(result.get('retries', 0) or 0)
            errors = int(result.get('errors', 0) or 0)
            z = result.get('z', '')
            self.label_progress_status.setText(
                "Статус: готово · тайлы {}/{} · {:.1f}% · повторы {} · ошибки {} · z={}".format(
                    downloaded,
                    total,
                    (downloaded / total) * 100.0,
                    retries,
                    errors,
                    z
                )
            )
            self.label_progress_status.setVisible(True)
            self.warning_message(result.get('message', 'Выгрузка завершена.'))
        elif result.get('cancelled'):
            self.label_progress_status.setText("Статус: выгрузка отменена")
            self.label_progress_status.setVisible(True)
            self.warning_message("Выгрузка растра отменена.")
        else:
            self.label_progress_status.setText("Статус: ошибка выгрузки")
            self.label_progress_status.setVisible(True)
            self.warning_message(result.get('message', 'Выгрузка растра завершилась с ошибкой.'))


    def get_object(self):
        current_item = self.tree.currentItem()
        if not current_item:
            return
        item_num = current_item.data(0, Qt.ItemDataRole.UserRole)
        item_category = current_item.data(1, Qt.ItemDataRole.UserRole)
        item_type = current_item.data(2, Qt.ItemDataRole.UserRole) or 'wms'
        item_name = current_item.text(0)
        if not current_item.childCount():
            if item_type == 'wmts':
                self.export_selected_raster()
                return
            if self.draw_tool:
                self.draw_tool.rubberBand.reset()
                self.draw_tool = None
            self.draw_tool = DrawExtent(iface, self, item_name, item_num, item_category)
            iface.mapCanvas().setMapTool(self.draw_tool)
    

    def showEvent(self, event):
        self.btn_get_object.setFixedWidth(32)
        self.btn_get_object.setIconSize(QSize(24, 24))

        self.btn_cancel_object.setFixedWidth(32)
        self.btn_cancel_object.setIconSize(QSize(24, 24))

        self.btn_search.setFixedWidth(32)
        self.btn_search.setIconSize(QSize(24, 24))

        self.search_line.setMinimumHeight(self.btn_get_object.sizeHint().height())


    def onItemClickedSingle(self):
        current_item = self.tree.currentItem()
        item_num = current_item.data(0, Qt.ItemDataRole.UserRole)
        item_name = current_item.text(0)
        
        item_category = current_item.data(1, Qt.ItemDataRole.UserRole)
        item_type = current_item.data(2, Qt.ItemDataRole.UserRole) or 'wms'
        if not current_item.childCount():
            self.selected_item_num = item_num
            self.selected_item_name = item_name
            self.selected_item_category = item_category
            self.selected_item_type = item_type
            self.update_active_layer_label()
            self.configure_download_button()
            if self.draw_tool:
                self.draw_tool.rubberBand.reset()
                self.draw_tool = None
            if item_type != 'wmts':
                self.draw_tool = DrawExtent(iface, self, item_name, item_num, item_category)
            
        else:
            self.selected_item_num = None
            self.selected_item_name = ''
            self.selected_item_category = None
            self.selected_item_type = None
            self.update_active_layer_label()
            self.configure_download_button()
            if self.draw_tool:
                iface.mapCanvas().unsetMapTool(self.draw_tool)
                self.draw_tool.rubberBand.reset()
                self.draw_tool = None
            
        return item_num, item_name

    
    def onItemClicked(self):
        current_item = self.tree.currentItem()
        item_num = current_item.data(0, Qt.ItemDataRole.UserRole)
        item_name = current_item.text(0)
        item_type = current_item.data(2, Qt.ItemDataRole.UserRole) or 'wms'

        if not current_item.childCount():
            if item_type == 'wmts':
                add_xyz_layer(int(item_num), item_name)
            else:
                add_wms_layer(item_num, item_name)

        return item_num, item_name
    
    
    def save_wms(self, layer_num, layer_name):
        src_url = wms_url_template.format(layer_num)
        check_wms_keys = [k for k in QSettings().allKeys() if '/wms/' in k and layer_name in k ]
        if not check_wms_keys:
            for src_key in wms_keys:
                wms_value = src_url if 'url' in src_key else ""
                if 'referer' in src_key:
                    wms_value = 'https://nspd.gov.ru/map?active_layers%3D%E9%8B%8B'
                if '-header' in src_key:
                    wms_value = {'referer': 'https://nspd.gov.ru/map?active_layers=%E9%8B%8B'}
                QSettings().setValue(src_key.format('НСПД: '+layer_name), wms_value)
            iface.reloadConnections()

    def add_layer(self):
        """
        Сохраняет выбранный слой в списке соединений QGIS (WMS или XYZ),
        чтобы он появился в Browser/Connections и мог переиспользоваться.
        """
        current_item = self.tree.currentItem()
        if not current_item:
            return

        layer_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        layer_name = current_item.text(0)
        layer_type = current_item.data(2, Qt.ItemDataRole.UserRole) or 'wms'

        if current_item.childCount():
            return

        if layer_type == 'wmts':
            save_xyz_connection(int(layer_id), layer_name)
        else:
            self.save_wms(layer_id, layer_name)


def build_xyz_http_header():
    hdr = {'referer': XYZ_REFERRER, 'origin': XYZ_ORIGIN, 'user-agent': XYZ_UA}
    if NSPD_AUTH_TOKEN:
        hdr['authorization'] = f'Bearer {NSPD_AUTH_TOKEN}'
    return hdr


def save_xyz_connection(layer_id, layer_name, zmin=None, zmax=None):
    conn_name = 'НСПД: ' + layer_name
    url = wmts_url_template.format(layer_id)
    if zmin is None or zmax is None:
        zoom_info = get_xyz_zoom_info(layer_id)
        zmin = zoom_info['zmin']
        zmax = zoom_info['zmax']
    zmin = int(zmin)
    zmax = int(zmax)

    s = QSettings()

    # Новые ветки в QGIS: connections-xyz
    # В разных версиях ключи слегка отличаются, поэтому пишем набором.
    candidates = [
        # QGIS 3.28/3.34 часто читает это
        ('qgis/connections-xyz/{}/url', url),
        ('qgis/connections-xyz/{}/zmin', zmin),
        ('qgis/connections-xyz/{}/zmax', zmax),
        # заголовки (часто именно так)
        ('qgis/connections-xyz/{}/http-header', build_xyz_http_header()),
        ('qgis/connections-xyz/{}/referer', XYZ_REFERRER),
        # QGIS 3.40+ может читать новую ветку настроек.
        ('connections/xyz/items/{}/url', url),
        ('connections/xyz/items/{}/zmin', zmin),
        ('connections/xyz/items/{}/zmax', zmax),
        ('connections/xyz/items/{}/http-header', build_xyz_http_header()),
    ]

    for k, v in candidates:
        s.setValue(k.format(conn_name), v)

    iface.reloadConnections()

data, layers_meta = get_tms_list()
if not data.get('tree', {}).get('folders', {}):
    msg = QMessageBox(iface.mainWindow())
    msg.setTextFormat(Qt.TextFormat.RichText)
    msg.setWindowTitle("Уведомление")
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.setText('Сервис НСПД временно недоступен.<br>Рекомендуется отслеживать доступность НСПД на <a href="https://nspd.gov.ru/map">сайте</a>')
    msg.exec()
else:
    dockwidget = NSPD_DockWidget(None, data, layers_meta)
    iface.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dockwidget)
