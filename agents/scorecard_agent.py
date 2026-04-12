from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
import json
import re
load_dotenv()


def run_scorecard(idea: str, market: dict, competitors: dict, product: dict, llm) -> dict:
    prompt = ChatPromptTemplate.from_template("""
You are a senior venture capitalist who has evaluated thousands of startups.

Startup idea: {idea}
Market research: {market}
Competitor analysis: {competitors}
Product strategy: {product}

Score this startup on exactly these 5 dimensions, each out of 20 points.
Be honest and critical — not every startup deserves high scores.

Return ONLY a valid JSON object with no markdown, no backticks, no explanation:
{{
  "scores": [
    {{
      "dimension": "Market Size",
      "score": <number 0-20>,
      "reason": "one sentence explanation"
    }},
    {{
      "dimension": "Timing & Trends",
      "score": <number 0-20>,
      "reason": "one sentence explanation"
    }},
    {{
      "dimension": "Differentiation",
      "score": <number 0-20>,
      "reason": "one sentence explanation"
    }},
    {{
      "dimension": "Feasibility",
      "score": <number 0-20>,
      "reason": "one sentence explanation"
    }},
    {{
      "dimension": "Revenue Potential",
      "score": <number 0-20>,
      "reason": "one sentence explanation"
    }}
  ],
  "total": <sum of all 5 scores, max 100>,
  "verdict": "one of: Strong Pass | Pass | Conditional Pass | Needs Work | Pass",
  "summary": "2-3 sentence honest investor summary of this idea",
  "biggest_risk": "the single biggest risk in one sentence",
  "biggest_strength": "the single biggest strength in one sentence"
}}
""")

    chain = prompt | llm
    response = chain.invoke({
        "idea": idea,
        "market": json.dumps(market),
        "competitors": json.dumps(competitors),
        "product": json.dumps(product)
    })

    text = response.content.strip()
    text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]
    try:
        return json.loads(text)
    except Exception as e:
        print(f"[scorecard parse error] {e}")
        return {"error": "Failed to parse scorecard"}
