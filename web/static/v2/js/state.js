/**
 * 게임 상태 머신 — 4구간 하루 시스템
 * TITLE → PREP → BUSINESS → NIGHT → SLEEP → PREP ...
 */
const GameState = {
    gameId: null,
    segment: 'TITLE',       // Current UI segment
    gameData: null,          // Latest full game state

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
        if (typeof App !== 'undefined' && App.onSegmentChange) {
            App.onSegmentChange(seg);
        }
    },

    isActionSegment(seg) {
        return seg === 'PREP' || seg === 'NIGHT';
    },
};
