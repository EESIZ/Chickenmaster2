#!/usr/bin/env python3
"""스킬 아티팩트 검증 도구

생성된 스킬의 품질과 규격 준수 여부를 검증합니다.

검증 항목:
- 프론트매터: YAML 형식, name/description 필드
- 콘텐츠: Usage 섹션, 프롬프트 인젝션 패턴, 저작권 휴리스틱
- 링크: 외부 링크 유효성 (선택적)

사용법:
    uv run python -m tools.agent_tools.validate_skill_artifact --path .github/skills/my-skill
    uv run python -m tools.agent_tools.validate_skill_artifact --path output/my-skill --check-links
    uv run python -m tools.agent_tools.validate_skill_artifact --path skill.zip --output-md report.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import zipfile
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

import yaml


# ============================================================================
# 상수 정의
# ============================================================================

# 이름 패턴: 소문자, 숫자, 하이픈 (연속 하이픈 불가)
NAME_PATTERN = re.compile(r"^[a-z]([a-z0-9]|-(?!-))*[a-z0-9]$|^[a-z]$")

# Description 길이 제한
MIN_DESCRIPTION_LENGTH = 10
MAX_DESCRIPTION_LENGTH = 1024

# 프롬프트 인젝션 탐지 패턴
PROMPT_INJECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("system_override", re.compile(r"ignore\s+(all\s+)?(previous|above)\s+instructions", re.IGNORECASE)),
    ("role_impersonation", re.compile(r"you\s+are\s+(now|actually)\s+a", re.IGNORECASE)),
    ("jailbreak_attempt", re.compile(r"(DAN|do\s+anything\s+now|developer\s+mode)", re.IGNORECASE)),
    ("instruction_override", re.compile(r"disregard\s+(your|all)\s+(instructions|rules)", re.IGNORECASE)),
    ("base64_encoded", re.compile(r"base64\s*:\s*[A-Za-z0-9+/=]{50,}", re.IGNORECASE)),
    ("hidden_command", re.compile(r"\[SYSTEM\]|\[ADMIN\]|\[OVERRIDE\]", re.IGNORECASE)),
    ("prompt_leak", re.compile(r"(reveal|show|print)\s+(your\s+)?(system\s+)?(prompt|instructions)", re.IGNORECASE)),
]

# 저작권 휴리스틱 패턴
COPYRIGHT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("all_rights_reserved", re.compile(r"all\s+rights\s+reserved", re.IGNORECASE)),
    ("copyright_notice", re.compile(r"©\s*\d{4}|copyright\s*©?\s*\d{4}", re.IGNORECASE)),
    ("proprietary_notice", re.compile(r"proprietary\s+and\s+confidential", re.IGNORECASE)),
    ("license_block", re.compile(r"licensed?\s+under\s+[A-Za-z0-9\s]+license", re.IGNORECASE)),
]

# 긴 저작권 블록 임계값 (문자 수)
LONG_COPYRIGHT_BLOCK_THRESHOLD = 500


class Severity(str, Enum):
    """검증 결과 심각도"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# ============================================================================
# 유틸리티 함수
# ============================================================================

def get_project_root() -> Path:
    """프로젝트 루트 디렉토리 반환"""
    return Path(__file__).parent.parent.parent


def extract_frontmatter(content: str) -> tuple[dict[str, Any] | None, str | None]:
    """마크다운 콘텐츠에서 YAML 프론트매터 추출
    
    Args:
        content: 전체 마크다운 파일 내용
        
    Returns:
        (프론트매터 딕셔너리, 에러 메시지)
    """
    pattern = r"^---\s*\n(.*?)\n---\s*\n"
    match = re.match(pattern, content, re.DOTALL)
    
    if not match:
        return None, "YAML 프론트매터를 찾을 수 없습니다"
    
    try:
        frontmatter = yaml.safe_load(match.group(1))
        if not isinstance(frontmatter, dict):
            return None, "프론트매터가 딕셔너리 형식이 아닙니다"
        return frontmatter, None
    except yaml.YAMLError as e:
        return None, f"YAML 파싱 오류: {e}"


def extract_links(content: str) -> list[dict[str, str]]:
    """마크다운 콘텐츠에서 링크 추출
    
    Args:
        content: 마크다운 콘텐츠
        
    Returns:
        링크 정보 리스트 [{"url": ..., "text": ...}, ...]
    """
    # 인라인 링크: [text](url)
    inline_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    
    links = []
    for match in inline_pattern.finditer(content):
        text, url = match.groups()
        # 앵커 링크 제외
        if not url.startswith("#"):
            links.append({"text": text.strip(), "url": url.strip()})
    
    return links


def find_long_text_blocks(content: str, threshold: int = LONG_COPYRIGHT_BLOCK_THRESHOLD) -> list[dict[str, Any]]:
    """긴 텍스트 블록 탐지 (저작권 블록 휴리스틱)
    
    Args:
        content: 검사할 콘텐츠
        threshold: 블록 길이 임계값
        
    Returns:
        긴 블록 정보 리스트
    """
    # 코드 블록이 아닌 연속된 텍스트 블록 찾기
    # 빈 줄로 구분된 단락들
    paragraphs = re.split(r"\n\s*\n", content)
    
    long_blocks = []
    for i, para in enumerate(paragraphs):
        # 코드 블록 제외
        if para.strip().startswith("```"):
            continue
        
        # 리스트나 헤딩이 아닌 긴 텍스트
        if len(para) > threshold:
            # 저작권 관련 키워드가 포함된 경우
            for pattern_name, pattern in COPYRIGHT_PATTERNS:
                if pattern.search(para):
                    long_blocks.append({
                        "paragraph_index": i,
                        "length": len(para),
                        "pattern_matched": pattern_name,
                        "preview": para[:200] + "..." if len(para) > 200 else para,
                    })
                    break
    
    return long_blocks


# ============================================================================
# 검증 결과 타입
# ============================================================================

def create_check_result(
    name: str,
    severity: Severity,
    passed: bool,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """검증 결과 생성
    
    Args:
        name: 검증 항목 이름
        severity: 심각도
        passed: 통과 여부
        message: 결과 메시지
        details: 추가 세부 정보
        
    Returns:
        검증 결과 딕셔너리
    """
    result: dict[str, Any] = {
        "name": name,
        "severity": severity.value,
        "passed": passed,
        "message": message,
    }
    if details:
        result["details"] = details
    return result


# ============================================================================
# 프론트매터 검증
# ============================================================================

def validate_frontmatter(skill_md_path: Path) -> list[dict[str, Any]]:
    """프론트매터 검증
    
    검증 항목:
    - YAML 프론트매터 존재
    - name 필드 존재 및 형식 (소문자-하이픈, 연속 하이픈 불가)
    - description 필드 존재 및 길이 (10-1024자)
    - name이 폴더명과 일치
    
    Args:
        skill_md_path: SKILL.md 파일 경로
        
    Returns:
        검증 결과 리스트
    """
    checks: list[dict[str, Any]] = []
    
    # 파일 존재 확인
    if not skill_md_path.exists():
        checks.append(create_check_result(
            name="file_exists",
            severity=Severity.ERROR,
            passed=False,
            message=f"SKILL.md 파일을 찾을 수 없습니다: {skill_md_path}",
        ))
        return checks
    
    checks.append(create_check_result(
        name="file_exists",
        severity=Severity.ERROR,
        passed=True,
        message="SKILL.md 파일이 존재합니다",
    ))
    
    # 파일 읽기
    try:
        content = skill_md_path.read_text(encoding="utf-8")
    except OSError as e:
        checks.append(create_check_result(
            name="file_readable",
            severity=Severity.ERROR,
            passed=False,
            message=f"파일 읽기 오류: {e}",
        ))
        return checks
    
    # 프론트매터 추출
    frontmatter, error = extract_frontmatter(content)
    
    if error:
        checks.append(create_check_result(
            name="frontmatter_present",
            severity=Severity.ERROR,
            passed=False,
            message=error,
        ))
        return checks
    
    checks.append(create_check_result(
        name="frontmatter_present",
        severity=Severity.ERROR,
        passed=True,
        message="YAML 프론트매터가 존재합니다",
    ))
    
    assert frontmatter is not None  # type narrowing
    
    # name 필드 검증
    name = frontmatter.get("name")
    
    if name is None:
        checks.append(create_check_result(
            name="name_present",
            severity=Severity.ERROR,
            passed=False,
            message="'name' 필드가 누락되었습니다",
        ))
    elif not isinstance(name, str):
        checks.append(create_check_result(
            name="name_present",
            severity=Severity.ERROR,
            passed=False,
            message=f"'name' 필드는 문자열이어야 합니다 (현재: {type(name).__name__})",
        ))
    else:
        checks.append(create_check_result(
            name="name_present",
            severity=Severity.ERROR,
            passed=True,
            message=f"'name' 필드가 존재합니다: {name}",
        ))
        
        # name 형식 검증
        if NAME_PATTERN.match(name):
            checks.append(create_check_result(
                name="name_format",
                severity=Severity.ERROR,
                passed=True,
                message="'name' 형식이 올바릅니다 (소문자-하이픈)",
            ))
        else:
            # 연속 하이픈 체크
            if "--" in name:
                error_detail = "연속된 하이픈(--) 사용 불가"
            elif not name[0].islower() or not name[0].isalpha():
                error_detail = "소문자 알파벳으로 시작해야 합니다"
            elif name.endswith("-"):
                error_detail = "하이픈으로 끝날 수 없습니다"
            else:
                error_detail = "소문자, 숫자, 하이픈만 사용 가능"
                
            checks.append(create_check_result(
                name="name_format",
                severity=Severity.ERROR,
                passed=False,
                message=f"'name' 형식이 올바르지 않습니다: {name} ({error_detail})",
            ))
        
        # name이 폴더명과 일치하는지 검증
        folder_name = skill_md_path.parent.name
        if name == folder_name:
            checks.append(create_check_result(
                name="name_matches_folder",
                severity=Severity.ERROR,
                passed=True,
                message=f"'name'이 폴더명과 일치합니다: {name}",
            ))
        else:
            checks.append(create_check_result(
                name="name_matches_folder",
                severity=Severity.ERROR,
                passed=False,
                message=f"'name'({name})이 폴더명({folder_name})과 일치하지 않습니다",
            ))
    
    # description 필드 검증
    description = frontmatter.get("description")
    
    if description is None:
        checks.append(create_check_result(
            name="description_present",
            severity=Severity.ERROR,
            passed=False,
            message="'description' 필드가 누락되었습니다",
        ))
    elif not isinstance(description, str):
        checks.append(create_check_result(
            name="description_present",
            severity=Severity.ERROR,
            passed=False,
            message=f"'description' 필드는 문자열이어야 합니다 (현재: {type(description).__name__})",
        ))
    else:
        checks.append(create_check_result(
            name="description_present",
            severity=Severity.ERROR,
            passed=True,
            message=f"'description' 필드가 존재합니다 ({len(description)}자)",
        ))
        
        # description 길이 검증
        desc_len = len(description)
        if desc_len < MIN_DESCRIPTION_LENGTH:
            checks.append(create_check_result(
                name="description_length",
                severity=Severity.ERROR,
                passed=False,
                message=f"'description'이 너무 짧습니다 ({desc_len}자, 최소 {MIN_DESCRIPTION_LENGTH}자)",
            ))
        elif desc_len > MAX_DESCRIPTION_LENGTH:
            checks.append(create_check_result(
                name="description_length",
                severity=Severity.ERROR,
                passed=False,
                message=f"'description'이 너무 깁니다 ({desc_len}자, 최대 {MAX_DESCRIPTION_LENGTH}자)",
            ))
        else:
            checks.append(create_check_result(
                name="description_length",
                severity=Severity.ERROR,
                passed=True,
                message=f"'description' 길이가 적절합니다 ({desc_len}자)",
            ))
    
    return checks


# ============================================================================
# 콘텐츠 검증
# ============================================================================

def validate_content(skill_md_content: str) -> list[dict[str, Any]]:
    """콘텐츠 검증
    
    검증 항목:
    - Usage 섹션 존재
    - 프롬프트 인젝션 패턴 탐지
    - 저작권 휴리스틱 (긴 블록, "All rights reserved" 등)
    
    Args:
        skill_md_content: SKILL.md 파일 내용
        
    Returns:
        검증 결과 리스트
    """
    checks: list[dict[str, Any]] = []
    
    # Usage 섹션 검증
    usage_pattern = re.compile(r"^##\s+Usage", re.MULTILINE | re.IGNORECASE)
    has_usage = usage_pattern.search(skill_md_content)
    
    checks.append(create_check_result(
        name="usage_section",
        severity=Severity.ERROR,
        passed=bool(has_usage),
        message="'## Usage' 섹션이 존재합니다" if has_usage else "'## Usage' 섹션이 누락되었습니다",
    ))
    
    # 프롬프트 인젝션 패턴 검사
    injection_found: list[dict[str, str]] = []
    
    for pattern_name, pattern in PROMPT_INJECTION_PATTERNS:
        matches = pattern.findall(skill_md_content)
        if matches:
            injection_found.append({
                "pattern": pattern_name,
                "matches": matches[:3] if isinstance(matches[0], str) else [m[0] for m in matches[:3]],
            })
    
    if injection_found:
        checks.append(create_check_result(
            name="no_prompt_injection",
            severity=Severity.ERROR,
            passed=False,
            message=f"프롬프트 인젝션 패턴이 탐지되었습니다 ({len(injection_found)}개 유형)",
            details={"patterns_found": injection_found},
        ))
    else:
        checks.append(create_check_result(
            name="no_prompt_injection",
            severity=Severity.ERROR,
            passed=True,
            message="프롬프트 인젝션 패턴이 탐지되지 않았습니다",
        ))
    
    # 저작권 휴리스틱 검사
    copyright_matches: list[dict[str, Any]] = []
    
    for pattern_name, pattern in COPYRIGHT_PATTERNS:
        matches = pattern.findall(skill_md_content)
        if matches:
            copyright_matches.append({
                "pattern": pattern_name,
                "count": len(matches),
            })
    
    if copyright_matches:
        checks.append(create_check_result(
            name="copyright_heuristic",
            severity=Severity.WARNING,
            passed=False,
            message=f"저작권 관련 문구가 발견되었습니다 ({len(copyright_matches)}개 유형)",
            details={"patterns_found": copyright_matches},
        ))
    else:
        checks.append(create_check_result(
            name="copyright_heuristic",
            severity=Severity.WARNING,
            passed=True,
            message="저작권 관련 문구가 발견되지 않았습니다",
        ))
    
    # 긴 텍스트 블록 검사 (저작권 블록 휴리스틱)
    long_blocks = find_long_text_blocks(skill_md_content)
    
    if long_blocks:
        checks.append(create_check_result(
            name="long_copyright_blocks",
            severity=Severity.WARNING,
            passed=False,
            message=f"저작권 관련 긴 텍스트 블록이 발견되었습니다 ({len(long_blocks)}개)",
            details={"blocks": long_blocks},
        ))
    else:
        checks.append(create_check_result(
            name="long_copyright_blocks",
            severity=Severity.WARNING,
            passed=True,
            message="의심스러운 긴 텍스트 블록이 발견되지 않았습니다",
        ))
    
    # 빈 콘텐츠 검사 (프론트매터 제외)
    content_without_frontmatter = re.sub(r"^---\s*\n.*?\n---\s*\n", "", skill_md_content, flags=re.DOTALL)
    content_length = len(content_without_frontmatter.strip())
    
    if content_length < 100:
        checks.append(create_check_result(
            name="content_length",
            severity=Severity.WARNING,
            passed=False,
            message=f"콘텐츠가 너무 짧습니다 ({content_length}자)",
        ))
    else:
        checks.append(create_check_result(
            name="content_length",
            severity=Severity.INFO,
            passed=True,
            message=f"콘텐츠 길이: {content_length}자",
        ))
    
    return checks


# ============================================================================
# 링크 검증
# ============================================================================

def validate_links(skill_md_content: str, timeout: float = 5.0) -> list[dict[str, Any]]:
    """링크 검증 (선택적, 느릴 수 있음)
    
    외부 링크의 유효성을 검사합니다. 네트워크 요청이 필요하므로 느릴 수 있습니다.
    
    Args:
        skill_md_content: SKILL.md 파일 내용
        timeout: 요청 타임아웃 (초)
        
    Returns:
        검증 결과 리스트
    """
    checks: list[dict[str, Any]] = []
    
    links = extract_links(skill_md_content)
    
    if not links:
        checks.append(create_check_result(
            name="links_valid",
            severity=Severity.INFO,
            passed=True,
            message="검사할 외부 링크가 없습니다",
        ))
        return checks
    
    # 외부 링크만 필터링
    external_links = [
        link for link in links
        if link["url"].startswith(("http://", "https://"))
    ]
    
    if not external_links:
        checks.append(create_check_result(
            name="links_valid",
            severity=Severity.INFO,
            passed=True,
            message="검사할 외부 링크가 없습니다",
        ))
        return checks
    
    # HTTP 요청 시도
    try:
        import urllib.request
        import urllib.error
    except ImportError:
        checks.append(create_check_result(
            name="links_valid",
            severity=Severity.INFO,
            passed=True,
            message="urllib 모듈을 사용할 수 없습니다 (링크 검증 건너뜀)",
        ))
        return checks
    
    broken_links: list[dict[str, Any]] = []
    valid_count = 0
    
    for link in external_links:
        url = link["url"]
        try:
            request = urllib.request.Request(
                url,
                method="HEAD",
                headers={"User-Agent": "SkillValidator/1.0"},
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                if response.status < 400:
                    valid_count += 1
                else:
                    broken_links.append({
                        "url": url,
                        "text": link["text"],
                        "status": response.status,
                    })
        except urllib.error.HTTPError as e:
            broken_links.append({
                "url": url,
                "text": link["text"],
                "status": e.code,
                "error": str(e.reason),
            })
        except urllib.error.URLError as e:
            broken_links.append({
                "url": url,
                "text": link["text"],
                "status": None,
                "error": str(e.reason),
            })
        except Exception as e:  # noqa: BLE001
            broken_links.append({
                "url": url,
                "text": link["text"],
                "status": None,
                "error": str(e),
            })
    
    if broken_links:
        checks.append(create_check_result(
            name="links_valid",
            severity=Severity.WARNING,
            passed=False,
            message=f"유효하지 않은 링크가 발견되었습니다 ({len(broken_links)}개)",
            details={
                "broken_links": broken_links,
                "total_links": len(external_links),
                "valid_links": valid_count,
            },
        ))
    else:
        checks.append(create_check_result(
            name="links_valid",
            severity=Severity.INFO,
            passed=True,
            message=f"모든 외부 링크가 유효합니다 ({valid_count}개)",
        ))
    
    return checks


# ============================================================================
# 리포트 생성
# ============================================================================

def generate_report(
    validations: list[dict[str, Any]],
    output_json: Path | None = None,
    output_md: Path | None = None,
    skill_path: str = "",
) -> dict[str, Any]:
    """검증 리포트 생성
    
    JSON 및 마크다운 형식으로 검증 결과 리포트를 생성합니다.
    
    Args:
        validations: 검증 결과 리스트
        output_json: JSON 출력 파일 경로 (선택)
        output_md: 마크다운 출력 파일 경로 (선택)
        skill_path: 검증된 스킬 경로
        
    Returns:
        리포트 딕셔너리
    """
    # 상태 결정
    errors = [v for v in validations if v["severity"] == "error" and not v["passed"]]
    warnings = [v for v in validations if v["severity"] == "warning" and not v["passed"]]
    
    status: Literal["pass", "fail"] = "fail" if errors else "pass"
    
    report: dict[str, Any] = {
        "status": status,
        "skill_path": skill_path,
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_checks": len(validations),
            "passed": sum(1 for v in validations if v["passed"]),
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "checks": validations,
    }
    
    # JSON 출력
    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 마크다운 출력
    if output_md:
        md_content = generate_markdown_report(report)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        with open(output_md, "w", encoding="utf-8") as f:
            f.write(md_content)
    
    return report


def generate_markdown_report(report: dict[str, Any]) -> str:
    """마크다운 형식의 리포트 생성
    
    Args:
        report: 리포트 딕셔너리
        
    Returns:
        마크다운 문자열
    """
    status_emoji = "✅" if report["status"] == "pass" else "❌"
    summary = report["summary"]
    
    lines = [
        f"# 스킬 검증 리포트 {status_emoji}",
        "",
        f"**상태**: {report['status'].upper()}",
        f"**경로**: `{report['skill_path']}`",
        f"**시간**: {report['timestamp']}",
        "",
        "## 요약",
        "",
        f"| 항목 | 값 |",
        f"|------|-----|",
        f"| 전체 검사 | {summary['total_checks']} |",
        f"| 통과 | {summary['passed']} |",
        f"| 오류 | {summary['errors']} |",
        f"| 경고 | {summary['warnings']} |",
        "",
        "## 상세 결과",
        "",
    ]
    
    # 결과를 심각도별로 그룹화
    errors = [c for c in report["checks"] if c["severity"] == "error" and not c["passed"]]
    warnings = [c for c in report["checks"] if c["severity"] == "warning" and not c["passed"]]
    passed = [c for c in report["checks"] if c["passed"]]
    
    if errors:
        lines.append("### ❌ 오류")
        lines.append("")
        for check in errors:
            lines.append(f"- **{check['name']}**: {check['message']}")
            if "details" in check:
                lines.append(f"  - 세부 정보: `{json.dumps(check['details'], ensure_ascii=False)[:200]}`")
        lines.append("")
    
    if warnings:
        lines.append("### ⚠️ 경고")
        lines.append("")
        for check in warnings:
            lines.append(f"- **{check['name']}**: {check['message']}")
            if "details" in check:
                lines.append(f"  - 세부 정보: `{json.dumps(check['details'], ensure_ascii=False)[:200]}`")
        lines.append("")
    
    if passed:
        lines.append("### ✅ 통과")
        lines.append("")
        for check in passed:
            lines.append(f"- **{check['name']}**: {check['message']}")
        lines.append("")
    
    return "\n".join(lines)


# ============================================================================
# 메인 검증 함수
# ============================================================================

def validate_skill(
    skill_path: Path,
    check_links: bool = False,
    link_timeout: float = 5.0,
) -> dict[str, Any]:
    """스킬 아티팩트 전체 검증
    
    Args:
        skill_path: 스킬 디렉토리 또는 ZIP 파일 경로
        check_links: 외부 링크 검증 여부
        link_timeout: 링크 검증 타임아웃 (초)
        
    Returns:
        검증 결과 리포트
    """
    validations: list[dict[str, Any]] = []
    
    # ZIP 파일 처리
    if skill_path.suffix == ".zip":
        if not zipfile.is_zipfile(skill_path):
            return {
                "status": "fail",
                "skill_path": str(skill_path),
                "timestamp": datetime.now().isoformat(),
                "error": "유효한 ZIP 파일이 아닙니다",
            }
        
        # 임시 디렉토리에 압축 해제
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(skill_path, "r") as zf:
                zf.extractall(tmpdir)
            
            # SKILL.md 찾기
            tmppath = Path(tmpdir)
            skill_md_files = list(tmppath.rglob("SKILL.md"))
            
            if not skill_md_files:
                return {
                    "status": "fail",
                    "skill_path": str(skill_path),
                    "timestamp": datetime.now().isoformat(),
                    "error": "ZIP 파일 내에 SKILL.md를 찾을 수 없습니다",
                }
            
            skill_md_path = skill_md_files[0]
            content = skill_md_path.read_text(encoding="utf-8")
            
            # 프론트매터 검증
            validations.extend(validate_frontmatter(skill_md_path))
            
            # 콘텐츠 검증
            validations.extend(validate_content(content))
            
            # 링크 검증 (선택적)
            if check_links:
                validations.extend(validate_links(content, timeout=link_timeout))
    else:
        # 디렉토리 처리
        if skill_path.is_file():
            skill_md_path = skill_path
        else:
            skill_md_path = skill_path / "SKILL.md"
        
        # 프론트매터 검증
        validations.extend(validate_frontmatter(skill_md_path))
        
        # 파일이 존재하는 경우에만 콘텐츠/링크 검증
        if skill_md_path.exists():
            content = skill_md_path.read_text(encoding="utf-8")
            
            # 콘텐츠 검증
            validations.extend(validate_content(content))
            
            # 링크 검증 (선택적)
            if check_links:
                validations.extend(validate_links(content, timeout=link_timeout))
    
    # 리포트 생성
    return generate_report(validations, skill_path=str(skill_path))


# ============================================================================
# CLI 진입점
# ============================================================================

def main() -> None:
    """메인 CLI 진입점"""
    parser = argparse.ArgumentParser(
        description="스킬 아티팩트 검증 (JSON 출력)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
    # 디렉토리 검증
    uv run python -m tools.agent_tools.validate_skill_artifact --path .github/skills/my-skill
    
    # ZIP 파일 검증
    uv run python -m tools.agent_tools.validate_skill_artifact --path output/my-skill.zip
    
    # 링크 검증 포함
    uv run python -m tools.agent_tools.validate_skill_artifact --path skill/ --check-links
    
    # 리포트 파일 출력
    uv run python -m tools.agent_tools.validate_skill_artifact --path skill/ --output-json result.json --output-md report.md
        """,
    )
    parser.add_argument(
        "--path",
        type=str,
        required=True,
        help="스킬 디렉토리 또는 ZIP 파일 경로",
    )
    parser.add_argument(
        "--check-links",
        action="store_true",
        help="외부 링크 유효성 검사 (느릴 수 있음)",
    )
    parser.add_argument(
        "--link-timeout",
        type=float,
        default=5.0,
        help="링크 검증 타임아웃 (초, 기본값: 5.0)",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="JSON 리포트 출력 파일 경로",
    )
    parser.add_argument(
        "--output-md",
        type=str,
        default=None,
        help="마크다운 리포트 출력 파일 경로",
    )
    
    args = parser.parse_args()
    project_root = get_project_root()
    
    # 경로 처리
    skill_path = Path(args.path)
    if not skill_path.is_absolute():
        skill_path = project_root / skill_path
    
    # 검증 실행
    result = validate_skill(
        skill_path=skill_path,
        check_links=args.check_links,
        link_timeout=args.link_timeout,
    )
    
    # 출력 파일 처리
    if args.output_json:
        output_json = Path(args.output_json)
        if not output_json.is_absolute():
            output_json = project_root / output_json
        output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    
    if args.output_md:
        output_md = Path(args.output_md)
        if not output_md.is_absolute():
            output_md = project_root / output_md
        md_content = generate_markdown_report(result)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        with open(output_md, "w", encoding="utf-8") as f:
            f.write(md_content)
    
    # JSON 출력
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 종료 코드
    if result.get("status") != "pass":
        sys.exit(1)


if __name__ == "__main__":
    main()
