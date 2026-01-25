#!/bin/bash
# Project Initialization & Template Migration Script
# 프로젝트 초기화 및 템플릿 마이그레이션 스크립트
#
# Usage:
#   ./init.sh              # 새 프로젝트 초기화
#   ./init.sh --init       # 명시적 초기화
#   ./init.sh --migrate /path/to/target  # 마이그레이션
#   ./init.sh --check      # 상태 점검
#   ./init.sh --help       # 도움말

set -e

# ============================================================================
# Color definitions for output
# ============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ============================================================================
# Utility functions
# ============================================================================

# Print colored message
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_header() {
    echo -e "\n${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${CYAN}  $1${NC}"
    echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_step() {
    echo -e "${BOLD}▶ $1${NC}"
}

# Get script directory (template root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ============================================================================
# Help message
# ============================================================================
show_help() {
    cat << EOF
${BOLD}프로젝트 초기화 및 템플릿 마이그레이션 도구${NC}

${BOLD}사용법:${NC}
    ./init.sh              새 프로젝트 초기화 (기본 모드)
    ./init.sh --init       명시적 초기화
    ./init.sh --migrate <path>  템플릿 마이그레이션
    ./init.sh --check      상태 점검
    ./init.sh --help       도움말 표시

${BOLD}모드 설명:${NC}
    ${CYAN}--init${NC}     필수 디렉토리 구조 생성, 기본 파일 생성, uv 환경 동기화
    ${CYAN}--migrate${NC}  tools/migrate_template.py를 사용한 템플릿 마이그레이션
               인터랙티브 모드: 컴포넌트 선택, dry-run 미리보기 제공
    ${CYAN}--check${NC}    필수 디렉토리/파일 존재 확인, uv/MCP/Git 상태 검증

${BOLD}예시:${NC}
    # 새 프로젝트 초기화
    ./init.sh

    # 다른 프로젝트에 템플릿 마이그레이션
    ./init.sh --migrate /path/to/other/project

    # 현재 상태 점검
    ./init.sh --check

${BOLD}마이그레이션 컴포넌트:${NC}
    instructions  - .github/copilot-instructions.md
    agents        - .github/agents/*.agent.md
    skills        - .github/skills/*/SKILL.md
    mcp           - .vscode/mcp.json
    agents_doc    - AGENTS.md
    agent_tools   - tools/agent_tools/*.py
    mcp_servers   - tools/mcp_servers/*.py

EOF
}

# ============================================================================
# Directory and file creation functions
# ============================================================================

create_directory() {
    local dir="$1"
    if [[ ! -d "$dir" ]]; then
        mkdir -p "$dir"
        print_success "디렉토리 생성: $dir"
    else
        print_info "디렉토리 존재: $dir"
    fi
}

create_file_if_not_exists() {
    local file="$1"
    local content="$2"
    
    if [[ ! -f "$file" ]]; then
        # Ensure parent directory exists
        mkdir -p "$(dirname "$file")"
        echo -e "$content" > "$file"
        print_success "파일 생성: $file"
    else
        print_info "파일 존재: $file"
    fi
}

# ============================================================================
# Init mode - Create project structure
# ============================================================================
do_init() {
    print_header "프로젝트 초기화"
    
    local project_root="${1:-$SCRIPT_DIR}"
    cd "$project_root"
    
    print_step "1. 필수 디렉토리 구조 생성"
    echo ""
    
    # Document directories
    create_directory "documents/notes"
    create_directory "documents/final"
    create_directory "documents/drafts"
    create_directory "documents/reference/papers"
    create_directory "documents/reference/technical"
    create_directory "documents/templates"
    
    # Config directories
    create_directory "configs/generated"
    create_directory "configs/evaluation"
    
    # Results and logs
    create_directory "results"
    create_directory "logs/slurm"
    create_directory "logs/tensorboard"
    
    # Temp and backup
    create_directory "temp"
    create_directory "backups"
    
    # Copilot memory
    create_directory ".copilot-memory"
    
    # GitHub structure
    create_directory ".github/agents"
    create_directory ".github/skills"
    
    # VS Code
    create_directory ".vscode"
    
    # Source code
    create_directory "src/experiments"
    create_directory "src/data"
    create_directory "src/utils"
    
    # Scripts
    create_directory "scripts/slurm/generated"
    
    # Tools
    create_directory "tools/agent_tools"
    create_directory "tools/mcp_servers"
    
    # Tests
    create_directory "tests"
    
    echo ""
    print_step "2. 기본 파일 생성"
    echo ""
    
    # PROJECT.md template
    local project_md_content="# 프로젝트 개요

## 프로젝트 이름
\`[프로젝트 이름을 입력하세요]\`

## 목표
\`[프로젝트의 주요 목표를 기술하세요]\`

## 현재 상태
- **Phase**: 초기화
- **진행률**: 0%

## 주요 마일스톤
1. [ ] 환경 설정 완료
2. [ ] 데이터 준비
3. [ ] 기본 실험 구현
4. [ ] 결과 분석

## 참고 자료
- [AGENTS.md](../AGENTS.md) - 에이전트 및 스킬 목록
- [QUICKSTART.md](QUICKSTART.md) - 빠른 시작 가이드

---
*마지막 업데이트: $(date +%Y-%m-%d)*"
    
    create_file_if_not_exists "documents/PROJECT.md" "$project_md_content"
    
    # README placeholder for generated configs
    local generated_readme="# Generated Configs

이 디렉토리에는 자동 생성된 설정 파일이 저장됩니다.

**주의**: 이 디렉토리의 파일은 실험 스크립트에 의해 덮어쓰여질 수 있습니다.
중요한 설정은 \`configs/\` 루트에 저장하세요.
"
    create_file_if_not_exists "configs/generated/README.md" "$generated_readme"
    
    # Update .gitignore
    print_step "3. .gitignore 업데이트"
    echo ""
    
    local gitignore_additions="
# ============================================================================
# Project-specific ignores (added by init.sh)
# ============================================================================

# Temporary files
temp/

# Backup files
backups/

# Agent memory files (local scratchpads)
*.memory.md
documents/**/*.memory.md

# Copilot memory database
.copilot-memory/

# Project status cache
.project_status_cache.json

# Generated SLURM scripts (optional - uncomment if needed)
# scripts/slurm/generated/
"
    
    if [[ -f ".gitignore" ]]; then
        # Check if our marker already exists
        if ! grep -q "added by init.sh" ".gitignore" 2>/dev/null; then
            echo "$gitignore_additions" >> ".gitignore"
            print_success ".gitignore 업데이트 완료"
        else
            print_info ".gitignore 이미 업데이트됨"
        fi
    else
        echo "$gitignore_additions" > ".gitignore"
        print_success ".gitignore 생성 완료"
    fi
    
    # uv sync
    echo ""
    print_step "4. uv 환경 동기화"
    echo ""
    
    if command -v uv &> /dev/null; then
        if [[ -f "pyproject.toml" ]]; then
            print_info "uv sync 실행 중..."
            if uv sync 2>&1 | head -20; then
                print_success "uv 환경 동기화 완료"
            else
                print_warning "uv sync 중 일부 경고가 발생했습니다"
            fi
        else
            print_warning "pyproject.toml이 없습니다. uv sync를 건너뜁니다."
        fi
    else
        print_warning "uv가 설치되어 있지 않습니다. 수동으로 환경을 설정하세요."
        print_info "설치: curl -LsSf https://astral.sh/uv/install.sh | sh"
    fi
    
    # Git initialization
    echo ""
    print_step "5. Git 초기화"
    echo ""
    
    if [[ ! -d ".git" ]]; then
        if command -v git &> /dev/null; then
            git init
            print_success "Git 저장소 초기화 완료"
        else
            print_warning "git이 설치되어 있지 않습니다"
        fi
    else
        print_info "Git 저장소가 이미 존재합니다"
    fi
    
    echo ""
    print_header "초기화 완료"
    print_success "프로젝트 초기화가 완료되었습니다!"
    echo ""
    print_info "다음 단계:"
    echo "  1. documents/PROJECT.md를 편집하여 프로젝트 정보를 입력하세요"
    echo "  2. ./init.sh --check로 상태를 확인하세요"
    echo ""
}

# ============================================================================
# Migrate mode - Template migration
# ============================================================================
do_migrate() {
    local target_path="$1"
    
    print_header "템플릿 마이그레이션"
    
    if [[ -z "$target_path" ]]; then
        print_error "대상 경로가 지정되지 않았습니다"
        echo ""
        echo "사용법: ./init.sh --migrate /path/to/target/project"
        exit 1
    fi
    
    # Resolve to absolute path
    if [[ ! "$target_path" = /* ]]; then
        target_path="$(cd "$target_path" 2>/dev/null && pwd)" || {
            print_error "대상 경로를 찾을 수 없습니다: $target_path"
            exit 1
        }
    fi
    
    if [[ ! -d "$target_path" ]]; then
        print_error "대상 디렉토리가 존재하지 않습니다: $target_path"
        exit 1
    fi
    
    print_info "소스 (템플릿): $SCRIPT_DIR"
    print_info "대상 (프로젝트): $target_path"
    echo ""
    
    # Interactive component selection
    print_step "마이그레이션 컴포넌트 선택"
    echo ""
    echo "사용 가능한 컴포넌트:"
    echo "  1. instructions  - .github/copilot-instructions.md"
    echo "  2. agents        - .github/agents/*.agent.md"
    echo "  3. skills        - .github/skills/*/SKILL.md"
    echo "  4. mcp           - .vscode/mcp.json"
    echo "  5. agents_doc    - AGENTS.md"
    echo "  6. agent_tools   - tools/agent_tools/*.py"
    echo "  7. mcp_servers   - tools/mcp_servers/*.py"
    echo "  8. all           - 모든 컴포넌트"
    echo ""
    
    read -p "컴포넌트 선택 (쉼표 구분, 기본값: all): " components_input
    components_input="${components_input:-all}"
    
    echo ""
    print_step "Dry-run 미리보기 실행"
    echo ""
    
    # Run dry-run first
    cd "$SCRIPT_DIR"
    
    local dry_run_output
    dry_run_output=$(uv run python -m tools.migrate_template \
        --target "$target_path" \
        --components "$components_input" \
        --dry-run 2>&1)
    
    local dry_run_status=$?
    
    echo "$dry_run_output" | python3 -c "
import sys
import json

try:
    data = json.load(sys.stdin)
    print()
    print('마이그레이션 예정 파일:')
    for f in data.get('migrated', []):
        print(f'  ✓ {f}')
    
    if data.get('conflicts'):
        print()
        print('충돌 파일 (--force 필요):')
        for f in data.get('conflicts', []):
            print(f'  ⚠ {f}')
    
    if data.get('protected'):
        print()
        print('보호된 파일 (건너뜀):')
        for f in data.get('protected', []):
            print(f'  ⊘ {f}')
    
    if data.get('skipped'):
        print()
        print('건너뛴 파일 (동일):')
        for f in data.get('skipped', []):
            print(f'  - {f}')
    
    print()
    summary = data.get('summary', {})
    print(f\"요약: 마이그레이션 {summary.get('total_migrated', 0)}개, \"
          f\"충돌 {summary.get('total_conflicts', 0)}개, \"
          f\"보호 {summary.get('total_protected', 0)}개, \"
          f\"건너뜀 {summary.get('total_skipped', 0)}개\")
except json.JSONDecodeError:
    print(sys.stdin.read())
" 2>/dev/null || echo "$dry_run_output"
    
    echo ""
    
    if [[ $dry_run_status -ne 0 ]]; then
        print_warning "Dry-run 중 경고가 발생했습니다"
    fi
    
    # Ask for confirmation
    echo ""
    read -p "마이그레이션을 진행하시겠습니까? [y/N]: " confirm
    
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        print_info "마이그레이션이 취소되었습니다"
        exit 0
    fi
    
    # Check for conflicts and ask about force
    local force_flag=""
    if echo "$dry_run_output" | grep -q '"conflicts":\s*\[' && \
       echo "$dry_run_output" | grep -q '"conflicts":\s*\[[^]]'; then
        echo ""
        read -p "충돌 파일을 강제로 덮어쓰시겠습니까? [y/N]: " force_confirm
        if [[ "$force_confirm" =~ ^[Yy]$ ]]; then
            force_flag="--force"
        fi
    fi
    
    echo ""
    print_step "마이그레이션 실행"
    echo ""
    
    # Run actual migration
    local migrate_output
    migrate_output=$(uv run python -m tools.migrate_template \
        --target "$target_path" \
        --components "$components_input" \
        $force_flag 2>&1)
    
    local migrate_status=$?
    
    # Parse and display result
    echo "$migrate_output" | python3 -c "
import sys
import json

try:
    data = json.load(sys.stdin)
    status = data.get('status', 'unknown')
    
    if status == 'success':
        print('✓ 마이그레이션 성공!')
    elif status == 'partial':
        print('⚠ 부분 마이그레이션 완료')
    else:
        print('✗ 마이그레이션 실패')
    
    print()
    
    if data.get('migrated'):
        print('마이그레이션 완료:')
        for f in data.get('migrated', []):
            print(f'  ✓ {f}')
    
    if data.get('backup_path'):
        print()
        print(f\"백업 위치: {data['backup_path']}\")
    
    summary = data.get('summary', {})
    print()
    print(f\"결과: 성공 {summary.get('total_migrated', 0)}개, \"
          f\"실패 {summary.get('total_errors', 0)}개\")

except json.JSONDecodeError:
    print(sys.stdin.read())
" 2>/dev/null || echo "$migrate_output"
    
    echo ""
    
    if [[ $migrate_status -eq 0 ]]; then
        print_success "마이그레이션이 완료되었습니다!"
        print_info "대상 프로젝트에서 ./init.sh --check를 실행하여 상태를 확인하세요"
    elif [[ $migrate_status -eq 2 ]]; then
        print_warning "일부 파일이 마이그레이션되지 않았습니다"
    else
        print_error "마이그레이션 중 오류가 발생했습니다"
        exit 1
    fi
}

# ============================================================================
# Check mode - Verify project status
# ============================================================================
do_check() {
    print_header "프로젝트 상태 점검"
    
    local project_root="${1:-$SCRIPT_DIR}"
    cd "$project_root"
    
    local total_checks=0
    local passed_checks=0
    local warnings=0
    
    # 1. Required directories
    print_step "1. 필수 디렉토리 확인"
    echo ""
    
    local required_dirs=(
        "documents/notes"
        "documents/final"
        "documents/drafts"
        "documents/reference/papers"
        "documents/reference/technical"
        "configs/generated"
        "results"
        "logs/slurm"
        "logs/tensorboard"
        ".github/agents"
        ".github/skills"
        ".vscode"
        "src"
        "tools/agent_tools"
    )
    
    for dir in "${required_dirs[@]}"; do
        ((total_checks++))
        if [[ -d "$dir" ]]; then
            print_success "$dir"
            ((passed_checks++))
        else
            print_error "$dir (없음)"
        fi
    done
    
    # 2. Required files
    echo ""
    print_step "2. 필수 파일 확인"
    echo ""
    
    local required_files=(
        "pyproject.toml"
        "AGENTS.md"
        ".github/copilot-instructions.md"
        ".gitignore"
    )
    
    for file in "${required_files[@]}"; do
        ((total_checks++))
        if [[ -f "$file" ]]; then
            print_success "$file"
            ((passed_checks++))
        else
            print_error "$file (없음)"
        fi
    done
    
    # Optional but recommended files
    local optional_files=(
        "documents/PROJECT.md"
        ".vscode/mcp.json"
        "README.md"
    )
    
    for file in "${optional_files[@]}"; do
        if [[ -f "$file" ]]; then
            print_success "$file"
        else
            print_warning "$file (권장)"
            ((warnings++))
        fi
    done
    
    # 3. uv environment
    echo ""
    print_step "3. uv 환경 상태"
    echo ""
    
    ((total_checks++))
    if command -v uv &> /dev/null; then
        print_success "uv 설치됨"
        ((passed_checks++))
        
        if [[ -f ".venv/bin/python" ]] || [[ -f ".venv/Scripts/python.exe" ]]; then
            print_success "가상환경 존재 (.venv)"
        else
            print_warning "가상환경 없음 (uv sync 필요)"
            ((warnings++))
        fi
        
        # Check if lock file exists
        if [[ -f "uv.lock" ]]; then
            print_success "잠금 파일 존재 (uv.lock)"
        else
            print_warning "잠금 파일 없음 (uv sync 필요)"
            ((warnings++))
        fi
    else
        print_error "uv 설치되지 않음"
        print_info "설치: curl -LsSf https://astral.sh/uv/install.sh | sh"
    fi
    
    # 4. MCP server configuration
    echo ""
    print_step "4. MCP 서버 설정"
    echo ""
    
    ((total_checks++))
    if [[ -f ".vscode/mcp.json" ]]; then
        print_success "mcp.json 존재"
        ((passed_checks++))
        
        # Parse and check servers
        local servers
        servers=$(python3 -c "
import json
import sys

try:
    with open('.vscode/mcp.json') as f:
        content = f.read()
        # Remove comments (simple approach for single-line comments)
        import re
        content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        data = json.loads(content)
    
    servers = data.get('servers', {})
    for name in servers:
        print(name)
except Exception as e:
    sys.exit(1)
" 2>/dev/null)
        
        if [[ -n "$servers" ]]; then
            while IFS= read -r server; do
                print_info "  서버: $server"
            done <<< "$servers"
        fi
    else
        print_warning "mcp.json 없음"
        ((warnings++))
    fi
    
    # 5. Git status
    echo ""
    print_step "5. Git 상태"
    echo ""
    
    ((total_checks++))
    if [[ -d ".git" ]]; then
        print_success "Git 저장소 초기화됨"
        ((passed_checks++))
        
        if command -v git &> /dev/null; then
            local branch
            branch=$(git branch --show-current 2>/dev/null)
            if [[ -n "$branch" ]]; then
                print_info "현재 브랜치: $branch"
            fi
            
            local uncommitted
            uncommitted=$(git status --porcelain 2>/dev/null | wc -l)
            if [[ "$uncommitted" -gt 0 ]]; then
                print_warning "커밋되지 않은 변경사항: ${uncommitted}개"
                ((warnings++))
            else
                print_success "작업 디렉토리 깨끗함"
            fi
        fi
    else
        print_warning "Git 저장소 아님"
        ((warnings++))
    fi
    
    # 6. Agent tools check
    echo ""
    print_step "6. 에이전트 도구 상태"
    echo ""
    
    local agent_tools=(
        "tools/agent_tools/get_status.py"
        "tools/agent_tools/submit_job.py"
        "tools/agent_tools/analyze_log.py"
    )
    
    local tools_ok=true
    for tool in "${agent_tools[@]}"; do
        if [[ -f "$tool" ]]; then
            print_success "$(basename "$tool")"
        else
            print_warning "$(basename "$tool") (없음)"
            tools_ok=false
        fi
    done
    
    if $tools_ok; then
        # Test get_status
        print_info "get_status 테스트 중..."
        if uv run python -m tools.agent_tools.get_status &>/dev/null; then
            print_success "get_status 실행 성공"
        else
            print_warning "get_status 실행 실패"
            ((warnings++))
        fi
    fi
    
    # Summary
    echo ""
    print_header "점검 결과 요약"
    
    echo -e "필수 항목: ${GREEN}$passed_checks${NC}/${total_checks} 통과"
    
    if [[ $warnings -gt 0 ]]; then
        echo -e "경고: ${YELLOW}$warnings${NC}개"
    fi
    
    echo ""
    
    if [[ $passed_checks -eq $total_checks ]]; then
        if [[ $warnings -eq 0 ]]; then
            print_success "모든 점검 통과! 프로젝트가 정상입니다."
        else
            print_success "필수 항목 통과. 경고 사항을 확인하세요."
        fi
    else
        local failed=$((total_checks - passed_checks))
        print_error "필수 항목 $failed개 실패. ./init.sh로 초기화하세요."
        exit 1
    fi
}

# ============================================================================
# Main entry point
# ============================================================================
main() {
    local mode="init"
    local target_path=""
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --help|-h)
                show_help
                exit 0
                ;;
            --init)
                mode="init"
                shift
                ;;
            --migrate)
                mode="migrate"
                shift
                if [[ $# -gt 0 && ! "$1" =~ ^-- ]]; then
                    target_path="$1"
                    shift
                fi
                ;;
            --check)
                mode="check"
                shift
                ;;
            *)
                # Unknown option - might be a path for migrate
                if [[ "$mode" == "migrate" && -z "$target_path" ]]; then
                    target_path="$1"
                else
                    print_error "알 수 없는 옵션: $1"
                    echo "도움말: ./init.sh --help"
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # Execute based on mode
    case "$mode" in
        init)
            do_init
            ;;
        migrate)
            do_migrate "$target_path"
            ;;
        check)
            do_check
            ;;
        *)
            print_error "알 수 없는 모드: $mode"
            exit 1
            ;;
    esac
}

# Run main
main "$@"
