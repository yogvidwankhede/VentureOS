from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
import json
import re
load_dotenv()


def run_pitch_generation(idea: str, market: dict, competitors: dict, llm) -> dict:
    prompt = ChatPromptTemplate.from_template("""
You are a startup pitch coach who has helped companies raise $500M+.

Startup idea: {idea}
Market data: {market}
Competitor landscape: {competitors}

Respond with ONLY a valid JSON object. No explanation, no markdown, no backticks.

The JSON must have exactly these keys:
{{
  "deck": [
    {{
      "slide_number": 1,
      "title": "slide title",
      "key_points": ["point 1", "point 2", "point 3"]
    }}
  ],
  "emails": [
    {{
      "investor_type": "Pre-seed VC",
      "subject_line": "email subject",
      "body": "full email text under 150 words"
    }}
  ],
  "domains": ["domain1.com", "domain2.io", "domain3.co", "domain4.app", "domain5.ai"]
}}

Include exactly 10 slides, 3 emails (Pre-seed VC, Angel, Accelerator), 5 domains.
""")

    chain = prompt | llm
    response = chain.invoke({
        "idea": idea,
        "market": json.dumps(market),
        "competitors": json.dumps(competitors)
    })
    return parse_json(response.content)


def parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]
    try:
        return json.loads(text)
    except Exception as e:
        print(f"[pitch_agent parse error] {e}\nRaw: {text}")
        return {"deck": [], "emails": [], "domains": []}
