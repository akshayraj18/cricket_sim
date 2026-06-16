"""Local HTTP server for the Cricket franchise sim's web UI.

A small stdlib `http.server` that does two jobs: serves the static frontend
(`webapp/index.html`, `app.js`, `styles.css`) and exposes a JSON action API
under `/api/...`. Each POST to `/api/<action>` mutates the single shared
`LeagueState` (and its `live_match`, when one is active) and responds with
the full state payload so the frontend can re-render. `/api/state` (GET)
returns that same payload without mutating anything, e.g. on page load.

Kept as a fallback/reference during the migration to the FastAPI backend
under `backend/`.
"""
import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from cricket_sim_engine.sim import LeagueState


PORT = 8765
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "webapp")
STATE = LeagueState()


def replace_state(new_state):
    """Swap in a freshly loaded `LeagueState` (used by `/api/load`)."""
    global STATE
    STATE = new_state


class Handler(BaseHTTPRequestHandler):
    """Routes static asset requests and `/api/...` JSON actions to `STATE`."""

    def send_json(self, payload, status=200):
        """Write `payload` to the response body as JSON with the given HTTP status."""
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_body(self):
        """Parse the request body as JSON, defaulting to an empty object."""
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

    def serve_static(self, path):
        """Serve a file from `static/`, defaulting `/` to `index.html`.

        Resolves the path within `STATIC_DIR` and rejects anything that
        would escape it (e.g. via `..`) or doesn't exist, returning a 404.
        """
        if path == "/":
            path = "/index.html"
        full_path = os.path.abspath(os.path.join(STATIC_DIR, path.lstrip("/")))
        if not full_path.startswith(os.path.abspath(STATIC_DIR)) or not os.path.exists(full_path):
            self.send_error(404)
            return
        with open(full_path, "rb") as handle:
            data = handle.read()
        content_type = mimetypes.guess_type(full_path)[0] or "application/octet-stream"
        # `content_type` is derived from the file extension, but guard against
        # any CRLF sneaking into a response header (HTTP response splitting).
        if "\r" in content_type or "\n" in content_type:
            content_type = "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        """Serve `/api/state` as JSON, otherwise fall through to static files."""
        parsed = urlparse(self.path)
        if parsed.path == "/api/state":
            self.send_json(STATE.payload())
            return
        if parsed.path == "/api/saves":
            self.send_json({"saves": LeagueState.list_saves()})
            return
        self.serve_static(parsed.path)

    def do_POST(self):
        """Dispatch a `/api/<action>` request to the matching `LeagueState`/`LiveMatch` method.

        On success, responds with the refreshed state payload; any exception
        raised by the action (e.g. invalid move, out-of-turn request) is
        caught and reported to the frontend as a 400 with the error message,
        so a single bad request can't crash the server or corrupt state.
        """
        body = self.read_body()
        try:
            if self.path == "/api/new":
                draft_pool = body.get("draft_pool", "current")
                if draft_pool == "rosters2026":
                    STATE.new_league_with_rosters(body.get("team", "Mumbai Mavericks"), body.get("difficulty", "hard"))
                else:
                    STATE.new_league(body.get("team", "Mumbai Mavericks"), body.get("difficulty", "hard"), draft_pool)
            elif self.path == "/api/load":
                replace_state(LeagueState.load(body.get("name") or None))
            elif self.path == "/api/save":
                STATE.save(body.get("name") or None)
            elif self.path == "/api/delete-save":
                LeagueState.delete_save(body["name"])
            elif self.path == "/api/draft":
                STATE.user_pick(body["player"])
            elif self.path == "/api/start-draft":
                STATE.start_draft()
            elif self.path == "/api/autodraft":
                if body.get("mode") == "all":
                    STATE.autodraft_to_end()
                else:
                    STATE.autodraft_user_pick()
            elif self.path == "/api/leadership":
                STATE.set_leadership(body["captain"], body["vice"], body.get("wicketkeeper", ""))
            elif self.path == "/api/presets":
                STATE.set_user_presets(
                    body.get("batting_order", []),
                    body.get("bowling_order", []),
                    body.get("starting_xi"),
                    body.get("impact_sub_name"),
                    body.get("wicketkeeper", ""),
                )
            elif self.path == "/api/open-retention":
                STATE.open_retention()
            elif self.path == "/api/retention":
                STATE.submit_retentions(body.get("players", []))
            elif self.path == "/api/begin-match":
                STATE.begin_match_day(interactive=True)
            elif self.path == "/api/simulate-round":
                STATE.simulate_current_round()
            elif self.path == "/api/start-playoffs":
                STATE.start_playoffs()
            elif self.path == "/api/toss":
                STATE.live_match.choose_toss(body["decision"])
            elif self.path == "/api/lineup":
                STATE.live_match.set_user_xi(
                    body.get("xi", []),
                    body.get("batting_order", []),
                    body.get("bowling_order", []),
                    body.get("intents", {}),
                    body.get("save", False),
                    body.get("context", "batting"),
                    body.get("wicketkeeper", ""),
                )
            elif self.path == "/api/play-over":
                STATE.live_match.play_over(body.get("bowler"), max_balls=int(body.get("balls", 6)), stop_on_wicket=body.get("stop_on_wicket", True))
            elif self.path == "/api/play-ball":
                STATE.live_match.play_over(body.get("bowler"), max_balls=1, stop_on_wicket=True)
            elif self.path == "/api/play-until":
                balls = int(body.get("balls", 6))
                while STATE.live_match and STATE.live_match.status == "over" and balls > 0:
                    before = STATE.live_match.score["balls"]
                    STATE.live_match.play_over(body.get("bowler"), max_balls=min(6, balls), stop_on_wicket=body.get("stop_on_wicket", True))
                    balls -= max(1, STATE.live_match.score["balls"] - before)
                    if body.get("stop_on_wicket", True) and STATE.live_match.score.get("last_event_wicket") and STATE.live_match.status != "over":
                        break
                    if STATE.live_match.status != "over":
                        break
            elif self.path == "/api/aggression":
                STATE.live_match.set_aggression(body.get("batting", {}), body.get("bowling", {}))
            elif self.path == "/api/next-batter":
                STATE.live_match.select_next_batter(body.get("name", ""))
            elif self.path == "/api/super-over-lineup":
                STATE.live_match.set_super_over_lineup(body.get("batters", []), body.get("bowler", ""))
            elif self.path == "/api/impact-sub":
                STATE.live_match.apply_impact_sub(body.get("out"), body.get("in"))
            elif self.path == "/api/complete-live-match":
                STATE.complete_live_match()
            else:
                self.send_error(404)
                return
            self.send_json(STATE.payload())
        except Exception as exc:
            self.send_json({"error": str(exc)}, 400)

    def log_message(self, fmt, *args):
        return


if __name__ == "__main__":
    print(f"Cricket UI running at http://localhost:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
