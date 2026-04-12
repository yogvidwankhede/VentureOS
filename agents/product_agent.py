from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
import json
import re
load_dotenv()


def run_product_strategy(idea: str, llm) -> dict:
    prompt = ChatPromptTemplate.from_template("""
You are a senior product manager at a top Silicon Valley startup.

Analyze this startup idea: {idea}

Respond with ONLY a valid JSON object. No explanation, no markdown, no backticks.

The JSON must have exactly these keys:
{{
  "mvp_features": [
    {{
      "feature": "feature name",
      "priority": "Must",
      "reason": "why this priority"
    }}
  ],
  "suggested_stack": [
    {{
      "tool": "tool or language name",
      "reason": "why recommended"
    }}
  ],
  "build_timeline": [
    {{
      "week": "Week 1-2",
      "milestone": "what gets built"
    }}
  ],
  "monetization": [
    {{
      "model": "revenue model name",
      "pros": ["pro 1", "pro 2"],
      "cons": ["con 1", "con 2"]
    }}
  ]
}}

Include 5 mvp_features, 4 stack items, 6 timeline entries, 2 monetization models.
Priority must be one of: Must, Should, Could, Won't
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
        print(f"[product_agent parse error] {e}\nRaw: {text}")
        return {
            "mvp_features": [],
            "suggested_stack": [],
            "build_timeline": [],
            "monetization": []
        }
