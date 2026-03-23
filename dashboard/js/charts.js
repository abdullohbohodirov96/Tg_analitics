/**
 * Charts Module — Chart.js bilan grafiklar chizish.
 * Barcha grafik yaratish va yangilash funksiyalari shu yerda.
 */

const Charts = {
    instances: {},
    isDark: true,

    /** Chart.js default stillarni sozlash */
    setDefaults() {
        const gridColor = this.isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)';
        const textColor = this.isDark ? '#8b8fa3' : '#64748b';

        Chart.defaults.color = textColor;
        Chart.defaults.borderColor = gridColor;
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.font.size = 12;
        Chart.defaults.plugins.legend.display = false;
        Chart.defaults.plugins.tooltip.backgroundColor = this.isDark ? '#1e2235' : '#fff';
        Chart.defaults.plugins.tooltip.titleColor = this.isDark ? '#f0f0f5' : '#1a1d29';
        Chart.defaults.plugins.tooltip.bodyColor = this.isDark ? '#8b8fa3' : '#64748b';
        Chart.defaults.plugins.tooltip.borderColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';
        Chart.defaults.plugins.tooltip.borderWidth = 1;
        Chart.defaults.plugins.tooltip.padding = 12;
        Chart.defaults.plugins.tooltip.cornerRadius = 8;
        Chart.defaults.animation.duration = 800;
    },

    /** Mavjud chartni yo'q qilish */
    destroy(id) {
        if (this.instances[id]) {
            this.instances[id].destroy();
            delete this.instances[id];
        }
    },

    /** ===== DAILY MESSAGES CHART ===== */
    createDailyMessages(canvasId, data) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 280);
        gradient.addColorStop(0, 'rgba(102,126,234,0.3)');
        gradient.addColorStop(1, 'rgba(102,126,234,0.0)');

        this.instances[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => d.date),
                datasets: [{
                    label: 'Xabarlar',
                    data: data.map(d => d.count),
                    borderColor: '#667eea',
                    backgroundColor: gradient,
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    pointBackgroundColor: '#667eea',
                    pointBorderColor: '#667eea',
                    pointHoverRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { display: false } },
                    y: { beginAtZero: true, grid: { color: this.isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' } },
                },
            },
        });
    },

    /** ===== RESPONSE TIME TREND ===== */
    createResponseTimeTrend(canvasId, data) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 280);
        gradient.addColorStop(0, 'rgba(251,191,36,0.3)');
        gradient.addColorStop(1, 'rgba(251,191,36,0.0)');

        this.instances[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => d.date),
                datasets: [{
                    label: "O'rtacha javob vaqti (s)",
                    data: data.map(d => d.avg_response_time),
                    borderColor: '#fbbf24',
                    backgroundColor: gradient,
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    pointBackgroundColor: '#fbbf24',
                    pointHoverRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { display: false } },
                    y: { beginAtZero: true },
                },
            },
        });
    },

    /** ===== OPERATOR PERFORMANCE ===== */
    createOperatorPerformance(canvasId, data) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const colors = ['#667eea', '#764ba2', '#34d399', '#fbbf24', '#f87171', '#60a5fa', '#a78bfa'];

        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.name),
                datasets: [{
                    label: 'Javoblar soni',
                    data: data.map(d => d.total_replies),
                    backgroundColor: data.map((_, i) => colors[i % colors.length] + '40'),
                    borderColor: data.map((_, i) => colors[i % colors.length]),
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { display: false } },
                    y: { beginAtZero: true },
                },
                plugins: { legend: { display: false } },
            },
        });
    },

    /** ===== USER GROWTH ===== */
    createUserGrowth(canvasId, data) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 280);
        gradient.addColorStop(0, 'rgba(52,211,153,0.3)');
        gradient.addColorStop(1, 'rgba(52,211,153,0.0)');

        // Kumulyativ hisoblash
        let cumulative = 0;
        const cumulativeData = data.map(d => {
            cumulative += d.count;
            return cumulative;
        });

        this.instances[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => d.date),
                datasets: [{
                    label: "Jami foydalanuvchilar",
                    data: cumulativeData,
                    borderColor: '#34d399',
                    backgroundColor: gradient,
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    pointBackgroundColor: '#34d399',
                    pointHoverRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { display: false } },
                    y: { beginAtZero: true },
                },
            },
        });
    },

    /** ===== HEATMAP (HTML bilan) ===== */
    createHeatmap(containerId, data) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const days = ['Yak', 'Du', 'Se', 'Chor', 'Pay', 'Ju', 'Sha'];
        const maxCount = Math.max(...data.map(d => d.count), 1);

        let html = '<div class="heatmap-grid">';

        // Header — soatlar
        html += '<div class="heatmap-label"></div>';
        for (let h = 0; h < 24; h++) {
            html += `<div class="heatmap-hour">${h}</div>`;
        }

        // Har bir kun uchun
        for (let d = 0; d < 7; d++) {
            html += `<div class="heatmap-label">${days[d]}</div>`;
            for (let h = 0; h < 24; h++) {
                const item = data.find(x => x.day === d && x.hour === h);
                const count = item ? item.count : 0;
                const intensity = count / maxCount;
                const bg = this.getHeatmapColor(intensity);
                html += `<div class="heatmap-cell" style="background:${bg}" title="${days[d]} ${h}:00 — ${count} xabar">${count || ''}</div>`;
            }
        }

        html += '</div>';
        container.innerHTML = html;
    },

    /** Heatmap rang olish */
    getHeatmapColor(intensity) {
        if (intensity === 0) return this.isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.03)';
        const r = Math.round(102 + (118 - 102) * intensity);
        const g = Math.round(126 + (75 - 126) * intensity);
        const b = Math.round(234 + (162 - 234) * intensity);
        const a = 0.2 + intensity * 0.7;
        return `rgba(${r},${g},${b},${a})`;
    },

    /** Theme yangilanganda barcha chartlarni qayta chizish */
    updateTheme(isDark) {
        this.isDark = isDark;
        this.setDefaults();
        // Chartlarni qayta chizish uchun ma'lumotlarni saqlab keyin chaqiriladi
    },
};
