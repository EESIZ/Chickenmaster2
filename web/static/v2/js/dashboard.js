/**
 * 대시보드 업데이트 — 4구간 시스템
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
            this._bar('bar-fatigue', p.fatigue, fatigueMax);
            this._bar('bar-happiness', p.happiness, 100);

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

        this._set('dash-stock', data.stock ?? '-');
        this._set('dash-ingredient', data.ingredient_qty ?? '-');
        this._set('dash-prepared', data.prepared_qty ?? 0);
        this._set('dash-reputation', data.reputation ?? 50);

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

    _bar(id, val, max) {
        const el = document.getElementById(id);
        if (el) el.style.width = Math.min(100, (val / max) * 100) + '%';
    },
};
