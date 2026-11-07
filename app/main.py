
import os
import json
from pathlib import Path

from fastapi import FastAPI
from openai import OpenAI

app = FastAPI(
    title="CNAPP Security Dashboard",
    description="Agentic AI DevSecOps Security Pipeline",
    version="1.0.0"
)

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent


@app.get("/")
def read_root():
    return {
        "message": "DevSecOps demo application is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


def load_scan_results(filename, default_data):
    """Load security scan results safely."""
    file_path = BASE_DIR / filename

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    except FileNotFoundError:
        return default_data

    except json.JSONDecodeError:
        return default_data


def perform_ai_alert_triage(trivy_data, bandit_data):
    """
    Analyze Trivy and Bandit security findings
    using an OpenAI-powered security assistant.
    """

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return {
            "status": "error",
            "message": "OPENAI_API_KEY is not configured"
        }

    prompt = f"""
You are an expert DevSecOps AI Security Agent.

Analyze the following security scan results.

TRIVY VULNERABILITIES:
{json.dumps(trivy_data)[:12000]}

BANDIT SAST FINDINGS:
{json.dumps(bandit_data)[:12000]}

Tasks:

1. Analyze all security findings.
2. Identify potential false positives.
3. Prioritize genuine security risks:
   P1 = Critical
   P2 = High
   P3 = Medium or Low
4. Explain the reason for each priority.
5. Recommend remediation steps.

Return valid JSON in this format:

{{
    "findings": [
        {{
            "priority": "P1",
            "description": "Security finding description",
            "rationale": "Reason for prioritization",
            "recommendation": "Suggested remediation"
        }}
    ]
}}

Do not claim a finding is a false positive without sufficient evidence.
"""

    try:
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional DevSecOps security analyst."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"}
        )

        result = response.choices[0].message.content

        if not result:
            raise ValueError("AI returned an empty response")

        return json.loads(result)

    except Exception as error:
        return {
            "status": "error",
            "message": str(error)
        }


@app.get("/api/cnapp")
def cnapp_api():

    # Load Trivy scan results
    trivy_data = load_scan_results(
        "trivy-results.json",
        {"Results": []}
    )

    # Load Bandit scan results
    bandit_data = load_scan_results(
        "bandit-results.json",
        {"results": []}
    )

    # Perform AI-powered alert triage
    ai_results = perform_ai_alert_triage(
        trivy_data,
        bandit_data
    )

    return {
        "status": "success",
        "project": "Agentic AI DevSecOps Pipeline",
        "triage_findings": ai_results
    }
