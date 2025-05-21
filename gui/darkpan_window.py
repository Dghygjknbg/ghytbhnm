import sys
import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QMessageBox, QStackedWidget,
    QFrame, QScrollArea, QProgressBar, QGridLayout, QDialog
)
from PySide6.QtCore import Qt, QSize, QByteArray
from PySide6.QtGui import QIcon, QTextCursor, QPixmap, QPainter
from PySide6.QtSvgWidgets import QSvgWidget

class DarkPanStyle:
    DARK_BG = "#2A2D3E"
    BLACK_BG = "#000000"
    DARK_SECONDARY = "#20233E"
    PRIMARY_COLOR = "#0091E8"
    LIGHT_TEXT = "#FFFFFF"
    GRAY_TEXT = "#6C7293"
    BORDER_COLOR = "#3A3F5C"
    INPUT_BG = "#20233E"
    HOVER_BG = "#343956"

    GLOBAL_STYLE = f"""
    QMainWindow {{ background-color: {DARK_BG}; color: {LIGHT_TEXT}; font-family: 'Segoe UI', sans-serif; }}
    QFrame#sidebar {{ background-color: {DARK_SECONDARY}; border-right: 1px solid {BORDER_COLOR}; }}
    QLabel#logo_label {{ margin-right: 10px; }}
    QLabel#title_label {{ color: {LIGHT_TEXT}; font-size: 20px; font-weight: bold; }}
    QPushButton#sidebar_btn {{ background-color: transparent; color: {GRAY_TEXT}; text-align: left; padding: 10px 20px; border: none; border-left: 3px solid transparent; font-size: 14px; }}
    QPushButton#sidebar_btn:hover {{ color: {PRIMARY_COLOR}; background-color: {HOVER_BG}; }}
    QPushButton#sidebar_btn:checked {{ color: {PRIMARY_COLOR}; background-color: {BLACK_BG}; border-left: 3px solid {PRIMARY_COLOR}; border-top-right-radius: 20px; border-bottom-right-radius: 20px; font-weight: bold; }}
    QScrollArea#content {{ background-color: {DARK_BG}; }}
    QWidget#content_container {{ padding: 25px; }}
    QFrame#stats-card {{ background-color: {DARK_SECONDARY}; border-radius: 8px; padding: 15px; }}
    QLabel#stats-icon {{ font-size: 32px; color: {PRIMARY_COLOR}; }}
    QLabel#stats-title {{ color: {GRAY_TEXT}; font-size: 13px; }}
    QLabel#stats-value {{ color: {LIGHT_TEXT}; font-size: 24px; font-weight: bold; }}
    QLabel#form-label {{ color: {GRAY_TEXT}; font-size: 14px; }}
    QLineEdit {{ background-color: {INPUT_BG}; color: {LIGHT_TEXT}; border: 1px solid {BORDER_COLOR}; border-radius: 5px; padding: 8px; }}
    QLineEdit:focus {{ border: 1px solid {PRIMARY_COLOR}; }}
    QPushButton#primary-btn {{ background-color: {PRIMARY_COLOR}; color: {LIGHT_TEXT}; border: none; border-radius: 5px; padding: 10px 20px; min-height: 40px; }}
    QPushButton#primary-btn:hover {{ background-color: #007acc; }}
    QProgressBar {{ background-color: {DARK_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 5px; text-align: center; height: 20px; }}
    QProgressBar::chunk {{ background-color: {PRIMARY_COLOR}; border-radius: 5px; }}
    """

# Преобразование SVG в QPixmap с заменой цвета
def svg_to_pixmap(svg_path, color, size=24):
    with open(svg_path, "r", encoding="utf-8") as f:
        data = f.read().replace("currentColor", color)
    widget = QSvgWidget()
    widget.load(QByteArray(data.encode()))
    widget.renderer().setAspectRatioMode(Qt.KeepAspectRatio)
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    widget.renderer().render(painter)
    painter.end()
    return pixmap

# Кнопка боковой панели с иконкой и состоянием
class SidebarButton(QPushButton):
    def __init__(self, text, icon_path=None):
        super().__init__(text)
        self.setObjectName("sidebar_btn")
        self.setCheckable(True)
        if icon_path:
            self.icon_normal = svg_to_pixmap(icon_path, DarkPanStyle.GRAY_TEXT)
            self.icon_active = svg_to_pixmap(icon_path, DarkPanStyle.PRIMARY_COLOR)
            self.setIcon(QIcon(self.icon_normal))
            self.setIconSize(QSize(24, 24))
        self.toggled.connect(self.update_icon)

    def update_icon(self, checked):
        self.setIcon(QIcon(self.icon_active if checked else self.icon_normal))

# Карточка статистики с прогрессбаром
class StatsCard(QFrame):
    def __init__(self, title, value, icon_path=None, progress=None):
        super().__init__()
        self.setObjectName("stats-card")
        layout = QVBoxLayout(self)
        hl = QHBoxLayout()
        if icon_path:
            icon_lbl = QLabel()
            pix = QPixmap(icon_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_lbl.setPixmap(pix)
            icon_lbl.setObjectName("stats-icon")
            hl.addWidget(icon_lbl)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("stats-title")
        hl.addWidget(title_lbl)
        hl.addStretch()
        layout.addLayout(hl)
        val_lbl = QLabel(value)
        val_lbl.setObjectName("stats-value")
        layout.addWidget(val_lbl)
        if progress is not None:
            bar = QProgressBar()
            bar.setValue(progress)
            bar.setFormat(f"{progress}%")
            layout.addWidget(bar)
        layout.addStretch()

# Главное окно с навигацией и страницами
class MainWindow(QMainWindow):
    def __init__(self, worker):
        super().__init__()
        self.worker = worker
        self.initUI()
        self.connectSignals()
        self.loadConfig()

    def initUI(self):
        self.setWindowTitle("X_Patch Pro Dashboard")
        self.resize(1200, 800)
        self.setWindowIcon(QIcon("logo.svg"))
        self.setStyleSheet(DarkPanStyle.GLOBAL_STYLE)

        main = QWidget(objectName="main_widget")
        hlayout = QHBoxLayout(main)
        self.setCentralWidget(main)

        # Sidebar
        sidebar = QFrame(objectName="sidebar")
        sidebar.setFixedWidth(250)
        sv = QVBoxLayout(sidebar)
        sv.setContentsMargins(15, 25, 15, 25)
        h = QHBoxLayout()
        logo = QLabel(objectName="logo_label")
        logo.setPixmap(QPixmap("logo.svg").scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        h.addWidget(logo)
        ttl = QLabel("X_Patch Pro", objectName="title_label")
        h.addWidget(ttl)
        h.addStretch()
        sv.addLayout(h)
        sv.addWidget(self._make_separator())
        sv.addWidget(QLabel("НАВИГАЦИЯ", objectName="nav_label"))
        self.dashboard_btn = SidebarButton("Dashboard", "gui/icons/dashboard.svg")
        self.profitcentr_btn = SidebarButton("ProfitCentr", "gui/icons/laptop.svg")
        self.tasks_btn = SidebarButton("Задания", "gui/icons/th.svg")
        self.statistics_btn = SidebarButton("Статистика", "gui/icons/chart-bar.svg")
        self.accounts_btn = SidebarButton("Аккаунты", "gui/icons/user.svg")
        for btn in (self.dashboard_btn, self.profitcentr_btn, self.tasks_btn, self.statistics_btn, self.accounts_btn):
            sv.addWidget(btn)
        sv.addWidget(QLabel("ДОПОЛНИТЕЛЬНО", objectName="additional_label"))
        self.settings_btn = SidebarButton("Настройки", "gui/icons/cog.svg")
        self.help_btn = SidebarButton("Помощь", "gui/icons/question-circle.svg")
        sv.addWidget(self.settings_btn)
        sv.addWidget(self.help_btn)
        sv.addStretch()
        sv.addWidget(QLabel("© X_Patch Pro 2025", objectName="footer_label"))

        # Content area
        scroll = QScrollArea(objectName="content")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        container = QWidget(objectName="content_container")
        vl = QVBoxLayout(container)
        vl.setSpacing(20)
        scroll.setWidget(container)

        self.stacked = QStackedWidget()

        # Dashboard page
        dash = QWidget()
        dl = QVBoxLayout(dash)
        dl.addWidget(QLabel("Dashboard", objectName="page-title"))
        stats_cards = [
            StatsCard("ВЫПОЛНЕНО", "385", "logo.svg", 75),
            StatsCard("ЗАРАБОТАНО", "₽ 2750", "logo.svg", 65),
            StatsCard("АККАУНТЫ", "8/10", "logo.svg", 80),
            StatsCard("СЕРВИСЫ", "3/5", "logo.svg", 60)
        ]
        grid = QGridLayout(objectName="stats-grid")
        grid.setSpacing(15)
        for i, card in enumerate(stats_cards):
            grid.addWidget(card, 0, i)
        dl.addLayout(grid)
        for title, text in [("Аналитика (в разработке)", "Здесь будут отображаться графики статистики"),
                            ("Модули в разработке", "Автоматическое распознавание капчи и прочее")]:
            card = QFrame(objectName="stats-card")
            cl = QVBoxLayout(card)
            cl.addWidget(QLabel(title, objectName="stats-title"))
            lbl = QLabel(text)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"color: {DarkPanStyle.GRAY_TEXT}; padding:20px;")
            cl.addWidget(lbl)
            dl.addWidget(card)
        self.stacked.addWidget(dash)

        # ProfitCentr page with two-column layout
        prof = QWidget()
        pl = QVBoxLayout(prof)
        pl.addWidget(QLabel("PROFITCENTR", objectName="page-title"))
        two_grid = QGridLayout()
        two_grid.setSpacing(15)
        
        # Site info card
        site_card = QFrame(objectName="stats-card")
        sl = QVBoxLayout(site_card)
        sl.setContentsMargins(15,15,15,15)
        
        # Header with logo and title
        header = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(QPixmap("logo.svg").scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header.addWidget(logo)
        header_text = QVBoxLayout()
        header_text.addWidget(QLabel("ProfitCentr", objectName="stats-title"))
        header_text.addWidget(QLabel("Сервис для заработка", objectName="form-label"))
        header.addLayout(header_text)
        header.addStretch()
        sl.addLayout(header)
        
        # Balance and settings
        balance = QLabel("Баланс: ₽ 0.00", objectName="stats-value")
        sl.addWidget(balance)
        settings_btn = QPushButton("Настройки", objectName="primary-btn")
        settings_btn.clicked.connect(self.show_settings_dialog)
        sl.addWidget(settings_btn)
        two_grid.addWidget(site_card,0,0)
        
        # Control card
        control = QFrame(objectName="stats-card")
        cl = QVBoxLayout(control)
        cl.setContentsMargins(15,15,15,15)
        cl.addWidget(QLabel("Управление", objectName="stats-title"))
        
        # Добавляем поля ввода
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.start_btn = QPushButton("Старт", objectName="primary-btn")
        cl.addWidget(self.start_btn)
        cl.addStretch()
        two_grid.addWidget(control,0,1)
        
        two_grid.setColumnStretch(0,1)
        two_grid.setColumnStretch(1,1)
        pl.addLayout(two_grid)
        # Logs card
        logc = QFrame(objectName="stats-card")
        ll = QVBoxLayout(logc)
        ll.addWidget(QLabel("Логи", objectName="stats-title"))
        self.logs = QTextEdit(objectName="logs")
        self.logs.setReadOnly(True)
        ll.addWidget(self.logs)
        pl.addWidget(logc)
        self.stacked.addWidget(prof)

        # Other placeholder pages
        for name in ["Задания", "Статистика", "Аккаунты"]:
            w = QWidget()
            l = QVBoxLayout(w)
            l.addWidget(QLabel(name, objectName="page-title"))
            l.addWidget(QLabel(f"Раздел {name} находится в разработке", alignment=Qt.AlignCenter,
                               styleSheet=f"color: {DarkPanStyle.GRAY_TEXT}; font-size:18px;"))
            self.stacked.addWidget(w)

        vl.addWidget(self.stacked)
        hlayout.addWidget(sidebar)
        hlayout.addWidget(scroll)
        self.dashboard_btn.setChecked(True)
        self.stacked.setCurrentIndex(0)

    def _make_separator(self):
        sep = QFrame(objectName="separator")
        sep.setFrameShape(QFrame.HLine)
        return sep

    def connectSignals(self):
        if self.worker:
            self.start_btn.clicked.connect(self.toggle_work)
            self.worker.signals.log_signal.connect(self.update_log)
            self.worker.signals.error_signal.connect(self.show_error)
            self.worker.signals.finished_signal.connect(self.on_finished)
        btns = [self.dashboard_btn, self.profitcentr_btn, self.tasks_btn, self.statistics_btn, self.accounts_btn]
        for idx, btn in enumerate(btns):
            btn.clicked.connect(lambda _, i=idx: self.switch_page(i))

    def switch_page(self, index):
        for btn in [self.dashboard_btn, self.profitcentr_btn, self.tasks_btn, self.statistics_btn, self.accounts_btn, self.settings_btn, self.help_btn]:
            btn.setChecked(False)
        btns = [self.dashboard_btn, self.profitcentr_btn, self.tasks_btn, self.statistics_btn, self.accounts_btn]
        if 0 <= index < len(btns):
            btns[index].setChecked(True)
        self.stacked.setCurrentIndex(index)

    def toggle_work(self):
        if self.worker.is_running:
            self.stop_work()
        else:
            self.start_work()

    def start_work(self):
        self.worker.user = self.username_input.text()
        self.worker.pwd = self.password_input.text()
        if not self.worker.user or not self.worker.pwd:
            self.update_log("Введите логин и пароль!")
            return
        self.worker.is_running = True
        self.start_btn.setText("Стоп")
        self.worker.start()

    def stop_work(self):
        self.worker.is_running = False
        self.start_btn.setText("Старт")
        self.worker.browser_controller.safe_quit()
        self.worker.wait()

    def update_log(self, message):
        ts = datetime.datetime.now().strftime('%H:%M:%S')
        self.logs.append(f"[{ts}] {message}")
        self.logs.moveCursor(QTextCursor.End)

    def show_error(self, message):
        QMessageBox.critical(self, "Ошибка", message)

    def on_finished(self):
        self.start_btn.setText("Старт")

    def loadConfig(self):
        try:
            with open("config.txt", "r") as f:
                data = f.read().splitlines()
                self.username_input.setText(data[0])
                self.password_input.setText(data[1])
        except:
            pass

    def show_settings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Настройки ProfitCentr")
        dialog.setFixedWidth(400)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Настройки авторизации", objectName="stats-title"))
        
        form = QVBoxLayout()
        form.setContentsMargins(0,15,0,15)
        
        # Перемещаем поля ввода в диалог
        username_input = QLineEdit(self.username_input.text())
        password_input = QLineEdit(self.password_input.text())
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        for lbl, w in [("Логин:", username_input), ("Пароль:", password_input)]:
            form.addWidget(QLabel(lbl, objectName="form-label"))
            form.addWidget(w)
        
        layout.addLayout(form)
        
        # Кнопки
        buttons = QHBoxLayout()
        save_btn = QPushButton("Сохранить", objectName="primary-btn")
        cancel_btn = QPushButton("Отмена")
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)
        
        # Обработчики
        def save_settings():
            self.username_input.setText(username_input.text())
            self.password_input.setText(password_input.text())
            try:
                with open("config.txt", "w") as f:
                    f.write(f"{username_input.text()}\n{password_input.text()}")
            except Exception as e:
                self.show_error(f"Ошибка сохранения: {str(e)}")
            dialog.accept()
            
        save_btn.clicked.connect(save_settings)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.setStyleSheet(DarkPanStyle.GLOBAL_STYLE)
        dialog.exec()

    def closeEvent(self, event):
        try:
            if self.worker and self.worker.is_running:
                self.stop_work()
        except:
            pass
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow(worker=None)
    window.show()
    sys.exit(app.exec())
