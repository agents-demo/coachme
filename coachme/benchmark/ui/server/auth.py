from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from contextvars import ContextVar
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from coachme.benchmark.core.data.paths import BenchmarkError, atomic_write_json, read_json

ROLES = {"admin", "operator", "labeler", "rater", "adjudicator"}
COOKIE = "coachme_benchmark_session"
TOKEN_TTL_HOURS = 12

_REQUEST_ROOT: ContextVar[Path | None] = ContextVar("benchmark_request_root", default=None)
_REQUEST_USER: ContextVar[dict[str, Any] | None] = ContextVar("benchmark_request_user", default=None)


def enabled() -> bool:
    return os.getenv("COACHME_BENCHMARK_AUTH", "false").strip().lower() in {"1", "true", "yes", "on"}


def secure_cookie() -> bool:
    return os.getenv("COACHME_BENCHMARK_COOKIE_SECURE", "false").strip().lower() in {"1", "true", "yes", "on"}


def auth_dir(base: Path) -> Path:
    raw = os.getenv("COACHME_BENCHMARK_AUTH_DIR", "").strip()
    return Path(raw).expanduser().resolve() if raw else (base / ".auth")


def tenants_root(base: Path) -> Path:
    raw = os.getenv("COACHME_BENCHMARK_TENANTS_ROOT", "").strip()
    return Path(raw).expanduser().resolve() if raw else (base / "tenants")


def tenant_root(base: Path, tenant: str) -> Path:
    name = (tenant or "default").strip()
    if not name or "/" in name or "\\" in name or name in {".", ".."}:
        raise BenchmarkError("invalid tenant")
    path = tenants_root(base) / name
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def current_root() -> Path:
    root = _REQUEST_ROOT.get()
    if root is None:
        raise RuntimeError("benchmark request context is not initialized")
    return root


def current_user() -> dict[str, Any] | None:
    return _REQUEST_USER.get()


def set_context(root: Path, user: dict[str, Any] | None) -> Any:
    first = _REQUEST_ROOT.set(root)
    _REQUEST_USER.set(user)
    return first


def reset_context(token: Any) -> None:
    _REQUEST_ROOT.reset(token)
    _REQUEST_USER.set(None)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _secret(base: Path) -> bytes:
    raw = os.getenv("COACHME_BENCHMARK_SESSION_SECRET", "").strip()
    if raw:
        return raw.encode("utf-8")
    path = auth_dir(base) / ".session_secret"
    if path.is_file():
        return path.read_bytes()
    path.parent.mkdir(parents=True, exist_ok=True)
    value = secrets.token_bytes(32)
    path.write_bytes(value)
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return value


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    if not password:
        raise BenchmarkError("password is required")
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260_000)
    return f"pbkdf2_sha256$260000${_b64(salt)}${_b64(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), _unb64(salt), int(iterations))
        return hmac.compare_digest(_b64(digest), expected)
    except (ValueError, TypeError):
        return False


class UserStore:
    def __init__(self, base: Path) -> None:
        self.path = auth_dir(base) / "users.json"

    def load(self) -> dict[str, dict[str, Any]]:
        data = read_json(self.path, {})
        return data if isinstance(data, dict) else {}

    def save(self, users: dict[str, dict[str, Any]]) -> None:
        atomic_write_json(self.path, users)
        try:
            self.path.chmod(0o600)
        except OSError:
            pass

    def add(
        self,
        username: str,
        password: str,
        *,
        role: str = "operator",
        tenant: str = "default",
        display_name: str = "",
    ) -> dict[str, Any]:
        name = username.strip()
        if not name or any(ch in name for ch in "/\\") or name in {".", ".."}:
            raise BenchmarkError("invalid username")
        if role not in ROLES:
            raise BenchmarkError(f"role must be one of: {', '.join(sorted(ROLES))}")
        users = self.load()
        if name in users:
            raise BenchmarkError(f"user already exists: {name}")
        users[name] = {
            "username": name,
            "display_name": display_name.strip() or name,
            "role": role,
            "tenant": (tenant or "default").strip(),
            "password": hash_password(password),
            "created_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        }
        self.save(users)
        return {key: users[name][key] for key in ("username", "display_name", "role", "tenant")}

    def authenticate(self, username: str, password: str) -> dict[str, Any] | None:
        record = self.load().get(username.strip())
        if not record or not verify_password(password, str(record.get("password", ""))):
            return None
        return {key: record.get(key) for key in ("username", "display_name", "role", "tenant")}

    def list(self) -> list[dict[str, Any]]:
        return [
            {key: record.get(key) for key in ("username", "display_name", "role", "tenant")}
            for record in sorted(self.load().values(), key=lambda item: str(item.get("username")))
        ]

    def remove(self, username: str) -> bool:
        users = self.load()
        if username not in users:
            return False
        users.pop(username)
        self.save(users)
        return True


def bootstrap_admin(base: Path) -> dict[str, Any] | None:
    password = os.getenv("COACHME_BENCHMARK_ADMIN_PASSWORD", "").strip()
    if not password:
        return None
    store = UserStore(base)
    if store.load():
        return None
    role = os.getenv("COACHME_BENCHMARK_ADMIN_ROLE", "admin").strip() or "admin"
    tenant = os.getenv("COACHME_BENCHMARK_ADMIN_TENANT", "default").strip() or "default"
    name = os.getenv("COACHME_BENCHMARK_ADMIN_USER", "admin").strip() or "admin"
    return store.add(name, password, role=role, tenant=tenant, display_name="Administrator")


def issue_token(base: Path, user: dict[str, Any]) -> str:
    payload = {
        "sub": user["username"],
        "role": user["role"],
        "tenant": user.get("tenant") or "default",
        "exp": int((datetime.now(UTC) + timedelta(hours=TOKEN_TTL_HOURS)).timestamp()),
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    signature = hmac.new(_secret(base), raw, hashlib.sha256).digest()
    return f"{_b64(raw)}.{_b64(signature)}"


def read_token(base: Path, token: str | None) -> dict[str, Any] | None:
    if not token or "." not in token:
        return None
    try:
        encoded, signature = token.rsplit(".", 1)
        raw = _unb64(encoded)
        expected = _b64(hmac.new(_secret(base), raw, hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        payload = json.loads(raw)
        if int(payload.get("exp", 0)) < int(datetime.now(UTC).timestamp()):
            return None
        user = UserStore(base).load().get(str(payload.get("sub")))
        if not user:
            return None
        return {
            "username": user["username"],
            "display_name": user.get("display_name") or user["username"],
            "role": user.get("role", "operator"),
            "tenant": user.get("tenant") or "default",
        }
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def allowed(role: str, method: str, path: str) -> bool:
    if role in {"admin", "operator"}:
        return True
    if path in {"/api/auth/me", "/api/auth/logout"}:
        return True
    if role == "labeler":
        if path in {"/api/runs"} or path.startswith("/api/runs/") and "/labels" in path:
            return True
        if path.startswith("/api/labels"):
            return True
        if method == "GET" and ("/clips" in path or "/media/" in path):
            return True
        return False
    if role == "rater":
        return any(part in path for part in ("/rate", "/blind/", "/ratings/", "/media/")) or path in {
            "/api/runs",
            "/api/auth/me",
        }
    if role == "adjudicator":
        return (
            "/adjudication" in path
            or "/reviews" in path
            or (method == "GET" and ("/clips" in path or "/media/" in path or "/labels" in path))
            or path in {"/api/runs"}
        )
    return False


def cookie_options() -> dict[str, Any]:
    return {
        "key": COOKIE,
        "httponly": True,
        "samesite": "lax",
        "secure": secure_cookie(),
        "max_age": TOKEN_TTL_HOURS * 3600,
    }


__all__ = [
    "COOKIE",
    "ROLES",
    "UserStore",
    "allowed",
    "auth_dir",
    "bootstrap_admin",
    "cookie_options",
    "current_root",
    "current_user",
    "enabled",
    "hash_password",
    "issue_token",
    "read_token",
    "reset_context",
    "secure_cookie",
    "set_context",
    "tenant_root",
    "tenants_root",
    "verify_password",
]
