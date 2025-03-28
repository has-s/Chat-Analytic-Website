document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form');
    const input = document.getElementById('vod_url');

    form.addEventListener('submit', (event) => {
        const vodUrl = input.value.trim();

        if (!vodUrl) {
            alert("Пожалуйста, введите URL трансляции.");
            event.preventDefault();
            return;
        }
    });
});