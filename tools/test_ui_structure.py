from html.parser import HTMLParser
from pathlib import Path
import unittest


SITE_HTML = Path(__file__).resolve().parents[1] / "index.html"


class SiteStructureParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.panels = set()
        self.primary_views = []
        self.more_targets = set()
        self._nav_stack = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.add(attributes["id"])
        if tag == "section" and "data-panel" in attributes:
            self.panels.add(attributes["data-panel"])
        if tag == "nav":
            self._nav_stack.append(attributes.get("aria-label", ""))
        if tag == "button":
            view = attributes.get("data-view")
            if view and self._nav_stack and self._nav_stack[-1] == "主要導覽":
                self.primary_views.append(view)
            target = attributes.get("data-open-panel")
            if target:
                self.more_targets.add(target)

    def handle_endtag(self, tag):
        if tag == "nav" and self._nav_stack:
            self._nav_stack.pop()


class SiteStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = SITE_HTML.read_text(encoding="utf-8")
        cls.parser = SiteStructureParser()
        cls.parser.feed(cls.html)

    def test_primary_navigation_has_four_approved_views(self):
        self.assertEqual(self.parser.primary_views, ["home", "itinerary", "map", "more"])

    def test_more_menu_keeps_existing_feature_panels_reachable(self):
        self.assertEqual(
            self.parser.more_targets,
            {"weather", "todos", "transport", "notes", "hotel", "packing"},
        )

    def test_original_interaction_hooks_remain_present(self):
        self.assertTrue({
            "schedule-search", "day-content", "weather-refresh", "todo-list",
            "packing-groups", "packing-edit", "app-install", "app-update",
        }.issubset(self.parser.ids))
        self.assertTrue({
            "home", "itinerary", "map", "more", "weather", "todos",
            "transport", "notes", "hotel", "packing",
        }.issubset(self.parser.panels))

    def test_park_shuttle_section_is_present(self):
        shuttle_start = self.html.index('data-park-shuttle="true"')
        shuttle_end = self.html.index("</section>", shuttle_start)
        shuttle_section = self.html[shuttle_start:shuttle_end]
        self.assertTrue(all(value in shuttle_section for value in (
            "沼平線", "(藍線)", "香林線", "(紅線)", "候車總站", "遊客中心站",
            "2.2 公里", "10 分鐘", "1.8 公里", "8 分鐘", "含上下車", "AM 08:00~PM 05:00",
            "(05)267-9917", "全票單程", "$70", "$35", "$150", "$75", "$100",
            "$50", "05:20", "05:50", "10/27 起", "facebook.com/alishanebus",
        )))

    def test_sunrise_status_omits_expired_notice_warning(self):
        self.assertFalse("公告可能過期，請查看林鐵官方公告" in self.html)


if __name__ == "__main__":
    unittest.main()