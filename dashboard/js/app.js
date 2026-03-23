/**
 * Dashboard App — Asosiy ilova logikasi.
 * Barcha sahifalar, ma'lumotlar yuklash, va UI boshqaruvi.
 */

const App = {
    currentView: 'overview',
    currentFilter: 'week',
    currentGroupId: '',
    dateFrom: null,
    dateTo: null,
    cachedData: {},
    groups: [],

    /** Ilovani boshlash */
    async init() {
        if (!Auth.requireAuth()) return;

        Charts.setDefaults();
        this.loadTheme();
        await this.loadGroups();

        if (this.currentView) this.navigate(this.currentView);
        this.bindEvents();
    },

    /** Hodisalarni bog'lash */
    bindEvents() {
        // Navigation
        document.querySelectorAll('.nav-item[data-view]').forEach(btn => {
            btn.addEventListener('click', () => {
                this.navigate(btn.dataset.view);
                // Mobile
                const sidebar = document.getElementById('sidebar');
                const overlay = document.getElementById('sidebarOverlay');
                if (sidebar) sidebar.classList.remove('open');
                if (overlay) overlay.classList.remove('show');
            });
        });

        // Date filters
        document.querySelectorAll('.filter-btn[data-period]').forEach(btn => {
            btn.addEventListener('click', () => {
                this.setFilter(btn.dataset.period);
            });
        });

        // Group filter click listener is handled in renderGroupIcons

        // Custom date
        const dateFromInput = document.getElementById('dateFrom');
        const dateToInput = document.getElementById('dateTo');
        if (dateFromInput) {
            dateFromInput.addEventListener('change', () => this.applyCustomDate());
        }
        if (dateToInput) {
            dateToInput.addEventListener('change', () => this.applyCustomDate());
        }

        // Theme toggle
        const themeBtn = document.getElementById('themeToggle');
        if (themeBtn) {
            themeBtn.addEventListener('click', () => this.toggleTheme());
        }

        // Logout
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => Auth.logout());
        }

        // Modal
        const chatModalClose = document.getElementById('chatModalClose');
        const chatModal = document.getElementById('chatModal');
        if (chatModalClose) {
            chatModalClose.addEventListener('click', () => this.closeChatModal());
        }
        if (chatModal) {
            chatModal.addEventListener('click', (e) => {
                if (e.target === chatModal) this.closeChatModal();
            });
        }

        // Group Settings Modal
        document.getElementById('closeSettingsModal')?.addEventListener('click', () => this.closeSettingsModal());
        document.getElementById('cancelSettings')?.addEventListener('click', () => this.closeSettingsModal());
        document.getElementById('groupSettingsForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveGroupSettings();
        });

        // Mobile menu
        const menuToggle = document.getElementById('menuToggle');
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebarOverlay');
        if (menuToggle) {
            menuToggle.addEventListener('click', () => {
                sidebar.classList.toggle('open');
                overlay.classList.toggle('show');
            });
        }
        if (overlay) {
            overlay.addEventListener('click', () => {
                sidebar.classList.remove('open');
                overlay.classList.remove('show');
            });
        }
    },

    /** ===== NAVIGATION ===== */
    navigate(view, params = {}) {
        this.currentView = view;
        this.params = params;

        // Nav item active holatini yangilash
        document.querySelectorAll('.nav-item').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === view);
        });

        // Header title yangilash
        const titles = {
            overview: '📊 Overview',
            operators: '👨‍💼 Operatorlar',
            users: '👥 Foydalanuvchilar',
            'operator-detail': '👨‍💼 Operator ma\'lumotlari',
            'user-detail': '👤 Foydalanuvchi ma\'lumotlari',
        };
        document.getElementById('pageTitle').textContent = titles[view] || 'Dashboard';

        // Sahifani ko'rsatish
        this.renderView();
    },

    /** Sahifani chizish */
    async renderView() {
        const content = document.getElementById('pageContent');
        content.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

        switch (this.currentView) {
            case 'overview':
                await this.renderOverview(content);
                break;
            case 'operators':
                await this.renderOperators(content);
                break;
            case 'users':
                await this.renderUsers(content);
                break;
            case 'operator-detail':
                await this.renderOperatorDetail(content);
                break;
            case 'user-detail':
                await this.renderUserDetail(content);
                break;
        }
    },

    /** ===== DATE FILTER ===== */
    setFilter(period) {
        this.currentFilter = period;
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.period === period);
        });

        // Period bo'yicha sanalarni hisoblash
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

        switch (period) {
            case 'today':
                this.dateFrom = today.toISOString().split('T')[0];
                this.dateTo = now.toISOString().split('T')[0];
                break;
            case 'yesterday':
                const yesterday = new Date(today);
                yesterday.setDate(yesterday.getDate() - 1);
                this.dateFrom = yesterday.toISOString().split('T')[0];
                this.dateTo = today.toISOString().split('T')[0];
                break;
            case 'week':
                const weekAgo = new Date(today);
                weekAgo.setDate(weekAgo.getDate() - 7);
                this.dateFrom = weekAgo.toISOString().split('T')[0];
                this.dateTo = now.toISOString().split('T')[0];
                break;
            case 'month':
                const monthAgo = new Date(today);
                monthAgo.setDate(monthAgo.getDate() - 30);
                this.dateFrom = monthAgo.toISOString().split('T')[0];
                this.dateTo = now.toISOString().split('T')[0];
                break;
            default:
                this.dateFrom = null;
                this.dateTo = null;
        }

        this.renderView();
    },

    applyCustomDate() {
        const from = document.getElementById('dateFrom').value;
        const to = document.getElementById('dateTo').value;
        if (from && to) {
            this.dateFrom = from;
            this.dateTo = to;
            this.currentFilter = 'custom';
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            this.renderView();
        }
    },

    /** API query params */
    getQueryParams() {
        const params = new URLSearchParams();
        if (this.dateFrom) params.set('date_from', this.dateFrom);
        if (this.dateTo) params.set('date_to', this.dateTo);
        if (this.currentGroupId) params.set('group_id', this.currentGroupId);
        return params.toString() ? '?' + params.toString() : '';
    },

    /** ===== GROUPS ===== */
    async loadGroups() {
        try {
            const data = await Auth.fetch('/api/stats/groups');
            if (data) {
                this.groups = data;
                this.renderGroupIcons();
            }
        } catch (e) {
            console.error("Gruppalarni yuklashda xato:", e);
        }
    },

    renderGroupIcons() {
        const container = document.getElementById('groupIcons');
        if (!container) return;

        let html = `
            <div class="group-item ${!this.currentGroupId ? 'active' : ''}" data-id="">
                <span>Barchasi</span>
            </div>
        `;

        this.groups.forEach(g => {
            const title = g.custom_title || g.title || 'Unknown';
            const initial = title.charAt(0).toUpperCase();
            html += `
                <div class="group-item ${this.currentGroupId == g.id ? 'active' : ''}" data-id="${g.id}">
                    <div class="group-initial">${initial}</div>
                    <span>${this.escapeHtml(title)}</span>
                </div>
            `;
        });

        if (this.currentGroupId) {
            html += `
                <div class="group-settings-btn" id="openSettingsBtn" title="Sozlamalar">
                    ⚙️
                </div>
            `;
        }

        container.innerHTML = html;

        // Group click
        container.querySelectorAll('.group-item').forEach(item => {
            item.addEventListener('click', () => {
                this.currentGroupId = item.dataset.id || '';
                this.renderGroupIcons();
                this.renderView();
            });
        });

        // Settings button
        const settingsBtn = document.getElementById('openSettingsBtn');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.openGroupSettings(this.currentGroupId);
            });
        }
    },

    openGroupSettings(groupId) {
        const group = this.groups.find(g => g.id == groupId);
        if (!group) return;

        document.getElementById('editGroupId').value = group.id;
        document.getElementById('originalGroupTitle').textContent = group.title;
        document.getElementById('customGroupTitle').value = group.custom_title || '';
        document.getElementById('groupLink').value = group.group_link || '';

        document.getElementById('groupSettingsModal').style.display = 'flex';
    },

    closeSettingsModal() {
        const modal = document.getElementById('groupSettingsModal');
        if (modal) modal.style.display = 'none';
    },

    async saveGroupSettings() {
        const id = document.getElementById('editGroupId').value;
        const custom_title = document.getElementById('customGroupTitle').value;
        const group_link = document.getElementById('groupLink').value;

        try {
            const data = await Auth.fetch(`/api/stats/groups/${id}`, {
                method: 'PUT',
                body: JSON.stringify({ custom_title, group_link })
            });

            if (data) {
                await this.loadGroups();
                this.closeSettingsModal();
                this.renderView();
            }
        } catch (error) {
            console.error('Error saving group settings:', error);
            alert('Xatolik yuz berdi');
        }
    },

    /** ===== OVERVIEW PAGE ===== */
    async renderOverview(container) {
        const q = this.getQueryParams();
        const [overview, messages, unanswered, answered] = await Promise.all([
            Auth.fetch(`/api/stats/overview${q}`),
            Auth.fetch(`/api/stats/daily-messages${q}`),
            Auth.fetch(`/api/stats/unanswered${q}`),
            Auth.fetch(`/api/stats/conversations${q}`) // This includes answered messages
        ]);

        if (!overview) return;

        container.innerHTML = `
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon blue">📨</div>
                    <div class="stat-label">Jami xabarlar</div>
                    <div class="stat-value">${this.formatNumber(overview.total_messages)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon green">👥</div>
                    <div class="stat-label">Foydalanuvchilar</div>
                    <div class="stat-value">${this.formatNumber(overview.unique_users)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon yellow">⏱</div>
                    <div class="stat-label">Javob vaqti (o'rtacha)</div>
                    <div class="stat-value">${this.formatTime(overview.avg_response_time)}</div>
                </div>
            </div>

            <!-- Main State Units -->
            <div class="tables-grid" style="grid-template-columns: 1fr 1fr; margin-top:24px; gap:24px">
                <!-- Unit 1: Unanswered -->
                <div class="table-card" style="border-top: 4px solid var(--danger); min-height:400px">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px">
                        <h2 style="margin:0"><span class="icon" style="background:var(--danger-soft); color:var(--danger); padding:8px; border-radius:12px; margin-right:8px">❌</span> Javob berilmaganlar</h2>
                        <div class="badge danger" style="font-size:1.2rem; padding:8px 16px">${this.formatNumber(overview.unanswered_users)}</div>
                    </div>
                    ${this.renderUnansweredTable(unanswered?.unanswered || [])}
                </div>

                <!-- Unit 2: Answered -->
                <div class="table-card" style="border-top: 4px solid var(--success); min-height:400px">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px">
                        <h2 style="margin:0"><span class="icon" style="background:var(--success-soft); color:var(--success); padding:8px; border-radius:12px; margin-right:8px">✅</span> Javob berilganlar</h2>
                        <div class="badge success" style="font-size:1.2rem; padding:8px 16px">${overview.response_rate}%</div>
                    </div>
                    ${this.renderRecentMessagesTable((answered?.recent_messages || []).filter(m => m.is_answered))}
                </div>
            </div>

            <!-- Charts & Recent Activity -->
            <div class="charts-grid" style="margin-top:24px">
                <div class="chart-card">
                    <h3><span class="icon">📈</span> Kunlik xabarlar</h3>
                    <div class="chart-container"><canvas id="dailyMessagesChart"></canvas></div>
                </div>
                <div class="chart-card full-width">
                    <h3><span class="icon">💬</span> Barcha so'nggi xabarlar</h3>
                    ${this.renderRecentMessagesTable(answered?.recent_messages || [])}
                </div>
            </div>
        `;

        // Chartlarni chizish
        setTimeout(() => {
            Charts.createDailyMessages('dailyMessagesChart', messages?.daily_messages || []);
        }, 100);
    },


    /** ===== USERS PAGE ===== */
    /** ===== USERS PAGE ===== */
    async renderUsers(container) {
        const q = this.getQueryParams();
        const data = await Auth.fetch(`/api/stats/users${q}`);
        if (!data) return;

        container.innerHTML = `
            <div class="table-card full-width">
                <h3><span class="icon">👥</span> Barcha foydalanuvchilar</h3>
                ${this.renderUsersTable(data.users || [])}
            </div>
        `;
    },

    /** ===== USER DETAIL PAGE ===== */
    async renderUserDetail(container) {
        const data = await Auth.fetch(`/api/stats/users/${this.params.id}`);
        if (!data) {
            container.innerHTML = '<div class="empty-state"><div class="icon">❌</div><p>Foydalanuvchi topilmadi</p></div>';
            return;
        }

        container.innerHTML = `
            <button class="back-btn" onclick="App.navigate('users')">← Orqaga</button>
            <div class="detail-header">
                <div class="detail-avatar">${(data.name || '?')[0].toUpperCase()}</div>
                <div class="detail-info">
                    <h2>${data.name}</h2>
                    <p>${data.username ? '@' + data.username : 'Username yo\'q'} · Telegram ID: ${data.telegram_id}</p>
                </div>
            </div>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon blue">💬</div>
                    <div class="stat-label">Xabarlar soni</div>
                    <div class="stat-value">${data.message_count}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon green">📅</div>
                    <div class="stat-label">Birinchi ko'rinish</div>
                    <div class="stat-value" style="font-size:18px">${data.first_seen ? this.formatDate(data.first_seen) : '-'}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon yellow">📅</div>
                    <div class="stat-label">Oxirgi ko'rinish</div>
                    <div class="stat-value" style="font-size:18px">${data.last_seen ? this.formatDate(data.last_seen) : '-'}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon ${data.is_answered ? 'green' : 'red'}">
                        ${data.is_answered ? '✅' : '❌'}
                    </div>
                    <div class="stat-label">Holat</div>
                    <div class="stat-value" style="font-size:18px">
                        <span class="badge ${data.is_answered ? 'success' : 'danger'}">
                            ${data.is_answered ? 'Javob berilgan' : 'Javobsiz'}
                        </span>
                    </div>
                </div>
            </div>
        `;
    },

    /** ===== TABLE RENDERERS ===== */

    renderUsersTable(users) {
        if (!users.length) return '<div class="empty-state"><p>Ma\'lumot yo\'q</p></div>';
        return `
    < div style = "overflow-x:auto" >
        <table class="data-table">
            <thead><tr><th>#</th><th>Ism</th><th>Xabarlar</th></tr></thead>
            <tbody>
                ${users.slice(0, 10).map((u, i) => `
                        <tr style="cursor:pointer" onclick="App.navigate('user-detail',{id:${u.id}})">
                            <td>${i + 1}</td>
                            <td><div class="user-name"><div class="avatar">${(u.name || '?')[0].toUpperCase()}</div>${u.name}</div></td>
                            <td><strong>${u.message_count}</strong></td>
                        </tr>
                    `).join('')}
            </tbody>
        </table></div >
            `;
    },

    renderOperatorsTable(operators) {
        if (!operators.length) return '<div class="empty-state"><p>Ma\'lumot yo\'q</p></div>';
        return `
            < div style = "overflow-x:auto" >
                <table class="data-table">
                    <thead><tr><th>#</th><th>Operator</th><th>Javoblar</th><th>Vaqt</th></tr></thead>
                    <tbody>
                        ${operators.slice(0, 10).map((op, i) => `
                        <tr style="cursor:pointer" onclick="App.navigate('operator-detail',{id:${op.id}})">
                            <td>${i < 3 ? ['🥇', '🥈', '🥉'][i] : i + 1}</td>
                            <td><div class="user-name"><div class="avatar">${(op.name || '?')[0].toUpperCase()}</div>${op.name}</div></td>
                            <td><strong>${op.total_replies}</strong></td>
                            <td>${this.formatTime(op.avg_response_time)}</td>
                        </tr>
                    `).join('')}
                    </tbody>
                </table></div >
                    `;
    },

    formatTime(seconds) {
        if (!seconds || seconds === 0) return '0s';
        if (seconds > 86400) return Math.round(seconds / 86400) + ' kun';
        if (seconds > 3600) return (seconds / 3600).toFixed(1) + ' soat';
        if (seconds > 60) return Math.round(seconds / 60) + ' daq';
        return Math.round(seconds) + 's';
    },

    formatDate(isoStr) {
        if (!isoStr) return '-';
        const d = new Date(isoStr);
        return d.toLocaleDateString('uz-UZ', { day: '2-digit', month: '2-digit', year: 'numeric' })
            + ' ' + d.toLocaleTimeString('uz-UZ', { hour: '2-digit', minute: '2-digit' });
    },

    escapeHtml(str) {
        const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
        return (str || '').replace(/[&<>"']/g, c => map[c]);
    },

    renderUnansweredTable(items) {
        if (!items.length) return '<div class="empty-state"><p>✅ Barcha xabarlarga javob berilgan</p></div>';
        return `
            <div style="overflow-x:auto">
                <table class="data-table">
                    <thead><tr><th>Foydalanuvchi</th><th>Kutish</th><th>Sana</th></tr></thead>
                    <tbody>
                        ${items.slice(0, 10).map(item => `
                            <tr>
                                <td>
                                    <div class="user-name">
                                        <div class="avatar">${(item.name || '?')[0].toUpperCase()}</div>
                                        ${this.escapeHtml(item.username ? '@' + item.username : item.name)}
                                    </div>
                                </td>
                                <td><span class="badge danger">${this.formatTime(item.waiting_time)}</span></td>
                                <td style="font-size:12px">${this.formatDate(item.created_at)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    },

    renderRecentMessagesTable(messages) {
        if (!messages.length) return '<div class="empty-state"><p>Ma\'lumot yo\'q</p></div>';
        return `
            <div style="overflow-x:auto">
                <table class="data-table">
                    <thead><tr><th>Foydalanuvchi</th><th>Xabar</th><th>Vaqt</th></tr></thead>
                    <tbody>
                        ${messages.slice(0, 20).map(msg => `
                            <tr>
                                <td>
                                    <div class="user-name">
                                        <div class="avatar" style="${msg.is_from_operator ? 'background:var(--success-soft);color:var(--success)' : ''}">
                                            ${(msg.name || '?')[0].toUpperCase()}
                                        </div>
                                        ${this.escapeHtml(msg.username ? '@' + msg.username : msg.name)}
                                    </div>
                                </td>
                                <td style="max-width:250px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
                                    ${msg.is_from_operator ? '<span class="badge success" style="margin-right:4px">Javob</span>' : ''}
                                    ${this.escapeHtml(msg.text || '(media)')}
                                </td>
                                <td style="font-size:11px;white-space:nowrap">${this.formatDate(msg.date)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    },

    renderUsersTable(users) {
        if (!users.length) return '<div class="empty-state"><p>Ma\'lumot yo\'q</p></div>';
        return `
            <div style="overflow-x:auto">
                <table class="data-table">
                    <thead><tr><th>#</th><th>Foydalanuvchi</th><th>Xabarlar</th><th>Amal</th></tr></thead>
                    <tbody>
                        ${users.slice(0, 50).map((u, i) => `
                            <tr>
                                <td>${i + 1}</td>
                                <td>
                                    <div class="user-name">
                                        <div class="avatar">${(u.name || '?')[0].toUpperCase()}</div>
                                        <div>
                                            <div style="font-weight:600">${this.escapeHtml(u.name)}</div>
                                            <div style="font-size:11px;color:var(--text-muted)">${u.username ? '@' + u.username : ''}</div>
                                        </div>
                                    </div>
                                </td>
                                <td><strong>${u.message_count}</strong></td>
                                <td><button class="filter-btn" onclick="App.navigate('user-detail',{id:${u.id}})">Batafsil</button></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    },

    /** ===== CHAT MODAL LOGIC ===== */
    async openChatModal(type) {
        const modal = document.getElementById('chatModal');
        const title = document.getElementById('chatModalTitle');
        const loading = document.getElementById('chatModalLoading');
        const content = document.getElementById('chatModalContent');

        modal.classList.remove('hidden');
        title.textContent = type === 'unanswered' ? '❌ Javobsiz qolgan suhbatlar' : '✅ Javob berilgan suhbatlar';
        content.innerHTML = '';
        loading.classList.remove('hidden');

        try {
            const endpoint = type === 'unanswered' ? '/api/stats/unanswered' : '/api/stats/answered';
            const data = await Auth.fetch(`${endpoint}${this.getQueryParams()}`);

            loading.classList.add('hidden');

            const list = data[type] || [];
            if (list.length === 0) {
                content.innerHTML = '<div class="empty-state"><p>Ma\'lumot topilmadi</p></div>';
                return;
            }

            content.innerHTML = list.map(chat => `
                <div class="chat-item">
                    <div class="chat-header">
                        <div class="chat-user">${this.escapeHtml(chat.name)} ${chat.username ? `<span style="color:var(--text-muted);font-weight:400">@${chat.username}</span>` : ''}</div>
                        <div class="chat-time">${this.formatDate(chat.created_at)}</div>
                    </div>
                    ${chat.group_title ? `<div class="chat-group-badge">Guruh: ${this.escapeHtml(chat.group_title)}</div>` : ''}
                    <div class="chat-text">
                        ${this.escapeHtml(chat.message_text ? `"${chat.message_text}"` : '(Xabar matni yo\'q)')}
                    </div>
                    <div style="font-size:12px;color:var(--${type === 'answered' ? 'success' : 'danger'});margin-bottom:8px">
                        ${type === 'answered' ? `Javob berilgan (Kutish: ${this.formatTime(chat.response_time)})` : `Kutmoqda: ${this.formatTime(chat.waiting_time)}`}
                    </div>
                </div>
            `).join('');

        } catch (error) {
            loading.classList.add('hidden');
            content.innerHTML = '<div class="empty-state"><p style="color:var(--danger)">Xatolik yuz berdi</p></div>';
        }
    },

    closeChatModal() {
        document.getElementById('chatModal').classList.add('hidden');
    },

    /** ===== THEME & UTILS ===== */
    toggleTheme() {
        const html = document.documentElement;
        const isDark = html.getAttribute('data-theme') !== 'light';
        html.setAttribute('data-theme', isDark ? 'light' : 'dark');
        localStorage.setItem('theme', isDark ? 'light' : 'dark');

        const btn = document.getElementById('themeToggle');
        if (btn) btn.innerHTML = isDark ? '🌙 Dark mode' : '☀️ Light mode';

        Charts.updateTheme(!isDark);
        this.renderView();
    },

    loadTheme() {
        const saved = localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-theme', saved);
        Charts.isDark = saved === 'dark';
        Charts.setDefaults();
        const btn = document.getElementById('themeToggle');
        if (btn) btn.innerHTML = saved === 'dark' ? '☀️ Light mode' : '🌙 Dark mode';
    },

    formatNumber(n) {
        if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
        if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
        return (n || 0).toString();
    },
};

// Ilovani boshlash
document.addEventListener('DOMContentLoaded', () => App.init());
