import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import re

# Конфігурація сторінки
st.set_page_config(page_title='Меню харчування', layout='wide')

# Ініціалізація бази даних
import sqlite3
conn = sqlite3.connect('menu_app.db')
c = conn.cursor()

# Створення таблиць
c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS logs (user TEXT, date TEXT, weight REAL, activity INTEGER)''')
conn.commit()

# Функції для користувачів
def create_user(username, password):
    c.execute('INSERT INTO users VALUES (?, ?)', (username, password))
    conn.commit()

def login(username, password):
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    return c.fetchone()

# Авторизація
st.sidebar.header('🔐 Авторизація')
username = st.sidebar.text_input('Ім\'я користувача')
password = st.sidebar.text_input('Пароль', type='password')

if st.sidebar.button('Увійти'):
    user = login(username, password)
    if user:
        st.sidebar.success(f'Вхід успішний: {username}')
        st.session_state['user'] = username
    else:
        st.sidebar.error('Неправильний логін або пароль')

if 'user' in st.session_state:
    # Вибір теми
    theme = st.sidebar.radio('🌗 Обери тему:', ['Світла', 'Темна'])

    # Завантаження меню
    menu = pd.read_csv('Харчування.csv', encoding='utf-8-sig').dropna()

    st.title('🍽️ Меню для Павла та Наталі 📅')

    # Вибір дня тижня
    selected_day = st.selectbox('📅 День тижня:', menu['Дні'].unique())

    # Фільтрація меню
    filtered_menu = menu[menu['Дні'].str.lower() == selected_day.lower()]

    # Витяг калорій
    def extract_calories(text):
        matches = re.findall(r'(\d+)\s?ккал', text)
        return sum(map(int, matches)) if matches else 0

    filtered_menu['Калорії (Павло)'] = filtered_menu['Страва (рецепт, калорії, техкарта)'].apply(extract_calories)
    filtered_menu['Калорії (Наталя)'] = (filtered_menu['Калорії (Павло)'] * 0.8).astype(int)

    # Відображення меню
    for _, row in filtered_menu.iterrows():
        with st.expander(f"⏰ {row['Час прийому їжі']}"):
            st.write(f"**📖 Рецепт:** {row['Страва (рецепт, калорії, техкарта)']}")
            st.write(f"🍽️ **Павло:** {row['Порція для чоловіка']} ({row['Калорії (Павло)']} ккал)")
            st.write(f"🍽️ **Наталя:** {row['Порція для дружини']} ({row['Калорії (Наталя)']} ккал)")

    # Графіки калорійності
    col1, col2 = st.columns(2)
    with col1:
        st.subheader('📊 Павло')
        st.bar_chart(filtered_menu.set_index('Час прийому їжі')['Калорії (Павло)'])

    with col2:
        st.subheader('📊 Наталя')
        st.bar_chart(filtered_menu.set_index('Час прийому їжі')['Калорії (Наталя)'])

    # Журнал ваги та фізичної активності
    st.header('📝 Журнал ваги та фізичної активності')

    date = st.date_input('📅 Дата запису:')
    weight_log = st.number_input('⚖️ Вага (кг):', 30.0, 200.0, step=0.1)
    activity_log = st.slider('🏃‍♂️ Фізична активність (хв/день):', 0, 180, step=10)

    if st.button('➕ Додати запис'):
        c.execute('INSERT INTO activity_logs (user, date, weight, activity) VALUES (?, ?, ?, ?)', (st.session_state['user'], date, weight_log, activity_log))
        conn.commit()
        st.success('✅ Запис додано!')

    # Відображення записів користувача
    logs_df = pd.read_sql(f"SELECT date, weight, activity FROM logs WHERE user='{st.session_state['user']}'", conn)
    if not logs.empty:
        st.dataframe(logs)
        st.line_chart(log_df.set_index('Дата')['Вага'])
        st.bar_chart(log_df.set_index('Дата')['Активність'])
else:
    st.info('Будь ласка, авторизуйтесь через бокову панель.')
