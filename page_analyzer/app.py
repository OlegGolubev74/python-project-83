from flask import Flask, render_template, request, redirect, url_for


from dotenv import load_dotenv

import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/analyze", methods=['POST'])
def analyze():
    url = request.form.get('url')  # Получаем URL из формы
    # Здесь будет логика анализа URL (пока просто редирект)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()