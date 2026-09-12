#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对选中书籍执行：解析 gid/token -> 拉取 E-Hentai 元数据 -> 写 calibre / 嵌入 ComicInfo.xml。"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
import re
import traceback
from io import BytesIO
from zipfile import ZipFile

from calibre.gui2 import error_dialog, info_dialog
from calibre.utils.zipfile import safe_replace

from calibre_plugins.EHentaiComicInfo.api import fetch_gmetadata
from calibre_plugins.EHentaiComicInfo.comicinfo import build_comicinfo_xml
from calibre_plugins.EHentaiComicInfo.config import prefs
from calibre_plugins.EHentaiComicInfo.metadata import build_calibre_mi

# 书名/文件名（去扩展名）中的 gid-token
GID_TOKEN_RE = re.compile(r'^(\d+)-([0-9a-fA-F]+)$')


def log(msg):
    print('[EHentaiComicInfo]', msg)


def resolve_gid_token(db, book_id, mi):
    """按 identifier -> 书名 -> 书库文件名 的顺序解析 (gid, token)。"""
    ident = (mi.identifiers or {}).get('ehentai') or ''
    if ident:
        parts = ident.split('_')
        if len(parts) >= 2 and parts[0].isdigit() and re.match(r'^[0-9a-fA-F]+$', parts[1]):
            return int(parts[0]), parts[1].lower()

    m = GID_TOKEN_RE.match((mi.title or '').strip())
    if m:
        return int(m.group(1)), m.group(2).lower()

    for fmt in ('cbz', 'zip', 'cbr', 'cb7'):
        if db.has_format(book_id, fmt):
            path = db.format_abspath(book_id, fmt)
            if path:
                base = os.path.splitext(os.path.basename(path))[0]
                m = GID_TOKEN_RE.match(base)
                if m:
                    return int(m.group(1)), m.group(2).lower()
    return None


def convert_zip_to_cbz(db, book_id):
    """将书库中的 zip 格式转为 cbz（内容不变，仅改扩展名）。返回是否发生了转换。"""
    if not db.has_format(book_id, 'zip') or db.has_format(book_id, 'cbz'):
        return False
    zpath = db.format(book_id, 'zip', as_path=True)
    cpath = os.path.splitext(zpath)[0] + '.cbz'
    os.rename(zpath, cpath)
    try:
        db.add_format(book_id, 'cbz', cpath, replace=True)
        db.remove_formats({book_id: {'zip'}})
    finally:
        try:
            os.remove(cpath)
        except OSError:
            pass
    return True


def embed_comicinfo(db, book_id, xml_text):
    """将 ComicInfo.xml 写入 cbz/zip；已存在则原位替换。返回使用的格式名。"""
    fmt = None
    for candidate in ('cbz', 'zip'):
        if db.has_format(book_id, candidate):
            fmt = candidate
            break
    if fmt is None:
        raise ValueError('书籍没有 cbz/zip 格式的文件')

    path = db.format(book_id, fmt, as_path=True)
    data = xml_text.encode('utf-8')

    existing = None
    with ZipFile(path) as zf:
        for name in zf.namelist():
            if name.lower() == 'comicinfo.xml':
                existing = name
                break

    if existing is not None:
        # 原位替换，避免重建 zip 产生重复条目
        with open(path, 'r+b') as f:
            safe_replace(f, existing, BytesIO(data))
    else:
        with ZipFile(path, 'a') as zf:
            zf.writestr('ComicInfo.xml', data)

    db.add_format(book_id, fmt, path, replace=True)
    try:
        os.remove(path)
    except OSError:
        pass
    return fmt


def run_fetch(ia, update_calibre=True, embed_xml=True):
    """主流程：对选中的书籍批量获取 E-Hentai 元数据。"""
    gui = ia.gui
    db = gui.current_db.new_api

    rows = gui.library_view.selectionModel().selectedRows()
    if not rows:
        return error_dialog(gui, 'EHentai ComicInfo', '没有选中的书籍', show=True)
    book_ids = [gui.library_view.model().id(r) for r in rows]

    # 1. 解析每本书的 (gid, token)
    targets = []   # (book_id, label, gid, token)
    skipped = []
    for book_id in book_ids:
        mi = db.get_metadata(book_id)
        label = '%s - %s' % (mi.title, ', '.join(mi.authors or []))
        gt = resolve_gid_token(db, book_id, mi)
        if gt is None:
            skipped.append(label)
        else:
            targets.append((book_id, label, gt[0], gt[1]))

    if not targets:
        return info_dialog(gui, 'EHentai ComicInfo',
                           '没有可处理的书籍。\n\n无法从以下书籍中解析 {gid}-{token}：\n    %s'
                           % '\n    '.join(skipped), show=True)

    # 2. 批量调用 API（自动去重 gidlist）
    seen = set()
    gidlist = []
    for _, _, gid, token in targets:
        if gid not in seen:
            seen.add(gid)
            gidlist.append((gid, token))

    proxy = prefs['proxy_url'].strip() if prefs['use_proxy'] else None
    try:
        gmetas = fetch_gmetadata(gidlist, proxy=proxy,
                                 interval=int(prefs['request_interval'] or 5),
                                 log=log)
    except Exception as e:
        log(traceback.format_exc())
        return error_dialog(gui, 'EHentai ComicInfo',
                            '调用 E-Hentai API 失败：\n%s' % e,
                            det_msg=traceback.format_exc(), show=True)

    # 3. 逐本应用
    ok, failed = [], []
    for book_id, label, gid, token in targets:
        gmeta = gmetas.get(gid)
        if not gmeta:
            failed.append('%s（API 未返回 gid=%s）' % (label, gid))
            continue
        if 'error' in gmeta:
            failed.append('%s（%s）' % (label, gmeta['error']))
            continue
        try:
            if update_calibre:
                mi = build_calibre_mi(gmeta)
                db.set_metadata(book_id, mi, force_changes=True, allow_case_change=True)

            if embed_xml:
                if prefs['convert_zip_to_cbz'] and convert_zip_to_cbz(db, book_id):
                    log('book %s: zip 已转为 cbz' % book_id)
                xml_text = build_comicinfo_xml(gmeta)
                fmt = embed_comicinfo(db, book_id, xml_text)
                log('book %s: ComicInfo.xml 已写入 %s' % (book_id, fmt))

            ok.append(label)
        except Exception as e:
            log(traceback.format_exc())
            failed.append('%s（%s）' % (label, e))

    # 4. 汇总
    msg = '成功处理 %d 本书。' % len(ok)
    if skipped:
        msg += '\n\n以下书籍无法解析 {gid}-{token}，已跳过：\n    %s' % '\n    '.join(skipped)
    if failed:
        msg += '\n\n以下书籍处理失败：\n    %s' % '\n    '.join(failed)
    info_dialog(gui, 'EHentai ComicInfo', msg, show=True)

    if ok:
        # 刷新书库视图
        gui.library_view.model().refresh_ids(set(book_ids))
        gui.current_tags = None
        gui.tags_view.recount()
