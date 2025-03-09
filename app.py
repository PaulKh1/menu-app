import streamlit as st
import pandas as pd
import numpy as np
import re
import sqlite3
import bcrypt
import datetime
from sqlalchemy import create_engine, text

# --------------------------------------------------------------------------------
# Налаштування сторінки Streamlit
st.set_page_config(page_title='Меню харчування', layout='wide')

# --------------------------------------------------------------------------------
# Підключення або створення бази даних SQLite
# Створимо engine через SQLAlchemy для зручності
engine = create_engine('sqlite:///food_app.db', echo=False)

# --------------------------------------------------------------------------------
# Функції для роботи з базою даних (користувачі, журнали, тощо)
def create_tables():
    """Створення таблиць, якщо їх ще немає."""
    with engine.connect() as conn:
        # Таблиця користувачів
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash BLOB NOT NULL
        );
        """)
        # Таблиця журналу ваги та активності
        conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATE NOT NULL,
            weight REAL NOT NULL,
            activity INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """)
        # Таблиця для push-нагадувань (демо)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reminder_time TEXT NOT NULL,
            message TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """)

create_tables()  # Створимо таблиці при запуску

def get_user_id(username):
    """Повертає id користувача за username."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id FROM users WHERE username = :u"),
            {"u": username}
        ).fetchone()
    return result[0] if result else None

def create_user(username, password):
    """Створюємо нового користувача, якщо такого немає. Повертає True/False."""
    if not username or not password:
        return False
    with engine.connect() as conn:
        # Перевірити, чи користувач уже існує
        existing = conn.execute(
            text("SELECT username FROM users WHERE username=:u"), 
            {"u": username}
        ).fetchone()
        if existing:
            return False
        
        # Хешуємо пароль
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Додаємо користувача
        conn.execute(
            text("INSERT INTO users (username, password_hash) VALUES (:u, :p)"),
            {"u": username, "p": password_hash}
        )
    return True

def login_user(username, password):
    """Перевіряє логін та пароль. Повертає True/False."""
    if not username or not password:
        return False
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT password_hash FROM users WHERE username=:u"), 
            {"u": username}
        ).fetchone()
    if not row:
        return False
    
    stored_hash = row[0]
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash)

# --------------------------------------------------------------------------------
# Функції для журналу (логів)
def add_log(user_id, date_value, weight_value, activity_value):
    """Додає запис про вагу й активність у таблицю logs."""
    with engine.connect() as conn:
        conn.execute(
            text("""INSERT INTO logs (user_id, date, weight, activity)
                    VALUES (:uid, :d, :w, :a)"""),
            {"uid": user_id, "d": date_value, "w": weight_value, "a": activity_value}
        )

def get_logs(user_id):
    """Отримує усі логи користувача з таблиці logs."""
    with engine.connect() as conn:
        data = conn.execute(
            text("SELECT date, weight, activity FROM logs WHERE user_id=:uid ORDER BY date"),
            {"uid": user_id}
        ).fetchall()
    # Перетворимо у DataFrame
    if data:
        df = pd.DataFrame(data, columns=['Дата', 'Вага', 'Активність'])
        return df
    else:
        return pd.DataFrame(columns=['Дата', 'Вага', 'Активність'])

# --------------------------------------------------------------------------------
# Функції для push-нагадувань (демо-реалізація)
def add_reminder(user_id, reminder_time, message):
    with engine.connect() as conn:
        conn.execute(
            text("""INSERT INTO reminders (user_id, reminder_time, message)
                    VALUES (:uid, :rt, :m)"""),
            {"uid": user_id, "rt": reminder_time, "m": message}
        )

def get_reminders(user_id):
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, reminder_time, message FROM reminders WHERE user_id=:uid"),
            {"uid": user_id}
        ).fetchall()
    if rows:
        df = pd.DataFrame(rows, columns=['ID', 'Час нагадування', 'Повідомлення'])
        return df
    else:
        return pd.DataFrame(columns=['ID', 'Час нагадування', 'Повідомлення'])

def delete_reminder(reminder_id):
    with engine.connect() as conn:
        conn.execute(
            text("DELETE FROM reminders WHERE id=:rid"),
            {"rid": reminder_id}
        )

# --------------------------------------------------------------------------------
# Зчитування меню з CSV
# Припустимо, що файл лежить в одній папці з app.py
@st.cache_data
def load_menu():
    df = pd.read_csv('Харчування.csv', encoding='utf-8-sig').dropna()
    return df

menu_df = load_menu()

# --------------------------------------------------------------------------------
# Допоміжні функції для меню
def extract_calories(text):
    """
    Витягує сумарні калорії з рядка (наприклад, "Омлет 350 ккал" -> 350).
    Якщо таких вказівок кілька, підсумовуємо.
    """
    matches = re.findall(r'(\d+)\s?ккал', text)
    return sum(map(int, matches)) if matches else 0

# --------------------------------------------------------------------------------
# ОТОЖ, ПОЧИНАЄМО ЛОГІКУ ДОДАТКА
def main():
    st.title("🍽️ Персональний додаток харчування, активності та покупок")

    if 'user' not in st.session_state:
        st.session_state['user'] = None
    
    # ----------------------
    # Авторизація / Реєстрація
    st.sidebar.header("🔐 Авторизація / Реєстрація")
    login_mode = st.sidebar.radio("Оберіть дію:", ["Вхід", "Реєстрація"])
    username_input = st.sidebar.text_input("Ім'я користувача:")
    password_input = st.sidebar.text_input("Пароль:", type='password')
    
    if st.sidebar.button("Увійти" if login_mode == "Вхід" else "Зареєструватися"):
        if login_mode == "Вхід":
            if login_user(username_input, password_input):
                st.session_state['user'] = username_input
                st.sidebar.success(f"Ласкаво просимо, {username_input}!")
            else:
                st.sidebar.error("Невірні ім'я користувача або пароль!")
        else:  # Реєстрація
            created = create_user(username_input, password_input)
            if created:
                st.sidebar.success(f"Користувач {username_input} зареєстрований успішно!")
                st.session_state['user'] = username_input
            else:
                st.sidebar.error("Такий користувач вже існує або некоректні дані!")
    
    # Якщо немає авторизованого користувача — припиняємо роботу
    if not st.session_state['user']:
        st.warning("Будь ласка, авторизуйтесь або зареєструйтесь.")
        return
    # -------------------------------------------------------------------------
    # Отримуємо user_id з бази
    user_id = get_user_id(st.session_state['user'])

    # Блок із можливістю вийти
    if st.sidebar.button("Вийти"):
        st.session_state['user'] = None
        st.experimental_rerun()

    # -------------------------------------------------------------------------
    # Бічна панель: Калькулятор ІМТ
    st.sidebar.header("🧮 Калькулятор ІМТ")
    weight_sidebar = st.sidebar.number_input("Вага (кг):", 30.0, 200.0, 80.0)
    height_sidebar = st.sidebar.number_input("Зріст (см):", 100, 220, 170)
    bmi = weight_sidebar / ((height_sidebar / 100)**2)
    st.sidebar.metric("Ваш ІМТ:", f"{bmi:.2f}")

    # -------------------------------------------------------------------------
    # Головні вкладки
    tabs = st.tabs(["Меню та покупки", "Журнал ваги та активності", "Пуш-нагадування"])

    # ========================== 1. МЕНЮ ТА СПИСОК ПОКУПОК =====================
    with tabs[0]:
        st.subheader("Меню та автоматичний список покупок")

        # --- (A) Відображення меню ---
        st.markdown("### Меню з файлу `Харчування.csv`")

        # Можливість вибрати фільтрацію за днем тижня **або** конкретною датою
        # (якщо у CSV є реальні дати у полі 'Дні')
        unique_days = menu_df['Дні'].unique().tolist()

        # Вибір: або ми фільтруємо за днем, або за датою
        day_or_date = st.selectbox("Оберіть день/дату:", unique_days)
        filtered_menu = menu_df[menu_df['Дні'].astype(str).str.lower() == str(day_or_date).lower()]

        # Витягуємо калорійність для кожного запису
        filtered_menu['Калорії (Павло)'] = filtered_menu['Страва (рецепт, калорії, техкарта)'].apply(extract_calories)
        # Можна припустити, що Наталя споживає ~80% калорій від Павла:
        filtered_menu['Калорії (Наталя)'] = (filtered_menu['Калорії (Павло)'] * 0.8).astype(int)

        # Відображення меню
        if filtered_menu.empty:
            st.info("Немає даних на цей день/дату.")
        else:
            for idx, row in filtered_menu.iterrows():
                st.write(f"**{row['Час прийому їжі']}**")
                st.write(f"- Рецепт: {row['Страва (рецепт, калорії, техкарта)']}")
                st.write(f"- Павло: {row['Порція для чоловіка']} ({row['Калорії (Павло)']} ккал)")
                st.write(f"- Наталя: {row['Порція для дружини']} ({row['Калорії (Наталя)']} ккал)")
                st.write("---")

            # Два графіки калорійності
            colA, colB = st.columns(2)
            with colA:
                st.write("#### Калорійність (Павло)")
                st.bar_chart(filtered_menu.set_index('Час прийому їжі')['Калорії (Павло)'])
            with colB:
                st.write("#### Калорійність (Наталя)")
                st.bar_chart(filtered_menu.set_index('Час прийому їжі')['Калорії (Наталя)'])

        # --- (B) Автоматичний список покупок ---
        st.markdown("### Автоматичний список покупок")

        # Вибираємо період, на скільки днів формувати список (від 1 до 7)
        days_count = st.slider("На скільки днів вперед згенерувати список покупок?", 1, 7, 1)

        # Для спрощення у прикладі: якщо у CSV `Дні` - це назви ("Понеділок", "Вівторок"...),
        # то "кілька днів уперед" - це умовна операція.
        # Якщо у CSV є реальні дати, ми можемо інтерпретувати date + days_count.

        # (Демо) Виберемо індекс поточного дня/дати у списку unique_days:
        if day_or_date in unique_days:
            current_index = unique_days.index(day_or_date)
            # Вибір наступних N днів
            selected_days = []
            for i in range(days_count):
                new_index = current_index + i
                if new_index < len(unique_days):
                    selected_days.append(unique_days[new_index])
                else:
                    break
        else:
            selected_days = [day_or_date]

        # Зберемо всі рядки меню, які потрапляють у вибрані дні
        selected_menu = menu_df[menu_df['Дні'].isin(selected_days)]

        # Ідея: нам потрібно аналізувати "Порція для чоловіка" та "Порція для дружини"
        # й "Страва (рецепт, калорії, техкарта)", щоб знайти інгредієнти.
        # Допустімо, що у рядку є фрагменти на зразок: "Молоко 200 мл", "Яйця 2 шт", ...
        # Це ДЕМООБРОБКА: шукаємо патерн "<Назва> <кількість> (г|шт|мл)"
        # Для реального застосування формат CSV має бути жорстко стандартизований.

        def parse_ingredients(text):
            """
            Шукає патерни типу 'Продукт_Слово 123 шт/г/мл'.
            Повертає список кортежів [('Продукт', 123, 'шт'), ...]
            """
            # Ось простий приклад пошуку (укр.+англ. літери, цифри + одиниці).
            pattern = r'([А-Яа-яЇїІіЄєҐґA-Za-z0-9]+)\s(\d+)\s?(шт|г|мл|kg|гр|кг)?'
            found = re.findall(pattern, text)
            # found = [('Яйця', '2', 'шт'), ('Молоко', '200', 'мл'), ...]
            # Приведемо кількість до int
            results = []
            for f in found:
                product_name = f[0]
                qty = int(f[1])
                unit = f[2] if f[2] else ''  # якщо одиниця пуста
                results.append((product_name, qty, unit))
            return results
        
        # Збираємо інгредієнти з усіх стовпців, де може бути текст порцій
        # (з рецепту, з порції для чоловіка, з порції для дружини)
        all_ingredients = {}

        for _, row in selected_menu.iterrows():
            # Обробка рецепту
            ing_recipe = parse_ingredients(str(row['Страва (рецепт, калорії, техкарта)']))
            # Обробка порції для чоловіка
            ing_man = parse_ingredients(str(row['Порція для чоловіка']))
            # Обробка порції для дружини
            ing_woman = parse_ingredients(str(row['Порція для дружини']))
            combined = ing_recipe + ing_man + ing_woman
            
            for (name, qty, unit) in combined:
                key = (name.lower(), unit.lower())  # ключ для унікального продукту+одиниці
                if key not in all_ingredients:
                    all_ingredients[key] = 0
                all_ingredients[key] += qty

        if st.button("Згенерувати список покупок"):
            if not all_ingredients:
                st.warning("Не вдалося знайти продукти у меню. Перевірте формат даних.")
            else:
                st.success("Список покупок сформовано!")
                shop_list = []
                for (name_unit, total_qty) in all_ingredients.items():
                    product_name, product_unit = name_unit
                    if product_unit == '':
                        product_unit = 'шт'  # умовно, якщо не знайдено
                    shop_list.append((product_name.capitalize(), total_qty, product_unit))
                
                df_shop = pd.DataFrame(shop_list, columns=['Продукт', 'Кількість', 'Од.'])
                st.dataframe(df_shop)

    # ===================== 2. ЖУРНАЛ ВАГИ ТА АКТИВНОСТІ =======================
    with tabs[1]:
        st.subheader("Журнал ваги та активності")

        # Форма додавання нового запису
        today = datetime.date.today()
        col1, col2, col3 = st.columns(3)
        with col1:
            date_input = st.date_input("Дата:", today)
        with col2:
            weight_input = st.number_input("Вага (кг):", 30.0, 300.0, 70.0)
        with col3:
            activity_input = st.slider("Активність (хв/день):", 0, 300, 30, 10)

        if st.button("Додати запис"):
            add_log(user_id, date_input, weight_input, activity_input)
            st.success("Запис успішно додано!")

        # Показуємо поточні логи
        logs_df = get_logs(user_id)
        if logs_df.empty:
            st.info("Поки що немає записів у журналі.")
        else:
            st.dataframe(logs_df)

            # Графік ваги (лінійний)
            st.line_chart(data=logs_df.set_index('Дата')['Вага'])
            # Графік активності (стовпчиковий)
            st.bar_chart(data=logs_df.set_index('Дата')['Активність'])

    # ===================== 3. ПУШ-НАГАДУВАННЯ (ДЕМО) =========================
    with tabs[2]:
        st.subheader("Нагадування про прийоми їжі (демо)")
        st.write("**Увага:** для реальних push-повідомлень потрібен зовнішній сервіс (Firebase, Telegram-бот тощо).")

        # Виведемо таблицю існуючих нагадувань
        reminders_df = get_reminders(user_id)
        if not reminders_df.empty:
            st.dataframe(reminders_df)
            # Додавання можливості видаляти нагадування
            reminder_to_delete = st.selectbox("ID нагадування для видалення:", [0] + reminders_df['ID'].tolist())
            if reminder_to_delete != 0:
                if st.button("Видалити обране нагадування"):
                    delete_reminder(reminder_to_delete)
                    st.success("Нагадування видалено!")
                    st.experimental_rerun()
        else:
            st.info("Немає жодного нагадування.")

        # Форма для створення нагадування
        colA, colB = st.columns(2)
        with colA:
            reminder_time = st.time_input("Час нагадування:", datetime.time(8, 0))
        with colB:
            message = st.text_input("Текст повідомлення:", value="Час їсти! 🍽️")

        if st.button("Додати нагадування"):
            # Збережемо в базі
            add_reminder(user_id, str(reminder_time), message)
            st.success("Нагадування додано!")
            st.experimental_rerun()

# Запуск основної функції
if __name__ == "__main__":
    main()
