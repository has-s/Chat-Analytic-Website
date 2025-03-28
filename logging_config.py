import logging

def setup_logger(name):
    """Настройка логгера."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Уровень логирования, можно выбрать INFO, WARNING, ERROR, CRITICAL

    # Формат вывода
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Настройка вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Уровень логирования для консоли
    console_handler.setFormatter(formatter)

    # Добавляем обработчики
    logger.addHandler(console_handler)

    return logger