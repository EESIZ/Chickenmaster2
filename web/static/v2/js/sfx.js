/**
 * 8bit 효과음 합성 — Web Audio API 런타임 합성
 * AudioContext는 첫 유저 제스처에서 lazy init
 */
const SFX = {
    _ctx: null,
    _enabled: true,

    init() {
        // Lazy — created on first user gesture via _ensureCtx
    },

    toggle() {
        this._enabled = !this._enabled;
        return this._enabled;
    },

    play(name) {
        if (!this._enabled) return;
        if (!this._ensureCtx()) return;

        switch (name) {
            case 'click':       this._click(); break;
            case 'coin':        this._coin(); break;
            case 'success':     this._success(); break;
            case 'fail':        this._fail(); break;
            case 'customer':    this._customer(); break;
            case 'decision':    this._decision(); break;
            case 'sleep':       this._sleep(); break;
            case 'morning':     this._morning(); break;
            case 'queue_add':   this._queueAdd(); break;
            case 'queue_remove': this._queueRemove(); break;
        }
    },

    _ensureCtx() {
        if (this._ctx) return true;
        try {
            this._ctx = new (window.AudioContext || window.webkitAudioContext)();
            return true;
        } catch (e) {
            return false;
        }
    },

    /**
     * Core: play oscillator note
     * @param {string} type - 'square','triangle','sawtooth','sine'
     * @param {number} freq - Hz
     * @param {number} duration - seconds
     * @param {number} volume - 0~1
     * @param {number} delay - seconds offset from now
     */
    _note(type, freq, duration, volume = 0.15, delay = 0) {
        const ctx = this._ctx;
        const t = ctx.currentTime + delay;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = type;
        osc.frequency.setValueAtTime(freq, t);
        gain.gain.setValueAtTime(volume, t);
        gain.gain.exponentialRampToValueAtTime(0.001, t + duration);

        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(t);
        osc.stop(t + duration);
    },

    /**
     * Core: frequency sweep
     */
    _sweep(type, freqStart, freqEnd, duration, volume = 0.15, delay = 0) {
        const ctx = this._ctx;
        const t = ctx.currentTime + delay;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = type;
        osc.frequency.setValueAtTime(freqStart, t);
        osc.frequency.linearRampToValueAtTime(freqEnd, t + duration);
        gain.gain.setValueAtTime(volume, t);
        gain.gain.exponentialRampToValueAtTime(0.001, t + duration);

        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(t);
        osc.stop(t + duration);
    },

    // ═══════════ SOUNDS ═══════════

    /** 짧은 블립 (1047Hz, 50ms) */
    _click() {
        this._note('square', 1047, 0.05, 0.1);
    },

    /** 차-칭 상승음 (523→1047Hz, 150ms) */
    _coin() {
        this._sweep('square', 523, 1047, 0.08, 0.12);
        this._note('square', 1047, 0.08, 0.12, 0.08);
    },

    /** 상승 3음 C5-E5-G5 (300ms) */
    _success() {
        this._note('triangle', 523, 0.12, 0.15, 0);       // C5
        this._note('triangle', 659, 0.12, 0.15, 0.1);     // E5
        this._note('triangle', 784, 0.15, 0.15, 0.2);     // G5
    },

    /** 하강 와와 (400→200Hz, 400ms) */
    _fail() {
        this._sweep('sawtooth', 400, 200, 0.4, 0.12);
    },

    /** 도어벨 딩동 (880-660Hz, 200ms) */
    _customer() {
        this._note('triangle', 880, 0.1, 0.12, 0);
        this._note('triangle', 660, 0.12, 0.12, 0.1);
    },

    /** 알림 차임 (800-1000-800Hz, 300ms) */
    _decision() {
        this._note('square', 800, 0.1, 0.12, 0);
        this._note('square', 1000, 0.1, 0.12, 0.1);
        this._note('square', 800, 0.12, 0.12, 0.2);
    },

    /** 자장가 하강 E5-C5-A4 (500ms) */
    _sleep() {
        this._note('triangle', 659, 0.15, 0.1, 0);      // E5
        this._note('triangle', 523, 0.15, 0.1, 0.15);    // C5
        this._note('triangle', 440, 0.25, 0.08, 0.3);    // A4
    },

    /** 기상 팡파레 C5-E5-G5-C6 (600ms) */
    _morning() {
        this._note('square', 523, 0.12, 0.12, 0);        // C5
        this._note('square', 659, 0.12, 0.12, 0.12);     // E5
        this._note('square', 784, 0.12, 0.12, 0.24);     // G5
        this._note('square', 1047, 0.2, 0.15, 0.36);     // C6
    },

    /** 팝 (660Hz 80ms) */
    _queueAdd() {
        this._note('square', 660, 0.08, 0.1);
    },

    /** 역팝 (660→330Hz 80ms) */
    _queueRemove() {
        this._sweep('square', 660, 330, 0.08, 0.1);
    },
};
