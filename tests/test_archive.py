import json
import os

import pytest

from lexikon.archive import load_raw, sync_raw
from lexikon.models import RawPage


def page(pageid=123, revid=1, text="Wikitext mit ''Format'' und {{§|30|SGB I}}"):
    return RawPage(pageid=pageid, title=f"Seite {pageid}", revid=revid,
                   timestamp="2024-01-01T00:00:00Z", wikitext=text, categories=("K",))


def test_writes_by_pageid(tmp_path):
    p = page()
    res = sync_raw([p], tmp_path)
    data = json.loads((tmp_path / "123.json").read_text(encoding="utf-8"))
    assert data["wikitext"] == p.wikitext
    assert res.written == 1


def test_unchanged_revid_not_rewritten(tmp_path):
    sync_raw([page()], tmp_path)
    f = tmp_path / "123.json"
    os.utime(f, (1, 1))
    res = sync_raw([page()], tmp_path)
    assert res.unchanged == 1 and res.written == 0
    assert f.stat().st_mtime == 1


def test_new_revid_rewritten(tmp_path):
    sync_raw([page()], tmp_path)
    res = sync_raw([page(revid=2, text="neu")], tmp_path)
    assert res.written == 1
    assert load_raw(tmp_path)[0].wikitext == "neu"


def test_missing_page_logged_not_deleted(tmp_path):
    sync_raw([page(123), page(124)], tmp_path)
    res = sync_raw([page(124)], tmp_path)
    assert res.deleted == [123]
    assert (tmp_path / "123.json").exists()
    log = [json.loads(l) for l in (tmp_path / "_deleted.jsonl").read_text().splitlines()]
    assert log == [{"pageid": 123, "title": "Seite 123", "last_revid": 1}]


def test_deleted_logged_only_once(tmp_path):
    sync_raw([page(123), page(124)], tmp_path)
    sync_raw([page(124)], tmp_path)
    sync_raw([page(124)], tmp_path)
    assert len((tmp_path / "_deleted.jsonl").read_text().splitlines()) == 1


def test_iterator_error_writes_no_deletions(tmp_path):
    sync_raw([page(123), page(124)], tmp_path)

    def broken():
        yield page(124)
        raise RuntimeError("Abbruch")

    with pytest.raises(RuntimeError):
        sync_raw(broken(), tmp_path)
    assert not (tmp_path / "_deleted.jsonl").exists()


def test_load_raw_skips_log(tmp_path):
    sync_raw([page(123), page(124)], tmp_path)
    sync_raw([page(124)], tmp_path)
    assert {p.pageid for p in load_raw(tmp_path)} == {123, 124}


def test_load_raw_excludes_deleted_when_asked(tmp_path):
    sync_raw([page(123), page(124)], tmp_path)
    sync_raw([page(124)], tmp_path)
    assert {p.pageid for p in load_raw(tmp_path, include_deleted=False)} == {124}


def test_category_change_without_new_revid_is_written(tmp_path):
    sync_raw([page()], tmp_path)
    changed = RawPage(pageid=123, title="Seite 123", revid=1, timestamp="2024-01-01T00:00:00Z",
                      wikitext=page().wikitext, categories=("K", "Neu"))
    res = sync_raw([changed], tmp_path)
    assert res.written == 1
    assert load_raw(tmp_path)[0].categories == ("K", "Neu")


def test_unreadable_pages_never_logged_as_deleted(tmp_path):
    sync_raw([page(123), page(124)], tmp_path)
    unreadable = []

    def pages_then_unreadable():
        yield page(124)
        unreadable.append({"pageid": 123, "title": "Seite 123", "lastrevid": 2})

    res = sync_raw(pages_then_unreadable(), tmp_path, unreadable=unreadable)
    assert res.deleted == []
    assert res.unreadable == 1
    assert not (tmp_path / "_deleted.jsonl").exists()
    log = [json.loads(l) for l in (tmp_path / "_unreadable.jsonl").read_text().splitlines()]
    assert log == [{"pageid": 123, "title": "Seite 123", "lastrevid": 2}]


def test_unreadable_log_replaced_each_run(tmp_path):
    sync_raw([], tmp_path, unreadable=[{"pageid": 1, "title": "A", "lastrevid": 1}])
    sync_raw([], tmp_path, unreadable=[])
    assert not (tmp_path / "_unreadable.jsonl").exists()
