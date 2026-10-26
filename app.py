import json
import os
import traceback
import unicodedata
from copy import deepcopy
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import urlopen

from odiseia.assistant_ai import AssistantAI
from odiseia.engine import (
    DEFAULT_PROFILE,
    apply_game_result,
    compute_caregiver_summary,
    evaluate_alerts,
    get_exercise_for_today,
    get_game_plan_for_today,
    record_session,
)
from odiseia.storage import load_state, save_state


WEB_DIR = Path(__file__).parent / "web"
ASSET_MAP = {
    "/style.css": WEB_DIR / "style.css",
    "/app.js": WEB_DIR / "app.js",
    "/config.js": WEB_DIR / "config.js",
    "/favicon.svg": WEB_DIR / "favicon.svg",
}



def clamp_int(value, low, high, default):
    try:
        iv = int(value)
    except Exception:
        return default
    return max(low, min(high, iv))


def bool_like(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "si", "sí", "yes", "y"}
    return False


def content_type_for(path: Path):
    suffix = path.suffix.lower()
    if suffix == ".html":
        return "text/html; charset=utf-8"
    if suffix == ".css":
        return "text/css; charset=utf-8"
    if suffix == ".js":
        return "application/javascript; charset=utf-8"
    if suffix == ".svg":
        return "image/svg+xml"
    return "application/octet-stream"


def social_recommendations(mood, social_today):
    ideas = []
    if social_today:
        ideas.append("Mantener la conexión: una conversación breve esta tarde.")
    else:
        ideas.append("Enviar un mensaje corto a un familiar o amistad cercana.")
        ideas.append("Salir 15 minutos al parque y saludar a alguien conocido.")
    if mood <= 2:
        ideas.append("Plan suave: música favorita + llamada de 5 minutos.")
    elif mood >= 4:
        ideas.append("Aprovechar energía alta con paseo corto acompañado.")
    ideas.append("Hidratación y actividad ligera tras la sesión.")
    return ideas


def _normalize_user_name(value):
    name = str(value or "").strip()
    name = " ".join(name.split())
    return name[:80]


def _default_user_state(name):
    profile = deepcopy(DEFAULT_PROFILE)
    profile["name"] = _normalize_user_name(name) or DEFAULT_PROFILE["name"]
    profile.setdefault("chat_history", [])
    profile.setdefault("pharmacy", {})
    profile.setdefault(
        "privacy",
        {
            "consent_data_processing": False,
            "share_with_platform": False,
            "allow_anon_analytics": False,
            "consent_updated_at": None,
        },
    )
    profile.setdefault("quedadas", [])
    profile.setdefault("joined_quedadas", [])
    return {"profile": profile, "sessions": []}


def _ensure_privacy_settings(profile):
    privacy = profile.get("privacy")
    if not isinstance(privacy, dict):
        privacy = {}
    privacy.setdefault("consent_data_processing", False)
    privacy.setdefault("share_with_platform", False)
    privacy.setdefault("allow_anon_analytics", False)
    privacy.setdefault("consent_updated_at", None)
    profile["privacy"] = privacy
    return privacy


def _has_pharmacy_data(profile):
    pharmacy = profile.get("pharmacy", {})
    if not isinstance(pharmacy, dict):
        return False
    meds = pharmacy.get("medications", [])
    taken = pharmacy.get("taken_log", [])
    appointments = pharmacy.get("appointments", [])
    return bool(meds or taken or appointments)


def _user_data_score(user_state):
    if not isinstance(user_state, dict):
        return 0
    profile = user_state.get("profile", {})
    sessions = user_state.get("sessions", [])
    if not isinstance(profile, dict):
        profile = {}
    if not isinstance(sessions, list):
        sessions = []
    pharmacy = profile.get("pharmacy", {})
    meds = pharmacy.get("medications", []) if isinstance(pharmacy, dict) else []
    taken = pharmacy.get("taken_log", []) if isinstance(pharmacy, dict) else []
    appointments = pharmacy.get("appointments", []) if isinstance(pharmacy, dict) else []
    return len(sessions) + (len(meds) * 3) + (len(appointments) * 2) + len(taken)


def _pick_template_user(users, exclude_name):
    best = None
    best_score = 0
    for name, user_state in users.items():
        if str(name) == str(exclude_name):
            continue
        score = _user_data_score(user_state)
        if score > best_score:
            best_score = score
            best = user_state
    return deepcopy(best) if best and best_score > 0 else None


def _build_generated_seed():
    today = date.today()
    med_id = f"med-seed-{int(datetime.now().timestamp())}"
    ap_id = f"ap-seed-{int(datetime.now().timestamp())}"
    sessions = [
        {
            "date": str(today - timedelta(days=7)),
            "mood": 3,
            "social_interaction": True,
            "latency_seconds": 42,
            "frustration": "baja",
            "help_requested": 1,
            "exercise_domain": "memoria",
            "exercise_id": "seed-0",
            "difficulty": 1,
            "correctness": 78,
            "orientation_errors": 0,
            "engagement_minutes": 8,
            "notes": "Sesión inicial autogenerada.",
        },
        {
            "date": str(today - timedelta(days=4)),
            "mood": 4,
            "social_interaction": True,
            "latency_seconds": 36,
            "frustration": "baja",
            "help_requested": 0,
            "exercise_domain": "atencion",
            "exercise_id": "seed-1",
            "difficulty": 1,
            "correctness": 82,
            "orientation_errors": 0,
            "engagement_minutes": 9,
            "notes": "",
        },
    ]
    pharmacy = {
        "medications": [
            {
                "id": med_id,
                "name": "Losartán",
                "dose_text": "50 mg",
                "times": ["08:00", "20:00"],
                "frequency": "daily",
                "weekday": today.weekday(),
                "start_date": str(today),
                "stock_units": 30,
                "low_stock_threshold": 5,
                "prescribed_by": "Dra. Pérez",
                "notes": "Tomar con agua.",
            }
        ],
        "taken_log": [],
        "appointments": [
            {
                "id": ap_id,
                "date": str(today + timedelta(days=1)),
                "time": "10:30",
                "place": "Centro de salud",
                "notes": "Cita autogenerada.",
            }
        ],
        "last_weight_kg": None,
        "dose_note": "La dosis la define un profesional de salud; no se calcula automáticamente.",
    }
    return {"sessions": sessions, "pharmacy": pharmacy}


def _seed_user_data_if_missing(root, user_state, user_name):
    if not isinstance(user_state, dict):
        return False
    profile = user_state.get("profile", {})
    sessions = user_state.get("sessions", [])
    if not isinstance(profile, dict):
        profile = {}
        user_state["profile"] = profile
    if not isinstance(sessions, list):
        sessions = []
        user_state["sessions"] = sessions

    needs_sessions = len(sessions) == 0
    needs_pharmacy = not _has_pharmacy_data(profile)
    if not needs_sessions and not needs_pharmacy:
        return False

    users = root.setdefault("users", {})
    template = _pick_template_user(users, user_name)
    if template:
        tpl_profile = template.get("profile", {}) if isinstance(template, dict) else {}
        tpl_sessions = template.get("sessions", []) if isinstance(template, dict) else []
        if needs_sessions and isinstance(tpl_sessions, list) and tpl_sessions:
            user_state["sessions"] = deepcopy(tpl_sessions)
        if needs_pharmacy and isinstance(tpl_profile, dict) and isinstance(tpl_profile.get("pharmacy"), dict):
            profile["pharmacy"] = deepcopy(tpl_profile.get("pharmacy", {}))
        return True

    generated = _build_generated_seed()
    if needs_sessions:
        user_state["sessions"] = deepcopy(generated["sessions"])
    if needs_pharmacy:
        profile["pharmacy"] = deepcopy(generated["pharmacy"])
    return True


def _resolve_role_and_user(handler):
    role = str(handler.headers.get("X-Odiseia-Role", "user")).strip().lower()
    if role not in {"user", "caregiver"}:
        role = "user"
    user_name = _normalize_user_name(handler.headers.get("X-Odiseia-User"))
    if not user_name:
        user_name = DEFAULT_PROFILE["name"]
    return role, user_name


def _resolve_actor_state(handler, create_if_missing=False):
    root = load_state()
    users = root.setdefault("users", {})
    role, user_name = _resolve_role_and_user(handler)

    user_state = users.get(user_name)
    if user_state is None:
        if not create_if_missing:
            root["profile"] = None
            root["sessions"] = []
            return root, None, role, user_name
        user_state = _default_user_state(user_name)
        users[user_name] = user_state

    if not isinstance(user_state, dict):
        user_state = _default_user_state(user_name)
        users[user_name] = user_state
    user_state.setdefault("profile", _default_user_state(user_name)["profile"])
    user_state.setdefault("sessions", [])
    if not isinstance(user_state.get("profile"), dict):
        user_state["profile"] = _default_user_state(user_name)["profile"]
    if not isinstance(user_state.get("sessions"), list):
        user_state["sessions"] = []
    user_state["profile"]["name"] = user_name
    seeded = _seed_user_data_if_missing(root, user_state, user_name)
    if seeded:
        save_state(root)

    root["active_user"] = user_name
    root["profile"] = user_state["profile"]
    root["sessions"] = user_state["sessions"]
    return root, user_state, role, user_name


def build_payload(state, assistant_ai, role="user", user_name=None):
    profile = state["profile"]
    privacy = _ensure_privacy_settings(profile)
    exercise = get_exercise_for_today(state)
    game_plan = get_game_plan_for_today(state)
    summary = compute_caregiver_summary(state)
    alerts = evaluate_alerts(state)
    recent = list(reversed(state["sessions"][-8:]))
    ui_params = profile.get("ui_params", {})
    llm_status = assistant_ai.status()
    return {
        "profile": {
            "name": profile.get("name", "Usuario"),
            "preferences": profile.get("preferences", []),
            "energy_preference": profile.get("energy_preference", "media"),
            "important_data": profile.get("important_data", {}),
        },
        "exercise": exercise,
        "game_plan": game_plan,
        "summary": summary,
        "alerts": alerts,
        "recent_sessions": recent,
        "llm_enabled": False,
        "llm_configured": llm_status["configured"],
        "llm_error": llm_status["error"],
        "social_ideas": social_recommendations(3, False),
        "ui_params": ui_params,
        "game_levels": profile.get("game_levels", {}),
        "pharmacy": build_pharmacy_payload(state),
        "quedadas": profile.get("quedadas", []),
        "joined_quedadas": profile.get("joined_quedadas", []),
        "privacy": privacy,
        "auth": {
            "role": role,
            "user_name": user_name or profile.get("name", DEFAULT_PROFILE["name"]),
        },
    }


def _default_quedadas():
    today = date.today()
    return [
        {
            "id": f"q-{int(datetime.now().timestamp())}",
            "activity": "Paseo en grupo",
            "place": "Parque central",
            "date": str(today + timedelta(days=2)),
            "time": "11:00",
            "description": "Paseo suave y charla con vecinos.",
        },
        {
            "id": f"q-{int(datetime.now().timestamp()) + 1}",
            "activity": "Taller de memoria",
            "place": "Centro cívico",
            "date": str(today + timedelta(days=5)),
            "time": "17:30",
            "description": "Actividad social con juegos sencillos.",
        },
    ]


def _valid_time_hhmm(value):
    try:
        datetime.strptime(str(value).strip(), "%H:%M")
        return True
    except ValueError:
        return False


def _parse_iso_day(value):
    try:
        return date.fromisoformat(str(value))
    except Exception:
        return None


def _safe_float(value, default=None):
    try:
        return float(value)
    except Exception:
        return default
def _norm_text(value):
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text


def _extract_interest_terms(preferences):
    terms = []
    for item in (preferences or []):
        token = _norm_text(item)
        if token and token not in terms:
            terms.append(token)
    return terms[:8]


def _score_event_by_interests(event_item, interest_terms):
    if not interest_terms:
        return 0, []
    haystack = " ".join(
        [
            _norm_text(event_item.get("title", "")),
            _norm_text(event_item.get("place", "")),
            _norm_text(event_item.get("description", "")),
            " ".join(_norm_text(x) for x in (event_item.get("types") or [])),
        ]
    )
    score = 0
    reasons = []
    for term in interest_terms:
        if term in haystack:
            score += 1
            reasons.append(term)
    return score, reasons[:3]


def _google_geocode_address(address):
    key = str(os.getenv("GOOGLE_MAPS_API_KEY", "")).strip()
    if not key:
        raise RuntimeError("GOOGLE_MAPS_API_KEY no configurada")
    params = {"address": str(address or "").strip(), "key": key}
    url = "https://maps.googleapis.com/maps/api/geocode/json?" + urlencode(params)
    with urlopen(url, timeout=8) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    status = str(payload.get("status", "")).strip().upper()
    if status not in {"OK"}:
        raise RuntimeError(f"Geocoding error: {status}")
    first = (payload.get("results") or [{}])[0]
    loc = (first.get("geometry") or {}).get("location") or {}
    lat = _safe_float(loc.get("lat"), None)
    lng = _safe_float(loc.get("lng"), None)
    if lat is None or lng is None:
        raise RuntimeError("Geocoding sin coordenadas válidas")
    return {
        "lat": lat,
        "lng": lng,
        "address": str(first.get("formatted_address", "")).strip() or str(address or "").strip(),
    }


def _google_reverse_geocode(lat, lng):
    key = str(os.getenv("GOOGLE_MAPS_API_KEY", "")).strip()
    if not key:
        raise RuntimeError("GOOGLE_MAPS_API_KEY no configurada")
    params = {"latlng": f"{lat},{lng}", "key": key}
    url = "https://maps.googleapis.com/maps/api/geocode/json?" + urlencode(params)
    with urlopen(url, timeout=8) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    status = str(payload.get("status", "")).strip().upper()
    if status not in {"OK"}:
        raise RuntimeError(f"Reverse geocoding error: {status}")
    first = (payload.get("results") or [{}])[0]
    return str(first.get("formatted_address", "")).strip()


def _mock_nearby_events(lat=None, lng=None, radius_km=5, q=""):
    qtxt = str(q or "").strip() or "actividad social"
    today = date.today()
    place_hint = "zona cercana"
    if lat is not None and lng is not None:
        place_hint = f"{round(lat, 3)}, {round(lng, 3)}"
    return [
        {
            "id": "mock-1",
            "title": f"Bingo comunitario ({qtxt})",
            "place": f"Centro cívico - {place_hint}",
            "date": str(today + timedelta(days=1)),
            "time": "18:00",
            "description": "Actividad grupal suave para socializar.",
            "source": "mock",
            "lat": lat if lat is not None else 40.4168,
            "lng": lng if lng is not None else -3.7038,
            "open_now": True,
            "open_status_text": "Abierto ahora",
            "hours_text": ["L-V: 10:00-20:00", "S: 10:00-14:00"],
            "types": ["community_center", "bingo"],
        },
        {
            "id": "mock-2",
            "title": "Paseo vecinal guiado",
            "place": f"Parque local - {place_hint}",
            "date": str(today + timedelta(days=2)),
            "time": "11:30",
            "description": "Paseo en grupo con charla y descanso.",
            "source": "mock",
            "lat": (lat + 0.004) if lat is not None else 40.4208,
            "lng": (lng + 0.004) if lng is not None else -3.6998,
            "open_now": True,
            "open_status_text": "Abierto ahora",
            "hours_text": ["L-D: 08:00-22:00"],
            "types": ["park", "walking"],
        },
        {
            "id": "mock-3",
            "title": "Taller de memoria",
            "place": f"Biblioteca de barrio ({radius_km} km)",
            "date": str(today + timedelta(days=3)),
            "time": "17:00",
            "description": "Ejercicios sencillos y conversación guiada.",
            "source": "mock",
            "lat": (lat - 0.003) if lat is not None else 40.4138,
            "lng": (lng - 0.005) if lng is not None else -3.7088,
            "open_now": False,
            "open_status_text": "Cerrado ahora",
            "hours_text": ["L-V: 16:00-20:00"],
            "types": ["library", "workshop"],
        },
    ]


def _google_place_details(place_id, key):
    params = {
        "place_id": place_id,
        "fields": "opening_hours,current_opening_hours,business_status",
        "key": key,
    }
    url = "https://maps.googleapis.com/maps/api/place/details/json?" + urlencode(params)
    with urlopen(url, timeout=8) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    status = str(payload.get("status", "")).strip().upper()
    if status not in {"OK"}:
        return {}
    return (payload.get("result") or {})


def _google_nearby_events(lat, lng, radius_km=5, q="", interest_terms=None):
    key = str(os.getenv("GOOGLE_MAPS_API_KEY", "")).strip()
    if not key:
        raise RuntimeError("GOOGLE_MAPS_API_KEY no configurada")

    radius_m = clamp_int(int(radius_km * 1000), 500, 50000, 5000)
    params = {
        "location": f"{lat},{lng}",
        "radius": radius_m,
        "key": key,
    }
    interest_text = " ".join(interest_terms or []).strip()
    if q and interest_text:
        params["keyword"] = f"{q} {interest_text}"
    elif q:
        params["keyword"] = q
    elif interest_text:
        params["keyword"] = interest_text
    else:
        params["keyword"] = "bingo centro cívico taller mayores"

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?" + urlencode(params)
    with urlopen(url, timeout=8) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    status = str(payload.get("status", "")).strip().upper()
    if status not in {"OK", "ZERO_RESULTS"}:
        raise RuntimeError(f"Google Places error: {status}")

    items = []
    for item in payload.get("results", [])[:12]:
        name = str(item.get("name", "")).strip()
        vicinity = str(item.get("vicinity", "")).strip() or "Ubicación cercana"
        place_id = str(item.get("place_id", "")).strip() or f"google-{len(items)+1}"
        if not name:
            continue
        opening = item.get("opening_hours") or {}
        open_now = opening.get("open_now")
        details = {}
        try:
            details = _google_place_details(place_id, key)
        except Exception:
            details = {}
        weekday_text = (
            ((details.get("opening_hours") or {}).get("weekday_text"))
            or ((details.get("current_opening_hours") or {}).get("weekday_text"))
            or []
        )
        if open_now is None:
            open_now = ((details.get("current_opening_hours") or {}).get("open_now"))
        open_status_text = "Horario no disponible"
        if open_now is True:
            open_status_text = "Abierto ahora"
        elif open_now is False:
            open_status_text = "Cerrado ahora"
        event_item = {
            "id": place_id,
            "title": name[:90],
            "place": vicinity[:140],
            "date": "",
            "time": "",
            "description": "Actividad cercana encontrada en Google Maps.",
            "source": "google",
            "lat": _safe_float(((item.get("geometry") or {}).get("location") or {}).get("lat"), None),
            "lng": _safe_float(((item.get("geometry") or {}).get("location") or {}).get("lng"), None),
            "types": item.get("types") or [],
            "open_now": open_now,
            "open_status_text": open_status_text,
            "hours_text": weekday_text[:7],
            "business_status": str(details.get("business_status") or item.get("business_status") or ""),
        }
        score, reasons = _score_event_by_interests(event_item, interest_terms or [])
        event_item["interest_score"] = score
        event_item["interest_reasons"] = reasons
        items.append(
            event_item
        )
    items.sort(key=lambda x: (-(x.get("interest_score") or 0), x.get("title", "")))
    return items


def _med_due_today(med, today_date):
    frequency = str(med.get("frequency", "daily")).strip().lower()
    if frequency == "daily":
        return True

    start_date = _parse_iso_day(med.get("start_date")) or today_date
    if frequency == "every_2_days":
        delta = (today_date - start_date).days
        return delta >= 0 and (delta % 2 == 0)

    if frequency == "weekly":
        weekday = clamp_int(med.get("weekday", start_date.weekday()), 0, 6, start_date.weekday())
        return today_date.weekday() == weekday

    return True


def _frequency_label(med):
    frequency = str(med.get("frequency", "daily")).strip().lower()
    if frequency == "every_2_days":
        return "Cada 2 dias"
    if frequency == "weekly":
        names = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
        weekday = clamp_int(med.get("weekday", 0), 0, 6, 0)
        return f"Semanal ({names[weekday]})"
    return "Diario"


def _ensure_pharmacy(state):
    profile = state.get("profile", {})
    pharmacy = profile.setdefault("pharmacy", {})
    meds = pharmacy.setdefault("medications", [])
    taken = pharmacy.setdefault("taken_log", [])
    appointments = pharmacy.setdefault("appointments", [])
    if not isinstance(meds, list):
        pharmacy["medications"] = []
    if not isinstance(taken, list):
        pharmacy["taken_log"] = []
    if not isinstance(appointments, list):
        pharmacy["appointments"] = []
    pharmacy.setdefault("last_weight_kg", None)
    pharmacy.setdefault("dose_note", "La dosis la define un profesional de salud; no se calcula automáticamente.")
    return pharmacy


def build_pharmacy_payload(state):
    pharmacy = _ensure_pharmacy(state)
    meds = pharmacy.get("medications", [])
    taken_log = pharmacy.get("taken_log", [])
    today_date = date.today()
    today = str(today_date)

    taken_map = set()
    for item in taken_log:
        if not isinstance(item, dict):
            continue
        if str(item.get("date", "")) != today:
            continue
        med_id = str(item.get("medication_id", ""))
        med_time = str(item.get("time", ""))
        if med_id and med_time:
            taken_map.add((med_id, med_time))

    rows = []
    total_due = 0
    total_taken = 0
    low_stock = []
    pending = []

    for med in meds:
        if not isinstance(med, dict):
            continue
        med_id = str(med.get("id", "")).strip()
        if not med_id:
            continue
        times = [str(t).strip() for t in med.get("times", []) if _valid_time_hhmm(t)]
        stock = max(0, int(med.get("stock_units", 0)))
        threshold = max(0, int(med.get("low_stock_threshold", 3)))
        due_items = []
        due_today = _med_due_today(med, today_date)
        if due_today:
            for t in times:
                taken = (med_id, t) in taken_map
                due_items.append({"time": t, "taken": taken})
                total_due += 1
                total_taken += 1 if taken else 0
                if not taken:
                    pending.append({"medication_id": med_id, "name": med.get("name", "Medicación"), "time": t})

        if stock <= threshold:
            low_stock.append({"medication_id": med_id, "name": med.get("name", "Medicación"), "stock_units": stock})

        rows.append(
            {
                "id": med_id,
                "name": str(med.get("name", "Medicación"))[:80],
                "dose_text": str(med.get("dose_text", ""))[:80],
                "times": times,
                "frequency": str(med.get("frequency", "daily")),
                "frequency_label": _frequency_label(med),
                "start_date": str(med.get("start_date", "")),
                "stock_units": stock,
                "low_stock_threshold": threshold,
                "prescribed_by": str(med.get("prescribed_by", ""))[:80],
                "notes": str(med.get("notes", ""))[:240],
                "due_today": due_today,
                "today_plan": due_items,
            }
        )

    appointments = []
    appointment_alerts = []
    tomorrow_date = today_date + timedelta(days=1)
    for ap in pharmacy.get("appointments", []):
        if not isinstance(ap, dict):
            continue
        ap_id = str(ap.get("id", "")).strip()
        ap_date = _parse_iso_day(ap.get("date"))
        ap_time = str(ap.get("time", "")).strip()
        ap_place = str(ap.get("place", "")).strip()
        if not ap_id or not ap_date or not _valid_time_hhmm(ap_time) or not ap_place:
            continue
        ap_row = {
            "id": ap_id,
            "date": str(ap_date),
            "time": ap_time,
            "place": ap_place[:120],
            "notes": str(ap.get("notes", ""))[:240],
        }
        appointments.append(ap_row)
        if ap_date == today_date:
            appointment_alerts.append({**ap_row, "when": "today"})
        elif ap_date == tomorrow_date:
            appointment_alerts.append({**ap_row, "when": "tomorrow"})

    pending.sort(key=lambda x: x["time"])
    appointments.sort(key=lambda x: (x["date"], x["time"]))
    appointment_alerts.sort(key=lambda x: (0 if x["when"] == "today" else 1, x["time"]))
    adherence = round((total_taken / total_due) * 100) if total_due else 0
    return {
        "dose_note": pharmacy.get("dose_note"),
        "last_weight_kg": pharmacy.get("last_weight_kg"),
        "medications": rows,
        "pending_today": pending,
        "low_stock": low_stock,
        "adherence_today": adherence,
        "today_total_due": total_due,
        "today_total_taken": total_taken,
        "appointments": appointments,
        "appointment_alerts": appointment_alerts,
    }


class OdiseiaHandler(BaseHTTPRequestHandler):
    ai = AssistantAI()

    def _send_bytes(self, payload, content_type="application/octet-stream", status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _send_json(self, data, status=200):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self._send_bytes(payload, "application/json; charset=utf-8", status=status)

    def _send_error_json(self, message, status=400, detail=None):
        data = {"ok": False, "error": message}
        if detail:
            data["detail"] = detail
        self._send_json(data, status=status)

    def _read_json(self):
        length = clamp_int(self.headers.get("Content-Length", "0"), 0, 2_000_000, 0)
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON inválido: {exc}") from exc

    def _serve_static(self, path):
        if path == "/" or path == "/index.html":
            file_path = WEB_DIR / "index.html"
        else:
            file_path = ASSET_MAP.get(path)

        if not file_path or not file_path.exists():
            self._send_error_json("Ruta no encontrada", status=404)
            return
        payload = file_path.read_bytes()
        self._send_bytes(payload, content_type_for(file_path), status=200)

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        try:
            path = urlparse(self.path).path
            if path.startswith("/api/"):
                self._handle_api_get(path)
                return
            self._serve_static(path)
        except Exception as exc:
            traceback.print_exc()
            self._send_error_json("Error interno", status=500, detail=str(exc))

    def do_POST(self):
        try:
            path = urlparse(self.path).path
            if path == "/api/chat":
                self._handle_chat()
                return
            if path == "/api/privacy/update":
                self._handle_privacy_update()
                return
            if path == "/api/privacy/delete-all":
                self._handle_delete_all_user_data()
                return
            if path == "/api/game/next":
                self._handle_next_game()
                return
            if path == "/api/game/result":
                self._handle_game_result()
                return
            if path == "/api/pharmacy/medication":
                self._handle_add_medication()
                return
            if path == "/api/pharmacy/taken":
                self._handle_mark_med_taken()
                return
            if path == "/api/pharmacy/refill":
                self._handle_refill_medication()
                return
            if path == "/api/pharmacy/appointment":
                self._handle_add_appointment()
                return
            if path == "/api/quedadas":
                self._handle_add_quedada()
                return
            if path == "/api/quedadas/join":
                self._handle_join_quedada()
                return
            if path == "/api/quedadas/leave":
                self._handle_leave_quedada()
                return
            if path == "/api/quedadas/join-nearby":
                self._handle_join_nearby_event()
                return
            if path == "/api/users/create":
                self._handle_create_user()
                return
            if path == "/api/session":
                self._handle_session()
                return
            self._send_error_json("Ruta API no válida", status=404)
        except Exception as exc:
            traceback.print_exc()
            self._send_error_json("Error interno", status=500, detail=str(exc))

    def _handle_api_get(self, path):
        if path == "/api/health":
            self._send_json({"ok": True, "status": "up"})
            return
        if path == "/api/maps/config":
            js_key = str(os.getenv("GOOGLE_MAPS_JS_API_KEY", "")).strip()
            self._send_json({"ok": True, "enabled": bool(js_key), "js_api_key": js_key})
            return
        if path == "/api/location/reverse":
            query = parse_qs(urlparse(self.path).query)
            lat = _safe_float((query.get("lat", [""])[0] or "").strip(), None)
            lng = _safe_float((query.get("lng", [""])[0] or "").strip(), None)
            if lat is None or lng is None:
                self._send_error_json("lat/lng requeridos", status=400)
                return
            try:
                address = _google_reverse_geocode(lat, lng)
            except Exception:
                address = f"{round(lat, 6)}, {round(lng, 6)}"
            self._send_json({"ok": True, "address": address, "lat": lat, "lng": lng})
            return
        if path == "/api/events/nearby":
            query = parse_qs(urlparse(self.path).query)
            state_for_prefs, _, _, _ = _resolve_actor_state(self)
            profile_for_prefs = state_for_prefs.get("profile") if isinstance(state_for_prefs, dict) else {}
            user_preferences = []
            if isinstance(profile_for_prefs, dict):
                raw_prefs = profile_for_prefs.get("preferences", [])
                if isinstance(raw_prefs, list):
                    user_preferences = [str(x).strip() for x in raw_prefs if str(x).strip()]
            interest_terms = _extract_interest_terms(user_preferences)
            lat = _safe_float((query.get("lat", [""])[0] or "").strip(), None)
            lng = _safe_float((query.get("lng", [""])[0] or "").strip(), None)
            address = str(query.get("address", [""])[0] or "").strip()[:180]
            radius_km = clamp_int(query.get("radius_km", ["5"])[0], 1, 50, 5)
            q = str(query.get("q", [""])[0] or "").strip()[:80]
            provider = str(os.getenv("EVENTS_PROVIDER", "mock")).strip().lower()
            if provider not in {"google", "mock"}:
                provider = "mock"

            events = []
            used_provider = provider
            error = None
            resolved_address = address or ""
            if provider == "google" and (lat is None or lng is None) and address:
                try:
                    geocoded = _google_geocode_address(address)
                    lat = geocoded["lat"]
                    lng = geocoded["lng"]
                    resolved_address = geocoded["address"]
                except Exception as exc:
                    error = str(exc)

            if provider == "google" and lat is not None and lng is not None:
                try:
                    events = _google_nearby_events(lat, lng, radius_km=radius_km, q=q, interest_terms=interest_terms)
                    used_provider = "google"
                    if not resolved_address:
                        try:
                            resolved_address = _google_reverse_geocode(lat, lng)
                        except Exception:
                            resolved_address = ""
                except Exception as exc:
                    error = str(exc)
                    events = _mock_nearby_events(lat=lat, lng=lng, radius_km=radius_km, q=q)
                    used_provider = "mock"
            else:
                events = _mock_nearby_events(lat=lat, lng=lng, radius_km=radius_km, q=q)
                used_provider = "mock"

            if used_provider == "mock":
                enriched = []
                for ev in events:
                    score, reasons = _score_event_by_interests(ev, interest_terms)
                    ev = dict(ev)
                    ev["interest_score"] = score
                    ev["interest_reasons"] = reasons
                    enriched.append(ev)
                events = sorted(enriched, key=lambda x: (-(x.get("interest_score") or 0), x.get("title", "")))

            self._send_json(
                {
                    "ok": True,
                    "provider": used_provider,
                    "fallback_reason": error,
                    "preferences_used": user_preferences[:8],
                    "resolved_address": resolved_address,
                    "center_lat": lat,
                    "center_lng": lng,
                    "events": events,
                }
            )
            return
        if path == "/api/bootstrap":
            state, _, role, user_name = _resolve_actor_state(self)
            if state.get("profile") is None:
                self._send_error_json(f"Usuario '{user_name}' no encontrado", status=404)
                return
            self._send_json({"ok": True, "data": build_payload(state, self.ai, role=role, user_name=user_name)})
            return
        if path == "/api/quedadas":
            state, _, _, user_name = _resolve_actor_state(self)
            if state.get("profile") is None:
                self._send_error_json(f"Usuario '{user_name}' no encontrado", status=404)
                return
            profile = state["profile"]
            quedadas = profile.get("quedadas")
            if not isinstance(quedadas, list):
                quedadas = []
            if not quedadas:
                quedadas = _default_quedadas()
                profile["quedadas"] = deepcopy(quedadas)
                save_state(state)
            joined = profile.get("joined_quedadas", [])
            if not isinstance(joined, list):
                joined = []
                profile["joined_quedadas"] = joined
            self._send_json({"ok": True, "quedadas": quedadas, "joined_quedadas": joined})
            return
        self._send_error_json("Endpoint API no encontrado", status=404)

    def _handle_privacy_update(self):
        data = self._read_json()
        state, _, role, user_name = _resolve_actor_state(self)
        if state.get("profile") is None:
            self._send_error_json(f"Usuario '{user_name}' no encontrado", status=404)
            return
        profile = state["profile"]
        privacy = _ensure_privacy_settings(profile)
        privacy["consent_data_processing"] = bool_like(data.get("consent_data_processing", False))
        privacy["share_with_platform"] = bool_like(data.get("share_with_platform", False))
        privacy["allow_anon_analytics"] = bool_like(data.get("allow_anon_analytics", False))
        privacy["consent_updated_at"] = datetime.now().isoformat(timespec="seconds")
        save_state(state)
        self._send_json({"ok": True, "privacy": privacy})

    def _handle_delete_all_user_data(self):
        state, _, role, user_name = _resolve_actor_state(self)
        if state.get("profile") is None:
            self._send_error_json(f"Usuario '{user_name}' no encontrado", status=404)
            return
        root = load_state()
        users = root.setdefault("users", {})
        users[user_name] = _default_user_state(user_name)
        root["active_user"] = user_name
        root["profile"] = users[user_name]["profile"]
        root["sessions"] = users[user_name]["sessions"]
        save_state(root)
        self._send_json(
            {
                "ok": True,
                "message": "Datos del usuario eliminados",
                "data": build_payload(root, self.ai, role=role, user_name=user_name),
            }
        )

    def _handle_add_quedada(self):
        data = self._read_json()
        state, _, _, user_name = _resolve_actor_state(self)
        if state.get("profile") is None:
            self._send_error_json(f"Usuario '{user_name}' no encontrado", status=404)
            return
        profile = state["profile"]
        quedadas = profile.setdefault("quedadas", [])
        if not isinstance(quedadas, list):
            quedadas = []
            profile["quedadas"] = quedadas

        activity = str(data.get("activity", "")).strip()[:80]
        place = str(data.get("place", "")).strip()[:120]
        ap_date = _parse_iso_day(data.get("date"))
        ap_time = str(data.get("time", "")).strip()
        description = str(data.get("description", "")).strip()[:300]
        if not activity or not place or not ap_date or not _valid_time_hhmm(ap_time):
            self._send_error_json("Datos de quedada inválidos", status=400)
            return

        quedada = {
            "id": f"q-{int(datetime.now().timestamp() * 1000)}",
            "activity": activity,
            "place": place,
            "date": str(ap_date),
            "time": ap_time,
            "description": description,
        }
        quedadas.append(quedada)
        quedadas.sort(key=lambda x: (x.get("date", ""), x.get("time", "")))
        save_state(state)
        joined = profile.get("joined_quedadas", [])
        if not isinstance(joined, list):
            joined = []
            profile["joined_quedadas"] = joined
        self._send_json({"ok": True, "quedadas": quedadas, "joined_quedadas": joined})

    def _handle_join_quedada(self):
        data = self._read_json()
        state, _, _, user_name = _resolve_actor_state(self)
        if state.get("profile") is None:
            self._send_error_json(f"Usuario '{user_name}' no encontrado", status=404)
            return
        profile = state["profile"]
        quedadas = profile.get("quedadas", [])
        if not isinstance(quedadas, list):
            quedadas = []
            profile["quedadas"] = quedadas
        joined = profile.get("joined_quedadas", [])
        if not isinstance(joined, list):
            joined = []
            profile["joined_quedadas"] = joined

        quedada_id = str(data.get("quedada_id", "")).strip()
        if not quedada_id:
            self._send_error_json("quedada_id requerido", status=400)
            return
        exists = any(str(item.get("id", "")) == quedada_id for item in quedadas if isinstance(item, dict))
        if not exists:
            self._send_error_json("Quedada no encontrada", status=404)
            return
        if quedada_id not in joined:
            joined.append(quedada_id)
            save_state(state)
        self._send_json({"ok": True, "quedadas": quedadas, "joined_quedadas": joined})

    def _handle_leave_quedada(self):
        data = self._read_json()
        state, _, _, user_name = _resolve_actor_state(self)
        if state.get("profile") is None:
            self._send_error_json(f"Usuario '{user_name}' no encontrado", status=404)
            return
        profile = state["profile"]
        quedadas = profile.get("quedadas", [])
        if not isinstance(quedadas, list):
            quedadas = []
            profile["quedadas"] = quedadas
        joined = profile.get("joined_quedadas", [])
        if not isinstance(joined, list):
            joined = []
            profile["joined_quedadas"] = joined

        quedada_id = str(data.get("quedada_id", "")).strip()
        if not quedada_id:
            self._send_error_json("quedada_id requerido", status=400)
            return
        if quedada_id in joined:
            profile["joined_quedadas"] = [x for x in joined if str(x) != quedada_id]
            save_state(state)
        self._send_json({"ok": True, "quedadas": quedadas, "joined_quedadas": profile.get("joined_quedadas", [])})

    def _handle_join_nearby_event(self):
        data = self._read_json()
        state, _, _, user_name = _resolve_actor_state(self)
        if state.get("profile") is None:
            self._send_error_json(f"Usuario '{user_name}' no encontrado", status=404)
            return
        profile = state["profile"]
        quedadas = profile.setdefault("quedadas", [])
        if not isinstance(quedadas, list):
            quedadas = []
            profile["quedadas"] = quedadas
        joined = profile.setdefault("joined_quedadas", [])
        if not isinstance(joined, list):
            joined = []
            profile["joined_quedadas"] = joined

        title = str(data.get("title", "")).strip()[:80]
        place = str(data.get("place", "")).strip()[:120]
        q_date = _parse_iso_day(data.get("date")) or (date.today() + timedelta(days=1))
        q_time = str(data.get("time", "")).strip()
        if not _valid_time_hhmm(q_time):
            q_time = "18:00"
        description = str(data.get("description", "")).strip()[:300]
        if not title or not place:
            self._send_error_json("Evento cercano inválido", status=400)
            return

        existing = None
        for item in quedadas:
            if not isinstance(item, dict):
                continue
            if (
                str(item.get("activity", "")).strip().lower() == title.lower()
                and str(item.get("place", "")).strip().lower() == place.lower()
                and str(item.get("date", "")).strip() == str(q_date)
                and str(item.get("time", "")).strip() == q_time
            ):
                existing = item
                break

        if existing is None:
            existing = {
                "id": f"q-{int(datetime.now().timestamp() * 1000)}",
                "activity": title,
                "place": place,
                "date": str(q_date),
                "time": q_time,
                "description": description,
            }
            quedadas.append(existing)
            quedadas.sort(key=lambda x: (x.get("date", ""), x.get("time", "")))

        qid = str(existing.get("id", "")).strip()
        if qid and qid not in joined:
            joined.append(qid)
        save_state(state)
        self._send_json({"ok": True, "quedadas": quedadas, "joined_quedadas": joined, "quedada_id": qid})

    def _handle_create_user(self):
        data = self._read_json()
        root = load_state()
        users = root.setdefault("users", {})

        name = _normalize_user_name(data.get("name"))
        if not name:
            self._send_error_json("Nombre de usuario requerido", status=400)
            return
        if name in users:
            self._send_error_json(f"El usuario '{name}' ya existe", status=409)
            return

        raw_preferences = data.get("preferences", [])
        if isinstance(raw_preferences, str):
            raw_preferences = [x.strip() for x in raw_preferences.split(",")]
        preferences = []
        if isinstance(raw_preferences, list):
            for item in raw_preferences:
                token = str(item).strip()
                if token and token not in preferences:
                    preferences.append(token[:40])
        if not preferences:
            preferences = list(DEFAULT_PROFILE.get("preferences", []))

        default_energy = str(DEFAULT_PROFILE.get("energy_preference", "media")).strip().lower()
        energy = str(data.get("energy_preference", default_energy)).strip().lower()
        if energy not in {"baja", "media", "alta"}:
            energy = default_energy if default_energy in {"baja", "media", "alta"} else "media"

        weight_kg = data.get("weight_kg")
        weight_value = None
        if weight_kg is not None and str(weight_kg).strip():
            try:
                w = round(float(weight_kg), 1)
                if 20 <= w <= 300:
                    weight_value = w
            except Exception:
                weight_value = None

        important_notes = str(data.get("important_notes", "")).strip()[:400]
        birth_year = clamp_int(data.get("birth_year", 0), 1900, date.today().year, 0)

        user_state = _default_user_state(name)
        profile = user_state["profile"]
        profile["preferences"] = preferences[:8]
        profile["energy_preference"] = energy
        important_data = dict(profile.get("important_data", {}))
        important_data["weight_kg"] = weight_value if weight_value is not None else important_data.get("weight_kg")
        important_data["birth_year"] = birth_year if birth_year else important_data.get("birth_year")
        important_data["notes"] = important_notes if important_notes else important_data.get("notes", "")
        profile["important_data"] = important_data
        privacy = _ensure_privacy_settings(profile)
        privacy["consent_data_processing"] = bool_like(data.get("consent_data_processing", False))
        privacy["share_with_platform"] = bool_like(data.get("share_with_platform", False))
        privacy["allow_anon_analytics"] = bool_like(data.get("allow_anon_analytics", False))
        privacy["consent_updated_at"] = datetime.now().isoformat(timespec="seconds")
        users[name] = user_state
        _seed_user_data_if_missing(root, user_state, name)
        pharmacy = profile.setdefault("pharmacy", {})
        if weight_value is not None:
            pharmacy["last_weight_kg"] = weight_value
        root["active_user"] = name
        root["profile"] = user_state["profile"]
        root["sessions"] = user_state["sessions"]
        save_state(root)

        self._send_json(
            {
                "ok": True,
                "message": "Usuario creado",
                "data": build_payload(root, self.ai, role="user", user_name=name),
            }
        )

    def _handle_chat(self):
        data = self._read_json()
        message = str(data.get("message", "")).strip()
        mood = clamp_int(data.get("mood", 3), 1, 5, 3)
        social_today = bool_like(data.get("social_today", False))
        state, _, role, user_name = _resolve_actor_state(self)
        if state.get("profile") is None:
            self._send_error_json(f"Usuario '{user_name}' no encontrado", status=404)
            return
        profile = state["profile"]
        history = profile.get("chat_history", [])
        if not isinstance(history, list):
            history = []
        reply, llm = self.ai.reply(message, profile, mood, social_today, history=history)

        history.append({"role": "user", "content": message[:500]})
        history.append({"role": "assistant", "content": reply[:500]})
        profile["chat_history"] = history[-12:]
        save_state(state)
        self._send_json(
            {
                "ok": True,
                "reply": reply,
                "llm_enabled": bool(llm.get("used_llm")),
                "llm_configured": bool(llm.get("configured")),
                "llm_error": llm.get("error"),
            }
        )

    def _handle_next_game(self):
        state, _, role, user_name = _resolve_actor_state(self)
        if state.get("profile") is None:
            self._send_error_json(f"Usuario '{user_name}' no encontrado", status=404)
            return
        try:
            data = self._read_json()
        except Exception:
            data = {}
        game_result = data.get("game_result") if isinstance(data, dict) else None
        if isinstance(game_result, dict):
            apply_game_result(state["profile"], game_result)
        plan = get_game_plan_for_today(state)
        state["profile"]["last_game"] = plan["id"]
        state["profile"]["game_nonce"] = int(state["profile"].get("game_nonce", 0)) + 1
        save_state(state)
        self._send_json({"ok": True, "game_plan": plan})

    def _handle_game_result(self):
        data = self._read_json()
        game_result = data.get("game_result")
        if not isinstance(game_result, dict):
            self._send_error_json("game_result requerido", status=400)
            return
        state, _, role, user_name = _resolve_actor_state(self)
        if state.get("profile") is None:
            self._send_error_json(f"Usuario '{user_name}' no encontrado", status=404)
            return
        apply_game_result(state["profile"], game_result)
        save_state(state)
        self._send_json({"ok": True, "game_levels": state["profile"].get("game_levels", {})})

    def _handle_add_medication(self):
        data = self._read_json()
        state, _, role, user_name = _resolve_actor_state(self)
        if state.get("profile") is None:
            self._send_error_json(f"Usuario '{user_name}' no encontrado", status=404)
            return
        pharmacy = _ensure_pharmacy(state)

        name = str(data.get("name", "")).strip()
        dose_text = str(data.get("dose_text", "")).strip()
        prescribed_by = str(data.get("prescribed_by", "")).strip()
        notes = str(data.get("notes", "")).strip()
        raw_times = data.get("times", [])
        if isinstance(raw_times, str):
            raw_times = [t.strip() for t in raw_times.split(",")]
        times = [t for t in raw_times if _valid_time_hhmm(t)]
        stock_units = clamp_int(data.get("stock_units", 0), 0, 5000, 0)
        low_stock_threshold = clamp_int(data.get("low_stock_threshold", 3), 0, 1000, 3)
        frequency = str(data.get("frequency", "daily")).strip().lower()
        if frequency not in {"daily", "every_2_days", "weekly"}:
            frequency = "daily"
        weekday = clamp_int(data.get("weekday", date.today().weekday()), 0, 6, date.today().weekday())
        start_date = _parse_iso_day(data.get("start_date")) or date.today()
        weight = data.get("weight_kg")

        if not name:
            self._send_error_json("Nombre de medicamento requerido", status=400)
            return
        if not dose_text:
            self._send_error_json("Dosis prescrita requerida", status=400)
            return
        if not times:
            self._send_error_json("Debes indicar al menos un horario en formato HH:MM", status=400)
            return

        medication_id = f"med-{int(datetime.now().timestamp() * 1000)}"
        pharmacy["medications"].append(
            {
                "id": medication_id,
                "name": name[:80],
                "dose_text": dose_text[:80],
                "times": times[:8],
                "frequency": frequency,
                "weekday": weekday,
                "start_date": str(start_date),
                "stock_units": stock_units,
                "low_stock_threshold": low_stock_threshold,
                "prescribed_by": prescribed_by[:80],
                "notes": notes[:240],
            }
        )

        if weight is not None and str(weight).strip():
            try:
                w = round(float(weight), 1)
                if 20 <= w <= 300:
                    pharmacy["last_weight_kg"] = w
            except Exception:
                pass

        save_state(state)
        self._send_json({"ok": True, "pharmacy": build_pharmacy_payload(state)})

    def _handle_mark_med_taken(self):
        data = self._read_json()
        state, _, role, user_name = _resolve_actor_state(self)
        if state.get("profile") is None:
            self._send_error_json(f"Usuario '{user_name}' no encontrado", status=404)
            return
        pharmacy = _ensure_pharmacy(state)
        med_id = str(data.get("medication_id", "")).strip()
        med_time = str(data.get("time", "")).strip()
        if not med_id or not _valid_time_hhmm(med_time):
            self._send_error_json("Medicación/horario inválido", status=400)
            return

        meds = [m for m in pharmacy["medications"] if str(m.get("id", "")) == med_id]
        if not meds:
            self._send_error_json("Medicamento no encontrado", status=404)
            return
        med = meds[0]

        today = str(date.today())
        already = any(
            isinstance(item, dict)
            and str(item.get("medication_id", "")) == med_id
            and str(item.get("date", "")) == today
            and str(item.get("time", "")) == med_time
            for item in pharmacy["taken_log"]
        )
        if not already:
            pharmacy["taken_log"].append(
                {
                    "medication_id": med_id,
                    "time": med_time,
                    "date": today,
                    "taken_at": datetime.now().isoformat(timespec="seconds"),
                }
            )
            med["stock_units"] = max(0, int(med.get("stock_units", 0)) - 1)

        save_state(state)
        self._send_json({"ok": True, "pharmacy": build_pharmacy_payload(state)})

    def _handle_refill_medication(self):
        data = self._read_json()
        state, _, role, user_name = _resolve_actor_state(self)
        if state.get("profile") is None:
            self._send_error_json(f"Usuario '{user_name}' no encontrado", status=404)
            return
        pharmacy = _ensure_pharmacy(state)
        med_id = str(data.get("medication_id", "")).strip()
        add_units = clamp_int(data.get("units", 0), 1, 5000, 0)
        if not med_id or add_units <= 0:
            self._send_error_json("Datos de recarga inválidos", status=400)
            return

        target = None
        for med in pharmacy["medications"]:
            if str(med.get("id", "")) == med_id:
                target = med
                break
        if not target:
            self._send_error_json("Medicamento no encontrado", status=404)
            return

        target["stock_units"] = max(0, int(target.get("stock_units", 0)) + add_units)
        save_state(state)
        self._send_json({"ok": True, "pharmacy": build_pharmacy_payload(state)})

    def _handle_add_appointment(self):
        data = self._read_json()
        state, _, role, user_name = _resolve_actor_state(self)
        if state.get("profile") is None:
            self._send_error_json(f"Usuario '{user_name}' no encontrado", status=404)
            return
        pharmacy = _ensure_pharmacy(state)

        ap_date = _parse_iso_day(data.get("date"))
        ap_time = str(data.get("time", "")).strip()
        place = str(data.get("place", "")).strip()
        notes = str(data.get("notes", "")).strip()
        if not ap_date:
            self._send_error_json("Fecha de cita invalida (YYYY-MM-DD)", status=400)
            return
        if not _valid_time_hhmm(ap_time):
            self._send_error_json("Hora de cita invalida (HH:MM)", status=400)
            return
        if not place:
            self._send_error_json("Debes indicar hospital o centro", status=400)
            return

        ap_id = f"ap-{int(datetime.now().timestamp() * 1000)}"
        pharmacy["appointments"].append(
            {
                "id": ap_id,
                "date": str(ap_date),
                "time": ap_time,
                "place": place[:120],
                "notes": notes[:240],
            }
        )
        save_state(state)
        self._send_json({"ok": True, "pharmacy": build_pharmacy_payload(state)})

    def _handle_session(self):
        data = self._read_json()
        state, _, role, user_name = _resolve_actor_state(self)
        if state.get("profile") is None:
            self._send_error_json(f"Usuario '{user_name}' no encontrado", status=404)
            return

        suggested = get_exercise_for_today(state)
        domain = str(data.get("exercise_domain", suggested["domain"]))
        exercise_id = str(data.get("exercise_id", suggested["id"]))
        difficulty = clamp_int(data.get("difficulty", suggested["difficulty"]), 1, 5, suggested["difficulty"])
        frustration = str(data.get("frustration", "media")).lower().strip()
        if frustration not in {"baja", "media", "alta"}:
            frustration = "media"

        session = {
            "date": str(date.today()),
            "mood": clamp_int(data.get("mood", 3), 1, 5, 3),
            "social_interaction": bool_like(data.get("social_interaction", False)),
            "latency_seconds": clamp_int(data.get("latency_seconds", 40), 5, 300, 40),
            "frustration": frustration,
            "help_requested": clamp_int(data.get("help_requested", 0), 0, 10, 0),
            "exercise_domain": domain,
            "exercise_id": exercise_id,
            "difficulty": difficulty,
            "correctness": clamp_int(data.get("correctness", 70), 0, 100, 70),
            "orientation_errors": clamp_int(data.get("orientation_errors", 0), 0, 5, 0),
            "engagement_minutes": clamp_int(data.get("engagement_minutes", 8), 1, 30, 8),
            "notes": str(data.get("notes", ""))[:400],
        }
        game_result = data.get("game_result")
        if isinstance(game_result, dict):
            session["game_result"] = {
                "id": str(game_result.get("id", ""))[:60],
                "difficulty": clamp_int(game_result.get("difficulty", 1), 1, 5, 1),
                "score": clamp_int(game_result.get("score", 0), 0, 100, 0),
                "max_score": clamp_int(game_result.get("max_score", 1), 1, 100, 1),
                "success": bool_like(game_result.get("success", False)),
                "response_seconds": clamp_int(game_result.get("response_seconds", 0), 0, 3600, 0),
                "hints_used": clamp_int(game_result.get("hints_used", 0), 0, 20, 0),
            }
        record_session(state, session)
        save_state(state)
        self._send_json(
            {
                "ok": True,
                "message": "Sesión guardada",
                "data": build_payload(state, self.ai, role=role, user_name=user_name),
            }
        )


def main():
    host = "127.0.0.1"
    port = 8001
    try:
        server = ThreadingHTTPServer((host, port), OdiseiaHandler)
    except OSError as exc:
        print(f"No se pudo abrir {host}:{port}: {exc}")
        print("Ejecuta scripts\\internal_bat\\stop_odiseia.bat o cierra el proceso que usa ese puerto.")
        raise
    print(f"Odiseia web app en http://{host}:{port}")
    print("Ctrl+C para salir")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()




