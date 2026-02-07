/**
 * 구간별 시간표 컴포넌트
 */
const Timeline = {
    totalHours: 3,

    render(queue, segmentHours) {
        this.totalHours = segmentHours || 3;
        const slotsEl = document.getElementById('timeline-slots');
        const infoEl = document.getElementById('timeline-info');
        if (!slotsEl) return;

        slotsEl.innerHTML = '';
        let usedHours = 0;

        (queue || []).forEach(item => {
            usedHours += item.hours;
        });

        const remaining = Math.max(0, this.totalHours - usedHours);

        // 유저가 배치한 슬롯
        (queue || []).forEach(item => {
            const slot = document.createElement('div');
            slot.className = 'timeline-slot';
            slot.dataset.cat = item.action_type;
            slot.dataset.slot = item.slot_order;
            slot.style.width = `${(item.hours / this.totalHours) * 100}%`;
            slot.style.flex = 'none';
            slot.innerHTML = `
                ${item.name} ${item.hours}h
                <span class="slot-remove">&times;</span>
            `;
            slot.addEventListener('click', () => this.onRemove(item.slot_order));
            slotsEl.appendChild(slot);
        });

        // 남는 시간 → 자동 휴식 표시
        if (remaining > 0) {
            const restSlot = document.createElement('div');
            restSlot.className = 'timeline-slot timeline-rest-auto';
            restSlot.dataset.cat = 'REST';
            restSlot.style.width = `${(remaining / this.totalHours) * 100}%`;
            restSlot.style.flex = 'none';
            restSlot.innerHTML = `☕ 휴식 ${remaining}h`;
            slotsEl.appendChild(restSlot);
        }

        if (infoEl) {
            infoEl.textContent = `${usedHours} / ${this.totalHours}시간` +
                (remaining > 0 ? ` (${remaining}시간 → 자동 휴식)` : ' (가득 참)');
        }

        const remEl = document.getElementById('timeline-remaining');
        if (remEl) {
            remEl.style.flex = '0';
        }

        // 큐가 비어있어도 확정 가능 (자동 휴식으로 채워짐)
        const btn = document.getElementById('btn-confirm');
        if (btn) btn.disabled = false;
    },

    async onRemove(slotOrder) {
        if (!GameState.gameId) return;
        try {
            const data = await API.removeFromQueue(GameState.gameId, slotOrder);
            this.render(data.queue, data.segment_hours);
            if (typeof App !== 'undefined') App.refreshCards();
        } catch (e) {
            alert(e.message);
        }
    },
};
