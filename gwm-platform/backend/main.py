from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.database import engine, Base
from app.api import auth, projects, jobs, datasets, analytics
from app.api import prompt  # Build 3: AI Prompt Engine
from app.api import countries  # Build 4: Country Profile Engine
from app.api import geography  # Build 5: Geography Engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DriveVerse AI Backend API")

# Setup CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(jobs.router)
app.include_router(datasets.router)
app.include_router(analytics.router)
app.include_router(prompt.router)   # Build 3: POST /prompt/parse, /prompt/generate
app.include_router(countries.router) # Build 4: GET|POST|PUT|DELETE /countries, POST /countries/scenario/expand
app.include_router(geography.router) # Build 5: POST /geography/resolve, /geography/build

@app.get("/")
def read_root():
    return {"status": "ok", "message": "GWM Platform API"}
