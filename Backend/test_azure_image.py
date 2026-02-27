"""
test_azure_image.py
───────────────────
Quick test for AZURE_IMAGE_AI_* variables in .env.
Sends a DALL-E 3 image-generation request to your Azure endpoint
and prints the resulting image URL.

Run from the Backend/ folder:
    python test_azure_image.py
"""

import json
import os
import urllib.request
import urllib.error


# ── 1. Parse .env (no external libraries needed) ──────────────────────────────

def load_env(path=".env"):
    env = {}
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                env[key.strip()] = val.strip().strip("\"'")
    except FileNotFoundError:
        print(f"[ERROR] {path} not found. Run this script from the Backend/ folder.")
    return env


# ── 2. Main test ──────────────────────────────────────────────────────────────

def test_azure_image():
    env = load_env()

    endpoint   = env.get("AZURE_IMAGE_AI_ENDPOINT_URL", "").rstrip("/")
    deployment = env.get("AZURE_IMAGE_AI_DEPLOYMENT_NAME", "")
    version    = env.get("AZURE_IMAGE_AI_APP_VERSION", "")
    token      = env.get("AZURE_IMAGE_AI_TOKEN", "")

    # Validate all variables are present
    missing = [k for k, v in {
        "AZURE_IMAGE_AI_ENDPOINT_URL":    endpoint,
        "AZURE_IMAGE_AI_DEPLOYMENT_NAME": deployment,
        "AZURE_IMAGE_AI_APP_VERSION":     version,
        "AZURE_IMAGE_AI_TOKEN":           token,
    }.items() if not v]

    if missing:
        print("[ERROR] Missing variables in .env:")
        for m in missing:
            print(f"  ✗ {m}")
        return

    # Build the Azure DALL-E generations URL
    url = f"{endpoint}/openai/deployments/{deployment}/images/generations?api-version={version}"

    headers = {
        "api-key": token,
        "Content-Type": "application/json",
    }

    payload = json.dumps({
        "prompt": "A serene mountain lake at sunrise, photorealistic",
        "n": 1,
        "size": "1024x1024",
        "quality": "standard",
        "style": "vivid"
    }).encode("utf-8")

    print("=" * 60)
    print("  Azure DALL-E 3 Image Generation — Quick Test")
    print("=" * 60)
    print(f"  Endpoint   : {endpoint}")
    print(f"  Deployment : {deployment}")
    print(f"  API Version: {version}")
    print("-" * 60)

    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))

        image_url = result["data"][0].get("url", "")
        revised   = result["data"][0].get("revised_prompt", "")

        print("\n[SUCCESS] Image generated successfully!\n")
        if revised:
            print(f"  Revised prompt : {revised}\n")
        print(f"  Image URL      : {image_url}")
        print("\n(Open the URL above in a browser to view the image)")

    except urllib.error.HTTPError as e:
        print(f"\n[ERROR] HTTP {e.code} — {e.reason}")
        try:
            body = json.loads(e.read().decode("utf-8"))
            print(json.dumps(body, indent=2))
        except Exception:
            pass
    except urllib.error.URLError as e:
        print(f"\n[ERROR] Could not reach endpoint: {e.reason}")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")


if __name__ == "__main__":
    test_azure_image()
