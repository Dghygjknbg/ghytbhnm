import time
import random
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, StaleElementReferenceException
from tasks.profitcentr.base_manager import BaseManager

class JumpManager(BaseManager):
    def __init__(self, browser_controller, log_callback=None, menu_manager=None):
        super().__init__(browser_controller, log_callback)
        self.menu_manager = menu_manager
        self._cache = {}
        self._max_retries = 3
        self._retry_delay = 2

    def check_menu(self):
        """Проверка меню с повторными попытками"""
        if not self.menu_manager:
            self._log("Менеджер меню не инициализирован")
            return False

        for attempt in range(self._max_retries):
            try:
                if self.menu_manager.check_menu():
                    self._log("Меню успешно открыто")
                    return True
                self._log(f"Попытка {attempt + 1} открыть меню не удалась")
                self.human_delay(self._retry_delay, self._retry_delay * 2)
            except Exception as e:
                self._log(f"Ошибка при проверке меню: {str(e)}")
        return False

    def click_jump_link(self):
        """Клик по ссылке переходов с повторными попытками"""
        for attempt in range(self._max_retries):
            try:
                jump_link = WebDriverWait(self.browser_controller.driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH, 
                        "//a[@class='ajax-site user_menuline' and contains(text(), 'Переходы')]"
                    ))
                )
                if self.human_click(jump_link):
                    self._log("Успешно кликнуто по ссылке переходов")
                    return True
                self._log(f"Попытка {attempt + 1} клика по ссылке переходов не удалась")
                self.human_delay(self._retry_delay, self._retry_delay * 2)
            except Exception as e:
                self._log(f"Ошибка при клике по ссылке переходов: {str(e)}")
        return False

    def wait_for_page_load(self, timeout=10):
        """Ожидание загрузки страницы с проверкой состояния"""
        try:
            WebDriverWait(self.browser_controller.driver, timeout).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )
            self.human_delay(0.5, 1.0)
            self._log("Страница успешно загружена")
            return True
        except TimeoutException:
            self._log("Превышено время ожидания загрузки страницы")
            return False
        except Exception as e:
            self._log(f"Ошибка при ожидании загрузки страницы: {str(e)}")
            return False

    def find_jump_element(self):
        """Поиск элемента прыжка с кэшированием"""
        cache_key = "jump_element"
        if cache_key in self._cache:
            try:
                element = self._cache[cache_key]
                if element.is_enabled() and element.is_displayed():
                    self._log("Элемент прыжка найден в кэше")
                    return element
            except (StaleElementReferenceException, WebDriverException):
                self._log("Элемент в кэше устарел")
                pass
            del self._cache[cache_key]

        try:
            element = WebDriverWait(self.browser_controller.driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//a[contains(@onclick, \"funcjs['go-jump']\")]"
                ))
            )
            self._cache[cache_key] = element
            self._log("Элемент прыжка успешно найден")
            return element
        except Exception as e:
            self._log(f"Ошибка при поиске элемента прыжка: {str(e)}")
            return None

    def extract_wait_time(self, onclick_value):
        """Извлечение времени ожидания с обработкой ошибок"""
        try:
            parts = onclick_value.split(",")
            if len(parts) >= 3:
                wait_time = int(parts[2].strip().strip("'"))
                self._log(f"Извлечено время ожидания: {wait_time} секунд")
                return max(wait_time, 0)  # Убеждаемся, что время не отрицательное
            self._log("Не удалось извлечь время ожидания из атрибута onclick")
            return 0
        except Exception as e:
            self._log(f"Ошибка при извлечении времени ожидания: {str(e)}")
            return 0

    def _safe_switch_to_window(self, window_handle):
        """Безопасное переключение на окно"""
        try:
            self.browser_controller.driver.switch_to.window(window_handle)
            self._log(f"Успешно переключено на окно: {window_handle}")
            return True
        except Exception as e:
            self._log(f"Ошибка при переключении на окно {window_handle}: {str(e)}")
            return False

    def process_jump(self, element):
        """Обработка прыжка с улучшенной обработкой ошибок"""
        original_window = None
        try:
            onclick_value = element.get_attribute('onclick')
            wait_time = self.extract_wait_time(onclick_value)
            if wait_time == 0:
                self._log("Не удалось получить время ожидания")
                return False

            original_window = self.browser_controller.driver.current_window_handle
            self._log(f"Текущее окно: {original_window}")

            if not self.human_click(element):
                self._log("Не удалось кликнуть по элементу прыжка")
                return False

            try:
                WebDriverWait(self.browser_controller.driver, 10).until(
                    lambda d: len(d.window_handles) > 1
                )
                self._log("Новое окно успешно открыто")
            except TimeoutException:
                self._log("Не удалось дождаться открытия нового окна")
                return False

            new_window = [w for w in self.browser_controller.driver.window_handles 
                         if w != original_window][0]
            self._log(f"Найдено новое окно: {new_window}")
            
            if not self._safe_switch_to_window(new_window):
                self._log("Не удалось переключиться на новую вкладку")
                return False

            # Добавляем 5 секунд к базовому времени ожидания
            total_wait_time = wait_time + 5
            self._log(f"Ожидание {total_wait_time} секунд...")
            time.sleep(total_wait_time)

            try:
                self.browser_controller.driver.close()
                self._log("Окно успешно закрыто")
            except Exception as e:
                self._log(f"Ошибка при закрытии окна: {str(e)}")

            if not self._safe_switch_to_window(original_window):
                self._log("Не удалось вернуться на исходное окно")
                return False

            self.browser_controller.driver.refresh()
            if not self.wait_for_page_load():
                self._log("Не удалось дождаться перезагрузки страницы")
                return False

            self._log("Прыжок успешно выполнен")
            return True

        except Exception as e:
            self._log(f"Ошибка при обработке прыжка: {str(e)}")
            if original_window:
                self._safe_switch_to_window(original_window)
            return False

    def start_work(self):
        """Основной рабочий процесс с улучшенной обработкой ошибок"""
        try:
            self._log("Начинаем работу с прыжками...")
            self._cache.clear()  # Очищаем кэш при старте

            if not self.check_menu():
                self._log("Не удалось открыть меню")
                return False

            if not self.click_jump_link():
                self._log("Не удалось перейти на страницу переходов")
                return False

            if not self.wait_for_page_load():
                self._log("Не удалось дождаться загрузки страницы")
                return False

            jump_count = 0
            max_jumps = 100  # Ограничение на количество прыжков
            consecutive_errors = 0
            max_consecutive_errors = 3

            while jump_count < max_jumps:
                jump_element = self.find_jump_element()
                
                if not jump_element:
                    self._log("Больше нет элементов для прыжков")
                    break

                if self.process_jump(jump_element):
                    jump_count += 1
                    consecutive_errors = 0
                    self._log(f"Успешно выполнен прыжок #{jump_count}")
                else:
                    consecutive_errors += 1
                    self._log(f"Ошибка при обработке прыжка (попытка {consecutive_errors})")
                    if consecutive_errors >= max_consecutive_errors:
                        self._log("Превышено максимальное количество последовательных ошибок")
                        break

                self.human_delay(2, 4)

            self._log(f"Работа с прыжками завершена. Выполнено прыжков: {jump_count}")
            return True

        except Exception as e:
            self._log(f"Критическая ошибка при выполнении работы с прыжками: {str(e)}")
            return False
