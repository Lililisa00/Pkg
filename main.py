import streamlit as st
import cv2
import numpy as np
from PIL import Image

def apply_sharpening(image, kernel_type):
    """
    Реализация высокочастотных фильтров (увеличение резкости).
    Используем свертку с различными ядрами.
    """
    if kernel_type == "Мягкая резкость (Basic)":
        kernel = np.array([[0, -1, 0],
                           [-1, 5, -1],
                           [0, -1, 0]])
    elif kernel_type == "Сильная резкость (Strong)":
        kernel = np.array([[-1, -1, -1],
                           [-1, 9, -1],
                           [-1, -1, -1]])
    else: # Laplacian
        # Лапласиан выделяет края, для добавления к исходному изображению
        # используется техника unsharp masking, но здесь покажем чистый фильтр
        # для демонстрации высокочастотной составляющей
        kernel = np.array([[0, 1, 0],
                           [1, -4, 1],
                           [0, 1, 0]])
    
    # Применение фильтра (filter2D выполняет свертку)
    return cv2.filter2D(image, -1, kernel)

def main():
    st.set_page_config(layout="wide", page_title="Лаб. работа №2: Вариант 8")
    
    st.title("Лабораторная работа: Обработка изображений (Вариант 8)")
    st.markdown("""
    **Задание:**
    1. Реализация высокочастотных фильтров (увеличение резкости).
    2. Глобальная пороговая обработка (2 метода) + Адаптивная пороговая обработка.
    """)

    # Загрузка изображения
    uploaded_file = st.sidebar.file_uploader("Загрузите изображение", type=["jpg", "png", "jpeg", "bmp"])

    if uploaded_file is not None:
        # Конвертация файла в формат для OpenCV
        image = Image.open(uploaded_file).convert("RGB")
        img_array = np.array(image)
        
        # Если изображение цветное, конвертируем в BGR (для OpenCV), затем в Gray для пороговой
        if len(img_array.shape) == 3:
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        else:
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
            img_gray = img_array

        st.sidebar.header("Настройки обработки")
        mode = st.sidebar.radio("Выберите метод:", ["Высокочастотные фильтры (Резкость)", "Пороговая обработка (Сегментация)"])

        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Исходное изображение")
            st.image(image, use_container_width=True)

        with col2:
            st.subheader("Результат")
            
            if mode == "Высокочастотные фильтры (Резкость)":
                st.info("Высокочастотные фильтры усиливают разницу между соседними пикселями, повышая резкость.")
                filter_type = st.selectbox("Тип фильтра", ["Мягкая резкость (Basic)", "Сильная резкость (Strong)", "Выделение краев (Laplacian)"])
                
                # Обработка
                processed_img = apply_sharpening(img_bgr, filter_type)
                
                # Конвертация обратно в RGB для отображения
                st.image(cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB), use_container_width=True)

            elif mode == "Пороговая обработка (Сегментация)":
                st.info("Преобразование изображения в черно-белое (бинарное) на основе порогов.")
                threshold_type = st.selectbox("Тип алгоритма",
                                              ["Глобальный: Ручной порог",
                                               "Глобальный: Метод Оцу (Otsu)",
                                               "Адаптивный: Mean (Среднее)",
                                               "Адаптивный: Gaussian (Гаусс)"])
                
                if threshold_type == "Глобальный: Ручной порог":
                    thresh_val = st.slider("Значение порога", 0, 255, 127)
                    _, processed_img = cv2.threshold(img_gray, thresh_val, 255, cv2.THRESH_BINARY)
                    st.caption(f"Все пиксели ярче {thresh_val} становятся белыми, остальные — черными.")
                    
                elif threshold_type == "Глобальный: Метод Оцу (Otsu)":
                    # Оцу автоматически находит оптимальный порог для бимодальной гистограммы
                    thresh_val, processed_img = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    st.caption(f"Алгоритм Оцу автоматически выбрал порог: {thresh_val}")
                    
                elif threshold_type == "Адаптивный: Mean (Среднее)":
                    block_size = st.slider("Размер блока (нечетное число)", 3, 51, 11, step=2)
                    c_val = st.slider("Константа C", 0, 20, 2)
                    processed_img = cv2.adaptiveThreshold(img_gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                                          cv2.THRESH_BINARY, block_size, c_val)
                    st.caption("Порог вычисляется как среднее значение в соседней области.")
                    
                elif threshold_type == "Адаптивный: Gaussian (Гаусс)":
                    block_size = st.slider("Размер блока (нечетное число)", 3, 51, 11, step=2)
                    c_val = st.slider("Константа C", 0, 20, 2)
                    processed_img = cv2.adaptiveThreshold(img_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                          cv2.THRESH_BINARY, block_size, c_val)
                    st.caption("Порог вычисляется как взвешенная сумма (по Гауссу) в соседней области.")

                st.image(processed_img, use_container_width=True, channels="GRAY")

if __name__ == "__main__":
    main()
