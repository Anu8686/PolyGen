import os
import time
import requests

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

TRIPO_API_KEY = os.getenv("TRIPO_API_KEY")

TRIPO_BASE_URL = "https://api.tripo3d.ai/v2/openapi"


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="PolyGen API",
    description="Generative Text-to-3D Asset Pipeline",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODEL
# ============================================================

class GenerateRequest(BaseModel):
    prompt: str


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return {
        "message": "PolyGen API is running",
        "version": "1.0.0",
        "tripo_configured": bool(TRIPO_API_KEY)
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "tripo_configured": bool(TRIPO_API_KEY)
    }


# ============================================================
# CREATE TRIPO TASK
# ============================================================

def create_tripo_task(prompt: str):

    if not TRIPO_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="TRIPO_API_KEY is not configured."
        )

    url = f"{TRIPO_BASE_URL}/task"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TRIPO_API_KEY}"
    }

    payload = {
        "type": "text_to_model",
        "model_version": "P1-20260311",
        "prompt": prompt,
        "face_limit": 10000,
        "texture": True,
        "pbr": True,
        "texture_quality": "standard"
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=60
    )

    print("Tripo create response:", response.status_code)
    print(response.text)

    if response.status_code != 200:

        raise HTTPException(
            status_code=response.status_code,
            detail=response.text
        )

    result = response.json()

    if result.get("code") != 0:

        raise HTTPException(
            status_code=400,
            detail=result
        )

    task_id = result.get("data", {}).get("task_id")

    if not task_id:

        raise HTTPException(
            status_code=500,
            detail="Tripo did not return a task ID."
        )

    return task_id


# ============================================================
# GET TRIPO TASK
# ============================================================

def get_tripo_task(task_id: str):

    url = f"{TRIPO_BASE_URL}/task/{task_id}"

    headers = {
        "Authorization": f"Bearer {TRIPO_API_KEY}"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=60
    )

    print("Tripo task response:", response.status_code)

    if response.status_code != 200:

        raise HTTPException(
            status_code=response.status_code,
            detail=response.text
        )

    result = response.json()

    if result.get("code") != 0:

        raise HTTPException(
            status_code=400,
            detail=result
        )

    return result.get("data", {})


# ============================================================
# GENERATE MODEL
# ============================================================

@app.post("/generate")
def generate_model(request: GenerateRequest):

    prompt = request.prompt.strip()

    # --------------------------------------------------------
    # VALIDATE PROMPT
    # --------------------------------------------------------

    if not prompt:

        raise HTTPException(
            status_code=400,
            detail="Prompt cannot be empty."
        )

    if len(prompt) > 1024:

        raise HTTPException(
            status_code=400,
            detail="Prompt must be 1024 characters or less."
        )


    print("----------------------------------------")
    print("PolyGen AI Generation Started")
    print("Prompt:", prompt)
    print("----------------------------------------")


    # --------------------------------------------------------
    # CREATE TRIPO TASK
    # --------------------------------------------------------

    task_id = create_tripo_task(prompt)

    print("Tripo Task ID:", task_id)


    # --------------------------------------------------------
    # WAIT FOR GENERATION
    # --------------------------------------------------------

    max_attempts = 90

    for attempt in range(max_attempts):

        task = get_tripo_task(task_id)

        status = task.get("status")

        progress = task.get("progress", 0)

        print(
            f"Attempt {attempt + 1}/{max_attempts} | "
            f"Status: {status} | "
            f"Progress: {progress}%"
        )


        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        if status == "success":

            output = task.get("output", {})

            model_url = (
                output.get("pbr_model")
                or output.get("model")
                or output.get("base_model")
            )

            preview_url = output.get(
                "rendered_image"
            )


            if not model_url:

                raise HTTPException(
                    status_code=500,
                    detail={
                        "message": "Generation completed but no model URL was returned.",
                        "task": task
                    }
                )


            print("----------------------------------------")
            print("3D MODEL GENERATED SUCCESSFULLY")
            print("Model URL:", model_url)
            print("----------------------------------------")


            return {
                "success": True,
                "message": "3D model generated successfully.",
                "prompt": prompt,
                "task_id": task_id,
                "model_url": model_url,
                "preview_url": preview_url,
                "format": "glb",
                "status": "success",
                "progress": 100
            }


        # ----------------------------------------------------
        # FAILED
        # ----------------------------------------------------

        if status in [
            "failed",
            "banned",
            "expired",
            "cancelled",
            "unknown"
        ]:

            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Tripo 3D generation failed.",
                    "task_id": task_id,
                    "status": status,
                    "task": task
                }
            )


        # ----------------------------------------------------
        # WAIT
        # ----------------------------------------------------

        time.sleep(2)


    # --------------------------------------------------------
    # TIMEOUT
    # --------------------------------------------------------

    raise HTTPException(
        status_code=504,
        detail={
            "message": "3D generation timed out.",
            "task_id": task_id
        }
    )