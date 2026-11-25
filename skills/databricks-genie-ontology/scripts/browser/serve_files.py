#!/usr/bin/env python3
"""Throwaway local file server used to move large generated cells into the Databricks page.

    python3 serve_files.py <directory> <port> <allowed-origin>
    e.g. python3 serve_files.py /tmp/cells 8765 https://<your-workspace-host>

Hardening (all enforced in code):
  * the directory is REQUIRED and must be a dedicated folder: startup is refused if ANYWHERE in its tree there is a file or folder
    named config.env, STATE.md, .env, .git, .ssh, .aws and similar secret names;
  * every request is resolved with realpath and must stay inside that folder (symlinks pointing outside are refused), and no
    path component may be one of those secret names;
  * CORS allows ONLY the one origin you pass (no wildcard), so other websites open in your browser cannot read the files;
  * every request path must start with a random token printed at startup; directory listings are disabled;
  * only .py/.json/.js/.md/.txt/.yaml files are served; binds to 127.0.0.1 only.
Fetch from the page with:   await (await fetch('http://127.0.0.1:PORT/<token>/<file>', {credentials:'omit'})).text()
and STOP the server when done (Ctrl-C or pkill -f serve_files.py).
"""
import http.server
import os
import secrets
import socketserver
import sys

SENSITIVE = {"config.env", "STATE.md", ".env", ".git", ".ssh", ".netrc", "id_rsa", ".aws", ".npmrc"}
ALLOWED_EXT = (".py", ".json", ".js", ".md", ".txt", ".yaml", ".yml")


def refuse(msg):
    print("refusing to start: " + msg, file=sys.stderr)
    sys.exit(2)


if len(sys.argv) != 4:
    refuse("usage: serve_files.py <directory> <port> <allowed-origin>")
root = os.path.realpath(sys.argv[1])
port = int(sys.argv[2])
origin = sys.argv[3].rstrip("/")
if not os.path.isdir(root):
    refuse(f"{root} is not a directory")
if not origin.startswith("http"):
    refuse("allowed-origin must be a full origin such as https://workspace-host.example")
hits = sorted({n for _, dirs, files in os.walk(root) for n in dirs + files if n in SENSITIVE})
if hits:
    refuse(f"{root} contains sensitive name(s) {hits}; copy only the generated files into a fresh directory")
os.chdir(root)
TOKEN = secrets.token_urlsafe(12)


class Handler(http.server.SimpleHTTPRequestHandler):
    def _ok_path(self):
        parts = self.path.split("?")[0].lstrip("/").split("/", 1)
        return len(parts) == 2 and parts[0] == TOKEN and parts[1].endswith(ALLOWED_EXT) and ".." not in parts[1]

    def translate_path(self, path):
        return super().translate_path("/" + path.split("?")[0].lstrip("/").split("/", 1)[-1])

    def list_directory(self, path):
        self.send_error(404)

    def _inside_root(self):
        target = os.path.realpath(self.translate_path(self.path))
        if os.path.commonpath([target, root]) != root:                 # symlink or traversal leaving the folder
            return False
        return not any(part in SENSITIVE for part in os.path.relpath(target, root).split(os.sep))

    def send_head(self):
        if not (self._ok_path() and self._inside_root()):
            self.send_error(404)
            return None
        return super().send_head()

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Access-Control-Allow-Methods", "GET,OPTIONS")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def log_message(self, *args):
        pass


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", port), Handler) as srv:
    print(f"serving {root} on http://127.0.0.1:{port}/{TOKEN}/<file>  (allowed origin {origin}; Ctrl-C to stop)", flush=True)
    srv.serve_forever()
