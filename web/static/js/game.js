/**
 * 게임 상태 관리
 */
const Game = {
  sessionId: null,
  state: null,       // GameStateResponse
  actions: null,     // AvailableActionsResponse
  logs: [],          // 행동 결과 로그

  async create(playerName) {
    this.state = await API.createGame(playerName);
    this.sessionId = this.state.session_id;
    this.logs = [];
    await this.refreshActions();
  },

  async refresh() {
    this.state = await API.getGame(this.sessionId);
  },

  async refreshActions() {
    this.actions = await API.getAvailableActions(this.sessionId);
  },

  async doAction(actionType, specificAction, timeHours) {
    const result = await API.executeAction(this.sessionId, actionType, specificAction, timeHours);
    this.logs.push(result);
    await this.refresh();
    await this.refreshActions();
    return result;
  },

  async endTurn() {
    const result = await API.advanceTurn(this.sessionId);
    this.logs = [];
    await this.refresh();
    await this.refreshActions();
    return result;
  },

  async changePrice(price) {
    const result = await API.changePrice(this.sessionId, price);
    await this.refresh();
    return result;
  },

  isBankrupt() {
    return this.state && this.state.player.money <= 0;
  },
};
