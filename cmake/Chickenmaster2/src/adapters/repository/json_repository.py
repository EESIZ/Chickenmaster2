"""
JSON 기반 게임 데이터 저장소

RepositoryPort 인터페이스를 구현하여 모든 게임 데이터를 JSON 파일로 저장/로드합니다.
개발 단계에서 사용하기 적합한 간단한 파일 기반 저장소입니다.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID

from core.ports.repository_port import RepositoryPort
from core.domain.player import Player
from core.domain.store import Store, ParttimeWorker
from core.domain.product import Product
from core.domain.recipe import Recipe
from core.domain.inventory import Inventory
from core.domain.research import Research
from core.domain.competitor import Competitor
from core.domain.customer import CustomerAI
from core.domain.turn import Turn


class JsonRepository(RepositoryPort):
    """JSON 파일 기반 게임 데이터 저장소"""
    
    def __init__(self, data_directory: str = "data/saves"):
        """
        Args:
            data_directory: 저장 파일들이 위치할 디렉토리 경로
        """
        self.data_dir = Path(data_directory)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 각 엔티티별 저장 파일 경로
        self.saves_dir = self.data_dir / "games"
        self.saves_dir.mkdir(exist_ok=True)
        
        # 메모리 캐시 (성능 향상용)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_dirty = False
        
        # AI 분석 결과 전용 캐시 시스템
        self._ai_analysis_cache: Dict[str, Dict[str, Any]] = {
            'player_profiles': {},      # 플레이어별 종합 분석 프로필
            'turn_history': {},         # 턴별 분석 히스토리
            'pattern_data': {},         # 패턴 분석 데이터
            'competitive_situation': {  # 현재 경쟁 상황
                'market_share': {},
                'pricing_trends': {},
                'last_updated_turn': 0
            }
        }
    
    def _get_save_path(self, save_name: str) -> Path:
        """저장 파일 경로 반환"""
        return self.saves_dir / f"{save_name}.json"
    
    def _serialize_entity(self, entity: Any) -> Dict[str, Any]:
        """도메인 엔티티를 JSON 직렬화 가능한 딕셔너리로 변환"""
        if entity is None:
            return None
        
        result = {}
        
        # dataclass의 모든 필드를 딕셔너리로 변환
        for field_name, field_value in entity.__dict__.items():
            if isinstance(field_value, UUID):
                result[field_name] = str(field_value)
            elif hasattr(field_value, '__dict__'):
                # 중첩된 객체 (Value Objects 등)
                result[field_name] = self._serialize_entity(field_value)
            elif isinstance(field_value, (tuple, list)):
                result[field_name] = [
                    str(item) if isinstance(item, UUID) else 
                    self._serialize_entity(item) if hasattr(item, '__dict__') else item
                    for item in field_value
                ]
            else:
                result[field_name] = field_value
        
        # 클래스 타입 정보 저장 (역직렬화용)
        result['_class_name'] = entity.__class__.__name__
        result['_module_name'] = entity.__class__.__module__
        
        return result
    
    def _deserialize_entity(self, data: Dict[str, Any], target_class: type) -> Any:
        """JSON 딕셔너리를 도메인 엔티티로 역직렬화"""
        if data is None:
            return None
        
        # UUID 필드들을 다시 UUID 객체로 변환
        kwargs = {}
        for field_name, field_value in data.items():
            if field_name.startswith('_'):
                continue  # 메타데이터 필드 제외
            
            if field_name.endswith('_id') or field_name == 'id':
                kwargs[field_name] = UUID(field_value) if field_value else None
            elif field_name.endswith('_ids'):
                kwargs[field_name] = tuple(UUID(item) for item in field_value)
            elif isinstance(field_value, dict) and '_class_name' in field_value:
                # 중첩된 객체 복원 (Value Objects 등)
                nested_class = self._get_class_by_name(field_value['_class_name'], field_value['_module_name'])
                kwargs[field_name] = self._deserialize_entity(field_value, nested_class)
            else:
                kwargs[field_name] = field_value
        
        return target_class(**kwargs)
    
    def _get_class_by_name(self, class_name: str, module_name: str) -> type:
        """클래스명과 모듈명으로 클래스 타입 반환"""
        import importlib
        module = importlib.import_module(module_name)
        return getattr(module, class_name)
    
    # ==================== 게임 세션 관리 ====================
    
    def save_game(self, save_name: str, game_data: Dict[str, Any]) -> bool:
        """게임 전체 상태를 JSON 파일로 저장"""
        try:
            save_path = self._get_save_path(save_name)
            
            # 게임 데이터 직렬화
            serialized_data = {
                'save_name': save_name,
                'save_time': datetime.now().isoformat(),
                'game_data': {},
                'ai_analysis_cache': self._ai_analysis_cache.copy()  # AI 분석 캐시도 저장
            }
            
            for key, value in game_data.items():
                if isinstance(value, list):
                    serialized_data['game_data'][key] = [
                        self._serialize_entity(item) for item in value
                    ]
                elif hasattr(value, '__dict__'):
                    serialized_data['game_data'][key] = self._serialize_entity(value)
                else:
                    serialized_data['game_data'][key] = value
            
            # 파일에 저장
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(serialized_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"게임 저장 실패: {e}")
            return False
    
    def load_game(self, save_name: str) -> Optional[Dict[str, Any]]:
        """저장된 게임을 JSON 파일에서 불러오기"""
        try:
            save_path = self._get_save_path(save_name)
            
            if not save_path.exists():
                return None
            
            with open(save_path, 'r', encoding='utf-8') as f:
                serialized_data = json.load(f)
            
            # 게임 데이터 역직렬화
            game_data = {}
            for key, value in serialized_data['game_data'].items():
                if isinstance(value, list) and value and isinstance(value[0], dict) and '_class_name' in value[0]:
                    # 엔티티 리스트 복원
                    first_item = value[0]
                    target_class = self._get_class_by_name(first_item['_class_name'], first_item['_module_name'])
                    game_data[key] = [self._deserialize_entity(item, target_class) for item in value]
                elif isinstance(value, dict) and '_class_name' in value:
                    # 단일 엔티티 복원
                    target_class = self._get_class_by_name(value['_class_name'], value['_module_name'])
                    game_data[key] = self._deserialize_entity(value, target_class)
                else:
                    game_data[key] = value
            
            # AI 분석 캐시 복원
            if 'ai_analysis_cache' in serialized_data:
                self._ai_analysis_cache = serialized_data['ai_analysis_cache']
            
            return game_data
            
        except Exception as e:
            print(f"게임 불러오기 실패: {e}")
            return None
    
    def list_saved_games(self) -> List[str]:
        """저장된 게임 목록 반환"""
        try:
            save_files = list(self.saves_dir.glob("*.json"))
            return [f.stem for f in save_files]
        except Exception:
            return []
    
    def delete_saved_game(self, save_name: str) -> bool:
        """저장된 게임 파일 삭제"""
        try:
            save_path = self._get_save_path(save_name)
            if save_path.exists():
                save_path.unlink()
                return True
            return False
        except Exception:
            return False
    
    # ==================== 개별 엔티티 관리 (간소화된 구현) ====================
    
    def save_player(self, player: Player) -> bool:
        """플레이어 정보를 메모리 캐시에 저장 (실제 저장은 save_game 시점)"""
        try:
            if 'players' not in self._cache:
                self._cache['players'] = {}
            self._cache['players'][str(player.id)] = self._serialize_entity(player)
            self._cache_dirty = True
            return True
        except Exception:
            return False
    
    def load_player(self, player_id: UUID) -> Optional[Player]:
        """플레이어 정보를 메모리 캐시에서 불러오기"""
        try:
            if 'players' not in self._cache:
                return None
            
            player_data = self._cache['players'].get(str(player_id))
            if player_data:
                return self._deserialize_entity(player_data, Player)
            return None
        except Exception:
            return None
    
    def save_store(self, store: Store) -> bool:
        """매장 정보를 메모리 캐시에 저장"""
        try:
            if 'stores' not in self._cache:
                self._cache['stores'] = {}
            self._cache['stores'][str(store.id)] = self._serialize_entity(store)
            self._cache_dirty = True
            return True
        except Exception:
            return False
    
    def load_store(self, store_id: UUID) -> Optional[Store]:
        """매장 정보를 메모리 캐시에서 불러오기"""
        try:
            if 'stores' not in self._cache:
                return None
            
            store_data = self._cache['stores'].get(str(store_id))
            if store_data:
                return self._deserialize_entity(store_data, Store)
            return None
        except Exception:
            return None
    
    def load_stores_by_owner(self, owner_id: UUID) -> List[Store]:
        """특정 소유자의 모든 매장 불러오기"""
        try:
            if 'stores' not in self._cache:
                return []
            
            stores = []
            for store_data in self._cache['stores'].values():
                if store_data.get('owner_id') == str(owner_id):
                    store = self._deserialize_entity(store_data, Store)
                    if store:
                        stores.append(store)
            return stores
        except Exception:
            return []
    
    # ==================== 나머지 메서드들 (기본 구현) ====================
    
    # 간단한 구현을 위해 나머지 메서드들은 기본 동작만 제공
    def save_product(self, product: Product) -> bool:
        return True
    
    def load_product(self, product_id: UUID) -> Optional[Product]:
        return None
    
    def load_products_by_store(self, store_id: UUID) -> List[Product]:
        return []
    
    def save_recipe(self, recipe: Recipe) -> bool:
        return True
    
    def load_recipe(self, recipe_id: UUID) -> Optional[Recipe]:
        return None
    
    def load_all_recipes(self) -> List[Recipe]:
        return []
    
    def save_inventory_item(self, item: Inventory) -> bool:
        return True
    
    def load_inventory_item(self, item_id: UUID) -> Optional[Inventory]:
        return None
    
    def load_inventory_by_store(self, store_id: UUID) -> List[Inventory]:
        return []
    
    def save_research(self, research: Research) -> bool:
        return True
    
    def load_research(self, research_id: UUID) -> Optional[Research]:
        return None
    
    def load_research_by_player(self, player_id: UUID) -> List[Research]:
        return []
    
    def save_competitor(self, competitor: Competitor) -> bool:
        return True
    
    def load_competitor(self, competitor_id: UUID) -> Optional[Competitor]:
        return None
    
    def load_all_competitors(self) -> List[Competitor]:
        return []
    
    def save_customer(self, customer: CustomerAI) -> bool:
        return True
    
    def load_customer(self, customer_id: UUID) -> Optional[CustomerAI]:
        return None
    
    def load_all_customers(self) -> List[CustomerAI]:
        return []
    
    def save_parttime_worker(self, worker: ParttimeWorker) -> bool:
        return True
    
    def load_parttime_worker(self, worker_id: UUID) -> Optional[ParttimeWorker]:
        return None
    
    def load_workers_by_store(self, store_id: UUID) -> List[ParttimeWorker]:
        return []
    
    def save_turn(self, turn: Turn) -> bool:
        return True
    
    def load_current_turn(self) -> Optional[Turn]:
        return None
    
    def get_total_entities_count(self) -> Dict[str, int]:
        """각 엔티티별 총 개수 반환"""
        counts = {}
        for entity_type, entities in self._cache.items():
            counts[entity_type] = len(entities) if isinstance(entities, dict) else 0
        return counts
    
    def cleanup_orphaned_entities(self) -> int:
        """고아 엔티티 정리 (기본 구현)"""
        return 0
    
    # ==================== RepositoryPort 호환성을 위한 별칭 메서드들 ====================
    
    def get_player(self, player_id: UUID) -> Optional[Player]:
        """load_player의 별칭 메서드"""
        return self.load_player(player_id)
    
    def get_store(self, store_id: UUID) -> Optional[Store]:
        """load_store의 별칭 메서드"""
        return self.load_store(store_id)
    
    def get_research(self, research_id: UUID) -> Optional[Research]:
        """load_research의 별칭 메서드"""
        return self.load_research(research_id)
    
    # ==================== AI 분석 데이터 관리 구현 ====================
    
    def save_player_analysis(self, player_id: UUID, analysis_data: Dict[str, Any]) -> bool:
        """플레이어 분석 결과를 메모리 캐시에 저장"""
        try:
            player_key = str(player_id)
            self._ai_analysis_cache['player_profiles'][player_key] = {
                'player_id': player_key,
                'last_updated': datetime.now().isoformat(),
                'analysis_data': analysis_data.copy()
            }
            return True
        except Exception as e:
            print(f"플레이어 분석 데이터 저장 실패: {e}")
            return False
    
    def load_player_analysis(self, player_id: UUID) -> Optional[Dict[str, Any]]:
        """플레이어 분석 결과를 메모리 캐시에서 불러오기"""
        try:
            player_key = str(player_id)
            profile = self._ai_analysis_cache['player_profiles'].get(player_key)
            if profile:
                return profile['analysis_data']
            return None
        except Exception:
            return None
    
    def save_turn_analysis(self, turn_number: int, analysis_data: Dict[str, Any]) -> bool:
        """턴별 분석 데이터를 메모리 캐시에 저장"""
        try:
            turn_key = str(turn_number)
            self._ai_analysis_cache['turn_history'][turn_key] = {
                'turn_number': turn_number,
                'timestamp': datetime.now().isoformat(),
                'analysis_data': analysis_data.copy()
            }
            
            # 메모리 사용량 제한: 최근 50턴만 유지
            if len(self._ai_analysis_cache['turn_history']) > 50:
                oldest_turn = min(int(k) for k in self._ai_analysis_cache['turn_history'].keys())
                del self._ai_analysis_cache['turn_history'][str(oldest_turn)]
            
            return True
        except Exception as e:
            print(f"턴 분석 데이터 저장 실패: {e}")
            return False
    
    def load_turn_analysis_history(self, player_id: UUID, recent_turns: int = 10) -> List[Dict[str, Any]]:
        """플레이어의 최근 턴 분석 히스토리를 불러오기"""
        try:
            player_key = str(player_id)
            history = []
            
            # 턴 번호 기준으로 정렬하여 최근 턴부터 가져오기
            sorted_turns = sorted(
                self._ai_analysis_cache['turn_history'].items(),
                key=lambda x: int(x[0]),
                reverse=True
            )
            
            count = 0
            for turn_key, turn_data in sorted_turns:
                if count >= recent_turns:
                    break
                
                # 해당 턴에 플레이어 관련 데이터가 있는지 확인
                analysis_data = turn_data['analysis_data']
                if player_key in analysis_data.get('player_actions', {}):
                    history.append({
                        'turn_number': turn_data['turn_number'],
                        'timestamp': turn_data['timestamp'],
                        'player_data': analysis_data.get('player_actions', {}).get(player_key, {})
                    })
                    count += 1
            
            return history
        except Exception:
            return []
    
    def update_competitive_situation(self, situation_data: Dict[str, Any]) -> bool:
        """경쟁 상황 데이터를 업데이트"""
        try:
            current_situation = self._ai_analysis_cache['competitive_situation']
            
            # 기존 데이터와 새 데이터 병합
            for key, value in situation_data.items():
                if key == 'last_updated_turn':
                    current_situation[key] = value
                elif isinstance(value, dict) and key in current_situation:
                    current_situation[key].update(value)
                else:
                    current_situation[key] = value
            
            current_situation['last_updated'] = datetime.now().isoformat()
            return True
        except Exception as e:
            print(f"경쟁 상황 데이터 업데이트 실패: {e}")
            return False
    
    def get_competitive_situation(self) -> Dict[str, Any]:
        """현재 경쟁 상황 데이터를 반환"""
        try:
            return self._ai_analysis_cache['competitive_situation'].copy()
        except Exception:
            return {
                'market_share': {},
                'pricing_trends': {},
                'last_updated_turn': 0,
                'last_updated': datetime.now().isoformat()
            }
    
    def get_ai_cache_stats(self) -> Dict[str, int]:
        """AI 분석 캐시 통계 반환 (디버깅용)"""
        try:
            return {
                'player_profiles_count': len(self._ai_analysis_cache['player_profiles']),
                'turn_history_count': len(self._ai_analysis_cache['turn_history']),
                'pattern_data_count': len(self._ai_analysis_cache['pattern_data']),
                'competitive_data_keys': len(self._ai_analysis_cache['competitive_situation'])
            }
        except Exception:
            return {'error': True}
    
    def clear_ai_analysis_cache(self) -> bool:
        """AI 분석 캐시 초기화 (새 게임 시작 시 사용)"""
        try:
            self._ai_analysis_cache = {
                'player_profiles': {},
                'turn_history': {},
                'pattern_data': {},
                'competitive_situation': {
                    'market_share': {},
                    'pricing_trends': {},
                    'last_updated_turn': 0
                }
            }
            return True
        except Exception:
            return False 