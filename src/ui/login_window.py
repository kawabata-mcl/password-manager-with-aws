#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ログインウィンドウ

アプリケーションのログイン画面を提供します。
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                           QLabel, QLineEdit, QPushButton, QMessageBox,
                           QDialog, QHBoxLayout)
from PyQt6.QtCore import Qt
from .main_window import MainWindow
from ..utils.credentials_manager import CredentialsManager
import json
import os
from cryptography.fernet import Fernet
from pathlib import Path

class AWSCredentialsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('AWS認証情報の設定')
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout()
        
        # アクセスキー
        access_key_label = QLabel('AWSアクセスキー:')
        self.access_key_input = QLineEdit()
        self.access_key_input.setPlaceholderText('AWSアクセスキーを入力')
        layout.addWidget(access_key_label)
        layout.addWidget(self.access_key_input)
        
        # シークレットキー
        secret_key_label = QLabel('AWSシークレットキー:')
        self.secret_key_input = QLineEdit()
        self.secret_key_input.setPlaceholderText('AWSシークレットキーを入力')
        self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(secret_key_label)
        layout.addWidget(self.secret_key_input)
        
        # ボタン
        button_layout = QHBoxLayout()
        save_button = QPushButton('保存')
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton('キャンセル')
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_credentials(self):
        """入力された認証情報を取得"""
        return {
            'access_key': self.access_key_input.text(),
            'secret_key': self.secret_key_input.text()
        }

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("パスワードマネージャー - ログイン")
        self.setFixedSize(400, 200)
        
        # 認証情報マネージャーの初期化
        self.credentials_manager = CredentialsManager()
        
        # メインウィジェットとレイアウトの設定
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # ユーザー名入力
        username_label = QLabel('ユーザー名:')
        self.username_input = QLineEdit()
        self.username_input.returnPressed.connect(self.on_return_pressed)
        layout.addWidget(username_label)
        layout.addWidget(self.username_input)
        
        # パスワード入力
        password_label = QLabel('パスワード:')
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.on_return_pressed)
        layout.addWidget(password_label)
        
        # パスワード入力欄とトグルボタンを水平に配置
        password_layout = QHBoxLayout()
        password_layout.addWidget(self.password_input)
        
        # パスワード表示/非表示切り替えボタン
        show_password_button = QPushButton('表示')
        show_password_button.setFixedWidth(60)
        show_password_button.clicked.connect(self.toggle_password_visibility)
        password_layout.addWidget(show_password_button)
        
        layout.addLayout(password_layout)
        
        # スペースを追加
        layout.addSpacing(10)
        
        # ボタンレイアウト
        button_layout = QHBoxLayout()
        
        # 新規登録ボタン（左）
        register_button = QPushButton('新規登録')
        register_button.clicked.connect(self.register)
        register_button.setFixedWidth(100)
        button_layout.addWidget(register_button)
        
        # スペーサーを追加（ログインボタンを右寄せ）
        button_layout.addStretch()
        
        # ログインボタン（右）
        login_button = QPushButton('ログイン')
        login_button.clicked.connect(self.login)
        login_button.setFixedWidth(120)
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        button_layout.addWidget(login_button)
        
        layout.addLayout(button_layout)
        
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
        
        # 初回ログインチェック
        if not self.has_aws_credentials():
            if not self.show_aws_credentials_dialog():
                return  # AWS認証情報の入力をキャンセルした場合
        
        # ログイン成功
        self.main_window = MainWindow(username)
        self.main_window.show()
        self.close()

    def has_aws_credentials(self):
        """AWS認証情報が設定されているかチェック"""
        access_key = self.credentials_manager.get_access_key()
        secret_key = self.credentials_manager.get_secret_key()
        return bool(access_key and secret_key)

    def show_aws_credentials_dialog(self):
        """AWS認証情報入力ダイアログを表示"""
        dialog = AWSCredentialsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            credentials = dialog.get_credentials()
            if not credentials['access_key'] or not credentials['secret_key']:
                QMessageBox.warning(self, "エラー", "AWS認証情報を入力してください。")
                return self.show_aws_credentials_dialog()
            
            try:
                self.credentials_manager.save_credentials(credentials)
                return True
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"AWS認証情報の保存に失敗しました: {e}")
                return False
        return False

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
        
        # AWS認証情報の入力を要求
        if not self.show_aws_credentials_dialog():
            return  # AWS認証情報の入力をキャンセルした場合
        
        users[username] = password
        self.save_users(users)
        
        QMessageBox.information(self, "成功", "ユーザー登録が完了しました。")
        self.username_input.clear()
        self.password_input.clear()

    def on_return_pressed(self):
        """エンターキーが押されたときの処理"""
        # ユーザー名とパスワードが両方入力されている場合のみログイン実行
        if self.username_input.text() and self.password_input.text():
            self.login()

    def toggle_password_visibility(self):
        """パスワードの表示/非表示を切り替え"""
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)