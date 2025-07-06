from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import appENV, PORT
from routes import assessmentRoutes, talkRoutes, userActionsRoutes  # Import routes


## Define API prefix based on environment
prefix = "/" + ("mindwave" if appENV == "production" else "dev")

## Set API documentation details
title = f"mindwave API for {appENV} Environment"
description = f"mindwave API for {appENV} Documentation"

tags_metadata = [
    {
        "name": "MindWave APIs",
        "description": "Endpoints to power mindwave",
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

# Include routers
app.include_router(assessmentRoutes.router, prefix=prefix + "/assessment", tags=["assessment"])
app.include_router(talkRoutes.router, prefix=prefix + "/talk", tags=["talk"])
app.include_router(userActionsRoutes.router, prefix=prefix + "/user-history", tags=["user-actions"])

if __name__ == "__main__":
    import uvicorn
    reload = True  if appENV != "production" else False
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=reload)