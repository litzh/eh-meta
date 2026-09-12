#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""界面动作：工具栏按钮 + 菜单。"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from qt.core import QMenu

from calibre.gui2.actions import InterfaceAction


class EHentaiComicInfo(InterfaceAction):

    name = 'EHentai ComicInfo'
    action_spec = ('EHentai ComicInfo', None,
                   '从 E-Hentai 获取元数据并嵌入 ComicInfo.xml', None)

    def genesis(self):
        self.menu = QMenu(self.gui)
        self.qaction.setMenu(self.menu)

        # 主按钮默认执行「全部」
        self.qaction.triggered.connect(self.do_all)

        self.menu.addAction('获取元数据并嵌入 ComicInfo（全部）',
                            lambda: self._run(True, True))
        self.menu.addAction('仅更新 calibre 元数据',
                            lambda: self._run(True, False))
        self.menu.addAction('仅嵌入 ComicInfo.xml',
                            lambda: self._run(False, True))
        self.menu.addSeparator()
        self.menu.addAction('配置…', self._configure)

    def do_all(self):
        self._run(True, True)

    def _run(self, update_calibre, embed_xml):
        from calibre_plugins.EHentaiComicInfo.main import run_fetch
        run_fetch(self, update_calibre=update_calibre, embed_xml=embed_xml)

    def _configure(self):
        self.interface_action_base_plugin.do_user_config(self.gui)

    def apply_settings(self):
        pass
