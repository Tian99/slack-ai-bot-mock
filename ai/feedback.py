import argparse, json, httpx

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--value", required=True, help='JSON like {"helpful": true, "trace_id": "abc"}')
    parser.add_argument("--endpoint", default="http://127.0.0.1:8080/feedback")
    args = parser.parse_args()
    data = json.loads(args.value)
    r = httpx.post(args.endpoint, json=data, timeout=10)
    print(r.status_code, r.text)
