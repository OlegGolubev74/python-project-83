import os
from datetime import date

import psycopg2
import requests
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request
from parser import parse_html
from url_normalizer import normalize_url, validate_url

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

print('------------------')
print(DATABASE_URL)
print('------------------')

try:
    conn = psycopg2.connect(DATABASE_URL)
    print("Подключился к БД")
except Exception as e:
    print(f"Не могу подключиться к БД: {e}")
    conn = None

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route("/")
def index():
    # Восстанавливаем введенный URL при ошибке валидации
    url = request.args.get('url', '')
    return render_template('index.html', url=url)


@app.post("/urls")
def analyze():
    url = request.form.get('url')  # Получаем URL из формы
    
    # Валидация URL
    is_valid, error_message = validate_url(url)
    if not is_valid:
        flash(error_message, 'danger')
        # Сохраняем введенный URL для отображения в форме
        return redirect(f'/?url={url}')
    
    # Нормализация URL
    normalized_url = normalize_url(url)
    
    if not normalized_url:
        flash("Некорректный URL", 'danger')
        return redirect(f'/?url={url}')
    
    # Выводим для отладки
    print(f"Оригинальный URL: {url}")
    print(f"Нормализованный URL: {normalized_url}")
    
    # Проверяем, существует ли уже такой URL в БД
    check_sql = "SELECT id FROM urls WHERE name = %s"
    insert_sql = """
        INSERT INTO urls (name, created_at) 
        VALUES (%s, %s) RETURNING id
    """

    with conn.cursor() as cur:
        try:
            # Проверяем существование
            cur.execute(check_sql, (normalized_url,))
            existing_url = cur.fetchone()
            
            if existing_url:
                # URL уже существует, показываем сообщение и 
                # редиректим на существующую запись
                url_id = existing_url[0]
                flash("Страница уже существует", 'info')
            else:
                # Добавляем новый URL
                cur.execute(insert_sql, (normalized_url, date.today()))
                conn.commit()
                url_id = cur.fetchone()[0]
                flash("Страница успешно добавлена", 'success')
            
            return redirect(f'/urls/{url_id}')
            
        except psycopg2.Error as e:
            conn.rollback()
            flash(f"Ошибка базы данных: {e}", 'danger')
            return redirect(f'/?url={url}')


@app.get("/urls/<int:id>")
def url_info(id):
    # Получаем информацию о сайте
    url_sql = "SELECT * FROM urls WHERE id = %s"
    # Получаем все проверки для этого сайта
    checks_sql = """
        SELECT * FROM url_checks 
        WHERE url_id = %s 
        ORDER BY id DESC
    """
    
    with conn.cursor() as cur:
        # Получаем информацию о сайте
        cur.execute(url_sql, (id,))
        url_result = cur.fetchone()
        
        if not url_result:
            flash("Страница не найдена", 'danger')
            return redirect('/urls')
        
        url_id, url_name, url_created_at = url_result
        
        # Получаем проверки для сайта
        cur.execute(checks_sql, (id,))
        checks = cur.fetchall()
    
    return render_template('url_info.html', 
                         variable1=url_id, 
                         variable2=url_name, 
                         variable3=url_created_at,
                         checks=checks)


@app.post("/urls/<int:id>/checks")
def check_url(id):
    """
    Выполняет проверку сайта и сохраняет результаты в БД
    """
    # Сначала проверяем, существует ли сайт
    check_site_sql = "SELECT name FROM urls WHERE id = %s"
    
    with conn.cursor() as cur:
        cur.execute(check_site_sql, (id,))
        site_result = cur.fetchone()
        
        if not site_result:
            flash("Страница не найдена", 'danger')
            return redirect('/urls')
        
        site_url = site_result[0]
    
    try:
        # Выполняем запрос к сайту
        response = requests.get(site_url, timeout=10)
        response.raise_for_status()  # Проверяем статус ответа
        
        # Парсим HTML
        parsed_data = parse_html(response.text)
        
        # Сохраняем проверку в БД
        insert_check_sql = """
            INSERT INTO url_checks 
            (url_id, status_code, h1, title, description, created_at) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        with conn.cursor() as cur:
            cur.execute(insert_check_sql, (
                id,
                response.status_code,
                parsed_data['h1'],
                parsed_data['title'],
                parsed_data['description'],
                date.today()
            ))
            conn.commit()
        
        flash("Страница успешно проверена", 'success')
        
    except Exception:
        # Все исключения обрабатываем одинаково - без деталей
        flash("Произошла ошибка при проверке", 'danger')
    
    return redirect(f'/urls/{id}')


@app.get("/urls")
def show_urls():
    # SQL запрос для получения сайтов с данными о последней проверке
    sql = """
        SELECT 
            u.id, 
            u.name, 
            u.created_at,
            MAX(uc.created_at) as last_check_date,
            (SELECT status_code 
             FROM url_checks 
             WHERE url_id = u.id 
             ORDER BY created_at DESC, id DESC 
             LIMIT 1) as last_status_code
        FROM urls u
        LEFT JOIN url_checks uc ON u.id = uc.url_id
        GROUP BY u.id, u.name, u.created_at
        ORDER BY u.created_at DESC, u.id DESC
    """
    
    with conn.cursor() as cur:
        cur.execute(sql)
        urls = cur.fetchall()
    
    return render_template('urls_info.html', urls=urls)


if __name__ == '__main__':
    app.run()