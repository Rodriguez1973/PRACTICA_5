const form = document.getElementById("generator-form");
const remoteApiUrlEl = document.getElementById("remoteApiUrl");
const output = document.getElementById("output");
const statusLabel = document.getElementById("status");
const elapsedLabel = document.getElementById("elapsed");
const healthBtn = document.getElementById("healthBtn");
const speakBtn = document.getElementById("speakBtn");
const stopSpeakBtn = document.getElementById("stopSpeakBtn");

let remoteConfigReady = false;

const setStatus = (text) => {
  statusLabel.textContent = text;
};

const loadWebConfig = async () => {
  try {
    const response = await fetch("/web-config");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const config = await response.json();
    remoteApiUrlEl.textContent = config.remote_api_base_url || "no configurada";
    if (!config.remote_key_configured) {
      setStatus("Falta REMOTE_API_KEY en el backend");
      remoteConfigReady = false;
      return;
    }
    remoteConfigReady = true;
    setStatus("Listo");
  } catch (err) {
    remoteApiUrlEl.textContent = "error cargando configuracion";
    setStatus(`Error de configuracion: ${err.message}`);
    remoteConfigReady = false;
  }
};

loadWebConfig();

healthBtn.addEventListener("click", async () => {
  if (!remoteConfigReady) {
    setStatus("Configura primero REMOTE_API_BASE_URL y REMOTE_API_KEY en backend");
    return;
  }

  setStatus("Probando conexion...");
  try {
    const response = await fetch("/health-remote");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    setStatus("Conexion con Azure API correcta");
  } catch (err) {
    setStatus(`No se pudo conectar: ${err.message}`);
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const seed = document.getElementById("seed").value.trim();
  const nWords = Number(document.getElementById("nWords").value);
  const strategy = document.getElementById("strategy").value;
  const temperature = Number(document.getElementById("temperature").value);
  const topK = Number(document.getElementById("topK").value);

  if (!remoteConfigReady) {
    setStatus("Configura primero REMOTE_API_BASE_URL y REMOTE_API_KEY en backend");
    return;
  }
  if (!seed) {
    setStatus("Faltan campos obligatorios");
    return;
  }

  const payload = {
    seed,
    n_words: nWords,
    strategy,
    temperature,
    top_k: topK,
  };

  setStatus("Generando...");
  elapsedLabel.textContent = "";

  try {
    const response = await fetch("/generate-proxy", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    const data = await response.json();
    output.textContent = data.generated_text;
    elapsedLabel.textContent = `${data.elapsed_ms} ms`;
    setStatus("Texto generado correctamente");
  } catch (err) {
    output.textContent = "No se pudo generar texto.";
    setStatus(`Error: ${err.message}`);
  }
});

speakBtn.addEventListener("click", () => {
  const text = output.textContent.trim();
  if (!text || text === "El texto generado aparecerá aquí.") {
    setStatus("No hay texto para leer");
    return;
  }

  if (!("speechSynthesis" in window)) {
    setStatus("Este navegador no soporta Text-to-Speech");
    return;
  }

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "es-ES";
  utterance.rate = 1;
  utterance.pitch = 1;

  utterance.onstart = () => setStatus("Reproduciendo voz...");
  utterance.onend = () => setStatus("Lectura finalizada");
  utterance.onerror = () => setStatus("Error al sintetizar voz");

  window.speechSynthesis.speak(utterance);
});

stopSpeakBtn.addEventListener("click", () => {
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
    setStatus("Lectura detenida");
  }
});
