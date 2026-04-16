"""
커스텀 도구 — PDF 읽기/테이블/용어 검증 + 동적 Python 코드 실행 샌드박스
"""

import contextlib
import difflib
import io
import os
import os.path as _ospath
import re
import signal
import traceback
from pathlib import Path

import pdfplumber
from langchain_core.tools import tool

UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", "uploads"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "output"))

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

MAX_OUTPUT = 10000


def _extract_text(file_path: str, start: int = 0, end: int = -1) -> tuple[str, int]:
    """PDF 전체 텍스트 추출 헬퍼. (text, total_pages) 반환."""
    with pdfplumber.open(file_path) as pdf:
        total = len(pdf.pages)
        e = end if end >= 0 else total
        s = max(0, start)
        e = min(e, total)
        lines = []
        for i in range(s, e):
            text = pdf.pages[i].extract_text()
            if text:
                lines.append(f"\n=== Page {i + 1} ===\n{text}")
        return "\n".join(lines), total


def _truncate(text: str, limit: int = MAX_OUTPUT) -> str:
    if len(text) > limit:
        return text[:limit] + "\n... (truncated)"
    return text


# ─── 기본 도구 ───


@tool
def list_uploads() -> str:
    """uploads 폴더의 파일 목록을 반환합니다."""
    if not UPLOAD_DIR.exists():
        return "uploads 폴더가 비어있습니다."
    files = [f.name for f in UPLOAD_DIR.iterdir() if f.is_file()]
    if not files:
        return "uploads 폴더가 비어있습니다."
    return "업로드된 파일:\n" + "\n".join(f"- uploads/{f}" for f in files)


@tool
def read_pdf(file_path: str, start_page: int = 0, end_page: int = -1) -> str:
    """PDF 파일에서 텍스트와 테이블을 추출합니다.
    큰 문서는 start_page/end_page로 페이지 범위를 지정하세요 (0-indexed).
    반환값에 TOTAL_PAGES 정보가 포함됩니다."""
    result_lines = []
    with pdfplumber.open(file_path) as pdf:
        total = len(pdf.pages)
        end = end_page if end_page >= 0 else total
        start = max(0, start_page)
        end = min(end, total)
        result_lines.append(f"TOTAL_PAGES: {total}")
        result_lines.append(f"READING: pages {start + 1}-{end} of {total}")

        for i in range(start, end):
            result_lines.append(f"\n=== Page {i + 1} ===")
            text = pdf.pages[i].extract_text()
            if text:
                result_lines.append(text)
            tables = pdf.pages[i].extract_tables()
            for j, t in enumerate(tables):
                result_lines.append(f"\n--- Table {j + 1} ({len(t)} rows) ---")
                for row in t:
                    result_lines.append("\t".join(str(c) if c else "" for c in row))

    return _truncate("\n".join(result_lines))


@tool
def extract_tables(file_path: str, page_range: str = "") -> str:
    """PDF에서 모든 표를 마크다운 표 형식으로 추출합니다.
    재무제표 등 숫자 테이블 추출에 최적화되어 있습니다.
    file_path: PDF 경로
    page_range: 페이지 범위 (예: '1-5' 또는 '3'). 비우면 전체."""
    with pdfplumber.open(file_path) as pdf:
        total = len(pdf.pages)

        if page_range:
            parts = page_range.split("-")
            start = int(parts[0]) - 1
            end = int(parts[-1]) if len(parts) > 1 else int(parts[0])
        else:
            start, end = 0, total

        start = max(0, start)
        end = min(end, total)

        results = [f"총 {total} 페이지 중 {start+1}-{end} 페이지 스캔\n"]
        table_count = 0

        for i in range(start, end):
            tables = pdf.pages[i].extract_tables()
            for j, table in enumerate(tables):
                table_count += 1
                if not table:
                    continue
                results.append(f"### Table {table_count} (Page {i+1})")
                # 헤더
                headers = table[0]
                results.append("| " + " | ".join(str(h) if h else "" for h in headers) + " |")
                results.append("| " + " | ".join("---" for _ in headers) + " |")
                # 행
                for row in table[1:]:
                    results.append("| " + " | ".join(str(c) if c else "" for c in row) + " |")
                results.append("")

        if table_count == 0:
            results.append("표가 감지되지 않았습니다. 텍스트에서 숫자 데이터를 추출합니다:\n")
            for i in range(start, end):
                text = pdf.pages[i].extract_text()
                if text:
                    for line in text.split("\n"):
                        if re.search(r"\d{1,3}(,\d{3})+|\d+\.\d+", line):
                            results.append(f"  Page {i+1}: {line}")

    return _truncate("\n".join(results))


@tool
def check_terminology(file_path: str, glossary_path: str) -> str:
    """문서의 용어 정확성을 용어집 기준으로 검증합니다.
    file_path: 검증할 문서 경로
    glossary_path: 용어집 PDF 경로"""
    glossary_text, _ = _extract_text(glossary_path)
    doc_text, _ = _extract_text(file_path)
    doc_lower = doc_text.lower()

    # 용어집에서 용어 추출 (번호. 용어명 패턴)
    term_pattern = re.compile(r"\d+\.\s+([A-Z][A-Za-z\s\-()]+?)(?:\n|Definition:)", re.MULTILINE)
    terms = term_pattern.findall(glossary_text)

    # "Common Error:" 패턴에서 오류 추출
    error_pattern = re.compile(r"Common Error:\s*Incorrect:\s*['\"](.+?)['\"]", re.MULTILINE)
    errors = error_pattern.findall(glossary_text)

    results = ["## 용어 검증 결과\n"]
    found = 0
    not_found = 0

    for term in terms:
        term = term.strip()
        if not term:
            continue
        abbr_match = re.search(r"\(([A-Z]{2,})\)", term)
        abbr = abbr_match.group(1) if abbr_match else None
        name = re.sub(r"\s*\([^)]*\)\s*", " ", term).strip()

        in_doc = name.lower() in doc_lower or (abbr and abbr in doc_text)
        if in_doc:
            found += 1
            results.append(f"- [FOUND] {term}")
        else:
            not_found += 1
            results.append(f"- [NOT FOUND] {term}")

    results.append(f"\n### 요약: {found}건 발견, {not_found}건 미발견")

    if errors:
        results.append("\n### 알려진 오류 목록")
        for e in errors:
            results.append(f"- {e}")

    return _truncate("\n".join(results))


# ─── 동적 Python 코드 실행 샌드박스 ───

_ALLOWED_MODULES = {
    "pdfplumber", "re", "difflib", "json", "csv", "math",
    "collections", "itertools", "functools",
    "datetime", "textwrap", "pathlib",
}

_SAFE_DIRS = [
    str(UPLOAD_DIR.resolve()),
    str(OUTPUT_DIR.resolve()),
]

_BUILTIN_IMPORT = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__


def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    """허용된 모듈만 import 가능한 제한된 __import__."""
    top_level = name.split(".")[0]
    allowed_tops = {m.split(".")[0] for m in _ALLOWED_MODULES}
    if top_level not in allowed_tops and name not in _ALLOWED_MODULES:
        raise ImportError(
            f"'{name}' 모듈은 샌드박스에서 사용할 수 없습니다. "
            f"허용 모듈: {sorted(_ALLOWED_MODULES)}"
        )
    return _BUILTIN_IMPORT(name, globals, locals, fromlist, level)


def _safe_open(path, mode="r", *args, **kwargs):
    """uploads/(읽기), output/(읽기/쓰기)만 허용하는 제한된 open."""
    resolved = os.path.realpath(path)
    if not any(resolved.startswith(d) for d in _SAFE_DIRS):
        raise PermissionError(
            f"접근 거부: {path}. uploads/ 와 output/ 만 접근 가능합니다."
        )
    if "w" in mode or "a" in mode:
        if not resolved.startswith(str(OUTPUT_DIR.resolve())):
            raise PermissionError(
                f"쓰기 거부: {path}. output/ 폴더에만 쓸 수 있습니다."
            )
    return open(path, mode, *args, **kwargs)


# os.path만 노출하는 제한된 os 프록시
class _RestrictedOS:
    path = _ospath


_SANDBOX_TIMEOUT = 30


@tool
def execute_python(code: str) -> str:
    """Python 코드를 실행합니다. 문서 검색, 비교, 조항 추출, 파일 저장 등
    기본 도구로 처리할 수 없는 작업에 사용하세요.

    사전 제공 변수: UPLOAD_DIR, OUTPUT_DIR, pdfplumber, re, difflib, json, csv, os.path, Path
    접근 가능 경로: uploads/ (읽기), output/ (읽기/쓰기)
    print()로 결과를 출력하거나 result 변수에 값을 할당하세요.

    code: 실행할 Python 코드 문자열"""
    stdout_capture = io.StringIO()

    sandbox_globals = {
        "__builtins__": {
            "print": lambda *a, **kw: print(*a, file=stdout_capture, **kw),
            "__import__": _safe_import,
            "open": _safe_open,
            # 기본 타입/함수
            "len": len, "range": range, "enumerate": enumerate,
            "zip": zip, "map": map, "filter": filter,
            "sorted": sorted, "reversed": reversed,
            "min": min, "max": max, "sum": sum, "abs": abs, "round": round,
            "int": int, "float": float, "str": str, "bool": bool,
            "list": list, "dict": dict, "set": set, "tuple": tuple,
            "isinstance": isinstance, "type": type,
            "True": True, "False": False, "None": None,
            "any": any, "all": all,
            "hasattr": hasattr, "getattr": getattr, "setattr": setattr,
            "repr": repr, "format": format, "chr": chr, "ord": ord,
            "bytes": bytes, "bytearray": bytearray,
            "ValueError": ValueError, "TypeError": TypeError,
            "KeyError": KeyError, "IndexError": IndexError,
            "Exception": Exception, "StopIteration": StopIteration,
            "RuntimeError": RuntimeError, "AttributeError": AttributeError,
            "FileNotFoundError": FileNotFoundError, "IOError": IOError,
            "PermissionError": PermissionError, "ImportError": ImportError,
            "iter": iter, "next": next, "callable": callable,
            "property": property, "staticmethod": staticmethod,
            "classmethod": classmethod, "super": super,
            "slice": slice, "frozenset": frozenset,
        },
        # 사전 import된 라이브러리
        "pdfplumber": pdfplumber,
        "re": re,
        "difflib": difflib,
        "json": __import__("json"),
        "csv": __import__("csv"),
        "os": _RestrictedOS(),
        "Path": Path,
        "UPLOAD_DIR": str(UPLOAD_DIR),
        "OUTPUT_DIR": str(OUTPUT_DIR),
    }

    def _timeout_handler(signum, frame):
        raise TimeoutError(f"코드 실행 시간 초과 ({_SANDBOX_TIMEOUT}초 제한)")

    try:
        compiled = compile(code, "<sandbox>", "exec")

        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(_SANDBOX_TIMEOUT)
        try:
            with contextlib.redirect_stdout(stdout_capture):
                exec(compiled, sandbox_globals)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

        stdout_result = stdout_capture.getvalue()

        if "result" in sandbox_globals and sandbox_globals["result"] is not None:
            result_val = str(sandbox_globals["result"])
            if stdout_result:
                return _truncate(stdout_result + "\n\n[result]:\n" + result_val)
            return _truncate(result_val)

        if stdout_result:
            return _truncate(stdout_result)

        return "(코드 실행 완료, 출력 없음)"

    except Exception:
        tb = traceback.format_exc()
        stdout_so_far = stdout_capture.getvalue()
        error_msg = f"[ERROR]\n{tb}"
        if stdout_so_far:
            error_msg = f"[PARTIAL OUTPUT]\n{stdout_so_far}\n\n{error_msg}"
        return _truncate(error_msg)
