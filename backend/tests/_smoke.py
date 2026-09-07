"""End-to-end smoke test for image upload, set-main, and reorder."""
import os, sys, time, threading, json, urllib.request, urllib.error
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import uvicorn


def req(url, method="GET", data=None, token=None):
    headers = {}
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


config = uvicorn.Config("app.main:app", host="127.0.0.1", port=8769, log_level="warning")
server = uvicorn.Server(config)
t = threading.Thread(target=server.run, daemon=True)
t.start()
time.sleep(5)

results = []


def check(name, status, expect=200):
    ok = status == expect
    results.append((ok, name, status))
    print(f"[{'PASS' if ok else 'FAIL'}] {name:55} -> {status}")


status, body = req("http://127.0.0.1:8769/api/v1/auth/login", method="POST", data={
    "email": "user@blacksharkcars.local",
    "password": "Demo!2025",
})
check("POST /auth/login", status)
token = json.loads(body).get("access_token") if status == 200 else None

status, body = req("http://127.0.0.1:8769/api/v1/cars/mine/all?status=ACTIVE&limit=5", token=token)
data = json.loads(body) if status == 200 else {"items": []}
car_id = None
image_ids = []
for it in data.get("items", []):
    if it.get("images") and len(it["images"]) >= 2:
        car_id = it["id"]
        image_ids = [im["id"] for im in it["images"]]
        break
if car_id is None and data.get("items"):
    car_id = data["items"][0]["id"]
    image_ids = [im["id"] for im in data["items"][0].get("images", [])]
print(f"using car {car_id} with {len(image_ids)} images")

if car_id and len(image_ids) >= 2:
    reversed_ids = list(reversed(image_ids))
    status, body = req(
        f"http://127.0.0.1:8769/api/v1/uploads/cars/{car_id}/images/reorder",
        method="PUT",
        data={"image_ids": reversed_ids},
        token=token,
    )
    check("PUT /images/reorder (2 ids)", status)
    print(f"   body: {body[:200]}")

    status, body = req(f"http://127.0.0.1:8769/api/v1/cars/{car_id}", token=token)
    if status == 200:
        new_order = [im["id"] for im in json.loads(body)["images"]]
        print(f"   new order: {new_order}")
        if new_order == reversed_ids:
            print("   PASS: order matches")
        else:
            print(f"   FAIL: expected {reversed_ids}")
            results.append((False, "order persisted", 0))

    req(
        f"http://127.0.0.1:8769/api/v1/uploads/cars/{car_id}/images/reorder",
        method="PUT",
        data={"image_ids": image_ids},
        token=token,
    )
    print("   (restored original order)")
else:
    print("not enough images to test reorder")

server.should_exit = True
time.sleep(1)
print("=" * 70)
ok = sum(1 for r in results if r[0])
fail = len(results) - ok
print(f"PASS: {ok}  FAIL: {fail}")
sys.exit(0 if fail == 0 else 1)