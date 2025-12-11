import os
from datetime import date

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')


def execute_query(query, params=None, fetch=True, fetchone=False):
    """
    Универсальная функция для выполнения SQL-запросов.
    
    Args:
        query: SQL-запрос
        params: параметры для запроса
        fetch: возвращать ли результат (для SELECT)
        fetchone: возвращать только одну запись
    
    Returns:
        Результат запроса или None
    """
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or ())
            
            # Для SELECT запросов возвращаем результат
            if fetch and query.strip().upper().startswith('SELECT'):
                if fetchone:
                    result = cur.fetchone()
                else:
                    result = cur.fetchall()
            else:
                # Для INSERT/UPDATE/DELETE коммитим
                # если есть RETURNING
                conn.commit()
                query_first_word = query.strip().upper().split()[0]
                if query_first_word in ('INSERT', 'UPDATE', 'DELETE'):
                    if 'RETURNING' in query.upper():
                        result = cur.fetchone()
                    else:
                        result = None
                else:
                    result = None
            
            return result


# Функции для работы с таблицей urls
def find_url_by_name(name):
    """Найти URL по имени"""
    return execute_query(
        "SELECT * FROM urls WHERE name = %s",
        (name,),
        fetchone=True
    )


def find_url_by_id(url_id):
    """Найти URL по ID"""
    return execute_query(
        "SELECT * FROM urls WHERE id = %s",
        (url_id,),
        fetchone=True
    )


def insert_url(name):
    """Добавить новый URL и вернуть его ID"""
    result = execute_query(
        "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id",
        (name, date.today()),
        fetchone=True
    )
    return result['id'] if result else None


def get_all_urls():
    """Получить все URL с информацией о последней проверке"""
    return execute_query("""
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
    """)


# Функции для работы с таблицей url_checks
def get_url_checks(url_id):
    """Получить все проверки для указанного URL"""
    return execute_query(
        "SELECT * FROM url_checks WHERE url_id = %s ORDER BY id DESC",
        (url_id,)
    )


def insert_url_check(url_id, status_code, h1=None,
                     title=None, description=None):
    """Добавить результат проверки URL"""
    execute_query(
        """
        INSERT INTO url_checks 
        (url_id, status_code, h1, title, description, created_at) 
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (url_id, status_code, h1, title, description, date.today()),
        fetch=False
    )