from urllib.parse import urlparse

import validators


def normalize_url(url):
    """
    Нормализует URL: оставляет протокол, но удаляет путь и параметры
    Возвращает нормализованную строку (с протоколом и доменом)
    """
    if not url:
        return None
    
    # Убираем пробелы в начале и конце
    url = url.strip()
    
    try:
        parsed = urlparse(url)
        
        # Проверяем, что есть протокол
        if not parsed.scheme:
            return None
        
        # Проверяем, что протокол http или https
        if parsed.scheme not in ('http', 'https'):
            return None
        
        # Убираем www. , если есть
        hostname = parsed.netloc.lower()
        if hostname.startswith('www.'):
            hostname = hostname[4:]
        
        # Проверяем, что есть домен
        if not hostname:
            return None
        
        # Собираем нормализованный URL: протокол + домен
        normalized = f"{parsed.scheme}://{hostname}"
        
        return normalized
    except Exception:
        return None


def validate_url(url):
    """
    Проверяет валидность URL
    Возвращает (is_valid, error_message)
    """
    if not url or not url.strip():
        return False, "URL не должен быть пустым"
    
    url_to_validate = url.strip()
    
    # Проверяем валидность с помощью библиотеки validators
    if not validators.url(url_to_validate):
        return False, "Некорректный URL"
    
    # Дополнительная проверка, что это http или https URL
    parsed = urlparse(url_to_validate)
    if parsed.scheme not in ('http', 'https'):
        return False, "Некорректный URL"
    
    # Проверяем длину URL (после нормализации)
    normalized = normalize_url(url_to_validate)
    if normalized is None:
        return False, "Некорректный URL"
    
    if len(normalized) > 255:
        return False, "URL превышает максимальную длину (255 символов)"
    
    return True, ""