#!/usr/bin/env python3
"""
Repository 포트와 JSON 구현체 테스트 스크립트
"""

import sys
sys.path.append('src')

def test_repository():
    try:
        # Import 테스트
        from core.ports.repository_port import RepositoryPort
        print('✅ RepositoryPort import 성공')
        
        from adapters.repository.json_repository import JsonRepository
        print('✅ JsonRepository import 성공')
        
        from core.domain.player import Player
        print('✅ Player import 성공')
        
        # 플레이어 생성 테스트
        player = Player.create_new('테스트 플레이어', 'chef')
        print(f'✅ Player 생성 성공: {player.name}')
        print(f'   - ID: {player.id}')
        print(f'   - 요리 스탯: {player.cooking.base_value}')
        print(f'   - 자금: {player.money.format_korean()}')
        
        # JsonRepository 테스트
        repo = JsonRepository('test_data')
        print('✅ JsonRepository 인스턴스 생성 성공')
        
        # 간단한 저장/로드 테스트
        success = repo.save_player(player)
        print(f'✅ Player 저장 성공: {success}')
        
        loaded_player = repo.load_player(player.id)
        if loaded_player:
            print(f'✅ Player 로드 성공: {loaded_player.name}')
        else:
            print('❌ Player 로드 실패')
        
        # 게임 데이터 저장 테스트
        game_data = {
            'player': player,
            'current_turn': 1,
            'game_start_date': '2024-01-01'
        }
        
        save_success = repo.save_game('test_save', game_data)
        print(f'✅ 게임 저장 성공: {save_success}')
        
        # 저장된 게임 목록 확인
        saved_games = repo.list_saved_games()
        print(f'✅ 저장된 게임 목록: {saved_games}')
        
        print('\n🎯 모든 기본 테스트 통과!')
        return True
        
    except Exception as e:
        print(f'❌ 테스트 실패: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_repository() 