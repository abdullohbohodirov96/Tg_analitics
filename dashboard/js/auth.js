/**
 * Auth Helper — Token boshqaruvi va API so'rovlar uchun.
 */

const Auth = {
    /** Token ni olish */
    getToken() {
        return localStorage.getItem('token');
    },

    /** Token ni saqlash */
    setToken(token) {
        localStorage.setItem('token', token);
    },

    /** Token ni o'chirish va login sahifasiga yo'naltirish */
    logout() {
        localStorage.removeItem('token');
        window.location.href = '/login';
    },

    /** Foydalanuvchi tizimga kirganmi */
    isAuthenticated() {
        return !!this.getToken();
    },

    /** Auth tekshirish — kirilmagan bo'lsa loginga yo'naltirish */
    requireAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = '/login';
            return false;
        }
        return true;
    },

    /**
     * API ga so'rov yuborish (auth header bilan)
     * @param {string} url - API endpoint
     * @param {object} options - fetch opsiyalari
     * @returns {Promise<any>}
     */
    async fetch(url, options = {}) {
        const token = this.getToken();
        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {}),
        };
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(url, { ...options, headers });

        // Token muddati o'tgan bo'lsa
        if (response.status === 401) {
            this.logout();
            return null;
        }

        return response.json();
    },
};
