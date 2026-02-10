/**
 * 대시보드 업데이트 — 게이지 바 시스템
 */
const Dashboard = {
    update(data) {
        if (!data) return;
        const p = data.player;
        const s = data.store;
        const t = data.turn;

        if (t) {
            this._set('dash-turn', t.turn_number);
            this._set('dash-date', t.game_date);
        }
        if (p) {
            this._set('dash-money', p.money_formatted);
            this._set('dash-fatigue', p.fatigue);
            this._set('dash-happiness', p.happiness);

            const fatigueMax = (p.stats?.stamina || 50) * 2;
            this._gaugeBar('bar-fatigue', p.fatigue, fatigueMax);
            this._gaugeBar('bar-happiness', p.happiness, 100);

            if (p.stats) {
                this._set('stat-cooking', p.stats.cooking);
                this._set('stat-management', p.stats.management);
                this._set('stat-service', p.stats.service);
                this._set('stat-tech', p.stats.tech);
                this._set('stat-stamina', p.stats.stamina);
            }
        }
        if (s) {
            this._set('dash-price', s.selling_price_formatted);
        }

        // 원재료 게이지 (max 200 for display)
        const iq = data.ingredient_qty ?? 0;
        this._set('dash-ingredient', iq);
        this._gaugeBar('bar-ingredient', iq, 200);

        // 준비량 게이지 (max = ingredient_qty or 100)
        const pq = data.prepared_qty ?? 0;
        this._set('dash-prepared', pq);
        this._gaugeBar('bar-prepared', pq, Math.max(iq, 50));

        // 신선도 게이지 (0~100)
        const fr = data.ingredient_freshness ?? 90;
        this._set('dash-freshness', Math.round(fr));
        this._gaugeBar('bar-freshness', fr, 100);
        this._updateFreshnessColor(fr);

        // 평판 게이지 (0~100)
        const rep = data.reputation ?? 50;
        this._set('dash-reputation', rep);
        this._gaugeBar('bar-reputation', rep, 100);

        // Segment indicator
        this.updateSegmentIndicator(data.current_segment || 'PREP');
    },

    updateSegmentIndicator(currentSeg) {
        const segs = ['PREP', 'BUSINESS', 'NIGHT', 'SLEEP'];
        const idx = segs.indexOf(currentSeg);

        document.querySelectorAll('.seg-badge').forEach(el => {
            const s = el.dataset.seg;
            const si = segs.indexOf(s);
            el.classList.remove('active', 'done');
            if (si < idx) el.classList.add('done');
            else if (si === idx) el.classList.add('active');
        });
    },

    updateDayTimeline(data) {
        const tc = GameState.timeConfig;
        const sh = GameState.segmentHours;
        const total = (sh.PREP || 0) + (sh.BUSINESS || 0) + (sh.NIGHT || 0) + (sh.SLEEP || 0);
        if (total <= 0) return;

        const setPct = (id, hours) => {
            const el = document.getElementById(id);
            if (el) el.style.width = ((hours / total) * 100) + '%';
        };

        setPct('seg-bar-PREP', sh.PREP);
        setPct('seg-bar-BUSINESS', sh.BUSINESS);
        setPct('seg-bar-NIGHT', sh.NIGHT);
        setPct('seg-bar-SLEEP', sh.SLEEP);

        // Labels
        this._set('label-wake', tc.wake_time + ':00');
        this._set('label-open', tc.open_time + ':00');
        this._set('label-close', tc.close_time + ':00');
        const sleepLabel = tc.sleep_time > 24
            ? (tc.sleep_time - 24) + ':00'
            : tc.sleep_time + ':00';
        this._set('label-sleep', sleepLabel);
    },

    _set(id, val) {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    },

    _gaugeBar(id, val, max) {
        const el = document.getElementById(id);
        if (el) el.style.width = Math.min(100, (val / max) * 100) + '%';
    },

    _updateFreshnessColor(freshness) {
        const el = document.getElementById('bar-freshness');
        if (!el) return;
        if (freshness >= 70) {
            el.style.backgroundColor = 'var(--green)';
        } else if (freshness >= 40) {
            el.style.backgroundColor = 'var(--orange)';
        } else {
            el.style.backgroundColor = 'var(--red)';
        }
    },
};
