import sys
import os
import time
import random
import datetime
import json
from pathlib import Path

# Добавляем текущую директорию в путь поиска модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QThread, QTimer
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

from tasks.profitcentr.auth import AuthManager
from tasks.profitcentr.captcha_manager import CaptchaManager
from tasks.profitcentr.jump import JumpManager
from gui.signals import WorkerSignals
from gui.darkpan_window import MainWindow
from tasks.profitcentr.base_manager import BaseManager

class MenuManager(BaseManager):
    """Менеджер для работы с меню"""
    def __init__(self, browser_controller, auth_manager, log_callback=None):
        super().__init__(browser_controller, log_callback)
        self.auth_manager = auth_manager
        self._max_retries = 3
        self._retry_delay = 2

    def check_menu(self):
        """Проверка состояния меню и его открытие при необходимости."""
        for attempt in range(self._max_retries):
            try:
                self.human_delay(0.5, 1.0)
                
                menu_block = WebDriverWait(self.browser_controller.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "mnu_tblock1"))
                )
                
                style = menu_block.get_attribute("style")
                
                if style and "display: none" in style:
                    self._log("Открываем меню...")
                    menu_title = WebDriverWait(self.browser_controller.driver, 10).until(
                        EC.presence_of_element_located((By.ID, "mnu_title1"))
                    )
                    
                    if not self.human_click(menu_title):
                        self._log(f"Попытка {attempt + 1} открыть меню не удалась")
                        self.human_delay(self._retry_delay, self._retry_delay * 2)
                        continue
                    
                    self.human_delay(0.8, 1.5)
                    
                    menu_block = self.browser_controller.driver.find_element(By.ID, "mnu_tblock1")
                    style = menu_block.get_attribute("style")
                    if style and "display: none" in style:
                        self._log("Не удалось открыть меню")
                        continue
                        
                return True
                
            except Exception as e:
                self._log(f"Ошибка при проверке меню: {str(e)}")
                if attempt < self._max_retries - 1:
                    self.human_delay(self._retry_delay, self._retry_delay * 2)
        
        return False

class BrowserController:
    """Управление браузером"""
    def __init__(self):
        self.driver = None
        self._is_headless = False

    def build_browser(self, headless=False):
        """Инициализация браузера с улучшенными настройками"""
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless")
                self._is_headless = True
            
            # Добавляем дополнительные настройки для стабильности
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--enable-unsafe-swiftshader")
            
            # Устанавливаем таймауты
            chrome_options.add_argument("--page-load-timeout=30")
            chrome_options.add_argument("--script-timeout=30")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)

            # Получаем размеры экрана
            screen_width = self.driver.execute_script("return window.screen.width")
            screen_height = self.driver.execute_script("return window.screen.height")
            
            # Устанавливаем размеры и позицию браузера
            # Половина ширины экрана, полная высота, позиция справа
            window_width = screen_width // 2
            window_height = screen_height
            window_x = screen_width - window_width  # Позиция справа
            window_y = 0
            
            self.driver.set_window_position(window_x, window_y)
            self.driver.set_window_size(window_width, window_height)
            
            return True
        except Exception as e:
            print(f"Ошибка при инициализации браузера: {str(e)}")
            return False

    def safe_quit(self):
        """Безопасное закрытие браузера"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"Ошибка при закрытии браузера: {str(e)}")
            finally:
                self.driver = None

    def is_headless(self):
        """Проверка режима работы браузера"""
        return self._is_headless

class ProWorker(QThread):
    """Основной рабочий поток"""
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        self.is_running = False
        self.user = ""
        self.pwd = ""
        self.headless = False
        self.browser_controller = BrowserController()
        self._max_retries = 3
        self._retry_delay = 2

    def _log(self, message):
        """Логирование с временной меткой"""
        self.signals.log_signal.emit(f"{datetime.datetime.now().strftime('%H:%M:%S')} | {message}")

    def run(self):
        """Основной цикл работы"""
        self.is_running = True
        try:
            if not self.browser_controller.build_browser(self.headless):
                raise Exception("Не удалось инициализировать браузер")
            
            # Инициализация AuthManager с логгированием
            self.auth_manager = AuthManager(
                self.browser_controller,
                log_callback=lambda msg: self.signals.log_signal.emit(msg)
            )

            # Процесс авторизации с повторными попытками
            for attempt in range(self._max_retries):
                if self.auth_manager.check_auth_status():
                    break
                    
                self._log(f"Попытка авторизации {attempt + 1}...")
                login_success = self.auth_manager.perform_login(self.user, self.pwd)
                if login_success:
                    break
                    
                if attempt < self._max_retries - 1:
                    self._log(f"Ожидание перед следующей попыткой...")
                    time.sleep(self._retry_delay)
            else:
                raise Exception("Не удалось авторизоваться после всех попыток")

            # Инициализация MenuManager
            self.menu_manager = MenuManager(
                self.browser_controller,
                self.auth_manager,
                log_callback=lambda msg: self.signals.log_signal.emit(msg)
            )

            # Инициализация JumpManager
            self.jump_manager = JumpManager(
                self.browser_controller,
                log_callback=lambda msg: self.signals.log_signal.emit(msg),
                menu_manager=self.menu_manager
            )

            # Запускаем основную логику работы с прыжками
            if not self.jump_manager.start_work():
                raise Exception("Ошибка при выполнении работы с прыжками")

            # Основная логика
            self._log("Работа завершена")

            # Выход из аккаунта
            self._log("Завершение сессии...")
            if not self.auth_manager.safe_logout():
                self._log("Предупреждение: не удалось корректно завершить сессию")

        except Exception as e:
            self.signals.error_signal.emit(str(e))
        finally:
            self.is_running = False
            self.signals.finished_signal.emit()
            self.browser_controller.safe_quit()

    def stop(self):
        """Безопасная остановка работы"""
        self.is_running = False
        self.browser_controller.safe_quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        worker = ProWorker()
        window = MainWindow(worker)
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        error_dialog = QMessageBox()
        error_dialog.critical(None, "Критическая ошибка", f"Произошла критическая ошибка: {str(e)}")
        sys.exit(1)