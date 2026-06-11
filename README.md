
# 💣 DoseBuster

<div align="center">

```
  ____                ____             _           
 |  _ \  ___  ___  __| __ ) _   _ ___| |_ ___ _ __ 
 | | | |/ _ \/ __|/ _  |  _ \| | | / __| __/ _ \ '__|
 | |_| | (_) \__ \ (_| | |_) | |_| \__ \ ||  __/ |   
 |____/ \___/|___/\__,_|____/ \__,_|___/\__\___|_|   
```

**El fuzzer que nunca deja de cavar — by DoseUser**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Async](https://img.shields.io/badge/Async-100%25-purple?style=flat-square)](https://docs.python.org/3/library/asyncio.html)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square)](CONTRIBUTING.md)

</div>

> Enumeración recursiva inteligente de directorios y archivos, motor 100% asíncrono y capacidades que superan cualquier herramienta actual.

## 🌟 Características principales

- **Recursión activa inmediata** – Nuevos directorios se exploran al instante sin esperar a que termine la cola actual.
- **Enumeración dual simultánea** – Búsqueda de directorios con wordlist + fuzzing de archivos usando extensiones configurables.
- **Motor asíncrono puro** – Construido sobre `asyncio` y `aiohttp`, conexiones reutilizables, reintentos inteligentes.
- **Anti falsos positivos** – `auto-tune` genera un baseline contra páginas 404 para descartar respuestas basura.
- **Persistencia y reanudación** – Archivo de estado que guarda el progreso exacto; reanuda escaneos interrumpidos sin reprocesar.
- **Rotación de User‑Agents, proxy, rate‑limiting** – Con un scheduler justo para evitar bloqueos.
- **Filtros avanzados** – Código de estado, tamaño, palabras, regex, similitud y lógica AND/OR.
- **Reportes elegantes** – ASCII art, progreso interactivo en consola, exportación a JSON, CSV, Markdown y HTML.
- **Modo Stealth** – Demoras aleatorias, fragmentación y evasión básica de WAF.
- **Extensible** – Arquitectura modular lista para DeepInfinity, clasificador ML, fuzzing de parámetros y más.

## ⚡ Instalación

```bash
git clone https://github.com/DoseUser/DoseBuster.git
cd DoseBuster
pip install -r requirements.txt
```

Requisitos: `aiohttp`, `colorama`, `pyyaml`, `jinja2` (opcional para HTML), `scikit-learn` (futuro).

## 🚀 Uso rápido

```bash
python dosebuster.py https://example.com -w wordlist.txt -x .bak,.zip,.php -d 3 --auto-tune -c 50
```

**Banderas principales:**

| Bandera | Descripción |
|--------|-------------|
| `-w` | Archivo con wordlist base |
| `-x` | Extensiones separadas por coma |
| `-d` | Profundidad máxima de recursión |
| `-c` | Conexiones simultáneas (concurrencia) |
| `--auto-tune` | Detecta falsos positivos comparando con 404 |
| `--delay` | Demora fija entre peticiones |
| `--jitter` | Jitter aleatorio (máximo) |
| `--stealth` | Modo sigiloso (demoras + rotación) |
| `--resume` | Reanudar desde estado guardado |
| `-f` | Formato de salida: `json,csv,md,html` |
| `--filter-code` | Filtrar por códigos (ej: `200,403`) |
| `--filter-size` | Filtrar por tamaño de respuesta |
| `--filter-regex` | Filtrar con expresión regular |
| `--parameter-fuzz` | Activa fuzzing de parámetros en APIs JSON |

Para ver la lista completa:

```bash
python dosebuster.py --help
```

## 📊 Reportes

Después del escaneo se generan archivos (según formato elegido):
- `dosebuster_report.json` – JSON completo con todos los hallazgos.
- `dosebuster_report.csv` – CSV con directorios y archivos.
- `dosebuster_report.md` – Tabla Markdown lista para pegar en documentación.
- `dosebuster_report.html` – Página web interactiva (si `jinja2` está instalado).

## 🧠 Modo de operación

1. **Baseline** (si `--auto-tune`): se pide un recurso inexistente y se analiza el comportamiento del servidor.
2. Se inserta la URL base en la cola y los trabajadores asíncronos comienzan a probar cada entrada de la wordlist.
3. Al detectar un directorio (código 200, 403, redirecciones, etc.) se encola inmediatamente para explorar en profundidad.
4. En paralelo, se añaden extensiones a cada palabra base para buscar archivos.
5. Los resultados se filtran en tiempo real; los interesantes se guardan y reportan.

## 💡 Ideas disruptivas (hoja de ruta)

- **DeepInfinity**: Crawling ligero de enlaces internos para descubrir rutas fuera del diccionario.
- **Clasificador ML**: Priorizar recursión sobre respuestas con mayor potencial usando scikit‑learn.
- **Fuzzing de parámetros acoplado**: Al detectar APIs JSON, inyecta wordlists de parámetros.
- **Evasión de WAF**: Codificación de ruta, doble encoding, mayúsculas/minúsculas aleatorias.
- **Integración con escáneres**: Búsqueda de secretos en `.env`, backup.sql; fuerza bruta de paneles login.
- **Wordlist adaptativa**: Genera entradas como `v1/api` → `v2/api` basándose en hallazgos.
- **Dashboard WebSocket**: Monitoreo en tiempo real desde el navegador.
- **API REST interna**: Control del escaneo desde otras herramientas.

## 🛡️ Lema

> *“El fuzzer que nunca deja de cavar – by DoseUser”*

## 👤 Créditos

Creado por **DoseUser** con la misión de llevar la enumeración web al siguiente nivel.

## 📜 Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.

---

⭐ ¡Dale una estrella al repo y contribuye con ideas para que DoseBuster nunca deje de cavar!
```
