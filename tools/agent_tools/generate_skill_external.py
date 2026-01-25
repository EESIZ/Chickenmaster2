#!/usr/bin/env python3
"""Skill Seekers 외부 문서 기반 스킬 생성 래퍼.

외부 라이브러리 문서를 기반으로 Agent Skill을 생성하는 도구.
보안을 위해 격리(quarantine) 모드를 기본으로 사용.

Usage:
    uv run python -m tools.agent_tools.generate_skill_external \
        --config configs/skill_seekers/my_library.json \
        --output-mode quarantine \
        --output-dir temp/skill_seekers/

Note:
    실제 Skill Seekers 호출은 분석 완료 후 구현 예정 (TBD).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict


class PathsOutput(TypedDict):
    """경로 정보 출력 스키마."""

    sandbox_dir: str
    quarantine_dir: str
    skill_md: str | None


class GenerationResult(TypedDict):
    """스킬 생성 결과 출력 스키마."""

    status: str  # "success" | "partial" | "failed"
    run_id: str
    config_name: str
    timestamp: str
    paths: PathsOutput
    warnings: list[str]
    errors: list[str]


def load_config(config_path: Path) -> dict[str, Any]:
    """설정 파일을 로드하고 기본 검증을 수행한다.

    Args:
        config_path: 설정 파일 경로 (JSON 형식)

    Returns:
        파싱된 설정 딕셔너리

    Raises:
        FileNotFoundError: 설정 파일이 존재하지 않는 경우
        ValueError: JSON 파싱 실패 또는 필수 필드 누락
    """
    if not config_path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")

    try:
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 파싱 실패: {e}") from e

    # 필수 필드 검증
    required_fields = ["name", "source_url"]
    missing_fields = [field for field in required_fields if field not in config]
    if missing_fields:
        raise ValueError(f"필수 필드 누락: {missing_fields}")

    return config


def prepare_sandbox(run_id: str, base_dir: Path) -> Path:
    """격리된 샌드박스 디렉터리를 준비한다.

    Args:
        run_id: 실행 고유 식별자
        base_dir: 샌드박스 기본 디렉터리

    Returns:
        생성된 샌드박스 디렉터리 경로
    """
    sandbox_dir = base_dir / run_id
    sandbox_dir.mkdir(parents=True, exist_ok=True)

    # 하위 디렉터리 구조 생성
    (sandbox_dir / "raw").mkdir(exist_ok=True)  # 원본 스크래핑 데이터
    (sandbox_dir / "processed").mkdir(exist_ok=True)  # 처리된 데이터
    (sandbox_dir / "output").mkdir(exist_ok=True)  # 생성된 스킬 파일

    return sandbox_dir


async def run_skill_seekers(
    config: dict[str, Any],
    sandbox_dir: Path,
) -> dict[str, Any]:
    """Skill Seekers를 실행하여 스킬을 생성한다.

    Note:
        실제 구현은 Skill Seekers 코드 분석 완료 후 추가 예정.
        현재는 placeholder로 동작.

    Args:
        config: 스킬 생성 설정
        sandbox_dir: 샌드박스 디렉터리 경로

    Returns:
        실행 결과 딕셔너리:
            - success: 성공 여부
            - skill_path: 생성된 스킬 파일 경로 (성공 시)
            - warnings: 경고 메시지 목록
            - errors: 오류 메시지 목록
    """
    # TODO: Skill Seekers 분석 완료 후 실제 구현 추가
    # 예상 구현 내용:
    # 1. Skill Seekers CLI 또는 API 호출
    # 2. 스크래핑 및 문서 처리
    # 3. 스킬 생성 및 검증
    # 4. 결과 파일 저장

    return {
        "success": False,
        "skill_path": None,
        "warnings": ["Skill Seekers 통합 미구현 - placeholder 반환"],
        "errors": ["TBD: run_skill_seekers 구현 필요"],
    }


def generate_json_output(
    status: str,
    run_id: str,
    config_name: str,
    paths: PathsOutput,
    warnings: list[str],
    errors: list[str],
) -> GenerationResult:
    """JSON 형식의 결과를 생성한다.

    Args:
        status: 실행 상태 ("success", "partial", "failed")
        run_id: 실행 고유 식별자
        config_name: 설정 파일 이름
        paths: 경로 정보
        warnings: 경고 메시지 목록
        errors: 오류 메시지 목록

    Returns:
        표준화된 JSON 출력 딕셔너리
    """
    return GenerationResult(
        status=status,
        run_id=run_id,
        config_name=config_name,
        timestamp=datetime.now(timezone.utc).isoformat(),
        paths=paths,
        warnings=warnings,
        errors=errors,
    )


def _generate_run_id() -> str:
    """고유한 실행 ID를 생성한다.

    Returns:
        타임스탬프 기반 실행 ID (예: "20260115_143052")
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _determine_status(result: dict[str, Any]) -> str:
    """실행 결과를 기반으로 상태를 결정한다.

    Args:
        result: run_skill_seekers 반환값

    Returns:
        상태 문자열: "success", "partial", "failed"
    """
    if result.get("success"):
        if result.get("warnings"):
            return "partial"
        return "success"
    return "failed"


async def main_async(args: argparse.Namespace) -> GenerationResult:
    """비동기 메인 실행 로직.

    Args:
        args: 파싱된 CLI 인수

    Returns:
        생성 결과 딕셔너리
    """
    warnings: list[str] = []
    errors: list[str] = []

    # 실행 ID 결정
    run_id = args.run_id or _generate_run_id()

    # 기본 경로 설정
    config_path = Path(args.config)
    output_dir = Path(args.output_dir)

    # 설정 로드
    try:
        config = load_config(config_path)
        config_name = config.get("name", config_path.stem)
    except (FileNotFoundError, ValueError) as e:
        return generate_json_output(
            status="failed",
            run_id=run_id,
            config_name=config_path.stem,
            paths=PathsOutput(
                sandbox_dir="",
                quarantine_dir="",
                skill_md=None,
            ),
            warnings=[],
            errors=[str(e)],
        )

    # 샌드박스 준비
    sandbox_dir = prepare_sandbox(run_id, output_dir)

    # quarantine 디렉터리 (검토 대기 영역)
    quarantine_dir = sandbox_dir / "quarantine"
    quarantine_dir.mkdir(exist_ok=True)

    # Skill Seekers 실행
    result = await run_skill_seekers(config, sandbox_dir)

    # 결과 수집
    warnings.extend(result.get("warnings", []))
    errors.extend(result.get("errors", []))

    # 상태 결정
    status = _determine_status(result)

    # 스킬 파일 경로
    skill_md_path = result.get("skill_path")
    if skill_md_path:
        skill_md_path = str(skill_md_path)

    return generate_json_output(
        status=status,
        run_id=run_id,
        config_name=config_name,
        paths=PathsOutput(
            sandbox_dir=str(sandbox_dir),
            quarantine_dir=str(quarantine_dir),
            skill_md=skill_md_path,
        ),
        warnings=warnings,
        errors=errors,
    )


def main() -> None:
    """CLI 엔트리포인트."""
    parser = argparse.ArgumentParser(
        description="Skill Seekers를 사용하여 외부 문서 기반 Agent Skill 생성",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
    # 기본 quarantine 모드로 실행
    uv run python -m tools.agent_tools.generate_skill_external \\
        --config configs/skill_seekers/langchain.json

    # 직접 출력 모드 (검토 없이 바로 생성)
    uv run python -m tools.agent_tools.generate_skill_external \\
        --config configs/skill_seekers/langchain.json \\
        --output-mode direct \\
        --output-dir .github/skills/

    # 커스텀 run-id 지정
    uv run python -m tools.agent_tools.generate_skill_external \\
        --config configs/skill_seekers/langchain.json \\
        --run-id langchain_v1
        """,
    )

    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="스킬 생성 설정 파일 경로 (JSON)",
    )

    parser.add_argument(
        "--output-mode",
        type=str,
        choices=["quarantine", "direct"],
        default="quarantine",
        help="출력 모드: quarantine(격리/검토 필요) 또는 direct(직접 생성) (기본값: quarantine)",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="temp/skill_seekers/",
        help="출력 디렉터리 (기본값: temp/skill_seekers/)",
    )

    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="실행 고유 식별자 (미지정 시 타임스탬프 자동 생성)",
    )

    args = parser.parse_args()

    # 비동기 실행
    result = asyncio.run(main_async(args))

    # JSON 출력
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 종료 코드 설정
    if result["status"] == "failed":
        sys.exit(1)
    elif result["status"] == "partial":
        sys.exit(0)  # 경고가 있어도 성공으로 처리
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
