import json
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class SiteBrowserSmokeTest(unittest.TestCase):
    def test_live_scene_summary_renders_as_matching_callout_in_chromium(self):
        chromium = shutil.which("chromium-browser") or shutil.which("chromium") or shutil.which("google-chrome")
        if not chromium:
            self.skipTest("Chromium is not installed")

        css_uri = Path("site/styles.css").resolve().as_uri()
        app_uri = Path("site/app.js").resolve().as_uri()
        html = textwrap.dedent(
            f"""
            <!doctype html>
            <html>
            <head>
              <meta charset="utf-8" />
              <link rel="stylesheet" href="{css_uri}" />
              <style>body {{ padding: 24px; }} .triage-card {{ position: static; max-width: 560px; }}</style>
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
              <pre id="browser-smoke-result"></pre>
              <script src="{app_uri}"></script>
              <script>
                renderLiveResult({{
                  label: 'rescue_volunteering_or_donation_effort',
                  priority: 'Active disaster response / responder activity',
                  latency_ms: 14820,
                  mode: 'Volunteer Mode · Speed Profile',
                  next_action: 'Route to incident-response coordination.',
                  live_model: true,
                  scene_summary: 'A firefighter is extinguishing a forest fire near a wooded area.',
                  disclaimer: 'Decision support only; not a replacement for trained responders.'
                }}, 'fireman extinguishing a forest fire', 'firefighter-forest-fire.jpg');
                const action = document.querySelector('#result-action').closest('.callout');
                const insight = document.querySelector('#result-reason').closest('.callout');
                const actionStyle = getComputedStyle(action);
                const insightStyle = getComputedStyle(insight);
                document.querySelector('#browser-smoke-result').textContent = JSON.stringify({{
                  actionRadius: actionStyle.borderRadius,
                  insightRadius: insightStyle.borderRadius,
                  actionPadding: actionStyle.padding,
                  insightPadding: insightStyle.padding,
                  insightLabel: document.querySelector('#result-reason-label').textContent,
                  insightText: document.querySelector('#result-reason').textContent,
                  insightBorder: insightStyle.borderColor,
                  actionBorder: actionStyle.borderColor
                }});
              </script>
            </body>
            </html>
            """
        )
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as tmp:
            tmp.write(html)
            tmp_path = Path(tmp.name)
        try:
            completed = subprocess.run(
                [
                    chromium,
                    "--headless",
                    "--no-sandbox",
                    "--disable-gpu",
                    "--dump-dom",
                    tmp_path.as_uri(),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
            )
        finally:
            tmp_path.unlink(missing_ok=True)

        marker = '<pre id="browser-smoke-result">'
        self.assertIn(marker, completed.stdout)
        rendered_json = completed.stdout.split(marker, 1)[1].split("</pre>", 1)[0]
        rendered = json.loads(rendered_json)

        self.assertEqual(rendered["insightLabel"], "Live Gemma 4 vision")
        self.assertIn("firefighter", rendered["insightText"])
        self.assertEqual(rendered["insightRadius"], rendered["actionRadius"])
        self.assertEqual(rendered["insightPadding"], rendered["actionPadding"])
        self.assertNotEqual(rendered["insightBorder"], "rgba(0, 0, 0, 0)")


if __name__ == "__main__":
    unittest.main()
