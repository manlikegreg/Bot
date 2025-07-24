"""Flask-powered web interface to control the breakout bot."""
from __future__ import annotations

import os
from typing import Annotated

from flask import Flask, redirect, render_template_string, request, url_for

from bot_controller import BotController
from logger import get_logger

logger = get_logger()

app = Flask(__name__)
controller = BotController()

# ---------------------------------------------------------------------------
# HTML template (inline for simplicity)
# ---------------------------------------------------------------------------

TEMPLATE: str = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\" />
    <title>Breakout Bot Control</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 400px; margin: auto; text-align: center; }
        .status { font-size: 1.2em; margin-bottom: 20px; }
        button { padding: 12px 24px; font-size: 1em; margin: 5px; cursor: pointer; }
        .running { color: green; }
        .stopped { color: red; }
    </style>
</head>
<body>
    <div class=\"container\">
        <h1>📊 Breakout Scalping Bot</h1>
        <p class=\"status {{ 'running' if is_running else 'stopped' }}\">
            Status: {{ 'RUNNING' if is_running else 'STOPPED' }}
        </p>
        <form method=\"post\" action=\"{{ url_for('toggle') }}\">
            {% if is_running %}
                <button type=\"submit\" name=\"action\" value=\"stop\" style=\"background:#e74c3c;color:#fff;\">Stop</button>
            {% else %}
                <button type=\"submit\" name=\"action\" value=\"start\" style=\"background:#2ecc71;color:#fff;\">Start</button>
            {% endif %}
        </form>
    </div>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index() -> str:  # noqa: D401
    """Render the control dashboard."""
    return render_template_string(TEMPLATE, is_running=controller.is_running)


@app.route("/toggle", methods=["POST"])
def toggle() -> Annotated[str, "WEBSERVER"]:  # type: ignore[name-defined]
    """Handle start/stop requests."""
    action: str = request.form.get("action", "")  # type: ignore[assignment]
    if action == "start":
        controller.start()
    elif action == "stop":
        controller.stop()
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_webui(host: str = "0.0.0.0", port: int = int(os.getenv("PORT", 8000))) -> None:
    """Start the Flask web server."""
    logger.info("Starting web UI on %s:%s", host, port)
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run_webui()