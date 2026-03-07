"""
FastAPI main application entry point for Intelli-Credit APIs.
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from api.upload_routes import router as upload_router
from api.score_routes import router as score_router
from api.cam_routes import router as cam_router
from api.search_routes import router as search_router
from api.auth_routes import router as auth_router
from api.gst_routes import router as gst_router
from api.qualitative_routes import router as qualitative_router
from api.recommendation_routes import router as recommendation_router
from api.regulatory_routes import router as regulatory_router

app = FastAPI(
    title="Intelli-Credit API",
    description="API for AI-Powered Credit Appraisal Engine",
    version="1.0.0"
)

os.makedirs("generated_cams", exist_ok=True)
app.mount("/generated_cams", StaticFiles(directory="generated_cams"), name="generated_cams")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload_router, prefix="/api/v1")
app.include_router(score_router, prefix="/api/v1")
app.include_router(cam_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(gst_router, prefix="/api/v1/gst")
app.include_router(qualitative_router, prefix="/api/v1/qualitative")
app.include_router(recommendation_router, prefix="/api/v1/recommendation")
app.include_router(regulatory_router, prefix="/api/v1/regulatory")

@app.get("/")
async def root():
    return {"message": "Intelli-Credit API is running."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
