"""Step 0 smoke test: confirm the classification endpoint responds, key read from env only."""
import os
import sys

import requests

API_BASE = "http://dobolyi.com:9001/v1"
MODEL_NAME = "cyankiwi/Qwen3.6-35B-A3B-AWQ-4bit"


def main() -> int:
    api_key = os.environ.get("DOBOLYI_API_KEY")
    if not api_key:
        print("DOBOLYI_API_KEY is not set in the environment.", file=sys.stderr)
        return 1

    resp = requests.post(
        f"{API_BASE}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": MODEL_NAME,
            "messages": [
                {"role": "user", "content": "Reply with exactly one word: OK"},
            ],
            "temperature": 0,
            "max_tokens": 300,
            "chat_template_kwargs": {"enable_thinking": False},
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    reasoning = data["choices"][0]["message"].get("reasoning")
    print("Smoke test succeeded.")
    print(f"Model: {MODEL_NAME}")
    print(f"Response content: {content!r}")
    print(f"Reasoning field: {reasoning!r}")
    print(f"finish_reason: {data['choices'][0]['finish_reason']!r}")
    print(f"usage: {data['usage']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
