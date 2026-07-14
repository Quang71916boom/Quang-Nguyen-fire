# 🌪️ Firestorm Chess (VS Code & Local Friendly)

An interactive chess application featuring a simulated 1600 ELO engine, real-time local tactical coaching, and a complete exportable/copyable Python implementation of the bot.

This application is designed to be **100% self-contained, offline-friendly, and VS Code-ready**. It requires **zero external API keys (no Gemini API required) and absolutely no Node.js or npm** to run!

---

## ✨ Features

- **No API Keys Needed**: Run the complete app locally without configuring any external services or APIs.
- **Offline Engines & Coaching**: Fully powered by WebAssembly (Pyodide) and Python-Chess directly inside your browser.
- **Durable Local Persistence**: Match histories and reinforcement learning (RL) tables are automatically synchronized and written to disk in your local directory (`history.json` and `rl_memory.json`), ensuring your progress is never cleared when you close the app.
- **Self-Play & Training Modes**: Watch the engine play against itself at adjustable speeds to train the RL Q-table.
- **Zero-Dependency Server**: Uses a lightweight pure-Python script (`server.py`) to serve files and save data. No `node_modules` or `npm install` needed!

---

## 🚀 How to Run Locally in VS Code (No Node.js Required)

### Prerequisites
- **Python 3.x** installed on your system.

### Step 1: Start the Local Development Server
Open your VS Code terminal and run:
```bash
python3 server.py
```
*(On Windows, you may need to type `python server.py` instead).*

### Step 2: Open the App
The server will start on port `3000`. Open your web browser and navigate to:
```
http://localhost:3000/
```

---

## 📂 File Structure

- `/app.py`: The core engine, positional evaluation table, minimax search with quiescence, and temporal-difference learning.
- `/index.html`: The interactive dashboard, fully styled with Tailwind CSS, supporting drag-and-drop or dropdown move input and visual statistics.
- `/server.py`: The lightweight, zero-dependency Python server that hosts the web interface and handles read/write persistence for match logs and reinforcement learning weights.
- `/history.json`: (Automatically generated) Your local persistent match history database.
- `/rl_memory.json`: (Automatically generated) Your local persistent reinforcement learning Q-tables.
