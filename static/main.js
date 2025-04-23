document.addEventListener("DOMContentLoaded", () => {
    const vodForm = document.getElementById("vodForm");
    const statusMessage = document.getElementById("status_message");
    const analyticsForm = document.getElementById("analytics_form");
    const resultsContainer = document.getElementById("results");
    let intervalId;

    // Скрываем форму аналитики до загрузки VOD
    analyticsForm.style.display = "none";

    // Отправка URL VOD
    vodForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        analyticsForm.style.display = "none";
        resultsContainer.innerHTML = "";
        statusMessage.textContent = "Загружаем данные...";

        try {
            const formData = new FormData(vodForm);
            const response = await fetch("/", { method: "POST", body: formData });
            const data = await response.json();

            if (response.ok && data.task_id) {
                statusMessage.textContent = "Данные загружаются, подождите...";
                await checkDataLoadingStatus(data.task_id);
            } else {
                statusMessage.textContent = data.message || "Ошибка загрузки данных.";
            }
        } catch (err) {
            statusMessage.textContent = "Ошибка при загрузке данных.";
            console.error(err);
        }
    });

    // Проверка статуса загрузки VOD
    async function checkDataLoadingStatus(taskId) {
        try {
            const response = await fetch(`/check_status/${taskId}`);
            const data = await response.json();

            if (data.status === "success") {
                statusMessage.textContent = "Данные загружены. Можно запускать аналитику.";
                analyticsForm.style.display = "block";
            } else if (data.status === "failure") {
                statusMessage.textContent = "Ошибка при загрузке данных: " + data.result;
            } else {
                statusMessage.textContent = "Данные загружаются, подождите...";
                setTimeout(() => checkDataLoadingStatus(taskId), 1000);
            }
        } catch (err) {
            statusMessage.textContent = "Ошибка при проверке статуса загрузки.";
            console.error(err);
        }
    }

    // Отправка настроек аналитики
    analyticsForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        resultsContainer.innerHTML = "";
        statusMessage.textContent = "Запуск аналитики...";

        try {
            const formData = new FormData(analyticsForm);

            // Преобразуем ключевые слова в JSON-массив
            const keywordsInput = analyticsForm.querySelector('input[name="keywords"]');
            const rawKeywords = keywordsInput?.value || "";
            const keywordsArray = rawKeywords
                .split(",")
                .map(k => k.trim())
                .filter(k => k.length > 0);
            formData.set("keywords", JSON.stringify(keywordsArray));

            const response = await fetch("/run_analysis", { method: "POST", body: formData });
            const data = await response.json();

            if (data.status === "success") {
                checkAnalysisStatus(data.task_id);
            } else {
                statusMessage.textContent = "Ошибка запуска аналитики.";
            }
        } catch (err) {
            statusMessage.textContent = "Ошибка при отправке формы аналитики.";
            console.error(err);
        }
    });

    // Поллинг статуса задачи аналитики
    function checkAnalysisStatus(taskId) {
        intervalId = setInterval(async () => {
            try {
                const response = await fetch(`/check_status/${taskId}`);
                const data = await response.json();

                if (data.status === "pending") {
                    statusMessage.textContent = "Аналитика выполняется, подождите...";
                } else if (data.status === "success") {
                    statusMessage.textContent = "Аналитика завершена.";
                    renderResults(data.result);
                    clearInterval(intervalId);
                } else {
                    statusMessage.textContent = data.status === "failure"
                        ? "Ошибка выполнения аналитики: " + data.result
                        : "Неизвестный статус задачи.";
                    clearInterval(intervalId);
                }
            } catch (err) {
                statusMessage.textContent = "Ошибка проверки статуса.";
                clearInterval(intervalId);
                console.error(err);
            }
        }, 1000);
    }

    // Рендер результатов
    function renderResults(result) {
        resultsContainer.innerHTML = "";
        const res = result.analysis_result || {};

        // Топ чаттеры
        if (res.top_chatters) {
            resultsContainer.innerHTML += "<h3>Топ чаттеры</h3>";
            const ul = document.createElement("ul");
            res.top_chatters.forEach(([name, count]) => {
                const li = document.createElement("li");
                li.textContent = `${name}: ${count} сообщений`;
                ul.appendChild(li);
            });
            resultsContainer.appendChild(ul);
        }

        // Топ пасты
        if (res.top_pastes) {
            resultsContainer.innerHTML += "<h3>Топ пасты</h3>";
            const ul = document.createElement("ul");
            res.top_pastes.forEach(paste => {
                const li = document.createElement("li");
                li.innerHTML = `<strong>${paste.base_pasta}</strong> (${paste.count})`;
                if (paste.variants?.length) {
                    const sub = document.createElement("ul");
                    paste.variants.forEach(v => {
                        const sli = document.createElement("li");
                        sli.textContent = `${v.text} (${v.count})`;
                        sub.appendChild(sli);
                    });
                    li.appendChild(sub);
                }
                ul.appendChild(li);
            });
            resultsContainer.appendChild(ul);
        }

        // Топ смайлики
        if (res.top_emoticons) {
            resultsContainer.innerHTML += "<h3>Топ смайлики</h3>";
            const grid = document.createElement("div");
            grid.className = "emote-grid";
            res.top_emoticons.forEach(emote => {
                const wr = document.createElement("div");
                wr.className = "emote";
                wr.innerHTML = `
                    <img src="${emote.url}" alt="${emote.name}" title="${emote.name}" width="32" height="32">
                    <div>${emote.name}: ${emote.count}</div>
                `;
                grid.appendChild(wr);
            });
            resultsContainer.appendChild(grid);
        }

        // График активности по минутам
        if (res.chat_activity?.messages_per_minute) {
            const old = document.getElementById("activityChart");
            if (old) old.remove();

            const canvas = document.createElement("canvas");
            canvas.id = "activityChart";
            resultsContainer.innerHTML += "<h3>Активность по минутам</h3>";
            resultsContainer.appendChild(canvas);

            const allData = res.chat_activity.messages_per_minute;
            const keywordData = res.chat_activity.keyword_messages_per_minute || {};

            const minutes = Array.from(new Set([
                ...Object.keys(allData),
                ...Object.keys(keywordData)
            ])).map(m => parseInt(m, 10)).sort((a, b) => a - b);

            const total = minutes.map(m => allData[m] || 0);
            const byKeyword = minutes.map(m => keywordData[m] || 0);

            new Chart(canvas, {
                type: "line",
                data: {
                    labels: minutes.map(m => `${m} мин`),
                    datasets: [
                        {
                            label: "По ключевым словам",
                            data: byKeyword,
                            fill: true,
                            tension: 0.5,
                            borderColor: "#e74c3c",
                            backgroundColor: "rgba(231, 76, 60, 0.2)"
                        },
                        {
                            label: "Все сообщения",
                            data: total,
                            fill: true,
                            tension: 0.5,
                            borderColor: "#3498db",
                            backgroundColor: "rgba(52, 152, 219, 0.1)"
                        }
                    ]
                },
                options: {
                    responsive: true,
                    interaction: { mode: "index", intersect: false },
                    plugins: { legend: { position: "top" } },
                    scales: {
                        x: { title: { display: true, text: "Минута стрима" } },
                        y: { beginAtZero: true, title: { display: true, text: "Количество сообщений" } }
                    }
                }
            });
        }
    }
});