"""A scripted stand-in for the real AI ("practice mode").

It is used when there is no API key, and by the tests, so the app can be built
and tried without calling Google. It has the same generate() method as
llm.GeminiClient, but it only returns fixed, pre-written answers. The app
labels this clearly on screen so nobody mistakes it for real AI output.
"""

import json

from models import DIMENSIONS

SCRIPTED_QUESTIONS = [
    "Thanks for sharing that. What have you already tried to fix this?",
    "Got it. Is anyone else part of this decision, or is it up to you?",
    "What result in the next 90 days would make this feel worth it?",
    "And how soon would you want to get started?",
]
GOODBYE = "Thank you, that is everything I need. The closer will read a summary before your call."


class PracticeClient:
    def generate(self, model: str, system: str, prompt: str, schema: dict) -> str:
        """Return a canned JSON answer that fits the shape that was asked for."""
        lead_lines = [line[6:] for line in prompt.splitlines() if line.startswith("LEAD: ")]
        shape = schema.get("title")

        if shape == "ChatTurn":
            asked = len(lead_lines) - 1  # how many scripted questions were used so far
            if asked < len(SCRIPTED_QUESTIONS):
                return json.dumps({"reply": SCRIPTED_QUESTIONS[asked], "done": False})
            return json.dumps({"reply": GOODBYE, "done": True})

        if shape == "ScoreResult":
            dimensions = [
                {
                    "name": name,
                    "score": 3 if lead_lines else 0,
                    "reason": "Practice mode: a fixed middle score, not a real judgement.",
                    # Use the lead's own lines as quotes so the quote check passes.
                    "quote": lead_lines[i % len(lead_lines)] if lead_lines else "",
                }
                for i, name in enumerate(DIMENSIONS)
            ]
            return json.dumps({"enough_information": bool(lead_lines), "dimensions": dimensions})

        if shape == "Brief":
            return json.dumps(
                {
                    "summary_lines": [
                        "Practice mode: this brief is a fixed template, not written by a real AI.",
                        f"The lead sent {len(lead_lines)} messages in the chat.",
                        "Add your API key to get a real brief.",
                    ],
                    "key_quotes": lead_lines[:3],
                    "unknowns": ["Everything a real AI would notice is missing in practice mode."],
                    "opening_line": "Thanks for making time today. What would you most like to get out of this call?",
                }
            )

        return json.dumps({"ok": True})  # used by the connection test shape
