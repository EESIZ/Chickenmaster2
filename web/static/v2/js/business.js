/**
 * 영업 타임랩스 엔진 — VN 스타일
 * 매 2초 = 1시간, 서버 예측 데이터(고객 도착) + 실시간 GameState 참조
 *
 * SSOT 원칙: prepared_qty 등 게임 상태는 항상 GameState.gameData에서 읽고,
 * 변경 시 GameState.updateState()로 갱신한다.
 */
const Business = {
    _timer: null,
    _hour: 0,
    _totalHours: 11,
    _openTime: 10,
    _customers: 0,       // 누적 방문 고객 (표시용)
    _served: 0,           // 누적 판매 수 (표시용)
    _revenue: 0,          // 누적 매출 (표시용)
    _price: 20000,
    _forecast: [],        // 서버 제공 시간별 고객 도착 예측
    _decisions: [],
    _decisionIdx: 0,
    _paused: false,

    // 의사결정 키 → 고객 캐릭터 매핑
    DECISION_CHARACTERS: {
        lunch_rush:         ['salaryman', 'officewoman', 'college_male'],
        group_reservation:  ['salaryman', 'officewoman', 'ajusshi'],
        complaint:          ['ajumma', 'thug'],
        special_order:      ['beauty'],
        delivery_rush:      ['delivery'],
        ingredient_shortage: [],
    },

    /** prepared_qty는 항상 GameState에서 읽는다 */
    get _prepared() {
        return GameState.gameData?.prepared_qty ?? 0;
    },
    set _prepared(val) {
        if (GameState.gameData) {
            GameState.gameData.prepared_qty = val;
        }
    },

    start(data) {
        this._totalHours = data.business_hours || 11;
        this._openTime = GameState.timeConfig.open_time || 10;
        this._price = data.price || 20000;
        this._forecast = data.hourly_forecast || [];
        this._decisions = (data.decisions || []).sort((a, b) => a.trigger_hour - b.trigger_hour);
        this._balance = data.balance || { prepare_gain: 5, prepare_cost: 3, rest_fatigue_recovery: 16 };
        this._decisionIdx = 0;
        this._hour = 0;
        this._customers = 0;
        this._served = 0;
        this._revenue = 0;
        this._paused = false;

        // 서버 데이터로 GameState 동기화
        GameState.updateState({
            prepared_qty: data.prepared_qty || 0,
            ingredient_qty: data.ingredient_qty,
            ingredient_freshness: data.ingredient_freshness,
        });

        // Reset biz overlay UI
        this._setEl('biz-time', this._formatTime(this._openTime));
        this._setEl('biz-customers', '0');
        this._setEl('biz-revenue', '\u20A90');
        this._setEl('biz-prepared', this._prepared);
        const bar = document.getElementById('biz-progress-bar');
        if (bar) bar.style.width = '0%';

        this._tick();
    },

    _tick() {
        if (this._paused) return;

        this._hour++;
        const currentTime = this._openTime + this._hour;
        const progress = (this._hour / this._totalHours) * 100;

        // Update clock
        this._setEl('biz-time', this._formatTime(currentTime));
        const bar = document.getElementById('biz-progress-bar');
        if (bar) bar.style.width = progress + '%';

        // forecast에서 고객 도착 수만 참조, 판매는 실시간 prepared 기반
        const forecast = this._forecast[this._hour - 1];
        if (forecast) {
            const hourCustomers = forecast.customers;
            const prepared = this._prepared;  // GameState에서 읽기
            const hourServed = Math.min(hourCustomers, prepared);
            const turned = hourCustomers - hourServed;
            const hourRevenue = hourServed * this._price;

            // GameState 갱신 (prepared 차감)
            this._prepared = prepared - hourServed;
            this._customers += hourCustomers;
            this._served += hourServed;
            this._revenue += hourRevenue;

            // UI 갱신
            this._setEl('biz-customers', this._customers);
            this._setEl('biz-revenue', '\u20A9' + this._revenue.toLocaleString());
            this._setEl('biz-prepared', this._prepared);

            // Coin SFX for served customers
            if (hourServed > 0) {
                setTimeout(() => SFX.play('coin'), 300);
            }

            // VN dialogue
            if (turned > 0) {
                VN.setText(`${this._formatTime(currentTime)} - ${hourCustomers}명 방문, ${hourServed}명 판매 <span style="color:var(--red)">(${turned}명 돌아감!)</span>`);
            } else {
                VN.setText(`${this._formatTime(currentTime)} - ${hourCustomers}명 방문, ${hourServed}명 판매`);
            }
        }

        // Check if prepared_qty is low — offer mid-business action
        if (this._prepared < 5 && (this._totalHours - this._hour) > 1) {
            this._paused = true;
            this._showBizAction();
            return;
        }

        // Check for decisions (show customer characters here)
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

    // 의사결정 이벤트 시에만 고객 캐릭터 표시
    _showEventCharacters(decisionKey) {
        const chars = this.DECISION_CHARACTERS[decisionKey] || [];
        if (chars.length === 0) return;

        const positions = ['left', 'center', 'right'];
        const numToShow = Math.min(chars.length, 3);
        for (let i = 0; i < numToShow; i++) {
            const id = 'biz-event-char-' + i;
            const pos = positions[i];
            VN.showCharacter(chars[i], pos, { id, enter: i === 0 ? 'left' : 'right' });
            const el = document.getElementById(id);
            if (el) el.classList.add('biz-customer');
        }
        SFX.play('customer');
    },

    _hideEventCharacters() {
        for (let i = 0; i < 3; i++) {
            VN.hideCharacter('biz-event-char-' + i);
        }
    },

    _effectText(effect) {
        if (!effect || Object.keys(effect).length === 0) return '';
        const parts = [];
        const map = {
            customer_bonus: ['고객', '+', '명'],
            customer_bonus_pct: ['고객', '+', '%'],
            stock_cost: ['준비량', '-', ''],
            money_cost: ['자금', '-', '원'],
            money_bonus: ['자금', '+', '원'],
            ingredient_gain: ['재료', '+', ''],
            reputation_change: ['평판', '', ''],
            fatigue_change: ['피로', '', ''],
            margin_penalty_pct: ['마진', '-', '%'],
            sales_penalty_pct: ['판매', '-', '%'],
        };
        for (const [key, val] of Object.entries(effect)) {
            const m = map[key];
            if (!m) continue;
            const sign = m[1] || (val >= 0 ? '+' : '');
            const fmt = key.includes('money') ? (val / 10000) + '만' : val;
            parts.push(`${m[0]}${sign}${fmt}${m[2]}`);
        }
        return parts.length ? ` (${parts.join(', ')})` : '';
    },

    _showDecision(dec) {
        SFX.play('decision');

        // Show relevant customer characters for this event
        this._showEventCharacters(dec.decision_key);

        const submitChoice = async (choice) => {
            VN.hideCenterOverlay();
            this._hideEventCharacters();
            try {
                const result = await API.submitDecision(GameState.gameId, dec.id, choice);

                // 서버 응답으로 GameState 동기화 (SSOT)
                GameState.syncFromResponse(result);

                // stock_cost는 실시간 prepared에서 차감
                const eff = result.effect || {};
                if (eff.stock_cost) {
                    this._prepared = Math.max(0, this._prepared - eff.stock_cost);
                }

                // biz overlay UI도 갱신
                this._setEl('biz-prepared', this._prepared);
                VN.setText(`의사결정: ${result.label}`);
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

        VN.showCenterChoices(dec.title, dec.description || '', [
            {
                label: 'A: ' + dec.choice_a_label + this._effectText(dec.choice_a_effect),
                cssClass: 'choice-a',
                onClick: () => submitChoice('A'),
            },
            {
                label: 'B: ' + dec.choice_b_label + this._effectText(dec.choice_b_effect),
                cssClass: 'choice-b',
                onClick: () => submitChoice('B'),
            },
        ]);
    },

    _showBizAction() {
        SFX.play('decision');
        const bal = this._balance;

        VN.showCenterChoices(
            '준비량 부족!',
            `남은 준비량: ${this._prepared}개\n어떻게 하시겠습니까?`,
            [
                {
                    label: `재료 준비 (-1h, 재료-${bal.prepare_cost} 준비량+${bal.prepare_gain})`,
                    cssClass: 'choice-a',
                    onClick: async () => {
                        VN.hideCenterOverlay();
                        try {
                            const res = await API.businessAction(GameState.gameId, 'PREPARE');
                            // 서버 응답으로 GameState 동기화 (SSOT)
                            GameState.syncFromResponse(res);
                            this._totalHours -= 1;
                            this._setEl('biz-prepared', this._prepared);
                            VN.setText(`재료 준비 완료! 준비량: ${this._prepared}`);
                        } catch (e) {
                            VN.setText('재료 준비 실패: ' + e.message);
                        }
                        this._resumeAfterBizAction();
                    },
                },
                {
                    label: `휴식 (-1h, 피로-${bal.rest_fatigue_recovery})`,
                    cssClass: 'choice-b',
                    onClick: async () => {
                        VN.hideCenterOverlay();
                        try {
                            const res = await API.businessAction(GameState.gameId, 'REST');
                            // 서버 응답으로 GameState 동기화 (SSOT)
                            GameState.syncFromResponse(res);
                            this._totalHours -= 1;
                            VN.setText(`휴식 완료! 피로: ${Math.round(GameState.gameData?.player?.fatigue ?? 0)}`);
                        } catch (e) {
                            VN.setText('휴식 실패: ' + e.message);
                        }
                        this._resumeAfterBizAction();
                    },
                },
                {
                    label: '그냥 계속 영업',
                    cssClass: 'choice-skip',
                    onClick: () => {
                        VN.hideCenterOverlay();
                        this._resumeAfterBizAction();
                    },
                },
            ]
        );
    },

    _resumeAfterBizAction() {
        this._paused = false;
        if (this._hour >= this._totalHours) {
            this._finish();
        } else {
            this._timer = setTimeout(() => this._tick(), 1000);
        }
    },

    async _finish() {
        if (this._timer) clearTimeout(this._timer);
        VN.setText('영업 종료!');
        SFX.play('success');

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

    _setEl(id, val) {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    },
};
