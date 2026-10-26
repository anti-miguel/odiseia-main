from datetime import date, timedelta
from random import Random
from statistics import mean


DEFAULT_PROFILE = {
    "name": "Usuario Demo",
    "preferences": ["cocina", "música", "familia", "fútbol"],
    "energy_preference": "media",
    "domain_levels": {
        "memoria": 2,
        "atencion": 2,
        "lenguaje": 2,
        "ejecutiva": 2,
        "orientacion": 2,
    },
    "last_domain": "orientacion",
    "game_levels": {
        "memory_words": 1,
        "reverse_digits": 1,
        "category_sprint": 1,
        "memory_cards": 1,
        "sudoku_4x4": 1,
        "crossword_mini": 1,
        "word_search": 1,
    },
    "game_adaptation": {
        "memory_words": [],
        "reverse_digits": [],
        "category_sprint": [],
        "memory_cards": [],
        "sudoku_4x4": [],
        "crossword_mini": [],
        "word_search": [],
    },
    "last_game": "word_search",
    "ui_params": {
        "senior_mode_default": True,
        "large_text_default": False,
        "high_contrast_default": False,
        "suggested_session_minutes": 8,
    },
    "privacy": {
        "consent_data_processing": False,
        "share_with_platform": False,
        "allow_anon_analytics": False,
        "consent_updated_at": None,
    },
    "game_nonce": 0,
}


EXERCISES = {
    "memoria": [
        "Recuerda estas 4 palabras y repítelas al final: café, ventana, perro, lluvia.",
        "Escucha una historia corta y responde 3 preguntas clave.",
        "Menciona 3 recuerdos agradables de la infancia con un detalle de lugar.",
    ],
    "atencion": [
        "Cuenta cuántas veces aparece la palabra 'sol' en una frase larga.",
        "Repite una secuencia de números al revés: 7-3-9-1.",
        "Encuentra el elemento diferente entre 5 opciones similares.",
    ],
    "lenguaje": [
        "Dime nombres de animales durante 45 segundos.",
        "Completa el refrán: 'No dejes para mañana...'.",
        "Busca un sinónimo de 'alegría' y úsalo en una frase.",
    ],
    "ejecutiva": [
        "Organicemos un día ideal en 4 pasos con horarios.",
        "Describe cómo prepararías una receta sencilla paso a paso.",
        "Prioriza 3 tareas de hoy y explica por qué en ese orden.",
    ],
    "orientacion": [
        "¿Qué día de la semana es hoy y en qué mes estamos?",
        "Menciona un evento próximo importante y cuándo será.",
        "Ubica la estación actual y una actividad típica de esta época.",
    ],
}


DOMAIN_ORDER = ["memoria", "atencion", "lenguaje", "ejecutiva", "orientacion"]
GAME_ORDER = ["memory_words", "reverse_digits", "category_sprint", "memory_cards", "sudoku_4x4", "crossword_mini", "word_search"]
GAME_WORDS = [
    "cafe",
    "parque",
    "lluvia",
    "tren",
    "jardin",
    "pelota",
    "reloj",
    "musica",
    "nieta",
    "ventana",
    "camino",
    "playa",
    "sol",
    "invierno",
    "cocina",
    "libro",
]
CATEGORIES = ["animales", "frutas", "ciudades", "colores", "profesiones", "deportes"]
SUDOKU_SOLUTIONS = [
    [[1, 2, 3, 4], [3, 4, 1, 2], [2, 1, 4, 3], [4, 3, 2, 1]],
    [[2, 1, 4, 3], [4, 3, 2, 1], [1, 2, 3, 4], [3, 4, 1, 2]],
]
SUDOKU_MASKS = [
    [[1, 1, 0, 0], [0, 1, 1, 0], [1, 0, 1, 0], [0, 1, 0, 1]],
    [[1, 0, 1, 0], [0, 1, 0, 1], [1, 0, 0, 1], [0, 1, 1, 0]],
    [[1, 0, 0, 1], [0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 1]],
    [[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 1], [0, 0, 1, 0]],
]
CROSSWORD_CLUE_BANK = [
    {"clue": "Mueble para dormir", "answer": "cama"},
    {"clue": "Objeto para ver la hora", "answer": "reloj"},
    {"clue": "Lugar donde cocinamos", "answer": "cocina"},
    {"clue": "Abre o cierra la entrada", "answer": "puerta"},
    {"clue": "Sirve para sentarse", "answer": "silla"},
    {"clue": "Se toma por la mañana", "answer": "cafe"},
    {"clue": "Se usa para leer de noche", "answer": "lampara"},
    {"clue": "Se coloca en la mesa", "answer": "plato"},
    {"clue": "Se abre para ventilar", "answer": "ventana"},
    {"clue": "Donde guardas comida fría", "answer": "nevera"},
    {"clue": "Lo usas para beber agua", "answer": "vaso"},
    {"clue": "Objeto para escribir", "answer": "lapiz"},
    {"clue": "Sirve para escuchar música", "answer": "radio"},
    {"clue": "Se enciende para iluminar", "answer": "luz"},
    {"clue": "Mueble donde comes", "answer": "mesa"},
    {"clue": "Va en la puerta para abrir", "answer": "llave"},
    {"clue": "Lugar con árboles y bancos", "answer": "parque"},
    {"clue": "Objeto para hablar a distancia", "answer": "telefono"},
    {"clue": "Vehículo de dos ruedas", "answer": "bicicleta"},
    {"clue": "Estación más fría del año", "answer": "invierno"},
]

WORDSEARCH_WORD_BANK = [
    "SOL",
    "MAR",
    "FLOR",
    "NUBE",
    "MESA",
    "SILLA",
    "PUERTA",
    "TECHO",
    "PARQUE",
    "CAMINO",
    "TREN",
    "MUSICA",
    "LIBRO",
    "JARDIN",
    "VENTANA",
    "COCINA",
    "PLAYA",
    "PERRO",
    "GATO",
    "FAMILIA",
    "ABRIGO",
    "CIELO",
    "FRUTA",
    "DEPORTE",
]
CARD_SYMBOLS = ["A", "L", "C", "S", "P", "R", "M", "N"]


def parse_iso(day):
    return date.fromisoformat(day)


def sessions_in_days(state, days):
    cutoff = date.today() - timedelta(days=days)
    return [s for s in state["sessions"] if parse_iso(s["date"]) >= cutoff]


def average(values, digits=1):
    if not values:
        return 0
    return round(mean(values), digits)


def next_domain(profile):
    current = profile.get("last_domain", DOMAIN_ORDER[0])
    idx = DOMAIN_ORDER.index(current)
    return DOMAIN_ORDER[(idx + 1) % len(DOMAIN_ORDER)]


def _next_game(profile):
    current = profile.get("last_game", GAME_ORDER[0])
    idx = GAME_ORDER.index(current) if current in GAME_ORDER else 0
    return GAME_ORDER[(idx + 1) % len(GAME_ORDER)]


def _ensure_game_profile(profile):
    profile.setdefault("game_levels", DEFAULT_PROFILE["game_levels"].copy())
    profile.setdefault("game_adaptation", {gid: [] for gid in GAME_ORDER})
    profile.setdefault("last_game", DEFAULT_PROFILE["last_game"])
    profile.setdefault("ui_params", DEFAULT_PROFILE["ui_params"].copy())
    profile.setdefault("game_nonce", 0)
    for gid in GAME_ORDER:
        profile["game_levels"].setdefault(gid, 1)
        profile["game_adaptation"].setdefault(gid, [])


def adaptation_rules(state, domain):
    recent = [s for s in reversed(state["sessions"]) if s["exercise_domain"] == domain][:3]
    level = state["profile"]["domain_levels"].get(domain, 2)

    if len(recent) >= 3 and all(s["correctness"] >= 85 and s["frustration"] == "baja" for s in recent[:3]):
        level = min(5, level + 1)
    elif len(recent) >= 2 and (
        all(s["correctness"] <= 55 for s in recent[:2])
        or any(s["frustration"] == "alta" for s in recent[:2])
    ):
        level = max(1, level - 1)

    state["profile"]["domain_levels"][domain] = level
    return level


def get_exercise_for_today(state):
    profile = state["profile"]
    domain = next_domain(profile)
    difficulty = adaptation_rules(state, domain)
    options = EXERCISES[domain]
    idx = (len(state["sessions"]) + difficulty) % len(options)

    prompt = options[idx]
    pref = profile.get("preferences", [])
    if pref:
        prompt += f" Contexto sugerido: usa el tema '{pref[len(state['sessions']) % len(pref)]}'."

    return {
        "id": f"{domain}-{idx}",
        "domain": domain,
        "difficulty": difficulty,
        "prompt": prompt,
    }


def _build_sudoku_plan(difficulty, offset):
    size = 4 if difficulty <= 3 else 6
    if size == 4:
        solution = SUDOKU_SOLUTIONS[offset % len(SUDOKU_SOLUTIONS)]
        mask_idx = min(len(SUDOKU_MASKS) - 1, max(0, difficulty - 1))
        mask = SUDOKU_MASKS[(mask_idx + offset) % len(SUDOKU_MASKS)]
        puzzle = []
        blanks = 0
        for r in range(4):
            row = []
            for c in range(4):
                if mask[r][c]:
                    row.append(solution[r][c])
                else:
                    row.append(0)
                    blanks += 1
            puzzle.append(row)
    else:
        # Latin square 6x6: uniqueness by row/column, compatible with current checker.
        solution = [[((r + c) % size) + 1 for c in range(size)] for r in range(size)]
        rng = Random(offset * 97 + difficulty * 13)
        puzzle = []
        blanks = 0
        hide_ratio = min(0.72, 0.42 + (difficulty * 0.08))
        for r in range(size):
            row = []
            for c in range(size):
                if rng.random() < hide_ratio:
                    row.append(0)
                    blanks += 1
                else:
                    row.append(solution[r][c])
            puzzle.append(row)
    return {
        "id": "sudoku_4x4",
        "name": f"Sudoku {size}x{size}",
        "difficulty": difficulty,
        "instructions": f"Completa la cuadrícula con números del 1 al {size} sin repetir en fila ni columna.",
        "payload": {"puzzle": puzzle, "solution": solution, "max_score": blanks, "size": size},
    }


def _build_crossword_plan(difficulty, offset):
    rng = Random(offset * 59 + difficulty * 17)
    pool = CROSSWORD_CLUE_BANK[:]
    rng.shuffle(pool)
    total = min(len(pool), 2 + difficulty + (1 if difficulty >= 4 else 0))
    entries = pool[:total]
    return {
        "id": "crossword_mini",
        "name": "Crucigrama rápido",
        "difficulty": difficulty,
        "instructions": "Resuelve las pistas y escribe una palabra por cada una.",
        "payload": {"theme": "Crucigrama dinámico", "entries": entries, "max_score": total},
    }


def _build_wordsearch_grid(words, size, rng):
    grid = [["" for _ in range(size)] for _ in range(size)]
    directions = [(1, 0), (0, 1), (1, 1), (-1, 1)]
    placed = []

    for raw in sorted(words, key=len, reverse=True):
        word = str(raw).upper()
        ok = False
        for _ in range(80):
            dr, dc = directions[rng.randrange(len(directions))]
            if dr == 1:
                r0 = rng.randrange(0, max(1, size - len(word) + 1))
            elif dr == -1:
                r0 = rng.randrange(len(word) - 1, size)
            else:
                r0 = rng.randrange(size)

            if dc == 1:
                c0 = rng.randrange(0, max(1, size - len(word) + 1))
            else:
                c0 = rng.randrange(size)

            fit = True
            rr, cc = r0, c0
            for ch in word:
                if rr < 0 or rr >= size or cc < 0 or cc >= size:
                    fit = False
                    break
                cell = grid[rr][cc]
                if cell not in ("", ch):
                    fit = False
                    break
                rr += dr
                cc += dc
            if not fit:
                continue

            rr, cc = r0, c0
            for ch in word:
                grid[rr][cc] = ch
                rr += dr
                cc += dc
            ok = True
            placed.append(word)
            break

        if not ok:
            continue

    alphabet = "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"
    for r in range(size):
        for c in range(size):
            if not grid[r][c]:
                grid[r][c] = alphabet[rng.randrange(len(alphabet))]

    rows = ["".join(row) for row in grid]
    return rows, placed


def _build_word_search_plan(difficulty, offset):
    rng = Random(offset * 71 + difficulty * 19)
    pool = WORDSEARCH_WORD_BANK[:]
    rng.shuffle(pool)
    target = min(len(pool), 3 + difficulty)
    words = [pool[i].upper() for i in range(target)]
    size = max(8, min(14, 7 + difficulty * 2))
    rows, placed = _build_wordsearch_grid(words, size, rng)
    if not placed:
        placed = [words[0]]
        row0 = list(rows[0])
        for i, ch in enumerate(placed[0][: len(row0)]):
            row0[i] = ch
        rows[0] = "".join(row0)
    return {
        "id": "word_search",
        "name": "Sopa de letras",
        "difficulty": difficulty,
        "instructions": "Busca palabras en la cuadrícula y escríbelas separadas por comas.",
        "payload": {
            "theme": "Sopa de letras dinámica",
            "grid": rows,
            "words": placed,
            "max_score": len(placed),
            "size": size,
        },
    }

def _build_memory_cards_plan(difficulty, offset):
    pairs = min(8, 3 + difficulty)
    base = [CARD_SYMBOLS[(offset + i) % len(CARD_SYMBOLS)] for i in range(pairs)]
    deck = base + base
    shuffled = []
    step = (offset % 5) + 3
    idx = offset % len(deck)
    while deck:
        idx = (idx + step) % len(deck)
        shuffled.append(deck.pop(idx))
    return {
        "id": "memory_cards",
        "name": "Memoria de cartas",
        "difficulty": difficulty,
        "instructions": "Levanta dos cartas y encuentra todas las parejas.",
        "payload": {"cards": shuffled, "pairs": pairs, "max_score": pairs},
    }

def _build_game_plan(game_id, difficulty, offset):
    if game_id == "memory_words":
        n_words = min(7, 4 + (difficulty - 1))
        words = [GAME_WORDS[(offset + i) % len(GAME_WORDS)] for i in range(n_words)]
        return {
            "id": "memory_words",
            "name": "Memoria de palabras",
            "difficulty": difficulty,
            "instructions": f"Memoriza {n_words} palabras y escríbelas después.",
            "payload": {"words": words, "max_score": n_words},
        }

    if game_id == "reverse_digits":
        n_digits = min(8, 3 + difficulty)
        seed_digits = "".join(str(((offset + i) * 7 + 3) % 10) for i in range(n_digits))
        return {
            "id": "reverse_digits",
            "name": "Números al revés",
            "difficulty": difficulty,
            "instructions": "Escribe la secuencia al revés.",
            "payload": {"sequence": seed_digits, "max_score": n_digits},
        }

    if game_id == "sudoku_4x4":
        return _build_sudoku_plan(difficulty, offset)

    if game_id == "crossword_mini":
        return _build_crossword_plan(difficulty, offset)

    if game_id == "word_search":
        return _build_word_search_plan(difficulty, offset)

    if game_id == "memory_cards":
        return _build_memory_cards_plan(difficulty, offset)

    target_count = min(12, 4 + (difficulty * 2))
    category = CATEGORIES[offset % len(CATEGORIES)]
    return {
        "id": "category_sprint",
        "name": "Torpedo de categorías",
        "difficulty": difficulty,
        "instructions": f"Escribe palabras de la categoría '{category}'. Objetivo: {target_count}.",
        "payload": {"category": category, "target_count": target_count, "max_score": target_count},
    }


def get_game_plan_for_today(state):
    profile = state["profile"]
    _ensure_game_profile(profile)
    game_id = _next_game(profile)
    difficulty = int(profile["game_levels"].get(game_id, 1))
    offset = len(state["sessions"]) + difficulty + int(profile.get("game_nonce", 0))
    return _build_game_plan(game_id, difficulty, offset)


def _adapt_game_level(profile, game_result):
    if not game_result:
        return
    game_id = str(game_result.get("id", "")).strip()
    if game_id not in GAME_ORDER:
        return
    levels = profile["game_levels"]
    adaptation = profile["game_adaptation"]
    ratio = 0
    score = max(0, int(game_result.get("score", 0)))
    max_score = max(1, int(game_result.get("max_score", 1)))
    ratio = score / max_score
    success = ratio >= 0.8
    history = adaptation.get(game_id, [])
    history.append(success)
    history = history[-4:]
    adaptation[game_id] = history

    current = max(1, min(5, int(levels.get(game_id, 1))))
    if len(history) >= 3 and all(history[-3:]):
        current = min(5, current + 1)
    elif len(history) >= 2 and not any(history[-2:]):
        current = max(1, current - 1)
    if score >= max_score and max_score > 0:
        current = min(5, current + 1)
    levels[game_id] = current
    profile["last_game"] = game_id


def apply_game_result(profile, game_result):
    _ensure_game_profile(profile)
    _adapt_game_level(profile, game_result)


def _adapt_ui_params(state):
    profile = state["profile"]
    ui = profile.get("ui_params", DEFAULT_PROFILE["ui_params"].copy())
    recent = sessions_in_days(state, 7)
    if not recent:
        profile["ui_params"] = ui
        return

    avg_latency = average([s.get("latency_seconds", 40) for s in recent])
    avg_correct = average([s.get("correctness", 70) for s in recent])
    frustration_high = len([s for s in recent if s.get("frustration") == "alta"])
    avg_minutes = average([s.get("engagement_minutes", 8) for s in recent])

    ui["senior_mode_default"] = True
    ui["high_contrast_default"] = avg_latency >= 65 or frustration_high >= 2
    ui["large_text_default"] = avg_latency >= 55 or frustration_high >= 2
    if avg_correct >= 85 and avg_minutes >= 8:
        ui["suggested_session_minutes"] = 10
    elif frustration_high >= 2:
        ui["suggested_session_minutes"] = 6
    else:
        ui["suggested_session_minutes"] = 8
    profile["ui_params"] = ui


def record_session(state, session):
    profile = state["profile"]
    _ensure_game_profile(profile)
    state["sessions"].append(session)
    profile["last_domain"] = session["exercise_domain"]
    _adapt_game_level(profile, session.get("game_result"))
    _adapt_ui_params(state)


def compute_caregiver_summary(state):
    s7 = sessions_in_days(state, 7)
    s28 = sessions_in_days(state, 28)
    recent = list(reversed(state["sessions"][-5:]))

    if recent:
        rows = [
            "<table style='width:100%;border-collapse:collapse;'>"
            "<tr><th>Fecha</th><th>Dominio</th><th>Acierto</th><th>Ánimo</th><th>Latencia</th></tr>"
        ]
        for s in recent:
            rows.append(
                "<tr>"
                f"<td>{s['date']}</td><td>{s['exercise_domain']}</td>"
                f"<td>{s['correctness']}%</td><td>{s['mood']}</td><td>{s['latency_seconds']}s</td>"
                "</tr>"
            )
        rows.append("</table>")
        recent_html = "".join(rows)
    else:
        recent_html = "<p>No hay sesiones registradas.</p>"

    game_sessions = [s for s in s28 if isinstance(s.get("game_result"), dict)]
    game_score = average(
        [
            (max(0, int(s["game_result"].get("score", 0))) / max(1, int(s["game_result"].get("max_score", 1)))) * 100
            for s in game_sessions
        ]
    )

    return {
        "sessions_28d": len(s28),
        "weekly_adherence": len(s7),
        "avg_mood": average([s["mood"] for s in s28]),
        "social_rate": average([100 if s["social_interaction"] else 0 for s in s28]),
        "avg_correctness": average([s["correctness"] for s in s28]),
        "avg_latency": average([s["latency_seconds"] for s in s28]),
        "avg_game_score": game_score,
        "recent_sessions_html": recent_html,
    }


def evaluate_alerts(state):
    s28 = sessions_in_days(state, 28)
    if len(s28) < 6:
        return []

    s14_recent = [s for s in s28 if parse_iso(s["date"]) >= date.today() - timedelta(days=14)]
    s14_prev = [
        s
        for s in s28
        if date.today() - timedelta(days=28) <= parse_iso(s["date"]) < date.today() - timedelta(days=14)
    ]
    if len(s14_recent) < 3 or len(s14_prev) < 3:
        return []

    rec_correct = average([s["correctness"] for s in s14_recent])
    prev_correct = average([s["correctness"] for s in s14_prev])
    rec_latency = average([s["latency_seconds"] for s in s14_recent])
    prev_latency = average([s["latency_seconds"] for s in s14_prev])
    rec_social = average([100 if s["social_interaction"] else 0 for s in s14_recent])
    prev_social = average([100 if s["social_interaction"] else 0 for s in s14_prev])
    rec_orient = average([s["orientation_errors"] for s in s14_recent])
    prev_orient = average([s["orientation_errors"] for s in s14_prev])

    alerts = []
    from_date = min(s["date"] for s in s14_recent)

    soft_triggers = []
    if rec_correct <= prev_correct - 12:
        soft_triggers.append("menor rendimiento en ejercicios")
    if rec_social <= prev_social - 25:
        soft_triggers.append("menos interacción social")
    if rec_latency >= prev_latency + 18:
        soft_triggers.append("mayor latencia de respuesta")

    if soft_triggers:
        alerts.append(
            {
                "level": "suave",
                "from_date": from_date,
                "what_changed": ", ".join(soft_triggers),
                "recommendation": "Realizar una llamada y reforzar rutina diaria durante 1-2 semanas.",
            }
        )

    priority_flags = 0
    reasons = []
    if rec_correct <= prev_correct - 20:
        priority_flags += 1
        reasons.append("descenso notable de rendimiento")
    if rec_social <= prev_social - 35:
        priority_flags += 1
        reasons.append("aislamiento creciente")
    if rec_orient >= prev_orient + 1.2:
        priority_flags += 1
        reasons.append("más señales de desorientación")

    if priority_flags >= 2:
        alerts.append(
            {
                "level": "prioritario",
                "from_date": from_date,
                "what_changed": ", ".join(reasons),
                "recommendation": "Programar visita y consultar profesional de salud si persiste otra semana.",
            }
        )

    return alerts

