/**
 * 영업 타임랩스 엔진
 * 매 2초 = 1시간, 시계 진행 + 고객 등장 + 매출 카운터 + 의사결정
 */
const Business = {
    _timer: null,
    _hour: 0,
    _totalHours: 11,
    _openTime: 10,
    _customers: 0,
    _revenue: 0,
    _prepared: 0,
    _decisions: [],
    _decisionIdx: 0,
    _paused: false,

    start(data) {
        this._totalHours = data.business_hours || 11;
        this._openTime = GameState.timeConfig.open_time || 10;
        this._prepared = data.prepared_qty || 0;
        this._decisions = (data.decisions || []).sort((a, b) => a.trigger_hour - b.trigger_hour);
        this._decisionIdx = 0;
        this._hour = 0;
        this._customers = 0;
        this._revenue = 0;
        this._paused = false;

        // Reset UI
        document.getElementById('biz-time').textContent = this._formatTime(this._openTime);
        document.getElementById('biz-customers').textContent = '0';
        document.getElementById('biz-revenue').textContent = '\u20A90';
        document.getElementById('biz-prepared').textContent = this._prepared;
        document.getElementById('biz-progress-bar').style.width = '0%';
        document.getElementById('biz-customer-area').innerHTML = '';
        document.getElementById('biz-log').innerHTML = '';

        this._tick();
    },

    _tick() {
        if (this._paused) return;

        this._hour++;
        const currentTime = this._openTime + this._hour;
        const progress = (this._hour / this._totalHours) * 100;

        // Update clock
        document.getElementById('biz-time').textContent = this._formatTime(currentTime);
        document.getElementById('biz-progress-bar').style.width = progress + '%';

        // Simulate customers this hour
        const hourCustomers = Math.floor(Math.random() * 5) + 2;
        this._customers += hourCustomers;
        this._revenue += hourCustomers * 20000; // rough estimate, actual calc on server

        document.getElementById('biz-customers').textContent = this._customers;
        document.getElementById('biz-revenue').textContent =
            '\u20A9' + this._revenue.toLocaleString();

        // Spawn customer sprite
        this._spawnCustomer(hourCustomers);

        // Log
        this._addLog(`${this._formatTime(currentTime)} - ${hourCustomers}명 방문`);

        // Check for decisions
        if (this._decisionIdx < this._decisions.length) {
            const nextDec = this._decisions[this._decisionIdx];
            if (this._hour >= nextDec.trigger_hour) {
                this._paused = true;
                this._decisionIdx++;
                this._showDecision(nextDec);
                return;
            }
        }

        // Check end
        if (this._hour >= this._totalHours) {
            this._finish();
            return;
        }

        this._timer = setTimeout(() => this._tick(), 2000);
    },

    _formatTime(h) {
        const hour = h % 24;
        return `${hour.toString().padStart(2, '0')}:00`;
    },

    _spawnCustomer(count) {
        const area = document.getElementById('biz-customer-area');
        for (let i = 0; i < Math.min(count, 3); i++) {
            const span = document.createElement('span');
            span.className = 'biz-customer';
            span.textContent = '🐔';
            span.style.left = (Math.random() * 80 + 10) + '%';
            area.appendChild(span);
            setTimeout(() => span.remove(), 3000);
        }
    },

    _addLog(msg) {
        const log = document.getElementById('biz-log');
        const line = document.createElement('div');
        line.className = 'biz-log-line';
        line.textContent = msg;
        log.prepend(line);
        // Keep max 8 lines
        while (log.children.length > 8) log.lastChild.remove();
    },

    _showDecision(dec) {
        const modal = document.getElementById('modal-decision');
        document.getElementById('decision-title').textContent = dec.title;
        document.getElementById('decision-desc').textContent = dec.description || '';

        const btnA = document.getElementById('btn-choice-a');
        const btnB = document.getElementById('btn-choice-b');
        btnA.textContent = dec.choice_a_label;
        btnB.textContent = dec.choice_b_label;

        const submitChoice = async (choice) => {
            btnA.onclick = null;
            btnB.onclick = null;
            modal.style.display = 'none';
            try {
                const result = await API.submitDecision(GameState.gameId, dec.id, choice);
                this._addLog(`의사결정: ${result.label}`);
            } catch (e) {
                console.error('의사결정 실패:', e);
            }
            this._paused = false;

            if (this._hour >= this._totalHours) {
                this._finish();
            } else {
                this._timer = setTimeout(() => this._tick(), 1000);
            }
        };

        btnA.onclick = () => submitChoice('A');
        btnB.onclick = () => submitChoice('B');
        modal.style.display = 'flex';
    },

    async _finish() {
        if (this._timer) clearTimeout(this._timer);
        this._addLog('영업 종료!');

        try {
            const data = await API.completeBusiness(GameState.gameId);
            App.onBusinessComplete(data);
        } catch (e) {
            alert('영업 완료 실패: ' + e.message);
        }
    },

    stop() {
        if (this._timer) clearTimeout(this._timer);
        this._paused = true;
    },
};
