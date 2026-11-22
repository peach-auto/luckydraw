const drawBtn = document.getElementById("draw-btn");
const resetBtn = document.getElementById("reset-btn");
const hint = document.getElementById("hint");
const resultSection = document.getElementById("result");
const resultTag = document.getElementById("result-tag");
const resultName = document.getElementById("result-name");
const resultMeta = document.getElementById("result-meta");
const resultRecipes = document.getElementById("result-recipes");
const resultExtra = document.getElementById("result-extra");

function getSelected(name) {
  const checked = document.querySelector(`input[name="${name}"]:checked`);
  return checked ? checked.value : null;
}

function updateDrawButton() {
  const period = getSelected("period");
  const mode = getSelected("mode");
  drawBtn.disabled = !(period && mode);
  hint.className = "hint";
  if (period && mode) {
    hint.textContent = `已选择：${period}餐 · ${mode}，可以开抽了！`;
    hint.classList.add("ready");
  } else if (period) {
    hint.textContent = "还差一步：请选择参与人数";
  } else if (mode) {
    hint.textContent = "还差一步：请选择用餐时段";
  } else {
    hint.textContent = "请先选择用餐时段和参与人数";
  }
}

document.querySelectorAll("input[type=radio]").forEach((el) => {
  el.addEventListener("change", updateDrawButton);
});

function renderRecipes(dishes) {
  resultRecipes.innerHTML = "";
  dishes.forEach((dish, index) => {
    const details = document.createElement("details");
    details.className = "recipe";
    if (index === 0) details.open = true; // 第一道默认展开，让用户直接看到做法

    const summary = document.createElement("summary");
    summary.textContent = dish.name;
    details.appendChild(summary);

    const body = document.createElement("div");
    body.className = "recipe-body";
    dish.sections.forEach((section) => {
      const row = document.createElement("div");
      row.className = "recipe-row";

      const label = document.createElement("span");
      label.className = "label";
      label.textContent = section.label;
      row.appendChild(label);

      section.lines.forEach((text) => {
        const line = document.createElement("p");
        line.textContent = text;
        row.appendChild(line);
      });
      body.appendChild(row);
    });
    details.appendChild(body);
    resultRecipes.appendChild(details);
  });
}

function renderResult(result) {
  const combo = result.combo;
  resultTag.textContent = `${result.period}餐 · ${result.mode}`;
  resultName.textContent = combo.name;
  resultMeta.textContent = `⏱ 约 ${combo.minutes} 分钟`;

  const extras = [combo.structure, combo.note].filter(Boolean);
  resultExtra.textContent = extras.join("　");
  resultExtra.classList.toggle("hidden", extras.length === 0);

  renderRecipes(combo.dishes);

  resultSection.classList.remove("hidden", "pop");
  void resultSection.offsetWidth; // 强制重排，让动画每次都能重播
  resultSection.classList.add("pop");
  resultSection.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function draw() {
  const period = getSelected("period");
  const mode = getSelected("mode");
  if (!period || !mode) return;

  drawBtn.disabled = true;
  drawBtn.textContent = "抽取中…";

  try {
    const resp = await fetch("/api/draw", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ period, mode }),
    });
    const data = await resp.json();
    if (data.ok) {
      renderResult(data.result);
    } else {
      hint.className = "hint error";
      hint.textContent = data.message;
    }
  } catch {
    hint.className = "hint error";
    hint.textContent = "网络异常，请稍后再试";
  } finally {
    drawBtn.textContent = "🎲 开始抽奖";
    updateDrawButton();
  }
}

drawBtn.addEventListener("click", draw);

resetBtn.addEventListener("click", () => {
  document.querySelectorAll("input[type=radio]").forEach((el) => {
    el.checked = false;
  });
  resultSection.classList.add("hidden");
  updateDrawButton();
});

updateDrawButton();
