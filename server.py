#!/usr/bin/env python3
import http.server
import socketserver
import os
import json
import mimetypes
import server_engine

# Load .env file for local environment variables if it exists
if os.path.exists(".env"):
    try:
        with open(".env", "r", encoding="utf-8") as dotenv_file:
            for dotenv_line in dotenv_file:
                dotenv_line = dotenv_line.strip()
                if dotenv_line and not dotenv_line.startswith("#"):
                    dotenv_kv = dotenv_line.split("=", 1)
                    if len(dotenv_kv) == 2:
                        dotenv_key, dotenv_val = dotenv_kv
                        # Remove whitespace and surrounding quotes
                        dotenv_val = dotenv_val.strip().strip("'\"")
                        os.environ[dotenv_key.strip()] = dotenv_val
    except Exception as dotenv_err:
        print(f"Warning: Failed to load .env file: {dotenv_err}")

PORT = int(os.environ.get("PYTHON_PORT", 3001))

class ChessRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        try:
            with open("server.log", "a", encoding="utf-8") as f:
                f.write(f"[{self.log_date_time_string()}] {self.address_string()} - " + (format % args) + "\n")
        except:
            pass

    def end_headers(self):
        # Enable CORS for local convenience
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        # Support CORS preflight
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        # Handle API routes
        if self.path == "/api/history":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            history_file = "history.json"
            if os.path.exists(history_file):
                with open(history_file, "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode("utf-8"))
            else:
                self.wfile.write(b"[]")
            return
            
        elif self.path == "/api/rl_memory":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            rl_file = "rl_memory.json"
            if os.path.exists(rl_file):
                with open(rl_file, "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode("utf-8"))
            else:
                default_rl = {
                    "games_played": 0,
                    "bot_wins": 0,
                    "bot_losses": 0,
                    "bot_draws": 0,
                    "q_table": {},
                    "recent_learnings": []
                }
                self.wfile.write(json.dumps(default_rl).encode("utf-8"))
            return

        # Fallback SPA routing / standard static files
        # Normalize path
        normalized_path = self.path.split("?")[0].split("#")[0]
        if normalized_path == "/" or normalized_path == "":
            normalized_path = "/index.html"
            
        local_path = normalized_path.lstrip("/")
        
        # If the file doesn't exist, fallback to index.html for SPA
        if not os.path.exists(local_path) or os.path.isdir(local_path):
            local_path = "index.html"
            
        # Serve the static file
        try:
            with open(local_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            
            # Determine Content-Type
            mime_type, _ = mimetypes.guess_type(local_path)
            if local_path.endswith(".py"):
                mime_type = "text/plain"
            elif local_path.endswith(".json"):
                mime_type = "application/json"
                
            if mime_type:
                self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(404, f"File not found: {e}")

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        if self.path == "/api/history":
            try:
                # Validate JSON
                data = json.loads(post_data.decode("utf-8"))
                with open("history.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                    
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                
        elif self.path == "/api/rl_memory":
            try:
                # Validate JSON
                data = json.loads(post_data.decode("utf-8"))
                with open("rl_memory.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                    
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                
        elif self.path == "/api/bot_move":
            try:
                data = json.loads(post_data.decode("utf-8"))
                fen = data["fen"]
                elo = data["elo"]
                q_table = data.get("q_table", {})
                
                # Perform the multi-core parallel backend search
                best_move, eval_score = server_engine.get_backend_bot_move(fen, elo, q_table)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "best_move": best_move.uci() if best_move else None,
                    "eval_score": eval_score
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                
        elif self.path == "/api/support":
            try:
                data = json.loads(post_data.decode("utf-8"))
                messages = data.get("messages", [])
                
                api_key = os.environ.get("GEMINI_API_KEY")
                if not api_key:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "error": "GEMINI_API_KEY environment variable is not configured. Please set it in Settings > Secrets."
                    }).encode("utf-8"))
                    return

                # Convert messages from simple format {"role": "user"|"assistant", "content": "..."}
                # to Gemini's format: {"role": "user"|"model", "parts": [{"text": "..."}]}

                contents = []
                for msg in messages:
                    role = msg.get("role")
                    if role == "assistant":
                        role = "model"
                    
                    if len(contents) > 0 and contents[-1]["role"] == role:
                        contents[-1]["parts"][0]["text"] += "\n\n" + msg.get("content", "")
                    else:
                        contents.append({
                            "role": role,
                            "parts": [{"text": msg.get("content", "")}]
                        })


                # Prepare the request body
                req_body = {
                    "contents": contents,
                    "systemInstruction": {
                        "parts": [{
                            "text": "You are a professional customer support assistant and technical troubleshooter for Firestorm Chess.\n"
                                    "Firestorm Chess is a state-of-the-art hybrid chess application built with custom local Python WebAssembly (Pyodide) and a threaded Python backend engine (server_engine.py).\n"
                                    "It features real-time move analysis, reinforcement learning (RL) backpropagation on a local Q-table (saved locally and to Firestore), offline gameplay vs. various minimax personalities (Beginner Beth 1000, Coach Nakamura 1600, GM Garry 2000, and FireStorm GM Alpha 2400), automatic opening book detection, and calendar events.\n\n"
                                    "Provide extremely helpful, friendly, and accurate troubleshooting advice. Address questions about performance, the engine, RL learning mechanics, saving history to Firebase, or rules of the game. Keep formatting neat and clear, using Markdown where appropriate."
                        }]
                    }
                }

                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                
                import urllib.request
                import urllib.error
                req = urllib.request.Request(
                    url,
                    data=json.dumps(req_body).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "aistudio-build"
                    },
                    method="POST"
                )
                
                try:
                    with urllib.request.urlopen(req) as response:
                        res_raw = response.read().decode("utf-8")
                        res_json = json.loads(res_raw)
                        
                        # Extract the reply text
                        reply_text = ""
                        try:
                            candidates = res_json.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                if parts:
                                    reply_text = parts[0].get("text", "")
                        except Exception as parse_err:
                            reply_text = f"Error parsing response: {str(parse_err)}"
                            
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "reply": reply_text
                        }).encode("utf-8"))
                except urllib.error.HTTPError as http_err:
                    err_details = http_err.read().decode("utf-8")
                    try:
                        err_json = json.loads(err_details)
                        err_msg = err_json.get("error", {}).get("message", err_details)
                    except:
                        err_msg = err_details
                    
                    self.send_response(http_err.code)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Gemini API Error: {err_msg}"}).encode("utf-8"))
                    return
                    
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_error(404, "Not Found")

class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    # Enable immediate port reuse
    allow_reuse_address = True

if __name__ == "__main__":
    server_address = ("0.0.0.0", PORT)
    print(f"Starting Firestorm Chess Python Web Server on port {PORT}...")
    print(f"Navigate to http://localhost:{PORT} in your web browser to run the app.")
    print("Press Ctrl+C to stop.")
    
    with ThreadedHTTPServer(server_address, ChessRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
