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
from PyQt6.QtCore import Qt, QTimer
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
        """イベントフィルター（ユーザーアクションの検出）"""
        if event.type() in [Qt.EventType.MouseButtonPress, Qt.EventType.KeyPress]:
            self.reset_session_timer()
        return super().eventFilter(obj, event)

    def refresh_table(self):
        """テーブルの内容を更新"""
        passwords = self.aws_manager.get_passwords(self.username)
        self.table.setRowCount(len(passwords))
        
        for row, data in enumerate(passwords):
            # ウェブサイト
            website_item = QTableWidgetItem(data['website'])
            website_item.setFlags(website_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, website_item)
            
            # ユーザー名
            username_item = QTableWidgetItem(data['username'])
            username_item.setFlags(username_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, username_item)
            
            # パスワード（マスク表示）
            password_item = QTableWidgetItem("*" * 8)
            password_item.setFlags(password_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, password_item)
            
            # メモ
            memo_item = QTableWidgetItem(data.get('memo', ''))
            memo_item.setFlags(memo_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, memo_item)
            
            # アクションボタンのセル
            action_widget = QWidget()
            action_layout = QHBoxLayout()
            action_layout.setContentsMargins(0, 0, 0, 0)
            
            # コピーボタン（ドロップダウンメニュー付き）
            copy_button = QPushButton("コピー")
            copy_menu = QMenu(copy_button)
            
            copy_username_action = copy_menu.addAction("ユーザー名をコピー")
            copy_username_action.triggered.connect(lambda checked, u=data['username']: pyperclip.copy(u))
            
            copy_password_action = copy_menu.addAction("パスワードをコピー")
            copy_password_action.triggered.connect(lambda checked, p=data['password']: pyperclip.copy(p))
            
            copy_website_action = copy_menu.addAction("ウェブサイトをコピー")
            copy_website_action.triggered.connect(lambda checked, w=data['website']: pyperclip.copy(w))
            
            copy_button.setMenu(copy_menu)
            action_layout.addWidget(copy_button)
            
            # 編集ボタン
            edit_button = QPushButton("編集")
            edit_button.clicked.connect(lambda checked, d=data: self.edit_password(d))
            action_layout.addWidget(edit_button)
            
            # 削除ボタン
            delete_button = QPushButton("削除")
            delete_button.clicked.connect(lambda checked, w=data['website']: self.delete_password(w))
            action_layout.addWidget(delete_button)
            
            action_widget.setLayout(action_layout)
            self.table.setCellWidget(row, 4, action_widget)

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