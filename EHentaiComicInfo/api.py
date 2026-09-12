#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E-Hentai gdata API 客户端（仅标准库，支持代理与分批限速）。"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import json
import time
import urllib.request

API_URL = 'https://api.e-hentai.org/api.php'
BATCH_SIZE = 25  # API 单次请求上限


def fetch_gmetadata(gidlist, proxy=None, interval=5, timeout=60, log=None):
    """分批调用 gdata 接口。

    :param gidlist: [(gid, token), ...]
    :param proxy: 代理 URL（None 表示直连）
    :param interval: 批与批之间的间隔秒数
    :return: {gid: gmetadata dict}
    """
    if log is None:
        log = _default_log

    handlers = []
    if proxy:
        handlers.append(urllib.request.ProxyHandler({'http': proxy, 'https': proxy}))
    else:
        handlers.append(urllib.request.ProxyHandler({}))  # 显式禁用系统代理
    opener = urllib.request.build_opener(*handlers)

    results = {}
    total = len(gidlist)
    for i in range(0, total, BATCH_SIZE):
        chunk = gidlist[i:i + BATCH_SIZE]
        log('查询 E-Hentai API: %d-%d / %d' % (i + 1, i + len(chunk), total))
        payload = json.dumps({
            'method': 'gdata',
            'gidlist': [[gid, token] for gid, token in chunk],
            'namespace': 1,
        }).encode('utf-8')
        req = urllib.request.Request(
            API_URL, data=payload,
            headers={'Content-Type': 'application/json'},
        )
        with opener.open(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        for entry in data.get('gmetadata', []):
            results[entry['gid']] = entry
        if i + BATCH_SIZE < total:
            time.sleep(interval)
    return results


def _default_log(msg):
    print('[EHentaiComicInfo]', msg)
