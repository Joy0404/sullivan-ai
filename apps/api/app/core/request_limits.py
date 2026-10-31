"""Bound multipart request bodies before the parser can spool unlimited media."""

import json

from starlette.formparsers import MultiPartException

from app.core.demo_gate import MAX_VIDEO_BYTES


class UploadBodyLimit:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope.get("path", "").endswith(
            "/video-file-analysis"
        ):
            return await self.app(scope, receive, send)
        limit = MAX_VIDEO_BYTES + 1024 * 1024  # bounded multipart envelope
        headers = dict(scope.get("headers", []))
        try:
            too_large = int(headers.get(b"content-length", b"0")) > limit
        except ValueError:
            too_large = True

        async def reject():
            body = json.dumps(
                {"detail": "업로드 영상은 100MB 이하여야 합니다."}, ensure_ascii=False
            ).encode()
            await send(
                {
                    "type": "http.response.start",
                    "status": 413,
                    "headers": [(b"content-type", b"application/json; charset=utf-8")],
                }
            )
            await send({"type": "http.response.body", "body": body})

        if too_large:
            return await reject()
        received = 0

        async def bounded_receive():
            nonlocal received, too_large
            message = await receive()
            received += len(message.get("body", b""))
            if received > limit:
                too_large = True
                # Starlette's multipart parser closes its temporary files on
                # MultiPartException, including chunked uploads without a length.
                raise MultiPartException("upload too large")
            return message

        async def bounded_send(message):
            if too_large:
                if message["type"] == "http.response.start":
                    await reject()
                return
            await send(message)

        await self.app(scope, bounded_receive, bounded_send)
