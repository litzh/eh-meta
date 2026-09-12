#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EHentai ComicInfo — calibre 界面动作插件。

对选中的书籍：
1. 从 ehentai identifier / 书名 / 书库文件名中解析 {gid}-{token}；
2. 调用 E-Hentai gdata API 获取元数据，覆盖写入 calibre（日文标题优先）；
3. 生成 ComicInfo.xml 嵌入压缩包（zip 可选先转 cbz）。
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

__license__ = 'GPL v3'
__copyright__ = '2026, lance'
__docformat__ = 'restructuredtext en'

from calibre.customize import InterfaceActionBase


class EHentaiComicInfoBase(InterfaceActionBase):

    name = 'EHentai ComicInfo'
    description = ('根据 {gid}-{token} 文件名/identifier 调用 E-Hentai API 获取元数据，'
                   '写入 calibre 并在压缩包内嵌入 ComicInfo.xml')
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'lance'
    version = (1, 0, 0)
    minimum_calibre_version = (6, 0, 0)

    actual_plugin = 'calibre_plugins.EHentaiComicInfo.ui:EHentaiComicInfo'

    def is_customizable(self):
        return True

    def config_widget(self):
        # 延迟导入，避免命令行下加载 GUI 库
        if self.actual_plugin_:
            from calibre_plugins.EHentaiComicInfo.config import ConfigWidget
            return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.save_settings()
