
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://readme-typing-svg.herokuapp.com?font=Fira+Code&size=28&duration=3000&pause=500&color=00F0FF&center=true&vCenter=true&width=600&lines=%F0%9F%92%A3+DoseBuster;El+fuzzer+que+nunca+deja+de+cavar" />
    <source media="(prefers-color-scheme: light)" srcset="https://readme-typing-svg.herokuapp.com?font=Fira+Code&size=28&duration=3000&pause=500&color=1E1E2E&center=true&vCenter=true&width=600&lines=%F0%9F%92%A3+DoseBuster;El+fuzzer+que+nunca+deja+de+cavar" />
    <img alt="DoseBuster - The fuzzer that never stops digging" src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&size=28&duration=3000&pause=500&color=00F0FF&center=true&vCenter=true&width=600&lines=%F0%9F%92%A3+DoseBuster;El+fuzzer+que+nunca+deja+de+cavar" />
  </picture>
</p>

<div align="center">

```
  ____                ____             _           
 |  _ \  ___  ___  __| __ ) _   _ ___| |_ ___ _ __ 
 | | | |/ _ \/ __|/ _  |  _ \| | | / __| __/ _ \ '__|
 | |_| | (_) \__ \ (_| | |_) | |_| \__ \ ||  __/ |   
 |____/ \___/|___/\__,_|____/ \__,_|___/\__\___|_|   
```

**The fuzzer that never stops digging — by DoseUser**

</div>

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8+-3B82F6?style=for-the-badge&logo=python&logoColor=white&labelColor=1E1E2E)](#)
[![Async](https://img.shields.io/badge/Async-100%25-9B59B6?style=for-the-badge&logo=asyncio&logoColor=white&labelColor=1E1E2E)](#)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge&logo=github&logoColor=white&labelColor=1E1E2E)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-EAB308?style=for-the-badge&logo=github&logoColor=white&labelColor=1E1E2E)](CONTRIBUTING.md)
[![Built with Fire](https://img.shields.io/badge/Built_with_%F0%9F%94%A5-DoseUser-FF4500?style=for-the-badge&labelColor=1E1E2E)](#)

</div>

---

## ⚡ *Why DoseBuster?*

> *Most fuzzers crawl linearly. DoseBuster digs recursively **in real-time** — every directory found becomes a new battlefield **immediately**, without waiting for the current job to finish. It’s like having a thousand shovel-blades hitting the server at once, but smarter.*

| 💥 Feature | 🔍 DoseBuster |
|-----------|-------------|
| **Instant Recursion** | New directories are queued **as soon as discovered**, using an adaptive producer-consumer model |
| **Dual Enumeration** | Simultaneous dir fuzzing + file discovery (`.bak`, `.zip`, `.git/config`, etc.) at every depth |
| **100% Async Python** | `asyncio` + `aiohttp` — reusable connections, intelligent retries, zero overhead |
| **False‑Positive Engine** | `--auto-tune` probes a non‑existent resource and creates a fingerprint to filter noise |
| **Stateful Resume** | Exact progress saved to disk — stop anytime and resume without reprocessing |
| **Stealth & Evasion** | Randomized delays, multiple User‑Agents, proxy support, jitter, and WAF‑aware path mutations |
| **Advanced Filters** | Filter by status, size, regex, word match, similarity ratio, and combine them with **AND/OR** logic |
| **Rich Reporting** | Live colored console, JSON, CSV, Markdown, and interactive HTML reports |

---

## 📦 Installation

```bash
git clone https://github.com/Doseuser/DoseBuster.git && cd DoseBuster
pip install -r requirements.txt
```

**Dependencies:**  
[`aiohttp`](https://pypi.org/project/aiohttp/) • [`colorama`](https://pypi.org/project/colorama/) • [`pyyaml`](https://pypi.org/project/pyyaml/) • [`jinja2`](https://pypi.org/project/jinja2/) *(optional, for HTML reports)*

---

## 🚀 Quick Start

```bash
python dosebuster.py https://example.com -w wordlist.txt -x .bak,.zip,.php -d 3 --auto-tune -c 50
```

**See all flags:**
```bash
python dosebuster.py --help
```

<details>
<summary><b>🔍 Core Flags</b></summary>

| Flag | Description |
|------|-------------|
| `-w` / `--wordlist` | Path to directory wordlist file |
| `-x` / `--extensions` | Comma-separated extensions to append (e.g., `.bak,.zip,.php`) |
| `-d` / `--depth` | Maximum recursion depth (default: 2) |
| `-c` / `--concurrency` | Simultaneous async workers (default: 30) |
| `--auto-tune` | Automatically detect and ignore custom error pages / wildcards |
| `--filter-code` | Only show responses with given status codes (e.g., `200,403`) |
| `--filter-size` | Only show responses with given content lengths |
| `--filter-regex` | Filter responses matching a regular expression |
| `--filter-words` | Filter responses containing specific words |
| `--filter-similarity` | Keep responses whose similarity to the baseline lies within a range (e.g., `0.5,0.9`) |
| `--filter-logic` | `and` or `or` — combine multiple filters (default: `or`) |
| `-f` / `--format` | Comma-separated output formats: `json`, `csv`, `md`, `html` |
| `--output` | Output file base name (default: `dosebuster_report`) |
| `--state-file` | File to save/load scan state (resume support) |
| `--resume` | Resume a previously interrupted scan |
| `--stealth` | Enable randomized delays, slower pace, and avoid detection |
| `--delay` | Fixed delay between requests (per worker) |
| `--jitter` | Maximum random jitter added to delay |
| `--rate-limit` | Global request-per-second cap |
| `--proxy` | HTTP proxy (e.g., `http://127.0.0.1:8080`) |
| `--rotate-ua` | Rotate User-Agent from a built-in list on every request |
| `--follow-redirects` | Follow HTTP redirects |
| `--output-all` | Print every checked URL to console, regardless of filter |
| `--parameter-fuzz` | Enable parameter fuzzing on JSON endpoints found |
| `--param-wordlist` | Custom wordlist for parameters (used with `--parameter-fuzz`) |

</details>

---

## 🧠 How It Works

1. **Baseline building** – If `--auto-tune` is on, DoseBuster requests a random fake path and records the server’s “not found” fingerprint.
2. **Queue bootstrap** – The base URL enters the async queue.
3. **Concurrent workers** – Each worker pops a directory from the queue and tests every wordlist entry + every extension against it.
4. **Real-time recursion** – When a hit is identified (HTTP status, redirect, or custom heuristics), that directory is **immediately re-queued** with a deeper depth.
5. **Filtering & false-positive removal** – Every response is compared to the baseline and tested against user-defined filters.
6. **Live feedback** – The console shows request count, directories/files found, and queue size, updating in place.
7. **Report generation** – At the end (or on interruption), all findings are exported in the chosen formats.

---

## 📊 Sample Report Snippets

<details open>
<summary><b>Console output</b></summary>

```
  ____                ____             _           
 |  _ \  ___  ___  __| __ ) _   _ ___| |_ ___ _ __ 
 | | | |/ _ \/ __|/ _  |  _ \| | | / __| __/ _ \ '__|
 | |_| | (_) \__ \ (_| | |_) | |_| \__ \ ||  __/ |   
 |____/ \___/|___/\__,_|____/ \__,_|___/\__\___|_|   
                                            by DoseUser

Progreso: 1242 peticiones | Directorios: 7 | Archivos: 13 | Cola: 45   
[200] https://example.com/admin/
[403] https://example.com/backup/
[200] https://example.com/.git/config
[200] https://example.com/wp-config.php.bak
...
```

</details>

<details>
<summary><b>JSON export</b></summary>

```json
{
  "directories": [
    {"url": "https://example.com/admin/", "depth": 1, "status": "found"},
    {"url": "https://example.com/api/", "depth": 1, "status": "found"}
  ],
  "files": [
    {"url": "https://example.com/.env.bak", "depth": 1, "status": 200, "size": 1024},
    {"url": "https://example.com/backup.sql.zip", "depth": 2, "status": 200, "size": 4056}
  ]
}
```

</details>

---

## 🗺️ Roadmap — Disruptive Upgrades

- [ ] **DeepInfinity** – Lightweight internal crawler that follows discovered links to uncover dictionary‑less routes.
- [ ] **ML‑powered Classifier** – Train a small scikit‑learn model on‑the‑fly to prioritize “juicy” directories.
- [ ] **Parameter Fuzz Expansion** – Detect API endpoints (JSON content‑type) and automatically fuzz query/POST params.
- [ ] **WAF Evasion Kit** – URL encoding tricks, double encoding, upper/lower case randomization, truncation.
- [ ] **Secret Extractor** – On finding `.env`, `backup.sql`, etc., launch regex‑based secret mining.
- [ ] **Default Credential Attack** – If a login form is found, try common/default credentials.
- [ ] **Predictive Wordlist** – Dynamically generate variations (e.g., `v1/api` → `v2/api`, `v3/api`).
- [ ] **Live WebSocket Dashboard** – Monitor scan progress from a browser in real time.
- [ ] **Internal REST API** – Pause, resume, modify wordlists on the fly, and stream results to other tools.
- [ ] **Multi‑IP Stealth** – Bind workers to different network interfaces for IP rotation.

---

## 🤝 Contributing

> *DoseBuster is crafted to be the ultimate enumeration tool. Have an idea for a disruptive feature? Open an issue or a PR — let’s make it happen.*

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/amazing-idea`)
3. Commit your changes (`git commit -m 'Add amazing idea'`)
4. Push to the branch (`git push origin feature/amazing-idea`)
5. Open a Pull Request

---

## 👤 Author

**DoseUser** — cybersecurity craftsman, builder of the fuzzer that never stops digging.

---

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

<div align="center">

### ⭐ Don’t forget to star the repo if you like it!

*Made with 💣 and async love*

</div>
```
