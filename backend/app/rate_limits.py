import json
from pathlib import Path


# path for json files (on mounted files in deployment)
# ip_requests_path = '/mnt/data/day_ip_requests.json'
# active_request_users_path = '/mnt/data/users_request_active.json'

RUNTIME_DIR = Path(__file__).resolve().parent / "runtime"
RUNTIME_DIR.mkdir(exist_ok=True)

ip_requests_path = RUNTIME_DIR / "day_ip_requests.json"
active_request_users_path = RUNTIME_DIR / "users_request_active.json"

def _load_json(path, default):
    if not path.exists():
        path.write_text(json.dumps(default, indent=4), encoding="utf-8")

    with open(path, "r") as f:
        return json.load(f)

def _write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def reset_ip_request_limits():
    _write_json(ip_requests_path, {})

def check_if_ip_limited(ip):

    # disregard development calls
    if ip == 'dev-ip':
        return False

    # limit for requests / day
    daily_request_limit = 25

    ip_limited = False

    ip_requests = _load_json(ip_requests_path, {})

    if ip in ip_requests:
        if ip_requests[ip] == daily_request_limit:
            ip_limited = True
        else:
            ip_requests[ip] += 1

    else:
        ip_requests[ip] = 1

    _write_json(ip_requests_path, ip_requests)

    return ip_limited

# functions to add user/ip to a list that stops a request being processed if they already have one in action, this is because the code that exists which stops a user sending a message when waiting for the response is client side, thus can be bypassed with changing client side code. this means that regardless, calls cannot be spammed
def add_or_remove_user_requestlist(add_or_remove, ip):

    active_user_requests_ips = _load_json(active_request_users_path, {"users": []})

    ongoing_request_ips = active_user_requests_ips["users"]

    if add_or_remove.lower() == "add":

        ongoing_request_ips.append(ip)

    elif add_or_remove.lower() == "remove":
        if ip in ongoing_request_ips:
            ongoing_request_ips.remove(ip)
    else:
        return ValueError


    _write_json(active_request_users_path, {"users": ongoing_request_ips})

def check_if_user_ongoing_request(ip):

    ongoing_request = False

    active_user_requests_ips = _load_json(active_request_users_path, {"users": []})

    ongoing_request_ips = active_user_requests_ips["users"]

    if ip in ongoing_request_ips:
        ongoing_request = True

    return ongoing_request
