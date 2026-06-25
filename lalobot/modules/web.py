from flask import Flask, request, jsonify, render_template_string
from lalobot.modules.osint_search import parse_readme

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Lalobot — OSINT Search</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #0d1117; color: #c9d1d9; font-family: 'Segoe UI', system-ui, sans-serif; min-height: 100vh; }

    header { background: #161b22; border-bottom: 1px solid #30363d; padding: 20px 40px; display: flex; align-items: center; gap: 16px; }
    header h1 { font-size: 1.4rem; color: #58a6ff; font-weight: 700; letter-spacing: 1px; }
    header span { color: #8b949e; font-size: 0.85rem; }

    .search-wrap { padding: 40px 40px 20px; max-width: 900px; margin: 0 auto; }
    .search-box { display: flex; gap: 10px; }
    .search-box input {
      flex: 1; padding: 12px 18px; border-radius: 8px;
      border: 1px solid #30363d; background: #161b22; color: #c9d1d9;
      font-size: 1rem; outline: none; transition: border .2s;
    }
    .search-box input:focus { border-color: #58a6ff; }
    .search-box input::placeholder { color: #484f58; }
    .search-box button {
      padding: 12px 24px; border-radius: 8px; border: none;
      background: #238636; color: #fff; font-size: 1rem;
      cursor: pointer; font-weight: 600; transition: background .2s;
    }
    .search-box button:hover { background: #2ea043; }

    .stats { padding: 0 40px 20px; max-width: 900px; margin: 0 auto; color: #8b949e; font-size: 0.88rem; min-height: 24px; }
    .results { padding: 0 40px 60px; max-width: 900px; margin: 0 auto; }

    .section-header {
      margin: 28px 0 12px; padding: 6px 14px;
      background: #161b22; border-left: 3px solid #f0883e;
      border-radius: 4px; font-size: 0.82rem; font-weight: 700;
      color: #f0883e; letter-spacing: 0.5px; text-transform: uppercase;
    }
    .card {
      background: #161b22; border: 1px solid #21262d;
      border-radius: 8px; padding: 14px 18px; margin-bottom: 10px;
      transition: border-color .2s; cursor: pointer;
    }
    .card:hover { border-color: #58a6ff; }
    .card-name { font-weight: 700; color: #58a6ff; font-size: 1rem; margin-bottom: 4px; }
    .card-url { color: #3fb950; font-size: 0.82rem; word-break: break-all; }
    .card-desc { margin-top: 6px; color: #8b949e; font-size: 0.88rem; line-height: 1.5; }

    .empty { text-align: center; padding: 60px 20px; color: #484f58; }
    .empty p { font-size: 1rem; }
    #spinner { display: none; color: #8b949e; font-size: 0.88rem; padding: 0 40px; max-width: 900px; margin: 0 auto 10px; }

    .modal-overlay {
      display: none; position: fixed; inset: 0;
      background: rgba(0,0,0,.75); z-index: 100;
      align-items: center; justify-content: center;
    }
    .modal-overlay.open { display: flex; }
    .modal {
      background: #161b22; border: 1px solid #30363d; border-radius: 12px;
      width: 92vw; max-width: 960px; height: 82vh;
      display: flex; flex-direction: column; overflow: hidden;
      box-shadow: 0 24px 60px rgba(0,0,0,.6);
    }
    .modal-header {
      display: flex; align-items: center; gap: 12px;
      padding: 14px 18px; border-bottom: 1px solid #30363d;
      background: #0d1117; flex-shrink: 0;
    }
    .modal-title { flex: 1; font-weight: 700; color: #58a6ff; font-size: 1rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .modal-url-bar {
      flex: 2; padding: 6px 12px; border-radius: 6px;
      border: 1px solid #30363d; background: #161b22;
      color: #8b949e; font-size: 0.78rem; white-space: nowrap;
      overflow: hidden; text-overflow: ellipsis;
    }
    .modal-btn { padding: 6px 14px; border-radius: 6px; border: none; font-size: 0.82rem; cursor: pointer; font-weight: 600; white-space: nowrap; }
    .btn-open { background: #238636; color: #fff; }
    .btn-open:hover { background: #2ea043; }
    .btn-close { background: #21262d; color: #c9d1d9; }
    .btn-close:hover { background: #30363d; }
    .modal-body { flex: 1; position: relative; }
    .modal-body iframe { width: 100%; height: 100%; border: none; }
    .modal-blocked {
      display: none; position: absolute; inset: 0;
      background: #0d1117; align-items: center; justify-content: center;
      flex-direction: column; gap: 16px; color: #8b949e; text-align: center; padding: 40px;
    }
    .modal-blocked.show { display: flex; }
    .modal-blocked a { color: #58a6ff; }
  </style>
</head>
<body>
  <header>
    <h1>&#x1F916; Lalobot — OSINT Search</h1>
    <span>awesome-osint &mdash; {{ total }} herramientas indexadas</span>
  </header>
  <div class="search-wrap">
    <div class="search-box">
      <input type="text" id="q" placeholder="Buscar herramienta, categoría, URL..." autofocus>
      <button onclick="buscar()">Buscar</button>
    </div>
  </div>
  <div id="spinner">Buscando...</div>
  <div class="stats" id="stats"></div>
  <div class="results" id="results">
    <div class="empty"><p>Escribe un término para buscar herramientas OSINT</p></div>
  </div>

  <div class="modal-overlay" id="modalOverlay" onclick="closeModal(event)">
    <div class="modal">
      <div class="modal-header">
        <span class="modal-title" id="modalTitle"></span>
        <span class="modal-url-bar" id="modalUrlBar"></span>
        <button class="modal-btn btn-open" onclick="openExternal()">&#x1F517; Abrir sitio</button>
        <button class="modal-btn btn-close" onclick="cerrarModal()">&#x2715; Cerrar</button>
      </div>
      <div class="modal-body">
        <iframe id="modalFrame" sandbox="allow-scripts allow-same-origin allow-forms" src="about:blank"></iframe>
        <div class="modal-blocked" id="modalBlocked">
          <p>Este sitio no permite mostrarse en un marco.<br>
          <a id="modalExtLink" href="#" target="_blank" rel="noopener">Abrir en nueva pestaña &#x2197;</a></p>
        </div>
      </div>
    </div>
  </div>

  <script>
    const input = document.getElementById('q');
    input.addEventListener('keydown', e => { if (e.key === 'Enter') buscar(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') cerrarModal(); });
    let currentUrl = '';

    async function buscar() {
      const q = input.value.trim();
      if (!q) return;
      document.getElementById('spinner').style.display = 'block';
      document.getElementById('stats').textContent = '';
      document.getElementById('results').innerHTML = '';
      const res = await fetch('/api/search?q=' + encodeURIComponent(q));
      const data = await res.json();
      document.getElementById('spinner').style.display = 'none';
      if (data.results.length === 0) {
        document.getElementById('stats').textContent = 'Sin resultados para "' + q + '"';
        document.getElementById('results').innerHTML = '<div class="empty"><p>No se encontraron herramientas para ese término.</p></div>';
        return;
      }
      document.getElementById('stats').textContent = data.results.length + ' resultado(s) para "' + q + '"';
      let html = '', lastSection = null;
      for (const r of data.results) {
        if (r.section !== lastSection) {
          html += '<div class="section-header">' + esc(r.section) + '</div>';
          lastSection = r.section;
        }
        html += `<div class="card" onclick="abrirModal('${esc(r.url)}','${esc(r.name)}')">
          <div class="card-name">${esc(r.name)}</div>
          <div class="card-url">${esc(r.url)}</div>
          ${r.desc ? '<div class="card-desc">' + esc(r.desc) + '</div>' : ''}
        </div>`;
      }
      document.getElementById('results').innerHTML = html;
    }

    function abrirModal(url, name) {
      currentUrl = url;
      const frame = document.getElementById('modalFrame');
      const blocked = document.getElementById('modalBlocked');
      document.getElementById('modalTitle').textContent = name;
      document.getElementById('modalUrlBar').textContent = url;
      document.getElementById('modalExtLink').href = url;
      blocked.classList.remove('show');
      frame.src = 'about:blank';
      let timer = setTimeout(() => {
        try { if (!frame.contentDocument?.body?.innerHTML) blocked.classList.add('show'); }
        catch(e) { blocked.classList.add('show'); }
      }, 4000);
      frame.onload = () => {
        clearTimeout(timer);
        try { if (!frame.contentDocument?.body?.innerHTML) blocked.classList.add('show'); }
        catch(e) { blocked.classList.add('show'); }
      };
      frame.src = url;
      document.getElementById('modalOverlay').classList.add('open');
      document.body.style.overflow = 'hidden';
    }

    function cerrarModal() {
      document.getElementById('modalOverlay').classList.remove('open');
      document.getElementById('modalFrame').src = 'about:blank';
      document.getElementById('modalBlocked').classList.remove('show');
      document.body.style.overflow = '';
    }

    function closeModal(e) { if (e.target === document.getElementById('modalOverlay')) cerrarModal(); }
    function openExternal() { window.open(currentUrl, '_blank', 'noopener'); }
    function esc(s) {
      return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
    }
  </script>
</body>
</html>
"""

ENTRIES = parse_readme()


@app.route("/")
def index():
    return render_template_string(HTML, total=len(ENTRIES))


@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").lower().strip()
    if not q:
        return jsonify({"results": []})
    results = [
        {"section": sec, "name": name, "url": url, "desc": desc}
        for sec, name, url, desc in ENTRIES
        if q in f"{name} {url} {desc} {sec}".lower()
    ]
    return jsonify({"results": results})


def run(host="0.0.0.0", port=5001):
    print(f"Servidor iniciado en http://localhost:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run()
