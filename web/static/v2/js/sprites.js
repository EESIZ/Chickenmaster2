/**
 * 픽셀 스프라이트 시스템 — Canvas로 도트 찍어 data URI PNG 생성
 * image-rendering: pixelated 으로 크리스프 업스케일
 */
const Sprites = {
    cache: {},

    init() {
        this._mascot();
        this._customerNormal();
        this._customerHappy();
        this._customerAngry();
        this._customerEating();
        this._iconCooking();
        this._iconAd();
        this._iconOperation();
        this._iconResearch();
        this._iconPersonal();
        this._iconRest();
        this._coin();
        this._meat();
        this._drumstick();
        this._star();
        this._check();
        this._xmark();
        this._arrowUp();
        this._arrowDown();
        this._moon();
        this._zzz();
    },

    get(name) {
        return this.cache[name] || '';
    },

    /**
     * Core draw util: creates WxH canvas, calls pixelFn, returns data URI
     */
    _draw(w, h, pixelFn) {
        const c = document.createElement('canvas');
        c.width = w;
        c.height = h;
        const ctx = c.getContext('2d');
        pixelFn(ctx);
        return c.toDataURL('image/png');
    },

    /** Helper: fill a single pixel */
    _px(ctx, x, y, color) {
        ctx.fillStyle = color;
        ctx.fillRect(x, y, 1, 1);
    },

    /** Helper: fill array of [x,y] with same color */
    _pxAll(ctx, coords, color) {
        ctx.fillStyle = color;
        coords.forEach(([x, y]) => ctx.fillRect(x, y, 1, 1));
    },

    /** Helper: fill rect */
    _rect(ctx, x, y, w, h, color) {
        ctx.fillStyle = color;
        ctx.fillRect(x, y, w, h);
    },

    // ═══════════════════════════════════════════
    // SPRITES
    // ═══════════════════════════════════════════

    /** 32x32 치킨 마스코트 (사장님 치킨) */
    _mascot() {
        this.cache.mascot = this._draw(32, 32, ctx => {
            const body = '#f5c518';    // gold
            const bodyDk = '#d4a012';
            const beak = '#ff9f43';
            const eye = '#1a1a2e';
            const white = '#ffffff';
            const red = '#e94560';     // comb
            const wing = '#e8b810';
            const feet = '#ff9f43';
            const hat = '#ffffff';
            const hatBand = '#e94560';

            // Chef hat
            this._rect(ctx, 11, 1, 10, 3, hat);
            this._rect(ctx, 10, 4, 12, 2, hat);
            this._rect(ctx, 10, 6, 12, 1, hatBand);

            // Comb (빨간 볏) peeking from under hat
            this._pxAll(ctx, [[14,7],[15,7],[16,7],[17,7]], red);

            // Head
            this._rect(ctx, 10, 8, 12, 10, body);
            this._rect(ctx, 9, 9, 1, 8, body);
            this._rect(ctx, 22, 9, 1, 8, body);

            // Eyes
            this._rect(ctx, 13, 11, 2, 2, white);
            this._rect(ctx, 18, 11, 2, 2, white);
            this._px(ctx, 14, 12, eye);
            this._px(ctx, 19, 12, eye);

            // Beak
            this._pxAll(ctx, [[15,14],[16,14],[15,15],[16,15]], beak);
            this._px(ctx, 17, 14, beak);

            // Blush
            this._pxAll(ctx, [[11,14],[12,14],[20,14],[21,14]], '#ff8a80');

            // Body
            this._rect(ctx, 9, 18, 14, 8, body);
            this._rect(ctx, 8, 19, 1, 6, body);
            this._rect(ctx, 23, 19, 1, 6, body);

            // Wings
            this._rect(ctx, 6, 19, 2, 5, wing);
            this._rect(ctx, 24, 19, 2, 5, wing);

            // Apron (white)
            this._rect(ctx, 12, 19, 8, 6, white);
            this._rect(ctx, 13, 19, 6, 1, hatBand); // apron string

            // Feet
            this._rect(ctx, 11, 26, 3, 2, feet);
            this._rect(ctx, 18, 26, 3, 2, feet);
            this._rect(ctx, 10, 28, 4, 1, feet);
            this._rect(ctx, 17, 28, 4, 1, feet);

            // Dark outline bottom
            this._rect(ctx, 10, 29, 4, 1, bodyDk);
            this._rect(ctx, 17, 29, 4, 1, bodyDk);
        });
    },

    /** 16x16 일반 고객 치킨 */
    _customerNormal() {
        this.cache.customer_normal = this._draw(16, 16, ctx => {
            const body = '#f5c518';
            const eye = '#1a1a2e';
            const beak = '#ff9f43';
            const red = '#e94560';
            const feet = '#ff9f43';

            // Comb
            this._pxAll(ctx, [[7,0],[8,0],[7,1],[8,1]], red);

            // Head
            this._rect(ctx, 5, 2, 6, 5, body);
            this._rect(ctx, 4, 3, 1, 3, body);
            this._rect(ctx, 11, 3, 1, 3, body);

            // Eyes
            this._px(ctx, 6, 4, eye);
            this._px(ctx, 9, 4, eye);

            // Beak
            this._px(ctx, 7, 5, beak);
            this._px(ctx, 8, 5, beak);

            // Body
            this._rect(ctx, 4, 7, 8, 5, body);
            this._rect(ctx, 3, 8, 1, 3, body);
            this._rect(ctx, 12, 8, 1, 3, body);

            // Feet
            this._rect(ctx, 5, 12, 2, 2, feet);
            this._rect(ctx, 9, 12, 2, 2, feet);
            this._px(ctx, 4, 14, feet);
            this._px(ctx, 6, 14, feet);
            this._px(ctx, 8, 14, feet);
            this._px(ctx, 10, 14, feet);
        });
    },

    /** 16x16 만족 고객 (하트) */
    _customerHappy() {
        this.cache.customer_happy = this._draw(16, 16, ctx => {
            const body = '#f5c518';
            const eye = '#1a1a2e';
            const beak = '#ff9f43';
            const red = '#e94560';
            const heart = '#ff4757';
            const feet = '#ff9f43';

            // Comb
            this._pxAll(ctx, [[7,1],[8,1]], red);

            // Head
            this._rect(ctx, 5, 2, 6, 5, body);
            this._rect(ctx, 4, 3, 1, 3, body);
            this._rect(ctx, 11, 3, 1, 3, body);

            // Happy eyes (^_^)
            this._px(ctx, 6, 4, eye);
            this._px(ctx, 7, 3, eye);
            this._px(ctx, 9, 4, eye);
            this._px(ctx, 10, 3, eye);

            // Beak (smiling)
            this._px(ctx, 7, 5, beak);
            this._px(ctx, 8, 5, beak);

            // Heart
            this._pxAll(ctx, [[13,1],[14,1],[13,2],[14,2],[12,2],[15,2],[12,3],[13,3],[14,3],[15,3],[13,4],[14,4]], heart);

            // Body
            this._rect(ctx, 4, 7, 8, 5, body);
            this._rect(ctx, 3, 8, 1, 3, body);
            this._rect(ctx, 12, 8, 1, 3, body);

            // Feet
            this._rect(ctx, 5, 12, 2, 2, feet);
            this._rect(ctx, 9, 12, 2, 2, feet);
        });
    },

    /** 16x16 불만 고객 (빨간 얼굴) */
    _customerAngry() {
        this.cache.customer_angry = this._draw(16, 16, ctx => {
            const body = '#ff6b6b';  // red tint body
            const eye = '#1a1a2e';
            const beak = '#ff9f43';
            const red = '#e94560';
            const feet = '#ff9f43';

            // Comb
            this._pxAll(ctx, [[7,0],[8,0],[7,1],[8,1]], red);

            // Head (reddish)
            this._rect(ctx, 5, 2, 6, 5, body);
            this._rect(ctx, 4, 3, 1, 3, body);
            this._rect(ctx, 11, 3, 1, 3, body);

            // Angry eyes (v_v brows)
            this._px(ctx, 6, 3, eye);
            this._px(ctx, 7, 4, eye);
            this._px(ctx, 9, 3, eye);
            this._px(ctx, 10, 4, eye);
            // pupils
            this._px(ctx, 6, 4, eye);
            this._px(ctx, 9, 4, eye);

            // Beak
            this._px(ctx, 7, 5, beak);
            this._px(ctx, 8, 5, beak);

            // Angry mark
            this._pxAll(ctx, [[13,1],[14,2],[13,3],[14,1],[13,2],[14,3]], '#ff0000');

            // Body
            this._rect(ctx, 4, 7, 8, 5, body);
            this._rect(ctx, 3, 8, 1, 3, body);
            this._rect(ctx, 12, 8, 1, 3, body);

            // Feet
            this._rect(ctx, 5, 12, 2, 2, feet);
            this._rect(ctx, 9, 12, 2, 2, feet);
        });
    },

    /** 16x16 먹는 고객 */
    _customerEating() {
        this.cache.customer_eating = this._draw(16, 16, ctx => {
            const body = '#f5c518';
            const eye = '#1a1a2e';
            const beak = '#ff9f43';
            const red = '#e94560';
            const feet = '#ff9f43';
            const drumstick = '#c8956c';

            // Comb
            this._pxAll(ctx, [[7,1],[8,1]], red);

            // Head
            this._rect(ctx, 5, 2, 6, 5, body);
            this._rect(ctx, 4, 3, 1, 3, body);
            this._rect(ctx, 11, 3, 1, 3, body);

            // Happy closed eyes
            this._pxAll(ctx, [[6,4],[7,4]], eye);
            this._pxAll(ctx, [[9,4],[10,4]], eye);

            // Open beak (eating)
            this._pxAll(ctx, [[7,5],[8,5],[9,5]], beak);
            this._px(ctx, 8, 6, beak);

            // Drumstick in hand
            this._rect(ctx, 12, 6, 3, 2, drumstick);
            this._px(ctx, 15, 7, '#a87a5a');

            // Body
            this._rect(ctx, 4, 7, 8, 5, body);
            this._rect(ctx, 3, 8, 1, 3, body);
            this._rect(ctx, 12, 8, 1, 3, body);

            // Feet
            this._rect(ctx, 5, 12, 2, 2, feet);
            this._rect(ctx, 9, 12, 2, 2, feet);
        });
    },

    /** 12x12 프라이팬 아이콘 */
    _iconCooking() {
        this.cache.icon_cooking = this._draw(12, 12, ctx => {
            const pan = '#888';
            const handle = '#555';
            const food = '#ff9f43';

            // Pan body
            this._rect(ctx, 2, 4, 7, 4, pan);
            this._rect(ctx, 1, 5, 1, 2, pan);
            this._rect(ctx, 9, 5, 1, 2, pan);

            // Handle
            this._rect(ctx, 9, 6, 3, 1, handle);

            // Food in pan
            this._rect(ctx, 3, 5, 2, 2, food);
            this._rect(ctx, 6, 5, 2, 2, food);

            // Steam
            this._px(ctx, 4, 2, '#aaa');
            this._px(ctx, 6, 1, '#aaa');
            this._px(ctx, 7, 3, '#aaa');
        });
    },

    /** 12x12 확성기 아이콘 */
    _iconAd() {
        this.cache.icon_ad = this._draw(12, 12, ctx => {
            const body = '#1e90ff';
            const horn = '#ff9f43';
            const sound = '#87ceeb';

            // Megaphone body
            this._rect(ctx, 1, 4, 4, 4, body);

            // Horn
            this._rect(ctx, 5, 3, 2, 6, horn);
            this._rect(ctx, 7, 2, 1, 8, horn);
            this._rect(ctx, 8, 1, 1, 10, horn);

            // Sound waves
            this._px(ctx, 10, 3, sound);
            this._px(ctx, 10, 5, sound);
            this._px(ctx, 10, 7, sound);
            this._px(ctx, 11, 2, sound);
            this._px(ctx, 11, 5, sound);
            this._px(ctx, 11, 8, sound);
        });
    },

    /** 12x12 렌치 아이콘 */
    _iconOperation() {
        this.cache.icon_operation = this._draw(12, 12, ctx => {
            const metal = '#bbb';
            const dark = '#888';

            // Wrench head
            this._rect(ctx, 1, 1, 4, 2, metal);
            this._rect(ctx, 1, 3, 1, 1, metal);
            this._rect(ctx, 4, 3, 1, 1, metal);

            // Shaft
            this._rect(ctx, 2, 3, 2, 6, dark);

            // Bottom
            this._rect(ctx, 1, 9, 4, 2, metal);
            this._rect(ctx, 1, 8, 1, 1, metal);
            this._rect(ctx, 4, 8, 1, 1, metal);
        });
    },

    /** 12x12 책/플라스크 아이콘 */
    _iconResearch() {
        this.cache.icon_research = this._draw(12, 12, ctx => {
            const glass = '#87ceeb';
            const liquid = '#6c5ce7';
            const bubble = '#ffffff';

            // Flask neck
            this._rect(ctx, 5, 0, 2, 3, glass);

            // Flask body
            this._rect(ctx, 3, 3, 6, 2, glass);
            this._rect(ctx, 2, 5, 8, 4, glass);
            this._rect(ctx, 3, 9, 6, 2, glass);

            // Liquid
            this._rect(ctx, 3, 6, 6, 3, liquid);
            this._rect(ctx, 4, 9, 4, 2, liquid);

            // Bubbles
            this._px(ctx, 4, 7, bubble);
            this._px(ctx, 7, 6, bubble);
            this._px(ctx, 5, 8, bubble);
        });
    },

    /** 12x12 덤벨/하트 아이콘 */
    _iconPersonal() {
        this.cache.icon_personal = this._draw(12, 12, ctx => {
            const bar = '#888';
            const weight = '#e94560';

            // Dumbbell bar
            this._rect(ctx, 3, 5, 6, 2, bar);

            // Left weight
            this._rect(ctx, 1, 3, 2, 6, weight);

            // Right weight
            this._rect(ctx, 9, 3, 2, 6, weight);
        });
    },

    /** 12x12 커피잔 아이콘 */
    _iconRest() {
        this.cache.icon_rest = this._draw(12, 12, ctx => {
            const cup = '#ffffff';
            const coffee = '#8b4513';
            const steam = '#aaa';

            // Steam
            this._px(ctx, 3, 0, steam);
            this._px(ctx, 5, 1, steam);
            this._px(ctx, 7, 0, steam);

            // Cup
            this._rect(ctx, 2, 3, 7, 6, cup);
            this._rect(ctx, 1, 3, 1, 1, cup);
            this._rect(ctx, 9, 3, 1, 1, cup);

            // Coffee inside
            this._rect(ctx, 3, 5, 5, 3, coffee);

            // Handle
            this._rect(ctx, 9, 4, 2, 3, cup);
            this._px(ctx, 10, 7, cup);

            // Saucer
            this._rect(ctx, 1, 9, 9, 1, cup);
            this._rect(ctx, 0, 10, 11, 1, cup);
        });
    },

    /** 10x10 동전 아이콘 */
    _coin() {
        this.cache.coin = this._draw(10, 10, ctx => {
            const gold = '#f5c518';
            const dark = '#d4a012';
            const shine = '#ffe66d';

            // Circle
            this._rect(ctx, 3, 0, 4, 1, gold);
            this._rect(ctx, 1, 1, 8, 1, gold);
            this._rect(ctx, 0, 2, 10, 6, gold);
            this._rect(ctx, 1, 8, 8, 1, gold);
            this._rect(ctx, 3, 9, 4, 1, gold);

            // Inner circle shadow
            this._rect(ctx, 3, 2, 4, 1, dark);
            this._rect(ctx, 2, 3, 6, 4, dark);
            this._rect(ctx, 3, 7, 4, 1, dark);

            // $ symbol
            this._px(ctx, 5, 3, shine);
            this._rect(ctx, 4, 4, 3, 1, shine);
            this._px(ctx, 4, 5, shine);
            this._rect(ctx, 4, 5, 3, 1, shine);
            this._px(ctx, 6, 6, shine);
            this._rect(ctx, 4, 6, 3, 1, shine);
            this._px(ctx, 5, 7, shine);

            // Shine
            this._px(ctx, 2, 2, shine);
        });
    },

    /** 12x12 고기 아이콘 */
    _meat() {
        this.cache.meat = this._draw(12, 12, ctx => {
            const meat = '#e17055';
            const fat = '#f8c8b8';
            const bone = '#fff5e6';

            // Meat body
            this._rect(ctx, 2, 2, 8, 7, meat);
            this._rect(ctx, 1, 3, 1, 5, meat);
            this._rect(ctx, 10, 3, 1, 5, meat);
            this._rect(ctx, 3, 1, 6, 1, meat);
            this._rect(ctx, 3, 9, 6, 1, meat);

            // Fat marbling
            this._pxAll(ctx, [[4,4],[6,3],[8,5],[3,6],[7,7],[5,6]], fat);

            // Bone
            this._rect(ctx, 0, 5, 2, 2, bone);
        });
    },

    /** 12x12 치킨 다리 아이콘 */
    _drumstick() {
        this.cache.drumstick = this._draw(12, 12, ctx => {
            const skin = '#f5c518';
            const skinDk = '#d4a012';
            const bone = '#fff5e6';
            const boneDk = '#e8dcc8';

            // Drumstick meat (top)
            this._rect(ctx, 3, 0, 6, 4, skin);
            this._rect(ctx, 2, 1, 1, 2, skin);
            this._rect(ctx, 9, 1, 1, 2, skin);
            this._rect(ctx, 4, 4, 4, 1, skin);

            // Shadow
            this._rect(ctx, 4, 3, 4, 1, skinDk);

            // Bone
            this._rect(ctx, 5, 5, 2, 4, bone);
            this._rect(ctx, 4, 9, 4, 1, bone);
            this._rect(ctx, 4, 10, 1, 1, boneDk);
            this._rect(ctx, 7, 10, 1, 1, boneDk);

            // Crispy spots
            this._px(ctx, 4, 1, skinDk);
            this._px(ctx, 7, 2, skinDk);
        });
    },

    /** 10x10 별 아이콘 */
    _star() {
        this.cache.star = this._draw(10, 10, ctx => {
            const gold = '#f5c518';
            const shine = '#ffe66d';

            // Star shape
            this._rect(ctx, 4, 0, 2, 2, gold);     // top
            this._rect(ctx, 3, 2, 4, 1, gold);
            this._rect(ctx, 0, 3, 10, 2, gold);     // middle bar
            this._rect(ctx, 1, 5, 8, 1, gold);
            this._rect(ctx, 2, 6, 6, 1, gold);
            this._rect(ctx, 2, 7, 2, 1, gold);
            this._rect(ctx, 6, 7, 2, 1, gold);
            this._rect(ctx, 1, 8, 2, 1, gold);
            this._rect(ctx, 7, 8, 2, 1, gold);

            // Shine
            this._px(ctx, 4, 3, shine);
            this._px(ctx, 5, 4, shine);
        });
    },

    /** 10x10 체크마크 (초록) */
    _check() {
        this.cache.check = this._draw(10, 10, ctx => {
            const green = '#2ed573';

            this._px(ctx, 1, 5, green);
            this._px(ctx, 2, 6, green);
            this._px(ctx, 3, 7, green);
            this._px(ctx, 4, 6, green);
            this._px(ctx, 5, 5, green);
            this._px(ctx, 6, 4, green);
            this._px(ctx, 7, 3, green);
            this._px(ctx, 8, 2, green);

            // Thicken
            this._px(ctx, 1, 6, green);
            this._px(ctx, 2, 7, green);
            this._px(ctx, 3, 8, green);
            this._px(ctx, 4, 7, green);
            this._px(ctx, 5, 6, green);
            this._px(ctx, 6, 5, green);
            this._px(ctx, 7, 4, green);
            this._px(ctx, 8, 3, green);
        });
    },

    /** 10x10 X마크 (빨강) */
    _xmark() {
        this.cache.xmark = this._draw(10, 10, ctx => {
            const red = '#ff4757';

            for (let i = 1; i < 9; i++) {
                this._px(ctx, i, i, red);
                this._px(ctx, 9 - i, i, red);
                // Thicken
                this._px(ctx, i + 1, i, red);
                this._px(ctx, 9 - i + 1, i, red);
            }
        });
    },

    /** 8x8 위 화살표 */
    _arrowUp() {
        this.cache.arrow_up = this._draw(8, 8, ctx => {
            const green = '#2ed573';

            this._rect(ctx, 3, 0, 2, 8, green);
            this._px(ctx, 2, 1, green);
            this._px(ctx, 5, 1, green);
            this._px(ctx, 1, 2, green);
            this._px(ctx, 6, 2, green);
            this._px(ctx, 0, 3, green);
            this._px(ctx, 7, 3, green);
        });
    },

    /** 8x8 아래 화살표 */
    _arrowDown() {
        this.cache.arrow_down = this._draw(8, 8, ctx => {
            const red = '#ff4757';

            this._rect(ctx, 3, 0, 2, 8, red);
            this._px(ctx, 2, 6, red);
            this._px(ctx, 5, 6, red);
            this._px(ctx, 1, 5, red);
            this._px(ctx, 6, 5, red);
            this._px(ctx, 0, 4, red);
            this._px(ctx, 7, 4, red);
        });
    },

    /** 16x16 초승달 */
    _moon() {
        this.cache.moon = this._draw(16, 16, ctx => {
            const moon = '#f5c518';
            const glow = '#ffe66d';

            // Crescent moon shape
            this._rect(ctx, 8, 1, 4, 2, moon);
            this._rect(ctx, 10, 3, 3, 2, moon);
            this._rect(ctx, 11, 5, 3, 3, moon);
            this._rect(ctx, 11, 8, 3, 2, moon);
            this._rect(ctx, 10, 10, 3, 2, moon);
            this._rect(ctx, 8, 12, 4, 2, moon);
            this._rect(ctx, 5, 13, 3, 1, moon);

            // Inner glow
            this._px(ctx, 10, 2, glow);
            this._px(ctx, 12, 6, glow);
            this._px(ctx, 11, 10, glow);
        });
    },

    /** 12x12 Zzz 말풍선 */
    _zzz() {
        this.cache.zzz = this._draw(12, 12, ctx => {
            const color = '#6c5ce7';
            const lite = '#a29bfe';

            // Big Z
            this._rect(ctx, 1, 1, 4, 1, color);
            this._px(ctx, 4, 2, color);
            this._px(ctx, 3, 3, color);
            this._px(ctx, 2, 4, color);
            this._rect(ctx, 1, 5, 4, 1, color);

            // Medium Z
            this._rect(ctx, 5, 4, 3, 1, lite);
            this._px(ctx, 7, 5, lite);
            this._px(ctx, 6, 6, lite);
            this._rect(ctx, 5, 7, 3, 1, lite);

            // Small z
            this._rect(ctx, 8, 7, 2, 1, color);
            this._px(ctx, 9, 8, color);
            this._rect(ctx, 8, 9, 2, 1, color);
        });
    },
};
