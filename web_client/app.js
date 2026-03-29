/**
 * app.js - Cliente web para la API de generación de texto
 * Práctica 5: Integración, Automatización y Modelos de Negocio
 */

// ─── Estado de la aplicación ───────────────────────────────────────────
const state = {
    connected: false,
    history: [],
    lastGeneration: null,
};

// ─── Elementos del DOM ───────────────────────────────────────────────
const elements = {
    apiUrl: document.getElementById('apiUrl'),
    apiKey: document.getElementById('apiKey'),
    healthBtn: document.getElementById('healthBtn'),
    healthStatus: document.getElementById('healthStatus'),
    
    seedInput: document.getElementById('seedInput'),
    nWords: document.getElementById('nWords'),
    strategy: document.getElementById('strategy'),
    temperature: document.getElementById('temperature'),
    tempValue: document.getElementById('tempValue'),
    topK: document.getElementById('topK'),
    generateBtn: document.getElementById('generateBtn'),
    loading: document.getElementById('loading'),
    error: document.getElementById('error'),
    
    resultsPanel: document.getElementById('resultsPanel'),
    generatedText: document.getElementById('generatedText'),
    resultStrategy: document.getElementById('resultStrategy'),
    resultWords: document.getElementById('resultWords'),
    resultTime: document.getElementById('resultTime'),
    copyBtn: document.getElementById('copyBtn'),
    shareBtn: document.getElementById('shareBtn'),
    
    history: document.getElementById('history'),
    clearHistoryBtn: document.getElementById('clearHistoryBtn'),
    
    connectionStatus: document.getElementById('connectionStatus'),
};

// ─── Event Listeners ───────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
    loadFromLocalStorage();
    elements.healthBtn.addEventListener('click', checkHealth);
    elements.generateBtn.addEventListener('click', generate);
    elements.temperature.addEventListener('input', (e) => {
        elements.tempValue.textContent = parseFloat(e.target.value).toFixed(1);
    });
    elements.copyBtn.addEventListener('click', copyToClipboard);
    elements.shareBtn.addEventListener('click', shareResult);
    elements.clearHistoryBtn.addEventListener('click', clearHistory);
});

// ─── Funciones principales ────────────────────────────────────────────

/**
 * Verifica la conexión con la API
 */
async function checkHealth() {
    try {
        hideError();
        elements.healthBtn.disabled = true;
        elements.healthBtn.textContent = '⏳ Verificando...';

        // Paso 1: verificar que la API responde y el modelo está cargado
        const healthResponse = await fetch(`${elements.apiUrl.value}/health`);
        const healthData = await healthResponse.json();

        if (!healthResponse.ok || !healthData.model_loaded || !healthData.tokenizer_loaded) {
            state.connected = false;
            showError('⚠️ Conexión parcial. Modelo o tokenizador no disponible.');
            updateConnectionStatus(false);
            return;
        }

        // Paso 2: validar la API key con un endpoint autenticado
        const authResponse = await fetch(`${elements.apiUrl.value}/strategies`, {
            headers: { 'X-API-Key': elements.apiKey.value }
        });

        if (authResponse.status === 401) {
            state.connected = false;
            showError('❌ API Key incorrecta. Verifica la clave e inténtalo de nuevo.');
            updateConnectionStatus(false);
            return;
        }

        if (!authResponse.ok) {
            state.connected = false;
            showError(`❌ Error al validar la API Key (HTTP ${authResponse.status}).`);
            updateConnectionStatus(false);
            return;
        }

        state.connected = true;
        showSuccess('✅ Conexión exitosa. Modelo cargado y API Key válida.');
        updateConnectionStatus(true);

    } catch (error) {
        state.connected = false;
        showError(`❌ Error de conexión: ${error.message}`);
        updateConnectionStatus(false);
    } finally {
        elements.healthBtn.disabled = false;
        elements.healthBtn.textContent = '📡 Verificar Conexión';
    }
}

/**
 * Genera texto usando la API
 */
async function generate() {
    try {
        // Validación
        const seed = elements.seedInput.value.trim();
        if (!seed) {
            showError('Por favor, introduce un texto inicial (seed).');
            return;
        }

        if (!state.connected) {
            showError('❌ No estás conectado a la API. Verifica la conexión primero.');
            return;
        }

        hideError();
        elements.generateBtn.disabled = true;
        elements.loading.style.display = 'block';

        // Construcción de la petición
        const payload = {
            seed: seed,
            n_words: parseInt(elements.nWords.value),
            strategy: elements.strategy.value,
            temperature: parseFloat(elements.temperature.value),
            top_k: parseInt(elements.topK.value),
        };

        const response = await fetch(`${elements.apiUrl.value}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': elements.apiKey.value,
            },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        const result = await response.json();
        displayResult(result);
        addToHistory(result);
        saveToLocalStorage();

    } catch (error) {
        showError(`Error: ${error.message}`);
    } finally {
        elements.generateBtn.disabled = false;
        elements.loading.style.display = 'none';
    }
}

/**
 * Muestra el resultado de la generación
 */
function displayResult(result) {
    elements.generatedText.textContent = result.generated_text;
    elements.resultStrategy.textContent = result.strategy;
    elements.resultWords.textContent = result.n_words_generated;
    elements.resultTime.textContent = result.elapsed_ms.toFixed(2);
    elements.resultsPanel.style.display = 'block';

    state.lastGeneration = {
        seed: result.seed,
        generated_text: result.generated_text,
    };

    // Auto-scroll al resultado
    elements.resultsPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Añade una generación al historial
 */
function addToHistory(result) {
    const historyEntry = {
        id: Date.now(),
        seed: result.seed,
        generated: result.generated_text,
        strategy: result.strategy,
        timestamp: new Date().toLocaleString('es-ES'),
    };

    state.history.unshift(historyEntry);
    if (state.history.length > 10) {
        state.history.pop();
    }

    renderHistory();
}

/**
 * Renderiza el historial
 */
function renderHistory() {
    if (state.history.length === 0) {
        elements.history.innerHTML = '<p style="color: #999;">Sin histórial aún</p>';
        return;
    }

    elements.history.innerHTML = state.history
        .map(entry => `
            <div class="history-item" onclick="loadFromHistory(${entry.id})">
                <div class="seed"><strong>Seed:</strong> ${escapeHtml(entry.seed)}</div>
                <div class="preview">${escapeHtml(entry.generated)}</div>
                <div class="time">${entry.timestamp}</div>
            </div>
        `)
        .join('');
}

/**
 * Carga una entrada del historial
 */
function loadFromHistory(id) {
    const entry = state.history.find(e => e.id === id);
    if (entry) {
        displayResult({
            seed: entry.seed,
            generated_text: entry.generated,
            strategy: entry.strategy,
            n_words_generated: entry.generated.split(' ').length - entry.seed.split(' ').length,
            elapsed_ms: 0,
        });
    }
}

/**
 * Limpia el historial
 */
function clearHistory() {
    if (confirm('¿Estás seguro de que quieres limpiar el historial?')) {
        state.history = [];
        renderHistory();
        saveToLocalStorage();
    }
}

// ─── Funciones auxiliares ───────────────────────────────────────────────

/**
 * Copia el texto generado al portapapeles
 */
function copyToClipboard() {
    if (state.lastGeneration) {
        const text = state.lastGeneration.generated_text;
        navigator.clipboard.writeText(text).then(() => {
            alert('✅ Texto copiado al portapapeles');
        }).catch(err => {
            console.error('Error al copiar:', err);
        });
    }
}

/**
 * Comparte el resultado
 */
function shareResult() {
    if (state.lastGeneration && navigator.share) {
        navigator.share({
            title: 'Texto generado por IA',
            text: state.lastGeneration.generated_text,
        }).catch(err => console.error('Error al compartir:', err));
    } else if (state.lastGeneration) {
        alert('API de compartir no disponible en tu navegador.');
    }
}

/**
 * Muestra un mensaje de error
 */
function showError(message) {
    elements.error.textContent = message;
    elements.error.classList.add('show');
}

/**
 * Muestra un mensaje de éxito
 */
function showSuccess(message) {
    elements.healthStatus.textContent = message;
    elements.healthStatus.className = 'status-message success';
}

/**
 * Oculta el mensaje de error
 */
function hideError() {
    elements.error.classList.remove('show');
    elements.healthStatus.className = 'status-message';
}

/**
 * Actualiza el estado de conexión en el footer
 */
function updateConnectionStatus(connected) {
    if (connected) {
        elements.connectionStatus.textContent = 'Conectado ✅';
        elements.connectionStatus.className = 'connected';
    } else {
        elements.connectionStatus.textContent = 'Desconectado ❌';
        elements.connectionStatus.className = '';
    }
}

/**
 * Escapa caracteres especiales de HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Guarda el estado en localStorage
 */
function saveToLocalStorage() {
    localStorage.setItem('apiUrl', elements.apiUrl.value);
    localStorage.setItem('history', JSON.stringify(state.history));
}

/**
 * Carga el estado desde localStorage
 */
function loadFromLocalStorage() {
    const savedUrl = localStorage.getItem('apiUrl');
    if (savedUrl) {
        elements.apiUrl.value = savedUrl;
    }

    const savedHistory = localStorage.getItem('history');
    if (savedHistory) {
        try {
            state.history = JSON.parse(savedHistory);
            renderHistory();
        } catch (e) {
            console.error('Error al cargar historial:', e);
        }
    } else {
        renderHistory();
    }
}
