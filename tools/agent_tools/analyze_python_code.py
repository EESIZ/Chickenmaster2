#!/usr/bin/env python3
"""Python 코드 분석 도구

AST 모듈을 사용하여 Python 소스 파일을 직접 분석합니다.
함수, 클래스, 임포트, 상수 등의 구조 정보를 추출합니다.

Usage:
    # 단일 파일 분석
    uv run python -m tools.agent_tools.analyze_python_code --file path/to/file.py
    
    # 디렉터리 분석
    uv run python -m tools.agent_tools.analyze_python_code --directory src/utils/ --recursive
    
    # 결과를 파일로 저장
    uv run python -m tools.agent_tools.analyze_python_code \
        --directory src/ --recursive --output results/analysis.json
    
    # 다른 출력 형식
    uv run python -m tools.agent_tools.analyze_python_code --file src/main.py --output-format markdown
"""

from __future__ import annotations

import argparse
import ast
import csv
import io
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def get_project_root() -> Path:
    """프로젝트 루트 디렉터리 반환."""
    return Path(__file__).parent.parent.parent


class PythonCodeAnalyzer(ast.NodeVisitor):
    """Python 코드 분석을 위한 AST Visitor.
    
    AST 노드를 순회하며 함수, 클래스, 임포트, 상수 정보를 추출합니다.
    """
    
    def __init__(self, source_lines: list[str]) -> None:
        """분석기 초기화.
        
        Args:
            source_lines: 소스 파일의 라인 목록 (docstring 추출용)
        """
        self.source_lines = source_lines
        self.functions: list[dict[str, Any]] = []
        self.classes: list[dict[str, Any]] = []
        self.imports: list[str] = []
        self.constants: list[str] = []
        self.module_docstring: str | None = None
        self._current_class: str | None = None
    
    def _get_docstring(self, node: ast.AST) -> str | None:
        """노드에서 docstring 추출.
        
        Args:
            node: AST 노드 (FunctionDef, ClassDef, Module)
            
        Returns:
            docstring 또는 None
        """
        return ast.get_docstring(node)
    
    def _get_decorator_names(self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> list[str]:
        """데코레이터 이름 목록 추출.
        
        Args:
            node: 데코레이터가 있는 노드
            
        Returns:
            데코레이터 이름 목록
        """
        decorators: list[str] = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                # @module.decorator 형태
                parts: list[str] = []
                current: ast.expr = decorator
                while isinstance(current, ast.Attribute):
                    parts.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    parts.append(current.id)
                decorators.append(".".join(reversed(parts)))
            elif isinstance(decorator, ast.Call):
                # @decorator(args) 형태
                if isinstance(decorator.func, ast.Name):
                    decorators.append(f"{decorator.func.id}(...)")
                elif isinstance(decorator.func, ast.Attribute):
                    parts = []
                    current = decorator.func
                    while isinstance(current, ast.Attribute):
                        parts.append(current.attr)
                        current = current.value
                    if isinstance(current, ast.Name):
                        parts.append(current.id)
                    decorators.append(f"{'.'.join(reversed(parts))}(...)")
        return decorators
    
    def _get_function_args(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[dict[str, Any]]:
        """함수 인자 정보 추출.
        
        Args:
            node: 함수 정의 노드
            
        Returns:
            인자 정보 목록 (이름, 타입힌트, 기본값 여부)
        """
        args_info: list[dict[str, Any]] = []
        args = node.args
        
        # 일반 인자
        defaults_offset = len(args.args) - len(args.defaults)
        for i, arg in enumerate(args.args):
            arg_dict: dict[str, Any] = {"name": arg.arg}
            
            # 타입 힌트
            if arg.annotation:
                arg_dict["type_hint"] = ast.unparse(arg.annotation)
            
            # 기본값 여부
            if i >= defaults_offset:
                arg_dict["has_default"] = True
            
            args_info.append(arg_dict)
        
        # *args
        if args.vararg:
            vararg_dict: dict[str, Any] = {"name": f"*{args.vararg.arg}"}
            if args.vararg.annotation:
                vararg_dict["type_hint"] = ast.unparse(args.vararg.annotation)
            args_info.append(vararg_dict)
        
        # keyword-only 인자
        kw_defaults_map = {
            i: d for i, d in enumerate(args.kw_defaults) if d is not None
        }
        for i, arg in enumerate(args.kwonlyargs):
            arg_dict = {"name": arg.arg, "keyword_only": True}
            if arg.annotation:
                arg_dict["type_hint"] = ast.unparse(arg.annotation)
            if i in kw_defaults_map:
                arg_dict["has_default"] = True
            args_info.append(arg_dict)
        
        # **kwargs
        if args.kwarg:
            kwarg_dict: dict[str, Any] = {"name": f"**{args.kwarg.arg}"}
            if args.kwarg.annotation:
                kwarg_dict["type_hint"] = ast.unparse(args.kwarg.annotation)
            args_info.append(kwarg_dict)
        
        return args_info
    
    def _get_return_type(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
        """함수 반환 타입 추출.
        
        Args:
            node: 함수 정의 노드
            
        Returns:
            반환 타입 문자열 또는 None
        """
        if node.returns:
            return ast.unparse(node.returns)
        return None
    
    def _get_base_classes(self, node: ast.ClassDef) -> list[str]:
        """클래스 기반 클래스 목록 추출.
        
        Args:
            node: 클래스 정의 노드
            
        Returns:
            기반 클래스 이름 목록
        """
        bases: list[str] = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(ast.unparse(base))
            elif isinstance(base, ast.Subscript):
                # Generic[T] 형태
                bases.append(ast.unparse(base))
        return bases
    
    def visit_Module(self, node: ast.Module) -> None:
        """모듈 노드 방문 - docstring 추출.
        
        Args:
            node: 모듈 노드
        """
        self.module_docstring = self._get_docstring(node)
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import) -> None:
        """import 문 방문.
        
        Args:
            node: Import 노드
        """
        for alias in node.names:
            import_str = alias.name
            if alias.asname:
                import_str += f" as {alias.asname}"
            self.imports.append(import_str)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """from ... import ... 문 방문.
        
        Args:
            node: ImportFrom 노드
        """
        module = node.module or ""
        level_dots = "." * node.level
        
        for alias in node.names:
            if alias.name == "*":
                self.imports.append(f"from {level_dots}{module} import *")
            else:
                import_str = f"from {level_dots}{module} import {alias.name}"
                if alias.asname:
                    import_str += f" as {alias.asname}"
                self.imports.append(import_str)
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """함수 정의 방문.
        
        Args:
            node: FunctionDef 노드
        """
        self._process_function(node, is_async=False)
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """비동기 함수 정의 방문.
        
        Args:
            node: AsyncFunctionDef 노드
        """
        self._process_function(node, is_async=True)
        self.generic_visit(node)
    
    def _process_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        is_async: bool = False,
    ) -> None:
        """함수 정보 처리.
        
        Args:
            node: 함수 노드
            is_async: 비동기 함수 여부
        """
        func_info: dict[str, Any] = {
            "name": node.name,
            "lineno": node.lineno,
            "end_lineno": node.end_lineno,
            "docstring": self._get_docstring(node),
            "decorators": self._get_decorator_names(node),
            "args": self._get_function_args(node),
            "return_type": self._get_return_type(node),
            "is_async": is_async,
        }
        
        # 클래스 내 메서드인 경우
        if self._current_class:
            func_info["class"] = self._current_class
            
            # 메서드 종류 판별
            if node.decorator_list:
                decorator_names = [
                    d.id if isinstance(d, ast.Name) else ""
                    for d in node.decorator_list
                ]
                if "staticmethod" in decorator_names:
                    func_info["method_type"] = "static"
                elif "classmethod" in decorator_names:
                    func_info["method_type"] = "class"
                elif "property" in decorator_names:
                    func_info["method_type"] = "property"
                else:
                    func_info["method_type"] = "instance"
            else:
                func_info["method_type"] = "instance"
        
        self.functions.append(func_info)
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """클래스 정의 방문.
        
        Args:
            node: ClassDef 노드
        """
        # 메서드 이름 추출
        methods: list[str] = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(item.name)
        
        class_info: dict[str, Any] = {
            "name": node.name,
            "lineno": node.lineno,
            "end_lineno": node.end_lineno,
            "docstring": self._get_docstring(node),
            "decorators": self._get_decorator_names(node),
            "bases": self._get_base_classes(node),
            "methods": methods,
        }
        
        self.classes.append(class_info)
        
        # 클래스 내부 메서드 처리
        prev_class = self._current_class
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = prev_class
    
    def visit_Assign(self, node: ast.Assign) -> None:
        """할당문 방문 - 모듈 레벨 상수 추출.
        
        Args:
            node: Assign 노드
        """
        # 클래스 내부가 아닌 경우만 (모듈 레벨 상수)
        if self._current_class is None:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    # 대문자로 시작하거나 전체 대문자인 경우 상수로 간주
                    name = target.id
                    if name.isupper() or (name[0].isupper() and "_" in name):
                        self.constants.append(name)
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """타입 어노테이션 할당문 방문.
        
        Args:
            node: AnnAssign 노드
        """
        # 클래스 내부가 아닌 경우만 (모듈 레벨 상수)
        if self._current_class is None and isinstance(node.target, ast.Name):
            name = node.target.id
            if name.isupper() or (name[0].isupper() and "_" in name):
                self.constants.append(name)
        self.generic_visit(node)


def analyze_file(path: Path) -> dict[str, Any]:
    """단일 Python 파일 분석.
    
    Args:
        path: 분석할 파일 경로
        
    Returns:
        분석 결과 딕셔너리:
        - path: 파일 경로
        - module_docstring: 모듈 docstring
        - imports: 임포트 목록
        - functions: 함수 정보 목록
        - classes: 클래스 정보 목록
        - constants: 상수 목록
        - metrics: 코드 메트릭
        
    Raises:
        FileNotFoundError: 파일이 존재하지 않는 경우
        SyntaxError: Python 문법 오류
    """
    if not path.exists():
        return {
            "status": "error",
            "error_type": "FileNotFoundError",
            "message": f"파일을 찾을 수 없습니다: {path}",
            "path": str(path),
            "timestamp": datetime.now().isoformat(),
        }
    
    if not path.suffix == ".py":
        return {
            "status": "error",
            "error_type": "InvalidFileType",
            "message": f"Python 파일이 아닙니다: {path}",
            "path": str(path),
            "timestamp": datetime.now().isoformat(),
        }
    
    try:
        # 파일 읽기 (여러 인코딩 시도)
        content: str | None = None
        encodings = ["utf-8", "utf-8-sig", "cp949", "euc-kr", "latin-1"]
        
        for encoding in encodings:
            try:
                content = path.read_text(encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            return {
                "status": "error",
                "error_type": "EncodingError",
                "message": f"파일 인코딩을 인식할 수 없습니다: {path}",
                "path": str(path),
                "timestamp": datetime.now().isoformat(),
            }
        
        source_lines = content.split("\n")
        
        # AST 파싱
        tree = ast.parse(content, filename=str(path))
        
        # 분석 수행
        analyzer = PythonCodeAnalyzer(source_lines)
        analyzer.visit(tree)
        
        # 결과 구성
        result: dict[str, Any] = {
            "status": "success",
            "path": str(path),
            "module_docstring": analyzer.module_docstring,
            "imports": analyzer.imports,
            "functions": analyzer.functions,
            "classes": analyzer.classes,
            "constants": analyzer.constants,
            "metrics": {
                "lines": len(source_lines),
                "non_empty_lines": len([ln for ln in source_lines if ln.strip()]),
                "functions": len([f for f in analyzer.functions if f.get("class") is None]),
                "methods": len([f for f in analyzer.functions if f.get("class") is not None]),
                "classes": len(analyzer.classes),
                "imports": len(analyzer.imports),
                "constants": len(analyzer.constants),
            },
            "timestamp": datetime.now().isoformat(),
        }
        
        return result
        
    except SyntaxError as e:
        return {
            "status": "error",
            "error_type": "SyntaxError",
            "message": f"Python 문법 오류: {e.msg}",
            "path": str(path),
            "lineno": e.lineno,
            "offset": e.offset,
            "text": e.text.strip() if e.text else None,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "message": str(e),
            "path": str(path),
            "timestamp": datetime.now().isoformat(),
        }


def analyze_directory(
    path: Path,
    recursive: bool = True,
    exclude_patterns: list[str] | None = None,
) -> dict[str, Any]:
    """디렉터리 내 모든 Python 파일 분석.
    
    Args:
        path: 분석할 디렉터리 경로
        recursive: 하위 디렉터리 포함 여부
        exclude_patterns: 제외할 패턴 목록 (예: ["test_*", "*_test.py"])
        
    Returns:
        분석 결과 딕셔너리:
        - files: 파일별 분석 결과
        - summary: 전체 요약
    """
    if not path.exists():
        return {
            "status": "error",
            "error_type": "DirectoryNotFoundError",
            "message": f"디렉터리를 찾을 수 없습니다: {path}",
            "path": str(path),
            "timestamp": datetime.now().isoformat(),
        }
    
    if not path.is_dir():
        return {
            "status": "error",
            "error_type": "NotADirectory",
            "message": f"디렉터리가 아닙니다: {path}",
            "path": str(path),
            "timestamp": datetime.now().isoformat(),
        }
    
    # 제외 패턴 기본값
    if exclude_patterns is None:
        exclude_patterns = ["__pycache__", ".git", ".venv", "venv", "node_modules"]
    
    # Python 파일 검색
    if recursive:
        py_files = list(path.rglob("*.py"))
    else:
        py_files = list(path.glob("*.py"))
    
    # 제외 패턴 적용
    filtered_files: list[Path] = []
    for py_file in py_files:
        exclude = False
        for pattern in exclude_patterns:
            if pattern in str(py_file):
                exclude = True
                break
        if not exclude:
            filtered_files.append(py_file)
    
    # 각 파일 분석
    files_results: dict[str, dict[str, Any]] = {}
    success_count = 0
    error_count = 0
    
    total_metrics = {
        "lines": 0,
        "non_empty_lines": 0,
        "functions": 0,
        "methods": 0,
        "classes": 0,
        "imports": 0,
        "constants": 0,
    }
    
    for py_file in sorted(filtered_files):
        relative_path = str(py_file.relative_to(path))
        result = analyze_file(py_file)
        files_results[relative_path] = result
        
        if result["status"] == "success":
            success_count += 1
            for key in total_metrics:
                total_metrics[key] += result["metrics"].get(key, 0)
        else:
            error_count += 1
    
    return {
        "status": "success",
        "directory": str(path),
        "recursive": recursive,
        "files_analyzed": success_count,
        "files_with_errors": error_count,
        "total_files": len(filtered_files),
        "files": files_results,
        "summary": {
            "total_metrics": total_metrics,
            "average_lines_per_file": (
                round(total_metrics["lines"] / success_count, 1)
                if success_count > 0 else 0
            ),
            "average_functions_per_file": (
                round(
                    (total_metrics["functions"] + total_metrics["methods"]) / success_count,
                    1,
                )
                if success_count > 0 else 0
            ),
        },
        "timestamp": datetime.now().isoformat(),
    }


def generate_summary_report(analysis_results: dict[str, Any]) -> str:
    """분석 결과에서 Markdown 요약 리포트 생성.
    
    Args:
        analysis_results: analyze_file 또는 analyze_directory의 결과
        
    Returns:
        Markdown 형식의 요약 리포트
    """
    lines: list[str] = []
    
    # 단일 파일 분석 결과
    if "module_docstring" in analysis_results:
        return _generate_file_report(analysis_results)
    
    # 디렉터리 분석 결과
    if "files" in analysis_results:
        return _generate_directory_report(analysis_results)
    
    return "분석 결과 형식을 인식할 수 없습니다."


def _generate_file_report(result: dict[str, Any]) -> str:
    """단일 파일 분석 리포트 생성.
    
    Args:
        result: analyze_file 결과
        
    Returns:
        Markdown 리포트
    """
    lines: list[str] = []
    
    if result.get("status") == "error":
        lines.append(f"# 분석 오류: {result.get('path', 'unknown')}")
        lines.append("")
        lines.append(f"**오류 유형**: {result.get('error_type')}")
        lines.append(f"**메시지**: {result.get('message')}")
        return "\n".join(lines)
    
    lines.append(f"# 코드 분석 리포트: {result['path']}")
    lines.append("")
    lines.append(f"**분석 시간**: {result['timestamp']}")
    lines.append("")
    
    # 모듈 docstring
    if result.get("module_docstring"):
        lines.append("## 모듈 설명")
        lines.append("")
        lines.append(f"> {result['module_docstring'][:200]}...")
        lines.append("")
    
    # 메트릭
    metrics = result.get("metrics", {})
    lines.append("## 코드 메트릭")
    lines.append("")
    lines.append("| 항목 | 값 |")
    lines.append("|------|-----|")
    lines.append(f"| 전체 라인 | {metrics.get('lines', 0)} |")
    lines.append(f"| 유효 라인 | {metrics.get('non_empty_lines', 0)} |")
    lines.append(f"| 함수 | {metrics.get('functions', 0)} |")
    lines.append(f"| 메서드 | {metrics.get('methods', 0)} |")
    lines.append(f"| 클래스 | {metrics.get('classes', 0)} |")
    lines.append(f"| 임포트 | {metrics.get('imports', 0)} |")
    lines.append(f"| 상수 | {metrics.get('constants', 0)} |")
    lines.append("")
    
    # 임포트
    if result.get("imports"):
        lines.append("## 임포트")
        lines.append("")
        for imp in result["imports"][:20]:
            lines.append(f"- `{imp}`")
        if len(result["imports"]) > 20:
            lines.append(f"- ... 외 {len(result['imports']) - 20}개")
        lines.append("")
    
    # 클래스
    if result.get("classes"):
        lines.append("## 클래스")
        lines.append("")
        for cls in result["classes"]:
            bases_str = f"({', '.join(cls['bases'])})" if cls.get("bases") else ""
            lines.append(f"### `{cls['name']}{bases_str}`")
            lines.append("")
            lines.append(f"- **위치**: L{cls['lineno']}-L{cls.get('end_lineno', '?')}")
            if cls.get("docstring"):
                doc_preview = cls["docstring"][:100].replace("\n", " ")
                lines.append(f"- **설명**: {doc_preview}...")
            if cls.get("methods"):
                lines.append(f"- **메서드**: {', '.join(cls['methods'][:10])}")
                if len(cls["methods"]) > 10:
                    lines.append(f"  - ... 외 {len(cls['methods']) - 10}개")
            lines.append("")
    
    # 함수 (클래스 외부)
    standalone_funcs = [f for f in result.get("functions", []) if f.get("class") is None]
    if standalone_funcs:
        lines.append("## 함수")
        lines.append("")
        for func in standalone_funcs[:30]:
            async_prefix = "async " if func.get("is_async") else ""
            args_preview = ", ".join([a["name"] for a in func.get("args", [])][:5])
            if len(func.get("args", [])) > 5:
                args_preview += ", ..."
            
            return_type = func.get("return_type", "")
            return_str = f" -> {return_type}" if return_type else ""
            
            lines.append(f"### `{async_prefix}{func['name']}({args_preview}){return_str}`")
            lines.append("")
            lines.append(f"- **위치**: L{func['lineno']}-L{func.get('end_lineno', '?')}")
            
            if func.get("decorators"):
                lines.append(f"- **데코레이터**: {', '.join(func['decorators'])}")
            
            if func.get("docstring"):
                doc_preview = func["docstring"][:100].replace("\n", " ")
                lines.append(f"- **설명**: {doc_preview}...")
            lines.append("")
        
        if len(standalone_funcs) > 30:
            lines.append(f"... 외 {len(standalone_funcs) - 30}개 함수")
            lines.append("")
    
    # 상수
    if result.get("constants"):
        lines.append("## 상수")
        lines.append("")
        lines.append(f"`{', '.join(result['constants'][:20])}`")
        if len(result["constants"]) > 20:
            lines.append(f"... 외 {len(result['constants']) - 20}개")
        lines.append("")
    
    return "\n".join(lines)


def _generate_directory_report(result: dict[str, Any]) -> str:
    """디렉터리 분석 리포트 생성.
    
    Args:
        result: analyze_directory 결과
        
    Returns:
        Markdown 리포트
    """
    lines: list[str] = []
    
    lines.append(f"# 디렉터리 분석 리포트: {result['directory']}")
    lines.append("")
    lines.append(f"**분석 시간**: {result['timestamp']}")
    lines.append(f"**재귀 분석**: {'예' if result['recursive'] else '아니오'}")
    lines.append("")
    
    # 요약
    lines.append("## 요약")
    lines.append("")
    lines.append("| 항목 | 값 |")
    lines.append("|------|-----|")
    lines.append(f"| 분석된 파일 | {result['files_analyzed']} |")
    lines.append(f"| 오류 파일 | {result['files_with_errors']} |")
    lines.append(f"| 전체 파일 | {result['total_files']} |")
    lines.append("")
    
    # 전체 메트릭
    summary = result.get("summary", {})
    total_metrics = summary.get("total_metrics", {})
    
    lines.append("## 전체 코드 메트릭")
    lines.append("")
    lines.append("| 항목 | 값 |")
    lines.append("|------|-----|")
    lines.append(f"| 전체 라인 | {total_metrics.get('lines', 0):,} |")
    lines.append(f"| 유효 라인 | {total_metrics.get('non_empty_lines', 0):,} |")
    lines.append(f"| 함수 | {total_metrics.get('functions', 0):,} |")
    lines.append(f"| 메서드 | {total_metrics.get('methods', 0):,} |")
    lines.append(f"| 클래스 | {total_metrics.get('classes', 0):,} |")
    lines.append(f"| 평균 라인/파일 | {summary.get('average_lines_per_file', 0)} |")
    lines.append(f"| 평균 함수/파일 | {summary.get('average_functions_per_file', 0)} |")
    lines.append("")
    
    # 파일별 요약
    lines.append("## 파일별 요약")
    lines.append("")
    lines.append("| 파일 | 라인 | 함수 | 클래스 | 상태 |")
    lines.append("|------|------|------|--------|------|")
    
    files = result.get("files", {})
    for file_path, file_result in sorted(files.items()):
        if file_result.get("status") == "success":
            m = file_result.get("metrics", {})
            total_funcs = m.get("functions", 0) + m.get("methods", 0)
            lines.append(
                f"| {file_path} | {m.get('lines', 0)} | {total_funcs} | "
                f"{m.get('classes', 0)} | ✅ |"
            )
        else:
            error_type = file_result.get("error_type", "Error")
            lines.append(f"| {file_path} | - | - | - | ❌ {error_type} |")
    
    lines.append("")
    
    # 오류 상세
    error_files = [
        (path, res) for path, res in files.items()
        if res.get("status") == "error"
    ]
    if error_files:
        lines.append("## 오류 상세")
        lines.append("")
        for file_path, file_result in error_files:
            lines.append(f"### {file_path}")
            lines.append("")
            lines.append(f"- **오류 유형**: {file_result.get('error_type')}")
            lines.append(f"- **메시지**: {file_result.get('message')}")
            if file_result.get("lineno"):
                lines.append(f"- **위치**: L{file_result.get('lineno')}")
            lines.append("")
    
    return "\n".join(lines)


def generate_csv_output(analysis_results: dict[str, Any]) -> str:
    """분석 결과에서 CSV 형식 출력 생성.
    
    Args:
        analysis_results: analyze_file 또는 analyze_directory의 결과
        
    Returns:
        CSV 형식 문자열
    """
    output = io.StringIO()
    
    # 단일 파일인 경우
    if "module_docstring" in analysis_results:
        files_data = {"file": analysis_results}
    elif "files" in analysis_results:
        files_data = analysis_results["files"]
    else:
        return "지원하지 않는 결과 형식입니다."
    
    # 함수/클래스 테이블 생성
    rows: list[dict[str, Any]] = []
    
    for file_path, file_result in files_data.items():
        if file_result.get("status") != "success":
            continue
        
        # 클래스 정보
        for cls in file_result.get("classes", []):
            rows.append({
                "file": file_path,
                "type": "class",
                "name": cls["name"],
                "lineno": cls["lineno"],
                "end_lineno": cls.get("end_lineno", ""),
                "parent": "",
                "decorators": ", ".join(cls.get("decorators", [])),
                "bases": ", ".join(cls.get("bases", [])),
                "docstring": (cls.get("docstring") or "")[:100],
            })
        
        # 함수 정보
        for func in file_result.get("functions", []):
            rows.append({
                "file": file_path,
                "type": "method" if func.get("class") else "function",
                "name": func["name"],
                "lineno": func["lineno"],
                "end_lineno": func.get("end_lineno", ""),
                "parent": func.get("class", ""),
                "decorators": ", ".join(func.get("decorators", [])),
                "bases": "",
                "docstring": (func.get("docstring") or "")[:100],
            })
    
    if not rows:
        return "분석 결과가 없습니다."
    
    fieldnames = [
        "file", "type", "name", "lineno", "end_lineno",
        "parent", "decorators", "bases", "docstring",
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    
    return output.getvalue()


def main() -> None:
    """메인 진입점."""
    parser = argparse.ArgumentParser(
        description="Python 코드 분석 도구 (AST 기반, JSON 출력)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
    # 단일 파일 분석
    uv run python -m tools.agent_tools.analyze_python_code --file src/main.py
    
    # 디렉터리 분석 (재귀)
    uv run python -m tools.agent_tools.analyze_python_code --directory src/ --recursive
    
    # Markdown 리포트 출력
    uv run python -m tools.agent_tools.analyze_python_code --file src/main.py --output-format markdown
    
    # 결과를 파일로 저장
    uv run python -m tools.agent_tools.analyze_python_code --directory src/ --output analysis.json
        """,
    )
    
    # 입력 옵션 (상호 배타적)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--file", "-f",
        type=str,
        help="분석할 Python 파일 경로",
    )
    input_group.add_argument(
        "--directory", "-d",
        type=str,
        help="분석할 디렉터리 경로",
    )
    
    # 추가 옵션
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        default=True,
        help="하위 디렉터리 포함 (기본값: True)",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="하위 디렉터리 제외",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="결과를 저장할 파일 경로",
    )
    parser.add_argument(
        "--output-format",
        type=str,
        choices=["json", "markdown", "csv"],
        default="json",
        help="출력 형식 (기본값: json)",
    )
    parser.add_argument(
        "--exclude",
        type=str,
        nargs="*",
        default=["__pycache__", ".git", ".venv", "venv", "node_modules"],
        help="제외할 패턴 목록",
    )
    
    args = parser.parse_args()
    project_root = get_project_root()
    
    # 재귀 옵션 처리
    recursive = args.recursive and not args.no_recursive
    
    # 분석 수행
    if args.file:
        file_path = Path(args.file)
        if not file_path.is_absolute():
            file_path = project_root / file_path
        result = analyze_file(file_path)
    else:
        dir_path = Path(args.directory)
        if not dir_path.is_absolute():
            dir_path = project_root / dir_path
        result = analyze_directory(
            dir_path,
            recursive=recursive,
            exclude_patterns=args.exclude,
        )
    
    # 출력 형식 처리
    if args.output_format == "json":
        output_str = json.dumps(result, indent=2, ensure_ascii=False)
    elif args.output_format == "markdown":
        output_str = generate_summary_report(result)
    elif args.output_format == "csv":
        output_str = generate_csv_output(result)
    else:
        output_str = json.dumps(result, indent=2, ensure_ascii=False)
    
    # 출력
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = project_root / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_str, encoding="utf-8")
        print(json.dumps({
            "status": "success",
            "message": f"결과가 저장되었습니다: {output_path}",
            "output_path": str(output_path),
            "output_format": args.output_format,
            "timestamp": datetime.now().isoformat(),
        }, indent=2, ensure_ascii=False))
    else:
        print(output_str)
    
    # 오류가 있으면 종료 코드 1
    if result.get("status") == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
