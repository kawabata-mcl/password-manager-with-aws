#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ログインウィンドウ

アプリケーションのログイン画面を提供します。
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                           QLabel, QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
from .main_window import MainWindow
import json
import os
from cryptography.fernet import Fernet
from pathlib import Path

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("パスワードマネージャー - ログイン")
        self.setFixedSize(400, 200)
        
        # メインウィジェットとレイアウトの設定
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # ユーザー名入力
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("ユーザー名")
        layout.addWidget(QLabel("ユーザー名:"))
        layout.addWidget(self.username_input)
        
        # パスワード入力
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("パスワード")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("パスワード:"))
        layout.addWidget(self.password_input)
        
        # ログインボタン
        login_button = QPushButton("ログイン")
        login_button.clicked.connect(self.login)
        layout.addWidget(login_button)
        
        # 新規登録ボタン
        register_button = QPushButton("新規登録")
        register_button.clicked.connect(self.register)
        layout.addWidget(register_button)
        
        # ログイン試行回数の初期化
        self.login_attempts = 0
        self.max_attempts = 3
        
        # 暗号化キーの設定
        self.setup_encryption()

    def setup_encryption(self):
        """暗号化の初期設定"""
        key_file = Path.home() / '.password_manager' / 'key.key'
        key_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not key_file.exists():
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
        
        with open(key_file, 'rb') as f:
            self.key = f.read()
        
        self.cipher_suite = Fernet(self.key)

    def get_user_data_path(self):
        """ユーザーデータファイルのパスを取得"""
        return Path.home() / '.password_manager' / 'users.dat'

    def load_users(self):
        """保存されているユーザー情報を読み込む"""
        try:
            if not self.get_user_data_path().exists():
                return {}
            
            with open(self.get_user_data_path(), 'rb') as f:
                encrypted_data = f.read()
                decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                return json.loads(decrypted_data)
        except Exception:
            return {}

    def save_users(self, users):
        """ユーザー情報を保存"""
        encrypted_data = self.cipher_suite.encrypt(json.dumps(users).encode())
        with open(self.get_user_data_path(), 'wb') as f:
            f.write(encrypted_data)

    def login(self):
        """ログイン処理"""
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "エラー", "ユーザー名とパスワードを入力してください。")
            return
        
        users = self.load_users()
        
        if username not in users or users[username] != password:
            self.login_attempts += 1
            remaining = self.max_attempts - self.login_attempts
            
            if remaining == 0:
                QMessageBox.critical(self, "エラー", "ログイン試行回数が上限に達しました。\nアプリケーションを終了します。")
                self.close()
            else:
                QMessageBox.warning(self, "エラー", 
                                  f"ユーザー名またはパスワードが正しくありません。\n残り試行回数: {remaining}")
            return
        
        # ログイン成功
        self.main_window = MainWindow(username)
        self.main_window.show()
        self.close()

    def register(self):
        """新規ユーザー登録"""
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "エラー", "ユーザー名とパスワードを入力してください。")
            return
        
        users = self.load_users()
        
        if username in users:
            QMessageBox.warning(self, "エラー", "このユーザー名は既に使用されています。")
            return
        
        users[username] = password
        self.save_users(users)
        
        QMessageBox.information(self, "成功", "ユーザー登録が完了しました。")
        self.username_input.clear()
        self.password_input.clear() 