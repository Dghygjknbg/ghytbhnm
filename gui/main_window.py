import sys
import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QMessageBox, QStackedWidget,
    QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QTextCursor, QFont, QPixmap

class SidebarButton(QPushButton):
    def __init__(self, text, icon_path=None):
        super().__init__(text)
        self.setFixedHeight(40)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        if icon_path:
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(20, 20))
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px 15px;
                border: none;
                border-radius: 5px;
                color: #ffffff;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: #2c3e50;
            }
            QPushButton:checked {
                background-color: #3498db;
            }
        """)

class MainWindow(QMainWindow):
    """Главное окно приложения"""
    def __init__(self, worker):
        super().__init__()
        self.worker = worker
        self.initUI()
        self.connectSignals()
        self.loadConfig()

    def initUI(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("X_Patch Automat")
        screen = QApplication.primaryScreen().availableGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        window_width = screen_width // 2
        window_height = screen_height // 2
        self.setGeometry(0, 0, window_width, window_height)
        self.setWindowIcon(QIcon("logo.svg"))

        # Создаем главный виджет и layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Создаем боковую панель
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-right: 1px solid #2c2c2c;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(15)

        # Логотип
        logo_label = QLabel()
        logo_pixmap = QPixmap("logo.svg")
        logo_label.setPixmap(logo_pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(logo_label)

        # Название приложения
        title_label = QLabel("X_Patch Automat")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 20px;
            }
        """)
        sidebar_layout.addWidget(title_label)

        # Кнопки меню
        self.dashboard_btn = SidebarButton("Dashboard")
        self.settings_btn = SidebarButton("Site Settings")
        
        sidebar_layout.addWidget(self.dashboard_btn)
        sidebar_layout.addWidget(self.settings_btn)
        sidebar_layout.addStretch()

        # Создаем контейнер для контента с отступами
        content_container = QWidget()
        content_container.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
            }
        """)
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # Создаем стек виджетов для страниц
        self.stacked_widget = QStackedWidget()
        
        # Страница Dashboard
        dashboard_page = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_page)
        dashboard_layout.setContentsMargins(0, 0, 0, 0)
        dashboard_label = QLabel("Dashboard (В разработке)")
        dashboard_label.setStyleSheet("font-size: 24px; color: #333;")
        dashboard_layout.addWidget(dashboard_label)
        
        # Страница настроек
        settings_page = QWidget()
        settings_layout = QVBoxLayout(settings_page)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        
        # Элементы управления для настроек
        self.username_label = QLabel("Логин:")
        self.username_input = QLineEdit()
        self.password_label = QLabel("Пароль:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.start_btn = QPushButton("Старт")
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        
        settings_layout.addWidget(self.username_label)
        settings_layout.addWidget(self.username_input)
        settings_layout.addWidget(self.password_label)
        settings_layout.addWidget(self.password_input)
        settings_layout.addWidget(self.start_btn)
        settings_layout.addWidget(self.logs)

        # Добавляем страницы в стек
        self.stacked_widget.addWidget(dashboard_page)
        self.stacked_widget.addWidget(settings_page)

        # Добавляем стек виджетов в контейнер контента
        content_layout.addWidget(self.stacked_widget)

        # Добавляем виджеты в главный layout
        main_layout.addWidget(sidebar)
        main_layout.addWidget(content_container)

        # Устанавливаем минимальный размер окна
        self.setMinimumSize(window_width, window_height)

        # Устанавливаем Dashboard как активную страницу
        self.dashboard_btn.setChecked(True)
        self.stacked_widget.setCurrentIndex(0)

    def connectSignals(self):
        """Подключение сигналов"""
        self.start_btn.clicked.connect(self.toggle_work)
        self.worker.signals.log_signal.connect(self.update_log)
        self.worker.signals.error_signal.connect(self.show_error)
        self.worker.signals.finished_signal.connect(self.on_finished)
        
        # Подключаем сигналы кнопок меню
        self.dashboard_btn.clicked.connect(self.switch_to_dashboard)
        self.settings_btn.clicked.connect(self.switch_to_settings)

    def switch_to_dashboard(self):
        """Переключение на страницу Dashboard"""
        self.stacked_widget.setCurrentIndex(0)
        self.dashboard_btn.setChecked(True)
        self.settings_btn.setChecked(False)

    def switch_to_settings(self):
        """Переключение на страницу настроек"""
        self.stacked_widget.setCurrentIndex(1)
        self.dashboard_btn.setChecked(False)
        self.settings_btn.setChecked(True)

    def toggle_work(self):
        """Управление работой"""
        if self.worker.is_running:
            self.stop_work()
        else:
            self.start_work()

    def start_work(self):
        """Запуск работы"""
        self.worker.user = self.username_input.text()
        self.worker.pwd = self.password_input.text()
        
        if not self.worker.user or not self.worker.pwd:
            self.update_log("Введите логин и пароль!")
            return
            
        self.worker.is_running = True
        self.start_btn.setText("Стоп")
        self.worker.start()

    def stop_work(self):
        """Остановка работы"""
        self.worker.is_running = False
        self.start_btn.setText("Старт")
        self.worker.browser_controller.safe_quit()

    def update_log(self, message):
        """Обновление логов"""
        self.logs.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}")
        self.logs.moveCursor(QTextCursor.End)

    def show_error(self, message):
        """Показ ошибок"""
        QMessageBox.critical(self, "Ошибка", message)

    def on_finished(self):
        """Завершение работы"""
        self.start_btn.setText("Старт")

    def loadConfig(self):
        """Загрузка конфигурации"""
        try:
            with open("config.txt", "r") as f:
                data = f.read().splitlines()
                self.username_input.setText(data[0])
                self.password_input.setText(data[1])
        except:
            pass

    def closeEvent(self, event):
        """Обработка закрытия"""
        self.stop_work()
        event.accept() 