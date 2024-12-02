#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
パスワードマネージャーアプリケーション

このアプリケーションは、AWSパラメータストアを使用してパスワード情報を
安全に管理するためのデスクトップアプリケーションです。
"""

import sys
from PyQt6.QtWidgets import QApplication
from ui.login_window import LoginWindow

def main():
    """アプリケーションのメインエントリーポイント"""
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec()) 