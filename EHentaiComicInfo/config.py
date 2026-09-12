#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""插件配置（JSONConfig + 配置对话框）。

注意：本模块仅在 GUI 环境下被 __init__.py 的 config_widget() 延迟导入，
因此可以安全地在顶部导入 Qt。
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from qt.core import (QWidget, QVBoxLayout, QFormLayout, QCheckBox,
                     QLineEdit, QSpinBox)

from calibre.utils.config import JSONConfig

prefs = JSONConfig('plugins/EHentaiComicInfo')
prefs.defaults = {
    'use_proxy': True,
    'proxy_url': 'http://127.0.0.1:7890',
    'request_interval': 5,       # 批量 API 请求之间的间隔（秒）
    'convert_zip_to_cbz': True,  # 嵌入 ComicInfo 前将 zip 转为 cbz
}


class ConfigWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        outer = QVBoxLayout()
        self.setLayout(outer)
        form = QFormLayout()
        outer.addLayout(form)

        self.use_proxy = QCheckBox('通过代理访问 E-Hentai API')
        self.use_proxy.setChecked(bool(prefs['use_proxy']))
        form.addRow(self.use_proxy)

        self.proxy_url = QLineEdit(str(prefs['proxy_url'] or ''))
        self.proxy_url.setPlaceholderText('http://127.0.0.1:7890')
        form.addRow('代理地址', self.proxy_url)

        self.interval = QSpinBox()
        self.interval.setRange(0, 60)
        self.interval.setValue(int(prefs['request_interval'] or 5))
        form.addRow('请求间隔（秒）', self.interval)

        self.convert_cbz = QCheckBox('嵌入 ComicInfo 前将 ZIP 转换为 CBZ')
        self.convert_cbz.setChecked(bool(prefs['convert_zip_to_cbz']))
        form.addRow(self.convert_cbz)

        outer.addStretch(1)

    def save_settings(self):
        prefs['use_proxy'] = self.use_proxy.isChecked()
        prefs['proxy_url'] = self.proxy_url.text().strip()
        prefs['request_interval'] = self.interval.value()
        prefs['convert_zip_to_cbz'] = self.convert_cbz.isChecked()
