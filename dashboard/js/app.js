/**
 * Dashboard App — Asosiy ilova logikasi.
 * Barcha sahifalar, ma'lumotlar yuklash, va UI boshqaruvi.
 */

const App = {
    currentView: 'overview',
    currentFilter: 'week',
    dateFrom: null,
    dateTo: null,
    cachedData: {},

    /** Ilovani boshlash */
    init() {
        if (!Auth.requireAuth()) return;

        Charts.setDefaults();
        this.bindEvents();
        this.loadTheme();
        this.navigate('overview');
    },

    /** Hodisalarni bog'lash */
    bindEvents() {
        // Navigation
        document.querySelectorAll('.nav-item[data-view]').forEach(btn => {
            btn.addEventListener('click', () => {
                this.navigate(btn.dataset.view);
            });
        });

        // Date filters
        document.querySelectorAll('.filter-btn[data-period]').forEach(btn => {
            btn.addEventListener('click', () => {
                this.setFilter(btn.dataset.period);
            });
        });

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
        return params.toString() ? '?' + params.toString() : '';
    },

    /** ===== OVERVIEW PAGE ===== */
    async renderOverview(container) {
        const q = this.getQueryParams();

        // Barcha ma'lumotlarni parallel yuklash
        const [overview, messages, responseTime, operators, heatmap, userGrowth, conversations, unanswered, users] = await Promise.all([
            Auth.fetch(`/api/stats/overview${q}`),
            Auth.fetch(`/api/stats/messages${q}`),
            Auth.fetch(`/api/stats/response-time${q}`),
            Auth.fetch(`/api/stats/operators${q}`),
            Auth.fetch(`/api/stats/heatmap${q}`),
            Auth.fetch(`/api/stats/user-growth${q}`),
            Auth.fetch(`/api/stats/conversations${q}`),
            Auth.fetch(`/api/stats/unanswered${q}`),
            Auth.fetch(`/api/stats/users${q}`),
        ]);

        if (!overview) return;

        container.innerHTML = `
            <!-- Stat Cards -->
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon blue">📨</div>
                    <div class="stat-label">Jami xabarlar</div>
                    <div class="stat-value">${this.formatNumber(overview.total_messages)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon green">👥</div>
                    <div class="stat-label">Unique foydalanuvchilar</div>
                    <div class="stat-value">${this.formatNumber(overview.unique_users)}</div>
                </div>
                <div class="stat-card clickable-card" onclick="App.openChatModal('answered')">
                    <div class="stat-icon purple">✅</div>
                    <div class="stat-label">Javob berilgan (Javob darajasi)</div>
                    <div class="stat-value">${overview.response_rate}%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon yellow">⏱</div>
                    <div class="stat-label">O'rtacha javob vaqti</div>
                    <div class="stat-value">${this.formatTime(overview.avg_response_time)}</div>
                </div>
                <div class="stat-card clickable-card" onclick="App.openChatModal('unanswered')">
                    <div class="stat-icon red">❌</div>
                    <div class="stat-label">Javobsiz userlar</div>
                    <div class="stat-value">${this.formatNumber(overview.unanswered_users)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon blue">👨‍💼</div>
                    <div class="stat-label">Faol operatorlar</div>
                    <div class="stat-value">${overview.active_operators}</div>
                </div>
            </div>

            <!-- Charts Row 1 -->
            <div class="charts-grid">
                <div class="chart-card">
                    <h3><span class="icon">📈</span> Kunlik xabarlar</h3>
                    <div class="chart-container"><canvas id="dailyMessagesChart"></canvas></div>
                </div>
                <div class="chart-card">
                    <h3><span class="icon">⏱</span> Javob vaqti trendi</h3>
                    <div class="chart-container"><canvas id="responseTimeChart"></canvas></div>
                </div>
                <div class="chart-card">
                    <h3><span class="icon">👨‍💼</span> Operator samaradorligi</h3>
                    <div class="chart-container"><canvas id="operatorChart"></canvas></div>
                </div>
                <div class="chart-card">
                    <h3><span class="icon">👥</span> Foydalanuvchilar o'sishi</h3>
                    <div class="chart-container"><canvas id="userGrowthChart"></canvas></div>
                </div>
                <div class="chart-card full-width">
                    <h3><span class="icon">🔥</span> Faollik heatmapi (soatlar bo'yicha)</h3>
                    <div id="heatmapContainer"></div>
                </div>
            </div>

            <!-- Tables -->
            <div class="tables-grid">
                <div class="table-card">
                    <h3><span class="icon">🏆</span> Eng faol foydalanuvchilar</h3>
                    ${this.renderUsersTable(users?.users || [])}
                </div>
                <div class="table-card">
                    <h3><span class="icon">👨‍💼</span> Eng yaxshi operatorlar</h3>
                    ${this.renderOperatorsTable(operators?.operators || [])}
                </div>
                <div class="table-card">
                    <h3><span class="icon">❌</span> Javobsiz suhbatlar</h3>
                    ${this.renderUnansweredTable(unanswered?.unanswered || [])}
                </div>
                <div class="table-card">
                    <h3><span class="icon">🐢</span> Sekin javoblar</h3>
                    ${this.renderSlowResponsesTable(conversations?.slow_responses || [])}
                </div>
                <div class="table-card full-width">
                    <h3><span class="icon">💬</span> So'nggi xabarlar</h3>
                    ${this.renderRecentMessagesTable(conversations?.recent_messages || [])}
                </div>
            </div>
        `;

        // Chartlarni chizish
        setTimeout(() => {
            Charts.createDailyMessages('dailyMessagesChart', messages?.daily_messages || []);
            Charts.createResponseTimeTrend('responseTimeChart', responseTime?.response_time_trend || []);
            Charts.createOperatorPerformance('operatorChart', operators?.operators || []);
            Charts.createUserGrowth('userGrowthChart', userGrowth?.user_growth || []);
            Charts.createHeatmap('heatmapContainer', heatmap?.heatmap || []);
        }, 100);
    },

    /** ===== OPERATORS PAGE ===== */
    async renderOperators(container) {
        const q = this.getQueryParams();
        const data = await Auth.fetch(`/api/stats/operators${q}`);
        if (!data) return;

        const operators = data.operators || [];

        container.innerHTML = `
            <div class="stats-grid" style="margin-bottom:24px">
                <div class="stat-card">
                    <div class="stat-icon blue">👨‍💼</div>
                    <div class="stat-label">Jami operatorlar</div>
                    <div class="stat-value">${operators.length}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon green">💬</div>
                    <div class="stat-label">Jami javoblar</div>
                    <div class="stat-value">${this.formatNumber(operators.reduce((s, o) => s + o.total_replies, 0))}</div>
                </div>
            </div>
            <div class="table-card full-width">
                <h3><span class="icon">🏆</span> Operatorlar reytingi</h3>
                <div style="overflow-x:auto">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Operator</th>
                                <th>Javoblar</th>
                                <th>O'rtacha vaqt</th>
                                <th>Javob berilgan userlar</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            ${operators.map((op, i) => `
                                <tr>
                                    <td>${i < 3 ? ['🥇', '🥈', '🥉'][i] : i + 1}</td>
                                    <td>
                                        <div class="user-name">
                                            <div class="avatar">${(op.name || '?')[0].toUpperCase()}</div>
                                            ${op.name}${op.username ? ` <span style="color:var(--text-muted)">@${op.username}</span>` : ''}
                                        </div>
                                    </td>
                                    <td><strong>${op.total_replies}</strong></td>
                                    <td>${this.formatTime(op.avg_response_time)}</td>
                                    <td>${op.answered_users}</td>
                                    <td><button class="filter-btn" onclick="App.navigate('operator-detail', {id:${op.id}})">Batafsil →</button></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                ${operators.length === 0 ? '<div class="empty-state"><div class="icon">👨‍💼</div><p>Hozircha operator ma\'lumotlari yo\'q</p></div>' : ''}
            </div>
        `;
    },

    /** ===== USERS PAGE ===== */
    async renderUsers(container) {
        const q = this.getQueryParams();
        const data = await Auth.fetch(`/api/stats/users${q}`);
        if (!data) return;

        const users = data.users || [];

        container.innerHTML = `
            <div class="table-card full-width">
                <h3><span class="icon">👥</span> Foydalanuvchilar ro'yxati</h3>
                <div style="overflow-x:auto">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Foydalanuvchi</th>
                                <th>Xabarlar</th>
                                <th>Birinchi ko'rinish</th>
                                <th>Oxirgi ko'rinish</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            ${users.map((user, i) => `
                                <tr>
                                    <td>${i + 1}</td>
                                    <td>
                                        <div class="user-name">
                                            <div class="avatar">${(user.name || '?')[0].toUpperCase()}</div>
                                            ${user.name}${user.username ? ` <span style="color:var(--text-muted)">@${user.username}</span>` : ''}
                                        </div>
                                    </td>
                                    <td><strong>${user.message_count}</strong></td>
                                    <td>${user.first_seen ? this.formatDate(user.first_seen) : '-'}</td>
                                    <td>${user.last_seen ? this.formatDate(user.last_seen) : '-'}</td>
                                    <td><button class="filter-btn" onclick="App.navigate('user-detail', {id:${user.id}})">Batafsil →</button></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                ${users.length === 0 ? '<div class="empty-state"><div class="icon">👥</div><p>Hozircha foydalanuvchi ma\'lumotlari yo\'q</p></div>' : ''}
            </div>
        `;
    },

    /** ===== OPERATOR DETAIL PAGE ===== */
    async renderOperatorDetail(container) {
        const data = await Auth.fetch(`/api/stats/operators/${this.params.id}`);
        if (!data) {
            container.innerHTML = '<div class="empty-state"><div class="icon">❌</div><p>Operator topilmadi</p></div>';
            return;
        }

        container.innerHTML = `
            <button class="back-btn" onclick="App.navigate('operators')">← Orqaga</button>
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
                    <div class="stat-label">Jami javoblar</div>
                    <div class="stat-value">${data.total_replies}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon yellow">⏱</div>
                    <div class="stat-label">O'rtacha javob vaqti</div>
                    <div class="stat-value">${this.formatTime(data.avg_response_time)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon green">👥</div>
                    <div class="stat-label">Javob berilgan userlar</div>
                    <div class="stat-value">${data.answered_users}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon red">❌</div>
                    <div class="stat-label">Javobsiz suhbatlar</div>
                    <div class="stat-value">${data.unanswered_chats}</div>
                </div>
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
                <div class="stat-card">
                    <div class="stat-icon purple">📊</div>
                    <div class="stat-label">Suhbatlar</div>
                    <div class="stat-value">${data.answered_conversations}/${data.total_conversations}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon blue">👨‍💼</div>
                    <div class="stat-label">Operator</div>
                    <div class="stat-value" style="font-size:16px">${data.operator ? data.operator.name : 'Tayinlanmagan'}</div>
                </div>
            </div>
        `;
    },

    /** ===== TABLE RENDERERS ===== */

    renderUsersTable(users) {
        if (!users.length) return '<div class="empty-state"><p>Ma\'lumot yo\'q</p></div>';
        return `
            <div style="overflow-x:auto">
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
            </table></div>
        `;
    },

    renderOperatorsTable(operators) {
        if (!operators.length) return '<div class="empty-state"><p>Ma\'lumot yo\'q</p></div>';
        return `
            <div style="overflow-x:auto">
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
            </table></div>
        `;
    },

    renderUnansweredTable(items) {
        if (!items.length) return '<div class="empty-state"><p>✅ Barcha xabarlarga javob berilgan</p></div>';
        return `
            <div style="overflow-x:auto">
            <table class="data-table">
                <thead><tr><th>Foydalanuvchi</th><th>Kutish vaqti</th><th>Sana</th></tr></thead>
                <tbody>
                    ${items.slice(0, 10).map(item => `
                        <tr>
                            <td><div class="user-name"><div class="avatar">${(item.name || '?')[0].toUpperCase()}</div>${item.username ? '@' + item.username : item.name}</div></td>
                            <td><span class="badge danger">${this.formatTime(item.waiting_time)}</span></td>
                            <td>${this.formatDate(item.created_at)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table></div>
        `;
    },

    renderSlowResponsesTable(items) {
        if (!items.length) return '<div class="empty-state"><p>Ma\'lumot yo\'q</p></div>';
        return `
            <div style="overflow-x:auto">
            <table class="data-table">
                <thead><tr><th>Foydalanuvchi</th><th>Javob vaqti</th><th>Sana</th></tr></thead>
                <tbody>
                    ${items.slice(0, 10).map(item => `
                        <tr>
                            <td><div class="user-name"><div class="avatar">${(item.name || '?')[0].toUpperCase()}</div>${item.username ? '@' + item.username : item.name}</div></td>
                            <td><span class="badge warning">${this.formatTime(item.response_time)}</span></td>
                            <td>${this.formatDate(item.created_at)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table></div>
        `;
    },

    renderRecentMessagesTable(messages) {
        if (!messages.length) return '<div class="empty-state"><p>Ma\'lumot yo\'q</p></div>';
        return `
            <div style="overflow-x:auto">
            <table class="data-table">
                <thead><tr><th>Foydalanuvchi</th><th>Xabar</th><th>Turi</th><th>Vaqt</th></tr></thead>
                <tbody>
                    ${messages.slice(0, 20).map(msg => `
                        <tr>
                            <td><div class="user-name"><div class="avatar">${(msg.name || '?')[0].toUpperCase()}</div>${msg.username ? '@' + msg.username : msg.name}</div></td>
                            <td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${this.escapeHtml(msg.text || '(media)')}</td>
                            <td>${msg.is_from_operator ? '<span class="badge info">Operator</span>' : msg.is_reply ? '<span class="badge success">Javob</span>' : '<span class="badge">User</span>'}</td>
                            <td style="white-space:nowrap">${this.formatDate(msg.date)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table></div>
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
                        <div class="chat-user">${chat.name} ${chat.username ? `<span style="color:var(--text-muted);font-weight:400">@${chat.username}</span>` : ''}</div>
                        <div class="chat-time">${this.formatDate(chat.created_at)}</div>
                    </div>
                    ${chat.group_title ? `<div class="chat-group-badge">Guruh: ${chat.group_title}</div>` : ''}
                    <div class="chat-text">
                        ${this.escapeHtml(chat.message_text ? `"${chat.message_text}"` : '(Xabar matni yo\'q)')}
                    </div>
                    ${type === 'answered' ? `
                    <div style="font-size:12px;color:var(--success);margin-bottom:8px">
                        Javob berilgan (Kutish: ${this.formatTime(chat.response_time)})
                    </div>
                    ` : `
                    <div style="font-size:12px;color:var(--danger);margin-bottom:8px">
                        Kutmoqda: ${this.formatTime(chat.waiting_time)}
                    </div>
                    `}
                    <div class="chat-actions">
                        ${chat.group_telegram_id && chat.message_id ?
                    `<a href="https://t.me/c/${chat.group_telegram_id}/${chat.message_id}" target="_blank" class="chat-link">💬 Telegramda javob berish</a>`
                    : ''}
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
    /** ===== THEME ===== */
    toggleTheme() {
        const html = document.documentElement;
        const isDark = html.getAttribute('data-theme') !== 'light';
        html.setAttribute('data-theme', isDark ? 'light' : 'dark');
        localStorage.setItem('theme', isDark ? 'light' : 'dark');

        const btn = document.getElementById('themeToggle');
        btn.innerHTML = isDark ? '🌙 Dark mode' : '☀️ Light mode';

        Charts.updateTheme(!isDark);
        // Re-render to update charts
        this.renderView();
    },

    loadTheme() {
        const saved = localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-theme', saved);
        Charts.isDark = saved === 'dark';
        Charts.setDefaults();
        const btn = document.getElementById('themeToggle');
        if (btn) {
            btn.innerHTML = saved === 'dark' ? '☀️ Light mode' : '🌙 Dark mode';
        }
    },

    /** ===== FORMATTERS ===== */
    formatNumber(n) {
        if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
        if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
        return (n || 0).toString();
    },

    formatTime(seconds) {
        if (!seconds || seconds === 0) return '0s';
        if (seconds > 86400) return Math.round(seconds / 86400) + 'k';
        if (seconds > 3600) return (seconds / 3600).toFixed(1) + 'soat';
        if (seconds > 60) return Math.round(seconds / 60) + 'daq';
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
};

// Ilovani boshlash
document.addEventListener('DOMContentLoaded', () => App.init());
