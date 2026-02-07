/**
 * v2 API 클라이언트 — 4구간 하루 시스템
 */
const API = {
    base: '/api/v2/games',

    async _fetch(url, options = {}) {
        const res = await fetch(url, {
            headers: { 'Content-Type': 'application/json' },
            ...options,
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: res.statusText }));
            throw new Error(err.detail || '요청 실패');
        }
        return res.json();
    },

    // 게임 수명주기
    listGames()          { return this._fetch(this.base); },
    createGame(name)     { return this._fetch(this.base, { method:'POST', body:JSON.stringify({player_name:name}) }); },
    getGame(id)          { return this._fetch(`${this.base}/${id}`); },
    deleteGame(id)       { return this._fetch(`${this.base}/${id}`, { method:'DELETE' }); },

    // 시간 설정
    updateTimeConfig(id, wake, open, close, sleep) {
        return this._fetch(`${this.base}/${id}/time-config`, {
            method:'PUT',
            body:JSON.stringify({ wake_time:wake, open_time:open, close_time:close, sleep_time:sleep }),
        });
    },

    // 행동 (카드 큐) — 구간 공통
    getAvailable(id)     { return this._fetch(`${this.base}/${id}/actions/available`); },
    addToQueue(id, actionType, specificAction) {
        return this._fetch(`${this.base}/${id}/actions/queue`, {
            method:'POST',
            body:JSON.stringify({ action_type:actionType, specific_action:specificAction }),
        });
    },
    removeFromQueue(id, slot) {
        return this._fetch(`${this.base}/${id}/actions/queue/${slot}`, { method:'DELETE' });
    },
    getQueue(id)         { return this._fetch(`${this.base}/${id}/actions/queue`); },

    // 구간 진행
    confirmPrep(id)      { return this._fetch(`${this.base}/${id}/segments/prep/confirm`, { method:'POST' }); },
    startBusiness(id)    { return this._fetch(`${this.base}/${id}/business/start`, { method:'POST' }); },
    submitDecision(id, decisionId, choice) {
        return this._fetch(`${this.base}/${id}/business/decisions/${decisionId}`, {
            method:'POST',
            body:JSON.stringify({ choice }),
        });
    },
    completeBusiness(id) { return this._fetch(`${this.base}/${id}/business/complete`, { method:'POST' }); },
    confirmNight(id)     { return this._fetch(`${this.base}/${id}/segments/night/confirm`, { method:'POST' }); },
    executeSleep(id)     { return this._fetch(`${this.base}/${id}/sleep/execute`, { method:'POST' }); },

    // 유틸
    changePrice(id, price) {
        return this._fetch(`${this.base}/${id}/price`, {
            method:'POST',
            body:JSON.stringify({ new_price:price }),
        });
    },
};
