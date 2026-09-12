#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""由 E-Hentai gallery metadata 生成 ComicInfo.xml。"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from datetime import datetime, timezone
from xml.dom import minidom
from xml.etree import ElementTree as ET

# E-Hentai language tag -> BCP 47
LANGUAGE_MAP = {
    'english': 'en', 'japanese': 'ja', 'chinese': 'zh', 'korean': 'ko',
    'spanish': 'es', 'french': 'fr', 'german': 'de', 'russian': 'ru',
    'italian': 'it', 'portuguese': 'pt', 'thai': 'th', 'vietnamese': 'vi',
    'polish': 'pl', 'dutch': 'nl', 'indonesian': 'id', 'ukrainian': 'uk',
    'czech': 'cs', 'hungarian': 'hu', 'swedish': 'sv', 'turkish': 'tr',
    'arabic': 'ar', 'tagalog': 'tl', 'finnish': 'fi', 'danish': 'da',
    'norwegian': 'no', 'greek': 'el', 'hebrew': 'he', 'catalan': 'ca',
    'slovak': 'sk', 'romanian': 'ro', 'bulgarian': 'bg', 'croatian': 'hr',
    'serbian': 'sr', 'slovenian': 'sl', 'estonian': 'et', 'latvian': 'lv',
    'lithuanian': 'lt', 'persian': 'fa', 'mongolian': 'mn', 'esperanto': 'eo',
}
LANGUAGE_IGNORE = {'translated', 'rewrite', 'n/a', 'text cleaned', 'speechless'}

# 非日式阅读方向的类别
WESTERN_CATEGORIES = {'Western'}


def split_namespaced_tags(tags):
    """将 'namespace:value' 形式的 tag 按命名空间分组。"""
    grouped = {}
    for tag in tags:
        if ':' in tag:
            ns, value = tag.split(':', 1)
            grouped.setdefault(ns.strip(), []).append(value.strip())
    return grouped


def build_comicinfo_xml(meta):
    """将 gallery metadata 转换为 ComicInfo.xml 文本。"""
    tags = meta.get('tags') or []
    grouped = split_namespaced_tags(tags)

    title_jpn = (meta.get('title_jpn') or '').strip()
    title = (meta.get('title') or '').strip()

    fields = {}

    fields['Title'] = title_jpn or title
    if title and title != fields['Title']:
        fields['Summary'] = title
    elif title_jpn and title:
        fields['Summary'] = title

    if grouped.get('artist'):
        fields['Writer'] = ', '.join(grouped['artist'])
    if grouped.get('group'):
        fields['Publisher'] = ', '.join(grouped['group'])

    category = (meta.get('category') or '').strip()
    tag_list = ([f'category:{category}'] if category else []) + tags
    if tag_list:
        fields['Tags'] = ', '.join(tag_list)

    for lang in grouped.get('language', []):
        if lang.lower() in LANGUAGE_IGNORE:
            continue
        fields['LanguageISO'] = LANGUAGE_MAP.get(lang.lower(), lang)
        break

    gid = meta.get('gid')
    token = meta.get('token')
    if gid and token:
        fields['Web'] = 'https://e-hentai.org/g/%s/%s/' % (gid, token)

    filecount = meta.get('filecount')
    if filecount:
        try:
            fields['PageCount'] = int(filecount)
        except (TypeError, ValueError):
            pass

    posted = meta.get('posted')
    if posted:
        try:
            dt = datetime.fromtimestamp(int(posted), tz=timezone.utc)
            fields['Year'], fields['Month'], fields['Day'] = dt.year, dt.month, dt.day
        except (TypeError, ValueError, OSError):
            pass

    fields['Manga'] = 'No' if category in WESTERN_CATEGORIES else 'YesAndRightToLeft'

    rating = meta.get('rating')
    if rating:
        try:
            fields['CommunityRating'] = ('%.2f' % float(rating)).rstrip('0').rstrip('.')
        except (TypeError, ValueError):
            pass

    root = ET.Element('ComicInfo')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    root.set('xmlns:xsd', 'http://www.w3.org/2001/XMLSchema')
    order = ['Title', 'Summary', 'Writer', 'Publisher', 'Tags', 'LanguageISO',
             'Web', 'PageCount', 'Year', 'Month', 'Day', 'Manga', 'CommunityRating']
    for name in order:
        if name in fields and fields[name] not in (None, ''):
            el = ET.SubElement(root, name)
            el.text = str(fields[name])

    raw = ET.tostring(root, encoding='unicode')
    pretty = minidom.parseString(raw).toprettyxml(indent='  ', encoding=None)
    # 去掉 minidom 生成的多余空行，保留 xml 声明
    lines = [ln for ln in pretty.splitlines() if ln.strip()]
    return '\n'.join(lines) + '\n'
