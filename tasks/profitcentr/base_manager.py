import time
import random
from typing import Optional, Callable

class BaseManager:
    """Базовый класс для всех менеджеров"""
    def __init__(self, browser_controller, log_callback: Optional[Callable[[str], None]] = None):
        self.browser_controller = browser_controller
        self.log_callback = log_callback or (lambda msg: None)
        self._max_retries = 3
        self._retry_delay = 2

    def _log(self, message: str) -> None:
        """Логирование с временной меткой"""
        if self.log_callback:
            self.log_callback(f"{time.strftime('%H:%M:%S')} | {message}")

    def human_delay(self, min_delay: float = 0.5, max_delay: float = 2.0) -> None:
        """Имитация человеческой задержки"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    def human_click(self, element) -> bool:
        """Имитация человеческого клика с обработкой ошибок"""
        try:
            self.human_delay(0.3, 0.7)
            self.browser_controller.driver.execute_script(
                "arguments[0].click();", 
                element
            )
            self.human_delay(0.2, 0.5)
            self._log("Успешно выполнен клик по элементу")
            return True
        except Exception as e:
            self._log(f"Ошибка при клике: {str(e)}")
            try:
                element.click()
                self._log("Успешно выполнен обычный клик по элементу")
                return True
            except Exception as click_error:
                self._log(f"Ошибка при обычном клике: {str(click_error)}")
                return False 