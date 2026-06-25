from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)


@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


@app.route("/api/ping")
def api_ping():
    return jsonify({"status": "ok"})


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
    from lalobot.modules.maigret_scan import capture_maigret
    from lalobot.modules.ghunt_scan import capture_ghunt
    from lalobot.modules.phoneinfooga import capture as capture_phone

    query_type = detect_type(q)

    if query_type == "email":
        with ThreadPoolExecutor(max_workers=2) as ex:
            f_holehe = ex.submit(capture_holehe, q)
            f_ghunt = ex.submit(capture_ghunt, q)
        return jsonify({
            "type": "email",
            "target": q,
            "holehe": f_holehe.result(),
            "ghunt": f_ghunt.result(),
        })

    if query_type == "phone":
        with ThreadPoolExecutor(max_workers=2) as ex:
            f_phone = ex.submit(capture_phone, q)
            f_dorks = ex.submit(phone_dorks, q)
        return jsonify({
            "type": "phone",
            "target": q,
            "phoneinfooga": f_phone.result(),
            "links": f_dorks.result(),
        })

    # username
    with ThreadPoolExecutor(max_workers=2) as ex:
        f_sherlock = ex.submit(capture_sherlock, q)
        f_maigret = ex.submit(capture_maigret, q)
    return jsonify({
        "type": "username",
        "target": q,
        "sherlock": f_sherlock.result(),
        "maigret": f_maigret.result(),
    })


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
    .search-wrap{max-width:760px;margin:60px auto 0;padding:0 24px}
    .subtitle{text-align:center;color:#8b949e;margin-bottom:32px;font-size:.95rem}
    .input-row{display:flex;gap:0;border:1px solid #30363d;border-radius:10px;overflow:hidden;transition:border .2s}
    .input-row:focus-within{border-color:#58a6ff}
    .badge{padding:0 16px;background:#161b22;display:flex;align-items:center;font-size:.78rem;font-weight:700;white-space:nowrap;border-right:1px solid #30363d;color:#484f58;min-width:110px;justify-content:center}
    .badge.email{color:#3fb950;border-color:#3fb950}
    .badge.phone{color:#f0883e;border-color:#f0883e}
    .badge.username{color:#58a6ff;border-color:#58a6ff}
    input{flex:1;padding:14px 16px;background:#161b22;border:none;color:#c9d1d9;font-size:1rem;outline:none}
    input::placeholder{color:#484f58}
    button{padding:14px 24px;background:#238636;border:none;color:#fff;font-size:.95rem;font-weight:600;cursor:pointer;transition:background .2s}
    button:hover{background:#2ea043}
    button:disabled{background:#21262d;color:#484f58;cursor:not-allowed}
    .hint{text-align:center;margin-top:10px;font-size:.82rem;color:#484f58;min-height:18px}
    .results{max-width:760px;margin:40px auto 80px;padding:0 24px}

    /* Spinner */
    .spinner{text-align:center;padding:48px;color:#8b949e}
    .spinner::after{content:'';display:inline-block;width:28px;height:28px;border:3px solid #30363d;border-top-color:#58a6ff;border-radius:50%;animation:spin .8s linear infinite;vertical-align:middle;margin-left:12px}
    @keyframes spin{to{transform:rotate(360deg)}}

    /* Summary */
    .summary{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px 20px;margin-bottom:24px;display:flex;gap:28px;flex-wrap:wrap}
    .summary-item{display:flex;flex-direction:column;gap:2px}
    .summary-num{font-size:1.6rem;font-weight:700;color:#58a6ff}
    .summary-label{font-size:.78rem;color:#8b949e}

    /* Tool section */
    .tool-section{margin-bottom:28px}
    .tool-header{display:flex;align-items:center;gap:10px;margin-bottom:12px}
    .tool-badge{padding:4px 12px;border-radius:20px;font-size:.75rem;font-weight:700;letter-spacing:.5px}
    .tool-badge.sherlock{background:#0d1f3c;color:#58a6ff;border:1px solid #1f6feb}
    .tool-badge.maigret{background:#1a0d3c;color:#a371f7;border:1px solid #6e40c9}
    .tool-badge.holehe{background:#0d2818;color:#3fb950;border:1px solid #238636}
    .tool-badge.ghunt{background:#3c1f0d;color:#f0883e;border:1px solid #bd561d}
    .tool-badge.phoneinfooga{background:#1a1a0d;color:#e3b341;border:1px solid #9e6a03}
    .tool-badge.dorks{background:#161b22;color:#8b949e;border:1px solid #30363d}
    .tool-count{font-size:.82rem;color:#8b949e}

    /* Cards */
    .card{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:12px 16px;margin-bottom:6px;display:flex;align-items:center;gap:12px;transition:border .15s}
    .card:hover{border-color:#30363d}
    .card-name{font-weight:600;color:#c9d1d9;font-size:.95rem;flex:1}
    .tag{padding:3px 10px;border-radius:20px;font-size:.72rem;font-weight:700}
    .tag.found{background:#0d2818;color:#3fb950;border:1px solid #238636}
    .tag.notfound{background:#161b22;color:#484f58;border:1px solid #30363d}
    .link-card{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:12px 16px;margin-bottom:6px;display:flex;flex-direction:column;gap:3px;text-decoration:none;transition:border .15s}
    .link-card:hover{border-color:#58a6ff}
    .link-card-name{font-weight:600;color:#58a6ff;font-size:.9rem}
    .link-card-url{font-size:.75rem;color:#484f58}

    /* Info grid */
    .info-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px;margin-bottom:8px}
    .info-item{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:12px 14px}
    .info-key{font-size:.72rem;color:#8b949e;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px}
    .info-val{font-size:.92rem;color:#c9d1d9;font-weight:500}

    /* Error / offline */
    .error-box{background:#1a0a0a;border:1px solid #6e1a1a;border-radius:8px;padding:12px 16px;color:#f85149;font-size:.88rem}
    .warn-box{background:#1a150a;border:1px solid #6e4b1a;border-radius:8px;padding:12px 16px;color:#d29922;font-size:.88rem}
    .offline-card{max-width:480px;margin:60px auto;background:#161b22;border:1px solid #30363d;border-radius:12px;padding:32px;text-align:center}
    .offline-card h3{color:#f0883e;margin-bottom:12px}
    .offline-card p{color:#8b949e;margin-bottom:16px;font-size:.9rem}
    .offline-card code{display:block;background:#0d1117;padding:10px 16px;border-radius:6px;color:#3fb950;font-family:monospace;font-size:.95rem;margin:12px 0}
    .divider{border:none;border-top:1px solid #21262d;margin:20px 0}
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
    <p class="subtitle">Ingresa un email, usuario o número — Lalobot detecta y ejecuta todas las herramientas</p>
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
      email:    { label:'✉ Email',    cls:'email',    desc:'Holehe + GHunt — servicios asociados e información de cuenta Google' },
      phone:    { label:'📞 Teléfono', cls:'phone',    desc:'PhoneInfoga + links OSINT — carrier, país, tipo de línea' },
      username: { label:'👤 Usuario',  cls:'username', desc:'Sherlock + Maigret — búsqueda en redes sociales y más sitios' },
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

    const BASE = window.location.origin;

    let backendOk = false;
    async function checkBackend() {
      try {
        const r = await fetch(BASE + '/api/ping', {signal: AbortSignal.timeout(2000)});
        backendOk = (await r.json()).status === 'ok';
      } catch { backendOk = false; }
      document.getElementById('dot').className = 'dot ' + (backendOk ? 'online' : '');
      document.getElementById('statusTxt').textContent = backendOk ? 'Servidor activo' : 'Servidor offline';
    }
    checkBackend();

    async function runSearch() {
      const q = qInput.value.trim();
      if (!q) return;
      if (!backendOk) { showOffline(); return; }

      btn.disabled = true; btn.textContent = 'Buscando...';
      const el = document.getElementById('results');
      el.innerHTML = '<div class="spinner">Ejecutando herramientas OSINT...</div>';

      try {
        const r = await fetch(BASE + '/api/query?q=' + encodeURIComponent(q));
        const data = await r.json();
        renderResults(el, data);
      } catch(e) {
        el.innerHTML = '<div class="error-box">Error al conectar con el servidor: ' + e.message + '</div>';
      } finally {
        btn.disabled = false; btn.textContent = 'Investigar';
      }
    }

    function renderResults(el, data) {
      if (data.error) { el.innerHTML = '<div class="error-box">⚠ ' + esc(data.error) + '</div>'; return; }
      if (data.type === 'email')    renderEmail(el, data);
      else if (data.type === 'phone')    renderPhone(el, data);
      else                               renderUsername(el, data);
    }

    /* ── USERNAME ── */
    function renderUsername(el, data) {
      const sh = data.sherlock || {};
      const mg = data.maigret  || {};
      const shFound = (sh.found || []).length;
      const mgFound = (mg.found || []).length;
      const total   = shFound + mgFound;

      let html = `<div class="summary">
        <div class="summary-item"><span class="summary-num">${total}</span><span class="summary-label">Perfiles totales</span></div>
        <div class="summary-item"><span class="summary-num" style="color:#58a6ff">${shFound}</span><span class="summary-label">Sherlock</span></div>
        <div class="summary-item"><span class="summary-num" style="color:#a371f7">${mgFound}</span><span class="summary-label">Maigret</span></div>
      </div>`;

      html += toolSection('Sherlock', 'sherlock', sh, renderProfileList);
      html += '<hr class="divider">';
      html += toolSection('Maigret', 'maigret', mg, renderProfileList);
      el.innerHTML = html;
    }

    function renderProfileList(data) {
      const found = data.found || [];
      if (data.error) return `<div class="warn-box">⚠ ${esc(data.error)}</div>`;
      if (!found.length) return `<div class="warn-box">Sin perfiles encontrados.</div>`;
      return found.map(f =>
        `<a class="link-card" href="${esc(f.url)}" target="_blank" rel="noopener">
          <span class="link-card-name">${esc(f.platform)}</span>
          <span class="link-card-url">${esc(f.url)}</span>
        </a>`
      ).join('');
    }

    /* ── EMAIL ── */
    function renderEmail(el, data) {
      const ho = data.holehe || {};
      const gh = data.ghunt  || {};
      const hoFound = (ho.found || []).length;

      let html = `<div class="summary">
        <div class="summary-item"><span class="summary-num" style="color:#3fb950">${hoFound}</span><span class="summary-label">Servicios (Holehe)</span></div>
        <div class="summary-item"><span class="summary-num" style="color:#f0883e">${gh.data && Object.keys(gh.data).length ? '✓' : '—'}</span><span class="summary-label">Google (GHunt)</span></div>
      </div>`;

      html += toolSection('Holehe', 'holehe', ho, renderHolehe);
      html += '<hr class="divider">';
      html += toolSection('GHunt', 'ghunt', gh, renderGhunt);
      el.innerHTML = html;
    }

    function renderHolehe(data) {
      if (data.error) return `<div class="warn-box">⚠ ${esc(data.error)}</div>`;
      let h = '';
      if ((data.found || []).length) {
        h += data.found.map(f =>
          `<div class="card"><span class="card-name">${esc(f.service)}</span><span class="tag found">Registrado</span></div>`
        ).join('');
      }
      if ((data.not_found || []).length) {
        h += `<div style="margin-top:10px;font-size:.75rem;color:#8b949e;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">No registrado</div>`;
        h += data.not_found.map(f =>
          `<div class="card"><span class="card-name" style="color:#484f58">${esc(f.service)}</span><span class="tag notfound">No encontrado</span></div>`
        ).join('');
      }
      return h || `<div class="warn-box">Sin resultados.</div>`;
    }

    function renderGhunt(data) {
      if (data.error) return `<div class="warn-box">⚠ ${esc(data.error)}</div>`;
      const d = data.data || {};
      if (!Object.keys(d).length) return `<div class="warn-box">Sin datos de cuenta Google.</div>`;
      let h = '<div class="info-grid">';
      if (d.name)      h += infoItem('Nombre', d.name);
      if (d.gaia_id)   h += infoItem('Gaia ID', d.gaia_id);
      if (d.last_edit) h += infoItem('Último cambio', d.last_edit);
      h += '</div>';
      if (d.services && d.services.length) {
        h += `<div style="margin-top:10px;font-size:.75rem;color:#8b949e;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">Servicios Google</div>`;
        h += d.services.map(s => `<div class="card"><span class="card-name">${esc(s)}</span></div>`).join('');
      }
      if (d.photo) {
        h += `<div style="margin-top:10px"><img src="${esc(d.photo)}" style="width:80px;height:80px;border-radius:50%;border:2px solid #30363d" alt="foto"></div>`;
      }
      return h;
    }

    /* ── PHONE ── */
    function renderPhone(el, data) {
      const pi = data.phoneinfooga || {};
      const links = data.links || [];

      let html = '';
      if (!pi.error && pi.valid) {
        html += `<div class="summary">
          <div class="summary-item"><span class="summary-num" style="color:#e3b341">${esc(pi.type || '?')}</span><span class="summary-label">Tipo de línea</span></div>
          <div class="summary-item"><span class="summary-num" style="color:#e3b341">${esc(pi.country || '?')}</span><span class="summary-label">País / Región</span></div>
          ${pi.carrier ? `<div class="summary-item"><span class="summary-num" style="color:#e3b341;font-size:1.1rem">${esc(pi.carrier)}</span><span class="summary-label">Operador</span></div>` : ''}
        </div>`;
      }

      html += toolSection('PhoneInfoga', 'phoneinfooga', pi, renderPhoneInfo);
      html += '<hr class="divider">';
      html += `<div class="tool-section">
        <div class="tool-header">
          <span class="tool-badge dorks">OSINT Links</span>
          <span class="tool-count">${links.length} fuentes</span>
        </div>
        ${links.map(l => `<a class="link-card" href="${esc(l.url)}" target="_blank" rel="noopener">
          <span class="link-card-name">${esc(l.name)}</span>
          <span class="link-card-url">${esc(l.url)}</span>
        </a>`).join('')}
      </div>`;
      el.innerHTML = html;
    }

    function renderPhoneInfo(data) {
      if (data.error) return `<div class="warn-box">⚠ ${esc(data.error)}</div>`;
      let h = '<div class="info-grid">';
      if (data.international) h += infoItem('Internacional', data.international);
      if (data.national)      h += infoItem('Nacional', data.national);
      if (data.country)       h += infoItem('País / Región', data.country);
      if (data.carrier)       h += infoItem('Operador', data.carrier);
      if (data.type)          h += infoItem('Tipo', data.type);
      if (data.timezones && data.timezones.length) h += infoItem('Zonas horarias', data.timezones.join(', '));
      h += '</div>';
      return h;
    }

    /* ── Helpers ── */
    function toolSection(name, cls, data, renderFn) {
      const count = data.found ? `${data.found.length} encontrados` : data.total ? `${data.total}` : '';
      return `<div class="tool-section">
        <div class="tool-header">
          <span class="tool-badge ${cls}">${name}</span>
          ${count ? `<span class="tool-count">${count}</span>` : ''}
        </div>
        ${renderFn(data)}
      </div>`;
    }

    function infoItem(k, v) {
      return `<div class="info-item"><div class="info-key">${esc(k)}</div><div class="info-val">${esc(v)}</div></div>`;
    }

    function showOffline() {
      document.getElementById('results').innerHTML = `
        <div class="offline-card">
          <h3>🔌 Servidor no disponible</h3>
          <p>Para usar Lalobot, inicia el servidor local:</p>
          <code>python3 main.py web</code>
          <p>Luego recarga esta página o accede desde<br><a href="${BASE}" style="color:#58a6ff">${BASE}</a></p>
        </div>`;
    }

    function esc(s) {
      return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
    }
  </script>
</body>
</html>"""


def run(host="0.0.0.0", port=5001):
    print(f"Servidor iniciado en http://localhost:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run()
