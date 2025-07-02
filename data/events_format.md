# 이벤트 CSV 파일 형식

## 개요
이벤트 시스템은 `data/events.csv` 파일에서 이벤트 데이터를 읽어옵니다.
게임 코드는 이 파일을 **읽기 전용**으로만 사용하며, 파일을 수정하지 않습니다.

## CSV 컬럼 구조

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| `id` | string | 이벤트 고유 ID (예: daily_001) |
| `name` | string | 이벤트 이름 |
| `description` | string | 이벤트 설명 |
| `event_type` | string | 이벤트 유형 (DAILY, OPPORTUNITY, CHOICE, CRISIS, CHAIN) |
| `probability_weight` | integer | 발생 확률 가중치 |
| `auto_effects` | JSON string | 자동 효과 목록 |
| `choices` | JSON string | 선택지 목록 |

## 이벤트 유형

### DAILY (일상 이벤트)
- 높은 확률로 발생
- auto_effects에 효과 정의
- choices는 빈 배열 []

### OPPORTUNITY (기회 이벤트)
- 긍정적인 효과
- auto_effects에 효과 정의
- choices는 빈 배열 []

### CRISIS (위기 이벤트)
- 부정적인 효과
- auto_effects에 효과 정의  
- choices는 빈 배열 []

### CHOICE (선택형 이벤트)
- 플레이어가 선택지를 고름
- auto_effects는 빈 배열 []
- choices에 선택지들 정의

### CHAIN (연쇄 이벤트)
- 다음 이벤트로 연결
- choices에 선택지들 정의

## JSON 데이터 형식

### auto_effects 형식
```json
[
  {
    "type": "money_gain",
    "amount": 5000
  },
  {
    "type": "awareness_gain", 
    "amount": 10
  }
]
```

### choices 형식
```json
[
  {
    "id": "develop",
    "description": "바로 개발해보자 (요리 경험치 +10, 자금 -20000원)",
    "effects": [
      {
        "type": "stat_gain",
        "stat": "cooking", 
        "amount": 10
      },
      {
        "type": "money_loss",
        "amount": 20000
      }
    ],
    "requirements": {
      "money": 20000
    }
  }
]
```

## 효과 타입 목록

| 효과 타입 | 설명 | 필수 파라미터 |
|-----------|------|---------------|
| `money_gain` | 자금 획득 | amount |
| `money_loss` | 자금 손실 | amount |
| `stat_gain` | 스탯 증가 | stat, amount |
| `stat_loss` | 스탯 감소 | stat, amount |
| `awareness_gain` | 인지도 증가 | amount |
| `awareness_loss` | 인지도 감소 | amount |
| `chain_flag` | 연쇄 이벤트 플래그 | value |

## 스탯 목록
- `cooking` - 요리
- `management` - 경영  
- `service` - 서비스
- `tech` - 기술
- `stamina` - 체력

## 주의사항

1. **JSON 이스케이프**: CSV에서 JSON 문자열은 따옴표를 `""` 형태로 이스케이프
2. **읽기 전용**: 게임 코드는 이 파일을 수정하지 않음
3. **형식 검증**: 잘못된 형식의 데이터는 로드 시 예외 발생
4. **ID 중복 금지**: 이벤트 ID는 중복되지 않아야 함

## 예시 행
```csv
daily_001,평범한 하루,오늘은 특별한 일 없이 평범하게 지나갔습니다.,DAILY,300,"[{""type"": ""money_gain"", ""amount"": 5000}]",[]
``` 