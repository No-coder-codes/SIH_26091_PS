from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Literal

# Ensure backend root directory is in sys.path for Vercel Serverless & direct execution
BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from app.financial.engine import calculate, schemes_payload
from app.services.advisor import advisor_mode, demo_advisor_reply
from app.services.feasibility import analyse_feasibility

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
DATA = Path(__file__).resolve().parent / "data" / "business_categories.json"

app = FastAPI(title="Gram Udyog API", version="0.2.0")
# The UI is served from this app in production. Explicit cross-origin access is
# opt-in for a separate frontend during development or deployment.
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "").strip()
allowed_origins = [item.strip() for item in allowed_origins_raw.split(",") if item.strip()] if allowed_origins_raw else ["*"]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

class FinancialRequest(BaseModel):
    location: str = Field(min_length=2, max_length=120)
    business_category: Literal["dairy", "textile", "agriculture"]
    margin_capital: float = Field(gt=0, le=10000000)
    district: str | None = Field(default=None, max_length=80)
    taluka: str | None = Field(default=None, max_length=80)
    locality: str | None = Field(default=None, max_length=120)
    enterprise_idea: str | None = Field(default=None, max_length=240)

    @field_validator("location")
    @classmethod
    def gujarat_context(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Location is required.")
        return value.strip()

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1200)
    financial_context: dict

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.2.0", "advisor_mode": advisor_mode()}

@app.get("/api/schemes")
def schemes():
    return schemes_payload()

@app.get("/api/business-categories")
def categories():
    return json.loads(DATA.read_text(encoding="utf-8"))

@app.post("/api/financial/calculate")
def financial_calculate(request: FinancialRequest):
    try:
        payload = calculate(request.margin_capital).payload()
        payload.update({
            "location": request.location,
            "business_category": request.business_category,
            "district": request.district,
            "taluka": request.taluka,
            "locality": request.locality,
            "enterprise_idea": request.enterprise_idea,
        })
        if payload["status"] == "eligible":
            payload["analysis"] = analyse_feasibility(request.business_category, payload, request.location)
        return payload
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

@app.post("/api/ai/chat")
def ai_chat(request: ChatRequest):
    # Server-side authoritative calculation verification: recalculate using engine if parameters exist
    ctx = request.financial_context.copy()
    if "margin_capital" in ctx and "business_category" in ctx and ctx.get("margin_capital"):
        try:
            margin = float(ctx["margin_capital"])
            category = ctx["business_category"]
            loc = ctx.get("location", "Gujarat")
            authoritative = calculate(margin).payload()
            authoritative.update({
                "location": loc,
                "business_category": category,
                "district": ctx.get("district"),
                "taluka": ctx.get("taluka"),
                "locality": ctx.get("locality"),
                "enterprise_idea": ctx.get("enterprise_idea"),
            })
            if authoritative["status"] == "eligible":
                authoritative["analysis"] = analyse_feasibility(category, authoritative, loc)
            ctx = authoritative
        except Exception:
            pass # Keep provided context if recalculation fails due to partial context

    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return {"mode": "demo", "reply": demo_advisor_reply(request.message, ctx)}
    try:
        from openai import OpenAI
        system = """You are the Gram Udyog financial explanation assistant. You are an explanation layer only. Explain only the structured financial results supplied by the authoritative backend engine. Never calculate or invent scheme parameters, loan limits, interest rates, eligibility criteria, financial calculations, or local market facts. If sufficient data or evidence is not present in the authoritative result, explicitly state that the prototype does not have enough data. Be concise, helpful, and plain-language; Hindi/Hinglish is welcome if the user uses it."""
        client = OpenAI(api_key=key, timeout=10.0)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            messages=[{"role": "system", "content": system}, {"role": "user", "content": f"Authoritative result JSON: {json.dumps(ctx)}\n\nUser question: {request.message}"}],
            temperature=0.2,
        )
        return {"mode": "live", "reply": response.choices[0].message.content}
    except Exception as error:
        # The product remains useful and honest when a configured provider fails.
        return {"mode": "demo", "reply": demo_advisor_reply(request.message, ctx), "provider_unavailable": True}

if FRONTEND.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND), name="assets")

@app.get("/")
def home():
    # Version the app bundle in the HTML response so a running local prototype
    # cannot pair a newer assessment form with a stale cached script.
    document = (FRONTEND / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(document.replace('/assets/app.js', '/assets/app.js?v=0.2.0'))

@app.get("/favicon.svg", include_in_schema=False)
def favicon():
    return FileResponse(FRONTEND / "favicon.svg", media_type="image/svg+xml")
