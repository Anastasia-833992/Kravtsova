import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime
from functools import partial

class CurrencyConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Currency Converter - Конвертер валют")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # API настройки (бесплатный API без ключа)
        self.api_url = "https://api.exchangerate-api.com/v4/latest/"
        
        # Файл для истории
        self.history_file = "conversion_history.json"
        
        # Загрузка истории
        self.history = self.load_history()
        
        # Данные о курсах валют
        self.currencies = []
        self.exchange_rates = {}
        
        # Создание интерфейса
        self.create_widgets()
        
        # Загрузка доступных валют
        self.load_currencies()
        
        # Обновление истории
        self.refresh_history()
        
    def load_history(self):
        """Загрузка истории из JSON файла"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as file:
                    return json.load(file)
            except (json.JSONDecodeError, IOError):
                return []
        return []
    
    def save_history(self):
        """Сохранение истории в JSON файл"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as file:
                json.dump(self.history, file, ensure_ascii=False, indent=2)
            return True
        except IOError:
            messagebox.showerror("Ошибка", "Не удалось сохранить историю!")
            return False
    
    def load_currencies(self):
        """Загрузка доступных валют из API"""
        try:
            # Используем USD как базовую валюту для получения списка
            response = requests.get(f"{self.api_url}USD", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            self.exchange_rates = data.get("rates", {})
            self.currencies = sorted(self.exchange_rates.keys())
            
            # Обновление выпадающих списков
            self.update_currency_lists()
            
            self.update_status("Курсы валют успешно загружены")
        except requests.RequestException as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить курсы валют:\n{str(e)}")
            # Используем резервный список валют
            self.currencies = ["USD", "EUR", "GBP", "JPY", "CNY", "RUB", "CAD", "AUD", "CHF"]
            self.update_currency_lists()
            self.update_status("Используется резервный список валют")
    
    def update_currency_lists(self):
        """Обновление выпадающих списков валют"""
        if hasattr(self, 'from_currency_combo') and hasattr(self, 'to_currency_combo'):
            current_from = self.from_currency_var.get()
            current_to = self.to_currency_var.get()
            
            self.from_currency_combo['values'] = self.currencies
            self.to_currency_combo['values'] = self.currencies
            
            # Восстановление предыдущих значений, если они есть в новом списке
            if current_from in self.currencies:
                self.from_currency_var.set(current_from)
            else:
                self.from_currency_var.set("USD")
                
            if current_to in self.currencies:
                self.to_currency_var.set(current_to)
            else:
                self.to_currency_var.set("EUR")
    
    def create_widgets(self):
        """Создание всех элементов интерфейса"""
        # Основной фрейм для конвертации
        main_frame = ttk.LabelFrame(self.root, text="Конвертация валют", padding=15)
        main_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Фрейм для выбора валют
        currencies_frame = ttk.Frame(main_frame)
        currencies_frame.pack(fill=tk.X, pady=5)
        
        # Из какой валюты
        ttk.Label(currencies_frame, text="Из валюты:", font=("Arial", 10)).grid(row=0, column=0, padx=5, sticky=tk.W)
        self.from_currency_var = tk.StringVar(value="USD")
        self.from_currency_combo = ttk.Combobox(currencies_frame, textvariable=self.from_currency_var, 
                                                values=self.currencies, width=10, state="readonly")
        self.from_currency_combo.grid(row=0, column=1, padx=5, pady=5)
        self.from_currency_combo.bind('<<ComboboxSelected>>', lambda e: self.get_exchange_rate())
        
        # В какую валюту
        ttk.Label(currencies_frame, text="В валюту:", font=("Arial", 10)).grid(row=0, column=2, padx=5, sticky=tk.W)
        self.to_currency_var = tk.StringVar(value="EUR")
        self.to_currency_combo = ttk.Combobox(currencies_frame, textvariable=self.to_currency_var,
                                              values=self.currencies, width=10, state="readonly")
        self.to_currency_combo.grid(row=0, column=3, padx=5, pady=5)
        self.to_currency_combo.bind('<<ComboboxSelected>>', lambda e: self.get_exchange_rate())
        
        # Фрейм для ввода суммы
        amount_frame = ttk.Frame(main_frame)
        amount_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(amount_frame, text="Сумма:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.amount_entry = ttk.Entry(amount_frame, width=20, font=("Arial", 10))
        self.amount_entry.pack(side=tk.LEFT, padx=5)
        self.amount_entry.bind('<Return>', lambda e: self.convert_currency())
        
        # Текущий курс
        self.rate_label = ttk.Label(amount_frame, text="", font=("Arial", 9, "italic"), foreground="blue")
        self.rate_label.pack(side=tk.LEFT, padx=20)
        
        # Кнопки действий
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Конвертировать", command=self.convert_currency,
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Очистить поля", command=self.clear_fields,
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Обновить курсы", command=self.load_currencies,
                  width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Очистить историю", command=self.clear_history,
                  width=15).pack(side=tk.LEFT, padx=5)
        
        # Результат конвертации
        result_frame = ttk.Frame(main_frame)
        result_frame.pack(fill=tk.X, pady=10)
        
        self.result_label = ttk.Label(result_frame, text="", font=("Arial", 12, "bold"), foreground="green")
        self.result_label.pack()
        
        # История конвертаций
        history_frame = ttk.LabelFrame(self.root, text="История конвертаций", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Таблица истории
        columns = ("Дата", "Время", "Сумма", "Из", "В", "Результат", "Курс")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=12)
        
        # Настройка колонок
        col_widths = {"Дата": 100, "Время": 80, "Сумма": 100, "Из": 60, "В": 60, "Результат": 120, "Курс": 100}
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=col_widths.get(col, 100), anchor=tk.CENTER if col not in ["Дата", "Время"] else tk.W)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Статус бар
        self.status_bar = ttk.Label(self.root, text="Готов к работе", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def get_exchange_rate(self):
        """Получение текущего курса обмена"""
        try:
            from_currency = self.from_currency_var.get()
            to_currency = self.to_currency_var.get()
            
            response = requests.get(f"{self.api_url}{from_currency}", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            rates = data.get("rates", {})
            rate = rates.get(to_currency, 1)
            
            self.rate_label.config(text=f"1 {from_currency} = {rate:.4f} {to_currency}")
            return rate
        except requests.RequestException:
            self.rate_label.config(text="Не удалось получить курс")
            return None
    
    def convert_currency(self):
        """Конвертация валюты"""
        # Получение и проверка суммы
        try:
            amount = float(self.amount_entry.get().strip())
            if amount <= 0:
                messagebox.showwarning("Предупреждение", "Сумма должна быть положительным числом!")
                return
        except ValueError:
            messagebox.showwarning("Предупреждение", "Пожалуйста, введите корректную сумму!")
            return
        
        # Получение курса
        rate = self.get_exchange_rate()
        if rate is None:
            messagebox.showerror("Ошибка", "Не удалось получить курс обмена!")
            return
        
        # Конвертация
        from_currency = self.from_currency_var.get()
        to_currency = self.to_currency_var.get()
        result = amount * rate
        
        # Отображение результата
        result_text = f"{amount:.2f} {from_currency} = {result:.2f} {to_currency}"
        self.result_label.config(text=result_text)
        
        # Сохранение в историю
        now = datetime.now()
        history_entry = {
            "timestamp": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "result": round(result, 2),
            "rate": round(rate, 4)
        }
        
        self.history.append(history_entry)
        self.save_history()
        self.refresh_history()
        
        self.update_status(f"Конвертация выполнена: {result_text}")
        
    def refresh_history(self):
        """Обновление таблицы истории"""
        # Очистка текущей таблицы
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Отображение истории (последние 50 записей для производительности)
        for entry in reversed(self.history[-50:]):
            self.history_tree.insert("", 0, values=(
                entry["date"],
                entry["time"],
                f"{entry['amount']:.2f}",
                entry["from_currency"],
                entry["to_currency"],
                f"{entry['result']:.2f}",
                f"{entry['rate']:.4f}"
            ))
        
        self.update_status(f"Загружено {len(self.history)} записей в истории")
    
    def clear_fields(self):
        """Очистка полей ввода и результата"""
        self.amount_entry.delete(0, tk.END)
        self.result_label.config(text="")
        self.rate_label.config(text="")
        self.amount_entry.focus()
        self.update_status("Поля очищены")
    
    def clear_history(self):
        """Очистка истории конвертаций"""
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить всю историю?"):
            self.history = []
            self.save_history()
            self.refresh_history()
            self.update_status("История очищена")
    
    def update_status(self, message):
        """Обновление статусной строки"""
        self.status_bar.config(text=message)
        # Автоматическая очистка статуса через 3 секунды
        self.root.after(3000, lambda: self.status_bar.config(text="Готов к работе"))

def main():
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()

if __name__ == "__main__":
    main()