const root = document.documentElement;
const themeToggle = document.querySelector('[data-theme-toggle]');
const themeIcon = document.querySelector('[data-theme-icon]');
const savedTheme = localStorage.getItem('railway-defect-detection-system-theme') || 'light';

function applyTheme(theme) {
    root.dataset.theme = theme;
    if (themeIcon) {
        themeIcon.textContent = theme === 'dark' ? '🌙' : '☀️';
    }
    localStorage.setItem('railway-defect-detection-system-theme', theme);
}

applyTheme(savedTheme);
themeToggle?.addEventListener('click', () => applyTheme(root.dataset.theme === 'dark' ? 'light' : 'dark'));
document.querySelector('[data-menu]')?.addEventListener('click', () => document.querySelector('[data-nav]').classList.toggle('open'));
