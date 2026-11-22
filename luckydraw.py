from flask import Flask, jsonify, render_template, request

from lottery import draw_one
from menu import MODE_LABELS, PERIOD_LABELS, POOL_MAP, load_menu

app = Flask(__name__)
menu, recipes = load_menu()

PERIOD_ALIASES = {"早": "breakfast", "中": "lunch", "晚": "dinner"}
MODE_ALIASES = {"单人": "single", "双人": "double"}


@app.route("/") 
def index():
    return render_template("index.html")


@app.post("/api/draw")
def api_draw():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"ok": False, "message": "请求格式不正确"}), 400

    period = str(payload.get("period", "")).strip()
    mode = str(payload.get("mode", "")).strip()

    period_key = PERIOD_ALIASES.get(period, period)
    mode_key = MODE_ALIASES.get(mode, mode)
    if period_key not in PERIOD_LABELS:
        return jsonify({"ok": False, "message": "请先选择用餐时段（早/中/晚）"}), 400
    if mode_key not in MODE_LABELS:
        return jsonify({"ok": False, "message": "请先选择参与人数（单人/双人）"}), 400

    pool_key = POOL_MAP[(period_key, mode_key)]
    try:
        combo = draw_one(menu[pool_key])
    except ValueError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 500

    return jsonify({
        "ok": True,
        "result": {
            "period": PERIOD_LABELS[period_key],
            "mode": MODE_LABELS[mode_key],
            "pool": pool_key,
            "combo": {
                "id": combo["id"],
                "name": combo["name"],
                "minutes": combo["minutes"],
                "structure": combo["structure"],
                "note": combo["note"],
                "dishes": [
                    {"name": recipes[code]["name"], "sections": recipes[code]["sections"]}
                    for code in combo["recipes"]
                ],
            },
        },
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
