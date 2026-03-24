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

        try {
            const response = await fetch(url, { ...options, headers, timeout: 30000 });

            if (response.status === 401) {
                console.error('Unauthorized - logging out');
                this.logout();
                return null;
            }

            if (!response.ok) {
                const error = await response.text();
                console.error(`API Error ${response.status} (${url}): ${error}`);
                // Return empty data structure based on endpoint
                if (url.includes('/tasks')) return { tasks: [] };
                if (url.includes('/history')) return { history_feed: [] };
                if (url.includes('/conversations')) return { unanswered: [], recent_messages: [] };
                if (url.includes('/users')) return { users: [] };
                if (url.includes('/operators')) return { active: [], predefined: [] };
                return null;
            }

            const data = await response.json();
            console.log(`API Success (${url}):`, data);
            return data || {};
        } catch (error) {
            console.error(`Fetch error (${url}):`, error);
            // Return empty data structure to prevent loading spinner
            if (url.includes('/tasks')) return { tasks: [] };
            if (url.includes('/history')) return { history_feed: [] };
            if (url.includes('/conversations')) return { unanswered: [], recent_messages: [] };
            if (url.includes('/users')) return { users: [] };
            if (url.includes('/operators')) return { active: [], predefined: [] };
            return null;
        }
    },
};
