document.addEventListener("DOMContentLoaded", () => {
    const vodForm = document.getElementById("vodForm");
    const statusMessage = document.getElementById("status_message");
    const analyticsForm = document.getElementById("analytics_form");
    const resultsContainer = document.getElementById("results");
    const workerStatusCounter = document.getElementById("active_tasks_counter"); // Добавим для отображения количества активных задач
    let intervalId;

    analyticsForm.style.display = "none";

    // Обновление информации о количестве активных задач
    async function updateWorkerStatus() {
        try {
            const response = await fetch("/worker_status");
            const data = await response.json();
            workerStatusCounter.textContent = data.active_tasks ?? "–"; // Обновляем счетчик
        } catch (e) {
            console.error("Ошибка при получении статуса воркеров:", e);
        }
    }

    // Обновить сразу
    updateWorkerStatus();
    // Повторять обновление каждые 10 секунд
    setInterval(updateWorkerStatus, 1000);

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
                checkAnalysisStatus(data.task_id);
            } else {
                statusMessage.textContent = "Ошибка запуска аналитики.";
            }
        } catch (err) {
            statusMessage.textContent = "Ошибка при отправке формы аналитики.";
            console.error(err);
        }
    });

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

    function renderResults(result) {
        resultsContainer.innerHTML = "";
        const res = result.analysis_result || {};

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
                    plugins: {
                        legend: { position: "top" },
                        categoryMapBackground: {
                            intervals: categoryIntervals.map(([from, to, label]) => ({ from, to, label })),
                            colors: categoryColors
                        },
                        zoom: {
                            zoom: {
                                wheel: { enabled: true },
                                pinch: { enabled: true },
                                mode: 'x'
                            },
                            pan: {
                                enabled: true,
                                mode: 'x',
                                threshold: 10
                            },
                            limits: {
                                x: { min: 'original', max: 'original' },
                                y: { min: 0 }
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

    const categoryMapBackground = {
        id: 'categoryMapBackground',
        beforeDraw(chart, args, options) {
            const { ctx, chartArea: { top, bottom }, scales: { x } } = chart;
            if (!options || !options.intervals) return;

            options.intervals.forEach(({ from, to, label }) => {
                const x1 = x.getPixelForValue(from);
                const x2 = x.getPixelForValue(to);
                const width = x2 - x1;

                ctx.save();
                ctx.fillStyle = options.colors?.[label] || 'rgba(200, 200, 200, 0.3)';
                ctx.fillRect(x1, top, width, bottom - top);
                ctx.restore();
            });
        }
    };

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
        return `rgba(${r}, ${g}, ${b}, 0.3)`;
    }
});