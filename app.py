import streamlit as st
import pandas as pd

# Завантаження меню з Excel
menu = pd.read_excel('Харчування.xlsx')
menu.dropna(inplace=True)

# Налаштування додатку Streamlit
st.title('📝 Інтерактивне меню харчування на тиждень')

# Вибір дня тижня
day = st.selectbox('Обери день тижня:', menu['Дні'].unique())

# Вибір типу прийому їжі
meal_time = st.selectbox('Тип прийому їжі:', ['Всі'] + list(menu['Час прийому їжі'].unique()))

# Фільтрація за днем і типом прийому їжі
filtered_menu = menu[menu['Дні'].str.lower() == day.lower()]
if meal_time != 'Всі':
    filtered_menu = filtered_menu[filtered_menu['Час прийому їжі'] == meal_time]

# Відображення меню
st.subheader(f'🍽️ Меню на {day}')
st.dataframe(filtered_menu[['Час прийому їжі', 'Страва (рецепт, калорії, техкарта)', 'Порція для чоловіка', 'Порція для дружини']])

# Редагування меню
st.subheader('✏️ Редагувати меню')
edited_menu = st.data_editor(filtered_menu)

# Графік калорійності
st.subheader('📊 Калорійність страв')
# Функція для витягування калорій з тексту
def extract_calories(text):
    import re
    matches = re.findall(r'(\d+)\s?ккал', text)
    return sum(map(int, matches)) if matches else 0

# Підрахунок калорій для Павла та Наталі
filtered_menu['Калорії (Павло)'] = filtered_menu['Страва (рецепт, калорії, техкарта)'].apply(extract_calories)
filtered_menu['Калорії (Наталя)'] = (filtered_menu['Калорії (Павло)'] * 0.8).astype(int)

# Відображення меню з калоріями
st.dataframe(filtered_menu[['Час прийому їжі', 'Страва (рецепт, калорії, техкарта)', 'Калорії (Павло)', 'Калорії (Наталя)']])

# Графік для Павла
st.subheader('📊 Калорійність страв (Павло)')
st.bar_chart(filtered_menu.set_index('Час прийому їжі')['Калорії (Павло)'])

# Графік для Наталі
st.subheader('📊 Калорійність страв (Наталя)')
st.bar_chart(filtered_menu.set_index('Час прийому їжі')['Калорії (Наталя)'])

