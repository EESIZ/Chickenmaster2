"""
AI 서비스 (메모리 최적화 버전)

경쟁자 AI의 플레이어 분석과 의사결정을 담당하는 애플리케이션 서비스입니다.
메모리 사용량을 최적화하여 대용량 데이터 처리 시에도 효율적으로 동작합니다.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
from uuid import UUID
from datetime import datetime
import statistics
from collections import defaultdict, Counter
from dataclasses import dataclass, field

from core.ports.repository_port import RepositoryPort
from core.ports.ai_engine_port import AIEnginePort, AIDecision
from core.domain.competitor import Competitor, CompetitorStrategy
from core.domain.player import Player
from core.domain.turn import TurnResult
from common.enums.action_type import ActionType


# 메모리 효율적인 분석 결과 저장을 위한 데이터클래스
@dataclass(frozen=True)
class AnalysisResult:
    """분석 결과를 메모리 효율적으로 저장"""
    confidence: float
    primary_trait: str
    secondary_data: Dict[str, float] = field(default_factory=dict)


# 패턴 매칭 최적화를 위한 상수
PATTERN_KEYWORDS = {
    'price': frozenset(['가격_인하', '가격_인상', '가격_조정']),
    'quality': frozenset(['품질_개선', '레시피_연구', '재료_업그레이드']),
    'expansion': frozenset(['매장_확장', '신규_개점', '인테리어_개선']),
    'marketing': frozenset(['마케팅', '광고', '홍보']),
    'competitive': frozenset(['가격_인하', '마케팅_강화', '공격적']),
    'strategic': frozenset(['품질_개선', '차별화', '브랜딩']),
    'avoidance': frozenset(['다른지역', '틈새', '회피']),
    'defensive': frozenset(['절약', '비용절감', '효율화']),
    'aggressive': frozenset(['확장', '투자', '공격']),
    'inefficient': frozenset(['과도한', '무리한', '성급한'])
}


class AIService:
    """메모리 최적화된 AI 분석 및 의사결정 서비스"""
    
    # 클래스 레벨 상수로 메모리 절약
    ANALYSIS_WEIGHTS = {
        'pattern_analysis': 0.20,
        'resource_allocation': 0.18,
        'timing_analysis': 0.15,
        'situational_response': 0.15,
        'competitive_reaction': 0.12,
        'learning_ability': 0.10,
        'pressure_response': 0.10
    }
    
    # 분석 임계값 상수
    HIGH_INVESTMENT_THRESHOLD = 100000
    MAJOR_INVESTMENT_THRESHOLD = 200000
    CONFIDENCE_BASE_ACTIONS = 20
    CONFIDENCE_BASE_INVESTMENT = 1000000
    
    def __init__(self, repository: RepositoryPort):
        self.repository = repository
        # 임시 캐시를 최소화하여 메모리 절약
        self._temp_cache: Dict[str, Any] = {}
    
    def analyze_player_comprehensive(self, player_id: UUID, recent_turns: int = 10) -> Dict[str, Any]:
        """플레이어에 대한 종합 분석 수행 (메모리 최적화)"""
        
        # 기존 분석 결과 로드 (필요한 경우에만)
        existing_analysis = self.repository.load_player_analysis(player_id)
        
        # 최근 턴 히스토리 수집 (제한된 수량만)
        turn_history = self.repository.load_turn_analysis_history(player_id, min(recent_turns, 15))
        
        if not turn_history:
            return self._create_default_analysis()
        
        # 히스토리 전처리 (한 번만 수행하여 중복 계산 방지)
        processed_data = self._preprocess_turn_history(turn_history)
        
        # 7가지 분석 방법을 메모리 효율적으로 실행
        analysis_results = self._execute_all_analyses(processed_data, existing_analysis)
        
        # 종합 분석 결과 생성 (최소한의 데이터만 포함)
        comprehensive_analysis = self._integrate_analysis_results_optimized(analysis_results)
        
        # 분석 결과 저장
        self.repository.save_player_analysis(player_id, comprehensive_analysis)
        
        # 임시 캐시 정리
        self._temp_cache.clear()
        
        return comprehensive_analysis
    
    def _preprocess_turn_history(self, turn_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """턴 히스토리를 한 번만 전처리하여 메모리 효율성 향상"""
        
        # 필요한 데이터만 추출하여 메모리 사용량 최소화
        all_actions = []
        money_spent_list = []
        timing_data = []
        
        for turn_data in turn_history:
            player_data = turn_data.get('player_data', {})
            actions = player_data.get('actions_taken', [])
            money_spent = player_data.get('money_spent', 0)
            
            all_actions.extend(actions)
            money_spent_list.append(money_spent)
            timing_data.append({
                'actions_count': len(actions),
                'action_variety': len(set(actions)),
                'money_spent': money_spent,
                'timing_score': player_data.get('timing_score', 5.0)
            })
        
        # 한 번에 계산하여 중복 연산 방지
        action_counter = Counter(all_actions)
        total_actions = len(all_actions)
        total_investment = sum(money_spent_list)
        
        return {
            'action_counter': action_counter,
            'total_actions': total_actions,
            'total_investment': total_investment,
            'money_spent_list': money_spent_list,
            'timing_data': timing_data,
            'turn_count': len(turn_history)
        }
    
    def _execute_all_analyses(self, processed_data: Dict[str, Any], 
                            existing_analysis: Optional[Dict[str, Any]]) -> Dict[str, AnalysisResult]:
        """모든 분석을 메모리 효율적으로 실행"""
        
        results = {}
        
        # 각 분석 메서드를 최적화된 버전으로 실행
        results['pattern_analysis'] = self._analyze_action_patterns_optimized(processed_data)
        results['resource_allocation'] = self._analyze_resource_allocation_optimized(processed_data)
        results['timing_analysis'] = self._analyze_timing_patterns_optimized(processed_data)
        results['situational_response'] = self._analyze_situational_response_optimized(processed_data)
        results['competitive_reaction'] = self._analyze_competitive_reaction_optimized(processed_data)
        results['learning_ability'] = self._analyze_learning_ability_optimized(processed_data, existing_analysis)
        results['pressure_response'] = self._analyze_pressure_response_optimized(processed_data)
        
        return results
    
    def _analyze_action_patterns_optimized(self, processed_data: Dict[str, Any]) -> AnalysisResult:
        """메모리 최적화된 패턴 분석"""
        action_counter = processed_data['action_counter']
        total_actions = processed_data['total_actions']
        
        if total_actions == 0:
            return AnalysisResult(0.0, '행동_없음')
        
        # 효율적인 패턴 계산 (집합 연산 사용)
        pattern_scores = {}
        for pattern_name, keywords in PATTERN_KEYWORDS.items():
            if pattern_name in ['price', 'quality', 'expansion']:
                score = sum(action_counter.get(action, 0) for action in keywords) / total_actions
                pattern_scores[pattern_name] = score
        
        # 주요 패턴 결정
        max_pattern = max(pattern_scores.items(), key=lambda x: x[1])
        
        if max_pattern[1] > 0.6:
            if max_pattern[0] == 'price':
                tendency = '가격_민감형'
            elif max_pattern[0] == 'quality':
                tendency = '품질_추구형'
            else:
                tendency = '확장_공격형'
        else:
            tendency = '균형_추구형'
        
        confidence = min(1.0, total_actions / self.CONFIDENCE_BASE_ACTIONS)
        
        return AnalysisResult(
            confidence=confidence,
            primary_trait=tendency,
            secondary_data={
                'dominant_pattern_score': max_pattern[1],
                'pattern_diversity': len([s for s in pattern_scores.values() if s > 0.1])
            }
        )
    
    def _analyze_resource_allocation_optimized(self, processed_data: Dict[str, Any]) -> AnalysisResult:
        """메모리 최적화된 자원 배분 분석"""
        total_investment = processed_data['total_investment']
        action_counter = processed_data['action_counter']
        
        if total_investment == 0:
            return AnalysisResult(0.0, '투자_없음')
        
        # 투자 분야 추정 (간소화된 로직)
        investment_ratios = defaultdict(float)
        
        for action, count in action_counter.items():
            weight = count / processed_data['total_actions']
            
            if any(keyword in action for keyword in PATTERN_KEYWORDS['quality']):
                investment_ratios['quality'] += weight * 0.3
            elif any(keyword in action for keyword in PATTERN_KEYWORDS['marketing']):
                investment_ratios['marketing'] += weight * 0.4
            elif any(keyword in action for keyword in PATTERN_KEYWORDS['expansion']):
                investment_ratios['expansion'] += weight * 0.5
        
        # 주요 투자 분야 결정
        if not investment_ratios:
            player_type = '균형_투자형'
        else:
            max_investment = max(investment_ratios.items(), key=lambda x: x[1])
            if max_investment[0] == 'quality':
                player_type = '프리미엄_전략가'
            elif max_investment[0] == 'marketing':
                player_type = '브랜딩_중시'
            else:
                player_type = '규모_확대형'
        
        confidence = min(1.0, total_investment / self.CONFIDENCE_BASE_INVESTMENT)
        
        return AnalysisResult(
            confidence=confidence,
            primary_trait=player_type,
            secondary_data={
                'max_investment_ratio': max(investment_ratios.values()) if investment_ratios else 0.0
            }
        )
    
    def _analyze_timing_patterns_optimized(self, processed_data: Dict[str, Any]) -> AnalysisResult:
        """메모리 최적화된 타이밍 분석"""
        timing_data = processed_data['timing_data']
        
        if len(timing_data) < 2:
            return AnalysisResult(0.0, '분석_불가')
        
        # 반응 속도 계산 (벡터화된 연산)
        reaction_speeds = [min(10, data['actions_count'] * 2) for data in timing_data if data['actions_count'] > 0]
        
        if not reaction_speeds:
            return AnalysisResult(0.0, '반응_없음')
        
        avg_reaction = statistics.mean(reaction_speeds)
        
        # 특성 분류
        if avg_reaction >= 8:
            characteristic = '즉석_대응형'
        elif avg_reaction <= 3:
            characteristic = '장기_계획형'
        else:
            characteristic = '신중한_대응형'
        
        confidence = min(1.0, len(reaction_speeds) / 5)
        
        return AnalysisResult(
            confidence=confidence,
            primary_trait=characteristic,
            secondary_data={'avg_reaction_speed': avg_reaction}
        )
    
    def _analyze_situational_response_optimized(self, processed_data: Dict[str, Any]) -> AnalysisResult:
        """메모리 최적화된 상황별 대응 분석"""
        money_spent_list = processed_data['money_spent_list']
        action_counter = processed_data['action_counter']
        
        # 위기/기회 상황 분석 (임계값 기반)
        high_spending_turns = sum(1 for amount in money_spent_list if amount > self.HIGH_INVESTMENT_THRESHOLD)
        
        if high_spending_turns == 0:
            return AnalysisResult(0.0, '분석_불가')
        
        # 방어적 vs 공격적 행동 비율
        defensive_count = sum(action_counter.get(action, 0) for action in PATTERN_KEYWORDS['defensive'])
        aggressive_count = sum(action_counter.get(action, 0) for action in PATTERN_KEYWORDS['aggressive'])
        
        if aggressive_count > defensive_count:
            risk_preference = '하이리스크_하이리턴'
        else:
            risk_preference = '안정_추구형'
        
        confidence = min(1.0, high_spending_turns / 5)
        
        return AnalysisResult(
            confidence=confidence,
            primary_trait=risk_preference,
            secondary_data={'risk_ratio': aggressive_count / (aggressive_count + defensive_count + 1)}
        )
    
    def _analyze_competitive_reaction_optimized(self, processed_data: Dict[str, Any]) -> AnalysisResult:
        """메모리 최적화된 경쟁 반응 분석"""
        action_counter = processed_data['action_counter']
        
        # 경쟁 스타일별 점수 계산
        style_scores = {
            'competitive': sum(action_counter.get(action, 0) for action in PATTERN_KEYWORDS['competitive']),
            'strategic': sum(action_counter.get(action, 0) for action in PATTERN_KEYWORDS['strategic']),
            'avoidance': sum(action_counter.get(action, 0) for action in PATTERN_KEYWORDS['avoidance'])
        }
        
        total_reactions = sum(style_scores.values())
        
        if total_reactions == 0:
            return AnalysisResult(0.0, '무반응형')
        
        # 주요 스타일 결정
        max_style = max(style_scores.items(), key=lambda x: x[1])
        
        style_mapping = {
            'competitive': '정면승부형',
            'strategic': '차별화형',
            'avoidance': '회피형'
        }
        
        competitive_style = style_mapping[max_style[0]]
        confidence = min(1.0, total_reactions / 10)
        
        return AnalysisResult(
            confidence=confidence,
            primary_trait=competitive_style,
            secondary_data={'dominance_ratio': max_style[1] / total_reactions}
        )
    
    def _analyze_learning_ability_optimized(self, processed_data: Dict[str, Any], 
                                          existing_analysis: Optional[Dict[str, Any]]) -> AnalysisResult:
        """메모리 최적화된 학습 능력 분석"""
        timing_data = processed_data['timing_data']
        
        if len(timing_data) < 3:
            return AnalysisResult(0.0, '분석_불가', {'learning_score': 50})
        
        # 성과 개선 추세 (간소화된 계산)
        performance_scores = [data['timing_score'] for data in timing_data]
        improvement_trend = sum(1 if performance_scores[i] > performance_scores[i-1] else -1 
                              for i in range(1, len(performance_scores)))
        
        # 실수 반복 패턴
        inefficient_actions = sum(processed_data['action_counter'].get(action, 0) 
                                for action in PATTERN_KEYWORDS['inefficient'])
        
        # 학습 점수 계산
        base_score = 50
        base_score += max(-20, min(20, improvement_trend * 5))
        base_score -= min(30, inefficient_actions * 5)
        
        learning_score = max(0, min(100, base_score))
        
        return AnalysisResult(
            confidence=min(1.0, len(timing_data) / 5),
            primary_trait=f'학습능력_{learning_score}점',
            secondary_data={'learning_score': learning_score}
        )
    
    def _analyze_pressure_response_optimized(self, processed_data: Dict[str, Any]) -> AnalysisResult:
        """메모리 최적화된 압박 반응 분석"""
        money_spent_list = processed_data['money_spent_list']
        action_counter = processed_data['action_counter']
        
        # 고압 상황 탐지 (연속된 고지출)
        pressure_situations = 0
        for i in range(1, len(money_spent_list)):
            if (money_spent_list[i] > self.HIGH_INVESTMENT_THRESHOLD and 
                money_spent_list[i-1] > self.HIGH_INVESTMENT_THRESHOLD):
                pressure_situations += 1
        
        if pressure_situations == 0:
            return AnalysisResult(0.0, '압박상황_없음')
        
        # 감정적 vs 이성적 대응 분석
        hasty_actions = sum(action_counter.get(action, 0) for action in PATTERN_KEYWORDS['inefficient'])
        total_actions = processed_data['total_actions']
        
        if hasty_actions / total_actions > 0.3:
            response_type = '감정적_대응형'
        else:
            response_type = '이성적_대응형'
        
        confidence = min(1.0, pressure_situations / 3)
        
        return AnalysisResult(
            confidence=confidence,
            primary_trait=response_type,
            secondary_data={'hasty_action_ratio': hasty_actions / total_actions}
        )
    
    def _integrate_analysis_results_optimized(self, analysis_results: Dict[str, AnalysisResult]) -> Dict[str, Any]:
        """메모리 최적화된 분석 결과 통합"""
        
        # 가중 신뢰도 계산
        weighted_confidence = sum(
            result.confidence * self.ANALYSIS_WEIGHTS[key] 
            for key, result in analysis_results.items()
        )
        
        # 주요 특성 추출 (가장 신뢰도 높은 것만)
        best_analyses = sorted(
            analysis_results.items(), 
            key=lambda x: x[1].confidence, 
            reverse=True
        )[:3]  # 상위 3개만 사용
        
        # 최소한의 정보만 포함하여 메모리 절약
        return {
            'analysis_timestamp': datetime.now().isoformat(),
            'overall_confidence': weighted_confidence,
            'primary_player_type': best_analyses[0][1].primary_trait,
            'secondary_traits': [result.primary_trait for _, result in best_analyses[1:3]],
            'confidence_scores': {key: result.confidence for key, result in best_analyses},
            'ai_strategy_recommendation': self._determine_ai_strategy_optimized(best_analyses)
        }
    
    def _determine_ai_strategy_optimized(self, best_analyses: List[Tuple[str, AnalysisResult]]) -> str:
        """메모리 최적화된 AI 전략 결정"""
        
        primary_trait = best_analyses[0][1].primary_trait
        
        # 간소화된 전략 매핑
        strategy_map = {
            '가격_민감형': '가성비_공략',
            '품질_추구형': '차별화_전략',
            '확장_공격형': '틈새시장_공략',
            '프리미엄_전략가': '대중화_전략',
            '정면승부형': '측면공격_전략',
            '하이리스크_하이리턴': '안정화_전략'
        }
        
        return strategy_map.get(primary_trait, '균형_전략')
    
    def _create_default_analysis(self) -> Dict[str, Any]:
        """기본 분석 결과 (메모리 최적화)"""
        return {
            'analysis_timestamp': datetime.now().isoformat(),
            'overall_confidence': 0.0,
            'primary_player_type': '신규_플레이어',
            'secondary_traits': [],
            'confidence_scores': {},
            'ai_strategy_recommendation': '관찰_전략'
        }
    
    def get_ai_decision_based_on_analysis(self, competitor: Competitor, 
                                        player_id: UUID) -> Optional[AIDecision]:
        """분석 기반 AI 의사결정 (메모리 최적화)"""
        
        # 캐시된 분석 결과 사용
        if player_id not in self._temp_cache:
            analysis = self.repository.load_player_analysis(player_id)
            if not analysis:
                return self._make_default_ai_decision(competitor)
            self._temp_cache[player_id] = analysis
        else:
            analysis = self._temp_cache[player_id]
        
        strategy = analysis.get('ai_strategy_recommendation', '균형_전략')
        
        # 전략별 의사결정 (간소화)
        decision_map = {
            '가성비_공략': self._create_cost_effective_decision,
            '틈새시장_공략': self._create_flanking_decision,
            '측면공격_전략': self._create_pressure_decision
        }
        
        decision_func = decision_map.get(strategy, self._make_default_ai_decision)
        return decision_func(competitor)
    
    def _create_cost_effective_decision(self, competitor: Competitor) -> AIDecision:
        """가성비 중심 결정"""
        return AIDecision(
            action_type=ActionType.COOK,
            target_amount=50000,
            reasoning="가성비_공략_전략"
        )
    
    def _create_flanking_decision(self, competitor: Competitor) -> AIDecision:
        """측면 공격 결정"""
        return AIDecision(
            action_type=ActionType.ADVERTISE,
            target_amount=30000,
            reasoning="틈새시장_공략_전략"
        )
    
    def _create_pressure_decision(self, competitor: Competitor) -> AIDecision:
        """압박 전략 결정"""
        return AIDecision(
            action_type=ActionType.RESEARCH,
            target_amount=80000,
            reasoning="압박_전략"
        )
    
    def _make_default_ai_decision(self, competitor: Competitor) -> AIDecision:
        """기본 AI 결정"""
        return AIDecision(
            action_type=ActionType.OPERATE,
            target_amount=40000,
            reasoning="기본_전략"
        )
    
    def clear_cache(self):
        """메모리 정리를 위한 캐시 클리어"""
        self._temp_cache.clear() 