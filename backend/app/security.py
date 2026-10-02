"""Bound the full HTTP body, including chunked multipart uploads, before parsing."""
from .analysis import MAX_BYTES
from starlette.responses import JSONResponse

class RequestLimitMiddleware:
    def __init__(self, app):
        self.app = app
    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope.get('method') not in ('POST','PUT','PATCH'):
            return await self.app(scope, receive, send)
        chunks, size = [], 0
        while True:
            event = await receive()
            if event['type'] == 'http.disconnect':
                return
            chunk = event.get('body', b'')
            size += len(chunk)
            if size > MAX_BYTES + 65536:
                response = JSONResponse({'error':{'code':'FILE_TOO_LARGE','message':'Upload at most 1 MiB of CSV data.'}}, status_code=413, headers={'Cache-Control':'no-store'})
                return await response(scope, receive, send)
            chunks.append(chunk)
            if not event.get('more_body',False):
                break
        body = b''.join(chunks)
        delivered = False
        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {'type':'http.request','body':body,'more_body':False}
            return await receive()
        await self.app(scope, replay, send)
