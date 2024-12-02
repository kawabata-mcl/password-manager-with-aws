#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
メインウィンドウ

パスワードマネージャーのメイン画面を提供します。
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QTableWidget, QTableWidgetItem,
                           QMessageBox, QMenu, QDialog, QLabel, QLineEdit,
                           QTextEdit)
from PyQt6.QtCore import Qt, QTimer, QEvent
import pyperclip
from ..utils.aws_manager import AWSManager
import configparser
from pathlib import Path

class PasswordDialog(QDialog):
    def __init__(self, parent=None, password_data=None):
        super().__init__(parent)
        self.setWindowTitle("パスワード情報" if password_data else "新規パスワード")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # ウェブサイト
        self.website_input = QLineEdit()
        self.website_input.setPlaceholderText("ウェブサイト")
        layout.addWidget(QLabel("ウェブサイト:"))
        layout.addWidget(self.website_input)
        
        # ユーザー名
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("ユーザー名")
        layout.addWidget(QLabel("ユーザー名:"))
        layout.addWidget(self.username_input)
        
        # パスワード
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("パスワード")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("パスワード:"))
        
        password_layout = QHBoxLayout()
        password_layout.addWidget(self.password_input)
        
        show_password_btn = QPushButton("表示")
        show_password_btn.clicked.connect(self.toggle_password_visibility)
        password_layout.addWidget(show_password_btn)
        
        layout.addLayout(password_layout)
        
        # メモ
        self.memo_input = QTextEdit()
        self.memo_input.setPlaceholderText("メモ")
        layout.addWidget(QLabel("メモ:"))
        layout.addWidget(self.memo_input)
        
        # ボタン
        button_layout = QHBoxLayout()
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("キャンセル")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 既存データがある場合は入力欄に設定
        if password_data:
            self.website_input.setText(password_data['website'])
            self.username_input.setText(password_data['username'])
            self.password_input.setText(password_data['password'])
            self.memo_input.setText(password_data.get('memo', ''))
            self.website_input.setReadOnly(True)

    def toggle_password_visibility(self):
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

    def get_data(self):
        return {
            'website': self.website_input.text(),
            'username': self.username_input.text(),
            'password': self.password_input.text(),
            'memo': self.memo_input.toPlainText()
        }

class MainWindow(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.setWindowTitle(f"パスワードマネージャー - {username}")
        self.setMinimumSize(800, 600)
        
        # AWS マネージャーの初期化
        config = configparser.ConfigParser()
        config.read(Path.home() / '.password_manager' / 'config.ini')
        self.aws_manager = AWSManager(config.get('AWS', 'region', fallback='ap-northeast-1'))
        
        # メインウィジェットとレイアウトの設定
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # ツールバー
        toolbar_layout = QHBoxLayout()
        
        add_button = QPushButton("新規追加")
        add_button.clicked.connect(self.add_password)
        toolbar_layout.addWidget(add_button)
        
        refresh_button = QPushButton("更新")
        refresh_button.clicked.connect(self.refresh_table)
        toolbar_layout.addWidget(refresh_button)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ウェブサイト", "ユーザー名", "パスワード", "メモ", "アクション"])
        self.table.setColumnWidth(0, 200)  # ウェブサイト
        self.table.setColumnWidth(1, 150)  # ユーザー名
        self.table.setColumnWidth(2, 150)  # パスワード
        self.table.setColumnWidth(3, 200)  # メモ
        self.table.setColumnWidth(4, 100)  # アクション
        layout.addWidget(self.table)
        
        # 自動ログアウトタイマーの設定
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self.auto_logout)
        self.reset_session_timer()
        
        # イベントフィルターの設定
        self.installEventFilter(self)
        
        # テーブルの初期化
        self.refresh_table()

    def reset_session_timer(self):
        """セッションタイマーをリセット"""
        config = configparser.ConfigParser()
        config.read(Path.home() / '.password_manager' / 'config.ini')
        timeout = config.getint('App', 'session_timeout', fallback=30)
        self.session_timer.start(timeout * 60 * 1000)  # 分をミリ秒に変換

    def auto_logout(self):
        """自動ログアウト処理"""
        QMessageBox.information(self, "セッション終了", "一定時間操作がなかったため、セッションを終了します。")
        self.close()

    def eventFilter(self, obj, event):
        """イベントフィルター"""
        if obj == self.table:
            if event.type() in [QEvent.Type.MouseButtonPress, QEvent.Type.KeyPress]:
                self.reset_clipboard_timer()
        return super().eventFilter(obj, event)

    def refresh_table(self):
        """テスワード一覧を更新"""
        try:
            passwords = self.aws_manager.get_passwords(self.username)
            
            # テーブルをクリア
            self.table.setRowCount(0)
            
            if not passwords:
                if self.aws_manager.ssm is None:
                    # 認証情報が設定されていない場合
                    self.show_credentials_warning()
                    return
                    
            # パスワード一覧を表示
            for i, password in enumerate(passwords):
                self.table.insertRow(i)
                self.table.setItem(i, 0, QTableWidgetItem(password.get('website', '')))
                self.table.setItem(i, 1, QTableWidgetItem(password.get('username', '')))
                self.table.setItem(i, 2, QTableWidgetItem('*' * 8))  # パスワードは表示しない
        except Exception as e:
            QMessageBox.warning(self, 'エラー', f'パスワード一覧の更新に失敗しました: {e}')

    def show_credentials_warning(self):
        """認証情報が設定されていない場合の警告を表示"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle('認証情報が必要です')
        msg.setText('AWS認証情報が設定されていません')
        msg.setInformativeText('AWSの認証情報を設定してください。設定画面を開きますか？')
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.show_settings_dialog()

    def show_settings_dialog(self):
        """設定画面を表示"""
        dialog = QDialog(self)
        dialog.setWindowTitle('AWS設定')
        dialog.setFixedSize(400, 200)
        
        layout = QVBoxLayout()
        
        # アクセスキー
        access_key_label = QLabel('AWSアクセスキー:')
        access_key_input = QLineEdit()
        access_key_input.setText(self.aws_manager.credentials_manager.get_access_key())
        layout.addWidget(access_key_label)
        layout.addWidget(access_key_input)
        
        # シークレットキー
        secret_key_label = QLabel('AWSシークレットキー:')
        secret_key_input = QLineEdit()
        secret_key_input.setText(self.aws_manager.credentials_manager.get_secret_key())
        secret_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(secret_key_label)
        layout.addWidget(secret_key_input)
        
        # ボタン
        button_layout = QHBoxLayout()
        save_button = QPushButton('保存')
        cancel_button = QPushButton('キャンセル')
        
        def save_credentials():
            self.aws_manager.update_credentials(
                access_key_input.text(),
                secret_key_input.text()
            )
            dialog.accept()
            self.refresh_table()
        
        save_button.clicked.connect(save_credentials)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec()

    def add_password(self):
        """新規パスワードの追加"""
        dialog = PasswordDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data['website'] or not data['username'] or not data['password']:
                QMessageBox.warning(self, "エラー", "ウェブサイト、ユーザー名、パスワードは必須です。")
                return
            
            if self.aws_manager.save_password(self.username, data):
                self.refresh_table()
            else:
                QMessageBox.warning(self, "エラー", "パスワードの保存に失敗しました。")

    def edit_password(self, password_data):
        """パスワードの編集"""
        dialog = PasswordDialog(self, password_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data['username'] or not data['password']:
                QMessageBox.warning(self, "エラー", "ユーザー名とパスワードは必須です。")
                return
            
            if self.aws_manager.save_password(self.username, data):
                self.refresh_table()
            else:
                QMessageBox.warning(self, "エラー", "パスワードの更新に失敗しました。")

    def delete_password(self, website):
        """パスワードの削除"""
        reply = QMessageBox.question(self, "確認", 
                                   f"'{website}' のパスワード情報を削除してもよろしいですか？",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.aws_manager.delete_password(self.username, website):
                self.refresh_table()
            else:
                QMessageBox.warning(self, "エラー", "パスワードの削除に失敗しました。") 