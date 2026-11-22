import re
from pathlib import Path

MENU_FILE = Path(__file__).parent / "家常饭食清单.txt"

COMBO_LINE = re.compile(r"^(B1|B2|L1|L2|D1|D2)-(\d{2})｜(.*)$")
RECIPE_TITLE = re.compile(r"^【([A-Z]\d{2})】\s*(.+)$")
SECTION_LINE = re.compile(r"^([^：\s]{1,8})：(.*)$")
CODE = re.compile(r"[A-Z]\d{2}")
MINUTES = re.compile(r"(\d+)\s*分钟")
TIP = re.compile(r"分钟（([^）]+)）")
BLOCK_END = re.compile(r"^(第[一二三四五六七八九十]+章|\d+\.\d+\s|[═=─]{3,})")

POOL_MAP = {
    ("breakfast", "single"): "B1",
    ("breakfast", "double"): "B2",
    ("lunch", "single"): "L1",
    ("lunch", "double"): "L2",
    ("dinner", "single"): "D1",
    ("dinner", "double"): "D2",
}
PERIOD_LABELS = {"breakfast": "早", "lunch": "中", "dinner": "晚"}
MODE_LABELS = {"single": "单人", "double": "双人"}


def _read_text(path):
    for encoding in ("utf-8", "gbk"):
        try:
            return Path(path).read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"无法识别清单文件编码：{path}")


def _extract(text):
    codes = CODE.findall(text)
    minutes = MINUTES.search(text)
    if not codes or not minutes:
        return None
    tip = TIP.search(text)
    return codes, int(minutes.group(1)), tip.group(1) if tip else ""


def _validate(pools, recipes):
    errors = []
    for pool_key, combos in pools.items():
        if not combos:
            errors.append(f"奖池 {pool_key} 为空")
        for combo in combos:
            if not combo["recipes"]:
                errors.append(f"{combo['id']} 没有做法编号")
            for code in combo["recipes"]:
                if code not in recipes:
                    errors.append(f"{combo['id']} 引用了未定义的做法 {code}")
    for code, recipe in recipes.items():
        if not recipe["sections"]:
            errors.append(f"做法 {code} 没有任何内容")
    if errors:
        raise ValueError("菜单数据有问题：\n" + "\n".join(errors))


def load_menu(path=MENU_FILE):
    pools = {key: [] for key in POOL_MAP.values()}
    recipes = {}
    combo = None
    recipe = None

    for raw in _read_text(path).splitlines():
        line = raw.strip()

        if not line:
            combo = None
            continue

        if BLOCK_END.match(line):
            combo = None
            recipe = None
            continue

        title = RECIPE_TITLE.match(line)
        if title:
            recipe = {"name": title.group(2).strip(), "sections": []}
            recipes[title.group(1)] = recipe
            combo = None
            continue

        if recipe is not None:
            section_match = SECTION_LINE.match(line)
            if section_match:
                content = section_match.group(2).strip()
                recipe["sections"].append({
                    "label": section_match.group(1),
                    "lines": [content] if content else [],
                })
            else:
                if not recipe["sections"]:
                    recipe["sections"].append({"label": "说明", "lines": []})
                recipe["sections"][-1]["lines"].append(line)
            continue

        combo_match = COMBO_LINE.match(line)
        if combo_match:
            pool_key, num, rest = combo_match.groups()
            found = _extract(rest)
            if found:
                codes, minutes, tip = found
                name = rest[: CODE.search(rest).start()].strip()
            else:
                codes, minutes, tip, name = [], 0, "", rest.strip()
            combo = {
                "id": f"{pool_key}-{num}",
                "name": name,
                "recipes": codes,
                "minutes": minutes,
                "structure": "",
                "note": tip,
            }
            pools[pool_key].append(combo)
            continue

        if combo is None:
            continue

        if line.startswith("做法："):
            found = _extract(line[3:])
            if found:
                codes, minutes, tip = found
                combo["recipes"] = codes
                combo["minutes"] = minutes
                if tip:
                    combo["note"] = f"{combo['note']}；{tip}" if combo["note"] else tip
        elif line.startswith("结构："):
            combo["structure"] = line[3:].strip()
        elif line.startswith("（") and line.endswith("）"):
            combo["note"] = f"{combo['note']}；{line}" if combo["note"] else line

    _validate(pools, recipes)
    return pools, recipes
