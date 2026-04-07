from openai import OpenAI
from openai import APIError

from app.config import settings


def get_client() -> OpenAI:
    return OpenAI(
        base_url=settings.hf_router_base_url,
        api_key=settings.hf_token,
    )


def chat_with_fallback(messages: list[dict], primary_model: str, secondary_model: str | None = None) -> tuple[str, str]:
    client = get_client()
    candidates = [primary_model]
    if secondary_model and secondary_model != primary_model:
        candidates.append(secondary_model)

    last_error = None
    for model_name in candidates:
        for _ in range(2):
            try:
                out = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    timeout=45,
                )
                text = out.choices[0].message.content if out.choices else "No answer generated."
                return text, model_name
            except APIError as exc:
                last_error = exc
                continue
            except Exception as exc:
                last_error = exc
                break
    raise RuntimeError(f"LLM request failed across models: {last_error}")
