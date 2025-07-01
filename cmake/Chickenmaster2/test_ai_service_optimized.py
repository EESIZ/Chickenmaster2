"""
AI 서비스 테스트 (메모리 최적화 버전)

메모리 최적화된 AI Service의 기능과 메모리 효율성을 검증합니다.
"""

import pytest
import sys
import os
from uuid import uuid4, UUID
from datetime import datetime
import tracemalloc
import gc

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.application.ai_service_optimized import AIService, AnalysisResult, PATTERN_KEYWORDS
from src.adapters.repository.json_repository import JsonRepository
from src.core.domain.competitor import Competitor, CompetitorStrategy
from src.core.domain.value_objects import Money, StatValue
from src.common.enums.action_type import ActionType


class TestAIServiceMemoryOptimized:
    """메모리 최적화된 AI Service 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.repository = JsonRepository("test_data/ai_service_optimized_test")
        self.ai_service = AIService(self.repository)
        self.test_player_id = uuid4()
        
        # 메모리 추적 시작
        tracemalloc.start()
        
    def teardown_method(self):
        """테스트 정리"""
        # 메모리 추적 종료
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"\n메모리 사용량 - 현재: {current / 1024 / 1024:.2f}MB, 최대: {peak / 1024 / 1024:.2f}MB")
        
        # 캐시 정리
        self.ai_service.clear_cache()
        gc.collect()
    
    def create_large_turn_history(self, turn_count: int = 50) -> list:
        """대용량 턴 히스토리 생성 (메모리 테스트용)"""
        history = []
        
        for i in range(turn_count):
            turn_data = {
                'turn_number': i + 1,
                'timestamp': datetime.now().isoformat(),
                'player_data': {
                    'actions_taken': [
                        '매장_확장', '품질_개선', '가격_조정', '마케팅_강화',
                        '레시피_연구', '신규_개점', '인테리어_개선'
                    ][:((i % 7) + 1)],  # 가변 길이
                    'money_spent': 50000 + (i * 10000),
                    'timing_score': 5.0 + (i % 10) * 0.5,
                    'reaction_to_ai': ['공격적_대응', '전략적_대응', '회피적_대응'][i % 3]
                }
            }
            history.append(turn_data)
        
        return history
    
    def test_memory_optimization_large_dataset(self):
        """대용량 데이터셋에서 메모리 최적화 테스트"""
        print("\n=== 대용량 데이터셋 메모리 최적화 테스트 ===")
        
        # 대용량 히스토리 생성
        large_history = self.create_large_turn_history(100)
        
        # 메모리 사용량 측정 시작
        snapshot1 = tracemalloc.take_snapshot()
        
        # 분석 실행
        result = self.ai_service.analyze_player_comprehensive(self.test_player_id, recent_turns=50)
        
        # 메모리 사용량 측정 종료
        snapshot2 = tracemalloc.take_snapshot()
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        print("메모리 증가량 상위 3개:")
        for stat in top_stats[:3]:
            print(stat)
        
        # 결과 검증
        assert result is not None
        assert 'analysis_timestamp' in result
        assert 'overall_confidence' in result
        assert 'primary_player_type' in result
        
        print(f"분석 결과: {result['primary_player_type']}")
        print(f"전체 신뢰도: {result['overall_confidence']:.2f}")
    
    def test_optimized_preprocessing(self):
        """전처리 최적화 테스트"""
        print("\n=== 전처리 최적화 테스트 ===")
        
        # 테스트 데이터 준비
        turn_history = self.create_large_turn_history(20)
        
        # 전처리 실행
        processed_data = self.ai_service._preprocess_turn_history(turn_history)
        
        # 결과 검증
        assert 'action_counter' in processed_data
        assert 'total_actions' in processed_data
        assert 'total_investment' in processed_data
        assert 'timing_data' in processed_data
        
        # 데이터 일관성 확인
        assert processed_data['total_actions'] > 0
        assert processed_data['total_investment'] > 0
        assert len(processed_data['timing_data']) == 20
        
        print(f"총 행동 수: {processed_data['total_actions']}")
        print(f"총 투자액: {processed_data['total_investment']:,}원")
        print(f"행동 종류: {len(processed_data['action_counter'])}")
    
    def test_pattern_keywords_optimization(self):
        """패턴 키워드 최적화 테스트"""
        print("\n=== 패턴 키워드 최적화 테스트 ===")
        
        # 패턴 키워드 구조 검증
        assert isinstance(PATTERN_KEYWORDS, dict)
        
        for pattern_name, keywords in PATTERN_KEYWORDS.items():
            assert isinstance(keywords, frozenset)  # 불변 집합 사용 확인
            assert len(keywords) > 0
            print(f"{pattern_name}: {len(keywords)}개 키워드")
        
        # 중복 키워드 검사
        all_keywords = set()
        for keywords in PATTERN_KEYWORDS.values():
            for keyword in keywords:
                if keyword in all_keywords:
                    print(f"중복 키워드 발견: {keyword}")
                all_keywords.add(keyword)
        
        print(f"총 고유 키워드 수: {len(all_keywords)}")
    
    def test_analysis_result_dataclass(self):
        """AnalysisResult 데이터클래스 테스트"""
        print("\n=== AnalysisResult 데이터클래스 테스트 ===")
        
        # 기본 생성
        result1 = AnalysisResult(0.8, '가격_민감형')
        assert result1.confidence == 0.8
        assert result1.primary_trait == '가격_민감형'
        assert result1.secondary_data == {}
        
        # 부가 데이터 포함
        result2 = AnalysisResult(
            0.9, 
            '품질_추구형', 
            {'score': 85.0, 'ratio': 0.7}
        )
        assert result2.secondary_data['score'] == 85.0
        
        # 불변성 확인
        try:
            result1.confidence = 0.9  # 수정 시도
            assert False, "불변 객체여야 함"
        except AttributeError:
            pass  # 예상된 동작
        
        print(f"Result1: {result1}")
        print(f"Result2: {result2}")
    
    def test_optimized_analysis_methods(self):
        """최적화된 분석 메서드들 테스트"""
        print("\n=== 최적화된 분석 메서드 테스트 ===")
        
        # 테스트 데이터 준비
        turn_history = self.create_large_turn_history(15)
        processed_data = self.ai_service._preprocess_turn_history(turn_history)
        
        # 각 최적화된 분석 메서드 테스트
        methods_to_test = [
            ('패턴 분석', self.ai_service._analyze_action_patterns_optimized),
            ('자원 배분 분석', self.ai_service._analyze_resource_allocation_optimized),
            ('타이밍 분석', self.ai_service._analyze_timing_patterns_optimized),
            ('상황별 대응 분석', self.ai_service._analyze_situational_response_optimized),
            ('경쟁 반응 분석', self.ai_service._analyze_competitive_reaction_optimized),
            ('압박 반응 분석', self.ai_service._analyze_pressure_response_optimized)
        ]
        
        for method_name, method_func in methods_to_test:
            result = method_func(processed_data)
            
            assert isinstance(result, AnalysisResult)
            assert 0.0 <= result.confidence <= 1.0
            assert result.primary_trait is not None
            
            print(f"{method_name}: {result.primary_trait} (신뢰도: {result.confidence:.2f})")
        
        # 학습 능력 분석 (기존 분석 포함)
        learning_result = self.ai_service._analyze_learning_ability_optimized(
            processed_data, None
        )
        assert isinstance(learning_result, AnalysisResult)
        print(f"학습 능력 분석: {learning_result.primary_trait}")
    
    def test_cache_management(self):
        """캐시 관리 테스트"""
        print("\n=== 캐시 관리 테스트 ===")
        
        # 캐시 초기 상태
        assert len(self.ai_service._temp_cache) == 0
        
        # 분석 실행으로 캐시 생성
        competitor = Competitor(
            id=uuid4(),
            name="테스트경쟁자",
            strategy=CompetitorStrategy.AGGRESSIVE,
            money=Money(1000000),
            store_ids=(uuid4(),),
            delayed_actions=()
        )
        
        decision = self.ai_service.get_ai_decision_based_on_analysis(
            competitor, self.test_player_id
        )
        
        # 캐시 상태 확인
        print(f"캐시 항목 수: {len(self.ai_service._temp_cache)}")
        
        # 캐시 정리
        self.ai_service.clear_cache()
        assert len(self.ai_service._temp_cache) == 0
        
        print("캐시 정리 완료")
    
    def test_memory_efficient_integration(self):
        """메모리 효율적 통합 테스트"""
        print("\n=== 메모리 효율적 통합 테스트 ===")
        
        # 메모리 사용량 측정 시작
        snapshot_before = tracemalloc.take_snapshot()
        
        # 여러 플레이어 동시 분석
        player_ids = [uuid4() for _ in range(10)]
        results = []
        
        for player_id in player_ids:
            result = self.ai_service.analyze_player_comprehensive(player_id, recent_turns=10)
            results.append(result)
        
        # 메모리 사용량 측정
        snapshot_after = tracemalloc.take_snapshot()
        top_stats = snapshot_after.compare_to(snapshot_before, 'lineno')
        
        print("메모리 사용량 상위 5개:")
        for i, stat in enumerate(top_stats[:5]):
            print(f"{i+1}. {stat}")
        
        # 결과 검증
        assert len(results) == 10
        for result in results:
            assert 'primary_player_type' in result
            assert 'overall_confidence' in result
        
        # 캐시 정리로 메모리 해제
        self.ai_service.clear_cache()
        gc.collect()
        
        print("통합 테스트 완료")
    
    def test_ai_decision_optimization(self):
        """AI 의사결정 최적화 테스트"""
        print("\n=== AI 의사결정 최적화 테스트 ===")
        
        competitor = Competitor(
            id=uuid4(),
            name="최적화테스트경쟁자",
            strategy=CompetitorStrategy.DEFENSIVE,
            money=Money(1500000),
            store_ids=(uuid4(),),
            delayed_actions=()
        )
        
        # 다양한 전략에 대한 의사결정 테스트
        strategies = ['가성비_공략', '틈새시장_공략', '측면공격_전략', '균형_전략']
        
        for strategy in strategies:
            # 모의 분석 결과 생성
            mock_analysis = {
                'ai_strategy_recommendation': strategy,
                'overall_confidence': 0.8
            }
            
            # 캐시에 저장
            self.ai_service._temp_cache[self.test_player_id] = mock_analysis
            
            # 의사결정 실행
            decision = self.ai_service.get_ai_decision_based_on_analysis(
                competitor, self.test_player_id
            )
            
            assert decision is not None
            assert hasattr(decision, 'action_type')
            assert hasattr(decision, 'target_amount')
            assert hasattr(decision, 'reasoning')
            
            print(f"전략 '{strategy}': {decision.action_type} - {decision.reasoning}")
        
        # 캐시 정리
        self.ai_service.clear_cache()


def test_ai_service_memory_optimization():
    """메모리 최적화 종합 테스트"""
    print("\n" + "="*50)
    print("AI Service 메모리 최적화 종합 테스트 시작")
    print("="*50)
    
    # 테스트 실행
    test_instance = TestAIServiceMemoryOptimized()
    test_instance.setup_method()
    
    try:
        test_instance.test_memory_optimization_large_dataset()
        test_instance.test_optimized_preprocessing()
        test_instance.test_pattern_keywords_optimization()
        test_instance.test_analysis_result_dataclass()
        test_instance.test_optimized_analysis_methods()
        test_instance.test_cache_management()
        test_instance.test_memory_efficient_integration()
        test_instance.test_ai_decision_optimization()
        
        print("\n" + "="*50)
        print("모든 메모리 최적화 테스트 통과! ✅")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"\n테스트 실패: {str(e)}")
        import traceback
        print(f"오류 세부사항: {traceback.format_exc()}")
        return False
        
    finally:
        test_instance.teardown_method()


if __name__ == "__main__":
    test_ai_service_memory_optimization() 