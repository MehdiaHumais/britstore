// Dashboard-specific JS
document.addEventListener('DOMContentLoaded', () => {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', () => {
            const label = input.closest('.form-group')?.querySelector('label');
            if (label && input.files?.[0]) {
                label.dataset.filename = input.files[0].name;
            }
        });
    });
});
