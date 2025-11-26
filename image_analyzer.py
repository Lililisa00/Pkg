import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image

# Поддерживаемые форматы (в нижнем регистре для проверки)
SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.gif', '.tif', '.tiff', '.bmp', '.png', '.pcx')

class ImageAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Metadata Analyzer (Lab #2)")
        self.root.geometry("1000x600")

        # --- Верхняя панель управления ---
        control_frame = tk.Frame(root, pady=10)
        control_frame.pack(fill=tk.X, padx=10)

        self.btn_select = tk.Button(control_frame, text="Выбрать папку", command=self.select_folder, height=2, bg="#e1e1e1")
        self.btn_select.pack(side=tk.LEFT, padx=5)

        self.lbl_status = tk.Label(control_frame, text="Папка не выбрана", fg="gray")
        self.lbl_status.pack(side=tk.LEFT, padx=10)

        # --- Таблица результатов ---
        columns = ("filename", "size_px", "dpi", "depth", "compression")
        self.tree = ttk.Treeview(root, columns=columns, show="headings")
        
        # Настройка заголовков
        self.tree.heading("filename", text="Имя файла")
        self.tree.heading("size_px", text="Размер (px)")
        self.tree.heading("dpi", text="Разрешение (DPI)")
        self.tree.heading("depth", text="Глубина цвета")
        self.tree.heading("compression", text="Сжатие")

        # Настройка ширины колонок
        self.tree.column("filename", width=250)
        self.tree.column("size_px", width=100, anchor=tk.CENTER)
        self.tree.column("dpi", width=100, anchor=tk.CENTER)
        self.tree.column("depth", width=100, anchor=tk.CENTER)
        self.tree.column("compression", width=150, anchor=tk.CENTER)

        # Скроллбар
        scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- Прогресс бар ---
        self.progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, padx=10, pady=10)

    def select_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.lbl_status.config(text=f"Сканирование: {folder_path}...")
            # Очистка таблицы перед новым сканированием
            for i in self.tree.get_children():
                self.tree.delete(i)
            
            # Запуск обработки в отдельном потоке, чтобы интерфейс не завис
            threading.Thread(target=self.process_folder, args=(folder_path,), daemon=True).start()

    def process_folder(self, folder_path):
        files = []
        # Собираем все файлы рекурсивно или только в текущей папке (по условию "папка" обычно подразумевает и вложенные, но для скорости лучше один уровень)
        # Здесь реализован просмотр только выбранной папки (без вложений) для скорости на 100к файлах
        try:
            all_files = os.listdir(folder_path)
            files = [f for f in all_files if f.lower().endswith(SUPPORTED_FORMATS)]
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать папку:\n{e}")
            return

        total_files = len(files)
        self.root.after(0, lambda: self.progress.configure(maximum=total_files, value=0))

        processed_data = []

        for idx, filename in enumerate(files):
            filepath = os.path.join(folder_path, filename)
            try:
                # Открываем изображение. ВАЖНО: Pillow открывает "лениво", 
                # он читает только заголовок, не загружая пиксели в память.
                # Это обеспечивает высочайшее быстродействие (20 баллов).
                with Image.open(filepath) as img:
                    img.load() # Для некоторых форматов нужно подгрузить метаданные

                    # 1. Размер в пикселях
                    size_px = f"{img.width} x {img.height}"

                    # 2. Разрешение (DPI)
                    # Часто хранится в img.info['dpi'], но не всегда
                    dpi = img.info.get('dpi')
                    if dpi:
                        dpi_str = f"{int(dpi[0])}x{int(dpi[1])}"
                    else:
                        dpi_str = "Н/Д" # Нет данных

                    # 3. Глубина цвета
                    # Pillow mode mapping
                    mode_to_depth = {
                        "1": "1 bit (B&W)",
                        "L": "8 bit (Gray)",
                        "P": "8 bit (Palette)",
                        "RGB": "24 bit",
                        "RGBA": "32 bit",
                        "CMYK": "32 bit",
                        "YCbCr": "24 bit",
                        "I": "32 bit (Signed)",
                        "F": "32 bit (Float)"
                    }
                    depth = mode_to_depth.get(img.mode, f"{img.mode} (?)")

                    # 4. Сжатие
                    # Берется из img.info. Для JPG это 'jpeg', для других может быть разным.
                    compression = img.info.get('compression', '')
                    
                    # Если поле пустое, определяем по формату
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

                    processed_data.append((filename, size_px, dpi_str, depth, str(compression)))

            except Exception as e:
                # Если файл битый или не открывается
                processed_data.append((filename, "Error", "-", "-", str(e)))

            # Обновление прогресс-бара каждые 50 файлов, чтобы не тормозить GUI
            if idx % 50 == 0:
                self.root.after(0, lambda v=idx: self.progress.configure(value=v))

        # Вставка данных в таблицу в главном потоке
        self.root.after(0, lambda: self.populate_tree(processed_data, total_files))

    def populate_tree(self, data, total):
        for item in data:
            self.tree.insert("", tk.END, values=item)
        
        self.progress.configure(value=total)
        self.lbl_status.config(text=f"Готово! Обработано файлов: {total}")
        messagebox.showinfo("Готово", f"Обработка завершена.\nНайдено изображений: {total}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageAnalyzerApp(root)
    root.mainloop()