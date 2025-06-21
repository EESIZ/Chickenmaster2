"""
CSV 이벤트 로더 구현체

EventLoaderPort 인터페이스를 구현하여 CSV 파일에서 이벤트 데이터를 로드합니다.
"""

import csv
import os
from typing import List, Dict
from pathlib import Path

from core.domain.event_loader import EventLoaderPort
from core.domain.event import EventTemplate


class CSVEventLoader(EventLoaderPort):
    """CSV 파일에서 이벤트를 로드하는 구현체"""
    
    def __init__(self):
        """CSV 이벤트 로더 초기화"""
        self._event_cache: Dict[str, EventTemplate] = {}
        self._csv_loaded = False
    
    def load_event_templates(self, csv_file_path: str) -> List[EventTemplate]:
        """CSV 파일에서 이벤트 템플릿들을 로드합니다."""
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_file_path}")
        
        # 파일 형식 검증
        if not self.validate_csv_format(csv_file_path):
            raise ValueError(f"CSV 파일 형식이 올바르지 않습니다: {csv_file_path}")
        
        event_templates = []
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, start=2):  # 헤더 다음부터 2행
                    try:
                        template = self._parse_csv_row(row, row_num)
                        event_templates.append(template)
                        
                        # 캐시에 저장
                        self._event_cache[template.csv_id] = template
                        
                    except Exception as e:
                        raise ValueError(f"CSV {row_num}행 파싱 오류: {e}")
                        
        except UnicodeDecodeError:
            raise ValueError(f"CSV 파일 인코딩 오류. UTF-8로 저장되어 있는지 확인하세요: {csv_file_path}")
        except Exception as e:
            raise ValueError(f"CSV 파일 읽기 오류: {e}")
        
        self._csv_loaded = True
        return event_templates
    
    def get_event_template_by_id(self, csv_id: str) -> EventTemplate:
        """CSV ID로 특정 이벤트 템플릿을 조회합니다."""
        if not self._csv_loaded:
            raise ValueError("먼저 load_event_templates()를 호출하여 CSV를 로드해야 합니다")
        
        if csv_id not in self._event_cache:
            raise ValueError(f"해당 ID의 이벤트를 찾을 수 없습니다: {csv_id}")
        
        return self._event_cache[csv_id]
    
    def validate_csv_format(self, csv_file_path: str) -> bool:
        """CSV 파일 형식이 올바른지 검증합니다."""
        required_columns = {
            'id', 'name', 'description', 'event_type', 
            'probability_weight', 'auto_effects', 'choices'
        }
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # 헤더 검증
                if not required_columns.issubset(set(reader.fieldnames)):
                    missing = required_columns - set(reader.fieldnames)
                    print(f"누락된 컬럼: {missing}")
                    return False
                
                # 최소 1개 행 존재하는지 확인
                try:
                    first_row = next(reader)
                    if not first_row:
                        print("CSV에 데이터 행이 없습니다")
                        return False
                except StopIteration:
                    print("CSV에 데이터 행이 없습니다")
                    return False
                
                return True
                
        except Exception as e:
            print(f"CSV 형식 검증 오류: {e}")
            return False
    
    def _parse_csv_row(self, row: Dict[str, str], row_num: int) -> EventTemplate:
        """CSV 행을 EventTemplate 객체로 변환"""
        try:
            # 필수 필드 검증
            required_fields = ['id', 'name', 'description', 'event_type', 'probability_weight']
            for field in required_fields:
                if not row.get(field, '').strip():
                    raise ValueError(f"필수 필드 '{field}'가 비어있습니다")
            
            # 확률 가중치 검증
            try:
                probability_weight = float(row['probability_weight'])
                if probability_weight < 0:
                    raise ValueError(f"확률 가중치는 0 이상이어야 합니다: {probability_weight}")
            except ValueError as e:
                raise ValueError(f"확률 가중치 변환 오류: {e}")
            
            # EventTemplate.from_csv_row를 직접 사용
            # (JSON 파싱은 해당 메서드에서 처리)
            return EventTemplate.from_csv_row(row)
            
        except Exception as e:
            raise ValueError(f"행 파싱 오류: {e}")
    

    def get_loaded_event_count(self) -> int:
        """로드된 이벤트 개수를 반환"""
        return len(self._event_cache)
    
    def clear_cache(self):
        """캐시를 초기화"""
        self._event_cache.clear()
        self._csv_loaded = False
    
    def get_all_event_ids(self) -> List[str]:
        """로드된 모든 이벤트 ID 목록을 반환"""
        return list(self._event_cache.keys()) 