"""Flask-powered web interface to control the breakout bot."""
from __future__ import annotations

import os
from typing import Annotated

from flask import Flask, jsonify, redirect, render_template_string, request, url_for

from bot_controller import BotController
from logger import LOG_PATH, get_logger
from performance import metrics

logger = get_logger()

app = Flask(__name__)
controller = BotController()

# ---------------------------------------------------------------------------
# HTML template (Bootstrap, animated)
# ---------------------------------------------------------------------------

TEMPLATE: str = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\" />
    <title>Breakout Bot Dashboard</title>
    <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
    <script src=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js\"></script>
    <style>
        body { padding-top: 40px; background:#f5f7fa; }
        .status-dot { height:14px; width:14px; border-radius:50%; display:inline-block; margin-right:6px; animation: pulse 1.5s infinite; }
        @keyframes pulse {
            0% { transform: scale(0.9); opacity:0.7 }
            50% { transform: scale(1); opacity:1 }
            100% { transform: scale(0.9); opacity:0.7 }
        }
        #logs-box { height: 300px; overflow-y: scroll; background:#272822; color:#f8f8f2; padding:10px; font-size:0.85em; border-radius:4px; }
        pre { margin:0 }
    </style>
</head>
<body>
<div class=\"container\">
    <div class=\"d-flex justify-content-between align-items-center mb-4\">
        <h2>📊 Breakout Scalping Bot</h2>
        <form method=\"post\" action=\"{{ url_for('toggle') }}\">
            {% if is_running %}
                <button class=\"btn btn-danger\" name=\"action\" value=\"stop\">Stop Bot</button>
            {% else %}
                <button class=\"btn btn-success\" name=\"action\" value=\"start\">Start Bot</button>
            {% endif %}
        </form>
    </div>

    <div class=\"row g-3 mb-4\">
        <div class=\"col-md-3\">
            <div class=\"card text-center shadow\">
                <div class=\"card-body\">
                    <span class=\"status-dot\" id=\"status-dot\" style=\"background:{{ 'green' if is_running else 'red' }}\"></span>
                    <span id=\"status-text\">{{ 'RUNNING' if is_running else 'STOPPED' }}</span>
                </div>
            </div>
        </div>
        <div class=\"col-md-3\"><div class=\"card shadow text-center\"><div class=\"card-body\"><h6>Runs</h6><h3 id=\"run-count\">0</h3></div></div></div>
        <div class=\"col-md-3\"><div class=\"card shadow text-center\"><div class=\"card-body\"><h6>Signals Sent</h6><h3 id=\"signals-sent\">0</h3></div></div></div>
        <div class=\"col-md-3\"><div class=\"card shadow text-center\"><div class=\"card-body\"><h6>Last Run (UTC)</h6><h6 id=\"last-run\">-</h6></div></div></div>
    </div>

    <h5>Last Signals</h5>
    <div id=\"signals-table\" class=\"table-responsive\"></div>

    <h5 class=\"mt-4\">Live Logs</h5>
    <div id=\"logs-box\"><pre id=\"logs-content\"></pre></div>
</div>

<script>
function fetchMetrics() {
    fetch('/api/metrics').then(r=>r.json()).then(d=>{
        document.getElementById('run-count').textContent = d.run_count;
        document.getElementById('signals-sent').textContent = d.signals_sent;
        document.getElementById('last-run').textContent = d.last_run ? new Date(d.last_run).toLocaleString() : '-';
        // status update
        const running = d.running;
        document.getElementById('status-text').textContent = running ? 'RUNNING' : 'STOPPED';
        document.getElementById('status-dot').style.background = running ? 'green' : 'red';

        // last signals table
        const tableDiv = document.getElementById('signals-table');
        if(!d.last_signals || d.last_signals.length===0) { tableDiv.innerHTML='<p>No signals yet.</p>'; return; }
        let html = '<table class="table table-striped table-sm"><thead><tr><th>Pair</th><th>Signal</th><th>Confidence</th><th>Reasons</th></tr></thead><tbody>';
        d.last_signals.forEach(s=>{
            html += `<tr><td>${s.pair}</td><td>${s.signal}</td><td>${s.confidence}%</td><td>${s.details.map(d=>d.reason).join(', ')}</td></tr>`;
        });
        html += '</tbody></table>';
        tableDiv.innerHTML = html;
    });
}

function fetchLogs() {
    fetch('/api/logs').then(r=>r.text()).then(t=>{
        const el = document.getElementById('logs-content');
        el.textContent = t;
        // auto-scroll to bottom
        const box = document.getElementById('logs-box');
        box.scrollTop = box.scrollHeight;
    });
}

fetchMetrics();
fetchLogs();
setInterval(fetchMetrics, 5000);
setInterval(fetchLogs, 5000);
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/", methods=["GET"])
def index() -> str:  # noqa: D401
    """Render the dashboard."""
    return render_template_string(TEMPLATE, is_running=controller.is_running)


@app.route("/toggle", methods=["POST"])
def toggle() -> Annotated[str, "WEBSERVER"]:  # type: ignore[name-defined]
    """Start or stop the bot."""
    action: str = request.form.get("action", "")  # type: ignore[assignment]
    if action == "start":
        controller.start()
    elif action == "stop":
        controller.stop()
    return redirect(url_for("index"))


# ----------------------- API endpoints ------------------------------------


@app.route("/api/metrics", methods=["GET"])
def api_metrics():  # noqa: D401
    """Return JSON snapshot of performance metrics."""
    return jsonify(metrics.snapshot(controller.is_running))


@app.route("/api/logs", methods=["GET"])
def api_logs():  # noqa: D401
    """Return last N lines of log file as plain text."""
    lines_param = request.args.get("lines", 300)
    try:
        n_lines = int(lines_param)
    except ValueError:
        n_lines = 300

    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            all_lines = f.readlines()[-n_lines:]
        return "".join(all_lines)
    except FileNotFoundError:
        return "Log file not found. Start the bot to generate logs."


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_webui(host: str = "0.0.0.0", port: int = int(os.getenv("PORT", 8000))) -> None:
    """Launch Flask server."""
    logger.info("Starting web UI on %s:%s", host, port)
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == "__main__":
    run_webui()