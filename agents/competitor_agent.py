from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
import json
import re
load_dotenv()


def run_competitor_analysis(idea: str, llm) -> dict:
    prompt = ChatPromptTemplate.from_template("""
You are a competitive intelligence expert.

Analyze this startup idea: {idea}

Respond with ONLY a valid JSON object. No explanation, no markdown, no backticks.

The JSON must have exactly these keys:
{{
  "competitors": [
    {{
      "name": "Company Name",
      "description": "what they do in 1 sentence",
      "funding": "estimated funding raised",
      "weakness": "their biggest gap",
      "our_advantage": "how our idea beats them"
    }}
  ],
  "whitespace": "the gap none of them fill in 2 sentences"
}}

Include exactly 4 competitors.
""")

    chain = prompt | llm
    response = chain.invoke({"idea": idea})
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
        print(f"[competitor_agent parse error] {e}\nRaw: {text}")
        return {
            "competitors": [],
            "whitespace": "Could not parse competitor data."
        }
