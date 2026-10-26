import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from odiseia.engine import DEFAULT_PROFILE, DOMAIN_ORDER


random.seed(7)

DATA = ROOT / "data"
FILE = DATA / "state.json"


def main():
    DATA.mkdir(exist_ok=True)
    sessions = []
    start = date.today() - timedelta(days=27)
    domain_i = 0

    for i in range(28):
        d = start + timedelta(days=i)
        if random.random() < 0.2:
            continue

        last_14 = i >= 14
        correctness_base = 78 if not last_14 else 62
        latency_base = 36 if not last_14 else 58
        social_yes = random.random() < (0.65 if not last_14 else 0.35)
        orientation_err = 0 if not last_14 else random.choice([0, 1, 2])

        sessions.append(
            {
                "date": str(d),
                "mood": random.randint(2, 4),
                "social_interaction": social_yes,
                "latency_seconds": max(10, int(random.gauss(latency_base, 8))),
                "frustration": random.choice(["baja", "media", "alta"] if last_14 else ["baja", "media"]),
                "help_requested": random.randint(0, 3),
                "exercise_domain": DOMAIN_ORDER[domain_i % len(DOMAIN_ORDER)],
                "exercise_id": f"demo-{i}",
                "difficulty": random.randint(1, 4),
                "correctness": max(25, min(98, int(random.gauss(correctness_base, 10)))),
                "orientation_errors": orientation_err,
                "engagement_minutes": random.randint(5, 12),
                "notes": "",
            }
        )
        domain_i += 1

    state = {
        "profile": DEFAULT_PROFILE,
        "sessions": sessions,
    }
    state["profile"]["name"] = "María (Demo)"
    state["profile"]["last_domain"] = sessions[-1]["exercise_domain"] if sessions else "orientacion"
    FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Datos demo escritos en {FILE}")
    print(f"Sesiones creadas: {len(sessions)}")


if __name__ == "__main__":
    main()
