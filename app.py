import streamlit as st
import pandas as pd
import numpy as np
import re

# Конфігурація сторінки
st.set_page_config(page_title='Меню харчування', layout='wide')

# Вибір теми (світла/темна)
theme = st.sidebar.radio('🌗 Обери тему:', ['Світла', 'Темна'])

# Завантаження меню
menu = pd.read_csv('Харчування.csv', encoding='utf-8-sig')
menu.dropna(inplace=True)

st.title('🍽️ Меню для Павла та Наталі 📅')

# Вибір дня тижня
selected_day = st.selectbox('📅 День тижня:', menu['Дні'].unique())

# Фільтрація меню
filtered_menu = menu[menu['Дні'].str.lower() == selected_day.lower()]

# Функція витягування калорій
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

# Інтерактивний калькулятор ІМТ
st.sidebar.subheader('🧮 Калькулятор ІМТ')
weight = st.sidebar.number_input('Вага (кг):', min_value=30.0, max_value=200.0, value=70.0)
height = st.sidebar.number_input('Зріст (см):', min_value=100, max_value=220, value=170)
bmi = weight / ((height / 100)**2)
st.sidebar.write(f'🧍 Твій ІМТ: {bmi:.1f}')

# Журнал ваги та фізичної активності
st.header('📝 Журнал ваги та фізичної активності')

if 'log_df' not in st.session_state:
    st.session_state['log_df'] = pd.DataFrame(columns=['Дата', 'Вага', 'Активність'])

date = st.date_input('📅 Дата запису:')
weight_log = st.number_input('⚖️ Вага (кг):', 30.0, 200.0, step=0.1)
activity_log = st.slider('🏃‍♂️ Фізична активність (хв/день):', 0, 180, step=10)

if st.button('➕ Додати запис'):
    new_record = {'Дата': pd.to_datetime(date), 'Вага': weight_log, 'Активність': activity_log}
    st.session_state.log_df = pd.concat([st.session_state.log_df, pd.DataFrame([new_record])], ignore_index=True)
    st.success('✅ Запис додано!')

if not st.session_state.log_df.empty:
    st.dataframe(st.session_state.log_df)
    st.line_chart(st.session_state.log_df.set_index('Дата')['Вага'])
    st.bar_chart(st.session_state.log_df.set_index('Дата')['Активність'])

# Автоматичний список покупок
st.subheader('🛒 Автоматичний список покупок')
days_selection = st.multiselect('📅 Обери дні для списку покупок:', menu['Дні'].unique(), default=[selected_day])
if st.button('📝 Сформувати список покупок'):
    selected_days_menu = menu[menu['Дні'].isin(days_selection)]
    all_ingredients = ' '.join(selected_days_menu['Страва (рецепт, калорії, техкарта)'])
    products = re.findall(r'([А-Яа-яЇїІіЄєҐґ\w]+)\s(\d+)\s?(г|шт)', all_ingredients)
    shopping_list = {}
    for product, amount, unit in products:
        key = f'{product} ({unit})'
        shopping_list[key] = shopping_list.get(key, 0) + int(amount)
    for product, total in shopping_list.items():
        st.write(f'- {product}: {total}')
