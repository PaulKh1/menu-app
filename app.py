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

# Стан авторизації
if 'user' not in st.session_state:
    st.session_state['user'] = None

# Авторизація та реєстрація
st.sidebar.header('🔐 Авторизація')
auth_mode = st.sidebar.radio('Оберіть дію:', ['Вхід', 'Реєстрація'])

username = st.sidebar.text_input('Ім\'я користувача:')
password = st.sidebar.text_input('Пароль:', type='password')

if st.sidebar.button('Підтвердити'):
    if login(username, password) if login_mode == 'Вхід' else create_user(username, password):
        st.session_state['user'] = username
        st.sidebar.success('Успішно!')
    else:
        st.sidebar.error('Помилка авторизації або реєстрації')

if 'user' in st.session_state:
    st.success(f"Вітаємо, {st.session_state['user']}!")

    # Завантаження меню
    menu = pd.read_csv('Харчування.csv', encoding='utf-8-sig').dropna()

    st.title('🍽️ Меню для Павла та Наталі 📅')
    selected_day = st.selectbox('📅 День тижня:', menu['Дні'].unique())
    filtered_menu = menu[menu['Дні'] == selected_day]

    def extract_calories(text):
        matches = re.findall(r'(\d+)\s?ккал', text)
        return sum(map(int, matches)) if matches else 0

    filtered_menu['Калорії (Павло)'] = filtered_menu['Страва (рецепт, калорії, техкарта)'].apply(extract_calories)
    filtered_menu['Калорії (Наталя)'] = (filtered_menu['Калорії (Павло)'] * 0.8).astype(int)

    for _, row in filtered_menu.iterrows():
        with st.expander(f"⏰ {row['Час прийому їжі']}"):
            st.write(f"📖 {row['Страва (рецепт, калорії, техкарта)']}")
            st.write(f"🍽️ Павло: {row['Порція для чоловіка']} ({row['Калорії (Павло)']} ккал)")
            st.write(f"🍽️ Наталя: {row['Порція для дружини']} ({row['Калорії (Наталя)']} ккал)")

    # Калькулятор ІМТ
    st.sidebar.header('🧮 Калькулятор ІМТ')
    weight = st.sidebar.number_input('Вага (кг):', 30.0, 200.0, 80.0)
    height = st.sidebar.number_input('Зріст (см):', 100, 220, 173)
    bmi = weight / ((height / 100)**2)
    st.sidebar.metric('📌 Твій ІМТ:', f'{bmi:.2f}')

    # Журнал ваги та активності
    st.subheader('📝 Журнал ваги та активності')

    date = st.date_input('📅 Дата')
    weight_log = st.number_input('⚖️ Вага (кг)', 30.0, 200.0, step=0.1)
    activity_log = st.slider('🏃‍♂️ Активність (хв)', 0, 180, 30)

    if st.button('✅ Додати запис'):
        c.execute('INSERT INTO logs VALUES (?, ?, ?, ?)', (st.session_state['user'], date.isoformat(), weight_log, activity_log))
        conn.commit()
        st.success('✅ Запис додано!')

    logs_df = pd.read_sql('SELECT date AS Дата, weight AS Вага, activity AS Активність FROM logs WHERE user=?', conn, params=(st.session_state['user'],))
    if not logs_df.empty:
        st.dataframe(logs_df)
        st.line_chart(logs_df.set_index('Дата')['Вага'])
        st.bar_chart(logs_df.set_index('Дата')['Активність'])

else:
    st.warning('Будь ласка, авторизуйтесь або зареєструйтесь через бокову панель.')
