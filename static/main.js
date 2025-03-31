document.addEventListener("DOMContentLoaded", () => {
    const vodForm = document.getElementById("vodForm");
    const statusMessage = document.getElementById("status_message");
    const analyticsForm = document.getElementById("analytics_form");
    let intervalId;

    // Обработчик отправки формы VOD
    vodForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        try {
            const formData = new FormData(vodForm);
            const response = await fetch("/", {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                // Если данные успешно загружены
                if (data.task_id) {
                    statusMessage.textContent = "Данные загружены. Можно запускать аналитику.";
                    analyticsForm.style.display = "block"; // Показать форму аналитики
                } else {
                    statusMessage.textContent = data.message || "Ошибка загрузки данных.";
                    analyticsForm.style.display = "none"; // Скрыть форму аналитики
                }
            } else {
                // Обработка ошибки, если статус не OK (например, код 400)
                statusMessage.textContent = data.message || "Ошибка загрузки данных.";
                analyticsForm.style.display = "none"; // Скрыть форму аналитики
            }

        } catch (error) {
            statusMessage.textContent = "Ошибка при загрузке данных.";
            analyticsForm.style.display = "none"; // Скрыть форму аналитики
            console.error(error);
        }
    });

    // Обработчик отправки формы аналитики
    analyticsForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        try {
            const formData = new FormData(analyticsForm);
            const response = await fetch("/run_analysis", {
                method: "POST",
                body: formData
            });

            const data = await response.json();
            if (data.status === "success") {
                checkAnalysisStatus(data.task_id);
            } else {
                statusMessage.textContent = "Ошибка запуска аналитики.";
            }
        } catch (error) {
            statusMessage.textContent = "Ошибка при отправке формы аналитики.";
            console.error(error);
        }
    });

    // Функция проверки статуса аналитики
    function checkAnalysisStatus(taskId) {
        intervalId = setInterval(async () => {
            try {
                const response = await fetch(`/check_status/${taskId}`);
                const data = await response.json();

                switch (data.status) {
                    case 'pending':
                        statusMessage.textContent = "Аналитика выполняется, подождите...";
                        break;
                    case 'success':
                        statusMessage.textContent = "Аналитика завершена. Результаты: " + JSON.stringify(data.result);
                        clearInterval(intervalId);
                        break;
                    case 'failure':
                        statusMessage.textContent = "Ошибка выполнения аналитики: " + data.result;
                        clearInterval(intervalId);
                        break;
                    default:
                        statusMessage.textContent = "Неизвестный статус задачи.";
                        clearInterval(intervalId);
                }
            } catch (error) {
                statusMessage.textContent = "Ошибка проверки статуса.";
                clearInterval(intervalId);
                console.error(error);
            }
        }, 1000);
    }
});