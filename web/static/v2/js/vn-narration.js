/**
 * VN 나레이션 텍스트 DB
 */
const VN_TEXT = {
    PREP: {
        intro: [
            "아침 햇살이 주방 창문으로 스며든다...",
            "오늘도 치킨집의 하루가 시작됐다.",
        ],
        action_prompt: "준비 시간이 {hours}시간 남았다. 무엇을 할까?",
        confirm: "좋아, 준비는 이 정도면 됐다. 가게를 열자!",
        results_intro: "준비 결과를 확인하자...",
    },
    BUSINESS: {
        intro: [
            "가게 문을 활짝 열었다!",
            "오늘도 열심히 팔아보자.",
        ],
        customer_arrive: "{count}명의 손님이 들어왔다!",
        turned_away: "{count}명이 빈손으로 돌아갔다...",
        no_stock: "이런... 준비한 치킨이 거의 다 떨어졌다!",
        prepare_done: "재료 준비 완료! 준비량: {qty}",
        rest_done: "잠깐 쉬었더니 좀 낫다. 피로: {fatigue}",
        summary_intro: "오늘 영업이 끝났다.",
    },
    NIGHT: {
        intro: [
            "가게 문을 닫고 정리를 마쳤다.",
            "저녁 시간... 자기 개발의 시간이다.",
        ],
        action_prompt: "야간 시간이 {hours}시간 남았다. 무엇을 할까?",
        confirm: "오늘 밤도 알찬 시간이었다. 이제 쉬자.",
        results_intro: "야간 활동 결과...",
    },
    SLEEP: {
        intro: [
            "이불 속으로 들어간다...",
            "오늘도 수고했다. 내일은 더 잘하자.",
        ],
        recovery: "{hours}시간 수면 — 피로 -{recovery} 회복",
        next_day: "새로운 아침이 밝았다!",
    },
    CHARACTERS: {
        narrator: "나레이션",
        owner: "나",
        parttime: "알바생",
        customer: "손님",
        inspector: "검사관",
    },
};
