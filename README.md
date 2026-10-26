# LÚMINA (Odiseia)

Prototipo desarrollado en equipo para el hackathon **OdiseIA4Good 2026**, cuyo reto era aplicar la IA a colectivos vulnerables.

## Equipo

Proyecto de cinco personas: cuatro estudiantes de Ciencia de Datos e IA de UDIT y un desarrollador full-stack. Miguel Canals se encargó de la mayor parte del desarrollo técnico y el perfil full-stack implementó uno de los módulos. Gracias a todo el equipo por el trabajo.

## Qué hace

App web para el acompañamiento cognitivo diario de personas mayores, con:

- Sesión autónoma guiada (check-in emocional, social, ejercicio, cierre)
- Conversación asistida por LLM (con fallback local si no hay API key)
- Voz en navegador (dictado y lectura de respuestas, si el navegador lo soporta)
- Panel de farmacia para recordatorios de toma, control de stock y recargas
- Catálogo de juegos cognitivos adaptativos:
  - `Memoria de palabras`
  - `Números al revés`
  - `Torpedo de categorías`
  - `Sudoku 4x4`
  - `Crucigrama rápido`
  - `Sopa de letras`
- Ejercicios cognitivos adaptativos por dominio
- Personalización por preferencias e historial
- Monitorización preventiva de tendencias (sin diagnóstico)
- Alertas para cuidador: `suave` y `prioritario`

## 1) Requisitos

- Python 3.10+

## 2) Arranque rápido

```bash
python scripts/seed_demo_data.py
python app.py
```

Abrir: `http://127.0.0.1:8001`

### Arranque en Windows (doble clic)

- Local: ejecuta `run_odiseia_LOCAL.bat`
- Online (URL pública): ejecuta `run_odiseia_ONLINE.bat`
- Los `.bat` auxiliares están en `scripts\internal_bat` para no ensuciar la raíz.
- El script usa `data/state.json` existente (si no existe, crea demo inicial)
- Si hay un fallo, deja detalle en `data/server.log`
- Si el puerto 8001 queda ocupado, ejecuta `scripts\internal_bat\stop_odiseia.bat` y vuelve a iniciar

Variables opcionales:

- `OPENAI_API_KEY`: activa LLM real en backend
- `ODISEIA_TEXT_MODEL` (default `gpt-4o`)
- `ODISEIA_STT_MODEL` (default `whisper-1`)
- `ODISEIA_TTS_MODEL` (default `gpt-4o-mini-tts`)
- `ODISEIA_TTS_VOICE` (default `alloy`)

## 3) Flujo de demo recomendado

1. Abrir la pantalla principal y mostrar ejercicio elegido automáticamente.
2. Hacer una mini conversación en el bloque de asistente.
3. Ejecutar el juego de memoria y guardar sesión.
4. Mostrar panel familiar con métricas y alertas.

## 4) Lógica principal implementada

- Rotación de dominios para evitar fatiga: `memoria -> atencion -> lenguaje -> ejecutiva -> orientacion`
- Rotación de juegos para evitar monotonía: `memory_words -> reverse_digits -> category_sprint`
- Adaptación de nivel por dominio:
  - Subida: 3 sesiones seguidas fáciles (`correctness >= 85` y frustración baja)
  - Bajada: 2 sesiones difíciles (`correctness <= 55`) o frustración alta
- Adaptación de nivel por juego:
  - Subida: 3 resultados seguidos exitosos (>=80%)
  - Bajada: 2 resultados seguidos no exitosos
- Recogida de métricas de juego:
  - `score`, `max_score`, `success`, `response_seconds`, `hints_used`, `difficulty`
- Ajuste automático de parámetros de interfaz (últimos 7 días):
  - `large_text_default`
  - `high_contrast_default`
  - `suggested_session_minutes`
- Alertas por ventanas de 14 días comparadas contra 14 días previos (total 28 días)
  - Suave: cambios moderados en rendimiento/social/latencia
  - Prioritario: combinación de al menos 2 señales fuertes (rendimiento, aislamiento, orientación)

## 5) Estructura

- `app.py`: backend API + servidor de frontend propio
- `web/index.html`: interfaz principal
- `web/style.css`: diseño visual
- `web/app.js`: lógica cliente (chat, juego, recomendaciones, panel)
- `odiseia/engine.py`: reglas de personalización, analítica y alertas
- `odiseia/assistant_ai.py`: integración LLM/voz y fallback
- `odiseia/storage.py`: persistencia robusta de estado
- `scripts/seed_demo_data.py`: genera dataset demo en `data/state.json`
- `data/state.json`: estado persistente (se crea automáticamente)

## 6) Privacidad por diseño (MVP)

- Persistencia local en JSON (sin envío a terceros)
- Campos mínimos para analítica
- Notas limitadas y opcionales
- Seguridad farmacológica: la app no calcula dosis por peso ni sustituye indicación médica

## 7) Siguientes mejoras sugeridas

- ASR/TTS para canal de voz real
- Exportar resumen semanal a PDF
- Multiusuario y autenticación para cuidadores
- Modo privado estricto (sin texto libre)

## 8) Hosting publico desde tu PC (localhost.run)

Si no quieres usar Railway, puedes publicar la app directamente desde tu ordenador.

### Opcion A: un click (recomendada)

1. Ejecuta `run_odiseia_ONLINE.bat`.
3. Mira la ventana `Odiseia Tunnel`: aparecerá una URL publica tipo:
   - `https://xxxxx.lhr.life`
4. El script también:
   - detecta la URL automáticamente,
   - la copia al portapapeles,
   - guarda `data/public_url.txt`,
   - genera y abre un QR en el navegador (`data/public_qr_url.txt`).
5. Comparte esa URL o el QR y la app quedará accesible mientras tu PC esté encendido.
6. Si localhost.run se cae temporalmente, el script reintenta automáticamente.

### Opcion B: comandos manuales

```bash
python app.py
cloudflared tunnel --url http://127.0.0.1:8001
```

### Notas importantes

- Si apagas el PC, la URL deja de funcionar.
- La URL de `trycloudflare.com` puede cambiar al reiniciar el túnel.
- Revisa seguridad básica antes de exponerla:
  - usa datos demo para presentaciones,
  - evita subir datos sensibles reales,
  - limita quién recibe la URL.

## 9) localhost.run con auto-reconnect y SSH key (opcional)

- El script `scripts/run_public_localhostrun.ps1` relanza el tunel automaticamente si se cae.
- Variables opcionales antes de arrancar:
  - `LOCALHOSTRUN_SSH_KEY`: ruta a tu clave privada SSH (para cuenta/subdominio reservado).
  - `LOCALHOSTRUN_SUBDOMAIN`: subdominio deseado (si tu cuenta de localhost.run lo permite).

Ejemplo en PowerShell:

```powershell
$env:LOCALHOSTRUN_SSH_KEY="C:\Users\Admin\.ssh\id_ed25519"
$env:LOCALHOSTRUN_SUBDOMAIN="lumina-demo"
.\run_odiseia_ONLINE.bat
```


## Configuración local y credenciales

No se incluyen claves, sesiones, conversaciones ni logs de ejecuciones anteriores. La aplicación crea `data/` al arrancar; el script `scripts/seed_demo_data.py` puede generar datos de demostración.

Configura las credenciales opcionales como variables de entorno del proceso. `.env.example` documenta sus nombres y no se carga automáticamente. Sin `OPENAI_API_KEY`, el asistente utiliza la respuesta local de reserva.

`GOOGLE_MAPS_API_KEY` se reserva al servidor. Para activar el mapa del navegador utiliza una clave distinta en `GOOGLE_MAPS_JS_API_KEY`, restringida por dominio y API en Google Cloud. Esa clave de navegador es pública por diseño.

No publiques `data/`, archivos `.env`, claves privadas ni compilados Python. Para continuar trabajando tras una limpieza del historial, clona de nuevo el repositorio; una copia antigua puede volver a introducir los archivos retirados.
