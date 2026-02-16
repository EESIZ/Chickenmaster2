/**
 * 메인 오케스트레이터 — VN 비주얼노벨 스타일 4구간 하루 시스템
 */
const App = {
    // 카테고리 메타 (탭 아이콘/라벨/색상)
    CATEGORY_META: {
        COOKING:     { icon: '🍳', label: '요리', color: '#e17055' },
        OPERATION:   { icon: '🔧', label: '운영', color: '#0984e3' },
        ADVERTISING: { icon: '📢', label: '광고', color: '#00b894' },
        RESEARCH:    { icon: '📚', label: '연구', color: '#6c5ce7' },
        PERSONAL:    { icon: '🏃', label: '개인', color: '#fdcb6e' },
        REST:        { icon: '💤', label: '휴식', color: '#636e72' },
        ORDER:       { icon: '📦', label: '주문', color: '#1e90ff' },
    },

    _activeTab: null,
    _sidebarData: null,

    async init() {
        Sprites.init();
        SFX.init();
        HUD.init();
        this._bindEvents();
        this._setupTitleScreen();
        await this._loadGameList();
        this.showScreen('title');
    },

    // ── 화면 전환 ──

    showScreen(name) {
        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
        const el = document.getElementById(`screen-${name}`);
        if (el) el.classList.add('active');
    },

    _showTimeline(show) {
        const el = document.getElementById('vn-timeline');
        if (el) el.style.display = show ? '' : 'none';
    },

    _showBizOverlay(show) {
        const el = document.getElementById('vn-biz-overlay');
        if (el) el.style.display = show ? '' : 'none';
    },

    _showSidebar(show) {
        const el = document.getElementById('action-sidebar');
        if (el) {
            if (show) {
                el.classList.add('open');
            } else {
                el.classList.remove('open');
                this._activeTab = null;
            }
        }
    },

    // ── 이벤트 바인딩 ──

    _bindEvents() {
        document.getElementById('btn-new-game').addEventListener('click', () => this._newGame());
        document.getElementById('btn-confirm').addEventListener('click', () => this._confirmSegment());
        document.getElementById('btn-price').addEventListener('click', () => this._showPriceModal());
        document.getElementById('btn-price-ok').addEventListener('click', () => this._changePrice());
        document.getElementById('btn-price-cancel').addEventListener('click', () => {
            document.getElementById('modal-price').style.display = 'none';
        });
        document.getElementById('btn-tc-ok').addEventListener('click', () => this._saveTimeConfig());
        document.getElementById('btn-tc-cancel').addEventListener('click', () => {
            document.getElementById('modal-time-config').style.display = 'none';
        });

        // BGM toggle
        document.getElementById('btn-bgm').addEventListener('click', () => this._toggleBGM());

        // SFX toggle
        const btnSfx = document.getElementById('btn-sfx');
        if (btnSfx) {
            btnSfx.addEventListener('click', () => {
                const on = SFX.toggle();
                btnSfx.style.opacity = on ? '1' : '.4';
            });
        }

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

        // Spacebar handler
        document.addEventListener('keydown', (e) => this._onKeyDown(e));
    },

    // ── 스페이스바 / 키보드 ──

    _onKeyDown(e) {
        // Ignore if typing in input
        const tag = document.activeElement?.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
        // Ignore if modal open
        if (document.querySelector('.modal[style*="flex"]')) return;

        if (e.code === 'Space') {
            e.preventDefault();
            this._handleSpace();
        }
    },

    _handleSpace() {
        // 0. Center overlay confirm button (리포트 확인)
        const centerOverlay = document.getElementById('vn-center-overlay');
        if (centerOverlay && centerOverlay.style.display !== 'none') {
            const confirmBtn = centerOverlay.querySelector('.choice-confirm');
            if (confirmBtn) {
                confirmBtn.click();
                return;
            }
        }

        // 1. Continue button visible → advance narration
        const cont = document.getElementById('vn-continue');
        if (cont && cont.style.display !== 'none' && cont.onclick) {
            cont.onclick();
            return;
        }

        // 2. Typewriter running → skip to full text
        const dlg = document.getElementById('vn-dialogue');
        if (VN._typeTimer && dlg) {
            dlg.onclick?.();
            return;
        }

        // 3. Confirm button visible and enabled → confirm segment
        const timeline = document.getElementById('vn-timeline');
        const btnConfirm = document.getElementById('btn-confirm');
        if (timeline && timeline.style.display !== 'none' && btnConfirm && !btnConfirm.disabled) {
            btnConfirm.click();
            return;
        }

        // 4. Single VN choice (sleep "다음 날로") → click it
        const choicesBox = document.getElementById('vn-choices');
        if (choicesBox && choicesBox.style.display !== 'none') {
            const btns = choicesBox.querySelectorAll('.vn-choice-btn:not(.disabled)');
            if (btns.length === 1) {
                btns[0].click();
                return;
            }
        }
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
        SFX.play('click');
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
        SFX.play('morning');

        // Store time config and segment hours
        if (data.time_config) GameState.timeConfig = data.time_config;
        if (data.segment_hours) GameState.segmentHours = data.segment_hours;

        // Update both HUD and detail panel
        HUD.update(data);
        Dashboard.update(data);

        const seg = data.current_segment || 'PREP';
        this._enterSegment(seg);
    },

    _enterSegment(segment) {
        GameState.setSegment(segment);
        HUD.updateSegment(segment);
        Dashboard.updateSegmentIndicator(segment);

        // Reset VN state
        VN.clearCharacters();
        VN.clearDialogue();
        VN.clearChoices();
        this._showTimeline(false);
        this._showBizOverlay(false);
        this._showSidebar(false);

        switch (segment) {
            case 'PREP':    this._enterPrepSegment(); break;
            case 'BUSINESS': this._enterBusinessSegment(); break;
            case 'NIGHT':   this._enterNightSegment(); break;
            case 'SLEEP':   this._enterSleepSegment(); break;
        }
    },

    // ── PREP 구간 ──

    async _enterPrepSegment() {
        VN.setScene('PREP');

        // Narration intro
        await VN.playNarration(VN_TEXT.PREP.intro);

        // Show action prompt
        const hours = GameState.segmentHours.PREP || 3;
        VN.setText(VN.formatText(VN_TEXT.PREP.action_prompt, { hours }));

        document.getElementById('timeline-title').textContent = '준비 시간표';
        document.getElementById('btn-confirm').textContent = '준비 완료 → 영업 시작 [Space]';
        this._showTimeline(true);

        // Show sidebar with action cards
        await this.refreshCards();
        await this._refreshQueue();
    },

    // ── NIGHT 구간 ──

    async _enterNightSegment() {
        GameState.setSegment('NIGHT');
        VN.setScene('NIGHT');

        // Refresh state
        const state = await API.getGame(GameState.gameId);
        GameState.gameData = state;
        HUD.update(state);
        Dashboard.update(state);

        // Narration intro
        await VN.playNarration(VN_TEXT.NIGHT.intro);

        // Show action prompt
        const hours = GameState.segmentHours.NIGHT || 3;
        VN.setText(VN.formatText(VN_TEXT.NIGHT.action_prompt, { hours }));

        document.getElementById('timeline-title').textContent = '야간 시간표';
        document.getElementById('btn-confirm').textContent = '야간 완료 → 취침 [Space]';
        this._showTimeline(true);

        // Show sidebar with action cards
        await this.refreshCards();
        await this._refreshQueue();
    },

    // ── BUSINESS 구간 ──

    async _enterBusinessSegment() {
        VN.setScene('BUSINESS');

        // Brief narration
        await VN.playNarration(VN_TEXT.BUSINESS.intro);

        // Show biz overlay + start timelapse
        this._showBizOverlay(true);
        VN.setText('영업이 진행 중입니다...');

        try {
            const data = await API.startBusiness(GameState.gameId);
            GameState.businessDecisions = data.decisions || [];
            Business.start(data);
        } catch (e) {
            alert('영업 시작 실패: ' + e.message);
        }
    },

    // ── SLEEP 구간 ──

    async _enterSleepSegment() {
        SFX.play('sleep');
        GameState.setSegment('SLEEP');
        VN.setScene('SLEEP');

        // Narration
        await VN.playNarration(VN_TEXT.SLEEP.intro);

        // Show recovery info + next day choice
        const sleepH = GameState.segmentHours.SLEEP || 7;
        const recoveryText = VN.formatText(VN_TEXT.SLEEP.recovery, {
            hours: sleepH,
            recovery: sleepH * 16
        });
        VN.setText(recoveryText);

        VN.showChoices([{
            label: '다음 날로 [Space]',
            meta: `수면 ${sleepH}시간`,
            onClick: () => this._executeSleep(),
        }]);
    },

    async _executeSleep() {
        VN.clearChoices();
        VN.setText('수면 중...');
        try {
            await API.executeSleep(GameState.gameId);
            const state = await API.getGame(GameState.gameId);
            GameState.gameData = state;
            if (state.time_config) GameState.timeConfig = state.time_config;
            if (state.segment_hours) GameState.segmentHours = state.segment_hours;
            HUD.update(state);
            Dashboard.update(state);

            await VN.playNarration([VN_TEXT.SLEEP.next_day]);

            SFX.play('morning');
            this._enterSegment('PREP');
        } catch (e) {
            alert('수면 실패: ' + e.message);
        }
    },

    // ── 사이드바 카드 렌더링 ──

    async refreshCards() {
        if (!GameState.gameId) return;
        try {
            const data = await API.getAvailable(GameState.gameId);
            this._sidebarData = data;
            this._renderSidebar(data);
        } catch (e) {
            console.error('카드 로드 실패:', e);
        }
    },

    _renderSidebar(data) {
        const categories = data.categories || [];
        if (categories.length === 0) return;

        const tabsEl = document.getElementById('sidebar-tabs');
        const panelEl = document.getElementById('sidebar-panel-actions');
        tabsEl.innerHTML = '';
        panelEl.innerHTML = '';

        // Build tabs using API key for matching
        categories.forEach((cat) => {
            const catKey = cat.key || cat.name;
            const meta = this.CATEGORY_META[catKey];
            const icon = cat.icon || (meta ? meta.icon : '📋');
            const label = meta ? meta.label : cat.name;
            const tab = document.createElement('button');
            tab.className = 'sidebar-tab';
            tab.dataset.cat = catKey;
            tab.innerHTML = `<span class="sidebar-tab-icon">${icon}</span><span class="sidebar-tab-label">${label}</span>`;
            tab.addEventListener('click', () => this._selectTab(catKey));
            tabsEl.appendChild(tab);
        });

        // Show sidebar and auto-select first tab
        this._showSidebar(true);
        if (categories.length > 0) {
            this._selectTab(categories[0].key || categories[0].name);
        }
    },

    _selectTab(catKey) {
        this._activeTab = catKey;

        // Highlight active tab
        document.querySelectorAll('.sidebar-tab').forEach(t => {
            t.classList.toggle('active', t.dataset.cat === catKey);
        });

        // Render actions for this category
        const panelEl = document.getElementById('sidebar-panel-actions');
        panelEl.innerHTML = '';

        const categories = this._sidebarData?.categories || [];
        const cat = categories.find(c => (c.key || c.name) === catKey);
        if (!cat) return;

        (cat.actions || []).forEach(a => {
            const div = document.createElement('div');
            div.className = 'sidebar-action';
            if (!a.can_do) div.classList.add('disabled');
            div.dataset.cat = a.action_type || catName;

            let metaText = `${a.hours}h`;
            if (a.cost > 0) metaText += ` | ₩${a.cost.toLocaleString()}`;
            metaText += ` | 피로${a.fatigue_per_hour >= 0 ? '+' : ''}${a.fatigue_per_hour}/h`;
            if (a.prepared_gain) metaText += ` | 준비+${a.prepared_gain}`;

            div.innerHTML = `<div class="sidebar-action-name">${a.name}</div><div class="sidebar-action-meta">${metaText}</div>`;

            div.addEventListener('click', () => {
                if (a.can_do) {
                    SFX.play('click');
                    this._addToQueue(a.action_type, a.specific_action);
                }
            });
            panelEl.appendChild(div);
        });
    },

    async _addToQueue(actionType, specificAction) {
        if (!GameState.gameId) return;
        try {
            const data = await API.addToQueue(GameState.gameId, actionType, specificAction);
            SFX.play('queue_add');
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
        SFX.play('click');
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

            // Hide timeline + sidebar
            this._showTimeline(false);
            this._showSidebar(false);

            // Show results as VN narration
            const title = seg === 'PREP' ? VN_TEXT.PREP.results_intro : VN_TEXT.NIGHT.results_intro;
            await VN.playNarration([title]);
            await PhaseCards.showActionResultsVN(data.action_results);

            // Confirm narration
            const confirmText = seg === 'PREP' ? VN_TEXT.PREP.confirm : VN_TEXT.NIGHT.confirm;
            await VN.playNarration([confirmText]);

            // Update dashboard
            const state = await API.getGame(GameState.gameId);
            GameState.gameData = state;
            HUD.update(state);
            Dashboard.update(state);

            // Auto-transition to next segment
            if (seg === 'PREP') {
                this._enterSegment('BUSINESS');
            } else if (seg === 'NIGHT') {
                this._enterSegment('SLEEP');
            }
        } catch (e) {
            alert('실행 실패: ' + e.message);
        } finally {
            btn.disabled = false;
            btn.textContent = seg === 'PREP' ? '준비 완료 → 영업 시작 [Space]' : '야간 완료 → 취침 [Space]';
        }
    },

    // ── 영업 완료 콜백 (Business.js가 호출) ──

    async onBusinessComplete(summaryData) {
        this._showBizOverlay(false);
        VN.clearCharacters();

        // 서버 응답으로 GameState 동기화 (SSOT)
        GameState.syncFromResponse(summaryData);

        // 영업 결과 리포트 (가운데 창)
        await PhaseCards.showBusinessSummaryVN(summaryData.summary);

        // 리포트 확인 후 야간으로 전환
        GameState.updateState({ current_segment: 'NIGHT' });
        this._enterSegment('NIGHT');
    },

    // ── 가격 변경 ──

    _showPriceModal() {
        SFX.play('click');
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
            SFX.play('coin');
            document.getElementById('modal-price').style.display = 'none';
            if (GameState.gameData?.store) {
                GameState.gameData.store.selling_price = result.new_price;
                GameState.gameData.store.selling_price_formatted = result.new_price_formatted;
            }
            HUD.update(GameState.gameData);
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
        } catch (e) {
            alert(e.message);
        }
    },

    // ── BGM ──

    _toggleBGM() {
        SFX.play('click');
        const audio = document.getElementById('bgm');
        const btn = document.getElementById('btn-bgm');
        if (!audio) return;

        if (audio.paused) {
            audio.play().then(() => {
                btn.textContent = '🔊';
                this._bgmOn = true;
            }).catch(() => {});
        } else {
            audio.pause();
            btn.textContent = '🔇';
            this._bgmOn = false;
        }
    },

    // ── 타이틀 화면 설정 ──

    _setupTitleScreen() {
        const mascotImg = document.getElementById('mascot-img');
        if (mascotImg) mascotImg.src = Sprites.get('mascot');
        this._startTitleParticles();
    },

    _startTitleParticles() {
        const container = document.getElementById('title-particles');
        if (!container) return;

        const spriteNames = ['coin', 'star', 'drumstick', 'meat', 'icon_cooking'];

        const spawnParticle = () => {
            const img = document.createElement('img');
            img.className = 'pixel-sprite title-particle';
            img.src = Sprites.get(spriteNames[Math.floor(Math.random() * spriteNames.length)]);
            img.style.width = (16 + Math.random() * 16) + 'px';
            img.style.height = img.style.width;
            img.style.left = (Math.random() * 100) + '%';
            img.style.animationDuration = (5 + Math.random() * 4) + 's';
            img.style.animationDelay = (Math.random() * 2) + 's';
            container.appendChild(img);
            setTimeout(() => img.remove(), 10000);
        };

        for (let i = 0; i < 5; i++) setTimeout(spawnParticle, i * 600);
        this._titleParticleTimer = setInterval(spawnParticle, 2000);
    },
};

// Boot
document.addEventListener('DOMContentLoaded', () => App.init());
