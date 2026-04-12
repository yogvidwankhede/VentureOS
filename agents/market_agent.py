from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
import json
import re
load_dotenv()


def run_market_research(idea: str, llm) -> dict:
    prompt = ChatPromptTemplate.from_template("""
You are a top-tier market research analyst at a VC firm.

Analyze this startup idea: {idea}

Respond with ONLY a valid JSON object. No explanation, no markdown, no backticks.

The JSON must have exactly these keys:
{{
  "market_size": "estimated TAM in dollars as a string",
  "growth_rate": "annual growth percentage as a string",
  "target_customer": "2-sentence description",
  "pain_point": "the core problem being solved",
  "market_trends": ["trend 1", "trend 2", "trend 3"],
  "opportunity_summary": "3-sentence market opportunity"
}}
""")

    chain = prompt | llm
    response = chain.invoke({"idea": idea})
    return parse_json(response.content)


def parse_json(text: str) -> dict:
    text = text.strip()
    # Strip markdown code blocks if present
    text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    # Find first { to last }
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]
    try:
        return json.loads(text)
    except Exception as e:
        print(f"[market_agent parse error] {e}\nRaw: {text}")
        return {
            "market_size": "N/A",
            "growth_rate": "N/A",
            "target_customer": text[:200],
            "pain_point": "Parse error — see raw output",
            "market_trends": [],
            "opportunity_summary": ""
        }
