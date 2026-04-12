from agents.scorecard_agent import run_scorecard
from agents.pitch_agent import run_pitch_generation
from agents.product_agent import run_product_strategy
from agents.competitor_agent import run_competitor_analysis
from agents.market_agent import run_market_research
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
import time
import json
load_dotenv()


def get_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.7
    )


def run_ventureOS_stream(idea: str):
    """Generator that yields SSE events as each agent completes"""
    llm = get_llm()

    # Market Research
    yield f"data: {json.dumps({'event': 'status', 'message': '📊 Running Market Research Agent...'})}\n\n"
    market = safe_run(run_market_research, idea, llm)
    yield f"data: {json.dumps({'event': 'market_research', 'data': market})}\n\n"
    time.sleep(2)

    # Competitor Analysis
    yield f"data: {json.dumps({'event': 'status', 'message': '🔍 Running Competitor Analysis Agent...'})}\n\n"
    competitors = safe_run(run_competitor_analysis, idea, llm)
    yield f"data: {json.dumps({'event': 'competitor_analysis', 'data': competitors})}\n\n"
    time.sleep(2)

    # Product Strategy
    yield f"data: {json.dumps({'event': 'status', 'message': '🛠️ Running Product Strategy Agent...'})}\n\n"
    product = safe_run(run_product_strategy, idea, llm)
    yield f"data: {json.dumps({'event': 'product_strategy', 'data': product})}\n\n"
    time.sleep(2)

    # Pitch & Emails
    yield f"data: {json.dumps({'event': 'status', 'message': '📈 Running Pitch & Outreach Agent...'})}\n\n"
    pitch = safe_run_pitch(run_pitch_generation, idea,
                           market, competitors, llm)
    yield f"data: {json.dumps({'event': 'pitch', 'data': pitch})}\n\n"
    time.sleep(2)

    # Scorecard
    yield f"data: {json.dumps({'event': 'status', 'message': '🎯 Running Fundability Scorecard Agent...'})}\n\n"
    scorecard = safe_run_scorecard(
        run_scorecard, idea, market, competitors, product, llm)
    yield f"data: {json.dumps({'event': 'scorecard', 'data': scorecard})}\n\n"

    # Done
    yield f"data: {json.dumps({'event': 'done', 'message': 'All agents complete!'})}\n\n"


def safe_run(fn, idea, llm, retries=3):
    for attempt in range(retries):
        try:
            return fn(idea, llm)
        except Exception as e:
            print(f"[Error attempt {attempt+1}] {e}")
            time.sleep(5)
    return {"error": "Failed after retries"}


def safe_run_pitch(fn, idea, market, competitors, llm, retries=3):
    for attempt in range(retries):
        try:
            return fn(idea, market, competitors, llm)
        except Exception as e:
            print(f"[Pitch error attempt {attempt+1}] {e}")
            time.sleep(5)
    return {"deck": [], "emails": [], "domains": []}


def safe_run_scorecard(fn, idea, market, competitors, product, llm, retries=3):
    for attempt in range(retries):
        try:
            return fn(idea, market, competitors, product, llm)
        except Exception as e:
            print(f"[Scorecard error attempt {attempt+1}] {e}")
            time.sleep(5)
    return {"error": "Failed after retries"}
