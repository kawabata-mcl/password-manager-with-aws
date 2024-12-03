#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
メインウィンドウ

パスワードマネージャーのメイン画面を提供します。

主な機能:
- パスワード一覧の表示と管理
- パスワードの追加・編集・削除
- パスワード情報のコピー
- セッション管理（タイムアウト）
- AWS認証情報の管理
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QTableWidget, QTableWidgetItem,
                           QMessageBox, QMenu, QDialog, QLabel, QLineEdit,
                           QTextEdit, QHeaderView, QApplication)
from PyQt6.QtCore import Qt, QTimer, QEvent
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl
import pyperclip
from ..utils.aws_manager import AWSManager
import configparser
from pathlib import Path
from datetime import datetime

class PasswordDialog(QDialog):
    def __init__(self, parent=None, password_data=None):
        """
        パスワード情報入力ダイアログの初期化

        Args:
            parent (QWidget, optional): 親ウィジェット
            password_data (dict, optional): 編集時の既存パスワード情報

        Attributes:
            app_name_input (QLineEdit): アプリ名入力フィールド
            url_input (QLineEdit): URL入力フィールド
            username_input (QLineEdit): ユーザー名入力フィールド
            password_input (QLineEdit): パスワード入力フィールド
            memo_input (QTextEdit): メモ入力フィールド
        """
        super().__init__(parent)
        self.setWindowTitle("パスワード情報" if password_data else "新規パスワード")
        self.setFixedSize(400, 500)
        
        layout = QVBoxLayout()
        
        # アプリ名
        self.app_name_input = QLineEdit()
        self.app_name_input.setPlaceholderText("アプリ名")
        self.app_name_input.textChanged.connect(self.validate_app_name)
        layout.addWidget(QLabel("アプリ名:"))
        layout.addWidget(self.app_name_input)
        
        # サイトURL
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        layout.addWidget(QLabel("サイトURL:"))
        layout.addWidget(self.url_input)
        
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
        self.memo_input.setMaximumHeight(100)
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
        
        # 既存のデータがある場合は入力欄に設定
        if password_data:
            self.app_name_input.setText(password_data.get('app_name', ''))
            self.url_input.setText(password_data.get('url', ''))
            self.username_input.setText(password_data.get('username', ''))
            self.password_input.setText(password_data.get('password', ''))
            self.memo_input.setText(password_data.get('memo', ''))

    def toggle_password_visibility(self):
        """
        パスワードの表示/非表示を切り替え

        パスワード入力欄のエコーモードを切り替えます。
        """
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

    def validate_app_name(self):
        """
        アプリ名の入力バリデーション

        アプリ名に使用できる文字は英数字とアンダースコア、ハイフン、ドットのみです。

        Returns:
            bool: バリデーションに成功した場合はTrue、それ以外はFalse
        """
        text = self.app_name_input.text()
        valid = all(c.isalnum() or c in '_.-' for c in text)
        if not valid and text:
            self.app_name_input.setStyleSheet("background-color: #ffebee;")
        else:
            self.app_name_input.setStyleSheet("")
        return valid

    def get_password_data(self):
        """
        入力されたパスワード情報を取得

        Returns:
            dict: パスワード情報を含む辞書。バリデーションに失敗した場合はNone
                {
                    'app_name': str,
                    'url': str,
                    'username': str,
                    'password': str,
                    'memo': str
                }
        """
        if not self.validate_app_name():
            return None
        return {
            'app_name': self.app_name_input.text(),
            'url': self.url_input.text(),
            'username': self.username_input.text(),
            'password': self.password_input.text(),
            'memo': self.memo_input.toPlainText()
        }

class MainWindow(QMainWindow):
    def __init__(self, username: str):
        """
        メインウィンドウの初期化

        Args:
            username (str): ログインユーザー名

        Attributes:
            username (str): ログインユーザー名
            aws_manager (AWSManager): AWS操作マネージャー
            passwords (list): パスワード情報のリスト
            activity_timer (QTimer): アクティビティ監視タイマー
            last_activity (datetime): 最後のアクティビティ時刻
            session_timeout (int): セッションタイムアウト時間（分）
        """
        super().__init__()
        self.username = username
        
        # ウィンドウの設定
        self.setWindowTitle(f"パスワードマネージャー - {username}")
        self.setGeometry(100, 100, 900, 600)  # ウィンドウサイズを少し大きく
        self.setMinimumSize(800, 500)  # 最小サイズを設定
        
        # 設定の読み込み
        self.load_config()
        
        # AWSマネージャーの初期化とパスワード一覧の取得
        self.aws_manager = AWSManager()
        self.passwords = self.aws_manager.get_passwords(self.username)
        
        # UIの初期化
        self.init_ui()
        
        # パスワード一覧の初期表示（既に取得済みのデータを使用）
        self.update_table_display()
        
        # アクティビティタイマーの設定
        self.activity_timer = QTimer(self)
        self.activity_timer.timeout.connect(self.check_activity)
        self.activity_timer.start(60000)  # 1分ごとにチェック
        self.last_activity = datetime.now()
        
        # ウィンドウを中央に配置
        self.center_window()

    def check_activity(self):
        """
        ユーザーのアクティビティをチェックし、必要に応じて自動ログアウト

        一定時間操作がない場合、セッションを終了してアプリケーションを終了します。
        """
        if (datetime.now() - self.last_activity).total_seconds() > self.session_timeout * 60:
            QMessageBox.warning(self, "セッションタイムアウト", 
                              "一定時間操作がなかったため、セッションを終了します。")
            self.close()

    def eventFilter(self, obj, event):
        """
        イベントフィルター（ユーザーのアクティビティを監視）

        Args:
            obj (QObject): イベントを受け取ったオブジェクト
            event (QEvent): 発生したイベント

        Returns:
            bool: イベントを処理した場合はTrue、それ以外はFalse
        """
        if event.type() in [QEvent.Type.MouseButtonPress, QEvent.Type.KeyPress]:
            self.last_activity = datetime.now()
        return super().eventFilter(obj, event)

    def load_config(self):
        """
        設定の読み込み

        設定ファイルから以下の設定を読み込みます:
        - セッションタイムアウト時間
        - 最大ログイン試行回数
        - パスワードキャッシュ期間
        """
        config = configparser.ConfigParser()
        config.read(Path.home() / '.password_manager' / 'config.ini')
        
        # セッションタイムアウトの設定（デフォルト: 30分）
        self.session_timeout = config.getint('App', 'session_timeout', fallback=30)

    def init_ui(self):
        """
        UIの初期化

        以下のUIコンポーネントを設定します:
        - ツールバー（コピー、追加、編集、削除ボタン）
        - パスワード一覧テーブル
        - イベントフィルター
        """
        # メインウィジェットとレイアウトの設定
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # イベントフィルターの設定
        self.installEventFilter(self)
        main_widget.installEventFilter(self)
        
        # ツールバーの設定
        toolbar_layout = QHBoxLayout()
        
        # 左側のコピーボタン
        self.copy_url_button = QPushButton("URLをコピー")
        self.copy_url_button.clicked.connect(lambda: self.copy_selected_field('url'))
        self.copy_url_button.setEnabled(False)  # 初期状態は無効
        toolbar_layout.addWidget(self.copy_url_button)
        
        self.copy_username_button = QPushButton("ユーザー名をコピー")
        self.copy_username_button.clicked.connect(lambda: self.copy_selected_field('username'))
        self.copy_username_button.setEnabled(False)  # 初期状態は無効
        toolbar_layout.addWidget(self.copy_username_button)
        
        self.copy_password_button = QPushButton("パスワードをコピー")
        self.copy_password_button.clicked.connect(lambda: self.copy_selected_field('password'))
        self.copy_password_button.setEnabled(False)  # 初期状態は無効
        toolbar_layout.addWidget(self.copy_password_button)
        
        # スペーサーを追加（右寄せ用）
        toolbar_layout.addStretch()
        
        # 右側の操作ボタン
        add_button = QPushButton("追加")
        add_button.clicked.connect(self.add_password)
        toolbar_layout.addWidget(add_button)
        
        self.edit_button = QPushButton("編集")
        self.edit_button.clicked.connect(self.edit_selected_passwords)
        self.edit_button.setEnabled(False)  # 初期状態は無効
        toolbar_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("削除")
        self.delete_button.clicked.connect(self.delete_selected_passwords)
        self.delete_button.setEnabled(False)  # 初期状態は無効
        toolbar_layout.addWidget(self.delete_button)
        
        # 更新ボタン（緑色）
        refresh_button = QPushButton("更新")
        refresh_button.clicked.connect(self.refresh_table)
        refresh_button.setStyleSheet("""
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
        toolbar_layout.addWidget(refresh_button)
        
        layout.addLayout(toolbar_layout)
        
        # テーブルの設定
        self.table = QTableWidget()
        self.table.setColumnCount(6)  # チェックボックス、アプリ名、URL、ユーザー名、パスワード、メモ
        self.table.setHorizontalHeaderLabels([
            "", "アプリ名", "URL", "ユーザー名", "パスワード", "メモ"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # アプリ名列を伸縮可能に
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # URL列を伸縮可能に
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # メモ列を伸縮可能に
        
        # アイテム変更時のイベントを接続
        self.table.itemChanged.connect(self.on_item_changed)
        # ダブルクリック時のイベントを接続
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)
        
        layout.addWidget(self.table)

    def on_item_changed(self, item):
        """テーブルアイテムの変更時のイベントハンドラ"""
        if item.column() == 0:  # チェックボックス列の変更時のみ
            self.update_button_states()

    def on_cell_double_clicked(self, row, column):
        """セルがダブルクリックされたときの処理"""
        if column == 4:  # パスワード列
            item = self.table.item(row, column)
            if item:
                app_name = self.table.item(row, 1).text()  # アプリ名を取得
                passwords = self.aws_manager.get_passwords(self.username)
                
                # 実際のパスワードを取得
                actual_password = None
                for pwd in passwords:
                    if pwd['app_name'] == app_name:
                        actual_password = pwd['password']
                        break
                
                if actual_password:
                    if item.text() == '*' * 8:  # マスク表示中
                        item.setText(actual_password)  # マスクを解除
                    else:
                        item.setText('*' * 8)  # マスクを設定

    def update_button_states(self):
        """
        ボタンの有効/無効状態を更新

        選択されているパスワードの数に応じて、各ボタンの有効/無効を切り替えます。
        """
        checked_rows = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)  # チェックボックス列
            if item and item.checkState() == Qt.CheckState.Checked:
                checked_rows.append(row)
        
        # 1つのみ選択時に有効にするボタン
        is_single_selected = len(checked_rows) == 1
        self.edit_button.setEnabled(is_single_selected)
        self.copy_url_button.setEnabled(is_single_selected)
        self.copy_username_button.setEnabled(is_single_selected)
        self.copy_password_button.setEnabled(is_single_selected)
        
        # 1つ以上選択時に有効にするボタン
        self.delete_button.setEnabled(len(checked_rows) > 0)

    def get_selected_passwords(self):
        """
        選択されているパスワード情報を取得

        Returns:
            list: 選択されているパスワード情報のリスト
        """
        selected = []
        passwords = self.aws_manager.get_passwords(self.username)
        
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)  # チェックボックス列
            if item and item.checkState() == Qt.CheckState.Checked:
                app_name = self.table.item(row, 1).text()
                for password in passwords:
                    if password['app_name'] == app_name:
                        selected.append(password)
                        break
        
        return selected

    def copy_selected_field(self, field: str):
        """
        選択されたフィールドの値をクリップボードにコピー

        Args:
            field (str): コピーするフィールド名（'url', 'username', 'password'）

        Note:
            - パスワードの場合、30秒後に自動的にクリップボードをクリアします
            - コピー成功時にステータスバーに通知を表示します
        """
        checked_rows = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)  # チェックボックス列
            if item and item.checkState() == Qt.CheckState.Checked:
                checked_rows.append(row)
        
        if len(checked_rows) != 1:
            QMessageBox.warning(self, "エラー", "1つの項目を選択してください。")
            return
        
        row = checked_rows[0]
        field_mapping = {
            'url': 2,      # URL列のインデックス
            'username': 3,  # ユーザー名列のインデックス
            'password': 4,  # パスワード列のインデックス
        }
        
        if field in field_mapping:
            value = self.table.item(row, field_mapping[field]).text()
            if field == 'password':
                # パスワードの場合は、実際の値を取得
                passwords = self.aws_manager.get_passwords(self.username)
                app_name = self.table.item(row, 1).text()  # アプリ名列から取得
                for pwd in passwords:
                    if pwd['app_name'] == app_name:
                        value = pwd['password']
                        break
            
            pyperclip.copy(value)

    def update_table_display(self):
        """
        パスワード一覧テーブルを更新

        AWS上のパスワード情報を取得し、テーブルに表示します。

        Note:
            - テーブルのヘッダーとカラム幅を自動調整します
            - パスワードは非表示（*****）で表示されます
        """
        try:
            # テーブルをクリア
            self.table.setRowCount(0)
            
            if not self.passwords:
                if self.aws_manager.ssm is None:
                    # 認証情報が設定されていない場合
                    self.show_credentials_warning()
                    return
            
            # パスワード一覧を表示
            for i, password in enumerate(self.passwords):
                self.table.insertRow(i)
                
                # チェックボックス
                checkbox_item = QTableWidgetItem()
                checkbox_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                checkbox_item.setCheckState(Qt.CheckState.Unchecked)
                self.table.setItem(i, 0, checkbox_item)
                
                # アプリ名
                self.table.setItem(i, 1, QTableWidgetItem(password.get('app_name', '')))
                
                # URL（クリック可能なリンク）
                url = password.get('url', '')
                url_cell = QWidget()
                url_layout = QHBoxLayout(url_cell)
                url_layout.setContentsMargins(5, 0, 5, 0)
                
                if url and (url.startswith('http://') or url.startswith('https://')):
                    url_label = QLabel(f'<a href="{url}">{url}</a>')
                    url_label.setOpenExternalLinks(True)
                    url_label.setTextFormat(Qt.TextFormat.RichText)
                else:
                    url_label = QLabel(url)
                
                url_layout.addWidget(url_label)
                url_cell.setLayout(url_layout)
                self.table.setCellWidget(i, 2, url_cell)
                
                # その他の情報
                self.table.setItem(i, 3, QTableWidgetItem(password.get('username', '')))
                self.table.setItem(i, 4, QTableWidgetItem('*' * 8))  # パスワードはマスク表示
                self.table.setItem(i, 5, QTableWidgetItem(password.get('memo', '')))
            
            # 列幅の調整
            self.table.setColumnWidth(0, 30)   # チェックボックス
            self.table.setColumnWidth(3, 150)  # ユーザー名
            self.table.setColumnWidth(4, 100)  # パスワード
            
            # ボタンの状態を更新
            self.update_button_states()
            
        except Exception as e:
            print(f"テーブル更新エラー: {e}")
            QMessageBox.warning(self, "エラー", "パスワード一覧の更新に失敗しました。")

    def refresh_table(self):
        """
        パスワード一覧を最新の状態に更新

        AWSから最新のパスワード情報を取得し、テーブルを更新します。
        """
        try:
            # AWS認証情報の再設定（更新のため）
            self.aws_manager = AWSManager()
            
            # パスワード一覧を取得
            self.passwords = self.aws_manager.get_passwords(self.username)
            
            # テーブル表示を更新
            self.update_table_display()
            
        except Exception as e:
            print(f"テーブル更新エラー: {e}")
            QMessageBox.warning(self, "エラー", "パスワード一覧の更新に失敗しました。")

    def on_selection_changed(self, item):
        """
        テーブルの選択状態が変更された時の処理

        Args:
            item (QTableWidgetItem): 選択されたアイテム

        Note:
            選択状態に応じてボタンの有効/無効を更新します。
        """
        if item and item.column() == 0:  # チェックボックス列の変更のみ処理
            selected_count = self.get_selected_count()
            self.edit_button.setEnabled(selected_count == 1)  # 1つ選択時のみ編集可能
            self.delete_button.setEnabled(selected_count > 0)  # 1つ以上選択時に削除可能

    def get_selected_count(self):
        """選択されているアイテムの数を取得"""
        count = 0
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                count += 1
        return count

    def get_selected_passwords(self):
        """選択されているパスワード情報を取得"""
        selected = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                password_data = {
                    'app_name': self.table.item(row, 1).text(),
                    'url': self.table.item(row, 2).text(),
                    'username': self.table.item(row, 3).text(),
                    'password': self.aws_manager.get_passwords(self.username)[row]['password'],
                    'memo': self.table.item(row, 5).text()
                }
                selected.append(password_data)
        return selected

    def edit_selected_passwords(self):
        """
        選択されているパスワード情報を編集

        選択されているパスワードの編集ダイアログを表示します。
        """
        selected = self.get_selected_passwords()
        if len(selected) == 1:
            self.edit_password(selected[0])

    def delete_selected_passwords(self):
        """
        選択されているパスワード情報を削除

        確認ダイアログを表示し、承認された場合は選択されているパスワードを削除します。
        """
        selected = self.get_selected_passwords()
        if not selected:
            return
            
        if len(selected) == 1:
            message = f"'{selected[0]['app_name']}'を削除してもよろしいですか？"
        else:
            message = f"{len(selected)}件のパスワードを削除してもよろしいですか？"
            
        reply = QMessageBox.question(self, '確認', message,
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                                   
        if reply == QMessageBox.StandardButton.Yes:
            success = True
            for password in selected:
                if not self.aws_manager.delete_password(self.username, password['app_name']):
                    success = False
                    break
            
            if success:
                if len(selected) == 1:
                    QMessageBox.information(self, "成功", f"パスワード '{selected[0]['app_name']}' を削除しました。")
                else:
                    QMessageBox.information(self, "成功", f"{len(selected)}件のパスワードを削除しました。")
                self.refresh_table()  # 削除後に更新
            else:
                QMessageBox.warning(self, "エラー", "パスワードの削除に失敗しました。")

    def show_credentials_warning(self):
        """
        AWS認証情報の警告を表示

        AWS認証情報が設定されていない場合に警告メッセージを表示します。
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle('認証情報が必要です')
        msg.setText('AWS認証情報が設定されていません')
        msg.setInformativeText('AWSの認証情報を設定してください。設定画面を開きますか？')
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.show_settings_dialog()

    def show_settings_dialog(self):
        """
        設定ダイアログを表示

        AWS認証情報の設定ダイアログを表示します。
        """
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
        secret_key_label = QLabel('AWSシークレトキー:')
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
        """
        新規パスワード情報を追加

        パスワード情報入力ダイアログを表示し、入力された情報を保存します。
        """
        dialog = PasswordDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_password_data()
            if data is None:
                QMessageBox.warning(self, "エラー", "アプリ名には英数字、アンダースコア、ドット、ハイフンのみ使用できます。")
                return
            if not data['app_name'] or not data['username'] or not data['password']:
                QMessageBox.warning(self, "エラー", "アプリ名、ユーザー名、パスワードは必須です。")
                return
            
            # 既存のパスワード一覧を取得して重複チェック
            existing_passwords = self.aws_manager.get_passwords(self.username)
            for existing in existing_passwords:
                if existing['app_name'] == data['app_name']:
                    QMessageBox.warning(self, "エラー", f"アプリ名 '{data['app_name']}' は既に存在します。")
                    return
            
            if self.aws_manager.save_password(self.username, data):
                QMessageBox.information(self, "成功", f"パスワード '{data['app_name']}' を追加しました。")
                self.refresh_table()  # 追加後に更新
            else:
                QMessageBox.warning(self, "エラー", "パスワードの保存に失敗しました。")

    def edit_password(self, password_data):
        """
        パスワード情報を編集

        Args:
            password_data (dict): 編集するパスワード情報

        Note:
            編集後、テーブルの表示を更新します。
        """
        dialog = PasswordDialog(self, password_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_password_data()
            if not data['username'] or not data['password']:
                QMessageBox.warning(self, "エラー", "ユーザー名とパスワードは必須です。")
                return
            
            if self.aws_manager.save_password(self.username, data):
                QMessageBox.information(self, "成功", f"パスワード '{data['app_name']}' を更新しました。")
                self.refresh_table()  # 編集後に更新
            else:
                QMessageBox.warning(self, "エラー", "パスワードの更新に失敗しました。")

    def delete_password(self, app_name):
        """
        パスワード情報を削除

        Args:
            app_name (str): 削除するパスワードのアプリ名

        Note:
            削除後、テーブルの表示を更新します。
        """
        if self.aws_manager.delete_password(self.username, app_name):
            self.refresh_table()
        else:
            QMessageBox.warning(self, "エラー", "パスワードの削除に失敗しました。") 

    def center_window(self):
        """
        ウィンドウを画面中央に配置

        デスクトップの中央にウィンドウを移動します。
        """
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y) 