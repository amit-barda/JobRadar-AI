import json
from openai import OpenAI
from ..config import settings

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )
    return _client


def chat_completion(system_prompt: str, user_prompt: str, model: str | None = None) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model=model or settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content or ""


def chat_json(system_prompt: str, user_prompt: str, model: str | None = None) -> dict:
    """Call the model and parse the response as JSON. Returns empty dict on failure."""
    raw = chat_completion(system_prompt, user_prompt + "\n\nRespond ONLY with valid JSON.", model)
    # Strip markdown code fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"raw": raw}
