document.addEventListener('DOMContentLoaded', () => {
    // Theme Toggle Logic
    const SUN_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;
    const MOON_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9.01 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;

    const btnThemeToggle = document.getElementById('btn-theme-toggle');
    if (localStorage.getItem('theme') === 'dark') {
        document.body.classList.add('dark-theme');
        if (btnThemeToggle) btnThemeToggle.innerHTML = SUN_SVG;
    } else {
        if (btnThemeToggle) btnThemeToggle.innerHTML = MOON_SVG;
    }
    
    if (btnThemeToggle) {
        btnThemeToggle.addEventListener('click', () => {
            btnThemeToggle.classList.add('rotating');
            setTimeout(() => {
                document.body.classList.toggle('dark-theme');
                if (document.body.classList.contains('dark-theme')) {
                    localStorage.setItem('theme', 'dark');
                    btnThemeToggle.innerHTML = SUN_SVG;
                } else {
                    localStorage.setItem('theme', 'light');
                    btnThemeToggle.innerHTML = MOON_SVG;
                }
                // Small delay to ensure innerHTML is painted before transitioning back
                setTimeout(() => btnThemeToggle.classList.remove('rotating'), 50);
            }, 300);
        });
    }

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
