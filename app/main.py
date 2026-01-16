from fastapi import FastAPI
import os
from typing import Union
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app.routers import (
    auth_router,
    locations_router,
    reviews_router,
    dict_router,
    pictures_router,
    users_router
)
app = FastAPI()

# Включите CORS для Android
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
os.makedirs("uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="uploads"), name="static")


app.include_router(auth_router,)

app.include_router(locations_router,)
app.include_router(reviews_router,)
app.include_router(dict_router,)
app.include_router(pictures_router,)
app.include_router(users_router,)
