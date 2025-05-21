import os
import time
import random
import json
import base64
from cryptography.fernet import Fernet
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from tasks.profitcentr.captcha_manager import CaptchaManager
from tasks.profitcentr.base_manager import BaseManager

class AuthManager(BaseManager):
    """Управление процессом авторизации"""
    def __init__(self, browser_controller, log_callback=None):
        super().__init__(browser_controller, log_callback)
        self.captcha_manager = CaptchaManager(browser_controller, log_callback)
        self._cache = {}
        self._load_encryption_key()
        self.credentials = self._load_encrypted_credentials()

    def _load_encryption_key(self):
        """Загрузка или создание ключа шифрования"""
        key_file = "auth_key.key"
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(self.key)
        self.cipher_suite = Fernet(self.key)

    def _encrypt_credentials(self, username, password):
        """Шифрование учетных данных"""
        credentials = json.dumps({"username": username, "password": password})
        return self.cipher_suite.encrypt(credentials.encode())

    def _decrypt_credentials(self, encrypted_data):
        """Расшифровка учетных данных"""
        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            return json.loads(decrypted_data)
        except Exception:
            return None

    def _load_encrypted_credentials(self):
        """Загрузка зашифрованных учетных данных"""
        try:
            if os.path.exists("credentials.enc"):
                with open("credentials.enc", "rb") as f:
                    return self._decrypt_credentials(f.read())
        except Exception as e:
            self._log(f"Ошибка при загрузке учетных данных: {str(e)}")
        return None

    def _save_encrypted_credentials(self, username, password):
        """Сохранение зашифрованных учетных данных"""
        try:
            encrypted_data = self._encrypt_credentials(username, password)
            with open("credentials.enc", "wb") as f:
                f.write(encrypted_data)
            return True
        except Exception as e:
            self._log(f"Ошибка при сохранении учетных данных: {str(e)}")
            return False

    def _validate_credentials(self, username, password):
        """Проверка валидности учетных данных"""
        if not username or not password:
            self._log("Логин и пароль не могут быть пустыми")
            return False
        return True

    def _check_input_fields(self):
        """Проверка наличия полей ввода"""
        try:
            WebDriverWait(self.browser_controller.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            WebDriverWait(self.browser_controller.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            return True
        except TimeoutException:
            self._log("Не удалось найти поля ввода")
            return False

    def human_type(self, element, text):
        """Имитация человеческого ввода текста"""
        try:
            element.clear()
            for char in text:
                element.send_keys(char)
                self.human_delay(0.1, 0.3)  # Задержка между символами
            return True
        except Exception as e:
            self._log(f"Ошибка при вводе текста: {str(e)}")
            return False

    def check_auth_status(self):
        """Проверка статуса авторизации"""
        try:
            # Проверяем URL
            if self.browser_controller.driver.current_url != "https://profitcentr.com/members":
                return False

            # Проверяем наличие элементов авторизованного пользователя
            try:
                WebDriverWait(self.browser_controller.driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "user_menu"))
                )
                return True
            except TimeoutException:
                return False
        except Exception as e:
            self._log(f"Ошибка при проверке статуса авторизации: {str(e)}")
            return False

    def handle_captcha(self):
        """Обработка капчи"""
        return self.captcha_manager.solve_captcha()

    def safe_logout(self):
        """Безопасный выход из системы с обработкой ошибок."""
        try:
            self._log("Начинаем процесс выхода из системы...")
            
            # Ждем загрузки страницы
            self.human_delay(1.0, 2.0)
            
            # Ищем ссылку выхода по частичному совпадению URL и тексту
            try:
                logout_link = WebDriverWait(self.browser_controller.driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH, 
                        "//a[contains(@href, 'logout?exit_account') and text()='Выход']"
                    ))
                )
            except TimeoutException:
                self._log("Не удалось найти ссылку выхода")
                return False

            # Прокручиваем к элементу, если он не виден
            try:
                self.browser_controller.driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                    logout_link
                )
                self.human_delay(0.5, 1.0)
            except Exception as e:
                self._log(f"Ошибка при прокрутке к элементу: {str(e)}")

            # Пробуем кликнуть разными способами
            try:
                # Сначала пробуем человеческий клик
                self.human_click(logout_link)
            except ElementClickInterceptedException:
                try:
                    # Если не получилось, пробуем через JavaScript
                    self.browser_controller.driver.execute_script("arguments[0].click();", logout_link)
                except Exception as e:
                    self._log(f"Ошибка при клике через JavaScript: {str(e)}")
                    return False

            # Ждем подтверждения выхода
            try:
                WebDriverWait(self.browser_controller.driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH, 
                        "//a[@href='/login' and contains(@class, 'btn_log')]"
                    ))
                )
                self._log("Успешно вышли из системы")
                return True
            except TimeoutException:
                self._log("Не удалось подтвердить выход из системы")
                return False

        except Exception as e:
            self._log(f"Ошибка при выходе из системы: {str(e)}")
            return False
        
    def perform_login(self, username, password):
        """Выполнение входа в аккаунт"""
        if not self._validate_credentials(username, password):
            self._log("Невалидные учетные данные")
            return False

        self._log("Инициализация авторизации...")
        self.browser_controller.driver.get("https://profitcentr.com/login")
        self.human_delay(1.0, 2.0)
        
        if not self._check_input_fields():
            return False

        try:
            username_field = self.browser_controller.driver.find_element(By.NAME, "username")
            password_field = self.browser_controller.driver.find_element(By.NAME, "password")
            
            self._log("Ввод логина...")
            if not self.human_type(username_field, username):
                return False
            self.human_delay(0.5, 1.0)
            
            self._log("Ввод пароля...")
            if not self.human_type(password_field, password):
                return False
            self.human_delay(0.5, 1.0)

            self._log("Проверка капчи...")
            if not self.handle_captcha():
                return False

            try:
                WebDriverWait(self.browser_controller.driver, 30).until(
                    EC.url_to_be("https://profitcentr.com/members"))
                
                # Сохраняем учетные данные при успешной авторизации
                self._save_encrypted_credentials(username, password)
                
                self._log("Авторизация успешно завершена")
                return True
            except TimeoutException:
                self._log("Превышено время ожидания авторизации")
                return False
            
        except Exception as e:
            self._log(f"Критическая ошибка при авторизации: {str(e)}")
            return False
