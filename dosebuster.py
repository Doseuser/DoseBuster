import asyncio
import aiohttp
import argparse
import sys
import os
import json
import csv
import time
import random
import re
import yaml
import signal
import string
import hashlib
from urllib.parse import urljoin, urlparse, quote, unquote
from difflib import SequenceMatcher
from collections import defaultdict
from colorama import init, Fore, Style
init(autoreset=True)

try:
    from jinja2 import Template
    HAS_JINJA = True
except ImportError:
    HAS_JINJA = False

DEFAULT_WORDLIST = [
    "admin", "backup", "config", "db", "login", "wp-admin", "api",
    "uploads", "images", "js", "css", "temp", "test", "old", "new",
    "v1", "v2", "private", "secret", "logs", "sql", "dump", "backup.zip",
    "archive.tar.gz", "web.config", ".git", ".env", "robots.txt"
]

DEFAULT_EXTENSIONS = [".bak", ".zip", ".php", ".asp", ".aspx", ".jsp", ".txt", ".old", ".tar.gz", ".sql", ".git/config"]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
]

class DoseBuster:
    def __init__(self, args):
        self.args = args
        self.wordlist = []
        self.extensions = []
        self.base_url = args.url.rstrip('/')
        self.max_depth = args.depth
        self.concurrency = args.concurrency
        self.rate_limit = args.rate_limit
        self.delay = args.delay
        self.jitter = args.jitter
        self.proxy = args.proxy
        self.user_agents = USER_AGENTS
        self.rotate_ua = args.rotate_ua
        self.stealth = args.stealth
        self.auto_tune = args.auto_tune
        self.baseline = None
        self.semaphore = asyncio.Semaphore(self.concurrency)
        self.queue = asyncio.Queue()
        self.results = {"directories": [], "files": [], "interesting": []}
        self.found_dirs = set()
        self.found_files = set()
        self.completed_urls = set()
        self.pending_dirs = set()
        self.total_requests = 0
        self.state_file = args.state_file
        self.output_file = args.output
        self.output_format = args.format
        self.filter_code = args.filter_code
        self.filter_size = args.filter_size
        self.filter_words = args.filter_words
        self.filter_regex = args.filter_regex
        self.filter_similarity = args.filter_similarity
        self.filter_logic = args.filter_logic
        self.timeout = aiohttp.ClientTimeout(total=args.timeout)
        self.session = None
        self.should_stop = False

    async def load_wordlist(self):
        if self.args.wordlist:
            with open(self.args.wordlist, 'r', encoding='utf-8', errors='ignore') as f:
                self.wordlist = [line.strip() for line in f if line.strip()]
        else:
            self.wordlist = DEFAULT_WORDLIST
        if self.args.extensions:
            self.extensions = self.args.extensions.split(',')
        else:
            self.extensions = DEFAULT_EXTENSIONS
        if self.args.lowercase:
            self.wordlist = list(set(w.lower() for w in self.wordlist))
        if self.args.uppercase:
            self.wordlist = list(set(w.upper() for w in self.wordlist))

    def get_random_ua(self):
        if self.rotate_ua:
            return random.choice(self.user_agents)
        return self.args.user_agent or self.user_agents[0]

    async def create_session(self):
        connector = aiohttp.TCPConnector(limit=0, force_close=False)
        headers = {"User-Agent": self.get_random_ua()}
        if self.args.headers:
            for h in self.args.headers:
                if ':' in h:
                    k, v = h.split(':', 1)
                    headers[k.strip()] = v.strip()
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout,
            headers=headers,
            trust_env=True
        )

    async def fetch(self, url, retries=1):
        for attempt in range(retries + 1):
            try:
                async with self.semaphore:
                    if self.rotate_ua:
                        self.session.headers['User-Agent'] = self.get_random_ua()
                    proxy = self.proxy if self.proxy else None
                    async with self.session.get(url, proxy=proxy, allow_redirects=self.args.follow_redirects, ssl=False) as resp:
                        content = await resp.text()
                        return resp, content
            except (aiohttp.ClientError, asyncio.TimeoutError):
                if attempt == retries:
                    raise
                await asyncio.sleep(1)
        return None, ""

    async def baseline_scan(self):
        non_existent = ''.join(random.choices(string.ascii_lowercase, k=12))
        url = self.base_url + '/' + non_existent + '/'
        resp, content = await self.fetch(url)
        if resp:
            self.baseline = {
                'status': resp.status,
                'headers': dict(resp.headers),
                'content': content,
                'length': len(content)
            }
        else:
            self.baseline = {'status': 404, 'headers': {}, 'content': '', 'length': 0}

    def similarity(self, a, b):
        if not a or not b:
            return 0
        return SequenceMatcher(None, a, b).ratio()

    def is_false_positive(self, resp, content):
        if not self.auto_tune or not self.baseline:
            return False
        if resp.status == self.baseline['status'] and resp.status not in (200, 301, 302, 307, 308):
            return True
        if len(content) == self.baseline['length'] and self.similarity(content, self.baseline['content']) > 0.9:
            return True
        if self.baseline['length'] > 0 and abs(len(content) - self.baseline['length']) < 5:
            if self.similarity(content, self.baseline['content']) > 0.8:
                return True
        return False

    def apply_filters(self, url, resp, content):
        if self.filter_code:
            codes = [int(c) for c in self.filter_code.split(',')]
            if resp.status not in codes:
                return False
        if self.filter_size:
            sizes = [int(s) for s in self.filter_size.split(',')]
            if len(content) not in sizes:
                return False
        if self.filter_words:
            words = self.filter_words.split(',')
            if not any(w in content for w in words):
                return False
        if self.filter_regex:
            if not re.search(self.filter_regex, content):
                return False
        if self.filter_similarity:
            sims = [float(x) for x in self.filter_similarity.split(',')]
            if self.baseline and self.baseline.get('content'):
                sim = self.similarity(content, self.baseline['content'])
                if not (sims[0] <= sim <= sims[1]):
                    return False
        if self.filter_logic == 'and':
            return True
        return True

    def detect_directory(self, url, resp, content):
        if resp.status in (200, 403, 401, 500, 301, 302):
            if 'Location' in resp.headers:
                redirect = resp.headers['Location']
                if redirect.rstrip('/') != url.rstrip('/'):
                    return True
            return True
        return False

    async def handle_found_dir(self, url, depth):
        if url in self.found_dirs or depth >= self.max_depth:
            return
        self.found_dirs.add(url)
        self.results["directories"].append({"url": url, "depth": depth, "status": "found"})
        self.results["interesting"].append({"url": url, "depth": depth, "type": "directory", "status": "found"})
        if self.args.recursive:
            await self.queue.put((url, depth + 1))

    async def handle_found_file(self, url, depth, resp, content):
        if url in self.found_files:
            return
        self.found_files.add(url)
        self.results["files"].append({"url": url, "depth": depth, "status": resp.status, "size": len(content)})
        self.results["interesting"].append({"url": url, "depth": depth, "type": "file", "status": resp.status, "size": len(content)})
        if self.args.parameter_fuzz and 'json' in resp.headers.get('Content-Type', '').lower():
            await self.fuzz_parameters(url)

    async def fuzz_parameters(self, base_url):
        params = self.args.param_wordlist or ['id', 'page', 'user', 'admin', 'debug', 'file', 'path']
        for param in params:
            fuzz_url = f"{base_url}?{param}=test"
            await self.queue.put((fuzz_url, -1))

    def normalize_url(self, url):
        parsed = urlparse(url)
        path = parsed.path
        if not path.endswith('/'):
            path += '/'
        return parsed._replace(path=path).geturl()

    async def process_directory(self, base, depth):
        normalized_base = self.normalize_url(base)
        tasks = []
        for word in self.wordlist:
            dir_url = urljoin(normalized_base, word) + '/'
            task = asyncio.ensure_future(self.check_url(dir_url, depth, is_dir=True))
            tasks.append(task)
            for ext in self.extensions:
                if ext.startswith('.'):
                    file_url = urljoin(normalized_base, word + ext)
                else:
                    file_url = urljoin(normalized_base, ext)
                task = asyncio.ensure_future(self.check_url(file_url, depth, is_dir=False))
                tasks.append(task)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def check_url(self, url, depth, is_dir):
        if self.should_stop:
            return
        if url in self.completed_urls:
            return
        self.total_requests += 1
        try:
            delay = self.delay
            if self.jitter:
                delay += random.uniform(0, self.jitter)
            if self.stealth:
                delay += random.uniform(1, 3)
            await asyncio.sleep(delay)
            if self.rate_limit > 0:
                await asyncio.sleep(1.0 / self.rate_limit)
            resp, content = await self.fetch(url, retries=self.args.retries)
            if not resp:
                return
            self.completed_urls.add(url)
            if self.is_false_positive(resp, content):
                return
            if not self.apply_filters(url, resp, content):
                return
            if is_dir and self.detect_directory(url, resp, content):
                await self.handle_found_dir(url, depth)
            elif not is_dir and resp.status in (200, 301, 302, 307, 308):
                await self.handle_found_file(url, depth, resp, content)
            if self.args.output_all:
                print(f"[{resp.status}] {url}")
        except Exception:
            pass

    async def worker(self, worker_id):
        while not self.should_stop:
            try:
                item = await asyncio.wait_for(self.queue.get(), timeout=1)
            except asyncio.TimeoutError:
                continue
            url, depth = item
            if self.args.recursive and depth < self.max_depth:
                await self.process_directory(url, depth)
            self.queue.task_done()

    async def progress_reporter(self):
        while not self.should_stop:
            print(f"\r{Fore.CYAN}Progreso: {self.total_requests} peticiones | Directorios: {len(self.found_dirs)} | Archivos: {len(self.found_files)} | Cola: {self.queue.qsize()}   ", end='', flush=True)
            await asyncio.sleep(2)

    def display_banner(self):
        banner = f"""{Fore.MAGENTA}{Style.BRIGHT}
  ____                ____             _           
 |  _ \\  ___  ___  __| __ ) _   _ ___| |_ ___ _ __ 
 | | | |/ _ \\/ __|/ _  |  _ \\| | | / __| __/ _ \\ '__|
 | |_| | (_) \\__ \\ (_| | |_) | |_| \\__ \\ ||  __/ |   
 |____/ \\___/|___/\\__,_|____/ \\__,_|___/\\__\\___|_|   
        {Fore.YELLOW}El fuzzer que nunca deja de cavar – by DoseUser
        {Style.RESET_ALL}"""
        print(banner)

    def save_state(self):
        state = {
            "base_url": self.base_url,
            "depth": self.max_depth,
            "completed_urls": list(self.completed_urls),
            "found_dirs": list(self.found_dirs),
            "found_files": list(self.found_files),
            "pending_dirs": list(self.pending_dirs),
            "results": self.results
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
        print(f"\n{Fore.GREEN}Estado guardado en {self.state_file}")

    def load_state(self):
        if not os.path.exists(self.state_file):
            return False
        with open(self.state_file, 'r') as f:
            state = json.load(f)
        self.completed_urls = set(state.get("completed_urls", []))
        self.found_dirs = set(state.get("found_dirs", []))
        self.found_files = set(state.get("found_files", []))
        self.results = state.get("results", {"directories":[],"files":[],"interesting":[]})
        pending = state.get("pending_dirs", [])
        for url, depth in pending:
            self.pending_dirs.add(url)
            self.queue.put_nowait((url, depth))
        print(f"{Fore.GREEN}Reanudando con {len(self.completed_urls)} URLs completadas, {self.queue.qsize()} pendientes")
        return True

    def generate_reports(self):
        if self.output_format == 'json' or 'json' in self.output_format:
            self.generate_json_report()
        if self.output_format == 'csv' or 'csv' in self.output_format:
            self.generate_csv_report()
        if self.output_format == 'md' or 'markdown' in self.output_format:
            self.generate_markdown_report()
        if self.output_format == 'html' and HAS_JINJA:
            self.generate_html_report()

    def generate_json_report(self):
        with open(self.output_file + ".json", 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"{Fore.GREEN}Reporte JSON: {self.output_file}.json")

    def generate_csv_report(self):
        with open(self.output_file + ".csv", 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["tipo", "url", "estado", "profundidad", "tamano"])
            for d in self.results["directories"]:
                writer.writerow(["directorio", d["url"], d.get("status",""), d["depth"], ""])
            for fi in self.results["files"]:
                writer.writerow(["archivo", fi["url"], fi["status"], fi["depth"], fi.get("size","")])
        print(f"{Fore.GREEN}Reporte CSV: {self.output_file}.csv")

    def generate_markdown_report(self):
        with open(self.output_file + ".md", 'w') as f:
            f.write("# DoseBuster Report\n")
            f.write("| Tipo | URL | Estado | Profundidad | Tamaño |\n")
            f.write("|------|-----|--------|-------------|--------|\n")
            for d in self.results["directories"]:
                f.write(f"| Directorio | {d['url']} | {d.get('status','')} | {d['depth']} | |\n")
            for fi in self.results["files"]:
                f.write(f"| Archivo | {fi['url']} | {fi['status']} | {fi['depth']} | {fi.get('size','')} |\n")
        print(f"{Fore.GREEN}Reporte Markdown: {self.output_file}.md")

    def generate_html_report(self):
        template = Template("""
        <html><head><title>DoseBuster Report</title></head><body>
        <h1>DoseBuster Scan Results</h1>
        <table border="1">
        <tr><th>Type</th><th>URL</th><th>Status</th><th>Depth</th><th>Size</th></tr>
        {% for d in results.directories %}<tr><td>Directory</td><td>{{d.url}}</td><td>{{d.status}}</td><td>{{d.depth}}</td><td></td></tr>{% endfor %}
        {% for fi in results.files %}<tr><td>File</td><td>{{fi.url}}</td><td>{{fi.status}}</td><td>{{fi.depth}}</td><td>{{fi.size}}</td></tr>{% endfor %}
        </table></body></html>
        """)
        html = template.render(results=self.results)
        with open(self.output_file + ".html", 'w') as f:
            f.write(html)
        print(f"{Fore.GREEN}Reporte HTML: {self.output_file}.html")

    async def run(self):
        self.display_banner()
        await self.load_wordlist()
        await self.create_session()
        if self.auto_tune:
            await self.baseline_scan()
        if self.args.resume and os.path.exists(self.state_file):
            loaded = self.load_state()
            if loaded:
                pass
        else:
            self.queue.put_nowait((self.base_url, 0))
        workers = [asyncio.create_task(self.worker(i)) for i in range(self.concurrency)]
        reporter = asyncio.create_task(self.progress_reporter())
        loop = asyncio.get_running_loop()
        def shutdown():
            self.should_stop = True
            print("\nDeteniendo...")
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, shutdown)
        await self.queue.join()
        self.should_stop = True
        reporter.cancel()
        for w in workers:
            w.cancel()
        await asyncio.gather(*workers, reporter, return_exceptions=True)
        await self.session.close()
        self.generate_reports()
        if self.state_file:
            self.save_state()

def main():
    parser = argparse.ArgumentParser(description="DoseBuster - El fuzzer que nunca deja de cavar - by DoseUser")
    parser.add_argument("url", help="URL base para el escaneo")
    parser.add_argument("-w", "--wordlist", help="Archivo de wordlist para directorios")
    parser.add_argument("-x", "--extensions", help="Extensiones separadas por coma, ej: .bak,.zip,.php")
    parser.add_argument("-d", "--depth", type=int, default=2, help="Profundidad máxima de recursión")
    parser.add_argument("-c", "--concurrency", type=int, default=30, help="Conexiones simultáneas")
    parser.add_argument("--rate-limit", type=int, default=0, help="Peticiones por segundo globales")
    parser.add_argument("--delay", type=float, default=0, help="Demora fija entre peticiones por hilo")
    parser.add_argument("--jitter", type=float, default=0, help="Jitter aleatorio máximo agregado a la demora")
    parser.add_argument("--timeout", type=int, default=10, help="Timeout de petición en segundos")
    parser.add_argument("--retries", type=int, default=1, help="Reintentos por petición")
    parser.add_argument("--follow-redirects", action="store_true", help="Seguir redirecciones")
    parser.add_argument("--auto-tune", action="store_true", help="Detección automática de falsos positivos")
    parser.add_argument("--filter-code", help="Filtrar por códigos de estado (ej: 200,403)")
    parser.add_argument("--filter-size", help="Filtrar por tamaño de respuesta (ej: 0,1234)")
    parser.add_argument("--filter-words", help="Filtrar por palabras en el contenido")
    parser.add_argument("--filter-regex", help="Filtrar por expresión regular en el cuerpo")
    parser.add_argument("--filter-similarity", help="Rango de similitud con baseline (ej: 0.5,0.9)")
    parser.add_argument("--filter-logic", choices=["and","or"], default="or", help="Lógica de combinación de filtros")
    parser.add_argument("--output", default="dosebuster_report", help="Nombre base del archivo de salida")
    parser.add_argument("-f", "--format", default="json,csv,md", help="Formatos de salida: json,csv,md,html")
    parser.add_argument("--state-file", default="dosebuster.state", help="Archivo de estado para reanudar")
    parser.add_argument("--resume", action="store_true", help="Reanudar escaneo desde archivo de estado")
    parser.add_argument("--proxy", help="Proxy HTTP (ej: http://127.0.0.1:8080)")
    parser.add_argument("--user-agent", help="User-Agent personalizado")
    parser.add_argument("--rotate-ua", action="store_true", help="Rotar User-Agents por petición")
    parser.add_argument("--headers", nargs="*", help="Cabeceras adicionales (Formato: 'Clave: Valor')")
    parser.add_argument("--stealth", action="store_true", help="Modo sigiloso con delays aleatorios")
    parser.add_argument("--recursive", action="store_true", default=True, help="Enumeración recursiva (defecto: activo)")
    parser.add_argument("--lowercase", action="store_true", help="Convertir wordlist a minúsculas")
    parser.add_argument("--uppercase", action="store_true", help="Convertir wordlist a mayúsculas")
    parser.add_argument("--output-all", action="store_true", help="Mostrar todos los resultados por consola")
    parser.add_argument("--parameter-fuzz", action="store_true", help="Fuzzing de parámetros en respuestas JSON")
    parser.add_argument("--param-wordlist", nargs="*", help="Wordlist de parámetros a probar")
    args = parser.parse_args()
    scanner = DoseBuster(args)
    try:
        asyncio.run(scanner.run())
    except KeyboardInterrupt:
        if scanner.state_file:
            scanner.save_state()
        sys.exit(1)

if __name__ == "__main__":
    main()
