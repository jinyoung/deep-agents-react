#!/usr/bin/env python3
"""
6개 유스케이스 E2E 테스트 스크립트.
백엔드(localhost:8000)가 실행 중이어야 합니다.
"""

import json
import sys
import time
import urllib.parse
from pathlib import Path

import httpx

BASE_URL = "http://localhost:8000"
SAMPLE_DIR = Path("sample_pdfs")
TIMEOUT = 180  # seconds per use case


def reset_session(client: httpx.Client, session_id: str):
    r = client.post(f"{BASE_URL}/api/session/reset", params={"session_id": session_id})
    assert r.status_code == 200, f"Reset failed: {r.text}"


def upload_files(client: httpx.Client, file_paths: list[Path], session_id: str):
    files = [("files", (f.name, f.read_bytes(), "application/pdf")) for f in file_paths]
    r = client.post(f"{BASE_URL}/api/upload", files=files, data={"session_id": session_id})
    assert r.status_code == 200, f"Upload failed: {r.text}"
    return r.json()


def run_prompt(client: httpx.Client, prompt: str, session_id: str) -> dict:
    """SSE 스트림을 읽어 이벤트를 수집하고 결과를 반환."""
    encoded = urllib.parse.quote(prompt)
    url = f"{BASE_URL}/api/stream?prompt={encoded}&session_id={session_id}"

    events = []
    tokens_text = []
    tool_names = []
    errors = []
    output_files = []

    with client.stream("GET", url, timeout=TIMEOUT) as resp:
        buf = ""
        for chunk in resp.iter_text():
            buf += chunk
            while "\n\n" in buf:
                raw, buf = buf.split("\n\n", 1)
                lines = raw.strip().split("\n")
                event_type = ""
                data_str = ""
                for line in lines:
                    if line.startswith("event:"):
                        event_type = line[6:].strip()
                    elif line.startswith("data:"):
                        data_str = line[5:].strip()
                if not event_type:
                    continue
                try:
                    data = json.loads(data_str) if data_str else {}
                except json.JSONDecodeError:
                    data = {"raw": data_str}

                events.append({"event": event_type, "data": data})

                if event_type == "token":
                    tokens_text.append(data.get("text", ""))
                elif event_type == "tool_start":
                    tool_names.append(data.get("name", ""))
                elif event_type == "error":
                    errors.append(data.get("message", ""))
                elif event_type == "done":
                    output_files = data.get("files", [])

    return {
        "events": events,
        "text": "".join(tokens_text),
        "tools_used": tool_names,
        "errors": errors,
        "output_files": output_files,
    }


def check_output_file(client: httpx.Client, filename: str, keywords: list[str]) -> tuple[bool, str]:
    """output 파일을 다운로드하여 키워드 포함 여부 확인."""
    r = client.get(f"{BASE_URL}/api/download/{filename}")
    if r.status_code != 200:
        return False, f"파일 다운로드 실패: {filename}"
    content = r.text.lower()
    missing = [kw for kw in keywords if kw.lower() not in content]
    if missing:
        return False, f"누락 키워드: {missing}"
    return True, "OK"


# ─── 유스케이스 테스트 ───


def test_case_1(client: httpx.Client) -> dict:
    """UC1: 원전 용어 Q&A (10건)"""
    session = "test_uc1"
    reset_session(client, session)
    upload_files(client, [SAMPLE_DIR / "Nuclear_Power_Terminology_Reference.pdf"], session)

    result = run_prompt(
        client,
        "업로드된 Nuclear_Power_Terminology_Reference.pdf 파일을 read_pdf로 읽고, "
        "용어집에 포함된 10개 원전 용어에 대해 Q&A 형식으로 정리하세요. "
        "각 용어의 정의, 사용 예시, 흔한 오류를 포함하세요. "
        "결과를 마크다운 파일로 저장하세요.",
        session,
    )
    return result


def test_case_2(client: httpx.Client) -> dict:
    """UC2: 감사보고서 재무제표 정리"""
    session = "test_uc2"
    reset_session(client, session)
    upload_files(client, [SAMPLE_DIR / "SAPCO_2024_Audit_Report.pdf"], session)

    result = run_prompt(
        client,
        "감사보고서에서 재무제표(재무상태표, 손익계산서, 현금흐름표)를 추출하여 "
        "한글로 정리해 주세요. 마크다운으로 저장하세요.",
        session,
    )
    return result


def test_case_3(client: httpx.Client) -> dict:
    """UC3: 2개 EPC 계약서 조항 비교"""
    session = "test_uc3"
    reset_session(client, session)
    upload_files(client, [
        SAMPLE_DIR / "EPC_Contract_ProjectAlpha.pdf",
        SAMPLE_DIR / "EPC_Contract_ProjectBeta.pdf",
    ], session)

    result = run_prompt(
        client,
        "두 EPC 계약서(Project Alpha, Project Beta)의 주요 조항을 비교해 주세요. "
        "특히 지체상금(Liquidated Damages), 보증기간(Warranty), "
        "분쟁해결(Dispute Resolution) 조항을 중심으로 비교표를 작성하세요.",
        session,
    )
    return result


def test_case_4(client: httpx.Client) -> dict:
    """UC4: O&M 계약서 지식검색"""
    session = "test_uc4"
    reset_session(client, session)
    upload_files(client, [SAMPLE_DIR / "Service_Agreement_OMContract.pdf"], session)

    result = run_prompt(
        client,
        "O&M 계약서에서 성과보증(Performance Guarantee) 관련 조항과 "
        "SLA 기준을 검색하여 정리해 주세요. 마크다운으로 저장하세요.",
        session,
    )
    return result


def test_case_5(client: httpx.Client) -> dict:
    """UC5: 기술 라이선스 계약서 지식검색"""
    session = "test_uc5"
    reset_session(client, session)
    upload_files(client, [SAMPLE_DIR / "Technology_License_Agreement.pdf"], session)

    result = run_prompt(
        client,
        "기술 라이선스 계약서에서 로열티 구조(Royalty)와 "
        "수출통제(Export Control) 관련 조항을 검색하여 정리해 주세요. 마크다운으로 저장하세요.",
        session,
    )
    return result


def test_case_6(client: httpx.Client) -> dict:
    """UC6: NDA 자문 (과거사례 기반)"""
    session = "test_uc6"
    reset_session(client, session)
    upload_files(client, [
        SAMPLE_DIR / "NDA_Advisory_CaseHistory.pdf",
        SAMPLE_DIR / "NDA_Draft_NewProject.pdf",
    ], session)

    result = run_prompt(
        client,
        "과거 NDA 자문 사례를 참고하여, 신규 NDA 초안의 문제점을 분석하고 "
        "수정의견을 제시해 주세요. 과거 사례별 수정 근거도 포함하세요. "
        "마크다운으로 저장하세요.",
        session,
    )
    return result


# ─── 메인 ───


def main():
    print("=" * 60)
    print("  ReAct Agent - 6 Use Cases E2E Test")
    print("=" * 60)

    client = httpx.Client(timeout=TIMEOUT)

    # 서버 상태 확인
    try:
        r = client.get(f"{BASE_URL}/api/files")
        assert r.status_code == 200
    except Exception as e:
        print(f"\n[ERROR] 백엔드 연결 실패: {e}")
        print(f"  먼저 python backend.py 를 실행하세요.")
        sys.exit(1)

    tests = [
        ("UC1: 원전 용어 Q&A", test_case_1),
        ("UC2: 감사보고서 재무제표", test_case_2),
        ("UC3: 계약서 조항 비교", test_case_3),
        ("UC4: O&M 지식검색", test_case_4),
        ("UC5: 라이선스 지식검색", test_case_5),
        ("UC6: NDA 자문", test_case_6),
    ]

    results = {}
    for name, test_fn in tests:
        print(f"\n{'─' * 50}")
        print(f"  {name}")
        print(f"{'─' * 50}")

        start = time.time()
        try:
            result = test_fn(client)
            elapsed = time.time() - start

            has_errors = len(result["errors"]) > 0
            has_tools = len(result["tools_used"]) > 0
            has_output = len(result["output_files"]) > 0

            status = "FAIL" if has_errors else ("PASS" if has_output else "WARN")

            print(f"  Status: {status}")
            print(f"  Time: {elapsed:.1f}s")
            print(f"  Tools: {', '.join(result['tools_used']) or 'none'}")
            print(f"  Output: {', '.join(result['output_files']) or 'none'}")
            if has_errors:
                print(f"  Errors: {result['errors']}")
            if result["text"]:
                preview = result["text"][:200].replace("\n", " ")
                print(f"  AI Text: {preview}...")

            results[name] = status
        except Exception as e:
            elapsed = time.time() - start
            print(f"  Status: ERROR")
            print(f"  Time: {elapsed:.1f}s")
            print(f"  Exception: {e}")
            results[name] = "ERROR"

    # 최종 요약
    print(f"\n{'=' * 60}")
    print("  SUMMARY")
    print(f"{'=' * 60}")
    for name, status in results.items():
        icon = {"PASS": "OK", "WARN": "!!", "FAIL": "XX", "ERROR": "!!"}[status]
        print(f"  [{icon}] {name}: {status}")

    passed = sum(1 for s in results.values() if s == "PASS")
    total = len(results)
    print(f"\n  {passed}/{total} passed")
    print(f"{'=' * 60}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
