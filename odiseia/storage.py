import json
import unicodedata
from copy import deepcopy
from pathlib import Path

from odiseia.engine import DEFAULT_PROFILE


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_FILE = DATA_DIR / "state.json"


def _default_pharmacy():
    return {
        "medications": [],
        "taken_log": [],
        "appointments": [],
        "last_weight_kg": None,
        "dose_note": "La dosis la define un profesional de salud; no se calcula automaticamente.",
    }


def _default_privacy():
    return {
        "consent_data_processing": False,
        "share_with_platform": False,
        "allow_anon_analytics": False,
        "consent_updated_at": None,
    }


def _default_profile_copy(name=None):
    profile = deepcopy(DEFAULT_PROFILE)
    if name:
        profile["name"] = str(name)[:80]
    return profile


def _default_user_state(name=None):
    return {"profile": _default_profile_copy(name), "sessions": []}


def _repair_mojibake(value):
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        repaired = text.encode("latin1").decode("utf-8")
        if repaired:
            return repaired
    except Exception:
        pass
    return text


def _normalize_preference(value):
    text = _repair_mojibake(value)
    text = " ".join(text.split())
    if not text:
        return ""
    normalized = unicodedata.normalize("NFD", text.lower())
    key = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    key = key.replace("¡", "").replace("¿", "")
    if key in {"musica", "masica"}:
        return "música"
    if key == "futbol":
        return "fútbol"
    return text


def _ensure_profile_shape(profile):
    changed = False

    def ensure_default(key, value):
        nonlocal changed
        if key not in profile:
            profile[key] = value
            changed = True

    ensure_default("name", DEFAULT_PROFILE["name"])
    ensure_default("preferences", deepcopy(DEFAULT_PROFILE["preferences"]))
    ensure_default("energy_preference", DEFAULT_PROFILE["energy_preference"])
    ensure_default("domain_levels", deepcopy(DEFAULT_PROFILE["domain_levels"]))
    ensure_default("last_domain", DEFAULT_PROFILE["last_domain"])
    ensure_default("game_levels", deepcopy(DEFAULT_PROFILE["game_levels"]))
    ensure_default("game_adaptation", deepcopy(DEFAULT_PROFILE["game_adaptation"]))
    ensure_default("last_game", DEFAULT_PROFILE["last_game"])
    ensure_default("ui_params", deepcopy(DEFAULT_PROFILE["ui_params"]))
    ensure_default("chat_history", [])
    ensure_default("pharmacy", _default_pharmacy())
    ensure_default("privacy", _default_privacy())
    ensure_default("important_data", {"weight_kg": None, "birth_year": None, "notes": ""})
    ensure_default("quedadas", [])
    ensure_default("joined_quedadas", [])

    if not isinstance(profile.get("chat_history"), list):
        profile["chat_history"] = []
        changed = True

    preferences = profile.get("preferences")
    if not isinstance(preferences, list):
        profile["preferences"] = deepcopy(DEFAULT_PROFILE["preferences"])
        changed = True
    else:
        normalized_preferences = []
        for item in preferences:
            token = _normalize_preference(item)
            if token and token not in normalized_preferences:
                normalized_preferences.append(token[:40])
        if not normalized_preferences:
            normalized_preferences = deepcopy(DEFAULT_PROFILE["preferences"])
        if normalized_preferences != preferences:
            profile["preferences"] = normalized_preferences
            changed = True

    pharmacy = profile.get("pharmacy")
    if not isinstance(pharmacy, dict):
        profile["pharmacy"] = _default_pharmacy()
        changed = True
    else:
        if "medications" not in pharmacy:
            pharmacy["medications"] = []
            changed = True
        if "taken_log" not in pharmacy:
            pharmacy["taken_log"] = []
            changed = True
        if "appointments" not in pharmacy:
            pharmacy["appointments"] = []
            changed = True
        if "last_weight_kg" not in pharmacy:
            pharmacy["last_weight_kg"] = None
            changed = True
        if "dose_note" not in pharmacy:
            changed = True
        pharmacy.setdefault(
            "dose_note",
            "La dosis la define un profesional de salud; no se calcula automaticamente.",
        )
        cleaned_appointments = []
        removed_lapaz = False
        for item in pharmacy.get("appointments", []):
            place = str((item or {}).get("place", "")).strip().lower()
            if "la paz" in place:
                removed_lapaz = True
                continue
            cleaned_appointments.append(item)
        if removed_lapaz:
            pharmacy["appointments"] = cleaned_appointments
            changed = True

    privacy = profile.get("privacy")
    if not isinstance(privacy, dict):
        profile["privacy"] = _default_privacy()
        changed = True
    else:
        if "consent_data_processing" not in privacy:
            privacy["consent_data_processing"] = False
            changed = True
        if "share_with_platform" not in privacy:
            privacy["share_with_platform"] = False
            changed = True
        if "allow_anon_analytics" not in privacy:
            privacy["allow_anon_analytics"] = False
            changed = True
        if "consent_updated_at" not in privacy:
            privacy["consent_updated_at"] = None
            changed = True

    if not isinstance(profile.get("joined_quedadas"), list):
        profile["joined_quedadas"] = []
        changed = True

    return changed


def _ensure_users(raw):
    changed = False
    users = raw.get("users")
    if not isinstance(users, dict):
        legacy_profile = raw.get("profile", {})
        if not isinstance(legacy_profile, dict):
            legacy_profile = _default_profile_copy()
        legacy_name = str(legacy_profile.get("name", DEFAULT_PROFILE["name"])).strip() or DEFAULT_PROFILE["name"]
        users = {
            legacy_name: {
                "profile": legacy_profile,
                "sessions": raw.get("sessions", []) if isinstance(raw.get("sessions"), list) else [],
            }
        }
        raw["users"] = users
        changed = True

    fixed = {}
    for name, user_state in users.items():
        user_name = str(name).strip()
        if not user_name:
            continue
        if not isinstance(user_state, dict):
            user_state = _default_user_state(user_name)
            changed = True
        profile = user_state.get("profile")
        sessions = user_state.get("sessions")
        if not isinstance(profile, dict):
            profile = _default_profile_copy(user_name)
            changed = True
        if not isinstance(sessions, list):
            sessions = []
            changed = True
        if _ensure_profile_shape(profile):
            changed = True
        fixed[user_name] = {"profile": profile, "sessions": sessions}

    if not fixed:
        fallback = _default_user_state(DEFAULT_PROFILE["name"])
        fixed[DEFAULT_PROFILE["name"]] = fallback
        changed = True

    raw["users"] = fixed
    raw["active_user"] = str(raw.get("active_user", "")).strip() or next(iter(fixed))
    if raw["active_user"] not in fixed:
        raw["active_user"] = next(iter(fixed))
        changed = True

    active = fixed[raw["active_user"]]
    raw["profile"] = active["profile"]
    raw["sessions"] = active["sessions"]
    return changed


def load_state():
    if not DATA_FILE.exists():
        DATA_DIR.mkdir(exist_ok=True)
        state = {"users": {DEFAULT_PROFILE["name"]: _default_user_state(DEFAULT_PROFILE["name"])}, "active_user": DEFAULT_PROFILE["name"]}
        _ensure_users(state)
        DATA_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        return state

    try:
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        broken = DATA_FILE.with_suffix(".broken.json")
        DATA_FILE.replace(broken)
        raw = {"users": {DEFAULT_PROFILE["name"]: _default_user_state(DEFAULT_PROFILE["name"])}, "active_user": DEFAULT_PROFILE["name"]}
        _ensure_users(raw)
        DATA_FILE.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    changed = _ensure_users(raw)
    if changed:
        save_state(raw)

    return raw


def save_state(state):
    DATA_DIR.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
