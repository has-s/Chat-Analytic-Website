document.addEventListener("DOMContentLoaded", () => {
    const vodForm = document.getElementById("vodForm");
    const statusMessage = document.getElementById("status_message");
    const analyticsForm = document.getElementById("analytics_form");
    let intervalId;

    // Изначально форма аналитики скрыта
    analyticsForm.style.display = "none";

    // Обработчик отправки формы VOD
    vodForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        // Скрываем форму аналитики при новой загрузке данных
        analyticsForm.style.display = "none"; // Прячем форму аналитики
        statusMessage.textContent = "Загружаем данные...";

        try {
            const formData = new FormData(vodForm);
            const response = await fetch("/", {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                if (data.task_id) {
                    statusMessage.textContent = "Данные загружаются, подождите...";
                    // Проверяем статус задачи загрузки данных
                    await checkDataLoadingStatus(data.task_id);
                } else {
                    // Сообщаем о том, что данные уже загружены
                    statusMessage.textContent = data.message || "Данные уже загружены.";
                }
            } else {
                // Обработка ошибки
                statusMessage.textContent = data.message || "Ошибка загрузки данных.";
            }

        } catch (error) {
            statusMessage.textContent = "Ошибка при загрузке данных.";
            console.error(error);
        }
    });

    // Функция для проверки статуса загрузки данных
    async function checkDataLoadingStatus(taskId) {
        try {
            const response = await fetch(`/check_status/${taskId}`);
            const data = await response.json();

            if (data.status === 'success') {
                // Если загрузка данных завершена успешно, показываем форму аналитики
                statusMessage.textContent = "Данные загружены. Можно запускать аналитику.";
                analyticsForm.style.display = "block"; // Показать форму аналитики
            } else if (data.status === 'failure') {
                // Если произошла ошибка, выводим сообщение
                statusMessage.textContent = "Ошибка при загрузке данных: " + data.result;
            } else {
                // Пока данные еще загружаются
                statusMessage.textContent = "Данные загружаются, подождите...";
                setTimeout(() => checkDataLoadingStatus(taskId), 1000); // Проверяем каждые 2 секунды
            }

        } catch (error) {
            statusMessage.textContent = "Ошибка при проверке статуса загрузки.";
            console.error(error);
        }
    }
});