#!/usr/bin/env python3
"""
GameLoopService 테스트 스크립트
"""

import sys
sys.path.append('src')

from datetime import date

def test_game_loop_service():
    try:
        # Import 테스트
        from application.game_loop_service import GameLoopService
        print('✅ GameLoopService import 성공')
        
        from adapters.repository.json_repository import JsonRepository
        print('✅ JsonRepository import 성공')
        
        from core.domain.player import Player
        print('✅ Player import 성공')
        
        # Repository 및 Service 생성
        repository = JsonRepository('test_data')
        game_loop_service = GameLoopService(repository)
        print('✅ GameLoopService 인스턴스 생성 성공')
        
        # 테스트 플레이어 생성
        player = Player.create_new('테스트 플레이어', 'chef')
        print(f'✅ Player 생성 성공: {player.name}')
        
        # 새 게임 시작 테스트
        start_date = date(2024, 1, 1)
        first_turn = game_loop_service.start_new_game(player, start_date)
        print(f'✅ 새 게임 시작 성공')
        print(f'   - 턴 번호: {first_turn.turn_number}')
        print(f'   - 게임 날짜: {first_turn.game_date}')
        print(f'   - 현재 페이즈: {first_turn.get_phase_name()}')
        
        # 게임 상태 확인
        status = game_loop_service.get_game_status()
        print(f'✅ 게임 상태 조회 성공')
        print(f'   - 실행 중: {status["is_running"]}')
        print(f'   - 현재 턴: {status["current_turn"]}')
        print(f'   - 현재 페이즈: {status["current_phase"]}')
        
        # 페이즈 실행 테스트
        phase_result = game_loop_service.execute_turn_phase()
        print(f'✅ 페이즈 실행 성공: {phase_result["success"]}')
        
        # 페이즈 진행 테스트
        next_turn = game_loop_service.advance_phase()
        print(f'✅ 페이즈 진행 성공')
        print(f'   - 새 페이즈: {next_turn.get_phase_name()}')
        
        # 여러 페이즈 진행 테스트
        print('\n🔄 전체 턴 진행 테스트:')
        for i in range(5):  # 5개 페이즈 더 진행
            current_turn = game_loop_service.get_current_turn()
            if current_turn and not current_turn.is_complete:
                current_phase = game_loop_service.get_current_phase()
                print(f'   단계 {i+1}: {current_phase.name}')
                game_loop_service.execute_turn_phase()
                next_turn = game_loop_service.advance_phase()
                if next_turn and next_turn.turn_number > current_turn.turn_number:
                    print(f'   → 턴 {next_turn.turn_number} 시작!')
                    break  # 다음 턴으로 넘어갔으므로 테스트 종료
            else:
                break
        
        # 최종 상태 확인
        final_status = game_loop_service.get_game_status()
        print(f'\n📊 최종 게임 상태:')
        print(f'   - 현재 턴: {final_status["current_turn"]}')
        print(f'   - 진행률: {final_status["progress"]:.1f}%')
        
        # 게임 중지
        game_loop_service.stop_game()
        print(f'✅ 게임 중지 성공')
        
        print('\n🎯 모든 GameLoopService 테스트 통과!')
        return True
        
    except Exception as e:
        print(f'❌ 테스트 실패: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_game_loop_service() 