#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EHentai Import — calibre 元数据读取插件。

添加图书时，若 zip 文件名符合 E-Hentai 命名格式 {gallery_id}-{gallery_token}.zip
（例如 2231376-a7584a5932.zip），自动将 ehentai identifier 写入书籍元数据，
供 EHentai ComicInfo 插件后续精确获取元数据。

文件名不匹配时抛出异常，calibre 会自动回退到默认的文件名解析逻辑。
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

__license__ = 'GPL v3'
__copyright__ = '2026, lance'
__docformat__ = 'restructuredtext en'

import os
import re

from calibre.customize import MetadataReaderPlugin

ZIP_NAME_RE = re.compile(r'^(\d+)-([0-9a-fA-F]+)\.zip$', re.IGNORECASE)


class EHentaiImport(MetadataReaderPlugin):

    name = 'EHentai Import'
    description = ('从 {gid}-{token}.zip 格式的 E-Hentai 文件名中识别 gallery，'
                   '导入时自动写入 ehentai identifier')
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'lance'
    version = (1, 0, 0)
    minimum_calibre_version = (5, 0, 0)

    file_types = {'zip'}

    def get_metadata(self, stream, ftype):
        from calibre.ebooks.metadata import MetaInformation

        fname = os.path.basename(getattr(stream, 'name', '') or '')
        m = ZIP_NAME_RE.match(fname)
        if not m:
            # 不是 E-Hentai 命名的 zip：抛异常让 calibre 回退默认逻辑
            raise ValueError('Not an E-Hentai archive name: %s' % fname)

        gid, token = m.group(1), m.group(2).lower()
        mi = MetaInformation(None, None)
        # 只设置 identifiers，title/authors 等由 calibre 从文件名兜底
        mi.identifiers = {'ehentai': '%s_%s' % (gid, token)}
        return mi
