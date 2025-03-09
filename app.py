import streamlit as st
import pandas as pd

# Конфігурація сторінки
st.set_page_config(page_title='Меню харчування', layout='wide')

# Тема (темна/світла)
theme = st.sidebar.radio('🌗 Обери тему:', ['Світла', 'Темна'])
if theme == 'Темна':
    st.markdown("""
    <style>
    .stApp {
        background-color: #121212;
        color: #FFFFFF;
    }
    </style>
    """, unsafe_allow_html=True)

# Завантаження меню
menu = pd.read_csv('Харчування.csv')
menu.dropna(inplace=True)

st.markdown("<h2 style='text-align:center;'>🍽️ Меню для Павла та Наталі 📅</h2>", unsafe_allow_html=True)

# Вибір дня тижня
col_day, col_meal = st.columns(2)
with col_day:
    day = st.selectbox('📅 День тижня:', menu['Дні'].unique())
with col_meal:
    meal_type = st.radio('🥗 Прийом їжі:', ['Всі'] + list(menu['Час прийому їжі'].unique()), horizontal=True)

# Фільтрація меню
filtered_menu = menu[menu['Дні'].str.lower() == day.lower()]
if meal_type != 'Всі':
    filtered_menu = filtered_menu[filtered_menu['Час прийому їжі'] == meal_type]

# Функція витягування калорій
def extract_calories(text):
    import re
    matches = re.findall(r'(\d+)\s?ккал', text)
    return sum(map(int, matches)) if matches else 0

filtered_menu['Калорії (Павло)'] = filtered_menu['Страва (рецепт, калорії, техкарта)'].apply(extract_calories)
filtered_menu['Калорії (Наталя)'] = (filtered_menu['Калорії (Павло)'] * 0.8).astype(int)

# Кольорове кодування калорійності
def calorie_color(value):
    if value < 200:
        return '🟢'
    elif value < 400:
        return '🟡'
    else:
        return '🔴'

# Відображення меню з емодзі
for idx, row in filtered_menu.iterrows():
    emoji = '🍳' if 'Сніданок' in row['Час прийому їжі'] else '🥪' if 'Перекус' in row['Час прийому їжі'] else '🥘'
    with st.expander(f"{emoji} {row['Час прийому їжі']}"):
        st.markdown(f"**📖 Рецепт:** {row['Страва (рецепт, калорії, техкарта)']}")
        st.markdown(f"- 🍽️ **Павло:** {row['Порція для чоловіка']} ({calorie_color(row['Калорії (Павло)'])} {row['Калорії (Павло)']} ккал)")
        st.markdown(f"- 🍽️ **Наталя:** {row['Порція для дружини']} ({calorie_color(row['Калорії (Наталя)'])} {row['Калорії (Наталя)']} ккал)")

# Графіки калорійності
col1, col2 = st.columns(2)

with col1:
    st.subheader('📊 Павло')
    st.bar_chart(filtered_menu.set_index('Час прийому їжі')['Калорії (Павло)'])

with col2:
    st.subheader('📊 Наталя')
    st.bar_chart(filtered_menu.set_index('Час прийому їжі')['Калорії (Наталя)'])
