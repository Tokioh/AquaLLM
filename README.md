# AquaLLM - Sistema de Atención al Cliente con IA

Un sistema de chatbot inteligente diseñado para que las empresas de agua potable ofrezcan atención al cliente 24/7. El chatbot puede responder preguntas sobre facturación, consumo, contratos y solicitudes utilizando una base de datos de clientes y un modelo de lenguaje local (Ollama).
---

## 🚀 Tecnologías Utilizadas

-   **Frontend:** React
-   **Backend:** Python con FastAPI
-   **Base de Datos:** Supabase (PostgreSQL)
-   **IA / LLM:** Ollama (ejecutando modelos como `gemma:2b` o `tinyllama` localmente)
-   **Servidor:** Uvicorn

---

## ✨ Características

-   **Consulta de Datos:** El usuario puede preguntar usando su número de cliente o medidor.
-   **Respuestas Contextualizadas:** El sistema busca información real del cliente en la base de datos (facturas, consumos, estado del servicio) para generar respuestas precisas.
-   **Procesamiento de Lenguaje Natural:** Utiliza un LLM para entender la pregunta del usuario y generar una respuesta en lenguaje natural.
-   **Operación Local:** Funciona de forma 100% local (después de la configuración inicial), sin depender de APIs de terceros para la IA.

---

## 📋 Prerrequisitos

Antes de empezar, asegúrate de tener instalado lo siguiente:

-   [Node.js](https://nodejs.org/en/) (versión LTS recomendada)
-   [Python](https://www.python.org/downloads/) (versión 3.8 o superior)
-   [Ollama](https://ollama.com/) y un modelo descargado (ej. `ollama run gemma:2b`)

---

## ⚙️ Instalación y Configuración

Sigue estos pasos para poner en marcha el proyecto en tu máquina local.

### 1. Clonar el Repositorio

```bash
git clone https://github.com/Tokioh/AquaLLM.git
cd AquaLLM
```

### 2. Configurar el Backend

```bash
# 1. Navega a la carpeta del backend
cd backend

# 2. Crea un entorno virtual
python -m venv .venv

# 3. Activa el entorno virtual
# En Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# En macOS/Linux:
source .venv/bin/activate

# 4. Instala las dependencias de Python
pip install -r requirements.txt

# 5. Configura tus credenciales
# Crea un archivo llamado .env en la carpeta 'backend' y añade tus claves:
# SUPABASE_URL="TU_URL_DE_SUPABASE"
# SUPABASE_KEY="TU_ANON_KEY_DE_SUPABASE"
```

### 3. Configurar el Frontend

```bash
# 1. Desde la raíz del proyecto, navega a la carpeta del frontend
cd ../frontend

# 2. Instala las dependencias de Node.js
npm install
```

---

## ▶️ Cómo Ejecutar la Aplicación

### 1. Iniciar el Servidor de Ollama

Asegúrate de que la aplicación de Ollama se esté ejecutando en tu máquina.

### 2. Iniciar el Backend (FastAPI)

Con el entorno virtual del backend activado (`.venv`), ejecuta el siguiente comando desde la carpeta `backend`:

```bash
uvicorn app.main:app --reload
```

El servidor backend estará disponible en `http://localhost:8000`. Puedes ver la documentación de la API en `http://localhost:8000/docs`.

### 3. Iniciar el Frontend (React)

En una **nueva terminal**, navega a la carpeta `frontend` y ejecuta:

```bash
npm start
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:3000`.

¡Y listo! Ya puedes interactuar con el chatbot.

---

## 📂 Estructura del Proyecto

```
.
├── backend/            # Código del servidor FastAPI
│   ├── app/
│   ├── .venv/
│   ├── .env            # (No versionado) Credenciales
│   └── requirements.txt
├── frontend/           # Código de la aplicación React
│   ├── public/
│   ├── src/
│   └── package.json
├── .gitignore          # Archivos ignorados por Git
└── README.md           # Este archivo
```
