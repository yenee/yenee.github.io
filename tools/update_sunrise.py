import html
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = ROOT / "sunrise-status.json"
SOURCE_URL = "https://afrts.forest.gov.tw/TP01_1.aspx"
TAIPEI = timezone(timedelta(hours=8))


def parse_notice(markup: str, today: date) -> dict[str, str]:
    text = html.unescape(re.sub(r"<[^>]*>", "", markup))
    text = re.sub(r"\s+", "", text)
    match = re.search(
        r"祝山線行駛時間[:：](\d{1,2})月(\d{1,2})日祝山線觀日列車"
        r"(\d{2}:\d{2})發車，回程末班車為(\d{2}:\d{2})，日出時間為(\d{2}:\d{2})",
        text,
    )
    if not match:
        raise ValueError("The official page did not contain a recognized Zhushan notice")

    month, day, departure, return_time, sunrise = match.groups()
    candidates = []
    for year in (today.year - 1, today.year, today.year + 1):
        try:
            candidates.append(date(year, int(month), int(day)))
        except ValueError:
            continue
    if not candidates:
        raise ValueError("The official page contained an invalid service date")
    service_date = min(candidates, key=lambda item: (abs((item - today).days), item < today))

    return {
        "serviceDate": service_date.isoformat(),
        "departureTime": departure,
        "returnTime": return_time,
        "sunriseTime": sunrise,
    }


def update_status() -> bool:
    request = Request(SOURCE_URL, headers={"User-Agent": "AlishanChiayiSlowTravel/1.0"})
    with urlopen(request, timeout=20) as response:
        markup = response.read().decode("utf-8", errors="replace")

    now = datetime.now(TAIPEI)
    bulletin = parse_notice(markup, now.date())
    existing = {}
    try:
        existing = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass
    if not isinstance(existing, dict):
        existing = {}

    fields = ("serviceDate", "departureTime", "returnTime", "sunriseTime")
    unchanged = all(existing.get(field) == bulletin[field] for field in fields)
    updated_at = existing.get("updatedAt")
    if not unchanged or not isinstance(updated_at, str):
        updated_at = now.isoformat(timespec="minutes")
    else:
        try:
            datetime.fromisoformat(updated_at)
        except ValueError:
            updated_at = now.isoformat(timespec="minutes")

    status = {
        **bulletin,
        "updatedAt": updated_at,
        "checkedAt": now.isoformat(timespec="minutes"),
        "sourceUrl": SOURCE_URL,
    }
    if status == existing:
        print("Official Zhushan notice is unchanged; check time is current")
        return False

    STATUS_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if unchanged:
        print(f"Checked unchanged official Zhushan notice: {bulletin['serviceDate']}")
    else:
        print(f"Updated official Zhushan notice: {bulletin['serviceDate']}")
    return True


if __name__ == "__main__":
    update_status()