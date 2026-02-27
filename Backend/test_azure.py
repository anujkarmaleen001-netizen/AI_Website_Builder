import json
import urllib.request
import urllib.error

def test_azure_openai():
    # 1. Parse .env file manually to avoid needing external libraries like python-dotenv
    env_vars = {}
    try:
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    env_vars[key] = val.strip("\"'")
    except FileNotFoundError:
        print("[ERROR] .env file not found.")
        return

    # 2. Extract the required variables
    endpoint = env_vars.get("AZURE_AI_ENDPOINT_URL", "").rstrip("/")
    deployment = env_vars.get("AZURE_AI_DEPLOYMENT_NAME", "")
    api_version = env_vars.get("AZURE_AI_APP_VERSION", "")
    token = env_vars.get("AZURE_AI_TOKEN", "")

    if not all([endpoint, deployment, api_version, token]):
        print("[ERROR] Missing one or more Azure variables in .env.")
        print(f"Endpoint: {'OK' if endpoint else 'MISSING'}")
        print(f"Deployment: {'OK' if deployment else 'MISSING'}")
        print(f"API Version: {'OK' if api_version else 'MISSING'}")
        print(f"Token: {'OK' if token else 'MISSING'}")
        return

    # 3. Construct the exact Azure OpenAI URL
    url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"

    headers = {
        "api-key": token,
        "Content-Type": "application/json"
    }

    payload = json.dumps({
        "messages": [{"role": "user", "content": "Hello! Please reply 'Active' if you receive this.Write a short joke around 60 token for me"}],
        "max_tokens": 10000
    }).encode("utf-8")

    print(f"Testing Azure OpenAI Endpoint...")
    print(f"URL: {url}")
    print(f"Model Deployment: {deployment}")
    print("-" * 50)

    # 4. Make the HTTP POST Request
    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            print("\n[SUCCESS] Token, endpoint, and model deployment are active and working.")
            print(f"Model Reply: {result['choices'][0]['message']['content']}")
            
    except urllib.error.HTTPError as e:
        print(f"\n[ERROR] HTTP Failed! Status Code: {e.code}")
        try:
            error_body = json.loads(e.read().decode("utf-8"))
            print(f"Error Details: {json.dumps(error_body, indent=2)}")
        except:
            print(f"Error Details: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"\n[ERROR] Request Error: {e}")

if __name__ == "__main__":
    test_azure_openai()
