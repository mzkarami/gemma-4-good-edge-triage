import json
import unittest
from pathlib import Path


class SiteLiveUiTest(unittest.TestCase):
    def test_volunteer_form_separates_curated_scenarios_from_live_upload(self):
        html = Path("site/index.html").read_text()
        self.assertIn("Curated showcase", html)
        self.assertIn("Live Gemma preview", html)
        self.assertIn("prepared product examples", html)
        self.assertIn("No upload, backend request, or new model call", html)
        self.assertIn("id=\"curated-scenarios\"", html)
        self.assertIn("id=\"live-inputs\"", html)
        self.assertIn("id=\"judge-token\"", html)
        self.assertIn("id=\"judge-token-error\"", html)
        self.assertIn("aria-describedby=\"judge-token-help judge-token-error\"", html)
        self.assertNotIn("Live API endpoint", html)
        self.assertNotIn("id=\"api-endpoint\"", html)
        self.assertIn("25 MB", html)

    def test_app_js_calls_live_api_with_judge_token_and_friendly_errors(self):
        js = Path("site/app.js").read_text()
        self.assertIn("runLiveInference", js)
        self.assertIn("X-Judge-Token", js)
        self.assertIn("FormData", js)
        self.assertIn("Image must be 25 MB or smaller", js)
        self.assertIn("Live model unavailable", js)
        self.assertIn("curated showcase is still usable", js)
        self.assertIn("setTokenError", js)
        self.assertIn("$('#judge-token')?.focus()", js)
        self.assertNotIn("runStaticSimulation", js)
        self.assertNotIn("classifyStaticDemo", js)

    def test_missing_judge_token_error_is_field_scoped(self):
        html = Path("site/index.html").read_text()
        css = Path("site/styles.css").read_text()
        js = Path("site/app.js").read_text()

        self.assertIn('id="judge-token-error" class="field-error"', html)
        self.assertIn('role="alert" aria-live="polite" hidden', html)
        self.assertIn(".field-error", css)
        self.assertIn("tokenInput?.setAttribute('aria-invalid'", js)
        self.assertIn("setTokenError('Use the judge token from the Kaggle submission notes.')", js)
        self.assertNotIn("setSimulationStatus('Use the judge token from the Kaggle submission notes.', 'error')", js)

    def test_volunteer_field_console_page_is_real_app_experience(self):
        index = Path("site/index.html").read_text()
        app = Path("site/app.html").read_text()
        css = Path("site/styles.css").read_text()
        js = Path("site/app.js").read_text()

        self.assertIn('href="app.html"', index)
        self.assertIn("Open Volunteer App", index)
        self.assertGreater(index.index('href="app.html"'), index.index('href="about.html"'))
        self.assertIn("Volunteer Field Console", app)
        self.assertIn("Use it like a field volunteer", app)
        self.assertIn('id="field-report"', app)
        self.assertIn('id="field-image"', app)
        self.assertIn('accept="image/*"', app)
        self.assertIn('capture="environment"', app)
        self.assertIn('id="field-audio"', app)
        self.assertIn('accept="audio/*"', app)
        self.assertIn('id="field-image-preview"', app)
        self.assertIn('id="phone-image-preview"', app)
        self.assertIn('id="send-coordinator"', app)
        self.assertIn('id="live-gemma-link"', app)
        self.assertIn("Draft saved locally", app)
        self.assertIn("Ready for coordinator handoff", app)
        self.assertIn("decision support, not emergency command", app.lower())
        self.assertIn("Run Edge-Triage", app)
        self.assertIn('id="app-result-card"', app)
        self.assertIn("This report looks like", app)
        self.assertIn(".field-console", css)
        self.assertIn(".phone-shell", css)
        self.assertIn(".field-image-preview", css)
        self.assertIn("initVolunteerConsole", js)
        self.assertIn("URL.createObjectURL", js)
        self.assertIn("field-image-preview", js)
        self.assertIn("send-coordinator", js)
        self.assertIn("localStorage.setItem('edge-triage-field-draft'", js)
        self.assertIn("Ready for coordinator handoff", js)
        self.assertNotIn("Queued for coordinator sync. Human review required before action.", js)

    def test_brand_assets_are_wired_for_site_and_submission(self):
        html = Path("site/index.html").read_text()
        self.assertIn("assets/brand/edge-triage-logo-icon.png", html)
        self.assertIn("assets/brand/edge-triage-cover-1600x900.jpg", html)
        self.assertIn("assets/brand/favicon.png", html)

        expected_assets = [
            Path("site/assets/brand/edge-triage-logo-icon.png"),
            Path("site/assets/brand/edge-triage-logo-square.png"),
            Path("site/assets/brand/edge-triage-cover-1600x900.jpg"),
            Path("site/assets/brand/favicon.png"),
            Path("media/brand/edge-triage-cover-1200x675.jpg"),
        ]
        for asset in expected_assets:
            with self.subTest(asset=str(asset)):
                self.assertTrue(asset.exists(), f"Missing brand asset: {asset}")
                self.assertGreater(asset.stat().st_size, 10_000, f"Brand asset looks empty: {asset}")

    def test_hero_explains_product_before_metrics(self):
        html = Path("site/index.html").read_text()
        css = Path("site/styles.css").read_text()

        self.assertIn("font-size: clamp(2.6rem, 7vw, 4.2rem);", css)
        self.assertNotIn("5.4rem", css)
        self.assertIn("volunteers receive messy text reports and photos", html)
        self.assertIn("triage label, priority, and conservative next action", html)
        self.assertIn("keeping humans in control", html)
        self.assertIn("Messy field report", html)
        self.assertIn("Gemma 4 local triage", html)
        self.assertIn("Priority + safe next action", html)
        hero_html = html.split('<section class="section-shell judge-guide"', 1)[0]
        self.assertNotIn("Try Volunteer Mode", hero_html)
        self.assertNotIn("View Optimization Mode", hero_html)
        self.assertNotIn("hero-actions", hero_html)
        self.assertNotIn("static demo", html.lower())
        self.assertNotIn("curated offline demo", html.lower())
        self.assertIn(".hero-flow", css)

    def test_optimization_mode_explains_edg_cards_for_nontechnical_judges(self):
        html = Path("site/index.html").read_text()
        css = Path("site/styles.css").read_text()

        self.assertIn("self-learning loop behind the submitted profiles", html)
        self.assertIn("Gemma 4 helps propose and evaluate a candidate triage profile", html)
        self.assertIn("AutoResearch-inspired harness measures F1, latency", html)
        self.assertIn("New crisis examples", html)
        self.assertIn("Gemma 4 candidate profile", html)
        self.assertIn("Measured keep/discard decision", html)
        self.assertIn("Gold-set evaluation", html)
        self.assertIn("F1 + latency + safety check", html)
        self.assertIn("Keep or discard", html)
        self.assertIn(".loop-steps", css)
        self.assertIn(".research-loop", css)
        self.assertIn("How to read the EDG cards", html)
        self.assertIn("Each card is a model improvement trial", html)
        self.assertIn("Think of an EDG card as a lab note", html)
        self.assertIn("fast enough for volunteers", html)
        self.assertIn("4-second field budget", html)
        self.assertIn(".experiment-intro", css)

        data = json.loads(Path("site/data.json").read_text())
        labels = json.dumps(data["experiments"])
        self.assertIn("Best high-accuracy profile", labels)
        self.assertIn("Partial fix, not safe alone", labels)
        self.assertIn("What changed", Path("site/app.js").read_text())
        self.assertIn("Technical note", Path("site/app.js").read_text())

    def test_judge_guide_and_trust_notes_help_different_reviewers(self):
        html = Path("site/index.html").read_text()
        css = Path("site/styles.css").read_text()

        self.assertIn("Choose the lens you care about", html)
        self.assertIn("Field responder", html)
        self.assertIn("ML evaluator", html)
        self.assertIn("Agents / AutoResearch", html)
        self.assertIn("Safety / Gemma 4", html)
        self.assertIn("Curated demo: fixed public-safe scenarios", html)
        self.assertIn("Live preview: real token-gated Gemma API", html)
        self.assertIn("Metrics: full-50 run-backed frontier", html)
        self.assertIn(".judge-grid", css)
        self.assertIn(".trust-strip", css)

    def test_competition_track_fit_section_is_specific_and_honest(self):
        html = Path("site/index.html").read_text()
        css = Path("site/styles.css").read_text()

        self.assertIn("Competition track fit", html)
        self.assertIn("Where Edge-Triage fits the Gemma 4 Good tracks", html)
        self.assertIn("working disaster-response product", html)
        self.assertIn("local Gemma stack", html)
        self.assertNotIn("deployed paths are separated from scaffolds", html)
        self.assertIn("Main Track", html)
        self.assertIn("Impact Track", html)
        self.assertIn("Global Resilience + Safety &amp; Trust", html)
        self.assertIn("Special Technology Track", html)
        self.assertIn("llama.cpp, LiteRT, Ollama, and Unsloth evidence", html)
        self.assertIn("core GGUF multimodal inference via <code>llama-cpp-python</code>", html)
        self.assertIn("Google AI Edge / <code>.litertlm</code> download and backend scaffolding", html)
        self.assertIn("checked-in <code>Modelfile</code>", html)
        self.assertIn("GGUF model source and fallback download path", html)
        self.assertLess(html.index("Choose the lens you care about"), html.index("Where Edge-Triage fits the Gemma 4 Good tracks"))
        self.assertLess(html.index("Where Edge-Triage fits the Gemma 4 Good tracks"), html.index("Switch between the two judge experiences"))
        self.assertIn(".track-grid", css)
        self.assertIn(".track-list", css)
        self.assertIn(".live-inputs .file-drop", css)
        self.assertIn("rgba(255, 255, 255, 0.72)", css)

    def test_evidence_section_tells_judge_friendly_proof_story(self):
        html = Path("site/index.html").read_text()
        css = Path("site/styles.css").read_text()

        self.assertIn("Why this matters in a real disaster response", html)
        self.assertIn("reports arrive fast, connectivity is uncertain", html)
        self.assertIn("Local Gemma 4", html)
        self.assertIn("Text and photos can stay near the incident", html)
        self.assertIn("GGUF/llama.cpp-style edge packaging", html)
        self.assertIn("The app routes; responders decide", html)
        self.assertIn("Public claims trace back to runs", html)
        self.assertIn("Known limits", html)
        self.assertIn("Honest fallback, human review required", html)
        self.assertIn("no medical or incident-command authority is delegated", html)
        self.assertIn("results.tsv", html)
        self.assertIn("docs/CURRENT_FRONTIER.md", html)
        self.assertIn(".evidence-heading-copy", css)
        self.assertIn(".limitation-card", css)

    def test_metrics_page_explains_numbers_and_ledger_filtering(self):
        html = Path("site/metrics.html").read_text()

        self.assertIn("What these numbers mean", html)
        self.assertIn("Two profiles, two response needs", html)
        self.assertIn("same 50-sample MEDIC/QCRI gold set", html)
        self.assertIn("Why not just show the raw maximum", html)
        self.assertIn("experiment ledger, not a leaderboard", html)
        self.assertIn("guarded CPU runs", html)
        self.assertIn("trustworthy comparable full-50 rows", html)

    def test_roadmap_and_about_pages_are_linked_and_judge_friendly(self):
        index = Path("site/index.html").read_text()
        roadmap = Path("site/roadmap.html").read_text()
        about = Path("site/about.html").read_text()
        css = Path("site/styles.css").read_text()

        self.assertIn('href="roadmap.html"', index)
        self.assertIn('href="about.html"', index)
        self.assertIn('href="about.html">Why it matters</a>', index)
        self.assertIn("Open why it matters", index)
        self.assertNotIn('href="about.html">About</a>', index)
        self.assertIn("native mobile apps", index)
        self.assertIn("Personal challenge, practical roadmap", index)
        self.assertIn("This challenge is also personal", index)
        self.assertIn("being a refugee from a young age", index)
        self.assertIn("spending eight years in a war-area context", index)
        self.assertIn("running an NGO that helps other NGOs use AI responsibly", index)
        self.assertIn("pro-bono Data/AI work with NGOs", index)
        self.assertLess(index.index("Why this matters in a real disaster response"), index.index("This challenge is also personal"))
        self.assertIn(".next-pages-grid", css)
        self.assertIn(".personal-context-heading", css)
        self.assertIn("What Edge-Triage could become next", roadmap)
        self.assertIn("Android and iOS interfaces", roadmap)
        self.assertIn("UN, WHO, IFRC/Red Cross", roadmap)
        self.assertIn("Multilingual, voice, and SMS-friendly workflows", roadmap)
        self.assertIn("NGO deployment kit", roadmap)
        self.assertIn("Why humanitarian AI feels personal", about)
        self.assertIn("displacement from a very young age", about)
        self.assertIn("years close to war-area realities", about)
        self.assertIn("Data and AI work with an NGO", about)
        self.assertIn("Gemma 4 is useful", about)
        self.assertNotIn("Mehrzad", about)
        self.assertIn(".roadmap-grid", css)
        self.assertIn(".story-card", css)

    def test_notebook_section_explains_reproducibility_paths(self):
        html = Path("site/index.html").read_text()
        css = Path("site/styles.css").read_text()

        self.assertIn('href="#notebooks"', html)
        self.assertIn("Three ways judges can go deeper", html)
        self.assertIn("Full codebase", html)
        self.assertIn("submission_notebook.ipynb", html)
        self.assertIn("Gemma 4 inference walkthrough", html)
        self.assertIn("analysis.ipynb", html)
        self.assertIn("Research ledger explorer", html)
        self.assertIn("Google Colab", html)
        self.assertIn("results.tsv", html)
        self.assertIn("docs/CURRENT_FRONTIER.md", html)
        self.assertIn(".notebook-grid", css)
        self.assertTrue(Path("submission_notebook.ipynb").exists())
        self.assertTrue(Path("analysis.ipynb").exists())

    def test_curated_samples_can_render_public_scenario_images(self):
        data = json.loads(Path("site/data.json").read_text())
        js = Path("site/app.js").read_text()
        for sample in data["samples"]:
            with self.subTest(sample=sample["id"]):
                self.assertIn("imageSrc", sample)
                self.assertIn("imageAlt", sample)
                self.assertTrue(Path("site", sample["imageSrc"]).exists())
        self.assertIn("assets/scenarios/bridge-flood-damage.jpg", json.dumps(data))
        self.assertIn("assets/scenarios/possible-casualty-damaged-building.jpg", json.dumps(data))
        self.assertIn("assets/scenarios/relief-cleaning-supplies.jpg", json.dumps(data))
        self.assertIn("assets/scenarios/helicopter-evacuation-assistance.jpg", json.dumps(data))
        self.assertIn("renderScenarioImage", js)
        self.assertIn("sample.imageSrc", js)

    def test_live_scene_summary_uses_polished_callout_not_raw_muted_text(self):
        html = Path("site/index.html").read_text()
        css = Path("site/styles.css").read_text()
        js = Path("site/app.js").read_text()

        self.assertIn('class="callout insight-callout"', html)
        self.assertIn('id="result-reason-label"', html)
        self.assertIn('id="result-reason">Select a report to see what the model understood', html)
        self.assertNotIn('id="result-reason" class="muted small"', html)
        self.assertIn(".insight-callout", css)
        self.assertIn("border-color: rgba(113,112,255,0.24)", css)
        self.assertIn("$('#result-reason-label').textContent = source", js)
        self.assertNotIn("`${source}: ${summary}", js)


if __name__ == "__main__":
    unittest.main()
