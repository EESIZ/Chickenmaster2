/**
 * DOM 렌더링
 */
const UI = {
  // 화면 전환
  showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
    document.getElementById(id).classList.remove('hidden');
  },

  // ── 타이틀 화면 ──
  initTitle() {
    this.showScreen('title-screen');
    document.getElementById('btn-start').onclick = async () => {
      const name = document.getElementById('player-name').value.trim() || '김치킨';
      document.getElementById('btn-start').disabled = true;
      try {
        await Game.create(name);
        this.renderGame();
      } catch (e) {
        alert('게임 생성 실패: ' + e.message);
      }
      document.getElementById('btn-start').disabled = false;
    };
  },

  // ── 게임 화면 ──
  renderGame() {
    this.showScreen('game-screen');
    this.renderDashboard();
    this.renderActions();
    this.renderLog();
  },

  renderDashboard() {
    const p = Game.state.player;
    const s = Game.state.store;
    const t = Game.state.turn;

    let fatigueStatus = '';
    if (p.is_exhausted) fatigueStatus = '<span class="badge danger">탈진</span>';
    else if (p.is_critically_fatigued) fatigueStatus = '<span class="badge warning">위험</span>';
    else if (p.is_fatigued) fatigueStatus = '<span class="badge caution">주의</span>';

    document.getElementById('dashboard').innerHTML = `
      <div class="dash-row">
        <div class="dash-main">
          <h2>${t.turn_number}일차 <small>(${t.game_date})</small></h2>
          <div class="money">${p.money_formatted}</div>
        </div>
        <div class="dash-time">
          <div class="time-circle">${t.remaining_hours}<small>h</small></div>
          <div>남은 시간</div>
        </div>
      </div>
      <div class="bars">
        <label>피로도 ${fatigueStatus}</label>
        <div class="bar"><div class="bar-fill fatigue" style="width:${Math.min(p.fatigue, 100)}%"></div></div>
        <label>행복도</label>
        <div class="bar"><div class="bar-fill happiness" style="width:${Math.min(p.happiness, 100)}%"></div></div>
      </div>
      <div class="stats-grid">
        <div class="stat">🍳 요리 <b>${p.stats.cooking}</b></div>
        <div class="stat">📊 경영 <b>${p.stats.management}</b></div>
        <div class="stat">🤝 서비스 <b>${p.stats.service}</b></div>
        <div class="stat">💻 기술 <b>${p.stats.tech}</b></div>
        <div class="stat">💪 체력 <b>${p.stats.stamina}</b></div>
      </div>
      <div class="inventory-row">
        <div class="inv-item">🍗 완성품 <b>${Game.state.stock}</b>개</div>
        <div class="inv-item">🥩 원재료 <b>${Game.state.ingredient_qty}</b>개</div>
      </div>
      <div class="store-info">
        ${s.name} &mdash; ${s.product_name} (${s.selling_price_formatted})
        <button class="btn-sm" onclick="UI.showPriceModal()">가격변경</button>
      </div>
    `;
  },

  renderActions() {
    if (!Game.actions) return;
    const container = document.getElementById('action-panel');
    const cats = Game.actions.categories;

    let html = '';
    for (const cat of cats) {
      html += `<div class="cat-group">
        <div class="cat-header" onclick="this.parentElement.classList.toggle('open')">${cat.icon} ${cat.name}</div>
        <div class="cat-actions">`;
      for (const a of cat.actions) {
        const cls = a.can_do ? '' : 'disabled';
        const costStr = a.cost > 0 ? ` | ₩${a.cost.toLocaleString()}` : '';
        const fatigueStr = a.fatigue_per_hour !== 0 ? ` | 피로${a.fatigue_per_hour > 0 ? '+' : ''}${a.fatigue_per_hour}/h` : '';
        let stockStr = '';
        if (a.stock_gain > 0) stockStr += ` | 🍗+${a.stock_gain}`;
        if (a.ingredient_cost > 0) stockStr += ` | 🥩-${a.ingredient_cost}`;
        if (a.ingredient_gain > 0) stockStr += ` | 🥩+${a.ingredient_gain}`;
        html += `<button class="action-btn ${cls}" ${a.can_do ? '' : 'disabled'}
          data-cat="${cat.key}" data-action="${a.specific_action}" data-hours="${a.hours}">
          <span class="action-name">${a.name}</span>
          <span class="action-meta">${a.hours}h${costStr}${fatigueStr}${stockStr}</span>
          <span class="action-exp">${a.exp_info}</span>
        </button>`;
      }
      html += `</div></div>`;
    }

    // 턴 종료 버튼
    html += `<button class="btn-end-turn" id="btn-end-turn">턴 종료 (다음 날로)</button>`;

    container.innerHTML = html;

    // 이벤트 바인딩
    container.querySelectorAll('.action-btn:not(.disabled)').forEach(btn => {
      btn.onclick = () => this.handleAction(btn);
    });
    document.getElementById('btn-end-turn').onclick = () => this.handleEndTurn();
  },

  async handleAction(btn) {
    const cat = btn.dataset.cat;
    const action = btn.dataset.action;
    let hours = parseInt(btn.dataset.hours);

    // 휴식은 시간 선택
    if (cat === 'REST') {
      const max = Math.min(Game.actions.remaining_hours, 12);
      const input = prompt(`몇 시간 수면할까요? (1~${max})`, String(max));
      if (!input) return;
      hours = Math.max(1, Math.min(parseInt(input) || 1, max));
    }

    btn.disabled = true;
    try {
      const result = await Game.doAction(cat, action, hours);
      this.renderGame();
      if (!result.success) alert(result.message);
    } catch (e) {
      alert(e.message);
    }
    btn.disabled = false;
  },

  async handleEndTurn() {
    const btn = document.getElementById('btn-end-turn');
    btn.disabled = true;
    btn.textContent = '진행 중...';
    try {
      const result = await Game.endTurn();
      this.showSettlement(result);
      this.renderGame();

      if (Game.isBankrupt()) {
        alert('자금이 바닥났습니다... 파산입니다!');
      }
    } catch (e) {
      alert('턴 진행 실패: ' + e.message);
    }
    btn.disabled = false;
    btn.textContent = '턴 종료 (다음 날로)';
  },

  showSettlement(result) {
    const s = result.settlement || {};
    const revenue = s.revenue || 0;
    const costs = s.costs || 0;
    const profit = s.profit || 0;
    const profitClass = profit >= 0 ? 'positive' : 'negative';

    // 판매 페이즈 정보 찾기
    const salesPhase = (result.phases || []).find(p => p.phase === 'SALES') || {};
    const sold = salesPhase.customer_count || 0;
    const stockLeft = result.stock != null ? result.stock : '?';
    const ingredientLeft = result.ingredient_qty != null ? result.ingredient_qty : '?';

    const modal = document.getElementById('settlement-modal');
    document.getElementById('settlement-content').innerHTML = `
      <h3>일일 결산</h3>
      <div class="settlement-row">판매 <span>${sold}마리</span></div>
      <div class="settlement-row">매출 <span>₩${revenue.toLocaleString()}</span></div>
      <div class="settlement-row">비용 <span>₩${costs.toLocaleString()}</span></div>
      <hr>
      <div class="settlement-row ${profitClass}">
        ${profit >= 0 ? '순이익' : '순손실'}
        <span>₩${Math.abs(profit).toLocaleString()}</span>
      </div>
      <div class="settlement-stock">남은 재고: 🍗${stockLeft}개 | 🥩${ingredientLeft}개</div>
      <button class="btn-primary" onclick="document.getElementById('settlement-modal').classList.add('hidden')">확인</button>
    `;
    modal.classList.remove('hidden');
  },

  showPriceModal() {
    const current = Game.state.store.selling_price;
    const input = prompt(`새 가격을 입력하세요 (5,000 ~ 100,000)\n현재: ₩${current.toLocaleString()}`, current);
    if (!input) return;
    const price = parseInt(input.replace(/,/g, ''));
    if (isNaN(price)) return alert('숫자를 입력하세요');
    Game.changePrice(price).then(() => this.renderDashboard()).catch(e => alert(e.message));
  },

  renderLog() {
    const el = document.getElementById('log-panel');
    if (!Game.logs.length) {
      el.innerHTML = '<div class="log-empty">행동을 선택하세요</div>';
      return;
    }
    el.innerHTML = Game.logs.map(l => {
      const cls = l.success ? 'log-ok' : 'log-fail';
      return `<div class="log-entry ${cls}">${l.message}</div>`;
    }).join('');
    el.scrollTop = el.scrollHeight;
  },
};

// 앱 시작
document.addEventListener('DOMContentLoaded', () => UI.initTitle());
