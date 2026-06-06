#!/usr/bin/env python3
"""
Ruhi CH portrait server — port 8768
POST /upload        → saves one or more images to Ruhi_CH/images/
GET  /images        → JSON list of filenames [{name, url}, ...]
GET  /image/<name>  → serves a specific image
GET  /status        → JSON {count: int}
DELETE /image/<name>→ deletes a specific image
"""
import http.server, os, json, mimetypes, urllib.parse
from pathlib import Path
from datetime import datetime

PORT     = 8768
IMG_DIR  = Path("/home/jo/claude_projects/P046_202604_KnowThyselfAstro/Ruhi_CH/images")
IMG_DIR.mkdir(parents=True, exist_ok=True)

CORS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".heif"}

def list_images():
    files = sorted(
        [f for f in IMG_DIR.iterdir() if f.suffix.lower() in IMAGE_EXTS],
        key=lambda f: f.stat().st_mtime
    )
    return [{"name": f.name, "url": f"/image/{f.name}"} for f in files]

def safe_name(original):
    ext  = Path(original).suffix.lower() or ".jpg"
    if ext == ".heic": ext = ".jpg"
    ts   = datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:22]
    return f"portrait_{ts}{ext}"

def parse_multipart(headers, body):
    """Yield (filename, data) tuples from a multipart body."""
    ct = headers.get("Content-Type", "")
    if "boundary=" not in ct:
        return
    boundary = ("--" + ct.split("boundary=")[-1].strip()).encode()
    parts = body.split(boundary)
    for part in parts[1:]:
        if part in (b"--\r\n", b"--"):
            continue
        if b"\r\n\r\n" not in part:
            continue
        header_block, _, payload = part.partition(b"\r\n\r\n")
        payload = payload.rstrip(b"\r\n")
        headers_text = header_block.decode("utf-8", errors="replace")
        filename = ""
        for line in headers_text.splitlines():
            if "filename=" in line:
                filename = line.split("filename=")[-1].strip().strip('"')
                break
        if filename and payload:
            yield filename, payload

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def _cors(self):
        for k, v in CORS.items():
            self.send_header(k, v)

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = urllib.parse.unquote(self.path.split("?")[0])

        if path == "/images":
            self._json(200, list_images())

        elif path == "/status":
            self._json(200, {"count": len(list_images())})

        elif path.startswith("/image/"):
            name = Path(path[7:]).name  # strip any path traversal
            img_path = IMG_DIR / name
            if img_path.exists() and img_path.suffix.lower() in IMAGE_EXTS:
                data = img_path.read_bytes()
                mime = mimetypes.guess_type(name)[0] or "image/jpeg"
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(data)))
                self._cors()
                self.end_headers()
                self.wfile.write(data)
            else:
                self._json(404, {"error": "not found"})

        else:
            self._json(404, {"error": "not found"})

    def do_DELETE(self):
        path = urllib.parse.unquote(self.path)
        if path.startswith("/image/"):
            name = Path(path[7:]).name
            img_path = IMG_DIR / name
            if img_path.exists() and img_path.suffix.lower() in IMAGE_EXTS:
                img_path.unlink()
                self._json(200, {"ok": True, "deleted": name})
            else:
                self._json(404, {"error": "not found"})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/upload":
            self._json(404, {"error": "not found"}); return

        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)
        saved  = []

        ct = self.headers.get("Content-Type", "")
        if "multipart/form-data" in ct:
            for orig_name, data in parse_multipart(self.headers, body):
                fname = safe_name(orig_name)
                (IMG_DIR / fname).write_bytes(data)
                saved.append(fname)
        else:
            fname = safe_name("upload.jpg")
            (IMG_DIR / fname).write_bytes(body)
            saved.append(fname)

        self._json(200, {"ok": True, "saved": saved, "images": list_images()})

if __name__ == "__main__":
    with http.server.HTTPServer(("0.0.0.0", PORT), Handler) as srv:
        print(f"Ruhi portrait server → http://0.0.0.0:{PORT}/")
        srv.serve_forever()
