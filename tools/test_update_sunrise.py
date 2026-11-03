import json
import tempfile
import unittest
from datetime import date, datetime, timedelta
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

import update_sunrise
from update_sunrise import parse_notice


class ParseNoticeTests(unittest.TestCase):
    def test_extracts_the_official_train_and_sunrise_times(self):
        markup = """
        <p>祝山線行駛時間：11月02日祝山線觀日列車05:30發車，
        回程末班車為07:10，日出時間為06:28。</p>
        """

        self.assertEqual(parse_notice(markup, date(2026, 11, 2)), {
            "serviceDate": "2026-11-02",
            "departureTime": "05:30",
            "returnTime": "07:10",
            "sunriseTime": "06:28",
        })

    def test_assigns_next_year_when_notice_crosses_new_year(self):
        markup = "祝山線行駛時間：1月01日祝山線觀日列車06:00發車，回程末班車為08:00，日出時間為07:00。"

        self.assertEqual(parse_notice(markup, date(2026, 12, 31))["serviceDate"], "2027-01-01")

    def test_rejects_pages_without_a_daily_bulletin(self):
        with self.assertRaises(ValueError):
            parse_notice("祝山線行駛時間：資料更新中", date(2026, 11, 2))


class UpdateStatusTests(unittest.TestCase):
    def setUp(self):
        self.today = datetime.now(update_sunrise.TAIPEI).date()
        self.markup = (
            f"祝山線行駛時間：{self.today.month}月{self.today.day}日"
            "祝山線觀日列車05:30發車，回程末班車為07:10，日出時間為06:28。"
        )
        self.bulletin = parse_notice(self.markup, self.today)
        self.directory = tempfile.TemporaryDirectory()
        self.status_path = Path(self.directory.name) / "sunrise-status.json"
        self.status_path.write_text("{}\n", encoding="utf-8")
        self.path_patcher = patch.object(update_sunrise, "STATUS_PATH", self.status_path)
        self.path_patcher.start()
        self.addCleanup(self.path_patcher.stop)
        self.addCleanup(self.directory.cleanup)

    def fetch_markup(self):
        return patch.object(update_sunrise, "urlopen", return_value=BytesIO(self.markup.encode("utf-8")))

    def test_changed_bulletin_updates_notice_and_check_times(self):
        existing = {
            **self.bulletin,
            "departureTime": "05:00",
            "updatedAt": "2000-01-01T00:00+08:00",
            "checkedAt": "2000-01-01T00:00+08:00",
            "sourceUrl": update_sunrise.SOURCE_URL,
        }
        self.status_path.write_text(json.dumps(existing), encoding="utf-8")
        before = datetime.now(update_sunrise.TAIPEI)

        with self.fetch_markup():
            self.assertTrue(update_sunrise.update_status())

        after = datetime.now(update_sunrise.TAIPEI)
        saved = json.loads(self.status_path.read_text(encoding="utf-8"))
        earliest = before.replace(second=0, microsecond=0)
        self.assertEqual(saved["departureTime"], "05:30")
        self.assertGreaterEqual(datetime.fromisoformat(saved["updatedAt"]), earliest)
        self.assertGreaterEqual(datetime.fromisoformat(saved["checkedAt"]), earliest)
        self.assertLessEqual(datetime.fromisoformat(saved["checkedAt"]), after)

    def test_unchanged_bulletin_advances_check_time_only(self):
        previous_check = (datetime.now(update_sunrise.TAIPEI) - timedelta(days=1)).isoformat(timespec="minutes")
        existing = {
            **self.bulletin,
            "updatedAt": "2000-01-01T00:00+08:00",
            "checkedAt": previous_check,
            "sourceUrl": update_sunrise.SOURCE_URL,
        }
        self.status_path.write_text(json.dumps(existing), encoding="utf-8")
        before = datetime.now(update_sunrise.TAIPEI)

        with self.fetch_markup():
            self.assertTrue(update_sunrise.update_status())

        after = datetime.now(update_sunrise.TAIPEI)
        saved = json.loads(self.status_path.read_text(encoding="utf-8"))
        earliest = before.replace(second=0, microsecond=0)
        self.assertEqual(saved["updatedAt"], existing["updatedAt"])
        self.assertGreaterEqual(datetime.fromisoformat(saved["checkedAt"]), earliest)
        self.assertLessEqual(datetime.fromisoformat(saved["checkedAt"]), after)

    def test_fetch_failure_keeps_previous_json_unchanged(self):
        previous = self.status_path.read_text(encoding="utf-8")

        with patch.object(update_sunrise, "urlopen", side_effect=URLError("offline")):
            with self.assertRaises(URLError):
                update_sunrise.update_status()

        self.assertEqual(self.status_path.read_text(encoding="utf-8"), previous)


if __name__ == "__main__":
    unittest.main()