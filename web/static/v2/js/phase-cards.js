/**
 * 행동 결과 + 영업 요약 — VN 나레이션 표시
 * 주사위는 내부 계산에만 사용, UI에는 보이지 않음
 * 결과는 한번에 모아서 출력
 */
const PhaseCards = {
    // ── 행동 결과를 한번에 모아서 표시 ──
    async showActionResultsVN(results) {
        if (!results || results.length === 0) return;

        // 자동 휴식(REST/SLEEP)은 제외하고 의미있는 행동만 모음
        const meaningful = results.filter(r =>
            r.success && r.message && !r.message.includes('쉬었습니다') &&
            !r.message.includes('눈을 감았') && !r.message.includes('커피') &&
            !r.message.includes('간식') && !r.message.includes('바람을 쐬') &&
            !r.message.includes('스마트폰')
        );
        const restCount = results.length - meaningful.length;

        // HTML로 한번에 조합
        const lines = [];
        for (const r of meaningful) {
            let line = r.message.split(',')[0]; // 첫 문장만

            const details = [];
            if (r.experience_gains) {
                const exp = Object.entries(r.experience_gains)
                    .filter(([,v]) => v > 0)
                    .map(([k,v]) => `${k}+${v}`)
                    .join(', ');
                if (exp) details.push(exp);
            }
            if (r.fatigue_change) {
                details.push(`피로${r.fatigue_change > 0 ? '+' : ''}${r.fatigue_change}`);
            }
            if (details.length) {
                line += ` <span style="color:var(--gold);font-size:.85em">[${details.join(' | ')}]</span>`;
            }
            lines.push(line);
        }

        if (restCount > 0) {
            lines.push(`<span style="color:var(--text-dim)">휴식 ${restCount}회</span>`);
        }

        if (lines.length > 0) {
            SFX.play('success');
            VN.setText(lines.join('<br>'));
            // 한번에 보여주고 클릭/스페이스로 넘김
            await new Promise(resolve => {
                const cont = document.getElementById('vn-continue');
                const dlg = document.getElementById('vn-dialogue');
                if (cont) {
                    cont.style.display = '';
                    cont.textContent = '클릭하여 계속 ▼';
                    const _advance = () => {
                        cont.style.display = 'none';
                        cont.onclick = null;
                        if (dlg) dlg.onclick = null;
                        resolve();
                    };
                    cont.onclick = _advance;
                    if (dlg) dlg.onclick = (e) => {
                        if (e.target.closest('.vn-choices')) return;
                        _advance();
                    };
                    // Auto-advance after 5 seconds
                    setTimeout(() => {
                        if (cont.onclick) _advance();
                    }, 5000);
                } else {
                    setTimeout(resolve, 3000);
                }
            });
        }
    },

    // ── 영업 결과 리포트 (가운데 창) ──
    async showBusinessSummaryVN(summary) {
        const s = summary || {};

        const served = s.actual_served || 0;
        const total = s.total_customers || 0;
        const turned = s.turned_away || 0;
        const sales = s.total_sales || 0;

        let html = '<div class="biz-report">';

        // 핵심 수치
        html += `<div class="biz-report-row"><span class="biz-report-label">영업 시간</span><span class="biz-report-value">${s.business_hours || 0}시간</span></div>`;
        html += `<div class="biz-report-row"><span class="biz-report-label">방문 고객</span><span class="biz-report-value">${total}명</span></div>`;
        html += `<div class="biz-report-row"><span class="biz-report-label">판매</span><span class="biz-report-value biz-good">${served}명</span></div>`;

        if (turned > 0) {
            html += `<div class="biz-report-row"><span class="biz-report-label">돌아간 고객</span><span class="biz-report-value biz-bad">${turned}명 (평판 -${s.turnaway_rep_penalty || 0})</span></div>`;
        }

        html += '<div class="biz-report-divider"></div>';

        html += `<div class="biz-report-row biz-report-total"><span class="biz-report-label">총 매출</span><span class="biz-report-value biz-gold">₩${sales.toLocaleString()}</span></div>`;
        html += `<div class="biz-report-row"><span class="biz-report-label">준비량 사용</span><span class="biz-report-value">${s.prepared_used || 0}개</span></div>`;

        if (s.freshness_mult != null) {
            html += `<div class="biz-report-row"><span class="biz-report-label">신선도 보정</span><span class="biz-report-value">x${s.freshness_mult}</span></div>`;
        }

        // 의사결정 결과
        if (s.decisions && s.decisions.length > 0) {
            html += '<div class="biz-report-divider"></div>';
            s.decisions.forEach(d => {
                html += `<div class="biz-report-row biz-report-decision"><span class="biz-report-label">${d.title}</span><span class="biz-report-value">${d.choice} 선택</span></div>`;
            });
        }

        html += '</div>';

        SFX.play('coin');
        await VN.showCenterReport('오늘의 영업 결과', html);
    },
};
