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

    def test_map_reference_gallery_keeps_attributed_lazy_images(self):
        image_sources = (
            "https://www.94iprofun.com/upload/images/MAP%E9%98%BF%E9%87%8C%E5%B1%B1%E5%9C%92%E5%8D%80%E5%85%A7-%E9%A3%AF%E5%BA%97%E4%B8%80%E8%A6%BD%E5%9C%96.jpg",
            "https://www.94iprofun.com/upload/images/%E5%9C%B0%E5%9C%96_%E9%98%BF%E9%87%8C%E5%B1%B1%E6%A3%AE%E6%9E%97%E5%9C%92%E5%8D%80%E5%9C%B0%E5%9C%96001.jpg",
            "https://www.94iprofun.com/upload/images/%E5%9C%B0%E5%9C%96_%E9%98%BF%E9%87%8C%E5%B1%B1%E6%A3%AE%E6%9E%97%E5%9C%92%E5%8D%80%E5%9C%B0%E5%9C%96.jpg",
            "https://www.94iprofun.com/upload/images/Map_%E5%A5%AE%E8%B5%B7%E6%B9%96001%20(1170%20x%20772).jpg",
            "https://static-assets.oen.tw/images/img-33BAFiaFOGz92cZTk4dAilqfq4c.jpg",
            "https://margaret.tw/wp-content/uploads/2013/11/%E6%B0%B4%E5%B1%B1%E7%99%82%E7%99%92%E6%AD%A5%E9%81%93photo6.jpg",
        )
        service_worker = (SITE_HTML.parent / "sw.js").read_text(encoding="utf-8")
        for image_source in image_sources:
            with self.subTest(image_source=image_source):
                self.assertTrue(f'src="{image_source}"' in self.html, "Image src should remain at its original URL")
                self.assertTrue(image_source in service_worker, "Missing Service Worker image URL")
        for expected in ('data-map-gallery="true"', 'alt="阿里山園區飯店一覽圖"',
                         'alt="水山療癒步道環境照片"', 'alt="奮起湖地圖"', 'loading="lazy"', "來源："):
            with self.subTest(gallery=expected):
                self.assertTrue(expected in self.html, f"Missing: {expected}")
        for expected in (
            'mode: "no-cors"', "REFERENCE_IMAGE_URLS", "REFERENCE_IMAGE_URLS.has(url.href)",
            "cache.put(imageUrl, response.clone())", "cache.put(event.request, response.clone())",
            "cache.match(event.request)",
        ):
            with self.subTest(service_worker=expected):
                self.assertTrue(expected in service_worker, f"Missing: {expected}")
        self.assertFalse("tile.openstreetmap.org" in service_worker, "OSM tiles must not be cached offline")
        self.assertTrue("v24" in service_worker, "Service Worker cache version should be v24")
        for library_asset in ("leaflet.js", "leaflet.css", "LICENSE"):
            with self.subTest(library_asset=library_asset):
                self.assertTrue(f"./vendor/leaflet/{library_asset}" in self.html or library_asset == "LICENSE", f"Missing library link: {library_asset}")
                self.assertTrue(f'"vendor/leaflet/{library_asset}"' in service_worker, f"Not precached: {library_asset}")
                self.assertTrue((SITE_HTML.parent / "vendor" / "leaflet" / library_asset).is_file())
        library_file = (SITE_HTML.parent / "vendor" / "leaflet" / "leaflet.js").read_text(encoding="utf-8")
        self.assertTrue("1.9.4" in library_file, "Unexpected Leaflet version")

    def test_map_shows_osm_all_stops_and_ordered_route(self):
        for expected in (
            "https://tile.openstreetmap.org/{z}/{x}/{y}.png", "OpenStreetMap</a> contributors",
            "L.map(", "L.tileLayer(", "L.marker(", "L.polyline(",
            "Number.isFinite(latitude)", "index + 1", "tripMap.invalidateSize(",
            "順序線僅表示停留順序，不是實際道路或步道",
            "OSM 底圖與外部導航需連網",
        ):
            with self.subTest(expected=expected):
                self.assertTrue(expected in self.html, f"Missing: {expected}")
        self.assertFalse('<iframe class="map-frame"' in self.html, "Old map iframe remains")
        self.assertFalse("maplibregl" in self.html, "MapLibre renderer should be removed")
        self.assertIn('class="map-frame" id="map-frame"', self.html)

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

    def test_sunrise_itinerary_and_presale_reminder(self):
        for expected in (
            '["05:00", "起床、走路至沼平車站", "步行約 5 分鐘；記得帶早餐。", "步行"]',
            '["05:30", "沼平車站 → 祝山站"',
            '步行 祝山站 → 小笠原山',
            '約 500 公尺大陡坡，約 15 分鐘腳程',
            '["07:00", "回程搭小火車或遊園車 → 沼平車站"',
            '前一日 16:30 前', '沼平車站無預售服務',
            '沼平車站發車時間前 20 分鐘', '沼平至祝山約 17 分鐘',
        ):
            with self.subTest(expected=expected):
                self.assertTrue(expected in self.html, expected)

    def test_bus_fares_match_current_fare_lookup(self):
        for expected in (
            "全票 $98 / 半票 $49（阿里山 → 奮起湖）",
            "全票 $98（阿里山 → 奮起湖）",
            "奮起湖 → 嘉義火車站：全票 $177 / 半票 $89",
            "全票 $98、半票 $49",
        ):
            with self.subTest(expected=expected):
                self.assertTrue(expected in self.html, f"Missing: {expected}")

    def test_day_one_uses_ciyun_viewpoint_instead_of_museum(self):
        self.assertFalse("阿里山博物館" in self.html, "Old museum stop remains")
        for expected in ("慈雲觀景", "https://maps.app.goo.gl/Ce9h5sdyZfWVwozj8", "看夕陽雲海"):
            with self.subTest(expected=expected):
                self.assertTrue(expected in self.html, f"Missing: {expected}")

    def test_updated_day_one_and_day_two_schedule(self):
        for expected in (
            '["13:00", "步行至遊客服務中心"', '商店買簡易午餐',
            '["14:30", "步道健行"', '["15:00", "香林服務區吃小吃點心"',
            '["16:00", "步道健行"', '["17:00", "慈雲觀景"',
            '["17:30", "前往商店街"', '["18:00", "商店街晚餐"',
            '["20:15", "飯店晚間回程接駁車"',
            '["20:30", "入住阿里山閣大飯店"', '巨木群棧道2',
            '步行約 5 分鐘；記得帶早餐。',
            'https://maps.app.goo.gl/vPgLwCoidxHcEvE87',
            'https://maps.app.goo.gl/2YxE1XsBzpFxUDYd6',
            '["09:00", "退房"', '["09:20", "飯店接駁 → 阿里山旅客服務中心"',
            '08:40 / 09:20 / 09:50', '["10:00", "步行至阿里山轉運站"',
            '["10:10", "搭台灣好行 7329A → 奮起湖"',
            '["11:00", "奮起湖車站寄放行李"', '["11:30", "奮起湖午餐與點心"',
            '["12:00", "百年肖楠林 · 散步"',
            '["14:00", "拿行李、搭阿里山號 → 嘉義市區"',
            '奮起湖車站 14:31 開車', '嘉義車站 16:51 抵達',
            '["18:30", "前往高鐵嘉義站"',
            '<td>嘉義縣公車 7322A</td><td>10:10</td><td>11:00</td>',
            "https://www.google.com/maps/search/?api=1&query=%E4%B8%80%E5%93%81%E9%A6%99%E9%87%8E%E7%94%9F%E6%84%9B%E7%8E%89",
            "https://www.google.com/maps/search/?api=1&query=%E6%9C%88%E5%8F%B0%E8%8C%B6%E9%A6%99%E9%8A%85%E9%91%BC%E7%87%92",
            '"燒肉觀止": "https://maps.app.goo.gl/x7MYVGzJ5BDuhRBA6"',
            'name: "林鐵本線小火車", meta: "11/23 · 11/09 開放預訂 · 全段 $600 / 奮起湖區間 $384", done: true',
        ):
            with self.subTest(expected=expected):
                self.assertTrue(expected in self.html, f"Missing: {expected}")
        self.assertFalse('"先帶早餐；' in self.html, "Water trail note still says to bring breakfast")
        self.assertFalse('"備註：可至商店買簡易午餐。' in self.html, "Lunch note still has the word 備註")

    def test_removed_trip_titles_and_car_rental_references(self):
        self.assertTrue('<h1>阿里山嘉義慢旅</h1>' in self.html)
        self.assertFalse('<h2 id="itinerary-heading">沿著山線慢慢走</h2>' in self.html)
        self.assertTrue('aria-label="每日行程"' in self.html)
        self.assertTrue('body[data-layout-mode="desktop"] .hero-art { align-self: start; margin-top: 15px; }' in self.html)
        for removed in ("租車自駕 →", "前往高鐵嘉義站還車", "嘉義市區租車", "租車安排尚未確認"):
            with self.subTest(removed=removed):
                self.assertFalse(removed in self.html, f"Removed text remains: {removed}")


if __name__ == "__main__":
    unittest.main()