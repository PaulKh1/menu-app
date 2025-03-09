import streamlit as st
import pandas as pd

st.set_page_config(page_title='Меню харчування', layout='wide')

# Завантаження меню
menu = pd.read_csv('Харчування.csv')
menu.dropna(inplace=True)

# Адаптивний заголовок
st.markdown("<h2 style='text-align:center;'>🍽️ Меню для Павла та Наталі 📅</h2>", unsafe_allow_html=True)

# Вибір дня тижня
day = st.selectbox('📅 Обери день тижня:', menu['Дні'].unique())

# Вибір прийому їжі
meal_type = st.radio('🥗 Тип прийому їжі:', ['Всі'] + list(menu['Час прийому їжі'].unique()), horizontal=True)

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

# Відображення меню у зручному форматі
for idx, row in filtered_menu.iterrows():
    with st.expander(f"⏰ {row['Час прийому їжі']}"):
        st.markdown(f"**📖 Рецепт:** {row['Страва (рецепт, калорії, техкарта)']}")
        st.markdown(f"- 🍽️ **Порція для Павла:** {row['Порція для чоловіка']} ({row['Калорії (Павло)']} ккал)")
        st.markdown(f"- 🍽️ **Порція для Наталі:** {row['Порція для дружини']} ({row['Калорії (Наталя)']} ккал)")

# Компактні графіки для смартфона
col1, col2 = st.columns(2)

with col1:
    st.subheader('📊 Павло')
    st.bar_chart(filtered_menu.set_index('Час прийому їжі')['Калорії (Павло)'])

with col2:
    st.subheader('📊 Наталя')
    st.bar_chart(filtered_menu.set_index('Час прийому їжі')['Калорії (Наталя)'])
