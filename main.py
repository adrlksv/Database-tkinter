import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
import re

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Запросы")

        self.create_widgets()
        self.load_city_codes()
        self.execute_query()  # Выполнить запрос "Вывести всех контрагентов" при запуске

    def create_widgets(self):
        # Верхняя панель для ввода запросов
        self.top_frame = ttk.Frame(self.root)
        self.top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.query_combo = ttk.Combobox(self.top_frame, values=[
            "Вывести уникальные города контрагентов",
            "Вывести всех контрагентов",
            "Вывести контрагентов с городами",
            "Вывести контрагентов из Москвы",
            "Вывести контрагентов из того же города, что и контрагент с номером 2",
            "Вывести всех поставщиков"
        ], state="readonly")  # Запрет на ручной ввод
        self.query_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.execute_button = ttk.Button(self.top_frame, text="Выполнить", command=self.execute_query)
        self.execute_button.pack(side=tk.LEFT, padx=5)

        # Поле для отображения результатов запросов
        self.tree_frame = ttk.Frame(self.root)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(self.tree_frame)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Добавление горизонтального скроллбара
        self.tree_scroll_x = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree_scroll_x.pack(side="bottom", fill="x")
        self.tree.configure(xscrollcommand=self.tree_scroll_x.set)

        # Добавление вертикального скроллбара
        self.tree_scroll_y = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree_scroll_y.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=self.tree_scroll_y.set)

        # Кнопки для добавления и удаления записей
        self.side_frame = ttk.Frame(self.root)
        self.side_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        self.add_button = ttk.Button(self.side_frame, text="Добавить контрагента", command=self.add_counterparty)
        self.add_button.pack(pady=5)

        self.delete_button = ttk.Button(self.side_frame, text="Удалить запись", command=self.delete_record)
        self.delete_button.pack(pady=5)

        # Кнопка теста подключения
        self.test_button = ttk.Button(self.side_frame, text="Тест подключения", command=self.test_connection)
        self.test_button.pack(pady=5)

    def load_city_codes(self):
        try:
            connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='Sexy163123',
                database='counterparties1'
            )
            cursor = connection.cursor()
            cursor.execute("SELECT city_code, city_name FROM cities")
            result = cursor.fetchall()
            self.city_codes = {row[1]: row[0] for row in result}  # Словарь {город: код города}
            self.city_code_options = [f"{row[0]} - {row[1]}" for row in result]  # Список строк вида "код города - город"
            self.city_names = list(self.city_codes.keys())  # Список городов
            cursor.close()
            connection.close()
        except mysql.connector.Error as err:
            messagebox.showerror("Ошибка", f"Ошибка загрузки кодов городов: {err}")

    def execute_query(self):
        query_text = self.query_combo.get()
        if not query_text:
            query_text = "Вывести всех контрагентов"

        queries = {
            "Вывести уникальные города контрагентов": ("SELECT DISTINCT city FROM counterparties;", ["Город"]),
            "Вывести всех контрагентов": ("SELECT appellation AS Name, city AS City, address AS Address, phone_number AS Phone, city_code AS CityCode FROM counterparties;", 
                                         ["Название", "Город", "Адрес", "Телефон", "Код города"]),
            "Вывести контрагентов с городами": ("SELECT c.appellation, c.city, c.address, c.phone_number, ct.city_name FROM counterparties c JOIN cities ct ON c.city_code = ct.city_code;", 
                                               ["Название", "Город", "Адрес", "Телефон", "Название города"]),
            "Вывести контрагентов из Москвы": ("SELECT appellation, city, address, phone_number, city_code FROM counterparties WHERE city = 'Москва';", 
                                               ["Название", "Город", "Адрес", "Телефон", "Код города"]),
            "Вывести контрагентов из того же города, что и контрагент с номером 2": ("SELECT appellation, city, address, phone_number, city_code FROM counterparties WHERE city IN (SELECT city FROM counterparties WHERE serial_number = '2');", 
                                                                                    ["Название", "Город", "Адрес", "Телефон", "Код города"]),
            "Вывести всех поставщиков": ("SELECT c.appellation, c.city, c.address, c.phone_number, t.type_counterparty FROM counterparties c JOIN types_of_counterparties t ON c.serial_number = t.serial_number WHERE t.type_counterparty = 'Поставщик';", 
                                         ["Название", "Город", "Адрес", "Телефон", "Тип контрагента"])
        }
        query, columns = queries.get(query_text, (None, None))
        if not query:
            messagebox.showerror("Ошибка", "Выберите корректный запрос")
            return

        try:
            connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='Sexy163123',
                database='counterparties1'
            )
            cursor = connection.cursor()
            cursor.execute(query)
            result = cursor.fetchall()

            # Очистка предыдущих данных и заголовков в treeview
            self.tree.delete(*self.tree.get_children())
            self.tree["columns"] = columns
            self.tree["show"] = "headings"
            for col in columns:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=100, anchor='w', stretch=tk.YES)

            for row in result:
                self.tree.insert("", tk.END, values=row)
            
            cursor.close()
            connection.close()
        except mysql.connector.Error as err:
            messagebox.showerror("Ошибка", f"Ошибка подключения к базе данных: {err}")

    def add_counterparty(self):
        self.add_window = tk.Toplevel(self.root)
        self.add_window.title("Добавить контрагента")

        self.add_window.grab_set()  # Сделать окно модальным
        self.add_window.resizable(False, False)  # Запретить изменение размеров окна

        ttk.Label(self.add_window, text="Название").grid(row=0, column=0, padx=5, pady=5)
        self.appellation_entry = ttk.Entry(self.add_window)
        self.appellation_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.add_window, text="Город").grid(row=1, column=0, padx=5, pady=5)
        self.city_combo = ttk.Combobox(self.add_window, values=self.city_names)
        self.city_combo.grid(row=1, column=1, padx=5, pady=5)
        self.city_combo.bind("<<ComboboxSelected>>", self.update_city_code)  # Обновление кода города при выборе

        ttk.Label(self.add_window, text="Адрес").grid(row=2, column=0, padx=5, pady=5)
        self.address_entry = ttk.Entry(self.add_window)
        self.address_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(self.add_window, text="Телефон").grid(row=3, column=0, padx=5, pady=5)
        vcmd = (self.add_window.register(self.validate_phone_number), '%P')
        self.phone_number_entry = ttk.Entry(self.add_window, validate="key", validatecommand=vcmd)
        self.phone_number_entry.grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(self.add_window, text="Код города").grid(row=4, column=0, padx=5, pady=5)
        self.city_code_combo = ttk.Combobox(self.add_window, values=self.city_code_options)
        self.city_code_combo.grid(row=4, column=1, padx=5, pady=5)

        self.add_submit_button = ttk.Button(self.add_window, text="Добавить", command=self.submit_counterparty)
        self.add_submit_button.grid(row=5, column=0, columnspan=2, pady=10)

    def update_city_code(self, event):
        city = self.city_combo.get()
        city_code = self.city_codes.get(city, "")
        self.city_code_combo.set(city_code)

    def validate_phone_number(self, phone_number):
        return re.match(r'^[\d\+\-]*$', phone_number) is not None

    def submit_counterparty(self):
        appellation = self.appellation_entry.get()
        city = self.city_combo.get()
        address = self.address_entry.get()
        phone_number = self.phone_number_entry.get()
        city_code = self.city_code_combo.get().split(' - ')[0] if ' - ' in self.city_code_combo.get() else self.city_code_combo.get()

        # Проверка существования города и кода города
        existing_city_code = self.city_codes.get(city)
        if not existing_city_code:
            messagebox.showerror("Ошибка", "Пожалуйста, выберите город из предложенных, контрагенты могут находиться на данный момент только в предложенных городах, расширение пока не планируется.")
            return
        if existing_city_code != city_code:
            messagebox.showerror("Ошибка", "Выберите верный код города для существующего города")
            return

        # Добавление контрагента
        try:
            connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='Sexy163123',
                database='counterparties1'
            )
            cursor = connection.cursor()
            query = "INSERT INTO counterparties (appellation, city, address, phone_number, city_code) VALUES (%s, %s, %s, %s, %s)"
            values = (appellation, city, address, phone_number, city_code)
            cursor.execute(query, values)
            connection.commit()
            cursor.close()
            connection.close()
            messagebox.showinfo("Успех", "Контрагент успешно добавлен")
            self.add_window.destroy()
            self.execute_query()  # Обновление списка контрагентов после добавления
        except mysql.connector.Error as err:
            messagebox.showerror("Ошибка", f"Ошибка добавления контрагента: {err}")

    def delete_record(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Ошибка", "Выберите запись для удаления")
            return
        
        item = self.tree.item(selected_item)
        appellation = item['values'][0]  # Название контрагента

        try:
            connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='Sexy163123',
                database='counterparties1'
            )
            cursor = connection.cursor()
            query = "DELETE FROM counterparties WHERE appellation = %s"
            cursor.execute(query, (appellation,))
            connection.commit()
            cursor.close()
            connection.close()
            messagebox.showinfo("Успех", "Запись успешно удалена")
            self.execute_query()  # Обновление списка контрагентов после удаления
        except mysql.connector.Error as err:
            messagebox.showerror("Ошибка", f"Ошибка удаления записи: {err}")

    def test_connection(self):
        try:
            connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='Sexy163123',
                database='counterparties1'
            )
            connection.close()
            messagebox.showinfo("Успех", "Подключение успешно")
        except mysql.connector.Error as err:
            messagebox.showerror("Ошибка", f"Ошибка подключения к базе данных: {err}")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()

   
