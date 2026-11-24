import json
from pathlib import Path

import pytest

from lexikon.api import ApiError, iter_raw_pages

FIX = Path(__file__).parent / "fixtures" / "api"


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.calls = []
        self.headers = {}

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append(dict(params))
        p = self.payloads.pop(0)
        return p if isinstance(p, FakeResponse) else FakeResponse(p)


def load(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def pages(payloads):
    s = FakeSession(payloads)
    return list(iter_raw_pages(s, pause=0)), s


def test_follows_continue():
    result, s = pages([load("batch1.json"), load("batch2.json")])
    assert [p.pageid for p in result] == [10, 11, 12]
    assert len(s.calls) == 2
    assert s.calls[1]["gapcontinue"] == "Betreuungsverfahren"
    assert s.calls[1]["continue"] == "gapcontinue||"


def test_maps_fields():
    result, _ = pages([load("batch1.json"), load("batch2.json")])
    betreuer, weiterleitung, verfahren = result
    assert betreuer.revid == 501
    assert betreuer.timestamp == "2024-01-02T03:04:05Z"
    assert betreuer.wikitext == "Der '''Betreuer''' ist ..."
    assert betreuer.categories == ("Personen",)
    assert betreuer.is_redirect is False
    assert weiterleitung.is_redirect is True
    assert verfahren.categories == ("Verfahren", "Gericht")


def test_request_params():
    _, s = pages([load("batch2.json")])
    p = s.calls[0]
    assert p["generator"] == "allpages"
    assert p["gaplimit"] == 50
    assert p["prop"] == "revisions|categories|info"
    assert p["rvprop"] == "ids|timestamp|content"
    assert p["rvslots"] == "main"
    assert p["formatversion"] == 2
    assert p["maxlag"] == 5
    assert p["cllimit"] == "max"


def test_raises_on_api_error():
    with pytest.raises(ApiError):
        pages([{"error": {"code": "badvalue", "info": "kaputt"}}])


def test_retries_maxlag_then_succeeds():
    lag = {"error": {"code": "maxlag", "info": "Waiting"}}
    result, s = pages([lag, load("batch2.json")])
    assert [p.pageid for p in result] == [12]
    assert len(s.calls) == 2


def test_gives_up_after_retries():
    with pytest.raises(ApiError):
        pages([FakeResponse({}, status=503)] * 3)


def test_merges_categories_split_across_responses():
    rev = {"revid": 1, "timestamp": "t", "slots": {"main": {"content": "x"}}}
    part1 = {
        "continue": {"clcontinue": "10|B", "continue": "||"},
        "query": {"pages": [{"pageid": 10, "title": "A", "revisions": [rev],
                             "categories": [{"title": "Kategorie:Eins"}]}]},
    }
    part2 = {
        "batchcomplete": True,
        "query": {"pages": [{"pageid": 10, "title": "A",
                             "categories": [{"title": "Kategorie:Zwei"}]}]},
    }
    result, _ = pages([part1, part2])
    assert len(result) == 1
    assert result[0].categories == ("Eins", "Zwei")


def test_page_without_revision_fails_loudly():
    payload = {"batchcomplete": True, "query": {"pages": [{"pageid": 5, "title": "X"}]}}
    with pytest.raises(ApiError):
        pages([payload])


def test_live_response_shape():
    """Aufgezeichnet von der Live-API am 24.11.2026 (Inhalte gekürzt)."""
    unreadable = []
    result = list(iter_raw_pages(FakeSession([load("live_batch.json")]), pause=0, unreadable=unreadable))
    assert [p.title for p in result] == ["Allgemeines", "Altenheim", "Alltagsgeschäfte"]
    assert result[0].categories == ("Inhaltliches",)
    assert result[0].wikitext
    assert unreadable == [{"pageid": 1502, "title": "Adressen", "lastrevid": 1510}]


def test_page_without_revision_collected_when_list_given():
    payload = {"batchcomplete": True, "query": {"pages": [{"pageid": 5, "title": "X", "lastrevid": 9}]}}
    unreadable = []
    assert list(iter_raw_pages(FakeSession([payload]), pause=0, unreadable=unreadable)) == []
    assert unreadable == [{"pageid": 5, "title": "X", "lastrevid": 9}]
