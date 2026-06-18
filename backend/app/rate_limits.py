"""File-backed request throttling helpers for the chat API.

The prototype stores simple daily IP and active-request counters in JSON files
under `app/runtime/`. This keeps local/deployment rate limiting lightweight and
easy to inspect without adding a database.
"""

import json
import os
import time
from pathlib import Path


# path for json files (on mounted files in deployment)
# ip_requests_path = '/mnt/data/day_ip_requests.json'
# active_request_users_path = '/mnt/data/users_request_active.json'

RUNTIME_DIR = Path(__file__).resolve().parent / "runtime"
RUNTIME_DIR.mkdir(exist_ok=True)

ip_requests_path = RUNTIME_DIR / "day_ip_requests.json"
active_request_users_path = RUNTIME_DIR / "users_request_active.json"
ACTIVE_REQUEST_TTL_SECONDS = int(os.getenv("SSA_ACTIVE_REQUEST_TTL_SECONDS", str(4 * 60)))

def _load_json(path, default):
    if not path.exists():
        path.write_text(json.dumps(default, indent=4), encoding="utf-8")

    with open(path, "r") as f:
        return json.load(f)

def _write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def _active_request_map():
    """Return active request locks as {request_key: timestamp}, pruning stale entries."""
    active_user_requests = _load_json(active_request_users_path, {"users": {}})
    raw_users = active_user_requests.get("users", {})
    now = time.time()

    if isinstance(raw_users, list):
        # Legacy lock files only stored keys, not timestamps. Treat them as stale
        # after reload so an old development lock cannot block a fresh chat.
        request_map = {}
    elif isinstance(raw_users, dict):
        request_map = {}
        for request_key, timestamp in raw_users.items():
            try:
                timestamp_value = float(timestamp)
            except (TypeError, ValueError):
                timestamp_value = now
            if now - timestamp_value <= ACTIVE_REQUEST_TTL_SECONDS:
                request_map[str(request_key)] = timestamp_value
    else:
        request_map = {}

    if request_map != raw_users:
        _write_json(active_request_users_path, {"users": request_map})

    return request_map

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

    ongoing_request_ips = _active_request_map()

    if add_or_remove.lower() == "add":

        ongoing_request_ips[ip] = time.time()

    elif add_or_remove.lower() == "remove":
        if ip in ongoing_request_ips:
            del ongoing_request_ips[ip]
    else:
        return ValueError


    _write_json(active_request_users_path, {"users": ongoing_request_ips})

def check_if_user_ongoing_request(ip):

    ongoing_request = False

    ongoing_request_ips = _active_request_map()

    if ip in ongoing_request_ips:
        ongoing_request = True

    return ongoing_request
