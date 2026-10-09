from src.storage.history import HistoryStorage


def test_previous_day_ignores_today_and_same_day_overwrites(tmp_path, monkeypatch):
    storage = HistoryStorage(tmp_path / "history.json")
    monkeypatch.setattr("src.storage.history.get_cairo_now", lambda: __import__("datetime").datetime(2026, 10, 9, 9))
    data = {"records": [{"date": "2026-10-08", "gold": {"21k": 6100}}]}
    storage.history_file.write_text(__import__("json").dumps(data))

    for price in (6120, 6130):  # two runs on the same day
        storage.save_record(1, price, 1, 1, 1, 1, 1)

    records = storage.load_history()["records"]
    assert [r["date"] for r in records] == ["2026-10-08", "2026-10-09"]
    assert records[-1]["gold"]["21k"] == 6130
    assert storage.get_previous_day_record()["gold"]["21k"] == 6100
