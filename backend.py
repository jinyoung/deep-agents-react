"""
FastAPI 백엔드 — LangGraph ReAct Agent + SSE 스트리밍
Docker 없이 로컬에서 PDF 읽기 + 마크다운 생성
"""

import asyncio
import json
import os
import re
import shutil
import threading
import unicodedata
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

load_dotenv()

UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", "uploads"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "output"))
BACKEND_HOST = os.environ.get("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.environ.get("BACKEND_PORT", "8000"))

_agent = None
_sessions: dict[str, list] = {}

SYSTEM_PROMPT = (
    "한국어로 응답하세요.\n"
    "당신은 문서 분석 전문가입니다. 해외 원전사업, 계약서, 재무제표, NDA 자문 등을 전문으로 합니다.\n\n"
    "## 사용 가능한 도구\n\n"
    "### 기본 도구\n"
    "- list_uploads: 업로드된 파일 목록 확인. **항상 먼저 호출하세요.**\n"
    "- read_pdf: PDF에서 텍스트/테이블 추출. file_path는 'uploads/파일명.pdf' 형식.\n"
    "- extract_tables: PDF에서 표를 마크다운 형식으로 추출. 재무제표에 활용.\n"
    "- check_terminology: 문서의 용어 정확성을 용어집 기준으로 검증.\n\n"
    "### execute_python (동적 코드 실행)\n"
    "기본 도구로 처리할 수 없는 작업은 Python 코드를 작성하여 실행하세요.\n"
    "다음과 같은 작업에 사용합니다:\n"
    "- **문서 검색**: PDF에서 키워드/구문 검색\n"
    "- **문서 비교**: 2개 문서의 diff 비교\n"
    "- **조항 추출**: 계약서에서 특정 Article/Section/Clause 추출\n"
    "- **파일 저장**: 결과를 output/ 폴더에 마크다운으로 저장\n"
    "- **데이터 가공**: 텍스트 파싱, 정규식, 집계 등\n\n"
    "#### execute_python 사용법\n"
    "```\n"
    "execute_python(code=\"\"\"\n"
    "# 사전 제공 변수: UPLOAD_DIR, OUTPUT_DIR\n"
    "# 사전 import: pdfplumber, re, difflib, json, csv, os.path, Path\n"
    "# print()로 결과 출력 또는 result 변수에 값 할당\n"
    "with pdfplumber.open(f'{UPLOAD_DIR}/파일명.pdf') as pdf:\n"
    "    text = '\\n'.join(p.extract_text() or '' for p in pdf.pages)\n"
    "print(text[:2000])\n"
    "\"\"\")\n"
    "```\n\n"
    "#### 자주 사용하는 코드 패턴\n\n"
    "**키워드 검색:**\n"
    "```python\n"
    "with pdfplumber.open(f'{UPLOAD_DIR}/파일.pdf') as pdf:\n"
    "    for i, page in enumerate(pdf.pages):\n"
    "        text = page.extract_text() or ''\n"
    "        if '검색어' in text.lower():\n"
    "            print(f'Page {i+1}: {text[:500]}')\n"
    "```\n\n"
    "**2개 문서 비교:**\n"
    "```python\n"
    "with pdfplumber.open(f'{UPLOAD_DIR}/a.pdf') as pa, pdfplumber.open(f'{UPLOAD_DIR}/b.pdf') as pb:\n"
    "    ta = '\\n'.join(p.extract_text() or '' for p in pa.pages)\n"
    "    tb = '\\n'.join(p.extract_text() or '' for p in pb.pages)\n"
    "diff = '\\n'.join(difflib.unified_diff(ta.splitlines(), tb.splitlines(), lineterm=''))\n"
    "print(diff[:5000])\n"
    "```\n\n"
    "**마크다운 저장:**\n"
    "```python\n"
    "content = '# 보고서\\n\\n내용...'\n"
    "with open(f'{OUTPUT_DIR}/report.md', 'w', encoding='utf-8') as f:\n"
    "    f.write(content)\n"
    "print(f'저장 완료: {OUTPUT_DIR}/report.md ({len(content)} chars)')\n"
    "```\n\n"
    "**조항 추출:**\n"
    "```python\n"
    "with pdfplumber.open(f'{UPLOAD_DIR}/contract.pdf') as pdf:\n"
    "    text = '\\n'.join(p.extract_text() or '' for p in pdf.pages)\n"
    "pattern = re.compile(r'^(Article|Section|Clause)\\s+\\d+[^\\n]*', re.MULTILINE | re.IGNORECASE)\n"
    "matches = pattern.findall(text)\n"
    "result = '\\n'.join(matches)\n"
    "```\n\n"
    "## 유스케이스별 가이드\n\n"
    "### 용어 Q&A\n"
    "list_uploads → read_pdf(용어집) → check_terminology → 결과 정리 → execute_python(저장)\n\n"
    "### 재무제표 정리\n"
    "list_uploads → extract_tables(감사보고서) → read_pdf(주석 확인) → execute_python(저장)\n\n"
    "### 계약서 조항 비교\n"
    "list_uploads → execute_python(조항 추출) → execute_python(diff 비교) → execute_python(저장)\n\n"
    "### 계약서 지식검색\n"
    "list_uploads → execute_python(키워드 검색) → execute_python(조항 추출) → execute_python(저장)\n\n"
    "### NDA 자문\n"
    "list_uploads → read_pdf(과거 사례) → read_pdf(신규 NDA) → execute_python(비교) → execute_python(저장)\n\n"
    "## 일반 규칙\n"
    "1. 항상 list_uploads부터 시작하세요.\n"
    "2. 경로는 list_uploads 결과에 나온 경로를 그대로 사용하세요.\n"
    "3. 각 단계 전에 무엇을 할지 간단히 설명하세요.\n"
    "4. 최종 결과는 execute_python으로 output/ 폴더에 마크다운으로 저장하세요.\n"
    "5. 표 데이터는 마크다운 표(|---|) 형식으로 변환하세요.\n"
    "6. execute_python 에러 시 에러 메시지를 읽고 코드를 수정하여 재실행하세요."
)


def get_agent():
    global _agent
    if _agent is not None:
        return _agent

    from langchain_openai import ChatOpenAI
    from langgraph.prebuilt import create_react_agent

    from tools import (
        check_terminology,
        execute_python,
        extract_tables,
        list_uploads,
        read_pdf,
    )

    llm = ChatOpenAI(
        model=os.environ.get("OPENAI_MODEL", "frentis-ai-model"),
        base_url=os.environ.get("OPENAI_BASE_URL", "") or None,
        api_key=os.environ.get("OPENAI_API_KEY", ""),
        temperature=0,
        streaming=False,
    )

    _agent = create_react_agent(
        model=llm,
        tools=[
            list_uploads, read_pdf, extract_tables, check_terminology,
            execute_python,
        ],
        prompt=SYSTEM_PROMPT,
    )
    return _agent


# ─── FastAPI ───

@asynccontextmanager
async def lifespan(app: FastAPI):
    UPLOAD_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    get_agent()
    yield


app = FastAPI(title="ReAct Agent (Simple)", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ─── 파일 업로드 (로컬) ───

@app.post("/api/upload")
async def upload_files(files: list[UploadFile] = File(...), session_id: str = Form("")):
    uploaded = []
    for f in files:
        content = await f.read()
        filename = unicodedata.normalize("NFC", f.filename or "unknown")
        path = UPLOAD_DIR / filename
        path.write_bytes(content)
        uploaded.append({"name": filename, "path": str(path), "size": len(content)})
    return {"uploaded": uploaded}


# ─── 파일 목록 ───

@app.get("/api/files")
async def list_files():
    def scan(d: Path):
        if not d.exists():
            return []
        return [{"name": f.name, "size": f"{f.stat().st_size / 1024:.1f}K"} for f in d.iterdir() if f.is_file()]
    return {"uploads": scan(UPLOAD_DIR), "output": scan(OUTPUT_DIR)}


# ─── 파일 다운로드 ───

@app.get("/api/download/{filename:path}")
async def download_file(filename: str):
    path = OUTPUT_DIR / filename
    if path.exists():
        return FileResponse(str(path), media_type="application/octet-stream", filename=path.name)
    return {"error": f"파일을 찾을 수 없습니다: {filename}"}


# ─── SSE 스트리밍 ───

_SENTINEL = object()


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _run_agent(prompt: str, session_id: str, aq: asyncio.Queue, loop: asyncio.AbstractEventLoop):
    try:
        ag = get_agent()
        history = _sessions.setdefault(session_id, [])
        history.append(HumanMessage(content=prompt))

        for event in ag.stream({"messages": list(history)}, stream_mode="updates"):
            loop.call_soon_threadsafe(aq.put_nowait, event)
    except Exception as e:
        loop.call_soon_threadsafe(aq.put_nowait, {"__error__": str(e)})
    finally:
        loop.call_soon_threadsafe(aq.put_nowait, _SENTINEL)


async def _generate_sse(prompt: str, session_id: str):
    aq: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    thread = threading.Thread(target=_run_agent, args=(prompt, session_id, aq, loop), daemon=True)
    thread.start()

    yield _sse("status", {"message": "에이전트 실행 시작..."})

    seen_refs = set()

    while True:
        item = await aq.get()
        if item is _SENTINEL:
            break
        if isinstance(item, dict) and "__error__" in item:
            yield _sse("error", {"message": item["__error__"]})
            break

        for node_name, node_data in item.items():
            if node_name.startswith("__"):
                continue
            if not isinstance(node_data, dict) or "messages" not in node_data:
                continue

            messages = node_data["messages"]
            if hasattr(messages, "value"):
                messages = messages.value
            if not isinstance(messages, list):
                messages = [messages] if messages else []

            for msg in messages:
                if isinstance(msg, AIMessage):
                    if msg.content:
                        text = msg.content if isinstance(msg.content, str) else str(msg.content)
                        if text.strip() and not text.startswith("<|"):
                            yield _sse("token", {"text": text, "node": node_name})
                    if msg.tool_calls:
                        for tc in msg.tool_calls:
                            yield _sse("tool_start", {
                                "tool_call_id": tc.get("id", ""),
                                "name": tc.get("name", ""),
                                "node": node_name,
                            })

                elif isinstance(msg, ToolMessage):
                    content = msg.content if isinstance(msg.content, str) else str(msg.content)

                    # 참조 파일 감지
                    for fm in re.findall(r"uploads/[^'\"\]\n,]+", content):
                        fname = fm.replace("uploads/", "")
                        if fname and fname not in seen_refs:
                            seen_refs.add(fname)
                            yield _sse("ref_file", {"name": fname, "path": fm})

                    yield _sse("tool_result", {
                        "tool_call_id": msg.tool_call_id or "",
                        "name": msg.name or "",
                        "content": content[:3000],
                        "node": node_name,
                    })

    # output 파일 목록
    out_files = [f.name for f in OUTPUT_DIR.iterdir() if f.is_file()] if OUTPUT_DIR.exists() else []
    yield _sse("done", {"message": "완료!", "files": out_files})


@app.get("/api/stream")
async def stream_endpoint(prompt: str = "", session_id: str = "default"):
    if not prompt:
        return {"error": "prompt is required"}
    return StreamingResponse(
        _generate_sse(prompt, session_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@app.post("/api/session/reset")
async def reset_session(session_id: str = "default"):
    _sessions.pop(session_id, None)
    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    shutil.rmtree(UPLOAD_DIR, ignore_errors=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(exist_ok=True)
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=BACKEND_HOST, port=BACKEND_PORT)
