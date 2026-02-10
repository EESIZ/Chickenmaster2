/**
 * 메인 오케스트레이터 — 4구간 하루 시스템
 */
const App = {
    async init() {
        this._bindEvents();
        await this._loadGameList();
        this.showScreen('title');
    },

    // ── 화면 전환 ──

    showScreen(name) {
        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
        const el = document.getElementById(`screen-${name}`);
        if (el) el.classList.add('active');
    },

    showArea(areaId) {
        const areas = ['area-action', 'area-action-results', 'area-business',
                       'area-business-summary', 'area-sleep'];
        areas.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = id === areaId ? '' : 'none';
        });
    },

    onSegmentChange(seg) {
        Dashboard.updateSegmentIndicator(seg);
    },

    // ── 이벤트 바인딩 ──

    _bindEvents() {
        document.getElementById('btn-new-game').addEventListener('click', () => this._newGame());
        document.getElementById('btn-confirm').addEventListener('click', () => this._confirmSegment());
        document.getElementById('btn-after-results').addEventListener('click', () => this._afterResults());
        document.getElementById('btn-after-business').addEventListener('click', () => this._enterNightSegment());
        document.getElementById('btn-next-day').addEventListener('click', () => this._executeSleep());
        document.getElementById('btn-price').addEventListener('click', () => this._showPriceModal());
        document.getElementById('btn-price-ok').addEventListener('click', () => this._changePrice());
        document.getElementById('btn-price-cancel').addEventListener('click', () => {
            document.getElementById('modal-price').style.display = 'none';
        });
        document.getElementById('btn-tc-ok').addEventListener('click', () => this._saveTimeConfig());
        document.getElementById('btn-tc-cancel').addEventListener('click', () => {
            document.getElementById('modal-time-config').style.display = 'none';
        });

        // Time config slider live labels
        ['wake', 'open', 'close', 'sleep'].forEach(key => {
            const slider = document.getElementById(`tc-${key}`);
            const label = document.getElementById(`tc-${key}-val`);
            if (slider && label) {
                slider.addEventListener('input', () => { label.textContent = slider.value; });
            }
        });

        document.getElementById('player-name').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this._newGame();
        });
    },

    // ── 게임 목록 (이어하기) ──

    async _loadGameList() {
        try {
            const games = await API.listGames();
            const listEl = document.getElementById('game-list');
            const section = document.getElementById('resume-section');
            if (!games || games.length === 0) {
                section.style.display = 'none';
                return;
            }
            section.style.display = '';
            listEl.innerHTML = '';
            games.forEach(g => {
                const div = document.createElement('div');
                div.className = 'resume-item';
                div.textContent = `${g.player_name} (${g.id})`;
                div.addEventListener('click', () => this._resumeGame(g.id));
                listEl.appendChild(div);
            });
        } catch (e) {
            // Silently ignore if server not ready
        }
    },

    // ── 새 게임 ──

    async _newGame() {
        const name = document.getElementById('player-name').value.trim() || '김치킨';
        const btn = document.getElementById('btn-new-game');
        btn.disabled = true;
        btn.textContent = '생성 중...';
        try {
            const data = await API.createGame(name);
            GameState.gameId = data.game_id;
            GameState.gameData = data;
            this._enterGame(data);
        } catch (e) {
            alert('게임 생성 실패: ' + e.message);
        } finally {
            btn.disabled = false;
            btn.textContent = '새 게임 시작';
        }
    },

    async _resumeGame(gameId) {
        try {
            const data = await API.getGame(gameId);
            GameState.gameId = data.game_id;
            GameState.gameData = data;
            this._enterGame(data);
        } catch (e) {
            alert('게임 로드 실패: ' + e.message);
        }
    },

    // ── 게임 진입 ──

    _enterGame(data) {
        this.showScreen('game');

        // Store time config and segment hours
        if (data.time_config) GameState.timeConfig = data.time_config;
        if (data.segment_hours) GameState.segmentHours = data.segment_hours;

        Dashboard.update(data);
        Dashboard.updateDayTimeline(data);

        const seg = data.current_segment || 'PREP';
        this._enterSegment(seg);
    },

    _enterSegment(segment) {
        GameState.setSegment(segment);
        switch (segment) {
            case 'PREP':    this._enterPrepSegment(); break;
            case 'BUSINESS': this._enterBusinessSegment(); break;
            case 'NIGHT':   this._enterNightSegment(); break;
            case 'SLEEP':   this._enterSleepSegment(); break;
        }
    },

    // ── PREP 구간 ──

    async _enterPrepSegment() {
        this.showArea('area-action');
        document.getElementById('timeline-title').textContent = '준비 시간표';
        document.getElementById('btn-confirm').textContent = '준비 완료 → 영업 시작';
        await this.refreshCards();
        await this._refreshQueue();
    },

    // ── NIGHT 구간 ──

    async _enterNightSegment() {
        GameState.setSegment('NIGHT');
        this.showArea('area-action');
        document.getElementById('timeline-title').textContent = '야간 시간표';
        document.getElementById('btn-confirm').textContent = '야간 완료 → 취침';

        // Refresh state
        const state = await API.getGame(GameState.gameId);
        GameState.gameData = state;
        Dashboard.update(state);

        await this.refreshCards();
        await this._refreshQueue();
    },

    // ── BUSINESS 구간 ──

    async _enterBusinessSegment() {
        this.showArea('area-business');
        try {
            const data = await API.startBusiness(GameState.gameId);
            GameState.businessDecisions = data.decisions || [];
            Business.start(data);
        } catch (e) {
            alert('영업 시작 실패: ' + e.message);
        }
    },

    // ── SLEEP 구간 ──

    _enterSleepSegment() {
        GameState.setSegment('SLEEP');
        this.showArea('area-sleep');
        const sleepH = GameState.segmentHours.SLEEP || 7;
        document.getElementById('sleep-info').textContent =
            `${sleepH}시간 수면 — 피로 -${sleepH * 16} 회복`;
    },

    async _executeSleep() {
        const btn = document.getElementById('btn-next-day');
        btn.disabled = true;
        btn.textContent = '수면 중...';
        try {
            const data = await API.executeSleep(GameState.gameId);
            // Refresh full state
            const state = await API.getGame(GameState.gameId);
            GameState.gameData = state;
            if (state.time_config) GameState.timeConfig = state.time_config;
            if (state.segment_hours) GameState.segmentHours = state.segment_hours;
            Dashboard.update(state);
            Dashboard.updateDayTimeline(state);
            this._enterSegment('PREP');
        } catch (e) {
            alert('수면 실패: ' + e.message);
        } finally {
            btn.disabled = false;
            btn.textContent = '다음 날';
        }
    },

    // ── 카드/큐 공통 ──

    async refreshCards() {
        if (!GameState.gameId) return;
        try {
            const data = await API.getAvailable(GameState.gameId);
            this._renderCards(data);
        } catch (e) {
            console.error('카드 로드 실패:', e);
        }
    },

    _renderCards(data) {
        const listEl = document.getElementById('card-list');
        if (!listEl) return;
        listEl.innerHTML = '';

        (data.categories || []).forEach(cat => {
            const group = document.createElement('div');
            group.className = 'category-group';

            const header = document.createElement('div');
            header.className = 'category-header';
            header.innerHTML = `
                <span>${cat.icon}</span>
                <h4>${cat.name}</h4>
                <span class="category-toggle">&darr;</span>
            `;
            header.addEventListener('click', () => {
                const body = group.querySelector('.category-body');
                body.classList.toggle('collapsed');
                header.querySelector('.category-toggle').textContent =
                    body.classList.contains('collapsed') ? '&rarr;' : '&darr;';
            });

            const body = document.createElement('div');
            body.className = 'category-body';

            (cat.actions || []).forEach(a => {
                const card = document.createElement('div');
                card.className = `action-card ${a.can_do ? '' : 'disabled'}`;
                card.innerHTML = `
                    <div class="card-name">${a.name}</div>
                    <div class="card-meta">
                        <span>${a.hours}시간</span>
                        ${a.cost > 0 ? `<span class="cost">\u20A9${a.cost.toLocaleString()}</span>` : ''}
                        <span>피로 ${a.fatigue_per_hour >= 0 ? '+' : ''}${a.fatigue_per_hour}/h</span>
                    </div>
                    ${a.exp_info ? `<div class="card-exp">${a.exp_info}</div>` : ''}
                    ${a.prepared_gain ? `<div class="card-exp" style="color:var(--orange)">준비량 +${a.prepared_gain}</div>` : ''}
                `;
                if (a.can_do) {
                    card.addEventListener('click', () => this._addToQueue(a.action_type, a.specific_action));
                }
                body.appendChild(card);
            });

            group.appendChild(header);
            group.appendChild(body);
            listEl.appendChild(group);
        });
    },

    async _addToQueue(actionType, specificAction) {
        if (!GameState.gameId) return;
        try {
            const data = await API.addToQueue(GameState.gameId, actionType, specificAction);
            Timeline.render(data.queue, data.segment_hours);
            await this.refreshCards();
        } catch (e) {
            alert(e.message);
        }
    },

    async _refreshQueue() {
        if (!GameState.gameId) return;
        try {
            const data = await API.getQueue(GameState.gameId);
            Timeline.render(data.queue, data.segment_hours);
        } catch (e) {
            console.error('큐 로드 실패:', e);
        }
    },

    // ── 행동 확정 (PREP or NIGHT) ──

    async _confirmSegment() {
        if (!GameState.gameId) return;
        const seg = GameState.segment;
        const btn = document.getElementById('btn-confirm');
        btn.disabled = true;
        btn.textContent = '실행 중...';
        try {
            let data;
            if (seg === 'PREP') {
                data = await API.confirmPrep(GameState.gameId);
            } else if (seg === 'NIGHT') {
                data = await API.confirmNight(GameState.gameId);
            } else {
                return;
            }

            // Show results
            PhaseCards.showActionResults(data.action_results);
            document.getElementById('action-results-title').textContent =
                seg === 'PREP' ? '준비 결과' : '야간 활동 결과';
            this.showArea('area-action-results');

            // Update dashboard
            const state = await API.getGame(GameState.gameId);
            GameState.gameData = state;
            Dashboard.update(state);
        } catch (e) {
            alert('실행 실패: ' + e.message);
        } finally {
            btn.disabled = false;
            btn.textContent = seg === 'PREP' ? '준비 완료 → 영업 시작' : '야간 완료 → 취침';
        }
    },

    _afterResults() {
        const seg = GameState.segment;
        if (seg === 'PREP') {
            this._enterBusinessSegment();
        } else if (seg === 'NIGHT') {
            this._enterSleepSegment();
        }
    },

    // ── 영업 완료 콜백 (Business.js가 호출) ──

    async onBusinessComplete(summaryData) {
        // Show summary
        PhaseCards.showBusinessSummary(summaryData.summary);
        this.showArea('area-business-summary');

        // Update dashboard
        if (summaryData.player) {
            GameState.gameData.player = summaryData.player;
        }
        GameState.gameData.prepared_qty = summaryData.prepared_qty;
        GameState.gameData.ingredient_freshness = summaryData.ingredient_freshness;
        GameState.gameData.current_segment = 'NIGHT';
        Dashboard.update(GameState.gameData);
        GameState.setSegment('NIGHT');
    },

    // ── 가격 변경 ──

    _showPriceModal() {
        const modal = document.getElementById('modal-price');
        const input = document.getElementById('input-price');
        if (GameState.gameData?.store) {
            input.value = GameState.gameData.store.selling_price;
        }
        modal.style.display = 'flex';
    },

    async _changePrice() {
        const input = document.getElementById('input-price');
        const price = parseInt(input.value, 10);
        if (isNaN(price)) return;
        try {
            const result = await API.changePrice(GameState.gameId, price);
            document.getElementById('modal-price').style.display = 'none';
            if (GameState.gameData?.store) {
                GameState.gameData.store.selling_price = result.new_price;
                GameState.gameData.store.selling_price_formatted = result.new_price_formatted;
            }
            Dashboard.update(GameState.gameData);
        } catch (e) {
            alert(e.message);
        }
    },

    // ── 시간 설정 ──

    async _saveTimeConfig() {
        const wake = parseInt(document.getElementById('tc-wake').value);
        const open = parseInt(document.getElementById('tc-open').value);
        const close = parseInt(document.getElementById('tc-close').value);
        const sleep = parseInt(document.getElementById('tc-sleep').value);

        try {
            const result = await API.updateTimeConfig(GameState.gameId, wake, open, close, sleep);
            GameState.timeConfig = result.time_config;
            GameState.segmentHours = result.segment_hours;
            document.getElementById('modal-time-config').style.display = 'none';
            Dashboard.updateDayTimeline(GameState.gameData);
        } catch (e) {
            alert(e.message);
        }
    },
};

// Boot
document.addEventListener('DOMContentLoaded', () => App.init());
