"""
CurRate - Конвертер валют с курсами ЦБ РФ
"""

import tkinter as tk
from tkinter import ttk
from tkcalendar import Calendar
from datetime import datetime
import pyperclip
import locale
import requests
from bs4 import BeautifulSoup

# Установка русской локали для корректного отображения даты
locale.setlocale(locale.LC_ALL, 'ru_RU')

def get_currency_rate(currency, date):
    """Получение курса валюты с сайта ЦБ РФ на указанную дату."""
    try:
        url = f"https://cbr.ru/currency_base/daily/?UniDbQuery.Posted=True&UniDbQuery.To={date}"
        response = requests.get(url)
        response.raise_for_status()  # Проверка на ошибки HTTP

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='data')
        if not table:
            return None

        for row in table.find_all('tr')[1:]:
            cols = row.find_all('td')
            if cols[1].text.strip() == currency:
                return float(cols[4].text.strip().replace(',', '.'))
    except Exception as e:
        print(f"Ошибка при получении курса валюты: {e}")
        return None

def copy_to_clipboard(text):
    """Копирование текста в буфер обмена."""
    pyperclip.copy(text)

def show_result():
    """Расчет и отображение результата конвертации."""
    date = date_entry.get()
    if not validate_date(date):
        return

    currency = currency_var.get()
    amount_str = amount_entry.get().replace(',', '.')
    if not validate_amount(amount_str):
        return

    amount = float(amount_str)
    rate = get_currency_rate(currency, date)
    if rate is None:
        result_label.config(text="Ошибка: не удалось получить курс валюты")
        return

    display_result(amount, rate, currency)

def validate_date(date):
    """Проверка корректности введенной даты."""
    try:
        if datetime.strptime(date, '%d.%m.%Y') > datetime.now():
            result_label.config(text="Ошибка: Дата превышает текущую!")
            return False
    except ValueError:
        result_label.config(text="Ошибка: Некорректный формат даты")
        return False
    return True

def validate_amount(amount_str):
    """Проверка корректности введенной суммы."""
    try:
        float(amount_str)
    except ValueError:
        result_label.config(text="Ошибка: некорректное значение суммы")
        return False
    return True

def display_result(amount, rate, currency):
    """Отображение результата конвертации."""
    result_in_rub = amount * rate
    currency_symbol = "$" if currency == "USD" else "€"
    result_str = f"{result_in_rub:,.2f} руб. ({currency_symbol}{amount:,.2f} по курсу {rate:,.4f})"
    result_str = result_str.replace(',', ' ').replace('.', ',').replace('руб,', 'руб.')
    result_label.config(text=result_str)
    copy_button.config(command=lambda: copy_to_clipboard(result_label.cget("text")))

def grab_date():
    """Обновление поля ввода даты при выборе в календаре."""
    date_entry.delete(0, tk.END)
    date_entry.insert(0, cal.get_date())

def main():
    """Главная функция запуска приложения."""
    global root, date_entry, cal, currency_var, amount_entry, result_label, copy_button

    # Настройка главного окна приложения
    root = tk.Tk()
    root.title("Конвертер валют (с) BiV 2024 г.")
    root.minsize(340, 455)

    # Создание и расположение виджетов
    tk.Label(root, text="Дата:").pack()
    date_entry = ttk.Entry(root)
    today_date = datetime.now().strftime('%d.%m.%Y')
    date_entry.insert(0, today_date)
    date_entry.pack()

    cal = Calendar(root, selectmode='day', locale='ru_RU', date_pattern='dd.mm.yyyy')
    cal.pack(pady=20)
    cal.bind("<<CalendarSelected>>", lambda event: grab_date())

    tk.Label(root, text="Выберите валюту:").pack()
    currency_var = tk.StringVar(value="USD")
    ttk.Radiobutton(root, text="USD", variable=currency_var, value="USD").pack()
    ttk.Radiobutton(root, text="EUR", variable=currency_var, value="EUR").pack()

    tk.Label(root, text="Введите сумму:").pack()
    amount_entry = ttk.Entry(root, width=27)
    amount_entry.pack()

    style = ttk.Style()
    style.configure("Large.TButton", font=("TkDefaultFont", 10), padding=10)

    convert_button = ttk.Button(root, text="Конвертировать", command=show_result, style="Large.TButton")
    convert_button.pack(pady=10)
    convert_button.config(width=20)

    result_label = ttk.Label(root, text="Укажите дату и сумму конвертации", font=("TkDefaultFont", 10, "bold"))
    result_label.pack()

    copy_button = ttk.Button(root, text="Копировать в буфер", style="Large.TButton")
    copy_button.pack(pady=10)
    copy_button.config(width=20)

    root.mainloop()

if __name__ == "__main__":
    main()
