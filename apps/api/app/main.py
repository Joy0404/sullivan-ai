import asyncio
import os
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.demo import build_demo_package
from app.core.demo_gate import (
    CONSENT_MESSAGE,
    KEY_MISSING_MESSAGE,
    SAMPLE_ONLY_MESSAGE,
    DemoGateError,
    allowed_sample_video_ids,
    analysis_timeout_seconds,
    check_access_code,
    client_ip,
    limiter,
    server_gemini_key,
)
from app.adapters.video_link import (
    LinkAnalyzerError,
    UnsafeVideoLinkError,
    analyze_uploaded_video_with_gemini,
    analyze_video_link,
    normalize_video_link,
    youtube_video_id,
)
from app.adapters.gemini_agent import (
    AgentTurnError,
    AgentUnavailableError,
    run_agent_turn,
)
from app.core.lecture_agent import LectureAgent, LectureNotFoundError
from app.models import (
    AnalysisPackageInput,
    AgentTurnInput,
    AgentTurnResponse,
    AssetInput,
    AssetRecord,
    LectureCreate,
    LectureSession,
    LectureSnapshot,
    NavigationRequest,
    NavigationResponse,
    VideoFileAnalysisResult,
    VideoLinkInput,
    VideoLinkResult,
)


DEFAULT_MAX_UPLOAD_VIDEO_BYTES = 100 * 1024 * 1024
TIMEOUT_MESSAGE = "분석 시간이 3분을 넘어 중단했어요. 분석 결과는 만들어지지 않았습니다."
CLEANUP_FAILED_NOTE = (
    "업로드한 임시 영상의 삭제를 확인하지 못했습니다. "
    "Gemini에 올라간 사본은 공급자 정책에 따라 최대 48시간 뒤 자동 삭제됩니다."
)


def _gate_http_error(error: DemoGateError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.message)


def _delete_temporary_file(path: str) -> bool:
    """Delete the local temporary copy; True when nothing is left behind."""
    if not path:
        return True
    try:
        os.unlink(path)
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return True


app = FastAPI(
    title="Sullivan AI Internet Lecture Accessibility Agent API",
    version="1.0.0-mvp",
    description=(
        "인터넷 강의의 음성과 화면을 비교해 시각적으로만 전달된 정보를 "
        "설명하고, 긴 지문을 비시각적으로 탐색하게 하는 대회용 MVP"
    ),
)
agent = LectureAgent()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_origin_regex=r"^http://(?:localhost|127\.0\.0\.1):\d+$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "product": "sullivan-ai-internet-lecture-agent",
        "project_stage": "competition-mvp",
        "analysis_mode": os.getenv("ANALYSIS_MODE", "local-agent-demo"),
        "raw_video_storage": "disabled",
        "uploaded_video_analysis": "explicit-consent-gemini",
        "temporary_media_retention": "deleted-after-analysis",
        "youtube_link_analysis": "configured" if os.getenv("GEMINI_API_KEY") else "needs-api-key",
        "agent_reasoning": "configured" if os.getenv("GEMINI_API_KEY") else "needs-api-key",
        "visual_verification": "gemini-two-pass" if os.getenv("GEMINI_API_KEY") else "needs-api-key",
        "external_link_analysis": "configured" if os.getenv("LINK_ANALYZER_URL") else "optional",
        "real_analysis_access": (
            "trial-code-required"
            if os.getenv("DEMO_ACCESS_CODE") and os.getenv("GEMINI_API_KEY")
            else "disabled"
        ),
        "daily_trial_limit": str(limiter.limit()),
    }


@app.post("/v1/lectures", response_model=LectureSession, status_code=201)
def create_lecture(payload: LectureCreate) -> LectureSession:
    return agent.create_session(payload)


@app.post(
    "/v1/lectures/{session_id}/assets",
    response_model=AssetRecord,
    status_code=201,
)
def register_asset(session_id: str, payload: AssetInput) -> AssetRecord:
    try:
        return agent.register_asset(session_id, payload)
    except LectureNotFoundError as error:
        raise HTTPException(status_code=404, detail="강의 세션을 찾을 수 없습니다.") from error


@app.post("/v1/lectures/{session_id}/video-link", response_model=VideoLinkResult)
async def register_video_link(
    session_id: str, payload: VideoLinkInput, request: Request
) -> VideoLinkResult:
    if not payload.rights_confirmed:
        raise HTTPException(status_code=400, detail="영상 이용·분석 권한 확인이 필요합니다.")
    try:
        session = agent.snapshot(session_id).session
        link = normalize_video_link(payload.url)
        asset_id = f"video-link-{uuid4().hex[:10]}"
        asset = agent.register_asset(
            session_id,
            AssetInput(
                asset_id=asset_id,
                name="링크 강의 영상",
                kind="video_link",
                media_type="text/uri-list",
                metadata={"url": link.normalized_url, "playback_kind": link.playback_kind},
            ),
        )
        if not payload.request_analysis:
            return VideoLinkResult(
                asset=asset,
                normalized_url=link.normalized_url,
                playback_kind=link.playback_kind,
                playback_url=link.playback_url,
                analysis_status="registered-only",
                message="링크를 재생 소스로 등록했습니다. AI 분석은 요청하지 않았습니다.",
            )
        api_key = server_gemini_key()
        needs_adapter = VideoLinkResult(
            asset=asset,
            normalized_url=link.normalized_url,
            playback_kind=link.playback_kind,
            playback_url=link.playback_url,
            analysis_status="needs-adapter",
            message=f"링크 재생은 준비되었습니다. {KEY_MISSING_MESSAGE}",
        )
        if not api_key:
            return needs_adapter
        if not payload.analysis_consent:
            raise HTTPException(status_code=400, detail=CONSENT_MESSAGE)
        if youtube_video_id(link.normalized_url) not in allowed_sample_video_ids():
            raise HTTPException(status_code=400, detail=SAMPLE_ONLY_MESSAGE)
        check_access_code(
            payload.access_code.get_secret_value() if payload.access_code else None
        )
        limiter.consume(client_ip(request))
        try:
            analysis = await asyncio.wait_for(
                analyze_video_link(
                    link.normalized_url,
                    title=session.title,
                    subject=session.subject,
                    problem_mode=session.problem_mode,
                    api_key_override=api_key,
                ),
                timeout=analysis_timeout_seconds(),
            )
        except asyncio.TimeoutError as error:
            raise HTTPException(status_code=504, detail=TIMEOUT_MESSAGE) from error
        if analysis is None:
            return needs_adapter
        snapshot = agent.analyze(session_id, analysis)
        indexed_asset = agent.mark_asset_indexed(session_id, asset_id)
        snapshot = agent.snapshot(session_id)
        return VideoLinkResult(
            asset=indexed_asset,
            normalized_url=link.normalized_url,
            playback_kind=link.playback_kind,
            playback_url=link.playback_url,
            analysis_status="completed",
            message="Gemini의 장면 분석과 독립 시각 근거 재검증을 완료했습니다.",
            snapshot=snapshot,
        )
    except LectureNotFoundError as error:
        raise HTTPException(status_code=404, detail="강의 세션을 찾을 수 없습니다.") from error
    except UnsafeVideoLinkError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except DemoGateError as error:
        raise _gate_http_error(error) from error
    except LinkAnalyzerError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.post(
    "/v1/lectures/{session_id}/video-file-analysis",
    response_model=VideoFileAnalysisResult,
)
async def analyze_uploaded_video_file(
    session_id: str,
    request: Request,
    video: UploadFile = File(...),
    asset_id: str = Form(...),
    rights_confirmed: bool = Form(False),
    cloud_analysis_consent: bool = Form(False),
    access_code: str = Form(""),
) -> VideoFileAnalysisResult:
    """Analyze one local video only after separate, explicit cloud consent.

    Real analysis also needs the trial code and an unused daily allowance. The
    raw file exists only in a temporary local path while it is relayed to
    Gemini. Both the provider copy and the local temporary file are deleted as
    soon as the analysis attempt finishes (success, failure or timeout), and a
    failed deletion is reported instead of being shown as a clean finish. Only
    the server's own Gemini key is used.
    """

    if not rights_confirmed:
        raise HTTPException(status_code=400, detail="영상 이용·분석 권한 확인이 필요합니다.")
    if not cloud_analysis_consent:
        raise HTTPException(
            status_code=400,
            detail="로컬 원본을 Gemini에 임시 전송해 분석하는 데 별도 동의가 필요합니다.",
        )

    try:
        snapshot = agent.snapshot(session_id)
    except LectureNotFoundError as error:
        raise HTTPException(status_code=404, detail="강의 세션을 찾을 수 없습니다.") from error

    matching_asset = next(
        (
            item
            for item in snapshot.assets
            if item.asset_id == asset_id and item.kind == "video"
        ),
        None,
    )
    if matching_asset is None:
        raise HTTPException(status_code=400, detail="먼저 같은 영상의 로컬 자산을 등록해 주세요.")

    api_key = server_gemini_key()
    if not api_key:
        raise HTTPException(status_code=503, detail=KEY_MISSING_MESSAGE)
    ip = client_ip(request)
    try:
        check_access_code(access_code)
        limiter.ensure_available(ip)
    except DemoGateError as error:
        raise _gate_http_error(error) from error

    mime_type = (video.content_type or "").lower()
    suffix_by_type = {
        "video/mp4": ".mp4",
        "video/webm": ".webm",
        "video/quicktime": ".mov",
        "video/x-m4v": ".m4v",
    }
    if mime_type not in suffix_by_type:
        extension_to_type = {
            ".mp4": "video/mp4",
            ".webm": "video/webm",
            ".mov": "video/quicktime",
            ".m4v": "video/x-m4v",
        }
        mime_type = extension_to_type.get(
            os.path.splitext(video.filename or "")[1].lower(), mime_type
        )
    if mime_type not in suffix_by_type:
        raise HTTPException(
            status_code=415,
            detail="직접 AI 분석은 MP4, WebM, MOV 또는 M4V 영상만 지원합니다.",
        )

    try:
        maximum_bytes = int(
            os.getenv("MAX_UPLOAD_VIDEO_BYTES", str(DEFAULT_MAX_UPLOAD_VIDEO_BYTES))
        )
    except ValueError:
        maximum_bytes = DEFAULT_MAX_UPLOAD_VIDEO_BYTES

    temporary_path = ""
    cleanup_report: dict[str, str] = {}
    analysis: AnalysisPackageInput | None = None
    remaining_trials: int | None = None
    failure: HTTPException | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix="sullivan-video-",
            suffix=suffix_by_type[mime_type],
            delete=False,
        ) as temporary_file:
            temporary_path = temporary_file.name
            received_bytes = 0
            while chunk := await video.read(1024 * 1024):
                received_bytes += len(chunk)
                if received_bytes > maximum_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "영상이 업로드 크기 제한을 넘어 분석하지 않았습니다. "
                            f"현재 제한은 {maximum_bytes // (1024 * 1024)}MB입니다."
                        ),
                    )
                temporary_file.write(chunk)

        if received_bytes == 0:
            raise HTTPException(status_code=400, detail="빈 영상 파일은 분석할 수 없습니다.")

        remaining_trials = limiter.consume(ip)
        analysis = await asyncio.wait_for(
            analyze_uploaded_video_with_gemini(
                temporary_path,
                display_name=os.path.basename(video.filename or "uploaded-video"),
                mime_type=mime_type,
                title=snapshot.session.title,
                subject=snapshot.session.subject,
                problem_mode=snapshot.session.problem_mode,
                api_key=api_key,
                cleanup_report=cleanup_report,
            ),
            timeout=analysis_timeout_seconds(),
        )
    except asyncio.TimeoutError:
        failure = HTTPException(status_code=504, detail=TIMEOUT_MESSAGE)
    except DemoGateError as error:
        failure = _gate_http_error(error)
    except LinkAnalyzerError as error:
        failure = HTTPException(status_code=502, detail=str(error))
    except HTTPException as error:
        failure = error
    finally:
        await video.close()
        # os.unlink(temporary_path) runs here on every path, timeouts included.
        local_deleted = _delete_temporary_file(temporary_path)

    cleanup_failed = (
        not local_deleted or cleanup_report.get("provider") == "delete-failed"
    )
    if failure is not None or analysis is None:
        failure = failure or HTTPException(
            status_code=502, detail="Gemini 영상 분석 결과를 받지 못했습니다."
        )
        if cleanup_failed:
            failure.detail = f"{failure.detail} {CLEANUP_FAILED_NOTE}"
        raise failure

    agent.analyze(session_id, analysis)
    agent.mark_asset_indexed(
        session_id,
        asset_id,
        note=(
            "명시적 동의에 따라 Gemini로 실제 발화·화면을 분석하고 "
            "독립 시각 근거 재검증을 완료했습니다. 원본은 저장하지 않습니다."
        ),
    )
    return VideoFileAnalysisResult.model_validate(
        {
            **agent.snapshot(session_id).model_dump(),
            "cleanup_status": "delete-failed" if cleanup_failed else "deleted",
            "cleanup_message": CLEANUP_FAILED_NOTE if cleanup_failed else "",
            "remaining_trials": remaining_trials,
        }
    )


@app.post(
    "/v1/lectures/{session_id}/analysis",
    response_model=LectureSnapshot,
)
def analyze_lecture(
    session_id: str, payload: AnalysisPackageInput
) -> LectureSnapshot:
    try:
        return agent.analyze(session_id, payload)
    except LectureNotFoundError as error:
        raise HTTPException(status_code=404, detail="강의 세션을 찾을 수 없습니다.") from error


@app.post(
    "/v1/lectures/{session_id}/demo-analysis",
    response_model=LectureSnapshot,
)
def run_demo_analysis(session_id: str) -> LectureSnapshot:
    """Load the deterministic stellar-evolution sample; never claim live analysis."""
    try:
        snapshot = agent.analyze(session_id, build_demo_package())
        for asset in snapshot.assets:
            if asset.kind == "video_link":
                agent.mark_asset_indexed(
                    session_id,
                    asset.asset_id,
                    note=(
                        "별의 진화 샘플용으로 사전에 준비한 접근성 분석입니다. "
                        "이 실행에서 영상을 새로 분석하지 않았습니다."
                    ),
                )
        return agent.snapshot(session_id)
    except LectureNotFoundError as error:
        raise HTTPException(status_code=404, detail="강의 세션을 찾을 수 없습니다.") from error


@app.get("/v1/lectures/{session_id}", response_model=LectureSnapshot)
def get_lecture(session_id: str) -> LectureSnapshot:
    try:
        return agent.snapshot(session_id)
    except LectureNotFoundError as error:
        raise HTTPException(status_code=404, detail="강의 세션을 찾을 수 없습니다.") from error


@app.post("/v1/lectures/{session_id}/agent-turn", response_model=AgentTurnResponse)
async def run_lecture_agent_turn(
    session_id: str, payload: AgentTurnInput
) -> AgentTurnResponse:
    """Observe lecture context, choose one tool action, then return a safe plan.

    The server's Gemini key is used only with a valid trial code; otherwise the
    browser falls back to its local assistant.
    """

    try:
        snapshot = agent.snapshot(session_id)
    except LectureNotFoundError:
        # Prebuilt samples are client-side and truthfully labelled as such. They
        # may provide only their existing accessibility snapshot, never video.
        if payload.snapshot is None:
            raise HTTPException(status_code=404, detail="강의 세션을 찾을 수 없습니다.")
        snapshot = payload.snapshot
    if server_gemini_key():
        try:
            check_access_code(
                payload.access_code.get_secret_value() if payload.access_code else None
            )
        except DemoGateError as error:
            raise HTTPException(
                status_code=error.status_code,
                detail=f"{error.message} 로컬 보조 모드로 답합니다.",
            ) from error
    try:
        return await run_agent_turn(
            snapshot,
            message=payload.message,
            current_time_ms=payload.current_time_ms,
        )
    except AgentUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except AgentTurnError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.post(
    "/v1/lectures/{session_id}/navigate",
    response_model=NavigationResponse,
)
def navigate_lecture(
    session_id: str, payload: NavigationRequest
) -> NavigationResponse:
    try:
        return agent.navigate(
            session_id, payload.command, payload.current_sentence_id
        )
    except LectureNotFoundError as error:
        raise HTTPException(status_code=404, detail="강의 세션을 찾을 수 없습니다.") from error


@app.post("/v1/lectures/{session_id}/end", response_model=LectureSession)
def end_lecture(session_id: str) -> LectureSession:
    try:
        return agent.end(session_id)
    except LectureNotFoundError as error:
        raise HTTPException(status_code=404, detail="강의 세션을 찾을 수 없습니다.") from error


# Serve the web app from the same origin so the browser calls the API with
# relative paths. Mounted last so every API route above takes precedence.
WEB_DIR = Path(os.getenv("WEB_DIR", str(Path(__file__).resolve().parents[2] / "web")))
if WEB_DIR.is_dir():
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
