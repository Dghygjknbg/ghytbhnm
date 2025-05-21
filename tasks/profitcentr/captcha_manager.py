import os
import time
from typing import Optional, Callable, Dict, List
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement

class CaptchaManager:
    """
    Менеджер для обработки и решения капчи на сайте.
    
    Отвечает за:
    - Определение типа капчи
    - Поиск и клик по нужным изображениям
    - Проверку успешности решения
    """
    
    # Маппинг текста задания капчи к соответствующим папкам с данными
    FOLDER_MAPPING: Dict[str, str] = {
        "Отметьте изображения с девушками": "girls",
        "Отметьте изображения с дорожными знаками": "road_signs",
        "Отметьте изображения с животными": "animals",
        "Отметьте изображения с машинами": "cars",
        "Отметьте изображения с мотоциклами": "motorcycles",
        "Отметьте изображения с цветами": "flowers"
    }
    
    def __init__(self, browser_controller, log_callback: Optional[Callable[[str], None]] = None):
        """
        Инициализация менеджера капчи.
        
        Args:
            browser_controller: Контроллер браузера для взаимодействия с веб-страницей
            log_callback: Функция для логирования сообщений
        """
        self.browser = browser_controller
        self.captcha_dir = os.path.join(os.path.dirname(__file__), "captcha")
        self.log = log_callback if log_callback else lambda x: None
        self.wait = WebDriverWait(self.browser.driver, 20)

    def get_image_segment(self, style: str) -> Optional[str]:
        """
        Извлекает сегмент изображения из CSS стиля.
        
        Args:
            style: CSS стиль элемента с URL изображения
            
        Returns:
            Сегмент изображения или None, если не удалось извлечь
        """
        try:
            base = style.split('url(')[1].split(')')[0]
            segments = base.split('/')
            return segments[-3] if len(segments) >= 3 else None
        except Exception:
            return None

    def check_image_exists(self, folder: str, segment: str) -> bool:
        """
        Проверяет наличие сегмента изображения в базе данных.
        
        Args:
            folder: Папка с данными для конкретного типа капчи
            segment: Сегмент изображения для проверки
            
        Returns:
            True если сегмент найден в базе, False в противном случае
        """
        file_path = os.path.join(self.captcha_dir, f"{folder}.txt")
        if not os.path.exists(file_path):
            return False
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return segment in f.read()
        except Exception as e:
            self.log(f"Ошибка при чтении файла {file_path}: {str(e)}")
            return False

    def solve_captcha(self) -> bool:
        """
        Решает капчу на странице.
        
        Процесс решения:
        1. Ожидает появления капчи
        2. Определяет тип капчи
        3. Находит и кликает по нужным изображениям
        4. Подтверждает решение
        
        Returns:
            True если капча решена успешно, False в случае ошибки
        """
        try:
            self.log("Ожидание загрузки капчи...")
            
            # Ждем появления заголовка капчи
            captcha_title = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "out-capcha-title"))
            )
            
            task_text = captcha_title.text.strip()
            self.log(f"Тип капчи: {task_text}")
            
            folder = self.FOLDER_MAPPING.get(task_text)
            if not folder:
                self.log(f"Неизвестный тип капчи: {task_text}")
                return False

            # Ждем появления группы изображений
            captcha_group = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "out-capcha"))
            )
            
            # Получаем все изображения
            images: List[WebElement] = captcha_group.find_elements(By.CLASS_NAME, "out-capcha-lab")
            self.log(f"Найдено изображений: {len(images)}")
            
            # Обрабатываем каждое изображение
            for img in images:
                if not img.is_displayed():
                    continue
                    
                style = img.get_attribute("style")
                segment = self.get_image_segment(style)
                
                if segment and self.check_image_exists(folder, segment):
                    self.log(f"Найдено совпадение: {segment}")
                    img.click()
                    time.sleep(0.5)  # Пауза для стабильности

            # Подтверждаем решение
            submit_btn = self.wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "btn_big_green"))
            )
            submit_btn.click()
            
            # Проверяем успешность решения
            try:
                self.wait.until(
                    EC.invisibility_of_element_located((By.CLASS_NAME, "out-capcha"))
                )
                self.log("Капча решена успешно")
                return True
            except TimeoutException:
                self.log("Капча не исчезла после решения")
                return False
            
        except TimeoutException as e:
            self.log(f"Таймаут при ожидании элементов капчи: {str(e)}")
            return False
        except NoSuchElementException as e:
            self.log(f"Элемент капчи не найден: {str(e)}")
            return False
        except Exception as e:
            self.log(f"Неожиданная ошибка при решении капчи: {str(e)}")
            return False
