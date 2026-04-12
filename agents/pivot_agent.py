from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
import json
import re
load_dotenv()


def run_pivot_suggester(idea: str, market: dict, competitors: dict, scorecard: dict, llm) -> dict:
    prompt = ChatPromptTemplate.from_template("""
You are a seasoned startup strategist who has helped hundreds of founders find their winning pivot.

Original idea: {idea}
Market research: {market}
Competitor landscape: {competitors}
Fundability scorecard: {scorecard}

Based on the weaknesses revealed in the scorecard and the gaps in the competitor landscape,
suggest 3 strategic pivots that could make this idea significantly stronger.

Each pivot should be meaningfully different — not just a small tweak.
Think: different customer segment, different business model, different distribution channel,
adjacent problem, or completely different monetization approach.

Return ONLY valid JSON with no markdown, no backticks, no explanation:
{{
  "pivots": [
    {{
      "title": "short catchy name for the pivot (4-6 words)",
      "description": "what the pivoted idea looks like in 2 sentences",
      "why": "why this pivot addresses the original idea's weaknesses",
      "target_customer": "who this pivot serves",
      "revenue_model": "how this pivot makes money",
      "difficulty": "Easy | Medium | Hard",
      "potential": "Low | Medium | High | Very High",
      "example": "a real company that succeeded with a similar pivot"
    }}
  ],
  "recommendation": "which pivot you recommend most and why in 2 sentences"
}}
""")

    chain = prompt | llm
    response = chain.invoke({
        "idea": idea,
        "market": json.dumps(market),
        "competitors": json.dumps(competitors),
        "scorecard": json.dumps(scorecard)
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
        print(f"[pivot_agent parse error] {e}")
        return {"pivots": [], "recommendation": ""}
