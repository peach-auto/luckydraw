import random
import unittest

from luckydraw import app
from lottery import draw_one
from menu import load_menu

menu, recipes = load_menu()


class MenuParserTests(unittest.TestCase):
    EXPECTED_COUNTS = {"B1": 20, "B2": 10, "L1": 20, "L2": 16, "D1": 16, "D2": 16}

    def test_pool_counts(self):
        for pool_key, expected in self.EXPECTED_COUNTS.items():
            self.assertEqual(len(menu[pool_key]), expected, pool_key)

    def test_combo_fields_complete(self):
        for combos in menu.values():
            for combo in combos:
                self.assertTrue(combo["name"], f"{combo['id']} 缺名字")
                self.assertGreaterEqual(combo["minutes"], 1, f"{combo['id']} 缺耗时")
                self.assertTrue(combo["recipes"], f"{combo['id']} 缺做法编号")

    def test_note_captured(self):
        combo = next(c for c in menu["L1"] if c["id"] == "L1-13")
        self.assertIn("可前一晚炖", combo["note"])

    def test_recipe_names(self):
        self.assertEqual(recipes["M01"]["name"], "白米饭")
        self.assertIn("番茄鸡蛋面", recipes["Z05"]["name"])

    def test_recipe_sections_parsed(self):
        labels = [section["label"] for section in recipes["B08"]["sections"]]
        self.assertEqual(labels, ["用料", "调料", "做法", "关键"])
        steps = next(s for s in recipes["B08"]["sections"] if s["label"] == "做法")
        self.assertEqual(len(steps["lines"]), 5)
        self.assertTrue(steps["lines"][0].startswith("1."))

    def test_no_separator_leaked_into_recipes(self):
        for code, recipe in recipes.items():
            for section in recipe["sections"]:
                for line in section["lines"]:
                    self.assertNotIn("====", line, f"{code} 的「{section['label']}」混入了分隔线")
                    self.assertTrue(line.strip(), f"{code} 的「{section['label']}」有空行")

    def test_no_codes_in_user_facing_text(self):
        """用户看到的任何文字里都不应出现 B08 / M01 这类内部编号。"""
        for combos in menu.values():
            for combo in combos:
                for field in ("name", "structure", "note"):
                    self.assertNotRegex(combo[field], r"[A-Z]\d{2}", f"{combo['id']} 的 {field}")
                for code in combo["recipes"]:
                    for section in recipes[code]["sections"]:
                        for line in section["lines"]:
                            self.assertNotRegex(line, r"[A-Z]\d{2}", f"{code} 的「{section['label']}」")


class LotteryFairnessTests(unittest.TestCase):
    def setUp(self):
        self.pool = menu["D1"]

    def test_draw_within_pool(self):
        for _ in range(100):
            self.assertIn(draw_one(self.pool, random.Random(1)), self.pool)

    def test_uniform_distribution(self):
        rng = random.Random(2026)
        counts = {id(combo): 0 for combo in self.pool}
        for _ in range(10000):
            counts[id(draw_one(self.pool, rng))] += 1
        expected = 10000 / len(self.pool)
        for count in counts.values():
            self.assertLessEqual(abs(count - expected), expected * 0.3)

    def test_empty_pool_raises(self):
        with self.assertRaises(ValueError):
            draw_one([])


class ApiTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def _post(self, payload=None, raw=None):
        if raw is not None:
            return self.client.post("/api/draw", data=raw, content_type="application/json")
        return self.client.post("/api/draw", json=payload)

    def test_index_page(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("今天吃什么", resp.get_data(as_text=True))

    def test_missing_period_rejected(self):
        self.assertEqual(self._post({"mode": "单人"}).status_code, 400)

    def test_missing_mode_rejected(self):
        self.assertEqual(self._post({"period": "早"}).status_code, 400)

    def test_empty_body_rejected(self):
        self.assertEqual(self._post({}).status_code, 400)

    def test_malformed_body_rejected(self):
        self.assertEqual(self._post(raw="{not json").status_code, 400)

    def test_invalid_value_rejected(self):
        self.assertEqual(self._post({"period": "夜宵", "mode": "单人"}).status_code, 400)

    def test_all_six_combinations_ok(self):
        for period in ("早", "中", "晚"):
            for mode in ("单人", "双人"):
                resp = self._post({"period": period, "mode": mode})
                self.assertEqual(resp.status_code, 200)
                data = resp.get_json()
                self.assertTrue(data["ok"])
                self.assertEqual(data["result"]["period"], period)
                self.assertEqual(data["result"]["mode"], mode)

                dishes = data["result"]["combo"]["dishes"]
                self.assertTrue(dishes)
                for dish in dishes:
                    # 返回给用户看的菜名里不能出现 B08 / M01 这类编号
                    self.assertNotRegex(dish["name"], r"[A-Z]\d{2}")
                    self.assertTrue(dish["sections"], f"{dish['name']} 没有做法")


if __name__ == "__main__":
    unittest.main()
