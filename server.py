#!/usr/bin/env python3
"""
server.py — Lightweight static web server with Steam store asset resolver.
Serves web/ static files and provides a zero-config /api/steam-details endpoint
to resolve modern Steam Store hashed header assets without CORS issues.
"""

import http.server
import json
import os
import socketserver
import urllib.request
import urllib.parse

PORT = 8000
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

class SteamCapsuluHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
        # Steam AppDetails proxy endpoint
        if parsed.path == "/api/steam-details":
            params = urllib.parse.parse_qs(parsed.query)
            appid = params.get("appid", [None])[0]
            
            if not appid:
                self.send_error(400, "Missing appid parameter")
                return

            try:
                steam_api_url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
                req = urllib.request.Request(
                    steam_api_url, 
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode("utf-8"))

                app_data = data.get(str(appid), {}).get("data", {})
                if not app_data:
                    res_payload = {"success": False, "error": "Game data not found on Steam"}
                else:
                    rel_info = app_data.get("release_date", {})
                    is_coming_soon = rel_info.get("coming_soon", False)
                    rel_date = rel_info.get("date", "")
                    
                    if app_data.get("is_free"):
                        price_str = "Free to Play"
                    elif app_data.get("price_overview"):
                        price_str = app_data.get("price_overview", {}).get("final_formatted", "N/A")
                    elif is_coming_soon:
                        price_str = "Coming Soon"
                    else:
                        price_str = "Free"

                    review_status = "Coming Soon" if is_coming_soon else "Positive"

                    res_payload = {
                        "success": True,
                        "appid": int(appid),
                        "name": app_data.get("name"),
                        "header_image": app_data.get("header_image"),
                        "capsule_image": app_data.get("capsule_image"),
                        "price": price_str,
                        "is_coming_soon": is_coming_soon,
                        "release_date": rel_date,
                        "review_status": review_status,
                        "genres": [g.get("description") for g in app_data.get("genres", [])]
                    }

                body = json.dumps(res_payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            except Exception as e:
                err_body = json.dumps({"success": False, "error": str(e)}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(err_body)))
                self.end_headers()
                self.wfile.write(err_body)
                return

        # Default static file handler
        return super().do_GET()

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), SteamCapsuluHandler) as httpd:
        print(f"🚀 Capsulu Server running at http://localhost:{PORT}")
        httpd.serve_forever()
