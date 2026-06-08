import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from sim_app import LeagueState


PORT = 8765
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
STATE = LeagueState()


def replace_state(new_state):
    global STATE
    STATE = new_state


class Handler(BaseHTTPRequestHandler):
    def send_json(self, payload, status=200):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

    def serve_static(self, path):
        if path == "/":
            path = "/index.html"
        full_path = os.path.abspath(os.path.join(STATIC_DIR, path.lstrip("/")))
        if not full_path.startswith(os.path.abspath(STATIC_DIR)) or not os.path.exists(full_path):
            self.send_error(404)
            return
        with open(full_path, "rb") as handle:
            data = handle.read()
        content_type = mimetypes.guess_type(full_path)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/state":
            self.send_json(STATE.payload())
            return
        self.serve_static(parsed.path)

    def do_POST(self):
        body = self.read_body()
        try:
            if self.path == "/api/new":
                STATE.new_league(body.get("team", "Mumbai Indians"), body.get("difficulty", "hard"))
            elif self.path == "/api/load":
                replace_state(LeagueState.load())
            elif self.path == "/api/save":
                STATE.save()
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
                    body.get("batting_first_xi", []),
                    body.get("bowling_first_xi", []),
                    body.get("bat_to_bowl", {}),
                    body.get("bowl_to_bat", {}),
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
    print(f"IPL UI running at http://localhost:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
