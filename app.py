import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import re

# Конфігурація сторінки
st.set_page_config(page_title='Меню харчування', layout='wide')

# Підключення до бази даних
conn = sqlite3.connect('menu_app.db')
c = conn.cursor()

# Створення таблиць (якщо їх немає)
c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT UNIQUE, password TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS logs (user TEXT, date DATE, weight REAL, activity INTEGER)''')
conn.commit()

# Функції користувачів
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    c.execute('SELECT username FROM users WHERE username = ?', (username,))
    if c.fetchone():
        return False
    hashed_password = hash_password(password)
    c.execute('INSERT INTO users VALUES (?, ?)', (username, hashed_password))
    conn.commit()
    return True

def login(username, password):
    hashed_password = hash_password(password)
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, hashed_password))
    return c.fetchone()

# Авторизація та реєстрація
st.sidebar.header('🔐 Авторизація')
login_mode = st.sidebar.radio('Оберіть дію:', ['Вхід', 'Реєстрація'])
username = st.sidebar.text_input("Ім'я користувача:")
password = st.sidebar.text_input('Пароль:', type='password')

if st.sidebar.button('Увійти' if login_mode == 'Вхід' else 'Зареєструватися'):
    if login_mode == 'Вхід':
        if login(username, password):
            st.sidebar.success(f'Вхід успішний: {username}')
            st.session_state['user'] = username
        else:
            st.sidebar.error('Неправильний логін або пароль')
    else:
        if create_user(username, password):
            st.sidebar.success(f'Користувача {username} зареєстровано успішно!')
            st.session_state['user'] = username
        else:
            st.sidebar.error('Користувач з таким іменем вже існує!')


    # Завантаження меню
    menu = pd.read_csv('Харчування.csv', encoding='utf-8-sig').dropna()

    selected_day = st.selectbox('📅 День тижня:', menu['Дні'].unique())
    filtered_menu = menu[menu['Дні'].str.lower() == selected_day.lower()]

    def extract_calories(text):
        return sum(map(int, re.findall(r'(\d+)\s?ккал', text)))

    filtered_menu['Калорії (Павло)'] = filtered_menu['Страва (рецепт, калорії, техкарта)'].apply(extract_calories)
    filtered_menu['Калорії (Наталя)'] = (filtered_menu['Калорії (Павло)'] * 0.8).astype(int)

    # Відображення меню
    for _, row in filtered_menu.iterrows():
        with st.expander(f"⏰ {row['Час прийому їжі']}"):
            st.write(f"📖 {row['Страва (рецепт, калорії, техкарта)']}")
            st.write(f"🍽️ Павло: {row['Порція для чоловіка']} ({row['Калорії (Павло)']} ккал)")
            st.write(f"🍽️ Наталя: {row['Порція для дружини']} ({row['Калорії (Наталя)']} ккал)")

    # Журнал ваги та активності
    st.subheader('📝 Журнал ваги та фізичної активності')

    date = st.date_input('📅 Дата запису:')
    weight_log = st.number_input('⚖️ Вага (кг):', 30.0, 200.0, step=0.1)
    activity_log = st.slider('🏃‍♂️ Активність (хв):', 0, 180, 30)

    if st.button('➕ Додати запис'):
        c.execute('INSERT INTO logs (user, date, weight, activity) VALUES (?, ?, ?, ?)', (username, date, weight_log, activity_log))
        conn.commit()
        st.success('✅ Запис додано!')

    # Відображення журналу
    logs_df = pd.read_sql(f"SELECT date as 'Дата', weight as 'Вага', activity as 'Активність' FROM logs WHERE user=?", conn, params=(username,))
    if not logs_df.empty:
        st.dataframe(logs_df)
        st.line_chart(logs_df.set_index('Дата')['Вага'])
        st.bar_chart(logs_df.set_index('Дата')['Активність'])
else:
    st.info('Будь ласка, авторизуйтесь або зареєструйтесь.')
