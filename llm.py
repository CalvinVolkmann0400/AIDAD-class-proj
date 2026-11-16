"""The single place where the app talks to the AI.

Every AI call in the app goes through ask_ai() below. That one function adds
the safety the demo needs: a time limit, a few retries when the AI service is
busy, and a clear error (AIError) instead of a crash or a made-up answer.

To test your key from the terminal:  uv run python llm.py
"""

import concurrent.futures
import os
import time

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

# Reads the line GEMINI_API_KEY=... from the local .env file (which is git-ignored).
load_dotenv()

# ---- Settings that are easy to change ----
MODEL = "gemini-3.6-flash"  # main model (free tier)
FALLBACK_MODEL = "gemini-3.5-flash-lite"  # lighter model, used for the last try
TIMEOUT_SECONDS = 30  # give up on one try after this long
HARD_LIMIT_SECONDS = TIMEOUT_SECONDS + 5  # safety net in case the SDK's own timeout fails
MAX_ATTEMPTS = 3  # how many tries before we show an error
WAIT_SECONDS = [2, 5]  # pause before try 2, then before try 3 ("backoff")

# Error codes that mean "busy, try again later" rather than "your request is wrong".
TEMPORARY_CODES = {429, 500, 502, 503, 504}


class AIError(Exception):
    """The AI could not give a usable answer. The message is safe to show on screen."""


class GeminiClient:
    """A thin wrapper around Google's Gemini SDK (the google-genai package)."""

    def __init__(self):
        from google import genai  # imported here so tests never need the real SDK

        self._client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    def generate(self, model: str, system: str, prompt: str, schema: dict) -> str:
        """Send one request and return the AI's answer as JSON text."""
        interaction = self._client.interactions.create(
            model=model,
            system_instruction=system,
            input=prompt,
            # Ask for JSON that follows our schema ("structured output").
            response_format={"type": "text", "mime_type": "application/json", "schema": schema},
            store=False,  # do not keep the conversation on Google's servers
            timeout=TIMEOUT_SECONDS,
        )
        return interaction.output_text


def has_api_key() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY"))


def ai_source() -> str:
    """A label for which AI is in use: the model name, or "practice" with no key."""
    return MODEL if has_api_key() else "practice"


def get_client():
    """The real Gemini client when a key exists, otherwise the scripted practice one."""
    if has_api_key():
        return GeminiClient()
    from fake_ai import PracticeClient

    return PracticeClient()


def ask_ai(system: str, prompt: str, answer_shape: type[BaseModel], client=None, sleep=time.sleep):
    """Ask the AI one question and get back a checked Pydantic object.

    system        instructions for the AI (its role and rules)
    prompt        the material to work on (for example the conversation so far)
    answer_shape  the Pydantic class the answer must fit
    client, sleep only passed in by tests, to swap in a fake AI and skip waiting
    """
    client = client or get_client()
    schema = answer_shape.model_json_schema()
    problem = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        model = FALLBACK_MODEL if attempt == MAX_ATTEMPTS else MODEL
        try:
            text = _call_with_time_limit(client, model, system, prompt, schema)
            return answer_shape.model_validate_json(text)  # Pydantic checks the shape
        except ValidationError:
            problem = "its answer was not in the expected format"
        except Exception as error:
            if not _is_temporary(error):
                raise AIError(f"The AI service refused the request: {_describe(error)}") from error
            problem = "the service was busy or too slow"
        if attempt < MAX_ATTEMPTS:
            sleep(WAIT_SECONDS[attempt - 1])
    raise AIError(
        f"The AI did not give a usable answer after {MAX_ATTEMPTS} tries ({problem}). "
        "Nothing was made up in its place."
    )


def _call_with_time_limit(client, model, system, prompt, schema) -> str:
    """Run the call in a background thread so a hanging request cannot freeze the app."""
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = pool.submit(client.generate, model, system, prompt, schema)
    try:
        return future.result(timeout=HARD_LIMIT_SECONDS)
    finally:
        pool.shutdown(wait=False)  # do not wait around for a stuck request


def _is_temporary(error: Exception) -> bool:
    """True for "busy / overloaded / timed out" errors, which are worth retrying."""
    if isinstance(error, TimeoutError):
        return True
    if getattr(error, "code", None) in TEMPORARY_CODES:
        return True
    text = str(error).lower()
    return any(word in text for word in ("overloaded", "unavailable", "timed out", "timeout"))


def _describe(error: Exception) -> str:
    """A short description of an error that can never contain the API key."""
    code = getattr(error, "code", "")
    status = getattr(error, "status", "") or type(error).__name__
    message = str(getattr(error, "message", "") or "")[:200]
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        message = message.replace(key, "[key hidden]")
    return f"{code} {status}. {message}".strip()


def test_connection() -> str:
    """Make one tiny real call. Returns "success" or a short reason (never the key)."""

    class Ping(BaseModel):
        ok: bool

    if not has_api_key():
        return "failed: no GEMINI_API_KEY found (create the .env file first)"
    try:
        ask_ai("You reply in JSON.", "Set ok to true.", Ping, client=GeminiClient())
        return "success"
    except AIError as error:
        return f"failed: {error}"


if __name__ == "__main__":
    print("AI connection test:", test_connection())
