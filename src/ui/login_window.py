#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ログインウィンドウ

アプリケーションのログイン画面を提供します。

主な機能:
- ユーザー認証
- 新規ユーザー登録
- AWS認証情報の設定
- セキュリティ機能（ログイン試行回数制限など）
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

class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        """
        新規ユーザー登録ダイアログの初期化

        Args:
            parent (QWidget, optional): 親ウィジェット

        Attributes:
            username_input (QLineEdit): ユーザー名入力フィールド
            password_input (QLineEdit): パスワード入力フィールド
            password_confirm_input (QLineEdit): パスワード確認入力フィールド
            access_key_input (QLineEdit): AWSアクセスキー入力フィールド
            secret_key_input (QLineEdit): AWSシークレットキー入力フィールド
        """
        super().__init__(parent)
        self.setWindowTitle('新規ユーザー登録')
        self.setFixedSize(400, 350)
        
        layout = QVBoxLayout()
        
        # ユーザー名
        username_label = QLabel('ユーザー名:')
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('ユーザー名を入力')
        layout.addWidget(username_label)
        layout.addWidget(self.username_input)
        
        # パスワード
        password_label = QLabel('パスワード:')
        layout.addWidget(password_label)
        
        password_layout = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('パスワードを入力')
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(self.password_input)
        
        show_password_btn = QPushButton("表示")
        show_password_btn.setFixedWidth(60)
        show_password_btn.clicked.connect(lambda: self.toggle_password_visibility(self.password_input))
        password_layout.addWidget(show_password_btn)
        layout.addLayout(password_layout)
        
        # パスワード確認
        password_confirm_label = QLabel('パスワード（確認）:')
        layout.addWidget(password_confirm_label)
        
        password_confirm_layout = QHBoxLayout()
        self.password_confirm_input = QLineEdit()
        self.password_confirm_input.setPlaceholderText('パスワードを再入力')
        self.password_confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_confirm_layout.addWidget(self.password_confirm_input)
        
        show_password_confirm_btn = QPushButton("表示")
        show_password_confirm_btn.setFixedWidth(60)
        show_password_confirm_btn.clicked.connect(lambda: self.toggle_password_visibility(self.password_confirm_input))
        password_confirm_layout.addWidget(show_password_confirm_btn)
        layout.addLayout(password_confirm_layout)
        
        # AWSアクセスキー
        access_key_label = QLabel('AWSアクセスキー:')
        self.access_key_input = QLineEdit()
        self.access_key_input.setPlaceholderText('AWSアクセスキーを入力')
        layout.addWidget(access_key_label)
        layout.addWidget(self.access_key_input)
        
        # AWSシークレットキー
        secret_key_label = QLabel('AWSシークレットキー:')
        layout.addWidget(secret_key_label)
        
        secret_key_layout = QHBoxLayout()
        self.secret_key_input = QLineEdit()
        self.secret_key_input.setPlaceholderText('AWSシークレットキーを入力')
        self.secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        secret_key_layout.addWidget(self.secret_key_input)
        
        show_secret_key_btn = QPushButton("表示")
        show_secret_key_btn.setFixedWidth(60)
        show_secret_key_btn.clicked.connect(lambda: self.toggle_password_visibility(self.secret_key_input))
        secret_key_layout.addWidget(show_secret_key_btn)
        layout.addLayout(secret_key_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        register_button = QPushButton('登録')
        register_button.clicked.connect(self.validate_and_accept)
        cancel_button = QPushButton('キャンセル')
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(register_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def toggle_password_visibility(self, input_field: QLineEdit):
        """
        パスワードの表示/非表示を切り替え

        Args:
            input_field (QLineEdit): 表示/非表示を切り替える入力フィールド
        """
        if input_field.echoMode() == QLineEdit.EchoMode.Password:
            input_field.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            input_field.setEchoMode(QLineEdit.EchoMode.Password)

    def validate_and_accept(self):
        """
        入力内容を検証して登録を実行

        以下の条件をチェックします：
        - すべての必須フィールドが入力されていること
        - パスワードと確認用パスワードが一致すること
        - ユーザー名が有効な文字のみを含むこと
        """
        username = self.username_input.text()
        password = self.password_input.text()
        password_confirm = self.password_confirm_input.text()
        access_key = self.access_key_input.text()
        secret_key = self.secret_key_input.text()
        
        # 必須フィールドのチェック
        if not all([username, password, password_confirm, access_key, secret_key]):
            QMessageBox.warning(self, "エラー", "すべての項目を入力してください。")
            return
        
        # パスワード一致チェック
        if password != password_confirm:
            QMessageBox.warning(self, "エラー", "パスワードが一致しません。")
            return
        
        # ユーザー名の文字チェック
        if not all(c.isalnum() or c in '_-' for c in username):
            QMessageBox.warning(self, "エラー", 
                              "ユーザー名には英数字とアンダースコア、ハイフンのみ使用できます。")
            return
        
        self.accept()

    def get_registration_data(self):
        """
        登録情報を取得

        Returns:
            dict: 登録情報を含む辞書
                {
                    'username': str,
                    'password': str,
                    'aws_access_key': str,
                    'aws_secret_key': str
                }
        """
        return {
            'username': self.username_input.text(),
            'password': self.password_input.text(),
            'aws_access_key': self.access_key_input.text(),
            'aws_secret_key': self.secret_key_input.text()
        }

class AWSCredentialsDialog(QDialog):
    def __init__(self, parent=None):
        """
        AWS認証情報入力ダイアログの初期化

        Args:
            parent (QWidget, optional): 親ウィジェット

        Attributes:
            access_key_input (QLineEdit): アクセスキー入力フィールド
            secret_key_input (QLineEdit): シークレットキー入力フィールド
        """
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
        """
        入力された認証情報を取得

        Returns:
            dict: AWS認証情報を含む辞書
                {
                    'access_key': str,
                    'secret_key': str
                }
        """
        return {
            'access_key': self.access_key_input.text(),
            'secret_key': self.secret_key_input.text()
        }

class LoginWindow(QMainWindow):
    def __init__(self):
        """
        ログインウィンドウの初期化

        Attributes:
            credentials_manager (CredentialsManager): AWS認証情報管理オブジェクト
            username_input (QLineEdit): ユーザー名入力フィールド
            password_input (QLineEdit): パスワード入力フィールド
            login_attempts (int): ログイン試行回数
            max_attempts (int): 最大ログイン試行回数
            cipher_suite (Fernet): 暗号化/復号化オブジェクト
        """
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
        register_button.clicked.connect(self.show_register_dialog)
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
        """
        暗号化の初期設定

        ユーザー情報の暗号化に使用する鍵の生成または読み込みを行います。

        Note:
            - 鍵ファイルが存在しない場合は新規に生成されます
            - 鍵は~/.password_manager/key.keyに保存されます
        """
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
        """
        ユーザーデータファイルのパスを取得

        Returns:
            Path: ユーザーデータファイルのパス（~/.password_manager/users.dat）
        """
        return Path.home() / '.password_manager' / 'users.dat'

    def load_users(self):
        """
        保存されているユーザー情報を読み込む

        Returns:
            dict: ユーザー名とパスワードのマッピング
                {username: password}

        Note:
            - ファイルが存在しない場合は空の辞書を返します
            - 復号化に失敗した場合は空の辞書を返します
        """
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
        """
        ユーザー情報を保存

        Args:
            users (dict): ユーザー名とパスワードのマッピング
                {username: password}

        Note:
            - データは暗号化されて保存されます
            - 既存のデータは上書きされます
        """
        encrypted_data = self.cipher_suite.encrypt(json.dumps(users).encode())
        with open(self.get_user_data_path(), 'wb') as f:
            f.write(encrypted_data)

    def login(self):
        """
        ログイン処理を実行

        ユーザー名とパスワードを検証し、正しい場合はメインウィンドウを表示します。

        Note:
            - ログイン試行回数が上限に達した場合、アプリケーションは終了します
        """
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "エラー", "ユーザー名とパスワードを入力してください。")
            return
        
        users = self.load_users()
        
        # ログイン試行回数のチェック
        if self.login_attempts >= self.max_attempts:
            QMessageBox.critical(self, "エラー", "ログイン試行回数が上限に達しました。\nアプリケーションを終了します。")
            self.close()
            return

        # ユーザーの存在チェック
        if username not in users:
            self.login_attempts += 1
            remaining = self.max_attempts - self.login_attempts
            QMessageBox.warning(
                self,
                "エラー",
                f"ユーザー '{username}' は登録されていません。\n"
                "新規登録ボタンから登録してください。\n"
                f"残り試行回数: {remaining}"
            )
            return
        
        # パスワードの検証
        if users[username] != password:
            self.login_attempts += 1
            remaining = self.max_attempts - self.login_attempts
            QMessageBox.warning(
                self,
                "エラー",
                "パスワードが正しくありません。\n"
                f"残り試行回数: {remaining}"
            )
            return
        
        # ログイン成功
        self.main_window = MainWindow(username)
        self.main_window.show()
        self.close()

    def has_aws_credentials(self):
        """
        AWS認証情報が設定されているかチェック

        Returns:
            bool: 認証情報が設定されている場合はTrue、それ以外はFalse
        """
        access_key = self.credentials_manager.get_access_key()
        secret_key = self.credentials_manager.get_secret_key()
        return bool(access_key and secret_key)

    def show_aws_credentials_dialog(self):
        """
        AWS認証情報入力ダイアログを表示

        Returns:
            bool: 認証情報の設定に成功した場合はTrue、それ以外はFalse

        Note:
            - キャンセルした場合はFalseを返します
            - 認証情報が不完全な場合は再度ダイアログを表示します
        """
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

    def show_register_dialog(self):
        """
        新規ユーザー登録ダイアログを表示

        新規ユーザーの登録処理を行います。
        登録が成功した場合、AWS認証情報も同時に保存されます。
        """
        dialog = RegisterDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_registration_data()
            
            try:
                # ユーザーの存在チェック
                users = self.load_users()
                if data['username'] in users:
                    QMessageBox.warning(self, "エラー", "このユーザー名は既に使用されています。")
                    return
                
                # AWS認証情報の保存
                credentials_manager = CredentialsManager()
                credentials = {
                    'access_key': data['aws_access_key'],
                    'secret_key': data['aws_secret_key'],
                    'username': data['username']
                }
                try:
                    credentials_manager.save_credentials(credentials)
                except Exception as e:
                    QMessageBox.warning(self, "エラー", "AWS認証情報の保存に失敗しました。")
                    print(f"AWS認証情報保存エラー: {str(e)}")
                    return
                
                # ユーザー情報の保存
                users[data['username']] = data['password']
                self.save_users(users)
                
                # 完了通知
                QMessageBox.information(
                    self,
                    "登録完了",
                    f"ユーザー '{data['username']}' の登録が完了しました。\n"
                    "このアカウントでログインできます。"
                )
                
                # 入力フィールドをクリア
                self.username_input.clear()
                self.password_input.clear()
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "エラー",
                    f"アカウント作成中にエラーが発生しました。\n"
                    f"エラー内容: {str(e)}"
                )

    def on_return_pressed(self):
        """
        Enterキー押下時の処理

        パスワード入力欄でEnterキーが押された場合、ログイン処理を実行します。
        """
        # ユーザー名とパスワードが両方入力されている場合のみログイン実行
        if self.username_input.text() and self.password_input.text():
            self.login()

    def toggle_password_visibility(self):
        """
        パスワードの表示/非表示を切り替え

        パスワード入力欄のエコーモードを切り替えます。
        """
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)