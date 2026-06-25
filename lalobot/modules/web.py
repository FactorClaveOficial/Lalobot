from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# ── CORS ──────────────────────────────────────────────────────────────────────

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route("/api/ping")
def api_ping():
    return jsonify({"status": "ok"})

# ── API: detección y búsqueda inteligente ─────────────────────────────────────

@app.route("/api/detect")
def api_detect():
    q = request.args.get("q", "").strip()
    from lalobot.modules.scanner import detect_type
    return jsonify({"type": detect_type(q), "query": q})


@app.route("/api/query")
def api_query():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Consulta vacía"})

    from lalobot.modules.scanner import detect_type, capture_sherlock, capture_holehe, phone_dorks
    query_type = detect_type(q)

    if query_type == "email":
        result = capture_holehe(q)
        return jsonify({"type": "email", "target": q, **result})

    if query_type == "phone":
        links = phone_dorks(q)
        return jsonify({"type": "phone", "target": q, "links": links})

    # username
    result = capture_sherlock(q)
    return jsonify({"type": "username", "target": q, **result})


# ── API: búsqueda en awesome-osint ────────────────────────────────────────────

@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").lower().strip()
    if not q:
        return jsonify({"results": []})
    from lalobot.modules.osint_search import parse_readme
    results = [
        {"section": sec, "name": name, "url": url, "desc": desc}
        for sec, name, url, desc in parse_readme()
        if q in f"{name} {url} {desc} {sec}".lower()
    ]
    return jsonify({"results": results})


# ── Interfaz web local ────────────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Lalobot — OSINT</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{background:#0d1117;color:#c9d1d9;font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh}
    header{background:#161b22;border-bottom:1px solid #30363d;padding:16px 32px;display:flex;align-items:center;gap:12px}
    header h1{font-size:1.3rem;color:#58a6ff;font-weight:700}
    .status{margin-left:auto;display:flex;align-items:center;gap:8px;font-size:.82rem;color:#8b949e}
    .dot{width:8px;height:8px;border-radius:50%;background:#484f58}
    .dot.online{background:#3fb950}
    .search-wrap{max-width:720px;margin:60px auto 0;padding:0 24px}
    .subtitle{text-align:center;color:#8b949e;margin-bottom:32px;font-size:.95rem}
    .input-row{display:flex;gap:0;border:1px solid #30363d;border-radius:10px;overflow:hidden;transition:border .2s}
    .input-row:focus-within{border-color:#58a6ff}
    .badge{padding:0 16px;background:#161b22;display:flex;align-items:center;font-size:.78rem;font-weight:700;white-space:nowrap;border-right:1px solid #30363d;color:#484f58;min-width:100px;justify-content:center}
    .badge.email{color:#3fb950;border-color:#3fb950}
    .badge.phone{color:#f0883e;border-color:#f0883e}
    .badge.username{color:#58a6ff;border-color:#58a6ff}
    input{flex:1;padding:14px 16px;background:#161b22;border:none;color:#c9d1d9;font-size:1rem;outline:none}
    input::placeholder{color:#484f58}
    button{padding:14px 24px;background:#238636;border:none;color:#fff;font-size:.95rem;font-weight:600;cursor:pointer;transition:background .2s}
    button:hover{background:#2ea043}
    button:disabled{background:#21262d;color:#484f58;cursor:not-allowed}
    .hint{text-align:center;margin-top:10px;font-size:.82rem;color:#484f58;min-height:18px}
    .results{max-width:720px;margin:40px auto 80px;padding:0 24px}
    .spinner{text-align:center;padding:48px;color:#8b949e}
    .spinner::after{content:'';display:inline-block;width:32px;height:32px;border:3px solid #30363d;border-top-color:#58a6ff;border-radius:50%;animation:spin .8s linear infinite;vertical-align:middle;margin-left:12px}
    @keyframes spin{to{transform:rotate(360deg)}}
    .section-title{font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#8b949e;margin:28px 0 12px}
    .card{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:12px 16px;margin-bottom:8px;display:flex;align-items:center;gap:12px}
    .card:hover{border-color:#30363d}
    .card a{color:#3fb950;font-size:.85rem;text-decoration:none;word-break:break-all}
    .card a:hover{text-decoration:underline}
    .card-name{font-weight:600;color:#c9d1d9;font-size:.95rem;flex:1}
    .tag{padding:3px 10px;border-radius:20px;font-size:.72rem;font-weight:700}
    .tag.found{background:#0d2818;color:#3fb950;border:1px solid #238636}
    .tag.notfound{background:#161b22;color:#484f58;border:1px solid #30363d}
    .summary{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px 20px;margin-bottom:20px;display:flex;gap:24px;flex-wrap:wrap}
    .summary-item{display:flex;flex-direction:column;gap:2px}
    .summary-num{font-size:1.6rem;font-weight:700;color:#58a6ff}
    .summary-label{font-size:.78rem;color:#8b949e}
    .link-card{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:14px 18px;margin-bottom:8px;display:flex;align-items:center;gap:12px;cursor:pointer;text-decoration:none;transition:border .2s}
    .link-card:hover{border-color:#58a6ff}
    .link-card-name{font-weight:600;color:#58a6ff;font-size:.95rem}
    .link-card-url{font-size:.78rem;color:#484f58;margin-top:2px}
    .error-box{background:#1a0a0a;border:1px solid #6e1a1a;border-radius:8px;padding:16px 20px;color:#f85149;font-size:.9rem}
    .offline-card{max-width:480px;margin:60px auto;background:#161b22;border:1px solid #30363d;border-radius:12px;padding:32px;text-align:center}
    .offline-card h3{color:#f0883e;margin-bottom:12px}
    .offline-card p{color:#8b949e;margin-bottom:16px;font-size:.9rem}
    .offline-card code{display:block;background:#0d1117;padding:10px 16px;border-radius:6px;color:#3fb950;font-family:monospace;font-size:.95rem;margin:12px 0}
  </style>
</head>
<body>
  <header>
    <h1>&#x1F916; Lalobot</h1>
    <span style="color:#8b949e;font-size:.85rem">Suite OSINT</span>
    <div class="status">
      <span class="dot" id="dot"></span>
      <span id="statusTxt">Conectando...</span>
    </div>
  </header>

  <div class="search-wrap">
    <p class="subtitle">Ingresa un email, usuario o número — Lalobot detecta y ejecuta la herramienta correcta</p>
    <div class="input-row">
      <div class="badge" id="badge">?</div>
      <input id="q" type="text" placeholder="juan@gmail.com  ·  juanito98  ·  +52 55 1234 5678"
             autocomplete="off" spellcheck="false">
      <button id="btn" onclick="runSearch()">Investigar</button>
    </div>
    <div class="hint" id="hint">Escribe para detectar el tipo automáticamente</div>
  </div>

  <div class="results" id="results"></div>

  <script>
    const TOOLS = {
      email:    { label:'✉ Email',    cls:'email',    desc:'Se ejecutará Holehe para buscar servicios asociados' },
      phone:    { label:'📞 Teléfono', cls:'phone',    desc:'Se generarán links de búsqueda OSINT' },
      username: { label:'👤 Usuario',  cls:'username', desc:'Se ejecutará Sherlock para buscar perfiles en redes' },
    };

    function detectType(v) {
      v = v.trim();
      if (!v) return null;
      if (/^[a-zA-Z0-9._%+\\-]+@[a-zA-Z0-9.\\-]+\\.[a-zA-Z]{2,}$/.test(v)) return 'email';
      const d = v.replace(/\\D/g,'');
      if (/^\\+?[\\d\\s\\-\\(\\)\\.]{7,20}$/.test(v) && d.length>=7 && d.length<=15) return 'phone';
      return 'username';
    }

    const qInput = document.getElementById('q');
    const badge  = document.getElementById('badge');
    const hint   = document.getElementById('hint');
    const btn    = document.getElementById('btn');

    qInput.addEventListener('input', () => {
      const t = detectType(qInput.value);
      if (!t || !qInput.value.trim()) {
        badge.textContent = '?'; badge.className = 'badge';
        hint.textContent = 'Escribe para detectar el tipo automáticamente';
      } else {
        const info = TOOLS[t];
        badge.textContent = info.label; badge.className = 'badge ' + info.cls;
        hint.textContent = info.desc;
      }
    });

    qInput.addEventListener('keydown', e => { if (e.key==='Enter') runSearch(); });

    // ── Estado del servidor ────────────────────────────────────────────────
    let backendOk = false;
    async function checkBackend() {
      try {
        const r = await fetch('http://localhost:5001/api/ping', {signal: AbortSignal.timeout(2000)});
        const d = await r.json();
        backendOk = d.status === 'ok';
      } catch { backendOk = false; }
      document.getElementById('dot').className = 'dot ' + (backendOk ? 'online' : '');
      document.getElementById('statusTxt').textContent = backendOk ? 'Servidor activo' : 'Servidor offline';
    }
    checkBackend();

    // ── Búsqueda ────────────────────────────────────────────────────────────
    async function runSearch() {
      const q = qInput.value.trim();
      if (!q) return;

      if (!backendOk) {
        showOffline(); return;
      }

      btn.disabled = true; btn.textContent = 'Buscando...';
      const results = document.getElementById('results');
      results.innerHTML = '<div class="spinner">Ejecutando investigación</div>';

      try {
        const r = await fetch('http://localhost:5001/api/query?q=' + encodeURIComponent(q));
        const data = await r.json();
        renderResults(data);
      } catch(e) {
        results.innerHTML = '<div class="error-box">Error al conectar con el servidor: ' + e.message + '</div>';
      } finally {
        btn.disabled = false; btn.textContent = 'Investigar';
      }
    }

    // ── Render resultados ──────────────────────────────────────────────────
    function renderResults(data) {
      const el = document.getElementById('results');

      if (data.error) {
        el.innerHTML = '<div class="error-box">⚠ ' + esc(data.error) + '</div>';
        return;
      }

      if (data.type === 'email') renderEmail(el, data);
      else if (data.type === 'phone') renderPhone(el, data);
      else if (data.type === 'username') renderUsername(el, data);
    }

    function renderEmail(el, data) {
      let html = '<div class="summary">';
      html += '<div class="summary-item"><span class="summary-num" style="color:#3fb950">' + (data.total||0) + '</span><span class="summary-label">Servicios encontrados</span></div>';
      if (data.not_found) html += '<div class="summary-item"><span class="summary-num" style="color:#484f58">' + data.not_found.length + '</span><span class="summary-label">No encontrado</span></div>';
      html += '</div>';

      if (data.found && data.found.length) {
        html += '<div class="section-title">✓ Registrado en</div>';
        data.found.forEach(f => {
          html += '<div class="card"><span class="card-name">' + esc(f.service) + '</span><span class="tag found">Encontrado</span></div>';
        });
      }

      if (data.not_found && data.not_found.length) {
        html += '<div class="section-title">— No encontrado</div>';
        data.not_found.forEach(f => {
          html += '<div class="card"><span class="card-name" style="color:#484f58">' + esc(f.service) + '</span><span class="tag notfound">No registrado</span></div>';
        });
      }

      el.innerHTML = html || '<div class="error-box">Sin resultados</div>';
    }

    function renderUsername(el, data) {
      const found = data.found || [];
      let html = '<div class="summary"><div class="summary-item"><span class="summary-num">' + found.length + '</span><span class="summary-label">Perfiles encontrados</span></div></div>';

      if (found.length) {
        html += '<div class="section-title">Perfiles en redes sociales</div>';
        found.forEach(f => {
          html += '<a class="link-card" href="' + esc(f.url) + '" target="_blank" rel="noopener">'
               + '<span class="link-card-name">' + esc(f.platform) + '</span>'
               + '<span class="link-card-url">' + esc(f.url) + '</span></a>';
        });
      } else {
        html += '<div class="error-box">No se encontraron perfiles para este usuario.</div>';
      }

      el.innerHTML = html;
    }

    function renderPhone(el, data) {
      const links = data.links || [];
      let html = '<div class="section-title">Links de búsqueda OSINT</div>';
      links.forEach(l => {
        if (l.url) {
          html += '<a class="link-card" href="' + esc(l.url) + '" target="_blank" rel="noopener">'
               + '<span class="link-card-name">' + esc(l.name) + '</span>'
               + '<span class="link-card-url">' + esc(l.url) + '</span></a>';
        }
      });
      el.innerHTML = html;
    }

    function showOffline() {
      document.getElementById('results').innerHTML = `
        <div class="offline-card">
          <h3>🔌 Servidor no disponible</h3>
          <p>Para usar Lalobot, inicia el servidor local:</p>
          <code>python3 main.py web</code>
          <p>Luego recarga esta página o accede desde<br><a href="http://localhost:5001" style="color:#58a6ff">http://localhost:5001</a></p>
        </div>`;
    }

    function esc(s) {
      return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
    }
  </script>
</body>
</html>"""


def run(host="0.0.0.0", port=5001):
    print(f"Servidor iniciado en http://localhost:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run()
