FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Добавляем непривилегированного пользователя
RUN groupadd -r appgroup && useradd -m -r -g appgroup appuser

# Копируем весь проект
COPY . .

# Установка переменной среды
ENV PYTHONUNBUFFERED=1

# Переключаемся на непривилегированного пользователя
USER appuser