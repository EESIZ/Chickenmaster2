#!/usr/bin/env python3
"""
ActionService 테스트 스크립트

플레이어 행동 시스템의 모든 기능을 검증합니다.
"""

import sys
import os
from uuid import uuid4

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from application.action_service import ActionService, ActionRequest
from adapters.repository.json_repository import JsonRepository
from core.domain.player import Player
from core.domain.store import Store
from core.domain.research import Research
from core.domain.value_objects import Money, Percentage, StatValue
from common.enums.action_type import ActionType, CookingAction, AdvertisingAction, OperationAction, ResearchAction, PersonalAction, RestAction
from common.enums.research_type import ResearchType


def test_action_service():
    """ActionService 전체 기능 테스트"""
    print("🧪 ActionService 테스트 시작")
    print("=" * 60)
    
    # 1. 초기 설정
    repository = JsonRepository("test_data/action_test.json")
    action_service = ActionService(repository)
    
    # 2. 테스트 플레이어 생성
    player = Player.create_new("테스트 플레이어", "chef", 2000000)  # 자금 200만원
    repository.save_player(player)
    
    # 3. 테스트 매장 생성
    store = Store.create_new(
        name="테스트 치킨집",
        owner_id=player.id,
        is_first_store=True,
        monthly_rent=500000
    )
    repository.save_store(store)
    
    # 4. 테스트 연구 생성
    from core.domain.research import ResearchTemplate
    from core.domain.value_objects import Progress
    
    research = Research(
        id=uuid4(),
        research_type=ResearchType.RECIPE,
        name="신메뉴 개발",
        description="새로운 치킨 메뉴를 개발합니다",
        progress=Progress(0),
        difficulty=3,
        required_stat="cooking",
        min_stat_required=10
    )
    repository.save_research(research)
    
    print(f"✅ 초기 설정 완료")
    print(f"   플레이어: {player.name}")
    print(f"   자금: {player.money.format_korean()}")
    print(f"   피로도: {player.fatigue.value}%")
    print(f"   스탯: 요리={player.cooking.base_value}, 경영={player.management.base_value}")
    print()
    
    # 5. 행동 카테고리별 테스트
    test_results = []
    
    # 5-1. 조리 행동 테스트
    print("🍳 조리 행동 테스트")
    print("-" * 40)
    cooking_result = test_cooking_actions(action_service, player.id)
    test_results.extend(cooking_result)
    
    # 5-2. 광고 행동 테스트
    print("\n📢 광고 행동 테스트")
    print("-" * 40)
    advertising_result = test_advertising_actions(action_service, player.id, store.id)
    test_results.extend(advertising_result)
    
    # 피로도 회복을 위한 수면
    print("\n💤 피로도 회복 (중간 수면)")
    print("-" * 40)
    rest_for_recovery(action_service, player.id)
    
    # 5-3. 운영 행동 테스트
    print("\n🏪 운영 행동 테스트")
    print("-" * 40)
    operation_result = test_operation_actions(action_service, player.id)
    test_results.extend(operation_result)
    
    # 5-4. 연구 행동 테스트
    print("\n🔬 연구 행동 테스트")
    print("-" * 40)
    research_result = test_research_actions(action_service, player.id, research.id)
    test_results.extend(research_result)
    
    # 5-5. 개인 행동 테스트
    print("\n🏃 개인 행동 테스트")
    print("-" * 40)
    personal_result = test_personal_actions(action_service, player.id)
    test_results.extend(personal_result)
    
    # 5-6. 휴식 행동 테스트
    print("\n😴 휴식 행동 테스트")
    print("-" * 40)
    rest_result = test_rest_actions(action_service, player.id)
    test_results.extend(rest_result)
    
    # 6. 특수 상황 테스트
    print("\n⚠️ 특수 상황 테스트")
    print("-" * 40)
    special_result = test_special_cases(action_service, player.id)
    test_results.extend(special_result)
    
    # 7. 가용 행동 목록 테스트
    print("\n📋 가용 행동 목록 테스트")
    print("-" * 40)
    available_result = test_available_actions(action_service, player.id)
    test_results.extend(available_result)
    
    # 8. 결과 요약
    print("\n" + "=" * 60)
    print("🎯 테스트 결과 요약")
    print("=" * 60)
    
    success_count = sum(1 for result in test_results if result[0])
    total_count = len(test_results)
    
    print(f"총 테스트: {total_count}개")
    print(f"성공: {success_count}개")
    print(f"실패: {total_count - success_count}개")
    print(f"성공률: {success_count/total_count*100:.1f}%")
    
    # 실패한 테스트 상세 출력
    failed_tests = [result for result in test_results if not result[0]]
    if failed_tests:
        print("\n❌ 실패한 테스트:")
        for success, test_name, error in failed_tests:
            print(f"   - {test_name}: {error}")
    else:
        print("\n🎉 모든 테스트가 성공했습니다!")
    
    # 최종 플레이어 상태 확인
    final_player = repository.get_player(player.id)
    print(f"\n📊 최종 플레이어 상태:")
    print(f"   자금: {final_player.money.format_korean()}")
    print(f"   피로도: {final_player.fatigue.value}%")
    print(f"   스탯: 요리={final_player.cooking.base_value}, 경영={final_player.management.base_value}, 서비스={final_player.service.base_value}")
    
    return success_count == total_count


def rest_for_recovery(action_service: ActionService, player_id):
    """피로도 회복을 위한 수면"""
    try:
        request = ActionRequest(
            player_id=player_id,
            action_type=ActionType.REST,
            specific_action="SLEEP",
            time_hours=8  # 8시간 수면으로 충분히 회복
        )
        result = action_service.execute_action(request)
        
        if result.success:
            print(f"✅ 피로도 회복: {result.message}")
            print(f"   피로도 변화: {result.fatigue_change}")
        else:
            print(f"❌ 피로도 회복 실패: {result.message}")
    except Exception as e:
        print(f"❌ 피로도 회복 오류: {str(e)}")


def test_cooking_actions(action_service: ActionService, player_id):
    """조리 행동 테스트"""
    results = []
    
    # 재료 준비
    try:
        request = ActionRequest(
            player_id=player_id,
            action_type=ActionType.COOKING,
            specific_action="PREPARE_INGREDIENTS",
            time_hours=2
        )
        result = action_service.execute_action(request)
        
        if result.success:
            print(f"✅ 재료 준비: {result.message}")
            print(f"   시간 소모: {result.time_consumed}시간, 피로도: +{result.fatigue_change}")
            results.append((True, "재료 준비", ""))
        else:
            print(f"❌ 재료 준비 실패: {result.message}")
            results.append((False, "재료 준비", result.message))
    except Exception as e:
        print(f"❌ 재료 준비 오류: {str(e)}")
        results.append((False, "재료 준비", str(e)))
    
    # 조리
    try:
        request = ActionRequest(
            player_id=player_id,
            action_type=ActionType.COOKING,
            specific_action="COOK",
            time_hours=3
        )
        result = action_service.execute_action(request)
        
        if result.success:
            print(f"✅ 조리: {result.message}")
            print(f"   경험치 획득: {result.experience_gains}")
            results.append((True, "조리", ""))
        else:
            print(f"❌ 조리 실패: {result.message}")
            results.append((False, "조리", result.message))
    except Exception as e:
        print(f"❌ 조리 오류: {str(e)}")
        results.append((False, "조리", str(e)))
    
    return results


def test_advertising_actions(action_service: ActionService, player_id, store_id):
    """광고 행동 테스트"""
    results = []
    
    # 전단지 배포
    try:
        request = ActionRequest(
            player_id=player_id,
            action_type=ActionType.ADVERTISING,
            specific_action="FLYER",
            time_hours=2,
            target_id=store_id
        )
        result = action_service.execute_action(request)
        
        if result.success:
            print(f"✅ 전단지 배포: {result.message}")
            print(f"   자금 소모: {abs(result.money_change):,}원")
            results.append((True, "전단지 배포", ""))
        else:
            print(f"❌ 전단지 배포 실패: {result.message}")
            results.append((False, "전단지 배포", result.message))
    except Exception as e:
        print(f"❌ 전단지 배포 오류: {str(e)}")
        results.append((False, "전단지 배포", str(e)))
    
    # 온라인 광고
    try:
        request = ActionRequest(
            player_id=player_id,
            action_type=ActionType.ADVERTISING,
            specific_action="ONLINE_AD",
            time_hours=1,
            target_id=store_id
        )
        result = action_service.execute_action(request)
        
        if result.success:
            print(f"✅ 온라인 광고: {result.message}")
            results.append((True, "온라인 광고", ""))
        else:
            print(f"❌ 온라인 광고 실패: {result.message}")
            results.append((False, "온라인 광고", result.message))
    except Exception as e:
        print(f"❌ 온라인 광고 오류: {str(e)}")
        results.append((False, "온라인 광고", str(e)))
    
    return results


def test_operation_actions(action_service: ActionService, player_id):
    """운영 행동 테스트"""
    results = []
    
    # 매장 청소
    try:
        request = ActionRequest(
            player_id=player_id,
            action_type=ActionType.OPERATION,
            specific_action="CLEAN",
            time_hours=2
        )
        result = action_service.execute_action(request)
        
        if result.success:
            print(f"✅ 매장 청소: {result.message}")
            print(f"   서비스 경험치: {result.experience_gains.get('service', 0)}")
            results.append((True, "매장 청소", ""))
        else:
            print(f"❌ 매장 청소 실패: {result.message}")
            results.append((False, "매장 청소", result.message))
    except Exception as e:
        print(f"❌ 매장 청소 오류: {str(e)}")
        results.append((False, "매장 청소", str(e)))
    
    # 장비 점검
    try:
        request = ActionRequest(
            player_id=player_id,
            action_type=ActionType.OPERATION,
            specific_action="EQUIPMENT_CHECK",
            time_hours=1
        )
        result = action_service.execute_action(request)
        
        if result.success:
            print(f"✅ 장비 점검: {result.message}")
            results.append((True, "장비 점검", ""))
        else:
            print(f"❌ 장비 점검 실패: {result.message}")
            results.append((False, "장비 점검", result.message))
    except Exception as e:
        print(f"❌ 장비 점검 오류: {str(e)}")
        results.append((False, "장비 점검", str(e)))
    
    return results


def test_research_actions(action_service: ActionService, player_id, research_id):
    """연구 행동 테스트"""
    results = []
    
    # 레시피 연구
    try:
        request = ActionRequest(
            player_id=player_id,
            action_type=ActionType.RESEARCH,
            specific_action="RECIPE",
            time_hours=3,
            target_id=research_id
        )
        result = action_service.execute_action(request)
        
        if result.success:
            print(f"✅ 레시피 연구: {result.message}")
            print(f"   요리 경험치: {result.experience_gains.get('cooking', 0)}")
            results.append((True, "레시피 연구", ""))
        else:
            print(f"❌ 레시피 연구 실패: {result.message}")
            results.append((False, "레시피 연구", result.message))
    except Exception as e:
        print(f"❌ 레시피 연구 오류: {str(e)}")
        results.append((False, "레시피 연구", str(e)))
    
    return results


def test_personal_actions(action_service: ActionService, player_id):
    """개인 행동 테스트"""
    results = []
    
    # 운동
    try:
        request = ActionRequest(
            player_id=player_id,
            action_type=ActionType.PERSONAL,
            specific_action="EXERCISE",
            time_hours=2
        )
        result = action_service.execute_action(request)
        
        if result.success:
            print(f"✅ 운동: {result.message}")
            print(f"   체력 경험치: {result.experience_gains.get('stamina', 0)}")
            results.append((True, "운동", ""))
        else:
            print(f"❌ 운동 실패: {result.message}")
            results.append((False, "운동", result.message))
    except Exception as e:
        print(f"❌ 운동 오류: {str(e)}")
        results.append((False, "운동", str(e)))
    
    # 학습
    try:
        request = ActionRequest(
            player_id=player_id,
            action_type=ActionType.PERSONAL,
            specific_action="STUDY",
            time_hours=2
        )
        result = action_service.execute_action(request)
        
        if result.success:
            print(f"✅ 학습: {result.message}")
            results.append((True, "학습", ""))
        else:
            print(f"❌ 학습 실패: {result.message}")
            results.append((False, "학습", result.message))
    except Exception as e:
        print(f"❌ 학습 오류: {str(e)}")
        results.append((False, "학습", str(e)))
    
    return results


def test_rest_actions(action_service: ActionService, player_id):
    """휴식 행동 테스트"""
    results = []
    
    # 수면
    try:
        request = ActionRequest(
            player_id=player_id,
            action_type=ActionType.REST,
            specific_action="SLEEP",
            time_hours=4  # 4시간 수면
        )
        result = action_service.execute_action(request)
        
        if result.success:
            print(f"✅ 수면: {result.message}")
            print(f"   피로도 변화: {result.fatigue_change} (음수면 회복)")
            results.append((True, "수면", ""))
        else:
            print(f"❌ 수면 실패: {result.message}")
            results.append((False, "수면", result.message))
    except Exception as e:
        print(f"❌ 수면 오류: {str(e)}")
        results.append((False, "수면", str(e)))
    
    return results


def test_special_cases(action_service: ActionService, player_id):
    """특수 상황 테스트"""
    results = []
    
    # 잘못된 행동 테스트
    try:
        request = ActionRequest(
            player_id=player_id,
            action_type=ActionType.COOKING,
            specific_action="INVALID_ACTION",
            time_hours=1
        )
        result = action_service.execute_action(request)
        
        if not result.success:
            print(f"✅ 잘못된 행동 검증: {result.message}")
            results.append((True, "잘못된 행동 검증", ""))
        else:
            print(f"❌ 잘못된 행동이 허용됨: {result.message}")
            results.append((False, "잘못된 행동 검증", "잘못된 행동이 허용됨"))
    except Exception as e:
        print(f"❌ 잘못된 행동 테스트 오류: {str(e)}")
        results.append((False, "잘못된 행동 검증", str(e)))
    
    # 존재하지 않는 플레이어 테스트
    try:
        request = ActionRequest(
            player_id=uuid4(),  # 존재하지 않는 ID
            action_type=ActionType.REST,
            specific_action="SLEEP",
            time_hours=1
        )
        result = action_service.execute_action(request)
        
        if not result.success:
            print(f"✅ 존재하지 않는 플레이어 검증: {result.message}")
            results.append((True, "존재하지 않는 플레이어 검증", ""))
        else:
            print(f"❌ 존재하지 않는 플레이어가 허용됨: {result.message}")
            results.append((False, "존재하지 않는 플레이어 검증", "존재하지 않는 플레이어가 허용됨"))
    except Exception as e:
        print(f"❌ 존재하지 않는 플레이어 테스트 오류: {str(e)}")
        results.append((False, "존재하지 않는 플레이어 검증", str(e)))
    
    return results


def test_available_actions(action_service: ActionService, player_id):
    """가용 행동 목록 테스트"""
    results = []
    
    try:
        # 12시간 남은 상황에서 가용 행동 조회
        available_actions = action_service.get_available_actions(player_id, 12)
        
        if available_actions:
            print(f"✅ 가용 행동 목록 조회 성공: {len(available_actions)}개 행동")
            
            # 카테고리별 행동 수 확인
            categories = {}
            for action in available_actions:
                action_type = action["action_type"]
                if action_type not in categories:
                    categories[action_type] = 0
                categories[action_type] += 1
            
            for category, count in categories.items():
                print(f"   {category.name}: {count}개")
            
            results.append((True, "가용 행동 목록 조회", ""))
        else:
            print(f"❌ 가용 행동 목록이 비어있음")
            results.append((False, "가용 행동 목록 조회", "목록이 비어있음"))
        
        # 시간이 부족한 상황 테스트
        limited_actions = action_service.get_available_actions(player_id, 1)  # 1시간만 남음
        
        if len(limited_actions) < len(available_actions):
            print(f"✅ 시간 제한 필터링 작동: {len(limited_actions)}개 행동 (전체 {len(available_actions)}개)")
            results.append((True, "시간 제한 필터링", ""))
        else:
            print(f"❌ 시간 제한 필터링 미작동")
            results.append((False, "시간 제한 필터링", "시간 제한이 적용되지 않음"))
            
    except Exception as e:
        print(f"❌ 가용 행동 목록 테스트 오류: {str(e)}")
        results.append((False, "가용 행동 목록 조회", str(e)))
    
    return results


if __name__ == "__main__":
    success = test_action_service()
    sys.exit(0 if success else 1)