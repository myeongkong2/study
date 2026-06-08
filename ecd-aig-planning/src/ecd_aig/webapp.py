from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from .models import load_project
from .pre_response import pre_response_readiness

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_ROOT = ROOT / "examples"
DEFAULT_PROJECT = EXAMPLES_ROOT / "job_stress_workload_12item_user_project.json"


def available_projects() -> list[str]:
    projects = []
    for path in EXAMPLES_ROOT.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            projects.append(path.name)
    return sorted(projects)


def resolve_project(name: str | None) -> Path:
    if not name:
        return DEFAULT_PROJECT
    candidate = EXAMPLES_ROOT / Path(name).name
    if candidate.suffix.lower() != ".json" or candidate.name != name or candidate.name not in available_projects():
        raise ValueError("unknown example project")
    return candidate


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/projects":
                self._json({"projects": available_projects()})
                return
            if parsed.path == "/api/project":
                selected = parse_qs(parsed.query).get("name", [None])[0]
                project_path = resolve_project(selected)
                project = load_project(project_path)
                self._json({"source": project_path.name, "project": project.to_dict(), "readiness": pre_response_readiness(project)})
                return
            self._html()
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self._json({"ok": False, "error": str(exc)}, status=400)

    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self) -> None:
        body = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


HTML = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>ECD-AIG Planning</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #f7f7f4; color: #1e2528; }
    header { padding: 24px 32px; border-bottom: 1px solid #d8ded8; background: #ffffff; }
    main { padding: 24px 32px; display: grid; grid-template-columns: 320px 1fr; gap: 20px; }
    section, aside { background: #fff; border: 1px solid #d8ded8; border-radius: 6px; padding: 16px; }
    .badge { display: inline-block; padding: 3px 8px; border-radius: 999px; background: #e6f2ee; margin-left: 8px; font-size: 12px; }
    table { width: 100%; border-collapse: collapse; }
    td, th { border-bottom: 1px solid #e6e8e6; padding: 8px; text-align: left; vertical-align: top; }
    pre { white-space: pre-wrap; background: #f2f3f0; padding: 12px; border-radius: 6px; }
  </style>
</head>
<body>
  <header><h1>ECD-AIG Planning <span class="badge">local prototype</span></h1></header>
  <main>
    <aside><h2>Readiness</h2><label for="project">Example project</label><select id="project"></select><div id="summary">Loading...</div></aside>
    <section><h2>Item Bank</h2><table id="items"></table></section>
  </main>
  <script>
    const summary = document.querySelector('#summary');
    const items = document.querySelector('#items');
    const projectSelect = document.querySelector('#project');
    const addText = (parent, tag, text) => {
      const node = document.createElement(tag);
      node.textContent = text;
      parent.appendChild(node);
    };
    const renderError = error => {
      summary.replaceChildren();
      items.replaceChildren();
      addText(summary, 'p', `Error: ${error}`);
    };
    const loadProject = name => fetch(`/api/project?name=${encodeURIComponent(name)}`)
      .then(r => r.json().then(data => {
        if (!r.ok) throw new Error(data.error || 'Unable to load project');
        return data;
      }))
      .then(data => {
        summary.replaceChildren();
        items.replaceChildren();
        addText(summary, 'p', `Project: ${data.project.title}`);
        addText(summary, 'p', `Pre-response status: ${data.readiness.status}`);
        addText(summary, 'p', `Structural screening: ${data.readiness.structural_screening.ok ? 'PASS' : 'FAIL'}`);
        addText(summary, 'p', `Item-quality screening: ${data.readiness.item_quality_screening.ok ? 'PASS' : 'FAIL'}`);
        addText(summary, 'p', `Boundary: ${data.readiness.validity_boundary}`);
        const header = document.createElement('tr');
        ['ID', 'Stem', 'KSA'].forEach(value => addText(header, 'th', value));
        items.appendChild(header);
        data.project.items.forEach(item => {
          const row = document.createElement('tr');
          [item.id, item.stem, item.ksa_id].forEach(value => addText(row, 'td', value || ''));
          items.appendChild(row);
        });
      })
      .catch(error => renderError(error.message));
    fetch('/api/projects').then(r => r.json()).then(data => {
      data.projects.forEach(name => {
        const option = document.createElement('option');
        option.value = name;
        option.textContent = name;
        projectSelect.appendChild(option);
      });
      projectSelect.value = 'job_stress_workload_12item_user_project.json';
      loadProject(projectSelect.value);
    }).catch(error => renderError(error.message));
    projectSelect.addEventListener('change', () => loadProject(projectSelect.value));
  </script>
</body>
</html>"""


def run(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Serving ECD-AIG webapp at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
