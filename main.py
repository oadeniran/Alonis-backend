from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from config import appENV, PORT
from routes import assessmentRoutes, talkRoutes, userActionsRoutes, commonRoutes  # Import routes
from starlette.middleware.base import BaseHTTPMiddleware
import json

class LogResponseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Capture response
        response = await call_next(request)

        # Read and decode the response body (works if it's JSON or text)
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        try:
            decoded = response_body.decode()
            if decoded.startswith('{') or decoded.startswith('['):
                parsed = json.loads(decoded)
                print(f"[RESPONSE] {request.url.path} ->", json.dumps(parsed, indent=2))
            else:
                print(f"[RESPONSE] {request.url.path} -> {decoded}")
        except Exception as e:
            print(f"[RESPONSE] {request.url.path} -> <Failed to decode body: {e}>")

        # Return a new Response with the original content (because body_iterator is now consumed)
        return Response(content=response_body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)


## Define API prefix based on environment
prefix = "/" + ("alonis" if appENV == "production"  else ("alonis" if appENV == "development" else "dev"))

## Set API documentation details
title = f"Alonis API for {appENV} Environment"
description = f"Alonis API for {appENV} Documentation"

tags_metadata = [
    {
        "name": "Alonis APIs",
        "description": "Endpoints to power alonis",
    }
]

## Initialize FastAPI app
app = FastAPI(
    docs_url=prefix + "/docs",
    openapi_url=prefix + "/openapi.json",
    title=title,
    description=description,
    openapi_tags=tags_metadata,
)

## Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

## Add custom middleware for logging responses
app.add_middleware(LogResponseMiddleware)

# Include routers
app.include_router(assessmentRoutes.router, prefix=prefix + "/assessment", tags=["assessment"])
app.include_router(talkRoutes.router, prefix=prefix + "/talk", tags=["talk"])
app.include_router(userActionsRoutes.router, prefix=prefix + "/user", tags=["user-actions"])
app.include_router(commonRoutes.router, prefix=prefix + "/common", tags=["common"])

if __name__ == "__main__":
    import uvicorn
    reload = True  if appENV != "production" else False
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=reload)