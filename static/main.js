document.addEventListener("DOMContentLoaded", () => {
    const vodForm = document.getElementById("vodForm");
    const statusMessage = document.getElementById("status_message");
    const analyticsForm = document.getElementById("analytics_form");
    const resultsContainer = document.getElementById("results");
    const workerStatusCounter = document.getElementById("active_tasks_counter"); // Добавим для отображения количества активных задач
    const maxWorkersCounter = document.getElementById("max_workers_counter");
    let intervalId;

    analyticsForm.style.display = "none";

// Обновление информации о количестве активных задач
async function updateWorkerStatus() {
    try {
        const response = await fetch("/worker_status");
        const data = await response.json();

        workerStatusCounter.textContent = data.active_tasks ?? "–"; // Обновляем счетчик активных задач
        maxWorkersCounter.textContent = data.max_workers ?? "–"; // Обновляем счетчик максимальных воркеров

    } catch (e) {
        console.error("Ошибка при получении статуса воркеров:", e);
    }
}

// Обновить сразу
updateWorkerStatus();
// Повторять обновление каждые 5 секунд
setInterval(updateWorkerStatus, 5000);

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

    analyticsForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        resultsContainer.innerHTML = "";
        statusMessage.textContent = "Запуск аналитики...";

        const submitButton = analyticsForm.querySelector("button[type='submit']");
        submitButton.disabled = true; // Отключаем кнопку, чтобы предотвратить повторное нажатие

        try {
            const formData = new FormData(analyticsForm);
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
                checkAnalysisStatus(data.task_id, submitButton); // передаем кнопку
            } else {
                statusMessage.textContent = "Ошибка запуска аналитики.";
                submitButton.disabled = false; // Восстанавливаем кнопку
            }
        } catch (err) {
            statusMessage.textContent = "Ошибка при отправке формы аналитики.";
            submitButton.disabled = false; // Восстанавливаем кнопку при ошибке
            console.error(err);
        }
    });

    function checkAnalysisStatus(taskId, submitButton) {
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
                    submitButton.disabled = false; // Включаем кнопку после выполнения
                } else {
                    statusMessage.textContent = data.status === "failure"
                        ? "Ошибка выполнения аналитики: " + data.result
                        : "Неизвестный статус задачи.";
                    clearInterval(intervalId);
                    submitButton.disabled = false; // Включаем кнопку при ошибке
                }
            } catch (err) {
                statusMessage.textContent = "Ошибка проверки статуса.";
                clearInterval(intervalId);
                submitButton.disabled = false; // Включаем кнопку при ошибке
                console.error(err);
            }
        }, 1000);
    }

    function renderResults(result) {
        resultsContainer.innerHTML = "";
        const res = result.analysis_result || {};

        if (res.top_chatters) {
            resultsContainer.innerHTML += "<h3>Топ чаттеры</h3>";
            const ul = document.createElement("ul");
            res.top_chatters.forEach(([name, count]) => {
                const li = document.createElement("li");

                // Обрезка длинных ников
                const shortenedName = name.length > 15 ? name.substring(0, 15) + "..." : name;

                // Сокращение "сообщений"
                const messageCount = count + " сообщ.";

                // Создание ссылки с ником
                li.innerHTML = `<a href="https://twitch.tv/${name}" target="_blank">${shortenedName}</a>: ${messageCount}`;
                ul.appendChild(li);
            });
            resultsContainer.appendChild(ul);
        }

        if (res.top_pastes) {
            resultsContainer.innerHTML += "<h3>Топ пасты</h3>";
            const ul = document.createElement("ul");

            res.top_pastes.forEach(paste => {
                const li = document.createElement("li");
                li.innerHTML = `<strong>(${paste.count})</strong> ${paste.base_pasta}`;

                if (paste.variants?.length) {
                    const sub = document.createElement("ul");
                    paste.variants.forEach(v => {
                        const sli = document.createElement("li");
                        sli.textContent = `(${v.count}) ${v.text}`;
                        sub.appendChild(sli);
                    });
                    li.appendChild(sub);
                }

                ul.appendChild(li);
            });

            resultsContainer.appendChild(ul);
        }

        if (res.top_emoticons) {
            resultsContainer.innerHTML += "<h3>Топ смайлики</h3>";
            const grid = document.createElement("div");
            grid.className = "emote-grid";

            res.top_emoticons.forEach(emote => {
                const wr = document.createElement("div");
                wr.className = "emote";
                wr.innerHTML = `
                    <img src="${emote.url}" alt="${emote.name}" title="${emote.name}" width="48" height="48">
                    <div>${emote.count}</div>
                `;
                grid.appendChild(wr);
            });

            resultsContainer.appendChild(grid);
        }

        if (res.chat_activity?.messages_per_minute) {
            const old = document.getElementById("activityChart");
            if (old) old.remove();

            const canvas = document.createElement("canvas");
            canvas.id = "activityChart";
            resultsContainer.innerHTML += "<h3>Активность по минутам</h3>";
            resultsContainer.appendChild(canvas);

            const navDiv = document.createElement("div");
            navDiv.style.margin = "10px 0";
            navDiv.innerHTML = `
                <button id="zoom_in_btn">+</button>
                <button id="zoom_out_btn">−</button>
                <button id="pan_left_btn">←</button>
                <button id="pan_right_btn">→</button>
                <button id="reset_zoom_btn">Сбросить масштаб</button>
            `;
            resultsContainer.appendChild(navDiv);

            const allData = res.chat_activity.messages_per_minute;
            const keywordData = res.chat_activity.keyword_messages_per_minute || {};
            const categoryIntervals = res.chat_activity.category_intervals || [];

            const minutes = Array.from(new Set([
                ...Object.keys(allData),
                ...Object.keys(keywordData)
            ])).map(m => parseInt(m, 10)).sort((a, b) => a - b);

            const total = minutes.map(m => allData[m] || 0);
            const byKeyword = minutes.map(m => keywordData[m] || 0);
            const categoryColors = generateCategoryColorMap(categoryIntervals);

            const chart = new Chart(canvas, {
                type: "line",
                data: {
                    labels: minutes.map(m => `${m} мин`),
                    datasets: [
                        {
                            label: "Ключевые слова",
                            data: byKeyword,
                            fill: true,
                            tension: 0,
                            borderColor: "#e74c3c",
                            borderWidth: 2,
                            backgroundColor: "rgba(231, 76, 60, 0.2)",
                            pointStyle: "rect",
                            pointRadius: 4,
                            pointBorderWidth: 1
                        },
                        {
                            label: "Все сообщения",
                            data: total,
                            fill: true,
                            tension: 0,
                            borderColor: "#3498db",
                            borderWidth: 2,
                            backgroundColor: "rgba(52, 152, 219, 0.1)",
                            pointStyle: "rect",
                            pointRadius: 4,
                            pointBorderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    interaction: { mode: "index", intersect: false },
                    plugins: {
                        legend: { position: "top" },
                        categoryMapBackground: {
                            intervals: categoryIntervals.map(([from, to, label]) => ({ from, to, label })),
                            colors: categoryColors
                        },
                        zoom: {
                            pan: {
                                enabled: true,
                                mode: 'x',
                                threshold: 10,
                                onPanComplete({ chart }) {
                                    const x = chart.scales.x;
                                    if (x.min < 0) chart.resetZoom();
                                },
                                limits: {
                                    x: {
                                        min: 0,
                                        max: minutes.length - 1
                                    }
                                }
                            },
                            zoom: {
                                wheel: { enabled: true },
                                pinch: { enabled: true },
                                mode: 'x',
                                limits: {
                                    x: {
                                        min: 0,
                                        max: minutes.length - 1
                                    },
                                    y: {
                                        min: 0
                                    }
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: { display: true, text: "Минута стрима" }
                        },
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: "Количество сообщений" }
                        }
                    }
                },
                plugins: [categoryMapBackground]
            });

            document.getElementById("zoom_in_btn").onclick = () => chart.zoom(1.2);
            document.getElementById("zoom_out_btn").onclick = () => chart.zoom(0.8);
            document.getElementById("pan_left_btn").onclick = () => chart.pan({ x: 50 });
            document.getElementById("pan_right_btn").onclick = () => chart.pan({ x: -50 });
            document.getElementById("reset_zoom_btn").onclick = () => chart.resetZoom();

            const legendDiv = document.createElement("div");
            legendDiv.innerHTML = "<h4>Категории:</h4>";
            Object.entries(categoryColors).forEach(([label, color]) => {
                const item = document.createElement("div");
                item.style.display = "inline-block";
                item.style.marginRight = "15px";
                item.innerHTML = `<span style="display:inline-block;width:12px;height:12px;background:${color};margin-right:5px;border-radius:2px;"></span>${label}`;
                legendDiv.appendChild(item);
            });
            resultsContainer.appendChild(legendDiv);
        }
    }

// Плагин фона с учётом границ видимой области
const categoryMapBackground = {
    id: 'categoryMapBackground',
    beforeDraw(chart, args, options) {
        const { ctx, chartArea: { top, bottom, left, right }, scales: { x } } = chart;
        if (!options || !options.intervals) return;

        options.intervals.forEach(({ from, to, label }) => {
            const x1 = Math.max(x.getPixelForValue(from), left);
            const x2 = Math.min(x.getPixelForValue(to), right);
            const width = x2 - x1;

            if (width <= 0) return;

            ctx.save();
            const patternCanvas = createStripePattern(options.colors?.[label] || '#ccc');
            const pattern = ctx.createPattern(patternCanvas, 'repeat');

            ctx.fillStyle = pattern;
            ctx.fillRect(x1, top, width, bottom - top);
            ctx.restore();
        });
    }
};

    function createStripePattern(color = '#000', background = '#fff') {
    const canvas = document.createElement('canvas');
    canvas.width = 8;
    canvas.height = 8;
    const ctx = canvas.getContext('2d');

    // Фон
    ctx.fillStyle = background;
    ctx.fillRect(0, 0, 8, 8);

    // Диагональные полосы
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, 8);
    ctx.lineTo(8, 0);
    ctx.stroke();

    return canvas;
}

function createLinePattern(color = '#3498db', bg = 'transparent') {
    const canvas = document.createElement('canvas');
    canvas.width = 8;
    canvas.height = 8;
    const ctx = canvas.getContext('2d');

    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, 8, 8);

    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, 8);
    ctx.lineTo(8, 0);
    ctx.stroke();

    return canvas;
}



    function generateCategoryColorMap(intervals) {
        const colorMap = {};
        intervals.forEach(([, , label]) => {
            if (!colorMap[label]) {
                colorMap[label] = hashColor(label);
            }
        });
        return colorMap;
    }

    function hashColor(label) {
        let hash = 0;
        for (let i = 0; i < label.length; i++) {
            hash = label.charCodeAt(i) + ((hash << 5) - hash);
        }
        const r = (hash >> 0) & 255;
        const g = (hash >> 8) & 255;
        const b = (hash >> 16) & 255;
        return `rgba(${r}, ${g}, ${b}, 0.5)`;
    }
});