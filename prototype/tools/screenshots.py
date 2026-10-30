"""Capture README screenshots of the running app with headless Chrome (CDP).

    python tools/screenshots.py --out ../docs/screenshots

Needs the app on http://localhost:8000 and the seeded demo (test accounts from seed_users.yaml).
"""
from __future__ import annotations

import argparse
import base64
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import httpx
import websocket
import yaml

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BASE = "http://localhost:8000"
ROOT = Path(__file__).resolve().parent.parent


def session_cookie(username: str, password: str) -> str:
    c = httpx.Client(base_url=BASE, follow_redirects=False)
    r = c.post("/login", data={"username": username, "password": password})
    assert r.status_code == 303, f"login failed for {username}"
    return c.cookies.get("session")


class Tab:
    def __init__(self, port: int):
        for _ in range(50):
            try:
                tabs = httpx.get(f"http://127.0.0.1:{port}/json").json()
                break
            except httpx.HTTPError:
                time.sleep(0.2)
        page = next(t for t in tabs if t["type"] == "page")
        self.ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=60)
        self.i = 0

    def call(self, method, **params):
        self.i += 1
        self.ws.send(json.dumps({"id": self.i, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.i:
                return msg.get("result", {})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT.parent / "docs" / "screenshots"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cfg = yaml.safe_load((ROOT / "seed_users.yaml").read_text())
    pw = {u["username"]: u["password"] for u in cfg["users"]}
    shots = json.loads((ROOT / "tools" / "shots.json").read_text())
    port = 9333
    prof = tempfile.mkdtemp()
    proc = subprocess.Popen([CHROME, "--headless=new", f"--remote-debugging-port={port}", f"--user-data-dir={prof}",
                             "--hide-scrollbars", "--force-device-scale-factor=1", "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        tab = Tab(port)
        tab.call("Network.enable")
        cookies = {}
        for s in shots:
            who = s["user"]
            if who not in cookies:
                cookies[who] = session_cookie(who, pw.get(who, cfg["institution_password"]))
            tab.call("Network.clearBrowserCookies")
            tab.call("Network.setCookie", name="session", value=cookies[who], url=BASE)
            tab.call("Emulation.setDeviceMetricsOverride", width=s.get("width", 1440), height=s.get("height", 900),
                     deviceScaleFactor=1, mobile=False)
            tab.call("Page.navigate", url=BASE + s["path"])
            time.sleep(s.get("wait", 2.5))
            if s.get("scroll"):
                tab.call("Runtime.evaluate", expression=f"window.scrollTo(0,{s['scroll']})")
                time.sleep(0.8)
            shot = tab.call("Page.captureScreenshot", format="png")
            (out / s["name"]).write_bytes(base64.b64decode(shot["data"]))
            print("saved", s["name"])
    finally:
        proc.terminate()
        shutil.rmtree(prof, ignore_errors=True)


if __name__ == "__main__":
    main()
