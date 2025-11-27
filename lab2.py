import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import zipfile
import tempfile
import math

# Поддерживаемые форматы (в нижнем регистре для проверки)
SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.gif', '.tif', '.tiff', '.bmp', '.png', '.pcx')

class ModernImageAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📁 Image Analyzer Pro")
        self.root.geometry("1400x800")
        self.root.configure(bg='#2c3e50')
        
        # Стили
        self.setup_styles()
        
        # Переменные
        self.current_folder = ""
        self.temp_dir = None
        
        # Создание интерфейса
        self.create_sidebar()
        self.create_main_area()
        self.create_status_bar()
        
        # Центрирование окна
        self.center_window()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Настройка стилей
        style.configure('Modern.TFrame', background='#34495e')
        style.configure('Sidebar.TFrame', background='#2c3e50')
        style.configure('Header.TLabel', background='#34495e', foreground='white', font=('Arial', 12, 'bold'))
        style.configure('Title.TLabel', background='#2c3e50', foreground='#ecf0f1', font=('Arial', 16, 'bold'))
        style.configure('Subtitle.TLabel', background='#2c3e50', foreground='#bdc3c7', font=('Arial', 10))
        
        # Стили для кнопок
        style.configure('Accent.TButton', background='#3498db', foreground='white', 
                       borderwidth=0, focuscolor='none', font=('Arial', 10, 'bold'))
        style.map('Accent.TButton', 
                 background=[('active', '#2980b9'), ('pressed', '#21618c')])
        
        style.configure('Secondary.TButton', background='#95a5a6', foreground='white',
                       borderwidth=0, focuscolor='none', font=('Arial', 10))
        style.map('Secondary.TButton',
                 background=[('active', '#7f8c8d'), ('pressed', '#6c7a7d')])
        
        style.configure('Success.TButton', background='#27ae60', foreground='white',
                       borderwidth=0, focuscolor='none', font=('Arial', 10))
        style.map('Success.TButton',
                 background=[('active', '#219653'), ('pressed', '#1e8449')])

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def create_sidebar(self):
        # Основной контейнер сайдбара
        sidebar = ttk.Frame(self.root, style='Sidebar.TFrame', width=300)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        sidebar.pack_propagate(False)
        
        # Заголовок
        title_frame = ttk.Frame(sidebar, style='Sidebar.TFrame')
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(title_frame, text="🖼️ Image Analyzer", style='Title.TLabel').pack(pady=(10, 5))
        ttk.Label(title_frame, text="Анализ метаданных изображений", style='Subtitle.TLabel').pack()
        
        # Раздел загрузки
        upload_frame = ttk.Frame(sidebar, style='Sidebar.TFrame')
        upload_frame.pack(fill=tk.X, pady=20)
        
        ttk.Label(upload_frame, text="ЗАГРУЗКА ДАННЫХ", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        # Кнопки загрузки
        self.btn_folder = ttk.Button(upload_frame, text="📁 Выбрать папку", 
                                   command=self.select_folder, style='Accent.TButton')
        self.btn_folder.pack(fill=tk.X, pady=5)
        
        self.btn_files = ttk.Button(upload_frame, text="📄 Выбрать файлы", 
                                  command=self.select_files, style='Secondary.TButton')
        self.btn_files.pack(fill=tk.X, pady=5)
        
        self.btn_zip = ttk.Button(upload_frame, text="🗜️ Загрузить ZIP", 
                                command=self.select_zip, style='Secondary.TButton')
        self.btn_zip.pack(fill=tk.X, pady=5)
        
        # Статистика
        stats_frame = ttk.Frame(sidebar, style='Sidebar.TFrame')
        stats_frame.pack(fill=tk.X, pady=20)
        
        ttk.Label(stats_frame, text="СТАТИСТИКА", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        self.stats_labels = {}
        stats_data = [
            ("📊 Всего файлов:", "total_files"),
            ("✅ Успешно:", "processed_files"),
            ("❌ Ошибки:", "error_files"),
            ("💾 Средний размер:", "avg_size"),
            ("📐 Среднее разрешение:", "avg_dpi")
        ]
        
        for text, key in stats_data:
            frame = ttk.Frame(stats_frame, style='Sidebar.TFrame')
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=text, style='Subtitle.TLabel', width=15, anchor=tk.W).pack(side=tk.LEFT)
            self.stats_labels[key] = ttk.Label(frame, text="0", style='Subtitle.TLabel', foreground='#3498db')
            self.stats_labels[key].pack(side=tk.RIGHT)
        
        # Информация о выбранном файле
        info_frame = ttk.Frame(sidebar, style='Sidebar.TFrame')
        info_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        ttk.Label(info_frame, text="ИНФОРМАЦИЯ О ФАЙЛЕ", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        self.file_info_text = tk.Text(info_frame, height=10, width=30, bg='#34495e', fg='#ecf0f1',
                                    font=('Arial', 9), relief=tk.FLAT, wrap=tk.WORD)
        self.file_info_text.pack(fill=tk.BOTH, expand=True)
        self.file_info_text.config(state=tk.DISABLED)

    def create_main_area(self):
        # Основная область
        main_frame = ttk.Frame(self.root, style='Modern.TFrame')
        main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)
        
        # Панель управления таблицей
        control_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(control_frame, text="РЕЗУЛЬТАТЫ АНАЛИЗА", style='Header.TLabel').pack(side=tk.LEFT)
        
        # Кнопки управления таблицей
        btn_frame = ttk.Frame(control_frame, style='Modern.TFrame')
        btn_frame.pack(side=tk.RIGHT)
        
        self.btn_export = ttk.Button(btn_frame, text="📤 Экспорт", style='Success.TButton')
        self.btn_export.pack(side=tk.LEFT, padx=5)
        
        self.btn_clear = ttk.Button(btn_frame, text="🗑️ Очистить", command=self.clear_table, style='Secondary.TButton')
        self.btn_clear.pack(side=tk.LEFT, padx=5)
        
        # Таблица с результатами
        table_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создание Treeview с кастомным стилем
        style = ttk.Style()
        style.configure('Custom.Treeview', 
                       background='#34495e',
                       foreground='white',
                       fieldbackground='#34495e',
                       borderwidth=0)
        style.configure('Custom.Treeview.Heading', 
                       background='#2c3e50',
                       foreground='white',
                       relief='flat')
        style.map('Custom.Treeview.Heading', 
                 background=[('active', '#3498db')])
        
        columns = ("filename", "size_px", "dpi", "depth", "compression", "compression_ratio", "file_size")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", style='Custom.Treeview')
        
        # Настройка заголовков
        headers = {
            "filename": "📄 Имя файла",
            "size_px": "📐 Размер (px)",
            "dpi": "🎯 Разрешение",
            "depth": "🎨 Глубина цвета",
            "compression": "🗜️ Сжатие", 
            "compression_ratio": "📊 % Сжатия",
            "file_size": "💾 Размер"
        }
        
        for col, text in headers.items():
            self.tree.heading(col, text=text)
        
        # Настройка ширины колонок
        self.tree.column("filename", width=250)
        self.tree.column("size_px", width=120, anchor=tk.CENTER)
        self.tree.column("dpi", width=100, anchor=tk.CENTER)
        self.tree.column("depth", width=120, anchor=tk.CENTER)
        self.tree.column("compression", width=120, anchor=tk.CENTER)
        self.tree.column("compression_ratio", width=100, anchor=tk.CENTER)
        self.tree.column("file_size", width=100, anchor=tk.CENTER)
        
        # Скроллбары
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Привязка события выбора
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

    def create_status_bar(self):
        status_frame = ttk.Frame(self.root, style='Modern.TFrame')
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Готов к работе", style='Subtitle.TLabel')
        self.status_label.pack(side=tk.LEFT)
        
        # Прогресс-бар
        self.progress = ttk.Progressbar(status_frame, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self.progress.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.progress_label = ttk.Label(status_frame, text="0%", style='Subtitle.TLabel', width=5)
        self.progress_label.pack(side=tk.RIGHT)

    def update_status(self, message):
        self.status_label.config(text=message)

    def update_progress(self, value, maximum=None):
        if maximum:
            self.progress.configure(maximum=maximum)
        self.progress.configure(value=value)
        if maximum:
            percentage = (value / maximum) * 100
            self.progress_label.config(text=f"{percentage:.0f}%")

    def clear_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.update_stats()
        self.update_status("Таблица очищена")

    def on_tree_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item, 'values')
            self.show_file_info(values)

    def show_file_info(self, values):
        self.file_info_text.config(state=tk.NORMAL)
        self.file_info_text.delete(1.0, tk.END)
        
        info_text = f"""📄 Файл: {values[0]}

📐 Размер: {values[1]}
🎯 Разрешение: {values[2]}
🎨 Глубина цвета: {values[3]}
🗜️ Сжатие: {values[4]}
📊 Эффективность: {values[5]}
💾 Размер файла: {values[6]}

--- Метаданные ---
Формат: {values[0].split('.')[-1].upper()}
Статус: ✅ Успешно"""
        
        self.file_info_text.insert(1.0, info_text)
        self.file_info_text.config(state=tk.DISABLED)

    def update_stats(self, data=None):
        if not data:
            for key in self.stats_labels:
                self.stats_labels[key].config(text="0")
            return
        
        total = len(data)
        processed = len([d for d in data if d[1] != "Error"])
        errors = total - processed
        
        # Расчет среднего размера
        sizes = []
        for item in data:
            if item[6] != "0 B":
                size_str = item[6]
                if 'KB' in size_str:
                    sizes.append(float(size_str.replace(' KB', '')) * 1024)
                elif 'MB' in size_str:
                    sizes.append(float(size_str.replace(' MB', '')) * 1024 * 1024)
                else:
                    sizes.append(float(size_str.replace(' B', '')))
        
        avg_size = sum(sizes) / len(sizes) if sizes else 0
        avg_size_str = self.format_file_size(avg_size)
        
        self.stats_labels['total_files'].config(text=str(total))
        self.stats_labels['processed_files'].config(text=str(processed))
        self.stats_labels['error_files'].config(text=str(errors))
        self.stats_labels['avg_size'].config(text=avg_size_str)
        self.stats_labels['avg_dpi'].config(text="96 DPI")

    # Далее идут все методы из предыдущей реализации (select_folder, select_files, select_zip, 
    # process_image, calculate_compression_ratio, format_file_size, и т.д.)
    # Они остаются без изменений, только замените self.root.after на self.update_progress
    # и self.lbl_status.config на self.update_status

    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.current_folder = folder_path
            self.update_status(f"📁 Сканирование папки: {os.path.basename(folder_path)}...")
            self.clear_table()
            threading.Thread(target=self.process_folder, args=(folder_path,), daemon=True).start()

    def select_files(self):
        file_paths = filedialog.askopenfilenames(
            title="Выберите изображения",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.tif *.pcx"), ("All files", "*.*")]
        )
        if file_paths:
            self.update_status(f"📄 Обработка {len(file_paths)} файлов...")
            self.clear_table()
            threading.Thread(target=self.process_files, args=(file_paths,), daemon=True).start()

    def select_zip(self):
        zip_path = filedialog.askopenfilename(
            title="Выберите ZIP архив",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        if zip_path:
            self.update_status(f"🗜️ Распаковка и анализ ZIP архива...")
            self.clear_table()
            threading.Thread(target=self.process_zip, args=(zip_path,), daemon=True).start()

    def calculate_compression_ratio(self, filepath, img):
        """Вычисляет процент сжатия изображения"""
        try:
            file_size = os.path.getsize(filepath)
            
            bits_per_pixel_map = {
                "1": 1, "L": 8, "P": 8, "RGB": 24, "RGBA": 32, 
                "CMYK": 32, "YCbCr": 24, "I": 32, "F": 32
            }
            
            bits_per_pixel = bits_per_pixel_map.get(img.mode, 24)
            theoretical_size = (img.width * img.height * bits_per_pixel) / 8
            
            if theoretical_size > 0:
                compression_ratio = ((theoretical_size - file_size) / theoretical_size) * 100
                compression_ratio = max(0, min(100, compression_ratio))
                return compression_ratio, file_size
            else:
                return 0, file_size
                
        except Exception as e:
            return 0, 0

    def format_file_size(self, size_bytes):
        """Форматирует размер файла в читаемый вид"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"

    def process_image(self, filepath, filename):
        """Обрабатывает одно изображение и возвращает данные"""
        try:
            with Image.open(filepath) as img:
                img.load()

                size_px = f"{img.width} x {img.height}"

                dpi = img.info.get('dpi')
                dpi_str = f"{int(dpi[0])}x{int(dpi[1])}" if dpi else "Н/Д"

                mode_to_depth = {
                    "1": "1 bit (B&W)", "L": "8 bit (Gray)", "P": "8 bit (Palette)",
                    "RGB": "24 bit", "RGBA": "32 bit", "CMYK": "32 bit",
                    "YCbCr": "24 bit", "I": "32 bit (Signed)", "F": "32 bit (Float)"
                }
                depth = mode_to_depth.get(img.mode, f"{img.mode} (?)")

                compression = img.info.get('compression', '')
                if not compression:
                    if img.format == 'JPEG':
                        compression = 'JPEG'
                    elif img.format == 'PNG':
                        compression = 'Deflate'
                    elif img.format == 'GIF':
                        compression = 'LZW'
                    elif img.format == 'BMP':
                        compression = 'RLE/None'
                    else:
                        compression = 'None'

                compression_ratio, file_size = self.calculate_compression_ratio(filepath, img)
                compression_ratio_str = f"{compression_ratio:.1f}%"
                file_size_str = self.format_file_size(file_size)

                return (filename, size_px, dpi_str, depth, str(compression), compression_ratio_str, file_size_str)

        except Exception as e:
            return (filename, "Error", "-", "-", str(e), "0%", "0 B")

    def process_folder(self, folder_path):
        files = []
        try:
            all_files = os.listdir(folder_path)
            files = [f for f in all_files if f.lower().endswith(SUPPORTED_FORMATS)]
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать папку:\n{e}")
            return

        self.process_file_list(files, folder_path)

    def process_files(self, file_paths):
        files_data = []
        for filepath in file_paths:
            filename = os.path.basename(filepath)
            if filename.lower().endswith(SUPPORTED_FORMATS):
                files_data.append((filename, filepath))
        
        self.process_file_list_with_paths(files_data)

    def process_zip(self, zip_path):
        try:
            self.temp_dir = tempfile.mkdtemp()
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                image_files = [f for f in file_list if f.lower().endswith(SUPPORTED_FORMATS)]
                
                if not image_files:
                    messagebox.showwarning("Предупреждение", "В архиве не найдено поддерживаемых изображений")
                    return
                
                files_data = []
                for image_file in image_files:
                    zip_ref.extract(image_file, self.temp_dir)
                    filepath = os.path.join(self.temp_dir, image_file)
                    files_data.append((os.path.basename(image_file), filepath))
                
                self.process_file_list_with_paths(files_data)
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обработать ZIP архив:\n{e}")

    def process_file_list(self, files, folder_path):
        total_files = len(files)
        self.update_progress(0, total_files)

        processed_data = []
        for idx, filename in enumerate(files):
            filepath = os.path.join(folder_path, filename)
            result = self.process_image(filepath, filename)
            processed_data.append(result)

            if idx % 10 == 0:
                self.update_progress(idx)

        self.finalize_processing(processed_data, total_files)

    def process_file_list_with_paths(self, files_data):
        total_files = len(files_data)
        self.update_progress(0, total_files)

        processed_data = []
        for idx, (filename, filepath) in enumerate(files_data):
            result = self.process_image(filepath, filename)
            processed_data.append(result)

            if idx % 10 == 0:
                self.update_progress(idx)

        self.finalize_processing(processed_data, total_files)

    def finalize_processing(self, processed_data, total_files):
        for item in processed_data:
            self.tree.insert("", tk.END, values=item)
        
        self.update_progress(total_files)
        self.update_stats(processed_data)
        self.update_status(f"✅ Готово! Обработано файлов: {total_files}")
        messagebox.showinfo("Готово", f"Обработка завершена.\nНайдено изображений: {total_files}")

    def __del__(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernImageAnalyzerApp(root)
    root.mainloop()
