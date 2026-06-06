#!/usr/bin/env python3
"""
Ruhi CH chart image server — port 8768
POST /upload  → saves image to Ruhi_CH/images/ruhi_chart.jpg
GET  /chart   → serves the chart image (or 404)
GET  /status  → JSON {exists: bool}
"""
import http.server, os, json, mimetypes
from pathlib import Path
from email import message_from_bytes

PORT      = 8768
IMG_PATH  = Path("/home/jo/claude_projects/P046_202604_KnowThyselfAstro/Ruhi_CH/images/ruhi_chart.jpg")
IMG_PATH.parent.mkdir(parents=True, exist_ok=True)

CORS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass  # quiet

    def _cors(self):
        for k, v in CORS.items():
            self.send_header(k, v)

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/chart":
            if IMG_PATH.exists():
                data = IMG_PATH.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(data)))
                self._cors()
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(404)
                self._cors()
                self.end_headers()
        elif self.path == "/status":
            body = json.dumps({"exists": IMG_PATH.exists()}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self._cors()
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path != "/upload":
            self.send_response(404); self.end_headers(); return

        ct = self.headers.get("Content-Type", "")
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)

        # multipart upload
        if "multipart/form-data" in ct:
            boundary = ct.split("boundary=")[-1].strip()
            msg = message_from_bytes(
                f"Content-Type: {ct}\r\n\r\n".encode() + raw
            )
            for part in msg.get_payload():
                if hasattr(part, 'get_payload'):
                    cd = part.get("Content-Disposition", "")
                    if "filename" in cd:
                        img_data = part.get_payload(decode=True)
                        if img_data:
                            IMG_PATH.write_bytes(img_data)
                            break
        else:
            # raw binary post
            IMG_PATH.write_bytes(raw)

        body = json.dumps({"ok": True, "path": str(IMG_PATH)}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    with http.server.HTTPServer(("0.0.0.0", PORT), Handler) as srv:
        print(f"Ruhi chart server → http://0.0.0.0:{PORT}/")
        srv.serve_forever()
