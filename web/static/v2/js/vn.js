/**
 * VN Scene Manager — 비주얼노벨 씬/캐릭터/대화 관리
 */
const VN = {
    // ── 사용 가능한 캐릭터 이미지 목록 ──
    CHARACTERS: {
        salaryman:      ['char-salaryman-1.png','char-salaryman-2.png','char-salaryman-3.png'],
        officewoman:    ['char-officewoman-1.png','char-officewoman-2.png','char-officewoman-3.png'],
        college_male:   ['char-college_male-1.png','char-college_male-2.png','char-college_male-3.png'],
        college_female: ['char-college_female-1.png','char-college_female-2.png','char-college_female-3.png'],
        ajusshi:        ['char-ajusshi-1.png','char-ajusshi-2.png','char-ajusshi-3.png'],
        ajumma:         ['char-ajumma-1.png','char-ajumma-2.png','char-ajumma-3.png'],
        thug:           ['char-thug-1.png','char-thug-2.png','char-thug-3.png'],
        beauty:         ['char-beauty-1.png','char-beauty-2.png','char-beauty-3.png'],
        delivery:       ['char-delivery-1.png','char-delivery-2.png','char-delivery-3.png'],
        family:         ['char-family-2.png'],
        inspector:      ['char-inspector-3.png'],
    },

    // 고객 풀 (영업 시 랜덤 표시)
    CUSTOMER_POOL: ['salaryman','officewoman','college_male','college_female',
                    'ajusshi','ajumma','beauty','family'],

    _currentScene: null,
    _typeTimer: null,
    _autoTimer: null,
    _charElements: {},

    // ── 씬 배경 ──
    setScene(segment) {
        const bg = document.getElementById('vn-scene-bg');
        const overlay = document.getElementById('vn-scene-overlay');
        if (!bg) return;

        bg.className = 'vn-scene-bg';
        overlay.className = 'vn-scene-overlay';

        const seg = segment.toUpperCase();
        bg.classList.add('scene-' + seg.toLowerCase());
        if (seg === 'NIGHT') overlay.classList.add('overlay-night');
        if (seg === 'PREP') overlay.classList.add('overlay-prep');
        if (seg === 'SLEEP') overlay.classList.add('overlay-sleep');
        this._currentScene = seg;
    },

    // ── 캐릭터 표시 ──
    showCharacter(category, position, opts = {}) {
        position = position || 'center';
        const container = document.getElementById('vn-characters');
        if (!container) return null;

        const pool = this.CHARACTERS[category];
        if (!pool || pool.length === 0) return null;

        const imgFile = pool[Math.floor(Math.random() * pool.length)];
        const id = opts.id || ('vn-char-' + category);

        // Remove existing with same id
        const existing = document.getElementById(id);
        if (existing) existing.remove();

        const el = document.createElement('div');
        el.id = id;
        el.className = 'vn-character';
        if (opts.enter) el.classList.add('enter-' + opts.enter);

        const img = document.createElement('img');
        img.src = 'images/' + imgFile;
        img.alt = category;
        el.appendChild(img);

        // Position
        const positions = { left: '20%', center: '50%', right: '80%' };
        el.style.left = positions[position] || position;

        container.appendChild(el);
        this._charElements[id] = el;
        return el;
    },

    hideCharacter(idOrCategory) {
        const id = idOrCategory.startsWith('vn-char-') ? idOrCategory : 'vn-char-' + idOrCategory;
        const el = document.getElementById(id);
        if (el) {
            el.style.opacity = '0';
            setTimeout(() => el.remove(), 400);
            delete this._charElements[id];
        }
    },

    clearCharacters() {
        const container = document.getElementById('vn-characters');
        if (container) container.innerHTML = '';
        this._charElements = {};
    },

    // 랜덤 고객 캐릭터 표시 (영업용 — 작은 사이즈)
    showRandomCustomer(position, id) {
        const cat = this.CUSTOMER_POOL[Math.floor(Math.random() * this.CUSTOMER_POOL.length)];
        const el = this.showCharacter(cat, position, { id: id || 'vn-char-customer', enter: 'right' });
        if (el) el.classList.add('biz-customer');
        return el;
    },

    // ── 대화창 ──
    showDialogue(speaker, text, callback) {
        const speakerEl = document.getElementById('vn-speaker');
        const textEl = document.getElementById('vn-text');
        const contEl = document.getElementById('vn-continue');
        const dlgEl = document.getElementById('vn-dialogue');
        if (!textEl) return;

        // Clear previous
        this.clearChoices();
        if (this._typeTimer) clearInterval(this._typeTimer);
        if (this._autoTimer) { clearTimeout(this._autoTimer); this._autoTimer = null; }
        this._typeTimer = null;

        speakerEl.textContent = speaker || '';
        textEl.className = 'vn-text';
        textEl.textContent = '';
        contEl.style.display = 'none';
        dlgEl.onclick = null;

        const _advance = () => {
            if (this._autoTimer) { clearTimeout(this._autoTimer); this._autoTimer = null; }
            contEl.style.display = 'none';
            contEl.onclick = null;
            dlgEl.onclick = null;
            callback();
        };

        const _showContinue = () => {
            if (!callback) return;
            contEl.style.display = '';
            contEl.onclick = _advance;
            dlgEl.onclick = (e) => {
                // Don't advance if clicking on choices
                if (e.target.closest('.vn-choices')) return;
                _advance();
            };
            // Auto-advance after 4 seconds
            this._autoTimer = setTimeout(_advance, 4000);
        };

        // Typewriter effect
        let i = 0;
        this._typeTimer = setInterval(() => {
            if (i < text.length) {
                textEl.textContent += text[i];
                i++;
            } else {
                clearInterval(this._typeTimer);
                this._typeTimer = null;
                _showContinue();
            }
        }, 30);

        // Click anywhere in dialogue to skip typewriter
        dlgEl.onclick = () => {
            if (this._typeTimer) {
                clearInterval(this._typeTimer);
                this._typeTimer = null;
                textEl.textContent = text;
                _showContinue();
            }
        };
    },

    showNarration(text, callback) {
        const textEl = document.getElementById('vn-text');
        if (textEl) textEl.className = 'vn-text narration';
        this.showDialogue('', text, callback);
    },

    // 나레이션 시퀀스 (여러 줄을 순서대로)
    async playNarration(lines) {
        for (const line of lines) {
            await new Promise(resolve => {
                this.showNarration(line, resolve);
            });
        }
    },

    // 대화 시퀀스
    async playDialogue(speaker, lines) {
        for (const line of lines) {
            await new Promise(resolve => {
                this.showDialogue(speaker, line, resolve);
            });
        }
    },

    clearDialogue() {
        if (this._typeTimer) { clearInterval(this._typeTimer); this._typeTimer = null; }
        if (this._autoTimer) { clearTimeout(this._autoTimer); this._autoTimer = null; }
        const s = document.getElementById('vn-speaker');
        const t = document.getElementById('vn-text');
        const c = document.getElementById('vn-continue');
        const d = document.getElementById('vn-dialogue');
        if (s) s.textContent = '';
        if (t) { t.textContent = ''; t.onclick = null; }
        if (c) { c.style.display = 'none'; c.onclick = null; }
        if (d) d.onclick = null;
        this.hideCenterOverlay();
    },

    // ── 선택지 ──
    showChoices(choices) {
        const box = document.getElementById('vn-choices');
        if (!box) return;
        box.innerHTML = '';
        box.style.display = '';

        choices.forEach(ch => {
            const btn = document.createElement('button');
            btn.className = 'vn-choice-btn';
            if (ch.disabled) btn.classList.add('disabled');

            const label = document.createElement('span');
            label.className = 'choice-label';
            label.textContent = ch.label;
            btn.appendChild(label);

            if (ch.meta) {
                const meta = document.createElement('span');
                meta.className = 'choice-meta';
                meta.textContent = ch.meta;
                btn.appendChild(meta);
            }

            if (ch.category) btn.dataset.cat = ch.category;

            btn.onclick = () => {
                if (!ch.disabled && ch.onClick) {
                    SFX.play('click');
                    ch.onClick();
                }
            };
            box.appendChild(btn);
        });
    },

    clearChoices() {
        const box = document.getElementById('vn-choices');
        if (box) { box.innerHTML = ''; box.style.display = 'none'; }
    },

    // ── 중앙 선택지 오버레이 (영업 의사결정 등) ──
    showCenterChoices(title, desc, choices) {
        const overlay = document.getElementById('vn-center-overlay');
        const titleEl = document.getElementById('vn-center-title');
        const descEl = document.getElementById('vn-center-desc');
        const choicesEl = document.getElementById('vn-center-choices');
        if (!overlay) return;

        titleEl.textContent = title || '';
        descEl.textContent = desc || '';
        choicesEl.innerHTML = '';

        choices.forEach(ch => {
            const btn = document.createElement('button');
            btn.className = 'vn-center-choice';
            if (ch.cssClass) btn.classList.add(ch.cssClass);
            btn.textContent = ch.label;
            btn.addEventListener('click', () => {
                if (ch.onClick) {
                    SFX.play('click');
                    ch.onClick();
                }
            });
            choicesEl.appendChild(btn);
        });

        overlay.style.display = 'flex';
    },

    // ── 중앙 리포트 (영업 결과 등) ──
    showCenterReport(title, htmlContent) {
        const overlay = document.getElementById('vn-center-overlay');
        const titleEl = document.getElementById('vn-center-title');
        const descEl = document.getElementById('vn-center-desc');
        const choicesEl = document.getElementById('vn-center-choices');
        if (!overlay) return Promise.resolve();

        titleEl.textContent = title || '';
        descEl.innerHTML = htmlContent || '';
        choicesEl.innerHTML = '';

        return new Promise(resolve => {
            const btn = document.createElement('button');
            btn.className = 'vn-center-choice choice-confirm';
            btn.textContent = '확인 [Space]';
            btn.addEventListener('click', () => {
                SFX.play('click');
                this.hideCenterOverlay();
                resolve();
            });
            choicesEl.appendChild(btn);
            overlay.style.display = 'flex';
        });
    },

    hideCenterOverlay() {
        const overlay = document.getElementById('vn-center-overlay');
        if (overlay) overlay.style.display = 'none';
    },

    // ── 텍스트 (대화창에 즉시 표시, 타이프라이터 없음) ──
    setText(html) {
        const textEl = document.getElementById('vn-text');
        if (textEl) { textEl.innerHTML = html; textEl.onclick = null; }
        const speakerEl = document.getElementById('vn-speaker');
        if (speakerEl) speakerEl.textContent = '';
        document.getElementById('vn-continue')?.style && (document.getElementById('vn-continue').style.display = 'none');
    },

    // ── 유틸 ──
    formatText(template, vars) {
        return template.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? '');
    },
};
