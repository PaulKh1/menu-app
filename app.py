import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import re
from datetime import datetime, timedelta

# Конфігурація сторінки
st.set_page_config(page_title='Меню харчування', layout='wide')

# Підключення до бази даних
conn = sqlite3.connect('menu_app.db')
c = conn.cursor()

# Створення таблиць
c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT UNIQUE, password TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS logs (user TEXT, date TEXT, weight REAL, activity INTEGER)''')

# Функції користувачів
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    hashed_password = hash_password(password)
    try:
        c.execute('INSERT INTO users VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def login(username, password):
    hashed_password = hash_password(password)
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, hashed_password))
    return c.fetchone()

# Авторизація та реєстрація
st.sidebar.header('🔐 Авторизація')
auth_mode = st.sidebar.radio('Оберіть дію:', ['Вхід', 'Реєстрація'])

username = st.sidebar.text_input('Ім\'я користувача:')
password = st.sidebar.text_input('Пароль:', type='password')

if st.sidebar.button('Підтвердити'):
    if auth_mode == 'Вхід':
        if login(username, password):
            st.session_state['user'] = username
            st.sidebar.success('Успішний вхід!')
        else:
            st.sidebar.error('Невірний логін або пароль')
    else:
        if create_user(username, password):
            st.session_state['user'] = username
            st.sidebar.success('Успішна реєстрація!')
        else:
            st.sidebar.error('Користувач вже існує')

if 'user' in st.session_state:
    st.success(f"Вітаємо, {st.session_state['user']}!")

    # Завантаження меню
    menu = pd.read_csv('Харчування.csv', encoding='utf-8-sig').dropna()

    st.title('🍽️ Меню для Павла та Наталі 📅')
    days_to_show = st.slider('📅 Виберіть кількість днів для меню:', 1, 7, 1)

    base_date = datetime.now()
    dates_list = [(base_date + timedelta(days=i)).strftime('%A') for i in range(days_to_show)]
    filtered_menu = menu[menu['Дні'].isin(dates_list)]

    def extract_calories(text):
        matches = re.findall(r'(\d+)\s?ккал', text)
        return sum(map(int, matches)) if matches else 0

    filtered_menu['Калорії (Павло)'] = filtered_menu['Страва (рецепт, калорії, техкарта)'].apply(extract_calories)
    filtered_menu['Калорії (Наталя)'] = (filtered_menu['Калорії (Павло)'] * 0.8).astype(int)

    for _, row in filtered_menu.iterrows():
        with st.expander(f"⏰ {row['Дні']} - {row['Час прийому їжі']}"):
            st.write(f"📖 {row['Страва (рецепт, калорії, техкарта)']}")
            st.write(f"🍽️ Павло: {row['Порція для чоловіка']} ({row['Калорії (Павло)']} ккал)")
            st.write(f"🍽️ Наталя: {row['Порція для дружини']} ({row['Калорії (Наталя)']} ккал)")

    # Автоматичний список покупок
    st.header('🛒 Автоматичний список покупок')
    if st.button('Сформувати список покупок'):
        ingredients = re.findall(r'(\w+)\s(\d+\s?(г|шт))', ' '.join(filtered_menu['Страва (рецепт, калорії, техкарта)']))
        shopping_list = {}
        for item, quantity, unit in ingredients:
            key = f'{item} ({unit})'
            shopping_list[key] = shopping_list.get(key, 0) + int(re.findall(r'\d+', quantity)[0])
        st.write(shopping_list)

    # Калькулятор ІМТ
    st.sidebar.header('🧮 Калькулятор ІМТ')
    weight = st.sidebar.number_input('Вага (кг):', 30.0, 200.0, 80.0)
    height = st.sidebar.number_input('Зріст (см):', 100, 220, 173)
    bmi = weight / ((height / 100)**2)
    st.sidebar.metric('📌 Твій ІМТ:', f'{bmi:.2f}')
else:
    st.warning('Будь ласка, авторизуйтесь або зареєструйтесь через бокову панель.')
