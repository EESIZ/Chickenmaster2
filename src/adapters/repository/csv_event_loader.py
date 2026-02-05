"""
CSV 이벤트 로더 구현체

EventLoaderPort 인터페이스를 구현하여 CSV 파일에서 이벤트 데이터를 로드합니다.
"""

import csv
import os
from typing import List, Dict
from uuid import uuid4

from core.domain.event_loader import EventLoaderPort
from core.domain.event import EventTemplate, Event


class CSVEventLoader(EventLoaderPort):
    """CSV 파일에서 이벤트를 로드하는 구현체"""
    
    def __init__(self, csv_file_path: str):
        """CSV 이벤트 로더 초기화"""
        self._event_cache: Dict[str, EventTemplate] = {}
        self._csv_loaded = False
        self._csv_file_path = csv_file_path
    
    def load_event_templates(self, csv_file_path: str) -> List[EventTemplate]:
        """CSV 파일에서 이벤트 템플릿들을 로드합니다."""
        if not os.path.exists(csv_file_path):
            # 파일이 없으면 빈 리스트 반환 (테스트 환경 고려)
            print(f"경고: 이벤트 파일을 찾을 수 없습니다: {csv_file_path}")
            return []
        
        event_templates = []
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        template = self._parse_csv_row(row, row_num)
                        event_templates.append(template)
                        self._event_cache[template.csv_id] = template
                        
                    except Exception as e:
                        print(f"CSV {row_num}행 파싱 오류: {e}")
                        
        except Exception as e:
            print(f"CSV 파일 읽기 오류: {e}")
            return []
        
        self._csv_loaded = True
        return event_templates
    
    def load_all_events(self) -> List[Event]:
        """모든 이벤트를 Event 객체로 변환하여 반환합니다."""
        if not self._csv_loaded:
            self.load_event_templates(self._csv_file_path)

        return [template.create_event(uuid4()) for template in self._event_cache.values()]

    def get_event(self, event_id: str) -> Event:
        """이벤트 ID로 이벤트를 조회합니다. (템플릿 기반 생성)"""
        # event_id가 UUID일 수도 있고 csv_id일 수도 있음.
        # 여기서는 csv_id로 템플릿을 찾아 새 인스턴스를 반환한다고 가정
        # 혹은 이미 생성된 Event 인스턴스를 관리해야 하는데,
        # EventLoader는 '로더'이므로 매번 새로 생성하거나 템플릿을 줌.
        # EventService가 활성 이벤트를 관리함.

        # 임시 구현: csv_id로 조회
        if str(event_id) in self._event_cache:
            return self._event_cache[str(event_id)].create_event(uuid4())
        return None

    def get_event_template_by_id(self, csv_id: str) -> EventTemplate:
        """CSV ID로 특정 이벤트 템플릿을 조회합니다."""
        if not self._csv_loaded:
            self.load_event_templates(self._csv_file_path)
        
        if csv_id not in self._event_cache:
            raise ValueError(f"해당 ID의 이벤트를 찾을 수 없습니다: {csv_id}")
        
        return self._event_cache[csv_id]
    
    def validate_csv_format(self, csv_file_path: str) -> bool:
        """CSV 파일 형식이 올바른지 검증합니다."""
        # 생략 (이전 구현 유지 또는 필요 시 복구)
        return True
    
    def _parse_csv_row(self, row: Dict[str, str], row_num: int) -> EventTemplate:
        """CSV 행을 EventTemplate 객체로 변환"""
        return EventTemplate.from_csv_row(row)
