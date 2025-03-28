document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("video_id");
    const button = document.getElementById("submit");
    const resultDiv = document.getElementById("output");
    const loadingDiv = document.getElementById("loading");

    button.addEventListener("click", function () {
        const videoId = input.value.trim();
        if (!videoId) return;

        showLoading(true);
        button.disabled = true;

        fetch("/start-task", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ video_id: videoId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.task_id) {
                checkTaskStatus(data.task_id);
            } else {
                showLoading(false);
                resultDiv.textContent = "Ошибка запуска задачи";
                button.disabled = false;
            }
        })
        .catch(error => {
            showLoading(false);
            resultDiv.textContent = `Ошибка: ${error.message}`;
            button.disabled = false;
        });
    });

    function checkTaskStatus(taskId) {
        const interval = setInterval(() => {
            fetch(`/task-status/${taskId}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === "completed") {
                    clearInterval(interval);
                    showLoading(false);
                    resultDiv.textContent = JSON.stringify(data.result, null, 2);
                    button.disabled = false;
                } else if (data.status === "failed") {
                    clearInterval(interval);
                    showLoading(false);
                    resultDiv.textContent = "Ошибка при обработке задачи";
                    button.disabled = false;
                }
            })
            .catch(error => {
                clearInterval(interval);
                showLoading(false);
                resultDiv.textContent = `Ошибка: ${error.message}`;
                button.disabled = false;
            });
        }, 2000);
    }

    function showLoading(show) {
        if (show) {
            loadingDiv.classList.remove("hidden");
        } else {
            loadingDiv.classList.add("hidden");
        }
    }
});