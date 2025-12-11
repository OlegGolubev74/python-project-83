import os

import requests
from flask import Flask, flash, redirect, render_template, request, url_for

from . import database
from .parser import parse_html
from .url_normalizer import normalize_url, validate_url

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route("/")
def index():
    """Главная страница с формой ввода URL"""
    url = request.args.get('url', '')
    return render_template('index.html', url=url)


@app.post("/urls")
def analyze():
    """Обработка добавления нового URL"""
    url = request.form.get('url')
    
    # Валидация URL
    is_valid, error_message = validate_url(url)
    if not is_valid:
        flash(error_message, 'danger')
        return render_template('index.html', url=url), 422
    
    # Нормализация URL
    normalized_url = normalize_url(url)
    if not normalized_url:
        flash("Некорректный URL", 'danger')
        return render_template('index.html', url=url), 422
    
    # Отладочная информация
    print(f"Оригинальный URL: {url}")
    print(f"Нормализованный URL: {normalized_url}")
    
    try:
        # Проверяем существование URL в БД
        existing_url = database.find_url_by_name(normalized_url)
        
        if existing_url:
            # URL уже существует
            url_id = existing_url['id']
            flash("Страница уже существует", 'info')
        else:
            # Добавляем новый URL
            url_id = database.insert_url(normalized_url)
            flash("Страница успешно добавлена", 'success')
        
        return redirect(url_for('url_info', id=url_id))
        
    except Exception as e:
        flash(f"Ошибка базы данных: {e}", 'danger')
        return redirect(f'/?url={url}')


@app.get("/urls/<int:id>")
def url_info(id):
    """Страница с информацией о сайте"""
    url_data = database.find_url_by_id(id)
    
    if not url_data:
        flash("Страница не найдена", 'danger')
        return redirect('/urls')
    
    checks = database.get_url_checks(id)
    
    return render_template('url_info.html',
                         variable1=url_data['id'],
                         variable2=url_data['name'],
                         variable3=url_data['created_at'],
                         checks=checks)


@app.post("/urls/<int:id>/checks")
def check_url(id):
    """Выполнить проверку сайта"""
    url_data = database.find_url_by_id(id)
    
    if not url_data:
        flash("Страница не найдена", 'danger')
        return redirect('/urls')
    
    site_url = url_data['name']
    
    try:
        # Выполняем запрос к сайту
        response = requests.get(site_url, timeout=10)
        response.raise_for_status()
        
        # Парсим HTML
        parsed_data = parse_html(response.text)
        
        # Сохраняем проверку в БД
        database.insert_url_check(
            url_id=id,
            status_code=response.status_code,
            h1=parsed_data['h1'],
            title=parsed_data['title'],
            description=parsed_data['description']
        )
        
        flash("Страница успешно проверена", 'success')
        
    except Exception:
        flash("Произошла ошибка при проверке", 'danger')
    
    return redirect(url_for('url_info', id=id))


@app.get("/urls")
def show_urls():
    """Страница со списком всех сайтов"""
    urls = database.get_all_urls()
    return render_template('urls_info.html', urls=urls)


if __name__ == '__main__':
    app.run(debug=os.getenv('DEBUG') == 'True')