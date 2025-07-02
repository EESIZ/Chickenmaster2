#!/usr/bin/env python3
"""
AI 분석 캐시 시스템 테스트

JsonRepository의 AI 분석 데이터 저장/로드 기능을 검증합니다.
"""

import sys
import os
from uuid import uuid4
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from adapters.repository.json_repository import JsonRepository


def test_ai_analysis_cache():
    """AI 분석 캐시 시스템 테스트"""
    print("🧪 AI 분석 캐시 시스템 테스트 시작")
    
    # 테스트용 저장소 생성
    repo = JsonRepository("test_data/ai_cache_test")
    
    # 테스트 데이터
    player_id = uuid4()
    
    print("\n1️⃣ 플레이어 분석 데이터 저장 테스트")
    analysis_data = {
        'player_type': '가격_민감형',
        'investment_style': '품질_추구형',
        'reaction_speed': '즉석_대응형',
        'risk_preference': '안정_추구형',
        'competitive_style': '정면승부형',
        'learning_ability': 85,
        'pressure_response': '감정적_의사결정',
        'pattern_confidence': 0.75,
        'last_analysis_turn': 15
    }
    
    success = repo.save_player_analysis(player_id, analysis_data)
    print(f"   플레이어 분석 저장: {'✅ 성공' if success else '❌ 실패'}")
    
    # 저장된 데이터 불러오기
    loaded_data = repo.load_player_analysis(player_id)
    if loaded_data:
        print(f"   분석 데이터 로드: ✅ 성공")
        print(f"   플레이어 타입: {loaded_data.get('player_type')}")
        print(f"   학습 능력: {loaded_data.get('learning_ability')}")
    else:
        print(f"   분석 데이터 로드: ❌ 실패")
    
    print("\n2️⃣ 턴별 분석 히스토리 테스트")
    
    # 여러 턴의 분석 데이터 저장
    for turn in range(10, 16):
        turn_analysis = {
            'player_actions': {
                str(player_id): {
                    'actions_taken': ['가격_인하', '마케팅_강화'],
                    'money_spent': 50000,
                    'fatigue_change': 15,
                    'reaction_to_ai': '공격적_대응',
                    'timing_score': 8.5
                }
            },
            'market_situation': {
                'competition_level': 'high',
                'customer_demand': 85
            }
        }
        
        success = repo.save_turn_analysis(turn, turn_analysis)
        if success:
            print(f"   턴 {turn} 분석 저장: ✅")
        else:
            print(f"   턴 {turn} 분석 저장: ❌")
    
    # 최근 턴 히스토리 불러오기
    history = repo.load_turn_analysis_history(player_id, recent_turns=3)
    print(f"\n   최근 3턴 히스토리 로드: {'✅ 성공' if history else '❌ 실패'}")
    print(f"   히스토리 개수: {len(history)}개")
    
    if history:
        for record in history:
            turn_num = record['turn_number']
            actions = record['player_data'].get('actions_taken', [])
            print(f"   - 턴 {turn_num}: {', '.join(actions)}")
    
    print("\n3️⃣ 경쟁 상황 데이터 테스트")
    
    competitive_data = {
        'market_share': {
            str(player_id): 35.5,
            'competitor_1': 28.2,
            'competitor_2': 22.1
        },
        'pricing_trends': {
            'average_price': 8500,
            'price_war_active': True,
            'trend_direction': 'downward'
        },
        'last_updated_turn': 15
    }
    
    success = repo.update_competitive_situation(competitive_data)
    print(f"   경쟁 상황 업데이트: {'✅ 성공' if success else '❌ 실패'}")
    
    situation = repo.get_competitive_situation()
    if situation:
        print(f"   경쟁 상황 로드: ✅ 성공")
        print(f"   플레이어 시장점유율: {situation.get('market_share', {}).get(str(player_id), 0)}%")
        print(f"   가격전쟁 활성: {situation.get('pricing_trends', {}).get('price_war_active', False)}")
    
    print("\n4️⃣ 캐시 통계 및 관리 테스트")
    
    stats = repo.get_ai_cache_stats()
    print(f"   캐시 통계:")
    print(f"   - 플레이어 프로필: {stats.get('player_profiles_count', 0)}개")
    print(f"   - 턴 히스토리: {stats.get('turn_history_count', 0)}개")
    print(f"   - 경쟁 데이터: {stats.get('competitive_data_keys', 0)}개 키")
    
    print("\n5️⃣ 세이브/로드 통합 테스트")
    
    # 게임 데이터와 함께 저장
    game_data = {
        'current_turn': 15,
        'players': [{'id': str(player_id), 'name': '테스트플레이어'}]
    }
    
    save_success = repo.save_game("ai_cache_test", game_data)
    print(f"   게임+AI캐시 저장: {'✅ 성공' if save_success else '❌ 실패'}")
    
    # 새 저장소 인스턴스에서 로드 테스트
    new_repo = JsonRepository("test_data/ai_cache_test")
    loaded_game = new_repo.load_game("ai_cache_test")
    
    if loaded_game:
        # AI 캐시가 복원되었는지 확인
        restored_analysis = new_repo.load_player_analysis(player_id)
        if restored_analysis:
            print(f"   AI캐시 복원: ✅ 성공")
            print(f"   복원된 플레이어 타입: {restored_analysis.get('player_type')}")
        else:
            print(f"   AI캐시 복원: ❌ 실패")
    else:
        print(f"   게임 로드: ❌ 실패")
    
    print("\n6️⃣ 캐시 초기화 테스트")
    
    clear_success = repo.clear_ai_analysis_cache()
    print(f"   캐시 초기화: {'✅ 성공' if clear_success else '❌ 실패'}")
    
    # 초기화 후 데이터 확인
    cleared_stats = repo.get_ai_cache_stats()
    all_cleared = all(count == 0 for key, count in cleared_stats.items() 
                     if key != 'competitive_data_keys' and not key.startswith('error'))
    
    print(f"   초기화 확인: {'✅ 성공' if all_cleared else '❌ 실패'}")
    
    print("\n🎯 AI 분석 캐시 시스템 테스트 완료!")
    return True


if __name__ == "__main__":
    try:
        test_ai_analysis_cache()
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc() 