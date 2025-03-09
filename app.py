import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Конфігурація сторінки
st.set_page_config(page_title='Меню харчування', layout='wide')

# Вибір теми
st.sidebar.header('Налаштування')
theme = st.sidebar.radio('🌗 Обери тему:', ['Світла', 'Темна'])
if theme == 'Темна':
    st.markdown("""
    <style>
        .main {background-color: #0e1117; color: white;}
    </style>
    """, unsafe_allow_html=True)

# Завантаження меню
menu = pd.read_csv('Харчування.csv', encoding='utf-8-sig').dropna()

st.title('🍽️ Меню для Павла та Наталі 📅')

# Вибір дня тижня
selected_day = st.selectbox('📅 День тижня:', menu['Дні'].unique())

# Фільтрація меню
filtered_menu = menu[menu['Дні'].str.lower() == selected_day.lower()]

# Функція для витягування калорій
def extract_calories(text):
    import re
    matches = re.findall(r'(\d+)\s?ккал', text)
    return sum(map(int, matches)) if matches else 0

filtered_menu['Калорії (Павло)'] = filtered_menu['Страва (рецепт, калорії, техкарта)'].apply(extract_calories)
filtered_menu['Калорії (Наталя)'] = (filtered_menu['Калорії (Павло)'] * 0.8).astype(int)

# Відображення меню з фото
for _, row in filtered_menu.iterrows():
    emoji = '🍳' if 'Сніданок' in row['Час прийому їжі'] else ('🍲' if 'Обід' in row['Час прийому їжі'] else '🥗')
    with st.expander(f"{emoji} {row['Час прийому їжі']}"):
        st.write(f"**Рецепт:** {row['Страва (рецепт, калорії, техкарта)']}")
        st.write(f"**Павло:** {row['Порція для чоловіка']} ({row['Калорії (Павло)']} ккал)")
        st.write(f"**Наталя:** {row['Порція для дружини']} ({row['Калорії (Наталя)']} ккал)")
        photo = st.file_uploader(f'Завантаж фото страви ({row["Час прийому їжі"]})', type=['png', 'jpg'])
        if photo:
            st.image(photo)

# Окремі графіки калорійності
col1, col2 = st.columns(2)
with col1:
    st.subheader('📊 Павло')
    st.bar_chart(filtered_menu.set_index('Час прийому їжі')['Калорії (Павло)'])

with col2:
    st.subheader('📊 Наталя')
    st.bar_chart(filtered_menu.set_index('Час прийому їжі')['Калорії (Наталя)'])

# Калькулятор ІМТ
st.sidebar.header('🧮 Калькулятор ІМТ')
weight = st.sidebar.number_input('Вага (кг):', 30.0, 200.0, 80.0)
height = st.sidebar.number_input('Зріст (см):', 100, 220, value=173)
bmi = weight / ((height / 100)**2)
st.sidebar.metric('📌 Твій ІМТ:', f'{bmi:.2f}')

# Журнал ваги та фізичної активності
st.header('📝 Журнал ваги та активності')

if 'log_df' not in st.session_state:
    st.session_state['log_df'] = pd.DataFrame(columns=['Дата', 'Вага', 'Активність'])

col1, col2, col3 = st.columns(3)
with col1:
    date = st.date_input('📅 Дата')

with col2:
    weight_log = st.number_input('⚖️ Вага (кг)', 30.0, 200.0, step=0.1)

with col3:
    activity_log = st.slider('🏃‍♂️ Активність (хв)', 0, 180, 30, 10)

if st.button('✅ Додати запис'):
    new_log = pd.DataFrame([{
        'Дата': pd.to_datetime(date),
        'Вага': weight_log,
        'Активність': activity_log
    }])
    st.session_state.log_df = pd.concat([st.session_state.log_df, new_log], ignore_index=True)
    st.success('Запис додано!')

# Показуємо записи
if not st.session_state.log_df.empty:
    st.dataframe(st.session_state.log_df)
    st.line_chart(st.session_state.log_df.set_index('Дата')['Вага'])
    st.bar_chart(st.session_state.log_df.set_index('Дата')['Активність'])

# Список покупок
st.header('🛒 Автоматичний список покупок на тиждень')
if st.button('📝 Створити список покупок'):
    products = filtered_menu['Страва (рецепт, калорії, техкарта)'].str.extractall(r'([А-Яа-яЇїІіЄєҐґ\w]+) \d+ ?г?').drop_duplicates()[0]
    st.write(products.tolist())

# Push-сповіщення
st.sidebar.header('🔔 Push-сповіщення про прийоми їжі')
notify = st.sidebar.checkbox('Активувати нагадування')
if notify:
    meal_times = filtered_menu['Час прийому їжі'].tolist()
    for time in meal_times:
        st.sidebar.info(f'Не забудь про {time}!')
