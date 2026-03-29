const formulario = document.getElementById("formulario-generador");
const urlApiRemota = document.getElementById("urlApiRemota");
const salidaGenerada = document.getElementById("salidaGenerada");
const etiquetaEstado = document.getElementById("estado");
const etiquetaTiempo = document.getElementById("tiempoTranscurrido");
const botonConexion = document.getElementById("botonConexion");
const botonHablar = document.getElementById("botonHablar");
const botonDetenerVoz = document.getElementById("botonDetenerVoz");

let configuracionRemotaLista = false;

const establecerEstado = (texto) => {
  etiquetaEstado.textContent = texto;
};

const cargarConfiguracionWeb = async () => {
  try {
    const respuesta = await fetch("/web-config");
    if (!respuesta.ok) {
      throw new Error(`HTTP ${respuesta.status}`);
    }
    const configuracion = await respuesta.json();
    urlApiRemota.textContent = configuracion.remote_api_base_url || "no configurada";
    if (!configuracion.remote_key_configured) {
      establecerEstado("Falta REMOTE_API_KEY en el backend");
      configuracionRemotaLista = false;
      return;
    }
    configuracionRemotaLista = true;
    establecerEstado("Listo");
  } catch (error) {
    urlApiRemota.textContent = "error cargando configuración";
    establecerEstado(`Error de configuración: ${error.message}`);
    configuracionRemotaLista = false;
  }
};

cargarConfiguracionWeb();

botonConexion.addEventListener("click", async () => {
  if (!configuracionRemotaLista) {
    establecerEstado("Configura primero REMOTE_API_BASE_URL y REMOTE_API_KEY en backend");
    return;
  }

  establecerEstado("Probando conexión...");
  try {
    const respuesta = await fetch("/health-remote");
    if (!respuesta.ok) {
      throw new Error(`HTTP ${respuesta.status}`);
    }
    establecerEstado("Conexión con Azure API correcta");
  } catch (error) {
    establecerEstado(`No se pudo conectar: ${error.message}`);
  }
});

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();

  const semilla = document.getElementById("semilla").value.trim();
  const numeroPalabras = Number(document.getElementById("numeroPalabras").value);
  const estrategia = document.getElementById("estrategia").value;
  const temperatura = Number(document.getElementById("temperatura").value);
  const topK = Number(document.getElementById("topK").value);

  if (!configuracionRemotaLista) {
    establecerEstado("Configura primero REMOTE_API_BASE_URL y REMOTE_API_KEY en backend");
    return;
  }
  if (!semilla) {
    establecerEstado("Faltan campos obligatorios");
    return;
  }

  const carga = {
    seed: semilla,
    n_words: numeroPalabras,
    strategy: estrategia,
    temperature: temperatura,
    top_k: topK,
  };

  establecerEstado("Generando...");
  etiquetaTiempo.textContent = "";

  try {
    const respuesta = await fetch("/generate-proxy", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(carga),
    });

    if (!respuesta.ok) {
      const error = await respuesta.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP ${respuesta.status}`);
    }

    const datos = await respuesta.json();
    salidaGenerada.textContent = datos.generated_text;
    etiquetaTiempo.textContent = `${datos.elapsed_ms} ms`;
    establecerEstado("Texto generado correctamente");
  } catch (error) {
    salidaGenerada.textContent = "No se pudo generar texto.";
    establecerEstado(`Error: ${error.message}`);
  }
});

botonHablar.addEventListener("click", () => {
  const texto = salidaGenerada.textContent.trim();
  if (!texto || texto === "El texto generado aparecerá aquí.") {
    establecerEstado("No hay texto para leer");
    return;
  }

  if (!("speechSynthesis" in window)) {
    establecerEstado("Este navegador no soporta Text-to-Speech");
    return;
  }

  window.speechSynthesis.cancel();
  const locucion = new SpeechSynthesisUtterance(texto);
  locucion.lang = "es-ES";
  locucion.rate = 1;
  locucion.pitch = 1;

  locucion.onstart = () => establecerEstado("Reproduciendo voz...");
  locucion.onend = () => establecerEstado("Lectura finalizada");
  locucion.onerror = () => establecerEstado("Error al sintetizar voz");

  window.speechSynthesis.speak(locucion);
});

botonDetenerVoz.addEventListener("click", () => {
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
    establecerEstado("Lectura detenida");
  }
});
