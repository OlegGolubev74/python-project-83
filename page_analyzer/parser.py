from bs4 import BeautifulSoup


def parse_html(html_content):
    """
    Парсит HTML и извлекает нужные данные
    Возвращает словарь с найденными элементами
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    result = {
        'h1': '',
        'title': '',
        'description': ''
    }
    
    # Ищем тег h1
    h1_tag = soup.find('h1')
    if h1_tag:
        result['h1'] = h1_tag.text.strip()[:255]  # Ограничиваем длину
    
    # Ищем тег title
    title_tag = soup.find('title')
    if title_tag:
        result['title'] = title_tag.text.strip()[:255]
    
    # Ищем мета-тег description
    meta_description = soup.find('meta', attrs={'name': 'description'})
    if meta_description and meta_description.get('content'):
        result['description'] = meta_description['content'].strip()[:255]
    
    return result