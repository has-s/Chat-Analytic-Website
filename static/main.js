document.addEventListener("DOMContentLoaded", function() {
    const vodForm = document.getElementById("vodForm");
    const taskId = document.getElementById("task_id").value;
    const statusMessage = document.getElementById("status_message");
    const analyticsForm = document.getElementById("analytics_form"); // Ссылка на форму аналитики
    let intervalId;

    if (taskId) {
        // Функция для проверки статуса задачи
        function checkTaskStatus() {
            fetch(`/check_status/${taskId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'pending') {
                        statusMessage.textContent = "Задача в процессе выполнения, подождите...";
                    } else if (data.status === 'success') {
                        statusMessage.textContent = `Задача выполнена. Не переживай, она сохранена!`;
                        clearInterval(intervalId); // Остановка таймера после выполнения

                        // Показываем форму аналитики
                        if (analyticsForm) {
                            analyticsForm.style.display = "block";
                        }
                    } else if (data.status === 'failure') {
                        statusMessage.textContent = `Ошибка: ${data.result}`;
                        clearInterval(intervalId); // Остановка таймера при ошибке
                    } else {
                        statusMessage.textContent = "Неизвестный статус задачи.";
                    }
                })
                .catch(error => {
                    console.error('Ошибка при проверке статуса задачи:', error);
                    clearInterval(intervalId); // Остановка таймера при ошибке запроса
                    statusMessage.textContent = "Ошибка при проверке статуса задачи.";
                });
        }

        // Запускаем проверку статуса каждые 1 секунду
        intervalId = setInterval(checkTaskStatus, 1000);
    }
});