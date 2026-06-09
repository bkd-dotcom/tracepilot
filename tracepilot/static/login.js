document.addEventListener('DOMContentLoaded', () => {
    // Theme Toggle Logic
    const btnThemeToggle = document.getElementById('btn-theme-toggle');
    if (localStorage.getItem('theme') === 'dark') {
        document.body.classList.add('dark-theme');
        btnThemeToggle.textContent = '☀️';
    }
    
    btnThemeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-theme');
        if (document.body.classList.contains('dark-theme')) {
            localStorage.setItem('theme', 'dark');
            btnThemeToggle.textContent = '☀️';
        } else {
            localStorage.setItem('theme', 'light');
            btnThemeToggle.textContent = '🌙';
        }
    });

    const btnLogin = document.getElementById('btn-login');
    const btnSubmitEmail = document.getElementById('btn-submit-email');
    const emailForm = document.getElementById('email-form');
    const loading = document.getElementById('loading');
    const divider = document.querySelector('.divider');

    // Google Auth Overlay elements
    const googleOverlay = document.getElementById('google-auth-overlay');
    const googleProgress = document.getElementById('google-progress');
    const btnGoogleNext = document.getElementById('btn-google-next');
    const googleEmailInput = document.getElementById('google-email-input');

    // Show Google Overlay
    btnLogin.addEventListener('click', () => {
        googleOverlay.classList.add('active');
        setTimeout(() => {
            googleEmailInput.focus();
        }, 100);
    });

    // Handle "Next" click
    function proceedToApp() {
        if (!googleEmailInput.value) {
            googleEmailInput.style.borderColor = '#d93025'; // Google Red
            return;
        }
        
        googleProgress.classList.add('active');
        btnGoogleNext.style.opacity = '0.7';
        btnGoogleNext.style.cursor = 'wait';
        
        // Simulate OAuth redirect delay
        setTimeout(() => {
            window.location.href = '/app';
        }, 1200);
    }

    if (btnGoogleNext) {
        btnGoogleNext.addEventListener('click', proceedToApp);
    }
    
    if (googleEmailInput) {
        googleEmailInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                proceedToApp();
            }
        });
    }

    // Fallback email login
    function simulateEmailLogin() {
        btnSubmitEmail.style.display = 'none';
        loading.style.display = 'block';

        setTimeout(() => {
            window.location.href = '/app';
        }, 1500);
    }

    btnSubmitEmail.addEventListener('click', simulateEmailLogin);
});
