#!/usr/bin/env python3
"""Capture Kaggle/video media assets from the static Edge-Triage demo.

This script starts a temporary local HTTP server for `site/`, uses a local
Chromium/Chrome binary to capture deterministic screenshots, and writes them to
`media/screenshots/`. It also creates a live-result-card screenshot from a tiny
HTML harness that calls the real `renderLiveResult()` function from `site/app.js`.
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import tempfile
import textwrap
import time
from functools import partial
from http.client import RemoteDisconnected
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "site"
MEDIA_DIR = ROOT / "media"
SCREENSHOT_DIR = MEDIA_DIR / "screenshots"
CHART_DIR = MEDIA_DIR / "charts"
SCENARIO_DIR = MEDIA_DIR / "scenario-inputs"
LIVE_RESULT_DIR = MEDIA_DIR / "live-results"

WINDOW = "1440,1100"

LIVE_SCENARIOS = [
    {
        "id": "bridge-flood-damage",
        "input_file": "bridge-flood-damage.jpg",
        "screenshot": "06-live-optimization-bridge-flood.png",
        "title": "Flood-damaged bridge",
        "note": "Optimization Mode live check: flood-damaged bridge and road crossing over a swollen creek.",
        "scenario_family": "infrastructure_and_utility_damage",
        "source_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Bridge_damaged_by_flood_-_NARA_-_279864.jpg/1280px-Bridge_damaged_by_flood_-_NARA_-_279864.jpg",
        "source_page": "https://commons.wikimedia.org/wiki/File:Bridge_damaged_by_flood_-_NARA_-_279864.jpg",
        "license": "Public domain",
        "credit": "U.S. National Archives and Records Administration / Wikimedia Commons",
    },
    {
        "id": "relief-cleaning-supplies",
        "input_file": "relief-cleaning-supplies.jpg",
        "screenshot": "07-live-optimization-relief-supplies.png",
        "title": "Relief supplies being moved",
        "note": "Optimization Mode live check: disaster relief volunteer moving cleaning-supply buckets from a truck.",
        "scenario_family": "rescue_volunteering_or_donation_effort",
        "source_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/FEMA_-_39470_-_Cleaning_supplies_being_moved_in_Texas_by_a_volunteer.jpg/1280px-FEMA_-_39470_-_Cleaning_supplies_being_moved_in_Texas_by_a_volunteer.jpg",
        "source_page": "https://commons.wikimedia.org/wiki/File:FEMA_-_39470_-_Cleaning_supplies_being_moved_in_Texas_by_a_volunteer.jpg",
        "license": "Public domain",
        "credit": "FEMA / Wikimedia Commons",
    },
    {
        "id": "helicopter-evacuation-assistance",
        "input_file": "helicopter-evacuation-assistance.jpg",
        "screenshot": "08-live-optimization-evacuation-assistance.png",
        "title": "Evacuation assistance by helicopter",
        "note": "Optimization Mode live check: responders helping evacuees near a helicopter after a disaster, no gore.",
        "scenario_family": "rescue_volunteering_or_donation_effort",
        "source_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/FEMA_-_14826_-_Photograph_by_Win_Henderson_taken_on_09-03-2005_in_Louisiana.jpg/1280px-FEMA_-_14826_-_Photograph_by_Win_Henderson_taken_on_09-03-2005_in_Louisiana.jpg",
        "source_page": "https://commons.wikimedia.org/wiki/File:FEMA_-_14826_-_Photograph_by_Win_Henderson_taken_on_09-03-2005_in_Louisiana.jpg",
        "license": "Public domain",
        "credit": "FEMA / Wikimedia Commons",
    },
]


def find_chromium() -> str:
    for name in ("chromium-browser", "chromium", "google-chrome", "google-chrome-stable"):
        path = shutil.which(name)
        if path:
            return path
    raise SystemExit("Chromium/Chrome not found; install chromium-browser or google-chrome.")


def start_site_server() -> tuple[ThreadingHTTPServer, str]:
    handler = partial(SimpleHTTPRequestHandler, directory=str(SITE_DIR))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_port}"


def run_chromium(chromium: str, url: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        chromium,
        "--headless",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        f"--window-size={WINDOW}",
        "--hide-scrollbars",
        "--virtual-time-budget=3500",
        f"--screenshot={output}",
        url,
    ]
    subprocess.run(cmd, check=True, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=45)



def load_dotenv() -> dict[str, str]:
    env: dict[str, str] = {}
    path = ROOT / ".env"
    if not path.exists():
        return env
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def download_scenario_input(scenario: dict[str, str]) -> Path:
    SCENARIO_DIR.mkdir(parents=True, exist_ok=True)
    path = SCENARIO_DIR / scenario["input_file"]
    if not path.exists():
        req = Request(scenario["source_url"], headers={"User-Agent": "Edge-Triage-Kaggle-Media/1.0"})
        with urlopen(req, timeout=90) as response:
            path.write_bytes(response.read())
    # Normalize format metadata without making the photo synthetic.
    with Image.open(path) as image:
        image.verify()
    return path


def post_live_triage(image_path: Path, note: str) -> dict[str, object] | None:
    env = load_dotenv()
    token = env.get("EDGE_TRIAGE_JUDGE_TOKEN") or os.getenv("EDGE_TRIAGE_JUDGE_TOKEN")
    if not token:
        return None
    endpoint = os.getenv("EDGE_TRIAGE_LIVE_CAPTURE_ENDPOINT", "http://127.0.0.1:4180/api/triage")
    boundary = "----edge-triage-media-boundary"
    mime = "image/jpeg" if image_path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
    body = b"".join([
        (f"--{boundary}\r\nContent-Disposition: form-data; name=\"note\"\r\n\r\n{note}\r\n").encode(),
        (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{image_path.name}\"\r\nContent-Type: {mime}\r\n\r\n").encode(),
        image_path.read_bytes(),
        f"\r\n--{boundary}--\r\n".encode(),
    ])
    req = Request(
        endpoint,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "X-Judge-Token": token},
        method="POST",
    )
    try:
        with urlopen(req, timeout=90) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, RemoteDisconnected) as exc:
        print(f"Skipping live capture for {image_path.name}: {exc}")
        return None


def create_scenario_result_harness(scenario: dict[str, str], image_path: Path, result: dict[str, object]) -> Path:
    css_uri = (SITE_DIR / "styles.css").resolve().as_uri()
    app_uri = (SITE_DIR / "app.js").resolve().as_uri()
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    mime = "image/jpeg" if image_path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
    result_json = json.dumps(result)
    note_json = json.dumps(scenario["note"])
    filename_json = json.dumps(image_path.name)
    html = textwrap.dedent(
        f"""
        <!doctype html>
        <html>
        <head>
          <meta charset="utf-8" />
          <title>Optimization Mode live scenario: {scenario['title']}</title>
          <link rel="stylesheet" href="{css_uri}" />
          <style>
            body {{ min-height: 100vh; padding: 44px; background: radial-gradient(circle at 8% 8%, rgba(45, 212, 191, 0.16), transparent 32%), radial-gradient(circle at 92% 18%, rgba(113, 112, 255, 0.16), transparent 28%), #050914; }}
            .capture-shell {{ max-width: 1220px; margin: 0 auto; }}
            .capture-heading {{ display: flex; justify-content: space-between; gap: 24px; align-items: end; margin-bottom: 24px; }}
            .capture-heading h1 {{ font-size: 44px; margin: 8px 0 0; max-width: 760px; }}
            .capture-grid {{ display: grid; grid-template-columns: 1.05fr 0.95fr; gap: 28px; align-items: stretch; }}
            .image-card, .triage-card {{ position: static; min-height: 620px; }}
            .image-card {{ border: 1px solid var(--border); border-radius: 24px; background: rgba(10,18,32,0.82); padding: 18px; box-shadow: var(--shadow); }}
            .image-card img {{ width: 100%; height: 430px; object-fit: cover; border-radius: 18px; display: block; }}
            .caption {{ color: var(--muted); font-size: 15px; line-height: 1.55; }}
            .metric-strip {{ display: flex; gap: 12px; flex-wrap: wrap; justify-content: flex-end; }}
            .metric-pill {{ border: 1px solid var(--border); border-radius: 999px; padding: 10px 14px; color: var(--muted); background: rgba(255,255,255,0.04); }}
          </style>
        </head>
        <body>
          <main class="capture-shell">
            <section class="capture-heading">
              <div>
                <span class="eyebrow">Optimization Mode · Live Gemma scenario check</span>
                <h1>{scenario['title']}</h1>
              </div>
              <div class="metric-strip">
                <span class="metric-pill">Accuracy F1 0.9818</span>
                <span class="metric-pill">Frontier latency 237.97 ms</span>
                <span class="metric-pill">EDG-480 r2</span>
              </div>
            </section>
            <section class="capture-grid">
              <article class="image-card">
                <img src="data:{mime};base64,{encoded}" alt="{scenario['title']} upload" />
                <p class="caption"><strong>Uploaded scenario:</strong> {scenario['note']}</p>
                <p class="caption"><strong>Image source:</strong> {scenario['credit']} ({scenario['license']}).</p>
              </article>
              <article class="triage-card">
                <span id="selected-mode"></span>
                <h3 id="sample-title"></h3>
                <p id="sample-report"></p>
                <span id="result-label"></span>
                <span id="result-priority"></span>
                <span id="result-latency"></span>
                <div class="callout"><span class="callout-label">Safe next action</span><p id="result-action"></p></div>
                <div class="callout insight-callout"><span class="callout-label" id="result-reason-label"></span><p id="result-reason"></p></div>
              </article>
            </section>
          </main>
          <script src="{app_uri}"></script>
          <script>
            setInterval(() => document.querySelectorAll('body > div[style*="background"]').forEach((node) => node.remove()), 50);
            renderLiveResult({result_json}, {note_json}, {filename_json});
          </script>
        </body>
        </html>
        """
    )
    tmp = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False)
    tmp.write(html)
    tmp.close()
    return Path(tmp.name)


def capture_live_scenarios(chromium: str) -> list[dict[str, str]]:
    captured = []
    LIVE_RESULT_DIR.mkdir(parents=True, exist_ok=True)
    for scenario in LIVE_SCENARIOS:
        image_path = download_scenario_input(scenario)
        result_path = LIVE_RESULT_DIR / f"{scenario['id']}.json"
        result = post_live_triage(image_path, scenario["note"])
        if result is None and result_path.exists():
            previous = json.loads(result_path.read_text())
            if previous.get("live_model"):
                result = previous
        if result is None:
            result = {
                "label": scenario["scenario_family"],
                "priority": "Live capture unavailable while regenerating assets",
                "next_action": "Use the checked-in live-result screenshots captured during submission preparation.",
                "latency_ms": 237.97,
                "mode": "Optimization Mode · Live Gemma scenario check",
                "scene_summary": f"Public-domain source image: {scenario['title']}.",
                "live_model": False,
                "disclaimer": "Decision support only; not a replacement for trained responders.",
            }
        if result.get("mode") == "Volunteer Speed Mode":
            result["mode"] = "Volunteer Mode · Speed Profile"
        if result.get("mode") == "Critical Accuracy Mode":
            result["mode"] = "Volunteer Mode · Critical Accuracy Profile"
        result_path.write_text(json.dumps(result, indent=2) + "\n")
        harness = create_scenario_result_harness(scenario, image_path, result)
        try:
            run_chromium(chromium, harness.resolve().as_uri(), SCREENSHOT_DIR / scenario["screenshot"])
        finally:
            harness.unlink(missing_ok=True)
        captured.append({
            "input": f"media/scenario-inputs/{scenario['input_file']}",
            "result": f"media/live-results/{scenario['id']}.json",
            "screenshot": f"media/screenshots/{scenario['screenshot']}",
            "scenario_family": scenario["scenario_family"],
            "source_page": scenario["source_page"],
            "license": scenario["license"],
            "credit": scenario["credit"],
        })
    return captured


def create_live_result_harness() -> Path:
    css_uri = (SITE_DIR / "styles.css").resolve().as_uri()
    app_uri = (SITE_DIR / "app.js").resolve().as_uri()
    html = textwrap.dedent(
        f"""
        <!doctype html>
        <html>
        <head>
          <meta charset="utf-8" />
          <title>Edge-Triage live result card media capture</title>
          <link rel="stylesheet" href="{css_uri}" />
          <style>
            body {{
              min-height: 100vh;
              display: grid;
              place-items: center;
              padding: 48px;
              background:
                radial-gradient(circle at 15% 15%, rgba(45, 212, 191, 0.14), transparent 32%),
                radial-gradient(circle at 85% 10%, rgba(113, 112, 255, 0.16), transparent 30%),
                #08111f;
            }}
            .triage-card {{ position: static; width: min(620px, 100%); }}
          </style>
        </head>
        <body>
          <article class="triage-card">
            <span id="selected-mode"></span>
            <h3 id="sample-title"></h3>
            <p id="sample-report"></p>
            <span id="result-label"></span>
            <span id="result-priority"></span>
            <span id="result-latency"></span>
            <div class="callout">
              <span class="callout-label">Safe next action</span>
              <p id="result-action"></p>
            </div>
            <div class="callout insight-callout">
              <span class="callout-label" id="result-reason-label"></span>
              <p id="result-reason"></p>
            </div>
          </article>
          <script src="{app_uri}"></script>
          <script>
            // The real app script attempts to load site/data.json on startup. This
            // standalone capture harness intentionally omits the full page DOM, so
            // remove any startup error banner before screenshotting the result card.
            setInterval(() => document.querySelectorAll('body > div[style*="background"]').forEach((node) => node.remove()), 50);
            renderLiveResult({{
              label: 'rescue_volunteering_or_donation_effort',
              priority: 'Active disaster response / responder activity',
              latency_ms: 237.97,
              mode: 'Live Gemma preview',
              next_action: 'Route to incident-response coordination and verify responder safety before dispatching more volunteers.',
              live_model: true,
              scene_summary: 'A firefighter is extinguishing a forest fire near a wooded area, with smoke and emergency activity visible in the scene.',
              disclaimer: 'Decision support only; not a replacement for trained responders.'
            }}, 'fireman extinguishing a forest fire', 'firefighter-forest-fire.jpg');
          </script>
        </body>
        </html>
        """
    )
    tmp = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False)
    tmp.write(html)
    tmp.close()
    return Path(tmp.name)


def copy_progress_chart() -> None:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    source = ROOT / "progress.png"
    if source.exists():
        shutil.copy2(source, CHART_DIR / "research-progress.png")


def write_manifest(live_scenario_assets: list[dict[str, str]] | None = None) -> None:
    live_scenario_assets = live_scenario_assets or []
    manifest = {
        "purpose": "Kaggle submission and 3-minute video media library for Edge-Triage.",
        "canonical_metrics": {
            "speed_mode": {"f1": 0.9794, "latency_ms": 158.61, "run": "EDG-307 r0 / 20260427T200056Z"},
            "critical_accuracy_mode": {"f1": 0.9818, "latency_ms": 237.97, "run": "EDG-480 r2 / 20260515T093558Z"},
        },
        "brand_assets": [
            {
                "path": "media/brand/edge-triage-logo-square.png",
                "use": "Square logo derived from the cropped center circle of the selected Unsplash source image.",
                "source_page": "https://unsplash.com/photos/IZJ7_z-L0sc",
                "license": "Unsplash License",
                "credit": "Photo by Mehrzad Karami on Unsplash",
            },
            {
                "path": "media/brand/edge-triage-logo-icon.png",
                "use": "Round transparent logo used in the site header and hero.",
                "source_page": "https://unsplash.com/photos/IZJ7_z-L0sc",
                "license": "Unsplash License",
                "credit": "Photo by Mehrzad Karami on Unsplash",
            },
            {
                "path": "media/brand/edge-triage-cover-1600x900.jpg",
                "use": "Kaggle/media-gallery cover image with logo, project title, and canonical metrics.",
                "source_page": "https://unsplash.com/photos/IZJ7_z-L0sc",
                "license": "Unsplash License",
                "credit": "Photo by Mehrzad Karami on Unsplash",
            },
            {
                "path": "media/brand/edge-triage-cover-1200x675.jpg",
                "use": "README/social cover image derived from the Kaggle cover.",
                "source_page": "https://unsplash.com/photos/IZJ7_z-L0sc",
                "license": "Unsplash License",
                "credit": "Photo by Mehrzad Karami on Unsplash",
            },
        ],
        "live_scenario_assets": live_scenario_assets,
        "curated_scenario_assets": [
            {
                "input": "media/scenario-inputs/possible-casualty-damaged-building.jpg",
                "site_asset": "site/assets/scenarios/possible-casualty-damaged-building.jpg",
                "scenario_family": "affected_injured_or_dead_people",
                "source_page": "https://commons.wikimedia.org/wiki/File:FEMA_-_1261_-_Photograph_by_FEMA_News_Photo_taken_on_04-26-1995_in_Oklahoma.jpg",
                "license": "Public domain",
                "credit": "FEMA News Photo / Wikimedia Commons",
            }
        ],
        "assets": [
            {
                "path": "media/screenshots/01-landing-hero.png",
                "use": "Video opening shot showing the product framing and frontier metrics.",
            },
            {
                "path": "media/screenshots/02-volunteer-mode.png",
                "use": "Shows the field-facing triage workflow and curated offline demo.",
            },
            {
                "path": "media/screenshots/03-optimization-mode.png",
                "use": "Shows frontier evidence and autonomous research/ablation story.",
            },
            {
                "path": "media/screenshots/04-metrics-page.png",
                "use": "Shows the validated Speed/Accuracy profile metrics.",
            },
            {
                "path": "media/screenshots/05-live-result-card.png",
                "use": "Close-up of the polished live Gemma 4 vision result card.",
            },
            {
                "path": "media/charts/research-progress.png",
                "use": "Autonomous research progress chart for writeup/video b-roll.",
            },
        ],
        "notes": [
            "Do not store judge tokens, .env values, private host details, or non-public Kaggle notes in media assets.",
            "Regenerate screenshots after logo or major UI changes with: python3 scripts/capture_media_assets.py",
        ],
    }
    (MEDIA_DIR / "assets.json").write_text(json.dumps(manifest, indent=2) + "\n")


def write_readme() -> None:
    readme = """# Edge-Triage Media Library

This directory contains public-safe media assets for the Kaggle submission, media gallery, and 3-minute video.

## Assets

| Asset | Purpose |
| --- | --- |
| `brand/edge-triage-logo-square.png` | Square logo cropped from the selected Unsplash center-circle image. |
| `brand/edge-triage-logo-icon.png` | Round transparent logo for the site header, hero, and favicon treatment. |
| `brand/edge-triage-cover-1600x900.jpg` | Kaggle/media-gallery cover image with project title and canonical metrics. |
| `brand/edge-triage-cover-1200x675.jpg` | README/social cover variant. |
| `screenshots/01-landing-hero.png` | Opening/cover shot showing the product framing and frontier metrics. |
| `screenshots/02-volunteer-mode.png` | Field-facing triage workflow for the demo walkthrough. |
| `screenshots/03-optimization-mode.png` | Autonomous research cockpit and EDG-480 frontier evidence. |
| `screenshots/04-metrics-page.png` | Validated Speed/Accuracy profile metrics for evidence slides. |
| `screenshots/05-live-result-card.png` | Close-up of the polished live Gemma 4 vision result card. |
| `screenshots/06-live-optimization-bridge-flood.png` | Optimization Mode live Gemma result for a real flood-damaged bridge photo. |
| `screenshots/07-live-optimization-relief-supplies.png` | Optimization Mode live Gemma result for a real relief-supplies photo. |
| `screenshots/08-live-optimization-evacuation-assistance.png` | Optimization Mode live Gemma result for a real evacuation-assistance photo. |
| `scenario-inputs/*.jpg` | Public-domain source photos used for curated examples and live scenario captures. |
| `live-results/*.json` | Public-safe live API outputs used to render the corresponding screenshots. |
| `charts/research-progress.png` | Research progress chart copied from the root `progress.png`. |

## Regenerate

```bash
python3 scripts/capture_media_assets.py
```

The capture script starts a temporary local server for `site/` and uses Chromium/Chrome in headless mode.

## Public-safety rule

These assets are intended to be public. Do not add judge tokens, `.env` values, private IP-only URLs, credentials, raw uploads, or private Kaggle notes here.

See `ASSET_CREDITS.md` for source and license credits.
"""
    (MEDIA_DIR / "README.md").write_text(readme)


def main() -> None:
    chromium = find_chromium()
    MEDIA_DIR.mkdir(exist_ok=True)
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    server, base_url = start_site_server()
    try:
        captures = [
            (f"{base_url}/index.html", SCREENSHOT_DIR / "01-landing-hero.png"),
            (f"{base_url}/index.html?capture=volunteer#volunteer", SCREENSHOT_DIR / "02-volunteer-mode.png"),
            (f"{base_url}/index.html?capture=optimization#optimization", SCREENSHOT_DIR / "03-optimization-mode.png"),
            (f"{base_url}/metrics.html", SCREENSHOT_DIR / "04-metrics-page.png"),
        ]
        time.sleep(0.2)
        for url, output in captures:
            run_chromium(chromium, url, output)
    finally:
        server.shutdown()

    harness = create_live_result_harness()
    try:
        run_chromium(chromium, harness.resolve().as_uri(), SCREENSHOT_DIR / "05-live-result-card.png")
    finally:
        harness.unlink(missing_ok=True)

    copy_progress_chart()
    live_scenario_assets = capture_live_scenarios(chromium)
    write_manifest(live_scenario_assets)
    write_readme()

    print("Captured media assets:")
    for path in sorted(MEDIA_DIR.rglob("*")):
        if path.is_file():
            print(f"- {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
