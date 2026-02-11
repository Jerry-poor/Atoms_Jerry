from __future__ import annotations

import json
from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.llm.client import ChatMessage, chat


class RunState(TypedDict, total=False):
    run_id: str
    input: str
    mode: str
    roles: list[str]
    role_order: list[str]
    role_index: int
    outputs: dict[str, str]
    files: list[dict]
    user_rules: list[str]
    project_rules: dict
    architecture: dict
    task_view: dict
    final: dict | None
    errors: list[str]

def _extract_json_obj(text: str) -> dict | None:
    """Best-effort JSON object extraction.

    Some models may wrap JSON with prose or accidentally emit multiple JSON-looking blocks.
    We scan for the first balanced {...} region that parses as JSON.
    """

    t = (text or "").strip()
    if not t:
        return None

    start = t.find("{")
    if start < 0:
        return None

    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(t)):
        ch = t[i]
        if in_str:
            if esc:
                esc = False
                continue
            if ch == "\\":
                esc = True
                continue
            if ch == '"':
                in_str = False
            continue

        if ch == '"':
            in_str = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = t[start : i + 1]
                try:
                    obj = json.loads(candidate)
                except Exception:
                    # Continue searching: there might be another JSON object later.
                    nxt = t.find("{", i + 1)
                    if nxt < 0:
                        return None
                    start = nxt
                    depth = 0
                    in_str = False
                    esc = False
                    continue
                return obj if isinstance(obj, dict) else None

    return None


def _normalize_files(obj: dict) -> tuple[str, list[dict]]:
    summary = str(obj.get("summary") or "").strip()
    files_in = obj.get("files")
    out: list[dict] = []
    if isinstance(files_in, list):
        for f in files_in:
            if not isinstance(f, dict):
                continue
            path = str(f.get("path") or "").strip()
            content = str(f.get("content") or "")
            if not path:
                continue
            out.append({"path": path, "content": content})
    return summary, out


def _is_snake_request(text: str) -> bool:
    t = (text or "").lower()
    return ("snake" in t) or ("贪吃蛇" in text)

def _is_stock_premium_request(text: str) -> bool:
    t = (text or "").lower()
    return ("股票" in text and "溢价" in text) or ("premium" in t and ("stock" in t or "equity" in t)) or ("监控" in text and ("溢价" in text or "价差" in text))

def _has_required_files(files: list[dict], required_paths: set[str]) -> bool:
    required = {p.strip().lower().replace("\\", "/") for p in required_paths if p and p.strip()}
    if not required:
        return True
    paths = set()
    for f in files or []:
        if not isinstance(f, dict):
            continue
        p = str(f.get("path") or "").strip().lower().replace("\\", "/")
        if p:
            paths.add(p)
    return required.issubset(paths)


def _merge_files(primary: list[dict], secondary: list[dict]) -> list[dict]:
    """Merge file lists by path; primary wins on conflicts."""
    out: list[dict] = []
    seen: set[str] = set()
    for src in (primary or [], secondary or []):
        for f in src:
            if not isinstance(f, dict):
                continue
            p = str(f.get("path") or "").strip()
            if not p:
                continue
            key = p.lower().replace("\\", "/")
            if key in seen:
                continue
            seen.add(key)
            out.append({"path": p, "content": str(f.get("content") or "")})
    return out


def _snake_web_files() -> list[dict]:
    # Minimal runnable Snake (canvas) demo.
    return [
        {
            "path": "index.html",
            "content": """<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Snake Demo</title>
    <link rel="stylesheet" href="./style.css" />
  </head>
  <body>
    <main class="wrap">
      <header class="top">
        <h1>贪吃蛇</h1>
        <div class="meta">
          <span id="score">Score: 0</span>
          <button id="btnRestart" type="button">Restart</button>
        </div>
      </header>
      <canvas id="c" width="560" height="560" aria-label="Snake game canvas"></canvas>
      <p class="hint">
        方向键/WASD 控制。空格暂停。触屏可用屏幕按钮。
      </p>
      <div class="pad" aria-hidden="true">
        <button data-dir="up">▲</button>
        <div class="row">
          <button data-dir="left">◀</button>
          <button data-dir="down">▼</button>
          <button data-dir="right">▶</button>
        </div>
      </div>
    </main>
    <script src="./app.js"></script>
  </body>
</html>
""",
        },
        {
            "path": "style.css",
            "content": """:root{--bg:#0b1020;--fg:#e8ecff;--muted:#9aa3c7;--card:#111a33;--grid:#1b2650;--snake:#7cf7b4;--food:#ff7aa2;--btn:#1d2a58}
*{box-sizing:border-box}
body{margin:0;font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Arial; background:radial-gradient(1000px 600px at 20% 10%, #1a2a66 0%, transparent 55%),var(--bg); color:var(--fg); min-height:100vh; display:flex; align-items:center; justify-content:center; padding:24px}
.wrap{width:min(900px,100%); background:linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02)); border:1px solid rgba(255,255,255,.10); border-radius:20px; padding:18px 18px 22px; box-shadow:0 24px 80px rgba(0,0,0,.35)}
.top{display:flex; align-items:center; justify-content:space-between; gap:12px; padding:8px 6px 16px}
h1{margin:0; font-size:20px; letter-spacing:.04em}
.meta{display:flex; align-items:center; gap:10px; color:var(--muted); font-size:13px}
button{cursor:pointer; border-radius:10px; border:1px solid rgba(255,255,255,.14); background:var(--btn); color:var(--fg); padding:8px 10px; font-size:12px}
button:hover{filter:brightness(1.06)}
canvas{width:min(560px,100%); aspect-ratio:1/1; display:block; margin:0 auto; border-radius:16px; background:linear-gradient(180deg, rgba(255,255,255,.05), rgba(255,255,255,.02)); border:1px solid rgba(255,255,255,.12)}
.hint{margin:14px 6px 0; text-align:center; color:var(--muted); font-size:12px}
.pad{display:none; margin:14px auto 0; width:min(280px, 100%); gap:10px; justify-content:center; align-items:center}
.pad .row{display:flex; gap:10px; justify-content:center}
.pad button{width:64px; height:48px}
@media (max-width: 560px){.pad{display:flex; flex-direction:column}}
""",
        },
        {
            "path": "app.js",
            "content": """(() => {
  const canvas = document.getElementById('c');
  const ctx = canvas.getContext('2d');
  const scoreEl = document.getElementById('score');
  const btnRestart = document.getElementById('btnRestart');

  const SIZE = 28; // 28x28 grid
  const CELL = canvas.width / SIZE;

  function randCell() {
    return { x: Math.floor(Math.random() * SIZE), y: Math.floor(Math.random() * SIZE) };
  }

  function same(a, b) { return a.x === b.x && a.y === b.y; }

  let snake, dir, nextDir, food, score, tickMs, paused, timer;

  function reset() {
    snake = [{ x: 8, y: 14 }, { x: 7, y: 14 }, { x: 6, y: 14 }];
    dir = { x: 1, y: 0 };
    nextDir = dir;
    score = 0;
    tickMs = 110;
    paused = false;
    spawnFood();
    updateScore();
    startLoop();
  }

  function spawnFood() {
    let f = randCell();
    while (snake.some(s => same(s, f))) f = randCell();
    food = f;
  }

  function updateScore() {
    scoreEl.textContent = `Score: ${score}`;
  }

  function startLoop() {
    if (timer) clearInterval(timer);
    timer = setInterval(step, tickMs);
  }

  function step() {
    if (paused) return draw();

    dir = nextDir;
    const head = snake[0];
    const nh = { x: head.x + dir.x, y: head.y + dir.y };

    // wrap
    nh.x = (nh.x + SIZE) % SIZE;
    nh.y = (nh.y + SIZE) % SIZE;

    // collision with body
    if (snake.some((s, i) => i !== 0 && same(s, nh))) {
      flash('Game Over');
      return reset();
    }

    snake.unshift(nh);
    if (same(nh, food)) {
      score += 1;
      if (score % 5 === 0) {
        tickMs = Math.max(60, tickMs - 10);
        startLoop();
      }
      spawnFood();
      updateScore();
    } else {
      snake.pop();
    }

    draw();
  }

  function drawGrid() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    ctx.globalAlpha = 0.35;
    ctx.strokeStyle = '#1b2650';
    ctx.lineWidth = 1;
    for (let i = 1; i < SIZE; i++) {
      ctx.beginPath();
      ctx.moveTo(i * CELL, 0);
      ctx.lineTo(i * CELL, canvas.height);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, i * CELL);
      ctx.lineTo(canvas.width, i * CELL);
      ctx.stroke();
    }
    ctx.restore();
  }

  function roundRect(x, y, w, h, r) {
    const rr = Math.min(r, w / 2, h / 2);
    ctx.beginPath();
    ctx.moveTo(x + rr, y);
    ctx.arcTo(x + w, y, x + w, y + h, rr);
    ctx.arcTo(x + w, y + h, x, y + h, rr);
    ctx.arcTo(x, y + h, x, y, rr);
    ctx.arcTo(x, y, x + w, y, rr);
    ctx.closePath();
  }

  function draw() {
    drawGrid();

    // food
    ctx.save();
    ctx.fillStyle = '#ff7aa2';
    const fx = food.x * CELL + 3, fy = food.y * CELL + 3;
    roundRect(fx, fy, CELL - 6, CELL - 6, 10);
    ctx.fill();
    ctx.restore();

    // snake
    for (let i = snake.length - 1; i >= 0; i--) {
      const s = snake[i];
      const x = s.x * CELL + 2, y = s.y * CELL + 2;
      ctx.save();
      ctx.fillStyle = i === 0 ? '#7cf7b4' : 'rgba(124,247,180,.78)';
      roundRect(x, y, CELL - 4, CELL - 4, 10);
      ctx.fill();
      ctx.restore();
    }

    if (paused) {
      ctx.save();
      ctx.fillStyle = 'rgba(0,0,0,.35)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#e8ecff';
      ctx.font = 'bold 28px ui-sans-serif, system-ui';
      ctx.textAlign = 'center';
      ctx.fillText('Paused', canvas.width / 2, canvas.height / 2);
      ctx.restore();
    }
  }

  function setDir(dx, dy) {
    // prevent reverse
    if (dx === -dir.x && dy === -dir.y) return;
    nextDir = { x: dx, y: dy };
  }

  function flash(text) {
    // lightweight feedback using document title
    const old = document.title;
    document.title = text;
    setTimeout(() => (document.title = old), 600);
  }

  window.addEventListener('keydown', (e) => {
    const k = e.key.toLowerCase();
    if (k === 'arrowup' || k === 'w') setDir(0, -1);
    else if (k === 'arrowdown' || k === 's') setDir(0, 1);
    else if (k === 'arrowleft' || k === 'a') setDir(-1, 0);
    else if (k === 'arrowright' || k === 'd') setDir(1, 0);
    else if (k === ' ') paused = !paused;
  });

  document.querySelectorAll('[data-dir]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const d = btn.getAttribute('data-dir');
      if (d === 'up') setDir(0, -1);
      if (d === 'down') setDir(0, 1);
      if (d === 'left') setDir(-1, 0);
      if (d === 'right') setDir(1, 0);
    });
  });

  btnRestart.addEventListener('click', reset);
  reset();
})(); 
""",
        },
    ]

def _stock_premium_web_files() -> list[dict]:
    # Minimal runnable "stock premium monitor" demo (mock data, client-side).
    return [
        {
            "path": "index.html",
            "content": """<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>股票溢价监控 Demo</title>
    <link rel="stylesheet" href="./style.css" />
  </head>
  <body>
    <main class="app">
      <header class="top">
        <div>
          <h1>股票溢价监控</h1>
          <p class="sub">本 Demo 使用模拟数据展示溢价监控的完整交互与输出结构。</p>
        </div>
        <div class="controls">
          <label class="field">
            <span>标的</span>
            <input id="symbol" value="AAPL" />
          </label>
          <label class="field">
            <span>阈值(%)</span>
            <input id="threshold" type="number" value="2" step="0.1" />
          </label>
          <button id="btnToggle">Start</button>
        </div>
      </header>

      <section class="grid">
        <div class="card">
          <div class="card-hd">
            <div class="title">实时溢价</div>
            <div class="pill" id="statusPill">idle</div>
          </div>
          <div class="kpis">
            <div class="kpi">
              <div class="k">现货价</div>
              <div class="v" id="spot">--</div>
            </div>
            <div class="kpi">
              <div class="k">参考价</div>
              <div class="v" id="ref">--</div>
            </div>
            <div class="kpi">
              <div class="k">溢价(%)</div>
              <div class="v" id="premium">--</div>
            </div>
          </div>
          <canvas id="chart" width="900" height="280" aria-label="premium chart"></canvas>
          <div class="note">提示：超过阈值会触发告警并写入事件列表。</div>
        </div>

        <div class="card">
          <div class="card-hd">
            <div class="title">事件</div>
            <div class="muted" id="evtMeta">0 events</div>
          </div>
          <div id="events" class="events"></div>
        </div>
      </section>
    </main>
    <script src="./app.js"></script>
  </body>
</html>
""",
        },
        {
            "path": "style.css",
            "content": """:root{--bg:#0b1020;--fg:#e8ecff;--muted:#9aa3c7;--card:#0f1834;--bd:rgba(255,255,255,.10);--ok:#34d399;--warn:#fb7185;--accent:#60a5fa}
*{box-sizing:border-box}
body{margin:0;font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Arial; background:radial-gradient(1000px 600px at 18% 8%, rgba(96,165,250,.35) 0%, transparent 55%),radial-gradient(800px 480px at 78% 10%, rgba(52,211,153,.22) 0%, transparent 55%),var(--bg); color:var(--fg)}
.app{max-width:1100px;margin:0 auto;padding:26px}
.top{display:flex;align-items:flex-end;justify-content:space-between;gap:18px;margin-bottom:18px}
h1{margin:0;font-size:22px;letter-spacing:.04em}
.sub{margin:6px 0 0;color:var(--muted);font-size:12px}
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end}
.field{display:flex;flex-direction:column;gap:6px;font-size:11px;color:var(--muted)}
input{height:36px;width:140px;border-radius:12px;border:1px solid var(--bd);background:rgba(255,255,255,.03);color:var(--fg);padding:0 10px;outline:none}
button{height:36px;border-radius:12px;border:1px solid var(--bd);background:rgba(96,165,250,.18);color:var(--fg);padding:0 14px;font-weight:600;cursor:pointer}
button:hover{filter:brightness(1.06)}
.grid{display:grid;grid-template-columns: 1.3fr .9fr;gap:14px}
@media (max-width: 980px){.grid{grid-template-columns:1fr}}
.card{background:linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.02)); border:1px solid var(--bd); border-radius:18px; padding:14px; box-shadow:0 24px 80px rgba(0,0,0,.35)}
.card-hd{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px}
.title{font-size:13px;font-weight:700}
.muted{color:var(--muted);font-size:11px}
.pill{font-size:11px;border:1px solid var(--bd);padding:4px 10px;border-radius:999px;background:rgba(255,255,255,.03)}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:10px}
.kpi{border:1px solid var(--bd);border-radius:14px;padding:10px;background:rgba(0,0,0,.12)}
.k{font-size:11px;color:var(--muted)}
.v{margin-top:6px;font-size:18px;font-weight:800}
canvas{width:100%;height:auto;border-radius:14px;border:1px solid var(--bd);background:rgba(0,0,0,.12)}
.note{margin-top:10px;color:var(--muted);font-size:11px}
.events{display:flex;flex-direction:column;gap:8px;max-height:430px;overflow:auto;padding-right:2px}
.evt{border:1px solid var(--bd);border-radius:14px;padding:10px;background:rgba(0,0,0,.12)}
.evt .t{display:flex;align-items:center;justify-content:space-between;gap:10px}
.evt .tag{font-size:10px;border-radius:999px;padding:3px 10px;border:1px solid var(--bd)}
.evt .msg{margin-top:6px;font-size:12px;line-height:1.6;color:rgba(232,236,255,.92)}
.tag.ok{background:rgba(52,211,153,.12)}
.tag.warn{background:rgba(251,113,133,.12)}
""",
        },
        {
            "path": "app.js",
            "content": """(() => {
  const elSymbol = document.getElementById('symbol');
  const elThreshold = document.getElementById('threshold');
  const btn = document.getElementById('btnToggle');
  const pill = document.getElementById('statusPill');

  const elSpot = document.getElementById('spot');
  const elRef = document.getElementById('ref');
  const elPremium = document.getElementById('premium');
  const elEvents = document.getElementById('events');
  const elEvtMeta = document.getElementById('evtMeta');

  const canvas = document.getElementById('chart');
  const ctx = canvas.getContext('2d');

  let running = false;
  let timer = null;
  const series = [];
  const events = [];

  function now() {
    const d = new Date();
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  function setPill(text) {
    pill.textContent = text;
  }

  function pushEvent(level, msg) {
    const e = { t: now(), level, msg };
    events.unshift(e);
    if (events.length > 60) events.pop();
    renderEvents();
  }

  function renderEvents() {
    elEvtMeta.textContent = `${events.length} events`;
    elEvents.innerHTML = '';
    for (const e of events) {
      const div = document.createElement('div');
      div.className = 'evt';
      div.innerHTML = `
        <div class="t">
          <div class="muted">${e.t}</div>
          <div class="tag ${e.level === 'warn' ? 'warn' : 'ok'}">${e.level}</div>
        </div>
        <div class="msg">${e.msg}</div>
      `;
      elEvents.appendChild(div);
    }
  }

  function draw() {
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    // grid
    ctx.save();
    ctx.globalAlpha = 0.35;
    ctx.strokeStyle = '#1b2650';
    for (let i = 1; i < 6; i++) {
      const y = (h * i) / 6;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }
    ctx.restore();

    if (series.length < 2) return;
    const maxN = 80;
    const shown = series.slice(-maxN);
    const min = Math.min(...shown.map(x => x.p));
    const max = Math.max(...shown.map(x => x.p));
    const pad = Math.max(0.4, (max - min) * 0.15);
    const lo = min - pad, hi = max + pad;

    function xy(i, p) {
      const x = (w * i) / (shown.length - 1);
      const y = h - ((p - lo) / (hi - lo)) * h;
      return [x, y];
    }

    ctx.save();
    ctx.lineWidth = 3;
    ctx.strokeStyle = '#60a5fa';
    ctx.beginPath();
    for (let i = 0; i < shown.length; i++) {
      const [x, y] = xy(i, shown[i].p);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.restore();

    // latest point
    const last = shown[shown.length - 1];
    const [lx, ly] = xy(shown.length - 1, last.p);
    ctx.save();
    ctx.fillStyle = last.p >= Number(elThreshold.value || 0) ? '#fb7185' : '#34d399';
    ctx.beginPath();
    ctx.arc(lx, ly, 6, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  function tick() {
    const symbol = String(elSymbol.value || 'AAPL').toUpperCase();
    const base = 100 + (symbol.charCodeAt(0) % 10) * 7;
    const spot = base + (Math.random() - 0.5) * 2.8;
    const ref = base + (Math.random() - 0.5) * 2.8;
    const premium = ((spot - ref) / ref) * 100;

    elSpot.textContent = spot.toFixed(2);
    elRef.textContent = ref.toFixed(2);
    elPremium.textContent = premium.toFixed(2);

    series.push({ t: Date.now(), p: premium });
    if (series.length > 500) series.shift();

    const th = Number(elThreshold.value || 0);
    if (Math.abs(premium) >= th) {
      pushEvent('warn', `${symbol} 溢价触发阈值：${premium.toFixed(2)}% (阈值 ${th}%)`);
    } else {
      pushEvent('ok', `${symbol} 更新：溢价 ${premium.toFixed(2)}%`);
    }
    draw();
  }

  function start() {
    running = true;
    btn.textContent = 'Stop';
    setPill('running');
    pushEvent('ok', '开始监控（模拟数据）');
    tick();
    timer = setInterval(tick, 1200);
  }

  function stop() {
    running = false;
    btn.textContent = 'Start';
    setPill('idle');
    if (timer) clearInterval(timer);
    timer = null;
    pushEvent('ok', '停止监控');
  }

  btn.addEventListener('click', () => (running ? stop() : start()));
  setPill('idle');
  renderEvents();
  draw();
})(); 
""",
        },
        {
            "path": "README.md",
            "content": """# 股票溢价监控 Demo\n\n这是一个纯前端的可运行 Demo（使用模拟数据），用于展示：\n- 输入标的/阈值\n- 定时刷新并计算溢价\n- 触发阈值告警\n- 绘制溢价曲线\n\n## 运行\n直接用浏览器打开 `index.html` 即可。\n""",
        },
    ]


def build_workflow():
    graph: StateGraph = StateGraph(RunState)

    def init(state: RunState) -> RunState:
        mode = (state.get("mode") or "engineer").strip().lower()
        if mode not in {"engineer", "team"}:
            mode = "engineer"

        roles_in = state.get("roles") or []
        default_team_roles = [
            "team_lead",
            "seo_expert",
            "product_manager",
            "architect",
            "engineer",
            "data_analyst",
            "deep_researcher",
        ]
        allowed = set(default_team_roles)

        if mode == "team":
            roles = [r for r in roles_in if isinstance(r, str) and r in allowed]
            if not roles:
                roles = list(default_team_roles)
            # Ensure a leader exists and goes first.
            if "team_lead" not in roles:
                roles = ["team_lead", *roles]
            else:
                roles = ["team_lead", *[r for r in roles if r != "team_lead"]]
            # Team mode must include architect + engineer so planning and code output always happen.
            if "architect" not in roles:
                roles.append("architect")
            if "engineer" not in roles:
                roles.append("engineer")
        else:
            roles = ["engineer"]

        return {
            **state,
            "mode": mode,
            "roles": roles,
            "role_order": roles if mode == "team" else [],
            "role_index": 0,
            "outputs": {},
            "errors": [],
        }

    def route_from_init(state: RunState) -> str:
        return "team_router" if state.get("mode") == "team" else "engineer_solo"

    def rule_node(state: RunState) -> RunState:
        """Adjudicate Global/User rules into a final ProjectRuleSet.

        For now, user rules are accepted as free-form strings and mapped into `UserRule` objects.
        This node is the single place where user rules are turned into an executable rule set.
        """
        from app.rules.engine import decide_project_rules
        from app.rules.global_rules import GLOBAL_RULES
        from app.rules.types import Scope, UserRule

        raw = state.get("user_rules") or []
        raw = [str(x).strip() for x in raw if isinstance(x, str) and str(x).strip()]

        user_rules: list[UserRule] = []
        for i, line in enumerate(raw, start=1):
            # Minimal module rule syntax: "module:<name>: <rule>"
            title = line
            scope = Scope.PROJECT
            module = None
            lower = line.lower()
            if lower.startswith("module:") and ":" in line[len("module:") :]:
                rest = line[len("module:") :]
                mod, _, r = rest.partition(":")
                if mod.strip() and r.strip():
                    scope = Scope.MODULE
                    module = mod.strip()
                    title = r.strip()

            user_rules.append(
                UserRule(
                    id=f"U-{i:03d}",
                    title=title,
                    description="",
                    scope=scope,
                    module=module,
                )
            )

        pr = decide_project_rules(GLOBAL_RULES, user_rules)
        outputs = dict(state.get("outputs") or {})
        if raw:
            msg = f"Rules adjudicated: accepted={len(pr.accepted_user_rules)}, rejected={len(pr.rejected_user_rules)}"
        else:
            msg = "Rules adjudicated: no user rules provided."
        # Use the node name as the output key so UIs can map node -> output reliably.
        outputs["rule_node"] = msg
        return {**state, "outputs": outputs, "project_rules": pr.model_dump()}

    def engineer_solo(state: RunState) -> RunState:
        input_text = (state.get("input") or "").strip()
        rules_obj = state.get("project_rules") or {}
        rules_json = json.dumps(rules_obj, ensure_ascii=False, indent=2)[:20_000]
        raw = chat(
            messages=[
                ChatMessage(
                    role="system",
                    content=(
                        "You are a senior software engineer.\n"
                        "Return ONLY valid JSON with this schema:\n"
                        '{ "summary": string, "files": [ { "path": string, "content": string } ] }\n'
                        "If generating a runnable demo, ALWAYS produce real code files.\n"
                        "For web demos, prefer these files:\n"
                        '- "index.html"\n'
                        '- "app.js"\n'
                        '- "style.css"\n'
                        "If the user asks for a Snake game (贪吃蛇), implement it with canvas and basic controls.\n"
                        "No markdown. No backticks. JSON only."
                    ),
                ),
                ChatMessage(
                    role="user",
                    content=(
                        "Project Rules (read-only):\n"
                        f"{rules_json}\n\n"
                        "Task:\n"
                        f"{input_text}"
                    ),
                ),
            ],
            fallback=json.dumps(
                {
                    "summary": f"[fallback] engineer: {input_text}",
                    "files": [{"path": "README.md", "content": f"[fallback]\n\n{input_text}\n"}],
                },
                ensure_ascii=False,
            ),
            stream=True,
            event_role="engineer",
        )
        obj = _extract_json_obj(raw) or {"summary": raw, "files": []}
        summary, files = _normalize_files(obj)
        if not summary:
            summary = raw.strip() or "Run completed"
        if _is_snake_request(input_text) and not _has_required_files(
            files, {"index.html", "app.js", "style.css"}
        ):
            # If the model emits non-code files (e.g. README only), still guarantee runnable demo files.
            files = _merge_files(_snake_web_files(), files)
        if _is_stock_premium_request(input_text) and not _has_required_files(
            files, {"index.html", "app.js", "style.css"}
        ):
            files = _merge_files(_stock_premium_web_files(), files)
        if not files:
            # Ensure we still surface something as a file artifact even if the model didn't comply.
            files = [{"path": "output.md", "content": summary}]
        outputs = dict(state.get("outputs") or {})
        outputs["engineer"] = summary
        final = {
            "summary": summary,
            "mode": "engineer",
            "roles": ["engineer"],
            "outputs": outputs,
            "files": files,
        }
        return {**state, "outputs": outputs, "files": files, "final": final}

    def _team_role_node(role: str, system: str, *, emits_files: bool = False) -> callable:
        def _fn(state: RunState) -> RunState:
            input_text = (state.get("input") or "").strip()
            outputs = dict(state.get("outputs") or {})
            user_content = input_text
            # Team-mode "engineer" must not see raw cross-role context. Provide only
            # a structured view that is safe to consume.
            if role == "engineer":
                safe_view = {
                    "project_rules": state.get("project_rules") or {},
                    "architecture_view": state.get("architecture") or {},
                    "task_view": state.get("task_view") or {},
                    "dependency_contracts": (state.get("architecture") or {}).get("contracts") or [],
                }
                user_content = json.dumps(safe_view, ensure_ascii=False, indent=2)[:40_000]
            else:
                context_lines = []
                for k, v in outputs.items():
                    if not isinstance(v, str) or not v.strip():
                        continue
                    context_lines.append(f"{k}: {v.strip()}")
                context = "\n\n".join(context_lines).strip()
                if context:
                    user_content = f"{input_text}\n\nContext so far:\n{context}"

            if emits_files:
                raw = chat(
                    messages=[
                        ChatMessage(
                            role="system",
                            content=(
                                f"{system}\n\n"
                                "Return ONLY valid JSON with this schema:\n"
                                '{ "summary": string, "files": [ { "path": string, "content": string } ] }\n'
                                "Put code into files. Prefer index.html/app.js/style.css for web demos.\n"
                                "In team mode, do NOT assume access to the full codebase unless the user explicitly provided it.\n"
                                "No markdown. No backticks. JSON only."
                            ),
                        ),
                        ChatMessage(role="user", content=user_content),
                    ],
                    fallback=json.dumps(
                        {
                            "summary": f"[fallback] {role}: {input_text}",
                            "files": [{"path": "output.md", "content": f"[fallback]\n\n{input_text}\n"}],
                        },
                        ensure_ascii=False,
                    ),
                    stream=True,
                    event_role=role,
                )
                obj = _extract_json_obj(raw) or {"summary": raw, "files": []}
                summary, files = _normalize_files(obj)
                if not summary:
                    summary = raw.strip() or "Run completed"
                if _is_snake_request(input_text) and not _has_required_files(
                    files, {"index.html", "app.js", "style.css"}
                ):
                    files = _merge_files(_snake_web_files(), files)
                if _is_stock_premium_request(input_text) and not _has_required_files(
                    files, {"index.html", "app.js", "style.css"}
                ):
                    files = _merge_files(_stock_premium_web_files(), files)
                if files:
                    state["files"] = files
                outputs[role] = summary
            else:
                out = chat(
                    messages=[
                        ChatMessage(role="system", content=system),
                        ChatMessage(role="user", content=user_content),
                    ],
                    fallback=f"[fallback] {role}: {input_text}",
                )
                outputs[role] = out
            return {
                **state,
                "outputs": outputs,
                "role_index": int(state.get("role_index") or 0) + 1,
            }

        return _fn

    team_lead = _team_role_node(
        "team_lead",
        "You are the team lead. Create a clear plan and delegate tasks to the team. Respond in Chinese.",
    )
    seo_expert = _team_role_node(
        "seo_expert",
        "You are an SEO expert. Provide SEO strategy, keywords, and on-page recommendations. Respond in Chinese.",
    )
    product_manager = _team_role_node(
        "product_manager",
        "You are a product manager. Clarify requirements, scope, and MVP. Respond in Chinese.",
    )
    def architect(state: RunState) -> RunState:
        """Planner/Architect role: JSON-only, planning facts only (no rules, no code)."""
        input_text = (state.get("input") or "").strip()
        outputs = dict(state.get("outputs") or {})
        raw = chat(
            messages=[
                ChatMessage(
                    role="system",
                    content=(
                        "You are a software architect (planner).\n"
                        "You do NOT write code and you do NOT define any rules.\n"
                        "Return ONLY valid JSON (no markdown, no prose) with this schema:\n"
                        "{\n"
                        '  "goals": { "project_goals": string[], "non_goals": string[] },\n'
                        '  "tech": { "languages": string[], "stack": string[], "runtime_constraints": string[] },\n'
                        '  "modules": [ { "name": string, "responsibility": string, "depends_on": string[] } ],\n'
                        '  "capabilities": [ { "module": string, "provides": string[], "not_provide": string[] } ],\n'
                        '  "contracts": [ { "name": string, "purpose": string, "inputs": string[], "outputs": string[], "guarantees": string[], "failure_modes": string[] } ],\n'
                        '  "tasks": [ { "id": string, "module": string, "description": string, "depends_on": string[] } ]\n'
                        "}\n"
                        "Chinese values are preferred."
                    ),
                ),
                ChatMessage(role="user", content=input_text),
            ],
            fallback=json.dumps(
                {
                    "goals": {"project_goals": [input_text or "实现用户需求"], "non_goals": []},
                    "tech": {"languages": ["TypeScript", "Python"], "stack": [], "runtime_constraints": []},
                    "modules": [],
                    "capabilities": [],
                    "contracts": [],
                    "tasks": [],
                },
                ensure_ascii=False,
            ),
            stream=True,
            event_role="architect",
        )
        obj = _extract_json_obj(raw)
        if not isinstance(obj, dict):
            # One retry asking for strict JSON only.
            raw2 = chat(
                messages=[
                    ChatMessage(
                        role="system",
                        content=(
                            "Return ONLY valid JSON object with keys: goals, tech, modules, capabilities, contracts, tasks.\n"
                            "No markdown, no prose."
                        ),
                    ),
                    ChatMessage(role="user", content=input_text),
                ],
                fallback="{}",
                stream=True,
                event_role="architect",
            )
            obj = _extract_json_obj(raw2)

        if not isinstance(obj, dict):
            obj = {}

        # Validate against a stable schema so downstream nodes can rely on shape.
        try:
            from app.langgraph.arch_schema import ArchitectPlan

            plan = ArchitectPlan.model_validate(obj)
            obj = plan.model_dump()
        except Exception:
            obj = {
                "goals": {"project_goals": [input_text or "实现用户需求"], "non_goals": []},
                "tech": {"languages": ["TypeScript", "Python"], "stack": [], "runtime_constraints": []},
                "modules": [],
                "capabilities": [],
                "contracts": [],
                "tasks": [],
            }
        # Lightweight summary for UI.
        goals = obj.get("goals") if isinstance(obj.get("goals"), dict) else {}
        pg = goals.get("project_goals") if isinstance(goals, dict) else []
        headline = pg[0] if isinstance(pg, list) and pg else "架构规划完成"
        outputs["architect"] = str(headline)
        return {
            **state,
            "outputs": outputs,
            "architecture": obj,
            "role_index": int(state.get("role_index") or 0) + 1,
        }
    team_engineer = _team_role_node(
        "engineer",
        (
            "You are a software engineer.\n"
            "You will receive a JSON 'Task View' plus read-only project rules and architecture/contracts.\n"
            "Implement the task by producing REAL code files in the JSON output schema.\n"
            "Do not include markdown or explanations outside JSON."
        ),
        emits_files=True,
    )
    data_analyst = _team_role_node(
        "data_analyst",
        "You are a data analyst. Define metrics, events, and validation plan. Respond in Chinese.",
    )
    deep_researcher = _team_role_node(
        "deep_researcher",
        (
            "You are a deep researcher. Identify unknowns, risks, and research plan with sources to consult. "
            "Respond in Chinese."
        ),
    )

    def route_team_next(state: RunState) -> str:
        idx = int(state.get("role_index") or 0)
        order = state.get("role_order") or []
        nxt = order[idx] if idx < len(order) else "team_finalize"
        # Inject a system node right before the team engineer so the engineer only
        # receives structured views (rules/plan/contracts/task view).
        if nxt == "engineer" and not isinstance(state.get("task_view"), dict):
            return "task_view"
        return nxt

    def team_router(state: RunState) -> RunState:
        return state

    def task_view(state: RunState) -> RunState:
        """Derive a strict Task View for engineers from user input + architect plan + project rules.

        Keep it JSON-only and small; engineers in team mode will receive only this view.
        """
        input_text = (state.get("input") or "").strip()
        outputs = dict(state.get("outputs") or {})
        arch = state.get("architecture") or {}
        rules_obj = state.get("project_rules") or {}
        view = {
            "task_goal": input_text,
            "module": "web",
            "inputs": ["user_query", "project_rules", "architecture_view", "dependency_contracts"],
            "outputs_required": [
                "A JSON object with summary + files (path/content)",
                "Prefer runnable web demo files when applicable",
            ],
            "forbidden": [
                "Assuming access to full repository unless explicitly provided",
                "Introducing new dependencies unless rules allow",
            ],
            "architecture_hint": arch.get("modules") if isinstance(arch, dict) else [],
            "rules_hint": rules_obj,
        }
        outputs["task_view"] = "Task view prepared."
        return {**state, "outputs": outputs, "task_view": view}

    def team_finalize(state: RunState) -> RunState:
        input_text = (state.get("input") or "").strip()
        outputs = dict(state.get("outputs") or {})
        files = list(state.get("files") or [])
        if files:
            paths = [str(f.get("path") or "") for f in files if isinstance(f, dict) and str(f.get("path") or "")]
            summary = "已生成代码文件：\n" + "\n".join(f"- {p}" for p in paths[:50])
            if any((p or "").lower().endswith("index.html") for p in paths):
                summary += "\n\n运行方式：直接用浏览器打开 `index.html`。"
        else:
            summary = chat(
                messages=[
                    ChatMessage(
                        role="system",
                        content=(
                            "You are the team lead. Synthesize the team's outputs into a final, actionable answer. "
                            "Respond in Chinese."
                        ),
                    ),
                    ChatMessage(
                        role="user",
                        content=f"User request:\n{input_text}\n\nTeam outputs:\n{outputs}\n\nFiles:\n{files}",
                    ),
                ],
                fallback=outputs.get("team_lead") or "[fallback] team_lead: Run completed",
            )
        final = {
            "summary": summary,
            "mode": "team",
            "roles": list(state.get("roles") or []),
            "outputs": outputs,
            "files": files,
        }
        return {**state, "final": final}

    graph.add_node("init", init)
    graph.add_node("rule_node", rule_node)
    graph.add_node("engineer_solo", engineer_solo)
    graph.add_node("team_router", team_router)
    graph.add_node("team_lead", team_lead)
    graph.add_node("seo_expert", seo_expert)
    graph.add_node("product_manager", product_manager)
    graph.add_node("architect", architect)
    graph.add_node("task_view", task_view)
    graph.add_node("engineer", team_engineer)
    graph.add_node("data_analyst", data_analyst)
    graph.add_node("deep_researcher", deep_researcher)
    graph.add_node("team_finalize", team_finalize)

    graph.set_entry_point("init")
    graph.add_edge("init", "rule_node")
    graph.add_conditional_edges(
        "rule_node", route_from_init, {"team_router": "team_router", "engineer_solo": "engineer_solo"}
    )

    graph.add_edge("engineer_solo", END)

    graph.add_conditional_edges(
        "team_router",
        route_team_next,
        {
            "team_lead": "team_lead",
            "seo_expert": "seo_expert",
            "product_manager": "product_manager",
            "architect": "architect",
            "task_view": "task_view",
            "engineer": "engineer",
            "data_analyst": "data_analyst",
            "deep_researcher": "deep_researcher",
            "team_finalize": "team_finalize",
        },
    )

    for node in [
        "team_lead",
        "seo_expert",
        "product_manager",
        "architect",
        "task_view",
        "engineer",
        "data_analyst",
        "deep_researcher",
    ]:
        graph.add_conditional_edges(
            node,
            route_team_next,
            {
                "team_lead": "team_lead",
                "seo_expert": "seo_expert",
                "product_manager": "product_manager",
                "architect": "architect",
                "task_view": "task_view",
                "engineer": "engineer",
                "data_analyst": "data_analyst",
                "deep_researcher": "deep_researcher",
                "team_finalize": "team_finalize",
            },
        )

    graph.add_edge("team_finalize", END)

    return graph.compile()


WORKFLOW = build_workflow()
