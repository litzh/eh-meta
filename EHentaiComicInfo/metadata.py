#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""由 E-Hentai gallery metadata 构建 calibre Metadata 对象。

- 标题日文优先（title_jpn），并解析 (社团)[作者]标题(杂志/原作)[附加] 结构；
- 覆盖式更新：调用方用 set_metadata 直接写入。
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import re
from datetime import datetime, timezone

from calibre.ebooks.metadata import MetaInformation

# E-Hentai language tag -> ISO 639-3（calibre languages 字段使用 639-3）
LANG_ISO639_3 = {
    'english': 'eng', 'japanese': 'jpn', 'chinese': 'zho', 'korean': 'kor',
    'spanish': 'spa', 'french': 'fra', 'german': 'deu', 'russian': 'rus',
    'italian': 'ita', 'portuguese': 'por', 'thai': 'tha', 'vietnamese': 'vie',
    'polish': 'pol', 'dutch': 'nld', 'indonesian': 'ind', 'ukrainian': 'ukr',
    'czech': 'ces', 'hungarian': 'hun', 'swedish': 'swe', 'turkish': 'tur',
    'arabic': 'ara', 'tagalog': 'tgl', 'finnish': 'fin', 'danish': 'dan',
    'norwegian': 'nor', 'greek': 'ell', 'hebrew': 'heb', 'catalan': 'cat',
    'slovak': 'slk', 'romanian': 'ron', 'bulgarian': 'bul', 'croatian': 'hrv',
    'serbian': 'srp', 'slovenian': 'slv', 'estonian': 'est', 'latvian': 'lav',
    'lithuanian': 'lit', 'persian': 'fas', 'mongolian': 'mon', 'esperanto': 'epo',
}
LANGUAGE_IGNORE = {'translated', 'rewrite', 'n/a', 'text cleaned', 'speechless'}


def _optional(pattern):
    return '(?:' + pattern + ')?'


# (publisher) [author] title (magazine_or_parody) [add1] [add2] [add3]
_TITLE_RE = re.compile(
    r'^\s*'
    + _optional(r'\((?P<publisher>[^\(\)]+)\)')
    + r'\s*'
    + _optional(r'\[(?P<author>[^\[\]]+)\]')
    + r'\s*'
    + r'(?P<title>[^\[\]\(\)]+)'
    + r'\s*'
    + _optional(r'\((?P<magazine_or_parody>[^\(\)]+)\)')
    + r'\s*'
    + _optional(r'\[(?P<add1>[^\[\]]+)\]')
    + r'\s*'
    + _optional(r'\[(?P<add2>[^\[\]]+)\]')
    + r'\s*'
    + _optional(r'\[(?P<add3>[^\[\]]+)\]')
)


def parse_title(title):
    """解析 E-Hentai 标题结构，返回 (clean_title, author, publisher)。"""
    m = _TITLE_RE.match(title or '')
    if not m:
        return (title or '').strip(), None, None
    return (m.group('title').strip(), m.group('author'), m.group('publisher'))


def _grouped_tags(tags):
    grouped = {}
    for tag in tags or []:
        if ':' in tag:
            ns, value = tag.split(':', 1)
            grouped.setdefault(ns.strip(), []).append(value.strip())
    return grouped


def build_calibre_mi(gmeta):
    """将 gdata 返回的 gmetadata dict 转为 calibre MetaInformation。

    未设置的字段保持 None，调用方 set_metadata 时不会改动这些字段。
    """
    tags = gmeta.get('tags') or []
    grouped = _grouped_tags(tags)

    title_jpn = (gmeta.get('title_jpn') or '').strip()
    title_eng = (gmeta.get('title') or '').strip()
    raw_title = title_jpn or title_eng
    clean_title, parsed_author, parsed_publisher = parse_title(raw_title)

    mi = MetaInformation(None, None)

    # 标题：日文优先，去掉 (社团)[作者] 等包装
    mi.title = clean_title or raw_title

    # 作者：artist tag 优先，其次标题中解析出的作者
    if grouped.get('artist'):
        mi.authors = grouped['artist']
    elif parsed_author:
        mi.authors = [parsed_author]

    # 出版者：group tag 优先，其次标题中解析出的社团
    if grouped.get('group'):
        mi.publisher = ', '.join(grouped['group'])
    elif parsed_publisher:
        mi.publisher = parsed_publisher

    # 标签：category + 全部原始 tags
    category = (gmeta.get('category') or '').strip()
    mi.tags = ([f'category:{category}'] if category else []) + list(tags)

    # 语言
    for lang in grouped.get('language', []):
        code = LANG_ISO639_3.get(lang.lower())
        if code and lang.lower() not in LANGUAGE_IGNORE:
            mi.languages = [code]
            break

    # 评分：E-Hentai 0-5 -> calibre 0-10
    rating = gmeta.get('rating')
    if rating:
        try:
            mi.rating = max(0.0, min(10.0, float(rating) * 2))
        except (TypeError, ValueError):
            pass

    # 发布日期
    posted = gmeta.get('posted')
    if posted:
        try:
            mi.pubdate = datetime.fromtimestamp(int(posted), tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            pass

    # identifier
    gid, token = gmeta.get('gid'), gmeta.get('token')
    if gid and token:
        mi.identifiers = {'ehentai': '%s_%s' % (gid, token)}
        url = 'https://e-hentai.org/g/%s/%s/' % (gid, token)
        comments = []
        if title_eng and title_eng != raw_title:
            comments.append(title_eng)
        comments.append(url)
        mi.comments = '\n'.join(comments)

    return mi
