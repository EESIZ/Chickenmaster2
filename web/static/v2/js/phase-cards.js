/**
 * 행동 결과 + 영업 요약 + 수면 카드
 */
const PhaseCards = {
    showActionResults(results) {
        const listEl = document.getElementById('action-results-list');
        if (!listEl) return;

        listEl.innerHTML = '';
        (results || []).forEach(r => {
            const div = document.createElement('div');
            div.className = `result-item ${r.success ? '' : 'failed'}`;
            let detail = '';
            if (r.experience_gains) {
                const exp = Object.entries(r.experience_gains)
                    .filter(([,v]) => v > 0)
                    .map(([k,v]) => `${k}+${v}`)
                    .join(', ');
                if (exp) detail += `경험치: ${exp}`;
            }
            if (r.fatigue_change) {
                detail += ` | 피로: ${r.fatigue_change > 0 ? '+' : ''}${r.fatigue_change}`;
            }
            div.innerHTML = `
                <div class="result-msg">${r.message || (r.success ? '성공' : '실패')}</div>
                ${detail ? `<div class="result-detail">${detail}</div>` : ''}
            `;
            listEl.appendChild(div);
        });
    },

    showBusinessSummary(summary) {
        const body = document.getElementById('business-summary-body');
        if (!body) return;

        const s = summary || {};
        const profitColor = s.total_sales >= 0 ? 'var(--green)' : 'var(--red)';

        let decisionsHtml = '';
        if (s.decisions && s.decisions.length > 0) {
            decisionsHtml = '<div class="summary-decisions">' +
                s.decisions.map(d =>
                    `<p class="result-line">- ${d.title}: ${d.choice === 'A' ? 'A' : 'B'} 선택</p>`
                ).join('') +
                '</div>';
        }

        body.innerHTML = `
            <p class="result-line">영업 시간: <span class="result-highlight">${s.business_hours || 0}시간</span></p>
            <p class="result-line">총 고객: <span class="result-highlight">${s.total_customers || 0}명</span></p>
            <p class="result-line">실제 판매: <span class="result-highlight">${s.actual_served || 0}명</span></p>
            <p class="result-line">총 매출: <span style="color:${profitColor};font-weight:700">\u20A9${(s.total_sales || 0).toLocaleString()}</span></p>
            <p class="result-line">재고 사용: ${s.stock_used || 0} | 준비량 사용: ${s.prepared_used || 0}</p>
            ${decisionsHtml}
        `;
    },
};
