/**
 * 게임 상태 머신 — SSOT (Single Source of Truth)
 * 모든 모듈은 GameState.gameData를 읽고, updateState()로 갱신한다.
 */
const GameState = {
    gameId: null,
    segment: 'TITLE',       // Current UI segment
    gameData: null,          // Latest full game state — THE source of truth

    SEGMENTS: ['PREP', 'BUSINESS', 'NIGHT', 'SLEEP'],

    SEGMENT_META: {
        PREP:     { icon: '🌅', title: '준비',  color: '#ff9f43' },
        BUSINESS: { icon: '🏪', title: '영업',  color: '#00b894' },
        NIGHT:    { icon: '🌙', title: '야간',  color: '#6c5ce7' },
        SLEEP:    { icon: '😴', title: '수면',  color: '#636e72' },
    },

    timeConfig: { wake_time: 7, open_time: 10, close_time: 21, sleep_time: 24 },
    segmentHours: { PREP: 3, BUSINESS: 11, NIGHT: 3, SLEEP: 7 },
    businessDecisions: [],

    setSegment(seg) {
        this.segment = seg;
        if (this.gameData) this.gameData.current_segment = seg;
        if (typeof App !== 'undefined' && App.onSegmentChange) {
            App.onSegmentChange(seg);
        }
    },

    isActionSegment(seg) {
        return seg === 'PREP' || seg === 'NIGHT';
    },

    /**
     * 부분 상태 업데이트 — 변경된 필드만 병합 후 UI 자동 갱신
     * @param {Object} partial - 변경할 필드들 (예: { prepared_qty: 10, money: 500000 })
     */
    updateState(partial) {
        if (!this.gameData || !partial) return;

        // player 객체는 deep merge
        if (partial.player && this.gameData.player) {
            Object.assign(this.gameData.player, partial.player);
            delete partial.player;
        }

        // store 객체도 deep merge
        if (partial.store && this.gameData.store) {
            Object.assign(this.gameData.store, partial.store);
            delete partial.store;
        }

        // 나머지 최상위 필드 병합
        Object.assign(this.gameData, partial);

        // UI 자동 갱신
        if (typeof HUD !== 'undefined') HUD.update(this.gameData);
        if (typeof Dashboard !== 'undefined') Dashboard.update(this.gameData);
    },

    /**
     * 서버 응답에서 게임 상태 필드를 추출하여 updateState 호출
     * submit_decision, business_action 등의 응답에서 사용
     */
    syncFromResponse(resp) {
        if (!resp) return;
        const fields = {};
        if (resp.prepared_qty != null) fields.prepared_qty = resp.prepared_qty;
        if (resp.ingredient_qty != null) fields.ingredient_qty = resp.ingredient_qty;
        if (resp.ingredient_freshness != null) fields.ingredient_freshness = resp.ingredient_freshness;
        if (resp.reputation != null) fields.reputation = resp.reputation;
        if (resp.money != null && this.gameData?.player) {
            fields.player = { money: resp.money };
        }
        if (resp.fatigue != null && this.gameData?.player) {
            fields.player = { ...(fields.player || {}), fatigue: resp.fatigue };
        }
        if (resp.player) fields.player = resp.player;
        if (Object.keys(fields).length > 0) {
            this.updateState(fields);
        }
    },
};
