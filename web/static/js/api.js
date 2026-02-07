/**
 * API 클라이언트 — fetch 래퍼
 */
const API = {
  base: '/api/games',

  async _json(resp) {
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || '요청 실패');
    }
    return resp.json();
  },

  createGame(playerName) {
    return fetch(this.base, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_name: playerName }),
    }).then(r => this._json(r));
  },

  getGame(sid) {
    return fetch(`${this.base}/${sid}`).then(r => this._json(r));
  },

  getAvailableActions(sid) {
    return fetch(`${this.base}/${sid}/actions/available`).then(r => this._json(r));
  },

  executeAction(sid, actionType, specificAction, timeHours) {
    const body = { action_type: actionType, specific_action: specificAction };
    if (timeHours != null) body.time_hours = timeHours;
    return fetch(`${this.base}/${sid}/actions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).then(r => this._json(r));
  },

  advanceTurn(sid) {
    return fetch(`${this.base}/${sid}/advance`, { method: 'POST' })
      .then(r => this._json(r));
  },

  changePrice(sid, newPrice) {
    return fetch(`${this.base}/${sid}/price`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_price: newPrice }),
    }).then(r => this._json(r));
  },

  deleteGame(sid) {
    return fetch(`${this.base}/${sid}`, { method: 'DELETE' })
      .then(r => this._json(r));
  },
};
