(function () {
  "use strict";

  const configBase = (window.ODISEIA_CONFIG && window.ODISEIA_CONFIG.API_BASE_URL) || window.ODISEIA_API_BASE_URL || "";
  const rawApiBase = String(configBase).trim().replace(/\/$/, "");
  const isPublicHost =
    location.hostname.endsWith(".trycloudflare.com") ||
    location.hostname.endsWith(".github.io") ||
    (location.hostname !== "localhost" && location.hostname !== "127.0.0.1");
  const pointsToLocal =
    rawApiBase.includes("localhost") || rawApiBase.includes("127.0.0.1") || rawApiBase.startsWith("http://192.168.");
  const API_BASE = isPublicHost && pointsToLocal ? "" : rawApiBase;

  const state = {
    exercise: null,
    alerts: [],
    gamePlan: null,
    llmEnabled: false,
    llmConfigured: false,
    lastAssistantText: "",
    listening: false,
    hasUserMessage: false,
    hasSavedSession: false,
    seniorMode: true,
    largeText: false,
    activeTab: "session",
    gameStartAt: Date.now(),
    lastGameResult: null,
    wordsVisible: true,
    cardsGame: null,
    reminderTimer: null,
    reminderAt: null,
    pharmacyData: null,
    medCountdownTimer: null,
    lastTakenReminder: null,
    dueNoticeSeen: {},
    appointmentNoticeSeen: {},
    appointmentNoticeDismissed: {},
    currentAppointmentNoticeKey: "",
    quedadasData: [],
    joinedQuedadas: [],
    nearbyEvents: [],
    nearbyCenter: null,
    nearbyGeo: { lat: null, lng: null },
    mapsConfig: null,
    mapInstance: null,
    mapMarkers: [],
    privacy: null,
    revealObserver: null,
    auth: {
      role: null,
      userName: "",
    },
  };

  const el = {};

  function byId(id) {
    return document.getElementById(id);
  }

  function bindElements() {
    [
      "loadingScreen",
      "llmState",
      "fontSizeBtn",
      "tabSessionBtn",
      "tabCaregiverBtn",
      "tabPharmacyBtn",
      "tabQuedadasBtn",
      "tabPrivacyBtn",
      "tabNav",
      "mainLayout",
      "landingView",
      "landingStartBtn",
      "authGate",
      "authRole",
      "authUserName",
      "authLoginBtn",
      "authError",
      "authConsentData",
      "authConsentShare",
      "newUserPrefs",
      "newUserEnergy",
      "newUserWeight",
      "newUserBirthYear",
      "newUserNotes",
      "createUserBtn",
      "activeContext",
      "switchUserBtn",
      "sessionView",
      "caregiverView",
      "pharmacyView",
      "quedadasView",
      "privacyView",
      "welcomeName",
      "prefTags",
      "sessionProgress",
      "progressText",
      "mood",
      "moodValue",
      "socialToday",
      "latencySeconds",
      "frustration",
      "orientationErrors",
      "engagementMinutes",
      "chatLog",
      "chatInput",
      "sendChatBtn",
      "voiceInputBtn",
      "speakBtn",
      "gameTitle",
      "gameInstruction",
      "gameDifficulty",
      "gameMemoryBox",
      "gameDigitsBox",
      "gameCategoryBox",
      "gameSudokuBox",
      "gameCrosswordBox",
      "gameWordsearchBox",
      "gameCardsBox",
      "memoryWords",
      "toggleWordsBtn",
      "memoryRecall",
      "digitsSequence",
      "digitsAnswer",
      "categoryName",
      "categoryTarget",
      "categoryAnswer",
      "sudokuGrid",
      "sudokuHelpText",
      "crosswordTheme",
      "crosswordList",
      "wordsearchTheme",
      "wordsearchGrid",
      "wordsearchWords",
      "wordsearchAnswer",
      "cardsGrid",
      "cardsMatched",
      "correctness",
      "helpRequested",
      "scoreMemoryBtn",
      "newMemoryBtn",
      "memoryScore",
      "socialIdeas",
      "notes",
      "saveSessionBtn",
      "exerciseDomain",
      "exerciseLevel",
      "exercisePrompt",
      "metricGrid",
      "alertsBox",
      "recentBody",
      "caregiverMedStatus",
      "caregiverMedCountdown",
      "pharmacyDoseNote",
      "pharmacyReminder",
      "pharmacyWeight",
      "pharmacyAdherence",
      "pharmacyPending",
      "pharmacyLowStock",
      "pharmacyRows",
      "medName",
      "medDose",
      "medTimes",
      "medFrequency",
      "medWeekday",
      "medStock",
      "medLow",
      "medPrescriber",
      "medWeight",
      "medNotes",
      "addMedBtn",
      "appointmentAlerts",
      "appointmentRows",
      "appointmentDate",
      "appointmentTime",
      "appointmentPlace",
      "appointmentNotes",
      "addAppointmentBtn",
      "medDueNotice",
      "medDueNoticeText",
      "medDueDismissBtn",
      "appointmentNotice",
      "appointmentNoticeText",
      "appointmentDismissBtn",
      "refreshBtn",
      "refreshQuedadasBtn",
      "quedadasContainer",
      "quedadaActivity",
      "quedadaPlace",
      "quedadaDate",
      "quedadaTime",
      "quedadaDescription",
      "addQuedadaBtn",
      "nearbyUseLocationBtn",
      "nearbyAddress",
      "nearbyDetectedAddress",
      "nearbyRadiusKm",
      "nearbyQuery",
      "searchNearbyBtn",
      "nearbyStatus",
      "nearbyMap",
      "nearbyResults",
      "privacyConsentData",
      "privacySharePlatform",
      "privacyAnonAnalytics",
      "savePrivacyBtn",
      "privacyStatus",
      "deleteAllDataBtn",
      "toast",
    ].forEach((id) => {
      el[id] = byId(id);
    });
    el.moodButtons = Array.from(document.querySelectorAll(".mood-btn"));
  }

  async function api(path, method = "GET", body = null) {
    const options = { method, headers: {} };
    if (state.auth.role && state.auth.userName) {
      options.headers["X-Odiseia-Role"] = state.auth.role;
      options.headers["X-Odiseia-User"] = state.auth.userName;
    }
    if (body !== null) {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }
    const target = API_BASE ? `${API_BASE}${path}` : path;
    const response = await fetch(target, options);
    const text = await response.text();
    let payload = {};
    try {
      payload = text ? JSON.parse(text) : {};
    } catch (err) {
      throw new Error("La respuesta no es JSON válido.");
    }
    if (!response.ok || payload.ok === false) {
      throw new Error(payload.error || "Error en API");
    }
    return payload;
  }

  function showToast(text) {
    el.toast.textContent = text;
    el.toast.classList.add("show");
    clearTimeout(showToast._timer);
    showToast._timer = setTimeout(() => el.toast.classList.remove("show"), 2400);
  }

  function hideLoadingScreen(delayMs = 700) {
    const wait = Math.max(0, Number(delayMs) || 0);
    setTimeout(() => {
      if (!el.loadingScreen) return;
      el.loadingScreen.classList.add("hidden");
    }, wait);
  }

  async function loadMapsConfig() {
    if (state.mapsConfig) return state.mapsConfig;
    try {
      const res = await api("/api/maps/config");
      state.mapsConfig = res || { enabled: false, js_api_key: "" };
    } catch (_) {
      state.mapsConfig = { enabled: false, js_api_key: "" };
    }
    return state.mapsConfig;
  }

  async function ensureGoogleMapsReady() {
    const cfg = await loadMapsConfig();
    const key = String((cfg && cfg.js_api_key) || "").trim();
    if (!key) return false;
    if (window.google && window.google.maps) return true;
    if (window.__luminaMapsLoading) return window.__luminaMapsLoading;
    window.__luminaMapsLoading = new Promise((resolve) => {
      const script = document.createElement("script");
      script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(key)}`;
      script.async = true;
      script.defer = true;
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.head.appendChild(script);
    });
    return window.__luminaMapsLoading;
  }

  async function renderNearbyMap() {
    if (!el.nearbyMap) return;
    const canUseMap = await ensureGoogleMapsReady();
    if (!canUseMap || !(window.google && window.google.maps)) {
      el.nearbyMap.innerHTML = "<p class='muted' style='padding:0.8rem'>Mapa no disponible (placeholder activo).</p>";
      return;
    }
    const center = state.nearbyCenter || { lat: 40.4168, lng: -3.7038 };
    if (!state.mapInstance) {
      state.mapInstance = new window.google.maps.Map(el.nearbyMap, {
        center,
        zoom: 13,
        mapTypeControl: false,
        streetViewControl: false,
      });
    } else {
      state.mapInstance.setCenter(center);
    }
    state.mapMarkers.forEach((m) => m.setMap(null));
    state.mapMarkers = [];
    (state.nearbyEvents || []).forEach((item) => {
      const lat = Number(item.lat);
      const lng = Number(item.lng);
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;
      const marker = new window.google.maps.Marker({
        map: state.mapInstance,
        position: { lat, lng },
        title: item.title || "Evento",
      });
      state.mapMarkers.push(marker);
    });
  }

  function markRevealTargets(root = document) {
    const scope = root && root.querySelectorAll ? root : document;
    const targets = scope.querySelectorAll(".card, .tab-btn, .status-pill, .alert-item, .metric, .quedada-card");
    let idx = 0;
    targets.forEach((node) => {
      if (!(node instanceof HTMLElement)) return;
      if (node.dataset.revealInit === "1") return;
      node.dataset.revealInit = "1";
      node.classList.add("reveal-on-load");
      node.style.transitionDelay = `${Math.min(260, idx * 35)}ms`;
      idx += 1;
      if (state.revealObserver) {
        state.revealObserver.observe(node);
      } else {
        requestAnimationFrame(() => node.classList.add("is-visible"));
      }
    });
  }

  function setupRevealAnimations() {
    if ("IntersectionObserver" in window) {
      state.revealObserver = new IntersectionObserver(
        (entries, obs) => {
          entries.forEach((entry) => {
            if (!entry.isIntersecting) return;
            entry.target.classList.add("is-visible");
            obs.unobserve(entry.target);
          });
        },
        { threshold: 0.1, rootMargin: "0px 0px -8% 0px" }
      );
    } else {
      state.revealObserver = null;
    }
    markRevealTargets(document);
  }

  function setLoading(button, loading, text = "Cargando...") {
    if (!button) return;
    if (loading) {
      button.dataset.original = button.textContent;
      button.textContent = text;
      button.disabled = true;
    } else {
      button.textContent = button.dataset.original || button.textContent;
      button.disabled = false;
    }
  }

  function setTab(tabName) {
    state.activeTab = tabName;
    const sessionActive = tabName === "session";
    const caregiverActive = tabName === "caregiver";
    const pharmacyActive = tabName === "pharmacy";
    const quedadasActive = tabName === "quedadas";
    const privacyActive = tabName === "privacy";
    el.tabSessionBtn.classList.toggle("active", sessionActive);
    el.tabCaregiverBtn.classList.toggle("active", caregiverActive);
    el.tabPharmacyBtn.classList.toggle("active", pharmacyActive);
    el.tabQuedadasBtn.classList.toggle("active", quedadasActive);
    el.tabPrivacyBtn.classList.toggle("active", privacyActive);
    el.sessionView.classList.toggle("hidden", !sessionActive);
    el.caregiverView.classList.toggle("hidden", !caregiverActive);
    el.pharmacyView.classList.toggle("hidden", !pharmacyActive);
    el.quedadasView.classList.toggle("hidden", !quedadasActive);
    el.privacyView.classList.toggle("hidden", !privacyActive);
    if (quedadasActive) {
      renderQuedadas();
    }
    markRevealTargets(document);
  }

  function normalizeUserName(value) {
    return String(value || "").trim().replace(/\s+/g, " ").slice(0, 80);
  }

  function getAllowedTabsForRole(role) {
    if (role === "caregiver") return ["caregiver", "pharmacy", "quedadas", "privacy"];
    return ["session", "pharmacy", "quedadas", "privacy"];
  }

  function applyRoleUi(role) {
    const allowed = getAllowedTabsForRole(role);
    el.tabSessionBtn.classList.toggle("hidden", !allowed.includes("session"));
    el.tabCaregiverBtn.classList.toggle("hidden", !allowed.includes("caregiver"));
    el.tabPharmacyBtn.classList.toggle("hidden", !allowed.includes("pharmacy"));
    el.tabQuedadasBtn.classList.toggle("hidden", !allowed.includes("quedadas"));
    el.tabPrivacyBtn.classList.toggle("hidden", !allowed.includes("privacy"));
    if (!allowed.includes(state.activeTab)) {
      setTab(allowed[0]);
    } else {
      setTab(state.activeTab);
    }
    const roleLabel = role === "caregiver" ? "Cuidador" : "Usuario";
    el.activeContext.textContent = `${roleLabel}: ${state.auth.userName || "-"}`;
  }

  function saveAuthToStorage() {
    try {
      localStorage.setItem("odiseia_auth", JSON.stringify(state.auth));
    } catch (_) {}
  }

  function readAuthFromStorage() {
    try {
      const raw = localStorage.getItem("odiseia_auth");
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      const role = parsed && parsed.role === "caregiver" ? "caregiver" : "user";
      const userName = normalizeUserName(parsed && parsed.userName);
      if (!userName) return null;
      return { role, userName };
    } catch (_) {
      return null;
    }
  }

  function clearAuth() {
    state.auth.role = null;
    state.auth.userName = "";
    state.appointmentNoticeDismissed = {};
    state.currentAppointmentNoticeKey = "";
    try {
      localStorage.removeItem("odiseia_auth");
    } catch (_) {}
  }

  function showLoginGate(errorText = "") {
    el.landingView.classList.add("hidden");
    el.authGate.classList.remove("hidden");
    el.tabNav.classList.add("hidden");
    el.mainLayout.classList.add("hidden");
    el.switchUserBtn.classList.add("hidden");
    el.activeContext.classList.add("hidden");
    el.authError.textContent = errorText || "";
  }

  function showLanding() {
    el.landingView.classList.remove("hidden");
    el.authGate.classList.add("hidden");
    el.tabNav.classList.add("hidden");
    el.mainLayout.classList.add("hidden");
    el.switchUserBtn.classList.add("hidden");
    el.activeContext.classList.add("hidden");
  }

  function renderPrivacy(privacy) {
    const safe = privacy || {};
    state.privacy = {
      consent_data_processing: !!safe.consent_data_processing,
      share_with_platform: !!safe.share_with_platform,
      allow_anon_analytics: !!safe.allow_anon_analytics,
      consent_updated_at: safe.consent_updated_at || null,
    };
    if (el.privacyConsentData) el.privacyConsentData.checked = state.privacy.consent_data_processing;
    if (el.privacySharePlatform) el.privacySharePlatform.checked = state.privacy.share_with_platform;
    if (el.privacyAnonAnalytics) el.privacyAnonAnalytics.checked = state.privacy.allow_anon_analytics;
    if (el.authConsentData) el.authConsentData.checked = state.privacy.consent_data_processing;
    if (el.authConsentShare) el.authConsentShare.checked = state.privacy.share_with_platform;

    if (!el.privacyStatus) return;
    if (state.privacy.consent_updated_at) {
      const dt = new Date(state.privacy.consent_updated_at);
      if (!Number.isNaN(dt.getTime())) {
        el.privacyStatus.textContent = `Actualizado: ${dt.toLocaleString("es-ES")}`;
        return;
      }
    }
    el.privacyStatus.textContent = "Sin confirmar";
  }

  function showAppShell() {
    el.landingView.classList.add("hidden");
    el.authGate.classList.add("hidden");
    el.tabNav.classList.remove("hidden");
    el.mainLayout.classList.remove("hidden");
    el.switchUserBtn.classList.remove("hidden");
    el.activeContext.classList.remove("hidden");
  }

  function appointmentDismissStorageKey() {
    return `odiseia_appointment_dismissed_${state.auth.userName || "anon"}`;
  }

  function readAppointmentDismissedMap() {
    try {
      const raw = localStorage.getItem(appointmentDismissStorageKey());
      if (!raw) return {};
      const parsed = JSON.parse(raw);
      return parsed && typeof parsed === "object" ? parsed : {};
    } catch (_) {
      return {};
    }
  }

  function saveAppointmentDismissedMap(map) {
    try {
      localStorage.setItem(appointmentDismissStorageKey(), JSON.stringify(map || {}));
    } catch (_) {}
  }

  function setAppointmentDismissed(key, value) {
    state.appointmentNoticeDismissed[key] = !!value;
    const map = readAppointmentDismissedMap();
    map[key] = !!value;
    saveAppointmentDismissedMap(map);
  }

  function isAppointmentDismissed(key) {
    if (state.appointmentNoticeDismissed[key]) return true;
    const map = readAppointmentDismissedMap();
    return !!map[key];
  }

  function buildAppointmentDismissKey(item) {
    return `${item.id}:${item.when}:${item.date || ""}:${item.time || ""}`;
  }

  function parseTodayTime(hhmm) {
    const parts = String(hhmm || "").split(":");
    if (parts.length !== 2) return null;
    const h = Number(parts[0]);
    const m = Number(parts[1]);
    if (!Number.isInteger(h) || !Number.isInteger(m) || h < 0 || h > 23 || m < 0 || m > 59) return null;
    const now = new Date();
    const out = new Date(now);
    out.setHours(h, m, 0, 0);
    return out;
  }

  function formatRemaining(ms) {
    const total = Math.max(0, Math.floor(ms / 1000));
    const h = Math.floor(total / 3600);
    const m = Math.floor((total % 3600) / 60);
    const s = total % 60;
    if (h > 0) return `${h}h ${m}m ${s}s`;
    return `${m}m ${s}s`;
  }

  function getNextPendingForMedication(med, now = new Date()) {
    const plan = (med && med.today_plan) || [];
    let next = null;
    for (const item of plan) {
      if (item.taken) continue;
      const when = parseTodayTime(item.time);
      if (!when) continue;
      if (!next || when < next.when) next = { time: item.time, when };
    }
    if (!next) return null;
    return {
      time: next.time,
      when: next.when,
      is_due: next.when.getTime() <= now.getTime(),
    };
  }

  function refreshMedicationButtons() {
    if (!state.pharmacyData) return;
    const now = new Date();
    (state.pharmacyData.medications || []).forEach((med) => {
      const btn = el.pharmacyRows.querySelector(`button.med-taken-btn[data-med-id="${med.id}"]`);
      if (!btn) return;
      const next = getNextPendingForMedication(med, now);
      btn.classList.remove("med-ok", "med-due");
      if (!next) {
        btn.classList.add("med-ok");
        btn.textContent = "Tomada";
        return;
      }
      btn.dataset.medTime = next.time;
      if (next.is_due) {
        btn.classList.add("med-due");
        btn.textContent = "Tomar ahora";
      } else {
        btn.classList.add("med-ok");
        btn.textContent = "Tomada";
      }
    });
  }

  function hideDueNotice() {
    el.medDueNotice.classList.add("hidden");
  }

  function showDueNotice(text) {
    el.medDueNoticeText.textContent = text;
    el.medDueNotice.classList.remove("hidden");
  }

  function hideAppointmentNotice() {
    state.currentAppointmentNoticeKey = "";
    el.appointmentNotice.classList.add("hidden");
  }

  function showAppointmentNotice(text, key = "") {
    el.appointmentNoticeText.textContent = text;
    state.currentAppointmentNoticeKey = key;
    el.appointmentNotice.classList.remove("hidden");
  }

  function checkDuePseudoNotification() {
    if (!state.pharmacyData) return;
    const pending = state.pharmacyData.pending_today || [];
    const now = new Date();
    let dueItem = null;

    pending.forEach((item) => {
      if (dueItem) return;
      const when = parseTodayTime(item.time);
      if (!when) return;
      if (when.getTime() <= now.getTime()) dueItem = item;
    });

    if (!dueItem) {
      hideDueNotice();
      return;
    }

    const key = `${new Date().toDateString()}::${dueItem.medication_id}::${dueItem.time}`;
    if (!state.dueNoticeSeen[key]) {
      showToast(`Es hora de tomar: ${dueItem.name} (${dueItem.time})`);
      state.dueNoticeSeen[key] = true;
    }
    showDueNotice(`Es hora de tomar ${dueItem.name} (${dueItem.time}).`);
  }

  function checkAppointmentNotifications() {
    if (!state.pharmacyData) return;
    const alerts = state.pharmacyData.appointment_alerts || [];
    if (!alerts.length) {
      hideAppointmentNotice();
      return;
    }

    const top = alerts[0];
    const whenText = top.when === "today" ? "Hoy" : "Mañana";
    const text = `${whenText} tienes cita médica a las ${top.time} en ${top.place}.`;
    const key = buildAppointmentDismissKey(top);
    if (!state.appointmentNoticeSeen[key]) {
      showToast(text);
      state.appointmentNoticeSeen[key] = true;
    }
    if (!isAppointmentDismissed(key)) {
      showAppointmentNotice(text, key);
    } else {
      hideAppointmentNotice();
    }
  }

  function renderAppointments(pharmacy) {
    const alerts = (pharmacy && pharmacy.appointment_alerts) || [];
    const rows = (pharmacy && pharmacy.appointments) || [];

    el.appointmentAlerts.innerHTML = "";
    if (!alerts.length) {
      const li = document.createElement("li");
      li.textContent = "Sin avisos de citas hoy.";
      el.appointmentAlerts.appendChild(li);
    } else {
      alerts.forEach((item) => {
        const li = document.createElement("li");
        const whenText = item.when === "today" ? "Hoy" : "Mañana";
        li.textContent = `${whenText}: ${item.time} - ${item.place}`;
        el.appointmentAlerts.appendChild(li);
      });
    }

    el.appointmentRows.innerHTML = "";
    if (!rows.length) {
      const tr = document.createElement("tr");
      tr.innerHTML = "<td colspan='4' class='table-empty'>Sin citas registradas.</td>";
      el.appointmentRows.appendChild(tr);
      return;
    }
    rows.forEach((item) => {
      const tr = document.createElement("tr");
      tr.innerHTML =
        `<td data-label='Fecha'>${item.date}</td>` +
        `<td data-label='Hora'>${item.time}</td>` +
        `<td data-label='Lugar'>${item.place}</td>` +
        `<td data-label='Notas'>${item.notes || "-"}</td>`;
      el.appointmentRows.appendChild(tr);
    });
  }

  function renderCaregiverMedicationReminder() {
    const pending = (state.pharmacyData && state.pharmacyData.pending_today) || [];
    const nextPendingItem = pending.length ? pending[0] : null;

    if (!state.lastTakenReminder) {
      if (nextPendingItem) {
        el.caregiverMedStatus.textContent = `Siguiente medicamento: ${nextPendingItem.name} (${nextPendingItem.time}).`;
      } else {
        el.caregiverMedStatus.textContent = "Aún no hay tomas registradas en esta sesión.";
      }
      el.caregiverMedCountdown.textContent = nextPendingItem
        ? "Pendiente de próxima toma"
        : "Sin cuenta atrás activa";
      return;
    }
    const now = new Date();
    const item = state.lastTakenReminder;
    if (!item.nextDue) {
      if (nextPendingItem) {
        el.caregiverMedStatus.textContent = `Tomada: ${item.name}. Siguiente medicamento: ${nextPendingItem.name} (${nextPendingItem.time}).`;
      } else {
        el.caregiverMedStatus.textContent = `Tomada: ${item.name}.`;
      }
      el.caregiverMedCountdown.textContent = "No quedan dosis para hoy.";
      return;
    }
    const diff = item.nextDue.getTime() - now.getTime();
    if (diff <= 0) {
      if (nextPendingItem) {
        el.caregiverMedStatus.textContent = `Pendiente: ${item.name}. Siguiente medicamento: ${nextPendingItem.name} (${nextPendingItem.time}).`;
      } else {
        el.caregiverMedStatus.textContent = `Pendiente: ${item.name}.`;
      }
      el.caregiverMedCountdown.textContent = "Ya toca la próxima toma.";
      return;
    }
    if (nextPendingItem) {
      el.caregiverMedStatus.textContent = `Tomada: ${item.name}. Siguiente medicamento: ${nextPendingItem.name} (${nextPendingItem.time}).`;
    } else {
      el.caregiverMedStatus.textContent = `Tomada: ${item.name}.`;
    }
    el.caregiverMedCountdown.textContent = `Próxima toma en ${formatRemaining(diff)} (a las ${item.nextTime})`;
  }

  function startMedicationUiTimer() {
    if (state.medCountdownTimer) {
      clearInterval(state.medCountdownTimer);
    }
    state.medCountdownTimer = setInterval(() => {
      renderCaregiverMedicationReminder();
      refreshMedicationButtons();
      checkDuePseudoNotification();
      checkAppointmentNotifications();
    }, 1000);
  }

  function schedulePharmacyReminder(pharmacy) {
    if (state.reminderTimer) {
      clearTimeout(state.reminderTimer);
      state.reminderTimer = null;
    }
    state.reminderAt = null;

    const pending = (pharmacy && pharmacy.pending_today) || [];
    const now = new Date();
    let next = null;
    pending.forEach((item) => {
      const when = parseTodayTime(item.time);
      if (!when) return;
      if (when <= now) return;
      if (!next || when < next.when) {
        next = { when, item };
      }
    });

    if (!next) {
      el.pharmacyReminder.textContent = "Sin recordatorios pendientes para hoy.";
      return;
    }

    state.reminderAt = next.when;
    el.pharmacyReminder.textContent = `Próximo recordatorio: ${next.item.name} a las ${next.item.time}`;

    const ms = Math.max(1000, next.when.getTime() - now.getTime());
    state.reminderTimer = setTimeout(() => {
      showToast(`Recordatorio de medicación: ${next.item.name} (${next.item.time})`);
      state.reminderTimer = null;
      schedulePharmacyReminder(pharmacy);
    }, ms);
  }

  function toggleLargeText() {
    state.largeText = !state.largeText;
    document.body.classList.toggle("large-text", state.largeText);
    el.fontSizeBtn.textContent = state.largeText ? "Letra normal" : "Letra grande";
  }

  function updateProgress() {
    let done = 0;
    if (Number(el.mood.value) >= 1) done += 1;
    if (state.hasUserMessage) done += 1;
    if (state.lastGameResult !== null) done += 1;
    if (state.hasSavedSession) done += 1;
    el.sessionProgress.value = done;
    el.progressText.textContent = `${done}/4 pasos`;
  }

  function metricItem(label, value) {
    const node = document.createElement("div");
    node.className = "metric";
    const small = document.createElement("div");
    small.className = "metric-label";
    small.textContent = label;
    const strong = document.createElement("div");
    strong.className = "metric-value";
    strong.textContent = String(value);
    node.appendChild(small);
    node.appendChild(strong);
    return node;
  }

  function renderSummary(summary) {
    el.metricGrid.innerHTML = "";
    el.metricGrid.appendChild(metricItem("Sesiones 28 días", summary.sessions_28d));
    el.metricGrid.appendChild(metricItem("Adherencia semanal", `${summary.weekly_adherence} días`));
    el.metricGrid.appendChild(metricItem("Ánimo medio", summary.avg_mood));
    el.metricGrid.appendChild(metricItem("Social", `${summary.social_rate}%`));
    el.metricGrid.appendChild(metricItem("Rendimiento", `${summary.avg_correctness}%`));
    el.metricGrid.appendChild(metricItem("Latencia", `${summary.avg_latency}s`));
    el.metricGrid.appendChild(metricItem("Puntaje juegos", `${summary.avg_game_score || 0}%`));
    markRevealTargets(el.metricGrid);
  }

  function renderAlerts(alerts) {
    const mergedAlerts = Array.isArray(alerts) ? alerts.slice() : [];
    const pending = (state.pharmacyData && state.pharmacyData.pending_today) || [];
    const now = new Date();
    const overdue = pending.find((item) => {
      const when = parseTodayTime(item.time);
      return !!when && when.getTime() <= now.getTime();
    });
    if (overdue) {
      mergedAlerts.unshift({
        level: "prioritario",
        from_date: new Date().toISOString().slice(0, 10),
        what_changed: `No se ha confirmado la toma de ${overdue.name} (${overdue.time}).`,
        recommendation: "Contactar con la persona y verificar la toma de medicación.",
      });
    }

    el.alertsBox.innerHTML = "";
    if (!mergedAlerts.length) {
      const empty = document.createElement("p");
      empty.className = "muted";
      empty.textContent = "Sin alertas activas.";
      el.alertsBox.appendChild(empty);
      return;
    }
    mergedAlerts.forEach((item) => {
      const block = document.createElement("div");
      block.className = `alert-item ${item.level}`;
      const top = document.createElement("strong");
      top.textContent = item.level.toUpperCase();
      const body = document.createElement("p");
      body.innerHTML = `Desde ${item.from_date}<br>${item.what_changed}<br><strong>Acción:</strong> ${item.recommendation}`;
      block.appendChild(top);
      block.appendChild(body);
      el.alertsBox.appendChild(block);
    });
    markRevealTargets(el.alertsBox);
  }

  function renderRecentSessions(rows) {
    el.recentBody.innerHTML = "";
    if (!rows || rows.length === 0) {
      const tr = document.createElement("tr");
      tr.innerHTML = "<td colspan='5'>Sin sesiones registradas.</td>";
      el.recentBody.appendChild(tr);
      return;
    }
    rows.forEach((s) => {
      const tr = document.createElement("tr");
      tr.innerHTML =
        `<td>${s.date}</td>` +
        `<td>${s.exercise_domain}</td>` +
        `<td>${s.correctness}%</td>` +
        `<td>${s.mood}</td>` +
        `<td>${s.latency_seconds}s</td>`;
      el.recentBody.appendChild(tr);
    });
  }

  function renderPharmacy(pharmacy) {
    if (!pharmacy) return;
    state.pharmacyData = pharmacy;
    el.pharmacyDoseNote.textContent = pharmacy.dose_note || "";
    el.pharmacyAdherence.textContent = `${Number(pharmacy.adherence_today || 0)}%`;
    el.pharmacyWeight.textContent = pharmacy.last_weight_kg ? `${pharmacy.last_weight_kg} kg` : "-";

    el.pharmacyPending.innerHTML = "";
    const pending = pharmacy.pending_today || [];
    if (!pending.length) {
      const li = document.createElement("li");
      li.textContent = "Sin tomas pendientes hoy.";
      el.pharmacyPending.appendChild(li);
    } else {
      pending.forEach((item) => {
        const li = document.createElement("li");
        li.textContent = `${item.time} - ${item.name}`;
        el.pharmacyPending.appendChild(li);
      });
    }

    el.pharmacyLowStock.innerHTML = "";
    const lows = pharmacy.low_stock || [];
    if (!lows.length) {
      const li = document.createElement("li");
      li.textContent = "Sin alertas de stock.";
      el.pharmacyLowStock.appendChild(li);
    } else {
      lows.forEach((item) => {
        const li = document.createElement("li");
        li.textContent = `${item.name}: quedan ${item.stock_units}`;
        el.pharmacyLowStock.appendChild(li);
      });
    }

    el.pharmacyRows.innerHTML = "";
    const meds = pharmacy.medications || [];
    if (!meds.length) {
      const tr = document.createElement("tr");
      tr.innerHTML = "<td colspan='5' class='table-empty'>Sin medicación registrada.</td>";
      el.pharmacyRows.appendChild(tr);
      return;
    }
    meds.forEach((med) => {
      const nextPending = getNextPendingForMedication(med, new Date());
      const nextTime = nextPending ? nextPending.time : (med.times || [])[0] || "08:00";
      const dueClass = nextPending && nextPending.is_due ? "med-due" : "med-ok";
      const btnLabel = nextPending && nextPending.is_due ? "Tomar ahora" : "Tomada";
      const tr = document.createElement("tr");
      tr.innerHTML =
        `<td data-label='Medicamento'>${med.name}</td>` +
        `<td data-label='Dosis'>${med.dose_text || "-"}</td>` +
        `<td data-label='Horarios'>${(med.times || []).join(", ") || "-"}<br><small>${med.frequency_label || "Diario"}</small></td>` +
        `<td data-label='Stock'>${med.stock_units}</td>` +
        "<td data-label='Acciones'>" +
        `<div class='pharmacy-actions'>` +
        `<button type='button' class='btn-soft med-taken-btn ${dueClass}' data-med-id='${med.id}' data-med-time='${nextTime}'>${btnLabel}</button>` +
        `<input type='number' min='1' max='5000' value='10' data-refill-input='${med.id}' />` +
        `<button type='button' class='btn-secondary med-refill-btn' data-med-id='${med.id}'>Recargar</button>` +
        `</div>` +
        "</td>";
      el.pharmacyRows.appendChild(tr);
    });
    schedulePharmacyReminder(pharmacy);
    refreshMedicationButtons();
    renderCaregiverMedicationReminder();
    checkDuePseudoNotification();
    renderAppointments(pharmacy);
    checkAppointmentNotifications();
    renderAlerts(state.alerts);
  }

  function renderProfile(profile) {
    el.welcomeName.textContent = `Hola, ${profile.name}`;
    el.prefTags.innerHTML = "";
    (profile.preferences || []).forEach((pref) => {
      const chip = document.createElement("span");
      chip.className = "tag";
      chip.textContent = pref;
      el.prefTags.appendChild(chip);
    });
  }

  function renderExercise(exercise) {
    state.exercise = exercise;
    el.exerciseDomain.textContent = exercise.domain;
    el.exerciseLevel.textContent = exercise.difficulty;
    el.exercisePrompt.textContent = exercise.prompt;
  }

  function addBubble(role, text) {
    const bubble = document.createElement("div");
    bubble.className = `bubble ${role}`;
    bubble.textContent = text;
    el.chatLog.appendChild(bubble);
    el.chatLog.scrollTop = el.chatLog.scrollHeight;
    if (role === "assistant") {
      state.lastAssistantText = text;
    }
  }

  function setLlmState(enabled, configured = false) {
    state.llmEnabled = !!enabled;
    state.llmConfigured = !!configured;
    if (state.llmEnabled) {
      el.llmState.textContent = "Asistente: IA activa";
      el.llmState.style.borderColor = "#72b39b";
    } else if (state.llmConfigured) {
      el.llmState.textContent = "Asistente: modo local (fallo IA)";
      el.llmState.style.borderColor = "#d98f8f";
    } else {
      el.llmState.textContent = "Asistente: modo local";
      el.llmState.style.borderColor = "#d3b594";
    }
  }

  function recommendationList(mood, socialToday) {
    const out = [];
    if (!socialToday) {
      out.push("Enviar un saludo por mensaje a una persona cercana.");
      out.push("Dar un paseo de 15 minutos por el parque.");
    } else {
      out.push("Repetir una llamada breve por la tarde.");
    }
    if (mood <= 2) {
      out.push("Plan suave: música tranquila y conversación corta.");
    } else if (mood >= 4) {
      out.push("Aprovechar energía alta con actividad fuera de casa.");
    }
    out.push("Tomar agua y preparar una actividad agradable para mañana.");
    return out;
  }

  function updateSocialIdeas() {
    const mood = Number(el.mood.value);
    const social = el.socialToday.value === "true";
    const items = recommendationList(mood, social);
    el.socialIdeas.innerHTML = "";
    items.forEach((idea) => {
      const li = document.createElement("li");
      li.textContent = idea;
      el.socialIdeas.appendChild(li);
    });
  }

  function setMood(value) {
    const mood = Math.max(1, Math.min(5, Number(value) || 3));
    el.mood.value = String(mood);
    el.moodValue.textContent = `Ánimo: ${mood}/5`;
    el.moodButtons.forEach((btn) => {
      btn.classList.toggle("active", Number(btn.dataset.mood) === mood);
    });
    updateSocialIdeas();
    updateProgress();
  }

  function normalizeToken(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]/g, "");
  }

  function renderSudoku(plan) {
    const puzzle = (plan.payload && plan.payload.puzzle) || [];
    const size = Math.max(1, puzzle.length || 4);
    el.sudokuGrid.innerHTML = "";
    el.sudokuGrid.style.gridTemplateColumns = `repeat(${size}, 1fr)`;
    el.sudokuGrid.style.maxWidth = `${Math.max(280, size * 64)}px`;
    if (el.sudokuHelpText) {
      el.sudokuHelpText.textContent = `Completa los espacios vacíos con números del 1 al ${size}.`;
    }
    for (let r = 0; r < puzzle.length; r += 1) {
      for (let c = 0; c < puzzle[r].length; c += 1) {
        const cell = document.createElement("div");
        cell.className = "sudoku-cell";
        const value = Number(puzzle[r][c] || 0);
        if (value >= 1) {
          cell.classList.add("given");
          cell.textContent = String(value);
        } else {
          const input = document.createElement("input");
          input.type = "text";
          input.maxLength = 1;
          input.inputMode = "numeric";
          input.setAttribute("aria-label", `Fila ${r + 1}, columna ${c + 1}`);
          input.dataset.row = String(r);
          input.dataset.col = String(c);
          input.addEventListener("input", () => {
            const maxDigit = Math.min(9, size);
            const allowed = new RegExp(`[^1-${maxDigit}]`, "g");
            input.value = input.value.replace(allowed, "");
          });
          cell.appendChild(input);
        }
        el.sudokuGrid.appendChild(cell);
      }
    }
  }

  function renderCrossword(plan) {
    const entries = (plan.payload && plan.payload.entries) || [];
    el.crosswordTheme.textContent = plan.payload.theme || "Crucigrama";
    el.crosswordList.innerHTML = "";
    entries.forEach((entry, idx) => {
      const wrap = document.createElement("div");
      wrap.className = "crossword-item";
      const label = document.createElement("label");
      label.textContent = `${idx + 1}. ${entry.clue}`;
      const input = document.createElement("input");
      input.type = "text";
      input.placeholder = "Escribe la palabra";
      input.dataset.cwIndex = String(idx);
      wrap.appendChild(label);
      wrap.appendChild(input);
      el.crosswordList.appendChild(wrap);
    });
  }

  function renderWordSearch(plan) {
    const rows = (plan.payload && plan.payload.grid) || [];
    const words = (plan.payload && plan.payload.words) || [];
    el.wordsearchTheme.textContent = plan.payload.theme || "Sopa de letras";
    el.wordsearchGrid.textContent = rows.join("\n");
    el.wordsearchWords.textContent = words.join(", ");
    el.wordsearchAnswer.value = "";
  }

  function updateCardsMatchedLabel() {
    const matchedPairs = state.cardsGame ? Math.floor(state.cardsGame.matched.size / 2) : 0;
    el.cardsMatched.textContent = String(matchedPairs);
  }

  function renderCardsBoard() {
    if (!state.cardsGame) return;
    el.cardsGrid.innerHTML = "";
    state.cardsGame.cards.forEach((value, idx) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "memory-card";
      btn.dataset.idx = String(idx);
      if (state.cardsGame.matched.has(idx)) btn.classList.add("matched");
      if (state.cardsGame.revealed.includes(idx)) btn.classList.add("revealed");
      if (state.cardsGame.matched.has(idx) || state.cardsGame.locked) btn.disabled = true;
      btn.innerHTML =
        `<span class="card-face card-front">?</span>` +
        `<span class="card-face card-back">${value}</span>`;
      btn.addEventListener("click", () => onCardClick(idx));
      el.cardsGrid.appendChild(btn);
    });
    updateCardsMatchedLabel();
  }

  function onCardClick(idx) {
    if (!state.cardsGame || state.gamePlan.id !== "memory_cards") return;
    if (state.cardsGame.locked) return;
    if (state.cardsGame.matched.has(idx)) return;
    if (state.cardsGame.revealed.includes(idx)) return;

    state.cardsGame.revealed.push(idx);
    renderCardsBoard();
    if (state.cardsGame.revealed.length < 2) return;

    const [a, b] = state.cardsGame.revealed;
    const same = state.cardsGame.cards[a] === state.cardsGame.cards[b];
    if (same) {
      state.cardsGame.matched.add(a);
      state.cardsGame.matched.add(b);
      state.cardsGame.revealed = [];
      state.cardsGame.moves += 1;
      renderCardsBoard();
      if (state.cardsGame.matched.size === state.cardsGame.cards.length) {
        showToast("¡Todas las parejas encontradas!");
      }
      return;
    }

    state.cardsGame.locked = true;
    state.cardsGame.moves += 1;
    setTimeout(() => {
      if (!state.cardsGame) return;
      state.cardsGame.revealed = [];
      state.cardsGame.locked = false;
      renderCardsBoard();
    }, 700);
  }

  function renderMemoryCards(plan) {
    const cards = (plan.payload && plan.payload.cards) || [];
    state.cardsGame = {
      cards: cards.slice(),
      revealed: [],
      matched: new Set(),
      moves: 0,
      locked: false,
    };
    renderCardsBoard();
  }

  function setMemoryWordsVisibility() {
    if (!state.gamePlan || state.gamePlan.id !== "memory_words") return;
    const words = (state.gamePlan.payload && state.gamePlan.payload.words) || [];
    el.memoryWords.textContent = state.wordsVisible ? words.join(", ") : "••••";
    el.memoryRecall.disabled = state.wordsVisible;
    if (state.wordsVisible) {
      el.memoryRecall.placeholder = "Oculta las palabras para poder escribir.";
    } else {
      el.memoryRecall.placeholder = "ej. parque, tren, lluvia, cafe";
      el.memoryRecall.focus();
    }
  }

  function renderGamePlan(plan) {
    state.gamePlan = plan;
    state.gameStartAt = Date.now();
    state.lastGameResult = null;
    updateProgress();
    el.memoryScore.textContent = "0/0";

    el.gameTitle.textContent = `Juego: ${plan.name}`;
    el.gameInstruction.textContent = plan.instructions;
    el.gameDifficulty.textContent = String(plan.difficulty);

    el.gameMemoryBox.classList.add("hidden");
    el.gameDigitsBox.classList.add("hidden");
    el.gameCategoryBox.classList.add("hidden");
    el.gameSudokuBox.classList.add("hidden");
    el.gameCrosswordBox.classList.add("hidden");
    el.gameWordsearchBox.classList.add("hidden");
    el.gameCardsBox.classList.add("hidden");

    if (plan.id === "memory_words") {
      el.gameMemoryBox.classList.remove("hidden");
      el.memoryRecall.value = "";
      state.wordsVisible = true;
      setMemoryWordsVisibility();
    } else if (plan.id === "reverse_digits") {
      el.gameDigitsBox.classList.remove("hidden");
      el.digitsSequence.textContent = plan.payload.sequence || "";
      el.digitsAnswer.value = "";
    } else if (plan.id === "category_sprint") {
      el.gameCategoryBox.classList.remove("hidden");
      el.categoryName.textContent = plan.payload.category || "categoría";
      el.categoryTarget.textContent = String(plan.payload.target_count || 4);
      el.categoryAnswer.value = "";
    } else if (plan.id === "sudoku_4x4") {
      el.gameSudokuBox.classList.remove("hidden");
      renderSudoku(plan);
    } else if (plan.id === "crossword_mini") {
      el.gameCrosswordBox.classList.remove("hidden");
      renderCrossword(plan);
    } else if (plan.id === "word_search") {
      el.gameWordsearchBox.classList.remove("hidden");
      renderWordSearch(plan);
    } else if (plan.id === "memory_cards") {
      el.gameCardsBox.classList.remove("hidden");
      renderMemoryCards(plan);
    }
  }

  function evaluateCurrentGame() {
    if (!state.gamePlan) {
      showToast("Aún no hay juego cargado.");
      return;
    }
    const plan = state.gamePlan;
    const responseSeconds = Math.round((Date.now() - state.gameStartAt) / 1000);
    let score = 0;
    let maxScore = Number(plan.payload.max_score || 1);

    if (plan.id === "memory_words") {
      if (state.wordsVisible) {
        showToast("Primero oculta las palabras para poder responder.");
        return;
      }
      const given = el.memoryRecall.value
        .split(",")
        .map((w) => normalizeToken(w))
        .filter(Boolean);
      const expected = new Set((plan.payload.words || []).map((w) => normalizeToken(w)));
      given.forEach((word) => {
        if (expected.has(word)) {
          score += 1;
          expected.delete(word);
        }
      });
    } else if (plan.id === "reverse_digits") {
      const ans = el.digitsAnswer.value.replace(/\s+/g, "");
      const reversed = String(plan.payload.sequence || "").split("").reverse().join("");
      let hits = 0;
      for (let i = 0; i < Math.min(ans.length, reversed.length); i += 1) {
        if (ans[i] === reversed[i]) hits += 1;
      }
      score = hits;
      maxScore = reversed.length || 1;
    } else if (plan.id === "category_sprint") {
      const words = el.categoryAnswer.value
        .split(",")
        .map((w) => normalizeToken(w))
        .filter(Boolean);
      const unique = new Set(words);
      score = Math.min(unique.size, maxScore);
    } else if (plan.id === "sudoku_4x4") {
      const solution = (plan.payload && plan.payload.solution) || [];
      const inputs = Array.from(el.sudokuGrid.querySelectorAll("input[data-row][data-col]"));
      inputs.forEach((input) => {
        input.classList.remove("sudoku-ok", "sudoku-bad");
        const r = Number(input.dataset.row);
        const c = Number(input.dataset.col);
        const expected = Number((solution[r] || [])[c] || 0);
        const got = Number(input.value || 0);
        if (got >= 1 && got === expected) {
          score += 1;
          input.classList.add("sudoku-ok");
        } else if (got >= 1) {
          input.classList.add("sudoku-bad");
        }
      });
      maxScore = inputs.length || 1;
    } else if (plan.id === "crossword_mini") {
      const entries = (plan.payload && plan.payload.entries) || [];
      entries.forEach((entry, idx) => {
        const input = el.crosswordList.querySelector(`input[data-cw-index="${idx}"]`);
        if (!input) return;
        if (normalizeToken(input.value) === normalizeToken(entry.answer)) score += 1;
      });
      maxScore = entries.length || 1;
    } else if (plan.id === "word_search") {
      const expected = new Set(((plan.payload && plan.payload.words) || []).map((w) => normalizeToken(w)));
      const given = new Set(
        el.wordsearchAnswer.value
          .split(",")
          .map((w) => normalizeToken(w))
          .filter(Boolean)
      );
      given.forEach((w) => {
        if (expected.has(w)) score += 1;
      });
      maxScore = expected.size || 1;
    } else if (plan.id === "memory_cards") {
      const matchedPairs = state.cardsGame ? Math.floor(state.cardsGame.matched.size / 2) : 0;
      score = matchedPairs;
      maxScore = Number(plan.payload.pairs || plan.payload.max_score || 1);
    }

    const success = score / Math.max(1, maxScore) >= 0.8;
    state.lastGameResult = {
      id: plan.id,
      difficulty: Number(plan.difficulty || 1),
      score,
      max_score: maxScore,
      success,
      response_seconds: responseSeconds,
      hints_used: plan.id === "memory_words" && state.wordsVisible ? 1 : 0,
    };
    el.memoryScore.textContent = `${score}/${maxScore}`;
    el.correctness.value = String(Math.round((score / Math.max(1, maxScore)) * 100));
    showToast(success ? "Muy bien. Juego completado." : "Buen intento. Repetimos mañana.");
    if (score >= maxScore && maxScore > 0) {
      api("/api/game/result", "POST", { game_result: state.lastGameResult }).catch(() => {});
    }
    updateProgress();
  }

  async function sendChat() {
    const message = el.chatInput.value.trim();
    if (!message) {
      showToast("Escribe o dicta un mensaje primero.");
      return;
    }
    addBubble("user", message);
    el.chatInput.value = "";
    state.hasUserMessage = true;
    updateProgress();
    setLoading(el.sendChatBtn, true, "Pensando...");
    try {
      const res = await api("/api/chat", "POST", {
        message,
        mood: Number(el.mood.value),
        social_today: el.socialToday.value === "true",
      });
      setLlmState(res.llm_enabled, res.llm_configured);
      if (!res.llm_enabled && res.llm_configured && res.llm_error) {
        showToast(`IA en fallback: ${res.llm_error}`);
      }
      addBubble("assistant", res.reply);
    } catch (err) {
      addBubble("assistant", "No pude responder ahora. Probemos con una frase más corta.");
      showToast(err.message);
    } finally {
      setLoading(el.sendChatBtn, false);
    }
  }

  function speakLastAssistant() {
    if (!state.lastAssistantText) {
      showToast("Aún no hay respuesta del asistente.");
      return;
    }
    if (!("speechSynthesis" in window)) {
      showToast("Tu navegador no soporta salida de voz.");
      return;
    }
    window.speechSynthesis.cancel();
    const utt = new SpeechSynthesisUtterance(state.lastAssistantText);
    utt.lang = "es-ES";
    utt.rate = 0.92;
    window.speechSynthesis.speak(utt);
  }

  function setupVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      el.voiceInputBtn.disabled = true;
      el.voiceInputBtn.textContent = "Voz no disponible (navegador)";
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "es-ES";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      state.listening = true;
      el.voiceInputBtn.textContent = "Escuchando...";
    };
    recognition.onend = () => {
      state.listening = false;
      el.voiceInputBtn.textContent = "Hablar";
    };
    recognition.onerror = () => {
      state.listening = false;
      el.voiceInputBtn.textContent = "Hablar";
      showToast("No se pudo capturar la voz.");
    };
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript || "";
      el.chatInput.value = transcript;
      showToast("Texto dictado cargado.");
    };

    el.voiceInputBtn.addEventListener("click", () => {
      if (state.listening) {
        recognition.stop();
        return;
      }
      recognition.start();
    });
  }

  function payloadFromForm() {
    return {
      mood: Number(el.mood.value),
      social_interaction: el.socialToday.value === "true",
      latency_seconds: Number(el.latencySeconds.value),
      frustration: el.frustration.value,
      orientation_errors: Number(el.orientationErrors.value),
      engagement_minutes: Number(el.engagementMinutes.value),
      correctness: Number(el.correctness.value),
      help_requested: Number(el.helpRequested.value),
      notes: el.notes.value,
      exercise_domain: state.exercise ? state.exercise.domain : "memoria",
      exercise_id: state.exercise ? state.exercise.id : "manual",
      difficulty: state.exercise ? Number(state.exercise.difficulty) : 2,
      game_result: state.lastGameResult,
    };
  }

  function updateMedFrequencyUi() {
    const weekly = el.medFrequency.value === "weekly";
    el.medWeekday.disabled = !weekly;
  }

  async function saveSession() {
    if (!state.lastGameResult) {
      showToast("Primero completa el juego del paso 3.");
      return;
    }
    setLoading(el.saveSessionBtn, true, "Guardando...");
    try {
      const res = await api("/api/session", "POST", payloadFromForm());
      hydrate(res.data);
      el.notes.value = "";
      state.hasSavedSession = true;
      updateProgress();
      showToast("Sesión guardada. Muy buen trabajo hoy.");
      setTab(state.auth.role === "caregiver" ? "caregiver" : "pharmacy");
    } catch (err) {
      showToast(err.message);
    } finally {
      setLoading(el.saveSessionBtn, false);
    }
  }

  function applyUiParams(uiParams) {
    if (!uiParams) return;
    state.seniorMode = true;
    state.largeText = !!uiParams.large_text_default;
    document.body.classList.add("senior-mode");
    document.body.classList.toggle("large-text", state.largeText);
    el.fontSizeBtn.textContent = state.largeText ? "Letra normal" : "Letra grande";
    if (uiParams.suggested_session_minutes) {
      el.engagementMinutes.value = String(uiParams.suggested_session_minutes);
    }
  }

  function hydrate(data) {
    if (data && data.auth) {
      state.auth.role = data.auth.role === "caregiver" ? "caregiver" : "user";
      state.auth.userName = normalizeUserName(data.auth.user_name || state.auth.userName);
      saveAuthToStorage();
    }
    renderProfile(data.profile);
    renderExercise(data.exercise);
    renderGamePlan(data.game_plan);
    renderSummary(data.summary);
    state.alerts = (data && data.alerts) || [];
    renderAlerts(state.alerts);
    renderRecentSessions(data.recent_sessions);
    renderPharmacy(data.pharmacy);
    state.quedadasData = (data && data.quedadas) || state.quedadasData || [];
    state.joinedQuedadas = (data && data.joined_quedadas) || state.joinedQuedadas || [];
    renderPrivacy(data && data.privacy);
    setLlmState(data.llm_enabled, data.llm_configured);
    applyUiParams(data.ui_params);
    applyRoleUi(state.auth.role || "user");
    updateSocialIdeas();
    if (el.chatLog.children.length === 0) {
      addBubble(
        "assistant",
        "Buenos días. Estoy aquí contigo. ¿Te apetece contarme cómo te sientes hoy"
      );
    }
  }

  async function loadBootstrap(opts = {}) {
    const options = opts || {};
    const res = await api("/api/bootstrap");
    hydrate(res.data);
    if (!options.silent) {
      showToast("Datos actualizados.");
    }
    return res;
  }

  async function loginWithRole(role, userName) {
    const cleanName = normalizeUserName(userName);
    if (!cleanName) {
      el.authError.textContent = "Escribe un nombre de usuario.";
      return;
    }
    if (!el.authConsentData.checked) {
      el.authError.textContent = "Debes aceptar el tratamiento de datos para entrar.";
      return;
    }
    state.auth.role = role === "caregiver" ? "caregiver" : "user";
    state.auth.userName = cleanName;
    state.appointmentNoticeDismissed = {};
    state.currentAppointmentNoticeKey = "";
    saveAuthToStorage();
    setLoading(el.authLoginBtn, true, "Entrando...");
    el.authError.textContent = "";
    try {
      await api("/api/privacy/update", "POST", {
        consent_data_processing: true,
        share_with_platform: !!el.authConsentShare.checked,
        allow_anon_analytics: state.privacy ? !!state.privacy.allow_anon_analytics : false,
      });
      await loadBootstrap({ silent: true });
      await loadQuedadas();
      showAppShell();
      applyRoleUi(state.auth.role);
      showToast(`Acceso cargado para ${state.auth.userName}.`);
    } catch (err) {
      clearAuth();
      showLoginGate(err.message || "No se pudo iniciar sesión.");
    } finally {
      setLoading(el.authLoginBtn, false);
    }
  }

  async function createUserFromGate() {
    const name = normalizeUserName(el.authUserName.value);
    if (!name) {
      el.authError.textContent = "Para crear usuario, primero escribe un nombre.";
      return;
    }
    if (!el.authConsentData.checked) {
      el.authError.textContent = "Debes aceptar el tratamiento de datos para crear el usuario.";
      return;
    }
    const payload = {
      name,
      preferences: el.newUserPrefs.value
        .split(",")
        .map((x) => x.trim())
        .filter(Boolean),
      energy_preference: el.newUserEnergy.value,
      weight_kg: el.newUserWeight.value.trim(),
      birth_year: Number(el.newUserBirthYear.value || 0),
      important_notes: el.newUserNotes.value.trim(),
      consent_data_processing: true,
      share_with_platform: !!el.authConsentShare.checked,
      allow_anon_analytics: false,
    };
    setLoading(el.createUserBtn, true, "Creando...");
    el.authError.textContent = "";
    try {
      await api("/api/users/create", "POST", payload);
      showToast("Usuario creado.");
      el.authRole.value = "user";
      await loginWithRole("user", name);
    } catch (err) {
      el.authError.textContent = err.message;
    } finally {
      setLoading(el.createUserBtn, false);
    }
  }

  async function saveMedication() {
    const payload = {
      name: el.medName.value.trim(),
      dose_text: el.medDose.value.trim(),
      times: el.medTimes.value
        .split(",")
        .map((x) => x.trim())
        .filter(Boolean),
      frequency: el.medFrequency.value,
      weekday: Number(el.medWeekday.value || 0),
      stock_units: Number(el.medStock.value || 0),
      low_stock_threshold: Number(el.medLow.value || 3),
      prescribed_by: el.medPrescriber.value.trim(),
      weight_kg: el.medWeight.value.trim(),
      notes: el.medNotes.value.trim(),
    };
    setLoading(el.addMedBtn, true, "Guardando...");
    try {
      const res = await api("/api/pharmacy/medication", "POST", payload);
      renderPharmacy(res.pharmacy);
      el.medName.value = "";
      el.medDose.value = "";
      el.medTimes.value = "";
      el.medPrescriber.value = "";
      el.medNotes.value = "";
      showToast("Medicamento guardado.");
    } catch (err) {
      showToast(err.message);
    } finally {
      setLoading(el.addMedBtn, false);
    }
  }

  async function saveAppointment() {
    const payload = {
      date: el.appointmentDate.value,
      time: el.appointmentTime.value,
      place: el.appointmentPlace.value.trim(),
      notes: el.appointmentNotes.value.trim(),
    };
    setLoading(el.addAppointmentBtn, true, "Guardando...");
    try {
      const res = await api("/api/pharmacy/appointment", "POST", payload);
      renderPharmacy(res.pharmacy);
      el.appointmentDate.value = "";
      el.appointmentTime.value = "";
      el.appointmentPlace.value = "";
      el.appointmentNotes.value = "";
      showToast("Cita médica guardada.");
    } catch (err) {
      showToast(err.message);
    } finally {
      setLoading(el.addAppointmentBtn, false);
    }
  }

  async function markMedicationTaken(medicationId, time) {
    try {
      const res = await api("/api/pharmacy/taken", "POST", {
        medication_id: medicationId,
        time,
      });
      const meds = (res.pharmacy && res.pharmacy.medications) || [];
      const med = meds.find((m) => m.id === medicationId);
      if (med) {
        const next = getNextPendingForMedication(med, new Date());
        state.lastTakenReminder = {
          medicationId,
          name: med.name,
          nextTime: next ? next.time : null,
          nextDue: next ? next.when : null,
        };
      }
      renderPharmacy(res.pharmacy);
      showToast("Toma registrada.");
    } catch (err) {
      showToast(err.message);
    }
  }

  async function refillMedication(medicationId, units) {
    try {
      const res = await api("/api/pharmacy/refill", "POST", {
        medication_id: medicationId,
        units: Number(units || 0),
      });
      renderPharmacy(res.pharmacy);
      showToast("Stock recargado.");
    } catch (err) {
      showToast(err.message);
    }
  }

  async function loadNextGame() {
    setLoading(el.newMemoryBtn, true, "Cambiando...");
    try {
      const res = await api("/api/game/next", "POST", { game_result: state.lastGameResult });
      renderGamePlan(res.game_plan);
      showToast("Juego cambiado.");
    } catch (err) {
      showToast(err.message);
    } finally {
      setLoading(el.newMemoryBtn, false);
    }
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function getDefaultQuedadas() {
    const today = new Date();
    const d1 = new Date(today);
    d1.setDate(today.getDate() + 2);
    const d2 = new Date(today);
    d2.setDate(today.getDate() + 5);
    return [
      {
        id: `q-${d1.getTime()}`,
        activity: "Paseo en grupo",
        place: "Parque central",
        date: d1.toISOString().slice(0, 10),
        time: "11:00",
        description: "Paseo suave y charla con vecinos.",
      },
      {
        id: `q-${d2.getTime()}`,
        activity: "Taller de memoria",
        place: "Centro cívico",
        date: d2.toISOString().slice(0, 10),
        time: "17:30",
        description: "Actividad de juegos y conversación.",
      },
    ];
  }

  function renderNearbyEvents() {
    if (!el.nearbyResults) return;
    el.nearbyResults.innerHTML = "";
    if (!state.nearbyEvents || state.nearbyEvents.length === 0) {
      el.nearbyResults.innerHTML = "<p class='muted'>No hay resultados todavía.</p>";
      return;
    }
    const joinedKey = new Set(
      (state.quedadasData || []).map((q) =>
        `${String(q.activity || "").trim().toLowerCase()}|${String(q.place || "").trim().toLowerCase()}|${String(q.date || "").trim()}|${String(q.time || "").trim()}`
      )
    );
    state.nearbyEvents.forEach((eventItem) => {
      const article = document.createElement("article");
      article.className = "quedada-card";
      const dateLine = eventItem.date ? `${escapeHtml(eventItem.date)} ${escapeHtml(eventItem.time || "")}`.trim() : "Fecha por confirmar";
      const openStatus = String(eventItem.open_status_text || "Horario no disponible");
      const reasons = Array.isArray(eventItem.interest_reasons) ? eventItem.interest_reasons : [];
      const reasonText = reasons.length ? `Coincide con: ${reasons.join(", ")}` : "Coincidencia general";
      const hoursText = Array.isArray(eventItem.hours_text) && eventItem.hours_text.length
        ? String(eventItem.hours_text[0])
        : "";
      const key = `${String(eventItem.title || "").trim().toLowerCase()}|${String(eventItem.place || "").trim().toLowerCase()}|${String(eventItem.date || "").trim()}|${String(eventItem.time || "").trim()}`;
      const isJoined = joinedKey.has(key);
      article.innerHTML =
        `<div class="quedada-header">` +
        `<h4 class="quedada-activity">${escapeHtml(eventItem.title || "Evento cercano")}</h4>` +
        `<span class="quedada-date">${dateLine}</span>` +
        `</div>` +
        `<div class="quedada-body">` +
        `<p class="quedada-place"><strong>Lugar:</strong> ${escapeHtml(eventItem.place || "Zona cercana")}</p>` +
        `<p class="quedada-description"><strong>Estado:</strong> ${escapeHtml(openStatus)}</p>` +
        `${hoursText ? `<p class="quedada-description"><strong>Horario:</strong> ${escapeHtml(hoursText)}</p>` : ""}` +
        `<p class="quedada-description"><strong>Intereses:</strong> ${escapeHtml(reasonText)}</p>` +
        `<p class="quedada-description">${escapeHtml(eventItem.description || "")}</p>` +
        `</div>` +
        `<div class="quedada-actions">` +
        `<button type="button" class="${isJoined ? "btn-soft" : "btn-primary"} nearby-join-btn">${isJoined ? "Apuntado" : "Me apunto"}</button>` +
        `</div>`;

      const joinBtn = article.querySelector(".nearby-join-btn");
      if (joinBtn) {
        joinBtn.addEventListener("click", async () => {
          if (isJoined) {
            showToast("Ya estás apuntado a esta quedada.");
            return;
          }
          try {
            const res = await api("/api/quedadas/join-nearby", "POST", {
              title: eventItem.title || "Actividad cercana",
              place: eventItem.place || "Zona cercana",
              date: eventItem.date || new Date().toISOString().slice(0, 10),
              time: eventItem.time || "18:00",
              description: eventItem.description || "Importada desde búsqueda cercana.",
            });
            state.quedadasData = (res && res.quedadas) || state.quedadasData;
            state.joinedQuedadas = (res && res.joined_quedadas) || state.joinedQuedadas;
            renderQuedadas();
            renderNearbyEvents();
            showToast("Te hemos apuntado y ya aparece en quedadas propuestas.");
          } catch (err) {
            showToast(err.message || "No se pudo completar la inscripción.");
          }
        });
      }
      el.nearbyResults.appendChild(article);
    });
    markRevealTargets(el.nearbyResults);
  }

  async function useCurrentLocationForNearby() {
    if (!navigator.geolocation) {
      showToast("Tu navegador no soporta geolocalización.");
      return;
    }
    setLoading(el.nearbyUseLocationBtn, true, "Ubicando...");
    try {
      const position = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 120000,
        });
      });
      const lat = Number(position.coords.latitude || 0);
      const lng = Number(position.coords.longitude || 0);
      state.nearbyGeo = { lat, lng };
      try {
        const geo = await api(`/api/location/reverse?lat=${encodeURIComponent(lat)}&lng=${encodeURIComponent(lng)}`);
        const address = String((geo && geo.address) || "").trim();
        if (address) {
          el.nearbyDetectedAddress.value = address;
          if (!String(el.nearbyAddress.value || "").trim()) {
            el.nearbyAddress.value = address;
          }
        } else {
          el.nearbyDetectedAddress.value = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
        }
      } catch (_) {
        el.nearbyDetectedAddress.value = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
      }
      showToast("Ubicación cargada.");
    } catch (_) {
      showToast("No se pudo obtener tu ubicación.");
    } finally {
      setLoading(el.nearbyUseLocationBtn, false);
    }
  }

  async function searchNearbyEvents() {
    const address = String(el.nearbyAddress.value || "").trim();
    const radiusKm = String(el.nearbyRadiusKm.value || "5").trim();
    const q = String(el.nearbyQuery.value || "").trim();
    const qs = new URLSearchParams({
      address,
      radius_km: radiusKm,
      q,
    });
    if (Number.isFinite(state.nearbyGeo.lat) && Number.isFinite(state.nearbyGeo.lng)) {
      qs.set("lat", String(state.nearbyGeo.lat));
      qs.set("lng", String(state.nearbyGeo.lng));
    }
    setLoading(el.searchNearbyBtn, true, "Buscando...");
    el.nearbyStatus.textContent = "Buscando...";
    try {
      const res = await api(`/api/events/nearby?${qs.toString()}`);
      state.nearbyEvents = Array.isArray(res.events) ? res.events : [];
      if (Number.isFinite(Number(res.center_lat)) && Number.isFinite(Number(res.center_lng))) {
        state.nearbyCenter = { lat: Number(res.center_lat), lng: Number(res.center_lng) };
      }
      if (res && res.resolved_address) {
        el.nearbyDetectedAddress.value = String(res.resolved_address);
      }
      renderNearbyEvents();
      renderNearbyMap();
      const provider = res.provider || "mock";
      const prefCount = Array.isArray(res.preferences_used) ? res.preferences_used.length : 0;
      const personalization = prefCount ? ` · personalizadas (${prefCount})` : "";
      if (provider === "google") {
        el.nearbyStatus.textContent = `Resultados reales (${state.nearbyEvents.length})${personalization}`;
      } else {
        el.nearbyStatus.textContent = `Placeholder (${state.nearbyEvents.length})${personalization}`;
      }
    } catch (err) {
      state.nearbyEvents = [];
      state.nearbyCenter = null;
      renderNearbyEvents();
      renderNearbyMap();
      el.nearbyStatus.textContent = "Sin resultados";
      showToast(err.message || "No se pudo buscar eventos cercanos.");
    } finally {
      setLoading(el.searchNearbyBtn, false);
    }
  }

  function renderQuedadas() {
    const container = el.quedadasContainer;
    if (!container) return;
    container.innerHTML = "";
    if (!state.quedadasData || state.quedadasData.length === 0) {
      container.innerHTML = "<p class='muted'>No hay quedadas propuestas en este momento.</p>";
      return;
    }

    const joined = new Set((state.joinedQuedadas || []).map((x) => String(x)));
    state.quedadasData.forEach((quedada) => {
      const article = document.createElement("article");
      article.className = "quedada-card";
      const isJoined = joined.has(String(quedada.id));
      const dateObj = new Date(quedada.date);
      const dateStr = Number.isNaN(dateObj.getTime())
        ? escapeHtml(quedada.date)
        : dateObj.toLocaleDateString("es-ES", {
            weekday: "short",
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
          });

      article.innerHTML =
        `<div class="quedada-header">` +
        `<h4 class="quedada-activity">${escapeHtml(quedada.activity)}</h4>` +
        `<span class="quedada-date">${dateStr} a las ${escapeHtml(quedada.time)}</span>` +
        `</div>` +
        `<div class="quedada-body">` +
        `<p class="quedada-place"><strong>Lugar:</strong> ${escapeHtml(quedada.place)}</p>` +
        `<p class="quedada-description">${escapeHtml(quedada.description || "")}</p>` +
        `</div>` +
        `<div class="quedada-actions">` +
        `<button type="button" class="${isJoined ? "btn-soft" : "btn-secondary"} quedada-join-btn" data-quedada-id="${escapeHtml(quedada.id)}">${isJoined ? "Desapuntarse" : "Me apunto"}</button>` +
        `</div>`;

      const joinBtn = article.querySelector(".quedada-join-btn");
      if (joinBtn) {
        joinBtn.addEventListener("click", async () => {
          const qid = String(quedada.id);
          const currentlyJoined = (state.joinedQuedadas || []).map((x) => String(x)).includes(qid);
          try {
            const endpoint = currentlyJoined ? "/api/quedadas/leave" : "/api/quedadas/join";
            const res = await api(endpoint, "POST", { quedada_id: qid });
            state.quedadasData = (res && res.quedadas) || state.quedadasData;
            state.joinedQuedadas = (res && res.joined_quedadas) || state.joinedQuedadas;
            renderQuedadas();
            showToast(currentlyJoined ? "Te has desapuntado de la quedada." : "Genial, te hemos apuntado a la quedada.");
          } catch (err) {
            showToast(err.message || "No se pudo actualizar la quedada.");
          }
        });
      }
      container.appendChild(article);
    });
    markRevealTargets(container);
  }

  async function loadQuedadas() {
    try {
      const res = await api("/api/quedadas");
      state.quedadasData = (res && res.quedadas) || [];
      state.joinedQuedadas = (res && res.joined_quedadas) || [];
    } catch (_) {
      if (!state.quedadasData || state.quedadasData.length === 0) {
        state.quedadasData = getDefaultQuedadas();
      }
      if (!Array.isArray(state.joinedQuedadas)) {
        state.joinedQuedadas = [];
      }
    }
    renderQuedadas();
  }

  async function saveQuedada() {
    const activity = el.quedadaActivity.value.trim();
    const place = el.quedadaPlace.value.trim();
    const date = el.quedadaDate.value.trim();
    const time = el.quedadaTime.value.trim();
    const description = el.quedadaDescription.value.trim();

    if (!activity || !place || !date || !time) {
      showToast("Completa actividad, lugar, fecha y hora.");
      return;
    }

    try {
      const res = await api("/api/quedadas", "POST", {
      activity,
      place,
      date,
      time,
      description,
      });
      state.quedadasData = (res && res.quedadas) || state.quedadasData;
      state.joinedQuedadas = (res && res.joined_quedadas) || state.joinedQuedadas;
    } catch (err) {
      showToast(err.message || "No se pudo crear la quedada.");
      return;
    }
    renderQuedadas();
    el.quedadaActivity.value = "";
    el.quedadaPlace.value = "";
    el.quedadaDate.value = "";
    el.quedadaTime.value = "";
    el.quedadaDescription.value = "";
    showToast("Quedada creada.");
  }

  async function savePrivacySettings() {
    setLoading(el.savePrivacyBtn, true, "Guardando...");
    try {
      const res = await api("/api/privacy/update", "POST", {
        consent_data_processing: !!el.privacyConsentData.checked,
        share_with_platform: !!el.privacySharePlatform.checked,
        allow_anon_analytics: !!el.privacyAnonAnalytics.checked,
      });
      renderPrivacy(res.privacy || {});
      showToast("Privacidad actualizada.");
    } catch (err) {
      showToast(err.message || "No se pudo guardar privacidad.");
    } finally {
      setLoading(el.savePrivacyBtn, false);
    }
  }

  async function deleteAllUserData() {
    const user = state.auth.userName || "este usuario";
    const ok = window.confirm(
      `Se borrarán todos los datos de ${user} (sesiones, farmacia, citas y quedadas). ¿Continuar?`
    );
    if (!ok) return;
    setLoading(el.deleteAllDataBtn, true, "Borrando...");
    try {
      await api("/api/privacy/delete-all", "POST", {});
      state.pharmacyData = null;
      state.quedadasData = [];
      state.privacy = null;
      state.lastGameResult = null;
      clearAuth();
      showLoginGate("Datos eliminados. Vuelve a iniciar sesión.");
      el.authUserName.value = "";
      el.authRole.value = "user";
      el.authConsentData.checked = false;
      el.authConsentShare.checked = false;
      hideDueNotice();
      hideAppointmentNotice();
      showToast("Todos los datos han sido eliminados.");
    } catch (err) {
      showToast(err.message || "No se pudo borrar la información.");
    } finally {
      setLoading(el.deleteAllDataBtn, false);
    }
  }

  function wireEvents() {
    el.tabSessionBtn.addEventListener("click", () => setTab("session"));
    el.tabCaregiverBtn.addEventListener("click", () => setTab("caregiver"));
    el.tabPharmacyBtn.addEventListener("click", () => setTab("pharmacy"));
    el.tabQuedadasBtn.addEventListener("click", () => setTab("quedadas"));
    el.tabPrivacyBtn.addEventListener("click", () => setTab("privacy"));
    el.landingStartBtn.addEventListener("click", () => showLoginGate(""));
    el.fontSizeBtn.addEventListener("click", toggleLargeText);
    el.socialToday.addEventListener("change", updateSocialIdeas);
    el.moodButtons.forEach((btn) => btn.addEventListener("click", () => setMood(btn.dataset.mood)));

    el.scoreMemoryBtn.addEventListener("click", evaluateCurrentGame);
    el.newMemoryBtn.addEventListener("click", loadNextGame);
    el.toggleWordsBtn.addEventListener("click", () => {
      state.wordsVisible = !state.wordsVisible;
      if (state.gamePlan && state.gamePlan.id === "memory_words") {
        setMemoryWordsVisibility();
      }
    });

    el.sendChatBtn.addEventListener("click", sendChat);
    el.chatInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendChat();
      }
    });
    el.speakBtn.addEventListener("click", speakLastAssistant);
    el.saveSessionBtn.addEventListener("click", saveSession);
    el.refreshBtn.addEventListener("click", async () => {
      try {
        await loadBootstrap();
      } catch (err) {
        showToast(err.message);
      }
    });
    el.refreshQuedadasBtn.addEventListener("click", () => {
      loadQuedadas();
    });
    el.authLoginBtn.addEventListener("click", () => loginWithRole(el.authRole.value, el.authUserName.value));
    el.authUserName.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        loginWithRole(el.authRole.value, el.authUserName.value);
      }
    });
    el.createUserBtn.addEventListener("click", createUserFromGate);
    el.switchUserBtn.addEventListener("click", () => {
      clearAuth();
      showLoginGate("");
      el.authUserName.value = "";
      el.authRole.value = "user";
      hideDueNotice();
      hideAppointmentNotice();
    });
    el.medDueDismissBtn.addEventListener("click", hideDueNotice);
    el.appointmentDismissBtn.addEventListener("click", () => {
      const alerts = (state.pharmacyData && state.pharmacyData.appointment_alerts) || [];
      if (state.currentAppointmentNoticeKey) {
        setAppointmentDismissed(state.currentAppointmentNoticeKey, true);
      }
      if (alerts.length) {
        alerts.forEach((item) => {
          setAppointmentDismissed(buildAppointmentDismissKey(item), true);
        });
      }
      hideAppointmentNotice();
    });
    el.addMedBtn.addEventListener("click", saveMedication);
    el.addAppointmentBtn.addEventListener("click", saveAppointment);
    el.addQuedadaBtn.addEventListener("click", saveQuedada);
    el.nearbyUseLocationBtn.addEventListener("click", useCurrentLocationForNearby);
    el.searchNearbyBtn.addEventListener("click", searchNearbyEvents);
    el.savePrivacyBtn.addEventListener("click", savePrivacySettings);
    el.deleteAllDataBtn.addEventListener("click", deleteAllUserData);
    el.medFrequency.addEventListener("change", updateMedFrequencyUi);
    el.pharmacyRows.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) return;
      if (target.classList.contains("med-taken-btn")) {
        markMedicationTaken(target.dataset.medId, target.dataset.medTime);
        return;
      }
      if (target.classList.contains("med-refill-btn")) {
        const medId = target.dataset.medId;
        const input = el.pharmacyRows.querySelector(`input[data-refill-input="${medId}"]`);
        const units = input ? input.value : "0";
        refillMedication(medId, units);
      }
    });
  }

  function init() {
    bindElements();
    wireEvents();
    setupVoiceInput();
    setMood(3);
    updateProgress();
    setTab("session");
    updateMedFrequencyUi();
    showLanding();
    setupRevealAnimations();
    const remembered = readAuthFromStorage();
    if (remembered) {
      el.authRole.value = remembered.role;
      el.authUserName.value = remembered.userName;
      showLoginGate("");
      el.authError.textContent = "Confirma consentimiento y pulsa Entrar.";
    }
    startMedicationUiTimer();
    hideLoadingScreen(900);
  }

  window.addEventListener("DOMContentLoaded", init);
})();
