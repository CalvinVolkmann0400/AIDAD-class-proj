"""Tests for the single AI call: retries, the fallback model, and honest errors."""

import pytest
from pydantic import BaseModel

import llm


class Answer(BaseModel):
    word: str


class ScriptedClient:
    """A fake AI that returns (or raises) whatever the test lists, one item per call."""

    def __init__(self, *results):
        self.results = list(results)
        self.models_used = []

    def generate(self, model, system, prompt, schema):
        self.models_used.append(model)
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class BusyError(Exception):
    status_code = 503  # "service overloaded"


class BadKeyError(Exception):
    status_code = 400  # "your request is wrong", so retrying cannot help


def no_sleep(seconds):
    pass


def test_good_answer_is_returned_as_a_pydantic_object():
    client = ScriptedClient('{"word": "hello"}')
    assert llm.ask_ai("s", "p", Answer, client=client, sleep=no_sleep).word == "hello"


def test_busy_errors_are_retried_and_the_second_try_uses_the_fallback_model():
    client = ScriptedClient(BusyError("overloaded"), BusyError("overloaded"), '{"word": "ok"}')
    assert llm.ask_ai("s", "p", Answer, client=client, sleep=no_sleep).word == "ok"
    assert client.models_used == [llm.MODEL, llm.FALLBACK_MODEL, llm.MODEL]


def test_gives_an_honest_error_after_all_tries_fail():
    client = ScriptedClient(*[BusyError("overloaded")] * llm.MAX_ATTEMPTS)
    with pytest.raises(llm.AIError, match="Nothing was made up"):
        llm.ask_ai("s", "p", Answer, client=client, sleep=no_sleep)


def test_wrong_shaped_answer_is_retried():
    client = ScriptedClient('{"wrong": 1}', '{"word": "fixed"}')
    assert llm.ask_ai("s", "p", Answer, client=client, sleep=no_sleep).word == "fixed"


def test_permanent_error_is_not_retried():
    client = ScriptedClient(BadKeyError("bad key"), '{"word": "never reached"}')
    with pytest.raises(llm.AIError, match="refused"):
        llm.ask_ai("s", "p", Answer, client=client, sleep=no_sleep)
    assert len(client.models_used) == 1


def test_a_hanging_call_times_out_and_is_retried(monkeypatch):
    import time

    monkeypatch.setattr(llm, "HARD_LIMIT_SECONDS", 0.2)

    class SlowThenFastClient:
        calls = 0

        def generate(self, model, system, prompt, schema):
            self.calls += 1
            if self.calls == 1:
                time.sleep(1)  # longer than the time limit
            return '{"word": "late"}'

    client = SlowThenFastClient()
    assert llm.ask_ai("s", "p", Answer, client=client, sleep=no_sleep).word == "late"
    assert client.calls == 2
