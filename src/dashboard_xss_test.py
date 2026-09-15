"""Step 3 Red Team XSS test: run an adversarial review-like string through the actual
dashboard rendering pipeline (generate_dashboard.render_dashboard) and confirm it can only
ever display as inert text, never execute as markup.

Writes a standalone test HTML file for manual/browser inspection; this script itself
statically confirms the raw payload is escaped in the generated HTML output.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from generate_dashboard import render_dashboard

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "dashboard_xss_test.html")

ADVERSARIAL_TITLE = '<script>window.__xss_fired = true;</script>'
ADVERSARIAL_TEXT = (
    '"><img src=x onerror=window.__xss_fired=true>'
    "raw quote \" and angle brackets < > and </script> tag-close attempt "
    "<svg onload=window.__xss_fired=true>"
)

ADVERSARIAL_RECORD = {
    "review_id": 999999,
    "title": ADVERSARIAL_TITLE,
    "text": ADVERSARIAL_TEXT,
    "rating": 1.0,
    "answer_key_status": "ok",
    "answer_key_label": "NEGATIVE",
    "answer_key_error": None,
    "raw_model_response": '{"label": "NEGATIVE"}',
    "parsed_status": "ok",
    "parsed_label": "NEGATIVE",
    "parsed_error": None,
    "match": True,
}


def main():
    # Baseline: how many legitimate closing </script> tags the template has with no
    # adversarial content at all. Computed dynamically (not hardcoded) so this test stays
    # correct as the template gains or loses <script> blocks over time.
    baseline_html = render_dashboard([])
    n_baseline_script_tags = baseline_html.count("</script>")

    html = render_dashboard([ADVERSARIAL_RECORD])

    # Static check 1: the raw, unescaped <script> tag from the adversarial title must
    # never appear verbatim in the generated HTML.
    assert "<script>window.__xss_fired" not in html, (
        "FAIL: raw <script> tag from review title appears unescaped in generated HTML"
    )

    # Static check 2: adding the adversarial record must not change the count of closing
    # </script> tags at all. If the adversarial text's embedded "</script>" string leaked
    # through unescaped, it would add an extra one and also break a legitimate data block
    # apart from where it belongs.
    n_closing_script_tags = html.count("</script>")
    assert n_closing_script_tags == n_baseline_script_tags, (
        f"FAIL: expected {n_baseline_script_tags} closing </script> tags (the template's "
        f"own baseline with no adversarial content), found {n_closing_script_tags}, the "
        "adversarial text's embedded '</script>' string likely leaked through unescaped"
    )

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print("Static check passed: raw adversarial <script> tag does not appear unescaped in HTML.")
    print(f"Test dashboard written to {OUTPUT_PATH} for browser confirmation.")
    print("Next: load this file in a browser, confirm no alert/script executes, and confirm")
    print("the title/text render as visible literal text in the table.")


if __name__ == "__main__":
    main()
