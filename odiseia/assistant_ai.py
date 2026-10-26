import io
import os
from datetime import date
from pathlib import Path


def _load_env_from_root():
    root = Path(__file__).resolve().parents[1]
    env_file = root / ".env"
    if not env_file.exists():
        return

    lines = env_file.read_text(encoding="utf-8").splitlines()
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.lower().startswith("export "):
            key = key[7:]
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value:
            os.environ[key] = value

    # Backward compatibility: .env with only the key in one line
    if not os.getenv("OPENAI_API_KEY", "").strip():
        for raw_line in lines:
            line = raw_line.strip().strip('"').strip("'")
            if line.startswith("sk-"):
                os.environ["OPENAI_API_KEY"] = line
                break


class AssistantAI:
    def __init__(self):
        _load_env_from_root()
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.text_model = os.getenv("ODISEIA_TEXT_MODEL", "gpt-4o")
        self.tts_model = os.getenv("ODISEIA_TTS_MODEL", "gpt-4o-mini-tts")
        self.tts_voice = os.getenv("ODISEIA_TTS_VOICE", "alloy")
        self.stt_model = os.getenv("ODISEIA_STT_MODEL", "whisper-1")
        self.last_error = None

    def _client(self):
        if not self.api_key:
            self.last_error = "OPENAI_API_KEY no configurada"
            return None
        try:
            from openai import OpenAI
        except Exception:
            self.last_error = "Paquete 'openai' no disponible"
            return None
        self.last_error = None
        return OpenAI(api_key=self.api_key)

    def status(self):
        return {"configured": bool(self.api_key), "error": self.last_error}

    def _fallback_reply(self, user_text, profile, mood):
        name = profile.get("name", "amigo")
        text = (user_text or "").strip().lower()
        if "como te llamas" in text or "quien eres" in text:
            return "Soy tu asistente de Odiseia. Estoy aqui para acompanarte y conversar contigo."

        base = f"{name}, gracias por compartirlo. "
        if mood <= 2:
            base += "Si quieres, hoy vamos suave: una pausa corta y una conversacion tranquila con alguien de confianza."
        else:
            base += "Si te apetece, podemos planear una actividad breve para hoy que te haga sentir bien."
        if user_text:
            base += f" Me quedo con esto que dijiste: '{user_text[:80]}'."
        return base

    def _build_chat_input(self, user_text, profile, mood, social_today, history):
        social_hint = "Ya tuvo interaccion social hoy." if social_today else "No tuvo interaccion social hoy."
        system = (
            "Eres un asistente para personas mayores. "
            "Habla en espanol natural, cercano y respetuoso, sin sonar robotico ni repetitivo. "
            "Primero responde directamente a lo que pregunta la persona. "
            "Solo propone una accion concreta cuando aporte valor real al mensaje. "
            "No repitas siempre llamada/paseo/mensaje; varia el lenguaje y las sugerencias. "
            "No diagnostiques ni des instrucciones medicas."
        )

        context = [
            f"Fecha: {date.today().isoformat()}",
            f"Perfil: {profile}",
            f"Estado de animo reportado: {mood}/5",
            social_hint,
            "Responde en maximo 90 palabras.",
            "Si la persona hace una pregunta concreta (por ejemplo: 'como te llamas'), respondela de forma directa.",
        ]

        chat_input = [{"role": "system", "content": system}]
        for item in (history or [])[-6:]:
            role = str(item.get("role", "")).strip().lower()
            content = str(item.get("content", "")).strip()
            if role in {"user", "assistant"} and content:
                chat_input.append({"role": role, "content": content[:500]})

        chat_input.append(
            {
                "role": "user",
                "content": f"{chr(10).join(context)}\nMensaje actual: {user_text}",
            }
        )
        return chat_input

    def reply(self, user_text, profile, mood, social_today, history=None):
        client = self._client()
        if client is None:
            return self._fallback_reply(user_text, profile, mood), {
                "used_llm": False,
                "configured": bool(self.api_key),
                "error": self.last_error,
            }

        try:
            chat_input = self._build_chat_input(user_text, profile, mood, social_today, history)
            resp = client.responses.create(
                model=self.text_model,
                temperature=0.8,
                input=chat_input,
            )
            text = getattr(resp, "output_text", None)
            if text:
                self.last_error = None
                return text.strip(), {"used_llm": True, "configured": True, "error": None}
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"

        return self._fallback_reply(user_text, profile, mood), {
            "used_llm": False,
            "configured": bool(self.api_key),
            "error": self.last_error,
        }

    def transcribe(self, audio_bytes):
        client = self._client()
        if client is None or not audio_bytes:
            return None

        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"
            out = client.audio.transcriptions.create(model=self.stt_model, file=audio_file)
            return getattr(out, "text", None)
        except Exception:
            return None

    def synthesize(self, text):
        client = self._client()
        if client is None or not text:
            return None

        try:
            result = client.audio.speech.create(model=self.tts_model, voice=self.tts_voice, input=text[:1000])
            return result.content
        except Exception:
            return None
