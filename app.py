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
calories_man = filtered_menu['Порція для чоловіка'].str.extract(r'(\d+)').astype(float)
calories_woman = filtered_menu['Порція для дружини'].str.extract(r'(\d+)').astype(float)

st.bar_chart(pd.DataFrame({
    'Чоловік': calories_man[0],
    'Дружина': calories_woman[0]
}, index=filtered_menu['Час прийому їжі']))
