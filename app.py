import js
from js import document, window
from pyodide.ffi import create_proxy
import json
import random
import time
import datetime
import sys

# Ensure system paths are configured correctly for imports
if "/" not in sys.path:
    sys.path.insert(0, "/")
if "/home/pyodide" not in sys.path:
    sys.path.insert(0, "/home/pyodide")

import chess
import chess.svg

# --- Positional tables and parameters matching ELO 1600 engine ---
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

PAWN_TABLE = [
    [  0,   0,   0,   0,   0,   0,   0,   0],
    [ 50,  50,  50,  50,  50,  50,  50,  50],
    [ 10,  10,  20,  30,  30,  20,  10,  10],
    [  5,   5,  10,  25,  25,  10,   5,   5],
    [  0,   0,   0,  20,  20,   0,   0,   0],
    [  5,  -5, -10,   0,   0, -10,  -5,   5],
    [  5,  10,  10, -20, -20,  10,  10,   5],
    [  0,   0,   0,   0,   0,   0,   0,   0]
]

KNIGHT_TABLE = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20,   0,   0,   0,   0, -20, -40],
    [-30,   0,  10,  15,  15,  10,   0, -30],
    [-30,   5,  15,  20,  20,  15,   5, -30],
    [-30,   0,  15,  20,  20,  15,   0, -30],
    [-30,   5,  10,  15,  15,  10,   5, -30],
    [-40, -20,   0,   5,   5,   0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50]
]

BISHOP_TABLE = [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10,   0,   0,   0,   0,   0,   0, -10],
    [-10,   0,   5,  10,  10,   5,   0, -10],
    [-10,   5,   5,  10,  10,   5,   5, -10],
    [-10,   0,  10,  10,  10,  10,   0, -10],
    [-10,  10,  10,  10,  10,  10,  10, -10],
    [-10,   5,   0,   0,   0,   0,   5, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20]
]

ROOK_TABLE = [
    [  0,   0,   0,   0,   0,   0,   0,   0],
    [  5,  10,  10,  10,  10,  10,  10,   5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [ -5,   0,   0,   0,   0,   0,   0,  -5],
    [  0,   0,   0,   5,   5,   0,   0,   0]
]

QUEEN_TABLE = [
    [-20, -10, -10,  -5,  -5, -10, -10, -20],
    [-10,   0,   0,   0,   0,   0,   0, -10],
    [-10,   0,   5,   5,   5,   5,   0, -10],
    [ -5,   0,   5,   5,   5,   5,   0,  -5],
    [  0,   0,   5,   5,   5,   5,   0,  -5],
    [-10,   5,   5,   5,   5,   5,   0, -10],
    [-10,   0,   5,   0,   0,   5,   0, -10],
    [-20, -10, -10,  -5,  -5, -10, -10, -20]
]

KING_MID_TABLE = [
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [ 20,  20,   0,   0,   0,   0,  20,  20],
    [ 20,  30,  10,   0,   0,  10,  30,  20]
]

KING_END_TABLE = [
    [-50, -40, -30, -20, -20, -30, -40, -50],
    [-30, -20, -10,   0,   0, -10, -20, -30],
    [-30, -10,  20,  30,  30,  20, -10, -30],
    [-30, -10,  30,  40,  40,  30, -10, -30],
    [-30, -10,  30,  40,  40,  30, -10, -30],
    [-30, -10,  20,  30,  30,  20, -10, -30],
    [-30, -30,   0,   0,   0,   0, -30, -30],
    [-50, -30, -30, -30, -30, -30, -30, -50]
]

# Get clean FEN helper
def get_clean_fen(fen: str) -> str:
    return " ".join(fen.split()[:4])

# Detailed move sequences for the 50 most popular and effective openings in chess history
OPENING_LINES = {
    "Ruy Lopez": ["e4", "e5", "Nf3", "Nc6", "Bb5", "a6", "Ba4", "Nf6", "O-O", "Be7"],
    "Sicilian Najdorf": ["e4", "c5", "Nf3", "d6", "d4", "cxd4", "Nxd4", "Nf6", "Nc3", "a6", "Be3", "e5"],
    "Sicilian Dragon": ["e4", "c5", "Nf3", "d6", "d4", "cxd4", "Nxd4", "Nf6", "Nc3", "g6", "Be3", "Bg7", "f3", "Nc6"],
    "Sicilian Scheveningen": ["e4", "c5", "Nf3", "d6", "d4", "cxd4", "Nxd4", "Nf6", "Nc3", "e6", "Be2", "Be7"],
    "Sicilian Alapin": ["e4", "c5", "c3", "d5", "exd5", "Qxd5", "d4", "Nf6", "Nf3", "e6"],
    "French Defense Advance": ["e4", "e6", "d4", "d5", "e5", "c5", "c3", "Nc6", "Nf3", "Qb6"],
    "French Defense Exchange": ["e4", "e6", "d4", "d5", "exd5", "exd5", "Bd3", "Bd6", "Nf3", "Ne7"],
    "French Classical": ["e4", "e6", "d4", "d5", "Nc3", "Nf6", "Bg5", "Be7", "e5", "Nfd7"],
    "Caro-Kann Classical": ["e4", "c6", "d4", "d5", "Nc3", "dxe4", "Nxe4", "Bf5", "Ng3", "Bg6"],
    "Caro-Kann Advance": ["e4", "c6", "d4", "d5", "e5", "Bf5", "Nf3", "e6", "Be2", "c5"],
    "Caro-Kann Panov": ["e4", "c6", "d4", "d5", "exd5", "cxd5", "c4", "Nf6", "Nc3", "e6"],
    "Italian Game": ["e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5", "c3", "Nf6", "d4", "exd4", "cxd4", "Bb4+"],
    "Two Knights Defense": ["e4", "e5", "Nf3", "Nc6", "Bc4", "Nf6", "Ng5", "d5", "exd5", "Na5", "Bb5+", "c6", "dxc6", "bxc6"],
    "Scotch Game": ["e4", "e5", "Nf3", "Nc6", "d4", "exd4", "Nxd4", "Bc5", "Be3", "Qf6", "c3", "Nge7"],
    "Scandinavian Defense": ["e4", "d5", "exd5", "Qxd5", "Nc3", "Qa5", "d4", "Nf6", "Nf3", "Bf5"],
    "Alekhine's Defense": ["e4", "Nf6", "e5", "Nd5", "d4", "d6", "c4", "Nb6", "f4", "dxe5", "fxe5"],
    "Pirc Defense": ["e4", "d6", "d4", "Nf6", "Nc3", "g6", "f4", "Bg7", "Nf3", "O-O"],
    "Queen's Gambit Declined": ["d4", "d5", "c4", "e6", "Nc3", "Nf6", "Bg5", "Be7", "e3", "O-O", "Nf3", "Nbd7"],
    "Queen's Gambit Accepted": ["d4", "d5", "c4", "dxc4", "Nf3", "Nf6", "e3", "e6", "Bxc4", "c5", "O-O", "a6"],
    "Slav Defense": ["d4", "d5", "c4", "c6", "Nf3", "Nf6", "Nc3", "dxc4", "a4", "Bf5"],
    "King's Indian Defense": ["d4", "Nf6", "c4", "g6", "Nc3", "Bg7", "e4", "d6", "Nf3", "O-O", "Be2", "e5"],
    "Nimzo-Indian Defense": ["d4", "Nf6", "c4", "e6", "Nc3", "Bb4", "e3", "O-O", "Bd3", "d5"],
    "Grünfeld Defense": ["d4", "Nf6", "c4", "g6", "Nc3", "d5", "cxd5", "Nxd5", "e4", "Nxc3", "bxc3", "Bg7"],
    "Catalan Opening": ["d4", "Nf6", "c4", "e6", "g3", "d5", "Bg2", "Be7", "Nf3", "O-O"],
    "English Opening": ["c4", "e5", "Nc3", "Nf6", "g3", "d5", "cxd5", "Nxd5", "Bg2", "Nb6"],
    "Reti Opening": ["Nf3", "d5", "c4", "e6", "g3", "Nf6", "Bg2", "Be7", "O-O", "O-O"],
    "London System": ["d4", "d5", "Bf4", "Nf6", "e3", "e6", "Nf3", "Bd6", "Bg3", "O-O"],
    "Dutch Leningrad": ["d4", "f5", "g3", "Nf6", "Bg2", "g6", "Nf3", "Bg7", "O-O", "O-O"],
    "Dutch Stonewall": ["d4", "f5", "c4", "Nf6", "g3", "e6", "Bg2", "d5", "Nf3", "c6", "O-O", "Bd6"],
    "Benko Gambit": ["d4", "Nf6", "c4", "c5", "d5", "b5", "cxb5", "a6", "bxa6", "Bxa6"],
    "Modern Benoni": ["d4", "Nf6", "c4", "c5", "d5", "e6", "Nc3", "exd5", "cxd5", "d6", "e4", "g6"],
    "Vienna Game": ["e4", "e5", "Nc3", "Nf6", "f4", "d5", "fxe5", "Nxe4", "Nf3", "Be7"],
    "King's Gambit Accepted": ["e4", "e5", "f4", "exd4", "Nf3", "g5", "Bc4", "Bg7", "O-O", "h6"],
    "Evans Gambit": ["e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5", "b4", "Bxb4", "c3", "Ba5"],
    "Danish Gambit": ["e4", "e5", "d4", "exd4", "c3", "dxc3", "Bc4", "cxb2", "Bxb2"],
    "Chigorin Defense": ["d4", "d5", "c4", "Nc6", "Nc3", "dxc4", "Nf3", "Nf6", "e4", "Bg4"],
    "Albin Countergambit": ["d4", "d5", "c4", "e5", "dxe5", "d4", "Nf3", "Nc6", "a3", "Bg4"],
    "Budapest Gambit": ["d4", "Nf6", "c4", "e5", "dxe5", "Ng4", "Bf4", "Nc6", "Nf3", "Bb4+"],
    "Trompowsky Attack": ["d4", "Nf6", "Bg5", "e6", "e4", "h6", "Bxf6", "Qxf6", "Nf3", "d6"],
    "Richter-Veresov Attack": ["d4", "d5", "Nc3", "Nf6", "Bg5", "Bf5", "f3", "Nbd7"],
    "Scandinavian Modern": ["e4", "d5", "exd5", "Nf6", "d4", "Nxd5", "c4", "Nb6", "Nf3", "g6"],
    "Petroff's Defense": ["e4", "e5", "Nf3", "Nf6", "Nxe5", "d6", "Nf3", "Nxe4", "d4", "d5"],
    "Philidor Defense": ["e4", "e5", "Nf3", "d6", "d4", "exd4", "Nxd4", "Nf6", "Nc3", "Be7"],
    "Bogo-Indian Defense": ["d4", "Nf6", "c4", "e6", "Nf3", "Bb4+", "Bd2", "Qe7", "g3", "Nc6"],
    "Colle System": ["d4", "d5", "Nf3", "Nf6", "e3", "e6", "Bd3", "c5", "c3", "Nc6"],
    "King's Indian Attack": ["Nf3", "d5", "g3", "Nf6", "Bg2", "c6", "O-O", "Bf5", "d3", "e6"],
    "Nimzowitsch Defense": ["e4", "Nc6", "d4", "d5", "e5", "Bf5", "c3", "e6", "Nf3", "f6"],
    "Semi-Slav Defense": ["d4", "d5", "c4", "c6", "Nf3", "Nf6", "Nc3", "e6", "e3", "Nbd7"],
    "Bird's Opening": ["f4", "d5", "Nf3", "Nf6", "e3", "g6", "b3", "Bg7", "Bb2", "O-O"],
    "Larsen's Opening": ["b3", "e5", "Bb2", "Nc6", "e3", "Nf6", "Bb5", "Bd6", "Na3", "a6"]
}

import sys
if '/' not in sys.path:
    sys.path.append('/')

def populate_opening_book():
    book = {}
    baseline = {
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -": ["e4", "d4", "Nf3", "c4"],
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3": ["c5", "e5", "e6", "c6"],
        "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3": ["Nf6", "d5"],
        "rnbqkbnr/pppppppp/8/8/5N2/8/PPPPPPPP/RNBQKB1R b KQkq -": ["Nf6", "d5", "e6"],
        "rnbqkbnr/pppppppp/8/8/2P5/8/PP1PPPPP/RNBQKBNR b KQkq -": ["Nf6", "e5", "c5"],
        "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6": ["Nf3", "Bc4", "Nc3"],
        "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq -": ["Nc6", "Nf6", "d6"],
        "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6": ["Nf3", "Nc3", "c3"],
        "rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq -": ["d6", "Nc6", "e6"],
        "rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq d6": ["c4", "Nf3", "Bf4"],
        "rnbqkbnr/pppppppp/5n2/8/3P4/8/PPP1PPPP/RNBQKBNR w KQkq -": ["c4", "Nf3", "g3"],
        "rnbqkbnr/pppppppp/5n2/8/2PP4/8/PP2PPPP/RNBQKBNR b KQkq -": ["e6", "g6", "c6"]
    }
    for fen, moves in baseline.items():
        book[fen] = list(moves)
        
    for name, moves in OPENING_LINES.items():
        temp_board = chess.Board()
        for move_san in moves:
            clean_f = get_clean_fen(temp_board.fen())
            try:
                move_obj = temp_board.parse_san(move_san)
                if clean_f not in book:
                    book[clean_f] = []
                if move_san not in book[clean_f]:
                    book[clean_f].append(move_san)
                temp_board.push(move_obj)
            except Exception as e:
                print(f"Error parsing '{move_san}' in {name}:", e)
                break
                
    try:
        from gm_db import GM_DB
        for fen, moves in GM_DB.items():
            if fen not in book:
                book[fen] = []
            for m in moves:
                if m not in book[fen]:
                    book[fen].append(m)
        print("Loaded Capablanca and Carlsen GM database! Entries:", len(GM_DB))
    except Exception as e:
        print("Could not load gm_db:", e)

    try:
        from carlsen_stockfish_db import CARLSEN_GAMES_BOOK, STOCKFISH_17_1_GAMES_BOOK
        # Load Magnus Carlsen's 250 best games
        for fen, moves in CARLSEN_GAMES_BOOK.items():
            if fen not in book:
                book[fen] = []
            for m in moves:
                if m not in book[fen]:
                    book[fen].append(m)
        # Load Stockfish 17.1's 250 best games
        for fen, moves in STOCKFISH_17_1_GAMES_BOOK.items():
            if fen not in book:
                book[fen] = []
            for m in moves:
                if m not in book[fen]:
                    book[fen].append(m)
        print("Loaded Magnus Carlsen's best 250 games and Stockfish 17.1's best 250 games databases!")
    except Exception as e:
        print("Could not load carlsen_stockfish_db:", e)
                
    return book

OPENING_BOOK = populate_opening_book()

# --- Browser LocalStorage Handlers ---
def load_rl_memory():
    stored = window.localStorage.getItem("chess_rl_memory")
    if stored:
        try:
            return json.loads(stored)
        except Exception:
            pass
    return {
        "games_played": 0,
        "bot_wins": 0,
        "bot_losses": 0,
        "bot_draws": 0,
        "q_table": {},
        "recent_learnings": []
    }

def save_rl_memory(data):
    json_str = json.dumps(data)
    window.localStorage.setItem("chess_rl_memory", json_str)
    try:
        import js_helper
        js_helper.save_rl_memory_to_server(json_str)
    except Exception as e:
        print("Error saving RL memory to server:", e)

def load_matches_history():
    stored = window.localStorage.getItem("chess_matches_history")
    if stored:
        try:
            return json.loads(stored)
        except Exception:
            pass
    return []

def save_matches_history(history):
    json_str = json.dumps(history)
    window.localStorage.setItem("chess_matches_history", json_str)
    try:
        import js_helper
        js_helper.save_history_to_server(json_str)
    except Exception as e:
        print("Error saving matches history to server:", e)

# Clean FEN is computed earlier in file to initialize the opening book.

class SearchTimeout(Exception):
    pass

# --- Pure Python Minimax & Position Evaluation Engine ---
GARRY_TRANSPOSITION_TABLE = {}

def update_engine_log_ui(depth, nodes_visited, elapsed_ms, pv):
    try:
        depth_el = document.getElementById("engine-depth")
        nodes_el = document.getElementById("engine-nodes")
        time_el = document.getElementById("engine-time")
        nps_el = document.getElementById("engine-nps")
        pv_el = document.getElementById("engine-pv")
        
        if depth_el:
            depth_el.innerText = str(depth)
        if nodes_el:
            nodes_el.innerText = f"{nodes_visited:,}"
        if time_el:
            time_el.innerText = f"{elapsed_ms} ms" if elapsed_ms > 0 else "< 1 ms"
        if nps_el:
            nps = int(nodes_visited / (elapsed_ms / 1000.0)) if elapsed_ms > 0 else 0
            nps_el.innerText = f"{nps:,} nps" if nps > 0 else "N/A"
        if pv_el:
            if pv:
                pv_str = " ".join([m.uci() if hasattr(m, 'uci') else str(m) for m in pv])
                pv_el.innerText = pv_str
                pv_el.title = pv_str
            else:
                pv_el.innerText = "N/A"
                pv_el.title = "N/A"
    except Exception as e:
        print("Error updating engine log UI:", e)

class PurePythonChessEngine:
    def __init__(self, use_quiescence: bool = True, q_table: dict = None, time_limit: float = None, personality: str = "Nakamura"):
        self.use_quiescence = use_quiescence
        self.q_table = q_table or {}
        self.time_limit = time_limit
        self.start_time = None
        self.personality = personality
        self.nodes_visited = 0
        if personality in ["Garry", "FireStorm"]:
            global GARRY_TRANSPOSITION_TABLE
            self.transposition_table = GARRY_TRANSPOSITION_TABLE
        else:
            self.transposition_table = {}

    def is_endgame(self, board: chess.Board) -> bool:
        major_pieces = 0
        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if piece and piece.piece_type not in (chess.PAWN, chess.KING):
                major_pieces += 1
        return major_pieces <= 4

    def evaluate_board(self, board: chess.Board) -> int:
        score = 0
        endgame = self.is_endgame(board)

        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if not piece:
                continue

            pt = piece.piece_type
            color = piece.color
            val = PIECE_VALUES.get(pt, 0)

            file_idx = chess.square_file(sq)
            rank_idx = 7 - chess.square_rank(sq)

            r_idx = rank_idx if color == chess.WHITE else 7 - rank_idx
            f_idx = file_idx if color == chess.WHITE else 7 - file_idx

            table_val = 0
            if pt == chess.PAWN:
                table_val = PAWN_TABLE[r_idx][f_idx]
            elif pt == chess.KNIGHT:
                table_val = KNIGHT_TABLE[r_idx][f_idx]
            elif pt == chess.BISHOP:
                table_val = BISHOP_TABLE[r_idx][f_idx]
            elif pt == chess.ROOK:
                table_val = ROOK_TABLE[r_idx][f_idx]
            elif pt == chess.QUEEN:
                table_val = QUEEN_TABLE[r_idx][f_idx]
            elif pt == chess.KING:
                table_val = KING_END_TABLE[r_idx][f_idx] if endgame else KING_MID_TABLE[r_idx][f_idx]

            net_val = val + table_val
            if color == chess.WHITE:
                score += net_val
            else:
                score -= net_val

        # Personality-Specific Heuristics
        personality = getattr(self, "personality", "Nakamura")

        # 1. BEGINNER BETH (Reckless and aggressive, throws attacks hoping they work, ignores safety)
        if personality == "Beth":
            # Overvalue checks and attacks near king
            white_king_sq = board.king(chess.WHITE)
            black_king_sq = board.king(chess.BLACK)
            
            # Beth (as Black) attacks White King
            if white_king_sq is not None:
                wk_file = chess.square_file(white_king_sq)
                wk_rank = chess.square_rank(white_king_sq)
                for r_offset in [-2, -1, 0, 1, 2]:
                    for f_offset in [-2, -1, 0, 1, 2]:
                        r = wk_rank + r_offset
                        f = wk_file + f_offset
                        if 0 <= r < 8 and 0 <= f < 8:
                            target_sq = chess.square(f, r)
                            if board.is_attacked_by(chess.BLACK, target_sq):
                                score -= 45  # massive value to Black for attacking near white king

            # Beth (as White) attacks Black King
            if black_king_sq is not None:
                bk_file = chess.square_file(black_king_sq)
                bk_rank = chess.square_rank(black_king_sq)
                for r_offset in [-2, -1, 0, 1, 2]:
                    for f_offset in [-2, -1, 0, 1, 2]:
                        r = bk_rank + r_offset
                        f = bk_file + f_offset
                        if 0 <= r < 8 and 0 <= f < 8:
                            target_sq = chess.square(f, r)
                            if board.is_attacked_by(chess.WHITE, target_sq):
                                score += 45  # massive value to White for attacking near black king

            # Beth ignores piece protection and self king safety completely!
            # (No safety deductions for Beth)

        # 2. GM GARRY (Careful, methodical, doesn't throw random attacks, values structural safety & defense)
        elif personality in ["Garry", "FireStorm"]:
            # Highly value King safety and Pawn shield
            white_king_sq = board.king(chess.WHITE)
            black_king_sq = board.king(chess.BLACK)

            # Check White's king shield if castled
            if white_king_sq is not None and not endgame:
                wk_file = chess.square_file(white_king_sq)
                wk_rank = chess.square_rank(white_king_sq)
                # If white king is kingside (f1/g1/h1)
                if wk_file >= 5 and wk_rank == 0:
                    # Expect pawns on f2, g2, h2
                    for f_shield in [5, 6, 7]:
                        shield_sq = chess.square(f_shield, 1)
                        p = board.piece_at(shield_sq)
                        if p and p.piece_type == chess.PAWN and p.color == chess.WHITE:
                            score += 15
                        else:
                            score -= 25  # penalty if broken/advanced
                # If white king is queenside (a1/b1/c1)
                elif wk_file <= 2 and wk_rank == 0:
                    for f_shield in [0, 1, 2]:
                        shield_sq = chess.square(f_shield, 1)
                        p = board.piece_at(shield_sq)
                        if p and p.piece_type == chess.PAWN and p.color == chess.WHITE:
                            score += 15
                        else:
                            score -= 25

            # Check Black's king shield if castled
            if black_king_sq is not None and not endgame:
                bk_file = chess.square_file(black_king_sq)
                bk_rank = chess.square_rank(black_king_sq)
                # If black king is kingside (f8/g8/h8)
                if bk_file >= 5 and bk_rank == 7:
                    # Expect pawns on f7, g7, h7
                    for f_shield in [5, 6, 7]:
                        shield_sq = chess.square(f_shield, 6)
                        p = board.piece_at(shield_sq)
                        if p and p.piece_type == chess.PAWN and p.color == chess.BLACK:
                            score -= 15
                        else:
                            score += 25
                # If black king is queenside (a8/b8/c8)
                elif bk_file <= 2 and bk_rank == 7:
                    for f_shield in [0, 1, 2]:
                        shield_sq = chess.square(f_shield, 6)
                        p = board.piece_at(shield_sq)
                        if p and p.piece_type == chess.PAWN and p.color == chess.BLACK:
                            score -= 15
                        else:
                            score += 25

            # Piece protection: penalty for leaving own pieces completely hanging / undefended when attacked
            for sq in chess.SQUARES:
                piece = board.piece_at(sq)
                if piece and piece.piece_type != chess.KING:
                    is_attacked = board.is_attacked_by(not piece.color, sq)
                    is_defended = len(board.attackers(piece.color, sq)) > 0
                    if is_attacked:
                        p_val = PIECE_VALUES.get(piece.piece_type, 100)
                        # Hanging piece (under attack, not defended)
                        if not is_defended:
                            penalty = int(p_val * 0.4)
                            if piece.color == chess.WHITE:
                                score -= penalty
                            else:
                                score += penalty
                        # Insufficient defense (under attack, defended but defender is less valuable, etc.)
                        else:
                            penalty = int(p_val * 0.1)
                            if piece.color == chess.WHITE:
                                score -= penalty
                            else:
                                score += penalty

            # Center control: methodical strategic grip (d4, e4, d5, e5 squares)
            center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
            for cs in center_squares:
                white_ctrl = len(board.attackers(chess.WHITE, cs))
                black_ctrl = len(board.attackers(chess.BLACK, cs))
                score += (white_ctrl - black_ctrl) * 10

            # Only methodical attacks (no speculative random king attacks)
            # Garry will only give king attack bonus if the enemy king's pawn shield is broken or weak!
            if white_king_sq is not None:
                # White's king under attack
                wk_file = chess.square_file(white_king_sq)
                wk_rank = chess.square_rank(white_king_sq)
                for r_offset in [-1, 0, 1]:
                    for f_offset in [-1, 0, 1]:
                        r = wk_rank + r_offset
                        f = wk_file + f_offset
                        if 0 <= r < 8 and 0 <= f < 8:
                            target_sq = chess.square(f, r)
                            if board.is_attacked_by(chess.BLACK, target_sq):
                                score -= 15

            if black_king_sq is not None:
                # Black's king under attack
                bk_file = chess.square_file(black_king_sq)
                bk_rank = chess.square_rank(black_king_sq)
                for r_offset in [-1, 0, 1]:
                    for f_offset in [-1, 0, 1]:
                        r = bk_rank + r_offset
                        f = bk_file + f_offset
                        if 0 <= r < 8 and 0 <= f < 8:
                            target_sq = chess.square(f, r)
                            if board.is_attacked_by(chess.WHITE, target_sq):
                                score += 15

        # 3. COACH NAKAMURA (Default / Standard accurate tactical evaluation)
        else:
            # Nakamura has robust balanced attacking & defending heuristics
            white_king_sq = board.king(chess.WHITE)
            black_king_sq = board.king(chess.BLACK)

            if white_king_sq is not None:
                wk_file = chess.square_file(white_king_sq)
                wk_rank = chess.square_rank(white_king_sq)
                for r_offset in [-1, 0, 1]:
                    for f_offset in [-1, 0, 1]:
                        r = wk_rank + r_offset
                        f = wk_file + f_offset
                        if 0 <= r < 8 and 0 <= f < 8:
                            target_sq = chess.square(f, r)
                            if board.is_attacked_by(chess.BLACK, target_sq):
                                score -= 20

            if black_king_sq is not None:
                bk_file = chess.square_file(black_king_sq)
                bk_rank = chess.square_rank(black_king_sq)
                for r_offset in [-1, 0, 1]:
                    for f_offset in [-1, 0, 1]:
                        r = bk_rank + r_offset
                        f = bk_file + f_offset
                        if 0 <= r < 8 and 0 <= f < 8:
                            target_sq = chess.square(f, r)
                            if board.is_attacked_by(chess.WHITE, target_sq):
                                score += 20

            if black_king_sq is not None:
                bk_file = chess.square_file(black_king_sq)
                for file_offset in [-1, 0, 1]:
                    f = bk_file + file_offset
                    if 0 <= f < 8:
                        for r in range(8):
                            sq = chess.square(f, r)
                            p = board.piece_at(sq)
                            if p and p.color == chess.WHITE and p.piece_type in (chess.ROOK, chess.QUEEN):
                                score += 35

            if white_king_sq is not None:
                wk_file = chess.square_file(white_king_sq)
                for file_offset in [-1, 0, 1]:
                    f = wk_file + file_offset
                    if 0 <= f < 8:
                        for r in range(8):
                            sq = chess.square(f, r)
                            p = board.piece_at(sq)
                            if p and p.color == chess.BLACK and p.piece_type in (chess.ROOK, chess.QUEEN):
                                score -= 35

        if personality == "FireStorm":
            try:
                # Add Magnus Carlsen central outpost knights preference and Stockfish active open file rooks preference
                for sq in chess.SQUARES:
                    piece = board.piece_at(sq)
                    if piece:
                        if piece.piece_type == chess.KNIGHT:
                            if piece.color == chess.WHITE and sq in [chess.D5, chess.E5]:
                                score += 35
                            elif piece.color == chess.BLACK and sq in [chess.D4, chess.E4]:
                                score -= 35
                        elif piece.piece_type == chess.ROOK:
                            file_idx = chess.square_file(sq)
                            open_file = True
                            for r in range(8):
                                check_p = board.piece_at(chess.square(file_idx, r))
                                if check_p and check_p.piece_type == chess.PAWN:
                                    open_file = False
                                    break
                            if open_file:
                                if piece.color == chess.WHITE:
                                    score += 25
                                else:
                                    score -= 25
            except Exception:
                pass

        return score

    def order_moves(self, board: chess.Board, moves: list[chess.Move]) -> list[chess.Move]:
        scored = []
        enemy_king_sq = board.king(not board.turn)
        personality = getattr(self, "personality", "Nakamura")
        for move in moves:
            prio = 0
            if board.is_capture(move):
                vic = board.piece_type_at(move.to_square) or chess.PAWN
                att = board.piece_type_at(move.from_square) or chess.PAWN
                prio += 1200 + (PIECE_VALUES.get(vic, 100) - PIECE_VALUES.get(att, 100) // 10)
                
                if enemy_king_sq is not None:
                    dist = chess.square_distance(move.to_square, enemy_king_sq)
                    if dist <= 2 and PIECE_VALUES.get(att, 100) > PIECE_VALUES.get(vic, 100):
                        prio += 300

            if move.promotion:
                prio += 1000

            if enemy_king_sq is not None:
                to_dist = chess.square_distance(move.to_square, enemy_king_sq)
                from_dist = chess.square_distance(move.from_square, enemy_king_sq)
                if to_dist < from_dist:
                    prio += (3 - to_dist) * 100 if to_dist <= 3 else 50

            to_rank = chess.square_rank(move.to_square)
            if board.turn == chess.WHITE and to_rank >= 4:
                prio += 80
            elif board.turn == chess.BLACK and to_rank <= 3:
                prio += 80

            try:
                if board.gives_check(move):
                    if personality == "Beth":
                        prio += 1200  # Beth loves giving checks recklessly!
                    elif personality in ["Garry", "FireStorm"]:
                        prio += 300   # Garry is methodical; checks are only parsed if sound, not given blindly
                    else:
                        prio += 800
            except:
                pass

            # Garry specific ordering
            if personality in ["Garry", "FireStorm"]:
                # Prioritize Castling for early King safety
                if board.is_castling(move):
                    prio += 900
                
                # Prioritize defending pieces under attack
                from_sq = move.from_square
                if board.is_attacked_by(not board.turn, from_sq):
                    prio += 500

            if personality == "FireStorm":
                try:
                    from carlsen_stockfish_db import get_master_move_bonus
                    prio += get_master_move_bonus(board, move, personality)
                except Exception:
                    pass
                    
            scored.append((move, prio))
            
        scored.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in scored]

    def quiescence_search(self, board: chess.Board, alpha: int, beta: int, is_maximizing: bool, depth_left: int = 3) -> int:
        self.nodes_visited += 1
        global is_historic_analysis
        if self.personality == "FireStorm" and depth_left == 3:
            if is_historic_analysis:
                depth_left = 50
            else:
                depth_left = 3

        if self.time_limit and self.start_time:
            import time
            if time.time() - self.start_time >= self.time_limit:
                raise SearchTimeout()

        stand_pat = self.evaluate_board(board)
        if depth_left == 0:
            return stand_pat

        if is_maximizing:
            if stand_pat >= beta:
                return beta
            if stand_pat > alpha:
                alpha = stand_pat

            captures = [m for m in board.legal_moves if board.is_capture(m)]
            for m in self.order_moves(board, captures):
                board.push(m)
                try:
                    val = self.quiescence_search(board, alpha, beta, False, depth_left - 1)
                finally:
                    board.pop()
                if val >= beta:
                    return beta
                if val > alpha:
                    alpha = val
            return alpha
        else:
            if stand_pat <= alpha:
                return alpha
            if stand_pat < beta:
                beta = stand_pat

            captures = [m for m in board.legal_moves if board.is_capture(m)]
            for m in self.order_moves(board, captures):
                board.push(m)
                try:
                    val = self.quiescence_search(board, alpha, beta, True, depth_left - 1)
                finally:
                    board.pop()
                if val <= alpha:
                    return alpha
                if val < beta:
                    beta = val
            return beta

    def parallel_search(self, board: chess.Board, depth: int, alpha: int, beta: int, is_maximizing: bool) -> tuple[int, list[chess.Move]]:
        import time
        t0 = time.time()
        self.nodes_visited = 0
        self.start_time = t0
        
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return self.evaluate_board(board), []
            
        ordered_root_moves = self.order_moves(board, legal_moves)
        
        if self.personality == "FireStorm":
            best_score = -999999 if is_maximizing else 999999
            best_pv = []
            
            # Use strict time limit of 3.0 seconds for prediction analysis to prevent UI freezing
            time_limit = self.time_limit or 3.0
            
            thread_failed = False
            try:
                from concurrent.futures import ThreadPoolExecutor, as_completed
                import os
                
                try:
                    num_workers = min(len(ordered_root_moves), os.cpu_count() or 4)
                except Exception:
                    num_workers = min(len(ordered_root_moves), 4)
                    
                # Search as far as possible (iterative deepening up to depth 12)
                for d in range(1, 13):
                    if time.time() - t0 >= time_limit * 0.8:
                        break
                        
                    futures = {}
                    completed_successfully = True
                    results = []
                    
                    with ThreadPoolExecutor(max_workers=num_workers) as executor:
                        for move in ordered_root_moves:
                            board_copy = board.copy()
                            board_copy.push(move)
                            
                            thread_engine = PurePythonChessEngine(
                                use_quiescence=self.use_quiescence,
                                q_table=self.q_table,
                                time_limit=time_limit - (time.time() - t0),
                                personality=self.personality
                            )
                            thread_engine.transposition_table = {}
                            thread_engine.start_time = t0
                            
                            fut = executor.submit(
                                thread_engine.minimax,
                                board_copy,
                                d - 1,
                                alpha,
                                beta,
                                not is_maximizing
                            )
                            futures[fut] = move
                            
                        for fut in as_completed(futures):
                            move = futures[fut]
                            try:
                                score, pv = fut.result()
                                results.append((score, [move] + pv))
                            except Exception:
                                completed_successfully = False
                                break
                                
                    if not completed_successfully or not results:
                        break
                        
                    if is_maximizing:
                        results.sort(key=lambda x: x[0], reverse=True)
                    else:
                        results.sort(key=lambda x: x[0])
                        
                    best_score, best_pv = results[0]
            except Exception as e:
                # ThreadPoolExecutor is either unsupported or failed in this browser/Pyodide environment.
                # Gracefully fall back to single-threaded iterative deepening search.
                thread_failed = True
                
            if thread_failed or not best_pv:
                # Optimized single-threaded iterative deepening search up to depth 12
                self.transposition_table = {}  # reset to fresh state
                for d in range(1, 13):
                    if time.time() - t0 >= time_limit * 0.8:
                        break
                    try:
                        score, pv = self.minimax(board, d, alpha, beta, is_maximizing)
                        best_score = score
                        if pv:
                            best_pv = pv
                    except SearchTimeout:
                        break
                
            if not best_pv:
                ordered = self.order_moves(board, legal_moves)
                best_pv = [ordered[0]]
                best_score = self.evaluate_board(board)
                
            res = best_score, best_pv
        else:
            res = self.minimax(board, depth, alpha, beta, is_maximizing)
            
        t1 = time.time()
        elapsed_ms = int((t1 - t0) * 1000)
        
        best_score, best_pv = res
        actual_depth = depth if self.personality != "FireStorm" else len(best_pv)
        update_engine_log_ui(actual_depth, self.nodes_visited, elapsed_ms, best_pv)
        
        return res

    def minimax(self, board: chess.Board, depth: int, alpha: int, beta: int, is_maximizing: bool) -> tuple[int, list[chess.Move]]:
        self.nodes_visited += 1
        if self.start_time is None:
            import time
            self.start_time = time.time()

        if self.time_limit and self.start_time:
            import time
            if time.time() - self.start_time >= self.time_limit:
                raise SearchTimeout()

        # Check Transposition Table
        fen_key = board.fen()
        if fen_key in self.transposition_table:
            stored_depth, stored_val, stored_pv = self.transposition_table[fen_key]
            if stored_depth >= depth:
                return stored_val, stored_pv

        if check_game_over(board):
            if board.is_checkmate():
                return (-50000 + depth if is_maximizing else 50000 - depth), []
            return 0, []

        if depth == 0:
            score = self.quiescence_search(board, alpha, beta, is_maximizing) if self.use_quiescence else self.evaluate_board(board)
            return score, []

        legal = list(board.legal_moves)
        if not legal:
            return self.evaluate_board(board), []

        ordered = self.order_moves(board, legal)
        best_pv = []

        if is_maximizing:
            max_val = -999999
            for m in ordered:
                clean_fen = get_clean_fen(board.fen())
                board.push(m)
                try:
                    val, pv = self.minimax(board, depth - 1, alpha, beta, False)
                finally:
                    board.pop()

                move_uci = m.uci()
                if clean_fen in self.q_table and move_uci in self.q_table[clean_fen]:
                    val += self.q_table[clean_fen][move_uci]

                if val > max_val:
                    max_val = val
                    best_pv = [m] + pv
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            if len(self.transposition_table) > 10000:
                self.transposition_table.clear()
            self.transposition_table[fen_key] = (depth, max_val, best_pv)
            return max_val, best_pv
        else:
            min_val = 999999
            for m in ordered:
                clean_fen = get_clean_fen(board.fen())
                board.push(m)
                try:
                    val, pv = self.minimax(board, depth - 1, alpha, beta, True)
                finally:
                    board.pop()

                move_uci = m.uci()
                if clean_fen in self.q_table and move_uci in self.q_table[clean_fen]:
                    val -= self.q_table[clean_fen][move_uci]

                if val < min_val:
                    min_val = val
                    best_pv = [m] + pv
                beta = min(beta, val)
                if beta <= alpha:
                    break
            if len(self.transposition_table) > 10000:
                self.transposition_table.clear()
            self.transposition_table[fen_key] = (depth, min_val, best_pv)
            return min_val, best_pv

def detect_checkmate_in_n(board: chess.Board, max_moves: int = 10) -> str | None:
    """
    Detects if either side can force checkmate in up to max_moves (2 * max_moves plies).
    Returns a string like 'M3' (White mates in 3) or '-M4' (Black mates in 4), or None.
    """
    max_plies = max_moves * 2
    memo = {}
    nodes = 0
    max_nodes = 500

    def search_attacker(b: chess.Board, plies_left: int) -> int | None:
        nonlocal nodes
        nodes += 1
        if nodes > max_nodes:
            return None
            
        if b.is_checkmate():
            return 0
        if check_game_over(b) or plies_left <= 0:
            return None
            
        state_key = (b.board_fen(), plies_left)
        if state_key in memo:
            return memo[state_key]

        best_mate = None
        legal_moves = list(b.legal_moves)
        
        # Candidate moves: checks only if plies_left is high
        if plies_left > 4:
            candidates = [m for m in legal_moves if b.gives_check(m)]
        else:
            candidates = legal_moves
            
        # Prioritize checks and captures
        def move_priority(m):
            score = 0
            if b.gives_check(m): score += 100
            if b.is_capture(m): score += 50
            return score
        candidates.sort(key=move_priority, reverse=True)

        for m in candidates:
            b.push(m)
            try:
                res = search_defender(b, plies_left - 1)
            finally:
                b.pop()
                
            if res is not None:
                plies_to_mate = res + 1
                if best_mate is None or plies_to_mate < best_mate:
                    best_mate = plies_to_mate
                    if best_mate == 1:
                        break

        memo[state_key] = best_mate
        return best_mate

    def search_defender(b: chess.Board, plies_left: int) -> int | None:
        nonlocal nodes
        nodes += 1
        if nodes > max_nodes:
            return None
            
        if b.is_checkmate():
            return 0
        if check_game_over(b) or plies_left <= 0:
            return None
            
        state_key = (b.board_fen(), plies_left)
        if state_key in memo:
            return memo[state_key]

        worst_mate = 0
        legal_moves = list(b.legal_moves)
        
        for m in legal_moves:
            b.push(m)
            try:
                res = search_attacker(b, plies_left - 1)
            finally:
                b.pop()
                
            if res is None:
                memo[state_key] = None
                return None
            else:
                plies_to_mate = res + 1
                if plies_to_mate > worst_mate:
                    worst_mate = plies_to_mate

        memo[state_key] = worst_mate
        return worst_mate

    # 1. Check if the active player can force mate
    active_mate = search_attacker(board, max_plies)
    if active_mate is not None and active_mate > 0:
        import math
        moves_to_mate = math.ceil(active_mate / 2)
        if board.turn == chess.WHITE:
            return f"M{moves_to_mate}"
        else:
            return f"-M{moves_to_mate}"

    # Reset nodes/memo for defense search
    nodes = 0
    memo.clear()

    # 2. Check if the active player is forced to be mated
    passive_mate = search_defender(board, max_plies)
    if passive_mate is not None and passive_mate > 0:
        import math
        moves_to_mate = math.ceil(passive_mate / 2)
        if board.turn == chess.WHITE:
            return f"-M{moves_to_mate}"
        else:
            return f"M{moves_to_mate}"

    return None

def parse_eval_to_float(val) -> float:
    try:
        if isinstance(val, str):
            if "M" in val or "m" in val:
                return -8.0 if val.startswith("-") else 8.0
            return float(val)
        return float(val)
    except:
        return 0.0

# --- Bot Move Selector based on ELO ---
def get_bot_move(board: chess.Board, elo: int, q_table: dict) -> tuple[chess.Move | None, float]:
    depth = 3
    use_quiescence = True
    randomize_chance = 0.0
    use_opening_book = True

    # Retrieve remaining time under time control
    time_remaining = float('inf')
    if game_time_limit > 0:
        try:
            time_remaining = float(window.getWhiteTime() if board.turn == chess.WHITE else window.getBlackTime())
        except Exception:
            time_remaining = float(game_time_limit)

    if elo <= 1000:
        depth = 1
        use_quiescence = False
        randomize_chance = 0.35
        use_opening_book = random.random() < 0.5
    elif elo <= 1600:
        # Search up to 3 moves ahead when over 1 minute left.
        # Under 1 minute left, we decrease depth to prevent running out of time.
        if time_remaining > 60:
            depth = 3
            randomize_chance = 0.01  # Play very high quality chess with almost zero deliberate blundering when relaxed
        elif time_remaining > 25:
            depth = 2
            randomize_chance = 0.05
        else:
            depth = 1
            randomize_chance = 0.10  # Time pressure scramble
        use_quiescence = True
        use_opening_book = True
    else:
        # Master/Grandmaster level
        if current_opponent_name and "FireStorm" in current_opponent_name:
            global is_historic_analysis
            if is_historic_analysis:
                depth = 50
            else:
                # Compressed: speed things up during live gameplay
                if time_remaining > 60:
                    depth = 4
                elif time_remaining > 30:
                    depth = 3
                elif time_remaining > 15:
                    depth = 2
                else:
                    depth = 1
        elif time_remaining > 60:
            depth = 4
        elif time_remaining > 30:
            depth = 3
        elif time_remaining > 15:
            depth = 2
        else:
            depth = 1
        use_quiescence = True
        randomize_chance = 0.0
        use_opening_book = True

    # 1. Opening Book
    best_move = None
    if use_opening_book:
        clean_fen = get_clean_fen(board.fen())
        if clean_fen in OPENING_BOOK:
            candidates = OPENING_BOOK[clean_fen]
            chosen_san = random.choice(candidates)
            try:
                best_move = board.parse_san(chosen_san)
            except Exception:
                pass

    # Determine bot personality
    personality = "Nakamura"
    if elo <= 1000 or (current_opponent_name and "Beth" in current_opponent_name):
        personality = "Beth"
    elif current_opponent_name and "FireStorm" in current_opponent_name:
        personality = "FireStorm"
    elif elo >= 2000 or (current_opponent_name and "Garry" in current_opponent_name):
        personality = "Garry"

    # 2. Minimax search
    if not best_move:
        # Scale search time limit dynamically to prevent timeouts
        if current_opponent_name and "FireStorm" in current_opponent_name:
            if is_historic_analysis:
                time_limit = 10.0
            else:
                # Compressed: speed things up
                if game_time_limit > 0:
                    time_limit = max(0.05, min(2.5, time_remaining / 45.0))
                else:
                    time_limit = 2.5
        elif game_time_limit > 0:
            time_limit = max(0.05, min(10.0, time_remaining / 45.0))
        else:
            time_limit = 10.0 if elo >= 2000 else None

        engine = PurePythonChessEngine(use_quiescence=use_quiescence, q_table=q_table, time_limit=time_limit, personality=personality)
        is_maximizing = board.turn == chess.WHITE
        
        legal = list(board.legal_moves)
        if legal:
            try:
                score_cp, pv = engine.parallel_search(board, depth, -999999, 999999, is_maximizing)
                if pv:
                    best_move = pv[0]
                else:
                    ordered = engine.order_moves(board, legal)
                    best_move = ordered[0]
            except Exception as ex:
                print("Error in parallel search, fallback:", ex)
                ordered = engine.order_moves(board, legal)
                best_move = ordered[0]
            
            # Legacy single-core search is bypassed as the parallel multicore search handles search successfully.
            pass

        # Handle random blunder/inaccuracy emulation
        legal = list(board.legal_moves)
        if randomize_chance > 0 and random.random() < randomize_chance and len(legal) > 1:
            scored_legal = []
            for m in legal:
                board.push(m)
                scored_legal.append((m, engine.evaluate_board(board)))
                board.pop()
            
            scored_legal.sort(key=lambda x: x[1], reverse=is_maximizing)
            idx = min(random.randint(1, 2), len(scored_legal) - 1)
            best_move = scored_legal[idx][0]

        if not best_move:
            best_move = random.choice(legal) if legal else None

    # Calculate exact evaluation after move
    eval_score = 0.0
    if best_move:
        board.push(best_move)
        engine_eval = PurePythonChessEngine(q_table=q_table, personality=personality)
        eval_score = round(engine_eval.evaluate_board(board) / 100.0, 2)
        board.pop()

    return best_move, eval_score

# --- RL TD-Learning Backpropagation ---
def learn_from_game(history, result, bot_color_str):
    rl_data = load_rl_memory()
    rl_data["games_played"] += 1

    if result == "win":
        rl_data["bot_wins"] += 1
    elif result == "loss":
        rl_data["bot_losses"] += 1
    else:
        rl_data["bot_draws"] += 1

    gamma = 0.85
    logged_learnings = []

    # Map colors
    bot_colors = []
    if bot_color_str == "both":
        bot_colors = [chess.WHITE, chess.BLACK]
    else:
        bot_colors = [chess.WHITE if bot_color_str == "white" else chess.BLACK]

    for b_color in bot_colors:
        # Filter moves played by this specific bot color
        bot_moves = [m for m in history if m.get("color") == ("w" if b_color == chess.WHITE else "b")]
        reversed_moves = list(reversed(bot_moves))

        for idx, m in enumerate(reversed_moves):
            discount = gamma ** idx
            adjustment = 0.0

            if result == "win":
                adjustment = 50.0 * discount if b_color == chess.WHITE else -50.0 * discount
            elif result == "loss":
                adjustment = -100.0 * discount if b_color == chess.WHITE else 100.0 * discount
            else:
                adjustment = 10.0 * discount if b_color == chess.WHITE else -10.0 * discount

            before_fen = m.get("before")
            if before_fen:
                clean_fen = get_clean_fen(before_fen)
                move_uci = m.get("from") + m.get("to")

                if clean_fen not in rl_data["q_table"]:
                    rl_data["q_table"][clean_fen] = {}

                current_val = rl_data["q_table"][clean_fen].get(move_uci, 0.0)
                new_val = max(-500.0, min(500.0, current_val + adjustment))
                rl_data["q_table"][clean_fen][move_uci] = round(new_val, 2)

                if idx < 3:
                    logged_learnings.append({
                        "fen": clean_fen,
                        "move": m.get("san", move_uci.upper()),
                        "adjustment": round(adjustment, 1),
                        "reason": f"{'White' if b_color == chess.WHITE else 'Black'} {result.capitalize()} feedback",
                        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
                    })

    if logged_learnings:
        rl_data["recent_learnings"] = (logged_learnings + rl_data["recent_learnings"])[:5]

    save_rl_memory(rl_data)
    update_rl_ui()
    return rl_data


# --- Game Engine & Session State Setup ---
board = chess.Board()
move_history = []
move_analyses = []
selected_square = None
premove_obj = None
last_eval = 0.0
game_over_saved = False
last_rendered_fen = None

# Game configurations
mode = "human"  # "human" or "self"
player_color = chess.WHITE
bot_elo = 1600
current_opponent_name = "Coach Nakamura"
game_time_limit = 300 # Default is 5 Min Blitz

# Self play controls
self_play_autoplay = False
autoplay_speed = 1.0
self_play_timer_id = None
view_index = None
manual_result = None
manual_outcome_str = None
is_historic_analysis = False
coach_enabled = True
resign_confirm_active = False

def check_game_over(b):
    if b is board and manual_result is not None:
        return True
    return b.is_game_over(claim_draw=True)

def get_game_result(b):
    if b is board and manual_result is not None:
        return manual_result
    return b.result(claim_draw=True)

# --- UI Sync & Rendering Handlers ---

def get_rendered_board():
    if view_index is not None and 0 <= view_index < len(move_history):
        temp_board = chess.Board()
        for idx in range(view_index + 1):
            m = move_history[idx]
            from_sq = chess.parse_square(m.get("from"))
            to_sq = chess.parse_square(m.get("to"))
            promo_piece = None
            moving_pc = temp_board.piece_at(from_sq)
            if moving_pc and moving_pc.piece_type == chess.PAWN:
                to_rank = chess.square_rank(to_sq)
                if (moving_pc.color == chess.WHITE and to_rank == 7) or (moving_pc.color == chess.BLACK and to_rank == 0):
                    san = m.get("san", "")
                    if "R" in san: promo_piece = chess.ROOK
                    elif "B" in san: promo_piece = chess.BISHOP
                    elif "N" in san: promo_piece = chess.KNIGHT
                    else: promo_piece = chess.QUEEN
            temp_board.push(chess.Move(from_sq, to_sq, promotion=promo_piece))
        return temp_board
    return board


def render_board():
    global last_rendered_fen
    render_board_obj = get_rendered_board()
    
    last_move_obj = render_board_obj.peek() if render_board_obj.move_stack else None
    check_sq = render_board_obj.king(render_board_obj.turn) if render_board_obj.is_check() else None
    
    orientation = chess.WHITE
    if mode == "human":
        orientation = player_color
        
    fill_dict = {}
    
    # 1. Premove highlights
    if premove_obj is not None and view_index is None:
        fill_dict[premove_obj.from_square] = "#EF444470" # soft red/coral
        fill_dict[premove_obj.to_square] = "#F9731670" # soft orange
        
    # 2. Selected square and legal moves highlights
    elif selected_square is not None and view_index is None:
        fill_dict[selected_square] = "#818CF880" # soft indigo-400
        
        is_player_turn = (mode == "human" and board.turn == player_color)
        if is_player_turn:
            # Show actual legal moves
            for m in board.legal_moves:
                if m.from_square == selected_square:
                    dest = m.to_square
                    if board.piece_at(dest) is not None:
                        fill_dict[dest] = "#F8717170" # soft red for capture
                    else:
                        fill_dict[dest] = "#34D39970" # soft emerald for target
        else:
            # Show pseudo-legal move options for potential premoving
            for m in board.generate_pseudo_legal_moves():
                if m.from_square == selected_square:
                    dest = m.to_square
                    if board.piece_at(dest) is not None:
                        fill_dict[dest] = "#F8717140"
                    else:
                        fill_dict[dest] = "#34D39940"
                        
    try:
        board_svg = chess.svg.board(
            board=render_board_obj,
            orientation=orientation,
            lastmove=last_move_obj,
            check=check_sq,
            fill=fill_dict,
            size=3840,
            colors={
                "square light": "#EAF0F6",
                "square dark": "#4B6584",
                "square light lastmove": "#C5E1A5",
                "square dark lastmove": "#9CCC65",
                "margin": "#1A1D24",
                "coord": "#E2E8F0"
            }
        )
    except TypeError:
        board_svg = chess.svg.board(
            board=render_board_obj,
            orientation=orientation,
            lastmove=last_move_obj,
            check=check_sq,
            size=3840,
            colors={
                "square light": "#EAF0F6",
                "square dark": "#4B6584",
                "square light lastmove": "#C5E1A5",
                "square dark lastmove": "#9CCC65",
                "margin": "#1A1D24",
                "coord": "#E2E8F0"
            }
        )
        
    document.getElementById("board-container").innerHTML = board_svg
    
    update_coordinate_selects()
    update_status()
    update_pgn()
    
    current_fen = render_board_obj.fen()
    current_fen_key = f"{view_index}_{current_fen}"
    if last_rendered_fen == current_fen_key:
        return
    last_rendered_fen = current_fen_key
    
    # Update analysis navigation banner
    nav_banner = document.getElementById("analysis-nav-banner")
    nav_text = document.getElementById("analysis-nav-text")
    if nav_banner and nav_text:
        if view_index is not None and 0 <= view_index < len(move_history):
            nav_banner.classList.remove("hidden")
            move_san = move_history[view_index].get("san", "")
            nav_text.innerText = f"Reviewing Move {view_index + 1}/{len(move_history)} ({move_san})"
        else:
            nav_banner.classList.add("hidden")
            
    # Run real-time FireStorm evaluation and prediction (multi-threaded, deep analysis)
    try:
        run_firestorm_realtime_analysis()
    except Exception as e:
        print("Error in FireStorm real-time analysis:", e)
        
    try:
        generate_positional_coach_commentary()
    except Exception as e:
        print("Error generating positional coach commentary:", e)
    
    # Update live move analyses log list
    try:
        update_live_analysis_ui()
    except Exception as e:
        print("Error updating live analysis UI:", e)
        
    # Update main banner last move quality
    try:
        update_last_move_analysis_banner()
    except Exception as e:
        print("Error updating last move banner:", e)
    
    try:
        is_check = render_board_obj.is_check()
        is_capture = False
        if render_board_obj.move_stack:
            try:
                last_m = render_board_obj.pop()
                is_capture = render_board_obj.is_capture(last_m)
                render_board_obj.push(last_m)
            except Exception as e:
                print("Error checking capture status:", e)
        
        game_over_result = None
        if view_index is None and check_game_over(render_board_obj):
            res = get_game_result(render_board_obj)
            if res == "1-0":
                game_over_result = "victory" if (mode == "human" and player_color == chess.WHITE) else "loss" if (mode == "human") else "victory"
            elif res == "0-1":
                game_over_result = "victory" if (mode == "human" and player_color == chess.BLACK) else "loss" if (mode == "human") else "victory"
            else:
                game_over_result = "draw"
                
        window.onTurnChanged(
            "w" if render_board_obj.turn == chess.WHITE else "b",
            check_game_over(render_board_obj) or view_index is not None,
            is_check,
            is_capture,
            game_over_result
        )
    except Exception as e:
        print("Error notifying turn change to JS:", e)


def update_coordinate_selects():
    select_from = document.getElementById("select-from")
    select_to = document.getElementById("select-to")
    
    is_bot_turn = (mode == "human" and board.turn != player_color) or check_game_over(board)
    
    prev_from = select_from.value
    prev_to = select_to.value
    
    # Save from options
    select_from.innerHTML = '<option value="">-- Choose Square --</option>'
    
    if not is_bot_turn:
        from_squares = sorted(list(set([chess.square_name(m.from_square) for m in board.legal_moves])))
        for sq in from_squares:
            opt = document.createElement("option")
            opt.value = sq
            opt.innerText = sq.upper()
            if sq == prev_from:
                opt.selected = True
            select_from.appendChild(opt)
            
    # Reset destination
    select_to.innerHTML = '<option value="">-- Select Destination --</option>'
    if select_from.value and not is_bot_turn:
        try:
            from_sq_idx = chess.parse_square(select_from.value)
            possible_destinations = sorted([chess.square_name(m.to_square) for m in board.legal_moves if m.from_square == from_sq_idx])
            for sq in possible_destinations:
                opt = document.createElement("option")
                opt.value = sq
                opt.innerText = sq.upper()
                if sq == prev_to:
                    opt.selected = True
                select_to.appendChild(opt)
            select_to.disabled = False
        except Exception:
            select_to.disabled = True
    else:
        select_to.disabled = True
        
    update_promo_visibility()
    update_quick_san_select()


def update_promo_visibility():
    select_from = document.getElementById("select-from")
    select_to = document.getElementById("select-to")
    promo_section = document.getElementById("promo-section")
    
    if select_from.value and select_to.value:
        try:
            from_sq_idx = chess.parse_square(select_from.value)
            moving_piece = board.piece_at(from_sq_idx)
            if moving_piece and moving_piece.piece_type == chess.PAWN:
                to_rank = select_to.value[1]
                if (board.turn == chess.WHITE and to_rank == "8") or (board.turn == chess.BLACK and to_rank == "1"):
                    promo_section.classList.remove("hidden")
                    return
        except Exception:
            pass
    promo_section.classList.add("hidden")


def analyze_move(board_before, move_obj):
    global is_historic_analysis
    analysis_personality = "Garry"
    if is_historic_analysis and current_opponent_name and "FireStorm" in current_opponent_name:
        analysis_personality = "FireStorm"
    engine = PurePythonChessEngine(use_quiescence=True, personality=analysis_personality)
    is_maximizing = board_before.turn == chess.WHITE
    
    # Get the best move and score from the before position using GM Garry search (depth 2)
    best_score, best_pv = engine.parallel_search(board_before, 2, -999999, 999999, is_maximizing)
    best_move = best_pv[0] if best_pv else None
    
    # Check if the move is in the opening book
    is_book = False
    clean_fen = get_clean_fen(board_before.fen())
    if clean_fen in OPENING_BOOK:
        for chosen_san in OPENING_BOOK[clean_fen]:
            try:
                book_m = board_before.parse_san(chosen_san)
                if book_m == move_obj:
                    is_book = True
                    break
            except:
                pass
                
    if is_book:
        return {
            "classification": "Book",
            "loss": 0.0,
            "best_move_san": board_before.san(best_move) if best_move else "",
            "evaluation": round(best_score / 100.0, 2)
        }
        
    # Calculate evaluation of actual move played
    board_after = board_before.copy()
    board_after.push(move_obj)
    
    mate_str = detect_checkmate_in_n(board_after, 3)
    if mate_str:
        eval_val = mate_str
        actual_score = 50000 if is_maximizing else -50000
    elif check_game_over(board_after):
        if board_after.is_checkmate():
            eval_val = "M0" if is_maximizing else "-M0"
            actual_score = 50000 if is_maximizing else -50000
        else:
            eval_val = 0.0
            actual_score = 0
    else:
        # Minimax depth 2 from the opponent's perspective
        actual_score, _ = engine.parallel_search(board_after, 2, -999999, 999999, not is_maximizing)
        eval_val = round(actual_score / 100.0, 2)
        
    # Calculate loss
    if is_maximizing:
        loss = (best_score - actual_score) / 100.0
    else:
        loss = (actual_score - best_score) / 100.0
        
    loss = max(0.0, loss)
    
    # Check if Brilliant sacrifice or underpromotion
    is_sacrifice = False
    is_underpromotion = False
    try:
        to_sq = move_obj.to_square
        piece_moved = board_before.piece_at(move_obj.from_square)
        if piece_moved:
            opp_color = not board_before.turn
            attackers = board_before.attackers(opp_color, to_sq)
            if attackers:
                defenders = board_before.attackers(board_before.turn, to_sq)
                if not defenders:
                    is_sacrifice = True
                else:
                    for atk_sq in attackers:
                        atk_pc = board_before.piece_at(atk_sq)
                        if atk_pc and atk_pc.piece_type < piece_moved.piece_type:
                            is_sacrifice = True
                            break

        # Check for underpromotion
        if move_obj.promotion and move_obj.promotion in [chess.KNIGHT, chess.BISHOP, chess.ROOK]:
            is_underpromotion = True
    except:
        pass
        
    if (is_sacrifice or is_underpromotion) and loss <= 0.15:
        classification = "Brilliant"
    elif loss <= 0.05:
        if best_move and move_obj == best_move:
            classification = "Best Move"
        else:
            classification = "Excellent"
    elif loss <= 0.25:
        classification = "Excellent"
    elif loss <= 0.55:
        classification = "Good Move"
    elif loss <= 1.25:
        classification = "Inaccuracy"
    elif loss <= 2.5:
        classification = "Mistake"
    else:
        classification = "Blunder"
        
    return {
        "classification": classification,
        "loss": round(loss, 2),
        "best_move_san": board_before.san(best_move) if best_move else "",
        "evaluation": eval_val,
        "is_sacrifice": is_sacrifice,
        "is_underpromotion": is_underpromotion
    }


def fast_analyze_move(board_before, move_obj):
    global is_historic_analysis
    analysis_personality = "Garry"
    if is_historic_analysis and current_opponent_name and "FireStorm" in current_opponent_name:
        analysis_personality = "FireStorm"
    engine = PurePythonChessEngine(use_quiescence=True, personality=analysis_personality)
    
    # 1. Check if Book Move
    is_book = False
    clean_fen = get_clean_fen(board_before.fen())
    if clean_fen in OPENING_BOOK:
        for chosen_san in OPENING_BOOK[clean_fen]:
            try:
                book_m = board_before.parse_san(chosen_san)
                if book_m == move_obj:
                    is_book = True
                    break
            except:
                pass
                
    if is_book:
        # Static evaluate of board before
        score_cp = engine.evaluate_board(board_before)
        eval_val = round(score_cp / 100.0, 2)
        return {
            "classification": "Book",
            "loss": 0.0,
            "best_move_san": "",
            "evaluation": eval_val,
            "is_sacrifice": False,
            "is_underpromotion": False
        }
        
    # 2. Get static evaluation before and after
    board_after = board_before.copy()
    board_after.push(move_obj)
    
    score_before = engine.evaluate_board(board_before)
    score_after = engine.evaluate_board(board_after)
    
    # Calculate loss from player's perspective
    is_maximizing = board_before.turn == chess.WHITE
    if is_maximizing:
        loss = (score_before - score_after) / 100.0
    else:
        loss = (score_after - score_before) / 100.0
        
    loss = max(0.0, loss)
    eval_val = round(score_after / 100.0, 2)
    
    # Simple check for underpromotion
    is_underpromotion = False
    if move_obj.promotion and move_obj.promotion in [chess.KNIGHT, chess.BISHOP, chess.ROOK]:
        is_underpromotion = True
        
    # Check for sacrifice
    is_sacrifice = False
    try:
        to_sq = move_obj.to_square
        piece_moved = board_before.piece_at(move_obj.from_square)
        if piece_moved:
            opp_color = not board_before.turn
            attackers = board_before.attackers(opp_color, to_sq)
            if attackers:
                defenders = board_before.attackers(board_before.turn, to_sq)
                if not defenders:
                    is_sacrifice = True
                else:
                    for atk_sq in attackers:
                        atk_pc = board_before.piece_at(atk_sq)
                        if atk_pc and atk_pc.piece_type < piece_moved.piece_type:
                            is_sacrifice = True
                            break
    except:
        pass
        
    if (is_sacrifice or is_underpromotion) and loss <= 0.25:
        classification = "Brilliant"
    elif loss <= 0.15:
        classification = "Best Move"
    elif loss <= 0.35:
        classification = "Excellent"
    elif loss <= 0.65:
        classification = "Good Move"
    elif loss <= 1.5:
        classification = "Inaccuracy"
    elif loss <= 3.0:
        classification = "Mistake"
    else:
        classification = "Blunder"
        
    return {
        "classification": classification,
        "loss": round(loss, 2),
        "best_move_san": "",
        "evaluation": eval_val,
        "is_sacrifice": is_sacrifice,
        "is_underpromotion": is_underpromotion
    }


def format_pv_moves(board, pv_list):
    if not pv_list:
        return "No moves predicted."
    
    temp_board = board.copy()
    formatted = []
    move_num = temp_board.fullmove_number
    is_white = temp_board.turn == chess.WHITE
    
    for i, m in enumerate(pv_list):
        if i >= 6: # Predict up to 3 full moves ahead (6 plies)
            break
        try:
            san = temp_board.san(m)
            if is_white:
                if i == 0:
                    formatted.append(f"{move_num}. {san}")
                elif i % 2 == 0:
                    formatted.append(f"{move_num + (i // 2)}. {san}")
                else:
                    formatted.append(san)
            else:
                if i == 0:
                    formatted.append(f"{move_num}... {san}")
                elif i % 2 == 1:
                    formatted.append(f"{move_num + (i // 2) + 1}. {san}")
                else:
                    formatted.append(san)
            temp_board.push(m)
        except:
            break
    return " ".join(formatted)


def run_firestorm_realtime_analysis():
    global last_eval
    active_board = get_rendered_board()
    engine = PurePythonChessEngine(use_quiescence=True, personality="FireStorm")
    is_maximizing = active_board.turn == chess.WHITE
    
    # FireStorm real-time analysis: analyze as far as possible up to depth 8 using ThreadPoolExecutor
    engine.time_limit = 3.0
    score_cp, pv = engine.parallel_search(active_board, 8, -999999, 999999, is_maximizing)
    
    # Check for forced checkmate up to 3 moves (6 plies)
    mate_str = detect_checkmate_in_n(active_board, 3)
    if mate_str:
        last_eval = mate_str
    else:
        last_eval = round(score_cp / 100.0, 2)
    
    # Update prediction box
    pred_el = document.getElementById("predicted-moves-list")
    if pred_el:
        if pv:
            html_parts = []
            temp_board = active_board.copy()
            move_num = temp_board.fullmove_number
            is_white = temp_board.turn == chess.WHITE
            
            for i, m in enumerate(pv):
                try:
                    san = temp_board.san(m)
                    span_class = "px-1.5 py-0.5 rounded text-xs font-semibold font-mono"
                    if temp_board.turn == chess.WHITE:
                        span_class += " bg-gray-100 text-[#0E0F11]"
                    else:
                        span_class += " bg-[#1E212A] text-gray-200 border border-[#2D3343]"
                        
                    label = ""
                    if is_white:
                        if i == 0:
                            label = f"{move_num}. "
                        elif i % 2 == 0:
                            label = f"{move_num + (i // 2)}. "
                    else:
                        if i == 0:
                            label = f"{move_num}... "
                        elif i % 2 == 1:
                            label = f"{move_num + (i // 2) + 1}. "
                    
                    html_parts.append(f'<span class="text-gray-500 font-medium">{label}</span><span class="{span_class}">{san}</span>')
                    temp_board.push(m)
                except:
                    break
            pred_el.innerHTML = " &rarr; ".join(html_parts)
        else:
            pred_el.innerHTML = '<span class="text-gray-500 italic">No further moves predicted (Game Over)</span>'
            
    return last_eval, pv


def update_live_analysis_ui():
    container = document.getElementById("live-move-analysis-container")
    if not container:
        return
        
    if move_history and move_analyses:
        container.innerHTML = ""
        for idx in reversed(range(min(len(move_history), len(move_analyses)))):
            m = move_history[idx]
            ana = move_analyses[idx]
            
            classification = ana.get("classification", "Good Move")
            badge_color = "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
            emoji = "⚪"
            
            if classification == "Brilliant":
                badge_color = "bg-purple-500/20 text-purple-300 border-purple-500/30 animate-pulse font-semibold shadow-sm shadow-purple-500/20"
                emoji = "🔥 !!"
            elif classification == "Best Move":
                badge_color = "bg-emerald-500/20 text-emerald-300 border-emerald-500/30 font-medium"
                emoji = "⭐"
            elif classification == "Excellent":
                badge_color = "bg-teal-500/10 text-teal-300 border-teal-500/20"
                emoji = "🌟"
            elif classification == "Good Move":
                badge_color = "bg-blue-500/10 text-blue-300 border-blue-500/20"
                emoji = "✅"
            elif classification == "Book":
                badge_color = "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
                emoji = "📖"
            elif classification == "Inaccuracy":
                badge_color = "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
                emoji = "⚠️ ?!"
            elif classification == "Mistake":
                badge_color = "bg-orange-500/10 text-orange-400 border-orange-500/20"
                emoji = "❓"
            elif classification == "Blunder":
                badge_color = "bg-indigo-500/20 text-indigo-400 border-indigo-500/30 animate-bounce font-medium"
                emoji = "❌ ??"
                
            color_label = "White" if m.get("color") == "w" else "Black"
            san_move = m.get("san", "")
            turn_num = (idx // 2) + 1
            move_info_str = f"Move {turn_num} ({color_label})"
            
            div = document.createElement("div")
            is_active = (view_index == idx)
            if is_active:
                div.className = "flex items-center justify-between p-3 bg-[#1E212A] border-2 border-indigo-500 rounded-xl transition duration-150 cursor-pointer shadow-md shadow-indigo-500/10"
            else:
                div.className = "flex items-center justify-between p-3 bg-[#0E0F11]/60 border border-[#2D3343]/50 rounded-xl hover:bg-[#15171C] hover:border-[#3E465B] transition duration-150 cursor-pointer"
            
            div.setAttribute("onclick", f"window.setViewIndex({idx})")
            
            sub_text = ""
            if classification in ["Inaccuracy", "Mistake", "Blunder"] and ana.get("best_move_san"):
                sub_text = f'<span class="text-[10px] text-gray-500">Best was <b class="text-emerald-400 font-mono">{ana["best_move_san"]}</b> (loss: -{ana["loss"]:.2f})</span>'
            elif classification == "Brilliant":
                sub_text = '<span class="text-[10px] text-purple-300 font-semibold">Incredible sacrifice!</span>'
            else:
                sub_text = f'<span class="text-[10px] text-gray-500">Engine eval: {ana["evaluation"]:.2f}</span>'
                
            div.innerHTML = f"""
                <div class="flex items-center gap-3">
                    <span class="w-8 h-8 rounded-lg bg-[#191D26] border border-[#2D3343] flex items-center justify-center font-mono font-medium text-xs text-gray-300">{san_move}</span>
                    <div class="flex flex-col">
                        <span class="text-xs text-gray-300 font-semibold">{move_info_str}</span>
                        {sub_text}
                    </div>
                </div>
                <span class="px-2.5 py-1 rounded-lg text-[10px] font-medium font-mono uppercase border {badge_color} flex items-center gap-1">
                    <span>{emoji}</span> <span>{classification}</span>
                </span>
            """
            container.appendChild(div)
    else:
        container.innerHTML = '<div class="text-xs text-gray-500 py-4 text-center">No moves played in this match yet. Start playing to see live analysis!</div>'


def update_last_move_analysis_banner():
    banner = document.getElementById("last-move-analysis")
    san_el = document.getElementById("last-move-san")
    badge_el = document.getElementById("last-move-badge")
    
    if not banner or not san_el or not badge_el:
        return
        
    if move_history and move_analyses:
        banner.classList.remove("hidden")
        latest_move = move_history[-1]
        latest_analysis = move_analyses[-1]
        
        san_el.innerText = latest_move.get("san", "")
        classification = latest_analysis.get("classification", "Good Move")
        
        badge_el.innerText = classification
        badge_el.className = "px-2.5 py-1 rounded-lg text-[10px] font-medium font-mono uppercase border"
        
        emoji = "⚪ "
        if classification == "Brilliant":
            badge_el.classList.add("bg-purple-500/20", "text-purple-300", "border-purple-500/30", "animate-pulse")
            emoji = "🔥 "
        elif classification == "Best Move":
            badge_el.classList.add("bg-emerald-500/20", "text-emerald-300", "border-emerald-500/30")
            emoji = "⭐ "
        elif classification == "Excellent":
            badge_el.classList.add("bg-teal-500/10", "text-teal-300", "border-teal-500/20")
            emoji = "🌟 "
        elif classification == "Good Move":
            badge_el.classList.add("bg-blue-500/10", "text-blue-300", "border-blue-500/20")
            emoji = "✅ "
        elif classification == "Book":
            badge_el.classList.add("bg-cyan-500/10", "text-cyan-400", "border-cyan-500/20")
            emoji = "📖 "
        elif classification == "Inaccuracy":
            badge_el.classList.add("bg-yellow-500/10", "text-yellow-400", "border-yellow-500/20")
            emoji = "⚠️ "
        elif classification == "Mistake":
            badge_el.classList.add("bg-orange-500/10", "text-orange-400", "border-orange-500/20")
            emoji = "❓ "
        elif classification == "Blunder":
            badge_el.classList.add("bg-indigo-500/20", "text-indigo-400", "border-indigo-500/30", "animate-bounce")
            emoji = "❌ "
            
        badge_el.innerText = emoji + classification
    else:
        banner.classList.add("hidden")


def update_quick_san_select():
    select_san = document.getElementById("select-quick-san")
    prev_san = select_san.value
    select_san.innerHTML = '<option value="">-- Quick Move Selection (SAN) --</option>'
    
    is_bot_turn = (mode == "human" and board.turn != player_color) or check_game_over(board)
    if not is_bot_turn:
        legal_moves_san = sorted([board.san(m) for m in board.legal_moves])
        for san in legal_moves_san:
            opt = document.createElement("option")
            opt.value = san
            opt.innerText = san
            if san == prev_san:
                opt.selected = True
            select_san.appendChild(opt)


def update_status():
    status_badge = document.getElementById("status-badge")
    
    if check_game_over(board):
        result = get_game_result(board)
        outcome_str = "Draw"
        if result == "1-0":
            outcome_str = "White won"
        elif result == "0-1":
            outcome_str = "Black won"
            
        if manual_outcome_str:
            outcome_str = manual_outcome_str
            
        status_badge.className = "px-4 py-2 rounded-xl border font-semibold flex items-center gap-2 text-sm bg-indigo-500/10 border-indigo-500/30 text-indigo-400"
        status_badge.innerHTML = f"🏆 Game Over! {result} ({outcome_str})"
        
        handle_game_over(result, outcome_str)
    elif board.is_check():
        status_badge.className = "px-4 py-2 rounded-xl border font-semibold flex items-center gap-2 text-sm bg-indigo-500/10 border-indigo-500/30 text-indigo-400 animate-bounce"
        status_badge.innerHTML = "⚠️ CHECK!"
    else:
        turn_str = "White's Turn" if board.turn == chess.WHITE else "Black's Turn"
        status_badge.className = "px-4 py-2 rounded-xl border font-semibold flex items-center gap-2 text-sm bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
        status_badge.innerHTML = f"""
            <span class="relative flex h-2 w-2">
                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            {turn_str}
        """


def generate_positional_coach_commentary():
    global coach_enabled
    if not coach_enabled:
        try:
            document.getElementById("coach-text").innerHTML = """
            <div class="text-center p-6 bg-slate-900/30 rounded-xl border border-slate-800 text-gray-400 text-xs flex flex-col items-center gap-2">
                <span class="text-lg">📴</span>
                <span class="font-semibold text-gray-300">Grandmaster Coach Commentary Disabled</span>
                <span class="text-[10px] text-gray-500">You can re-enable the coach anytime using the toggle button above to get tactical advice and live commentary.</span>
            </div>
            """
            coach_eval = document.getElementById("coach-eval")
            coach_rating = document.getElementById("coach-rating")
            if coach_eval:
                coach_eval.innerText = "N/A"
                coach_eval.className = "text-3xl font-semibold font-mono text-gray-500"
            if coach_rating:
                coach_rating.innerText = "Coach help is turned off"
                coach_rating.className = "text-sm font-semibold text-gray-500"
        except Exception as e:
            print("Error setting disabled coach UI:", e)
        return

    active_board = get_rendered_board()
    import random
    
    OPENING_GARRY_INSIGHTS = {
        "Ruy Lopez": "Ah, the Spanish Game—Ruy Lopez! A supreme test of chess understanding. White exerts immediate indirect pressure on the central e5-pawn, aiming for a slow, strangulating positional squeeze. Black must defend with steel-like precision, preparing queenside counter-expansion via b5 while securing their king.",
        "Sicilian Najdorf": "The Sicilian Najdorf! The legendary battleground of Bobby Fischer and myself. By playing a6, Black keeps White's knights out of b5 and prepares a flexible, asymmetric assault. White will castle queenside and push kingside pawns, while Black launches a fierce counter-offensive on the c-file. Precision is everything!",
        "Sicilian Dragon": "The Dragon! Black's dark-squared bishop on g7 acts as a sniper rifle pointing down the long diagonal. But beware of the Yugoslav Attack—White will storm the h-file, sacrifice a rook, and aim for a direct checkmate. This is not for the faint-hearted; you must calculate to the absolute end!",
        "Sicilian Scheveningen": "The Scheveningen! A highly elastic 'small center' structure with pawns on d6 and e6. White has a space advantage, but Black's position is a coiled spring. At the right moment, Black will strike back with d6-d5 or e6-e5 to shatter White's central grip.",
        "Sicilian Alapin": "The Alapin (c3 Sicilian). White rejects the hyper-sharp lines of the Open Sicilian in favor of establishing a classical pawn duo on d4 and e4. Black must strike back immediately with d5 or Nf6 to contest the center and avoid being squeezed.",
        "French Defense Advance": "The French Advance. White locks the center with e5, securing a space advantage and crowding Black's kingside. However, Black's strategy is clear: relentlessly attack the base of White's pawn chain on d4 with c5, Nc6, and Qb6. White must defend d4 with their life!",
        "French Defense Exchange": "The French Exchange. A highly symmetrical, calm pawn structure. While many consider it dry and drawish, I say it is a psychological battle! The player with superior piece activity, better king safety, and a clearer strategic plan will triumph.",
        "French Classical": "The French Classical. A tense positional struggle where White defends the e4-pawn with Nc3, and Black challenges it immediately. White gets a space advantage on the kingside, while Black must open up lines on the queenside.",
        "Caro-Kann Classical": "The Caro-Kann Classical. Black develops the light-squared bishop to f5 before locking the pawn chain with e6. It is exceptionally solid and free of major weaknesses, but White retains a space advantage and can try to harass the f5-bishop.",
        "Caro-Kann Advance": "The Caro-Kann Advance. White immediately gains space with e5, locking the pawn chain. Black usually strikes back with c5 or Bf5, trying to prove that White's center is overextended and vulnerable.",
        "Caro-Kann Panov": "The Caro-Kann Panov Attack. An aggressive weapon for White that creates an Isolated Queen Pawn (IQP) on d4. This gives White active piece play and half-open files for attack, but Black gets a target to blockade and pressure in the endgame.",
        "Italian Game": "The Italian Game! One of the oldest and most beautiful openings. White develops the bishop to c4, taking aim at Black's weakest point: the f7-pawn. The game can become a tactical bloodbath in the Evans Gambit or a subtle, slow positional struggle in the Giuoco Pianissimo.",
        "Two Knights Defense": "The Two Knights Defense! A wild, hyper-tactical opening. White's Ng5 tries to exploit f7 immediately, but Black responds with a dynamic pawn sacrifice (d5, Na5, c6) to seize the initiative and active piece play. Calculate every line, or face sudden doom!",
        "Scotch Game": "The Scotch Game. White immediately blows open the center with d4. This leads to open, active piece play. If you enjoy rapid development, tactical skirmishes in the center, and dynamic coordination, this is your home.",
        "Scandinavian Defense": "The Scandinavian! Black immediately challenges White's e4 pawn, but brings the Queen out very early. While White wins a tempo with Nc3, Black's position remains surprisingly resilient. You must play energetically to punish this early queen outing.",
        "Alekhine's Defense": "Alekhine's Defense! A provocative, hypermodern opening. Black lures White's pawns forward to create a massive center, intending to prove that White's pawns are overextended weaknesses rather than strengths. Play with high tactical alertness!",
        "Pirc Defense": "The Pirc Defense. Black allows White to build a classical pawn center, aiming to undermine it later with c5 or e5. It is flexible and asymmetric, offering rich opportunities for both sides to play for a win.",
        "Queen's Gambit Declined": "The Queen's Gambit Declined. The ultimate battlefield of classical chess. Black refuses to yield the center, maintaining a rock-solid pawn on d5. White will try to pressure the d5 square and exploit the passive light-squared bishop, while Black seeks active freeing breaks.",
        "Queen's Gambit Accepted": "The Queen's Gambit Accepted. Black takes the c4 pawn, temporarily giving up the center to gain rapid piece development and play against White's isolated d4 pawn. White must use their central space advantage to create attacking chances.",
        "Slav Defense": "The Slav Defense. One of the most resilient defenses in all of chess theory. Black solidifies the d5 pawn with c6, keeping the diagonal open for the light-squared bishop. It is incredibly tough to break down; White must play with great patience and strategic depth.",
        "King's Indian Defense": "The King's Indian! A hypermodern masterpiece that I have used to win countless battles. Black invites White to build a massive pawn center, only to launch a devastating, direct kingside pawn storm later with f5 and g5. The game is a race: who will mate the opponent first?",
        "Nimzo-Indian Defense": "The Nimzo-Indian. An exceptionally rich opening. Black pins White's knight on c3 to control the critical e4 square and potentially damage White's pawn structure with Bxc3. This leads to deep positional battles over pawn structures and open files.",
        "Grünfeld Defense": "The Grünfeld! A highly dynamic, concrete defense. Black allows White to establish a massive pawn center with e4 and d4, only to immediately blow it apart with d5, c5, and Bg7. It demands precise calculation and deep theoretical knowledge.",
        "Catalan Opening": "The Catalan! A highly sophisticated positional system. White combines the Queen's Gambit with a kingside fianchetto, where the light-squared bishop on g2 exerts long-term pressure along the main diagonal. An elegant and professional choice.",
        "English Opening": "The English Opening. White controls the central d5 square from the flank (c4), keeping the center fluid and avoiding early symmetric lines. It is a highly flexible, intellectual opening that can transpose into many systems.",
        "Dutch Leningrad": "The Dutch Leningrad. An aggressive, fighting system where Black plays f5 and g6, aiming for a kingside storm while maintaining a fluid center. It creates highly asymmetric, sharp positions where a single mistake can be fatal.",
        "Dutch Stonewall": "The Dutch Stonewall. Black establishes a rock-solid pawn wall on d5, e6, f5, and c6, completely neutralizing White's central activity. However, Black's light-squared bishop is severely restricted. A battle of planning and pawn breaks!",
        "Benko Gambit": "The Benko Gambit! An incredibly brave and strategic gambit. Black sacrifices a queenside pawn to open the a and b files for their rooks and queen, exerting long-term, permanent pressure on White's queenside. White must defend tenaciously.",
        "Modern Benoni": "The Modern Benoni. A highly volatile, asymmetrical opening. White has a central pawn majority, while Black has a queenside pawn majority and a powerful dark-squared bishop on g7. Every move is a double-edged sword!",
        "London System": "The London System. Exceptionally solid and bulletproof. However, don't let solidity turn into passivity! You must still seek active pawn breaks (like e4 or c4) and look to open up lines when the opponent shows weakness."
    }

    # Analytical sub-helpers
    def is_passed_pawn(board, sq, color):
        file_idx = chess.square_file(sq)
        rank_idx = chess.square_rank(sq)
        opp_color = not color
        files_to_check = [f for f in [file_idx - 1, file_idx, file_idx + 1] if 0 <= f <= 7]
        for f in files_to_check:
            if color == chess.WHITE:
                ranks_ahead = range(rank_idx + 1, 8)
            else:
                ranks_ahead = range(0, rank_idx)
            for r in ranks_ahead:
                check_sq = chess.square(f, r)
                piece = board.piece_at(check_sq)
                if piece and piece.piece_type == chess.PAWN and piece.color == opp_color:
                    return False
        return True

    def check_king_safety(board, color):
        king_sq = board.king(color)
        if not king_sq:
            return "neutral"
        file_idx = chess.square_file(king_sq)
        if file_idx >= 5:
            shield_files = [5, 6, 7]
            shield_rank = 1 if color == chess.WHITE else 6
            pawn_count = 0
            for f in shield_files:
                pc = board.piece_at(chess.square(f, shield_rank))
                if pc and pc.piece_type == chess.PAWN and pc.color == color:
                    pawn_count += 1
            if pawn_count <= 1:
                return "exposed_kingside"
        elif file_idx <= 2:
            shield_files = [0, 1, 2]
            shield_rank = 1 if color == chess.WHITE else 6
            pawn_count = 0
            for f in shield_files:
                pc = board.piece_at(chess.square(f, shield_rank))
                if pc and pc.piece_type == chess.PAWN and pc.color == color:
                    pawn_count += 1
            if pawn_count <= 1:
                return "exposed_queenside"
        elif file_idx in [3, 4]:
            if len(board.move_stack) > 12:
                return "center_stuck"
        return "secure"

    def get_rook_insights(board, color):
        rooks = board.pieces(chess.ROOK, color)
        insights = []
        seventh_rank = 6 if color == chess.WHITE else 1
        for sq in rooks:
            file_idx = chess.square_file(sq)
            rank_idx = chess.square_rank(sq)
            if rank_idx == seventh_rank:
                insights.append("rook_on_7th")
            is_open = True
            for r in range(8):
                pc = board.piece_at(chess.square(file_idx, r))
                if pc and pc.piece_type == chess.PAWN:
                    is_open = False
                    break
            if is_open:
                insights.append("rook_on_open_file")
        return list(set(insights))

    # 1. Determine active player & last move
    current_move_idx = view_index if view_index is not None else (len(move_history) - 1)
    
    last_move_obj = None
    if active_board.move_stack:
        last_move_obj = active_board.peek()
        
    move_desc = ""
    class_text = ""
    class_color = "text-gray-300"
    
    # Identify last move details if available
    if 0 <= current_move_idx < len(move_history):
        m = move_history[current_move_idx]
        san_move = m.get("san", "")
        color_label = "White" if m.get("color") == "w" else "Black"
        
        from_sq = m.get("from", "")
        to_sq = m.get("to", "")
        
        pc_type = m.get("piece", "")
        captured = m.get("captured", "")
        
        # Fallback dynamic resolution from the 'before' FEN if needed
        if (not pc_type or not captured) and m.get("before") and from_sq and to_sq:
            try:
                temp_board = chess.Board(m.get("before"))
                from_sq_val = chess.parse_square(from_sq)
                to_sq_val = chess.parse_square(to_sq)
                
                if not pc_type:
                    pc = temp_board.piece_at(from_sq_val)
                    if pc:
                        pc_type = pc.symbol().upper()
                        
                if not captured:
                    if temp_board.is_capture(chess.Move(from_sq_val, to_sq_val)):
                        if temp_board.is_en_passant(chess.Move(from_sq_val, to_sq_val)):
                            captured = "P"
                        else:
                            cap_pc_obj = temp_board.piece_at(to_sq_val)
                            if cap_pc_obj:
                                captured = cap_pc_obj.symbol().upper()
            except Exception as e:
                print("Error deducing piece type on the fly:", e)
        
        pc_type = pc_type.upper() if pc_type else ""
        if pc_type == "P": pc_type = "Pawn"
        elif pc_type == "N": pc_type = "Knight"
        elif pc_type == "B": pc_type = "Bishop"
        elif pc_type == "R": pc_type = "Rook"
        elif pc_type == "Q": pc_type = "Queen"
        elif pc_type == "K": pc_type = "King"
        if not pc_type:
            pc_type = "Piece"
            
        if captured:
            cap_pc = captured.upper()
            if cap_pc == "P": cap_pc = "Pawn"
            elif cap_pc == "N": cap_pc = "Knight"
            elif cap_pc == "B": cap_pc = "Bishop"
            elif cap_pc == "R": cap_pc = "Rook"
            elif cap_pc == "Q": cap_pc = "Queen"
            move_desc = f"{color_label}'s {pc_type} captured a {cap_pc} on {to_sq} (<strong>{san_move}</strong>)."
        else:
            if "O-O-O" in san_move:
                move_desc = f"{color_label} castled queenside to safety (<strong>{san_move}</strong>)."
            elif "O-O" in san_move:
                move_desc = f"{color_label} castled kingside, securing the king (<strong>{san_move}</strong>)."
            else:
                move_desc = f"{color_label} played <strong>{san_move}</strong>, relocating their {pc_type} from {from_sq} to {to_sq}."
                
        # Analysis classification evaluation
        if current_move_idx < len(move_analyses):
            ana = move_analyses[current_move_idx]
            classification = ana.get("classification", "")
            best_move_san = ana.get("best_move_san", "")
            
            if classification == "Brilliant":
                class_color = "text-cyan-400 font-semibold"
                if ana.get("is_underpromotion"):
                    class_text = f"🔥 <strong>Brilliant Underpromotion!</strong> An incredible tactical choice with {san_move}! Absolutely brilliant positional vision. This is the real art of chess."
                else:
                    class_text = f"🔥 <strong>Brilliant Sacrifice!</strong> A spectacular tactical strike with {san_move}! Truly brilliant tactical vision. Kasparov would be proud of such creative fire!"
            elif classification == "Best Move":
                class_color = "text-emerald-400 font-medium"
                class_text = f"⭐ <strong>Best Move!</strong> Highly accurate: {san_move} matches the exact engine recommendation. You are playing with clinical GM precision."
            elif classification == "Excellent":
                class_color = "text-emerald-300 font-semibold"
                class_text = f"✨ <strong>Excellent Move!</strong> Great play with {san_move}, keeping optimal pressure on the opponent and advancing your key plans."
            elif classification == "Good Move":
                class_color = "text-blue-400"
                class_text = f"📈 <strong>Good Move.</strong> A solid positional choice with {san_move}, maintaining comfortable balance and stability."
            elif classification == "Book":
                class_color = "text-cyan-400"
                class_text = f"📖 <strong>Book Move.</strong> Following classical chess theory: {san_move} is a well-established opening line."
            elif classification == "Inaccuracy":
                class_color = "text-yellow-400"
                class_text = f"⚠️ <strong>Inaccuracy.</strong> Slight deviation with {san_move}. The engine preferred {best_move_san} to lock down control and prevent counterplay."
            elif classification == "Mistake":
                class_color = "text-orange-400"
                class_text = f"❌ <strong>Mistake!</strong> A positional error. {san_move} cedes structural control. {best_move_san} would have been much stronger to hold the line."
            elif classification == "Blunder":
                class_color = "text-indigo-500 font-medium"
                class_text = f"🚨 <strong>Blunder!</strong> A catastrophic miscalculation. {san_move} seriously compromises the position. {best_move_san} was crucial here to avoid tactical ruin."

    # 2. Material Balance
    total_material_sans_kings = sum(len(active_board.pieces(pt, chess.WHITE)) * PIECE_VALUES[pt] + len(active_board.pieces(pt, chess.BLACK)) * PIECE_VALUES[pt] for pt in PIECE_VALUES if pt != chess.KING)
    turn_count = len(active_board.move_stack)
    
    # 3. Phase & Structural Commentary (Opening, Middlegame, Endgame)
    matched_opening = None
    if turn_count <= 24:
        current_sans = [m.get("san", "") for m in move_history[:current_move_idx + 1]]
        if current_sans:
            for op_name, op_moves in OPENING_LINES.items():
                if len(current_sans) <= len(op_moves):
                    if op_moves[:len(current_sans)] == current_sans:
                        matched_opening = op_name
                        break
                        
    if matched_opening:
        context_text = OPENING_GARRY_INSIGHTS.get(matched_opening, f"We are playing the deep theoretical lines of the <strong>{matched_opening}</strong>. In these positions, dynamic development and rapid activation of your pieces is key to seizing the initiative!")
    elif total_material_sans_kings <= 3000:
        context_text = "We have transitioned to an <strong>Endgame</strong>. All strategic paradigms have shifted! King centralization, pawn chains, and defending or creating passed pawns are now of paramount importance."
    else:
        center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
        white_center_attacks = sum(len(active_board.attackers(chess.WHITE, sq)) for sq in center_squares)
        black_center_attacks = sum(len(active_board.attackers(chess.BLACK, sq)) for sq in center_squares)
        if white_center_attacks > black_center_attacks + 1:
            context_text = "White enjoys a strong grip on the center squares, controlling major files. Black is being squeezed in space."
        elif black_center_attacks > white_center_attacks + 1:
            context_text = "Black dominates the central zone, restricting White's coordination and expansion."
        else:
            context_text = "We are in the heat of a complex <strong>Middlegame</strong>. The central files remain highly contested with strong pawn tension."

    # 4. Tactical Scanner (Direct Board Checks)
    tactical_findings = []
    
    # Check status
    if active_board.is_check():
        defending_color = "White" if active_board.turn == chess.WHITE else "Black"
        tactical_findings.append(f"⚠️ <strong class='text-indigo-400'>Check!</strong> {defending_color} is in check and must address this threat immediately!")
        
    # Pinned pieces
    pinned_info = []
    for sq in chess.SQUARES:
        pc = active_board.piece_at(sq)
        if pc and pc.piece_type != chess.KING:
            if active_board.is_pinned(pc.color, sq):
                pc_name = "Knight" if pc.piece_type == chess.KNIGHT else "Bishop" if pc.piece_type == chess.BISHOP else "Rook" if pc.piece_type == chess.ROOK else "Queen" if pc.piece_type == chess.QUEEN else "Pawn"
                pinned_info.append(f"the {pc_name} on {chess.square_name(sq)}")
    if pinned_info:
        tactical_findings.append(f"🔗 <strong class='text-cyan-400'>Tactical Pin:</strong> {', '.join(pinned_info[:2])} is currently pinned against the King.")
        
    # Fork detection
    if last_move_obj:
        to_sq = last_move_obj.to_square
        attacker_pc = active_board.piece_at(to_sq)
        if attacker_pc:
            attacks = active_board.attacks(to_sq)
            attacked_targets = []
            for target_sq in attacks:
                target_pc = active_board.piece_at(target_sq)
                if target_pc and target_pc.color == active_board.turn:
                    val = PIECE_VALUES.get(target_pc.piece_type, 100)
                    attacked_targets.append((target_sq, target_pc, val))
            if len(attacked_targets) >= 2:
                attacked_targets.sort(key=lambda x: x[2], reverse=True)
                t1_name = "Knight" if attacked_targets[0][1].piece_type == chess.KNIGHT else "Bishop" if attacked_targets[0][1].piece_type == chess.BISHOP else "Rook" if attacked_targets[0][1].piece_type == chess.ROOK else "Queen" if attacked_targets[0][1].piece_type == chess.QUEEN else "Pawn"
                t2_name = "Knight" if attacked_targets[1][1].piece_type == chess.KNIGHT else "Bishop" if attacked_targets[1][1].piece_type == chess.BISHOP else "Rook" if attacked_targets[1][1].piece_type == chess.ROOK else "Queen" if attacked_targets[1][1].piece_type == chess.QUEEN else "Pawn"
                tactical_findings.append(f"🔱 <strong class='text-indigo-400'>Fork Attack!</strong> The {attacker_pc.symbol().upper()} on {chess.square_name(to_sq)} is fork-attacking both {t1_name} on {chess.square_name(attacked_targets[0][0])} and {t2_name} on {chess.square_name(attacked_targets[1][0])}!")

    # Hanging pieces
    hanging_list = []
    for sq in chess.SQUARES:
        pc = active_board.piece_at(sq)
        if pc and pc.piece_type != chess.KING:
            is_attacked = active_board.is_attacked_by(not pc.color, sq)
            defenders = active_board.attackers(pc.color, sq)
            if is_attacked and len(defenders) == 0:
                pc_name = "Knight" if pc.piece_type == chess.KNIGHT else "Bishop" if pc.piece_type == chess.BISHOP else "Rook" if pc.piece_type == chess.ROOK else "Queen" if pc.piece_type == chess.QUEEN else "Pawn"
                hanging_list.append(f"the {pc_name} on {chess.square_name(sq)}")
    if hanging_list:
        tactical_findings.append(f"🔴 <strong class='text-indigo-400'>Hanging Piece!</strong> {', '.join(hanging_list[:2])} is completely hanging and unprotected!")

    # Passed pawns
    passed_pawns_white = []
    passed_pawns_black = []
    for sq in active_board.pieces(chess.PAWN, chess.WHITE):
        if is_passed_pawn(active_board, sq, chess.WHITE):
            passed_pawns_white.append(chess.square_name(sq))
    for sq in active_board.pieces(chess.PAWN, chess.BLACK):
        if is_passed_pawn(active_board, sq, chess.BLACK):
            passed_pawns_black.append(chess.square_name(sq))
            
    if passed_pawns_white:
        tactical_findings.append(f"🏃 <strong class='text-emerald-400'>Passed Pawn (White):</strong> Passed pawn on {', '.join(passed_pawns_white[:2])}. It is a powerful dynamic asset!")
    if passed_pawns_black:
        tactical_findings.append(f"🏃 <strong class='text-indigo-400'>Passed Pawn (Black):</strong> Passed pawn on {', '.join(passed_pawns_black[:2])}. Must be blockaded immediately!")

    # Bishop Pair
    has_white_pair = len(active_board.pieces(chess.BISHOP, chess.WHITE)) >= 2
    has_black_pair = len(active_board.pieces(chess.BISHOP, chess.BLACK)) >= 2
    if has_white_pair and not has_black_pair:
        tactical_findings.append("♝ <strong class='text-emerald-400'>Bishop Pair:</strong> White holds the bishop pair advantage on open diagonals.")
    elif has_black_pair and not has_white_pair:
        tactical_findings.append("♝ <strong class='text-indigo-400'>Bishop Pair:</strong> Black holds the bishop pair, commanding the board diagonals.")

    # King Safety check
    white_safety = check_king_safety(active_board, chess.WHITE)
    black_safety = check_king_safety(active_board, chess.BLACK)
    if white_safety in ["exposed_kingside", "exposed_queenside"]:
        tactical_findings.append("👑 <strong class='text-indigo-400'>King Vulnerability:</strong> White's king pawn shield is compromised. Safeguard the back rank!")
    elif white_safety == "center_stuck":
        tactical_findings.append("👑 <strong class='text-indigo-400'>King Stuck:</strong> White's king remains uncastled and vulnerable in the center of the board.")
        
    if black_safety in ["exposed_kingside", "exposed_queenside"]:
        tactical_findings.append("👑 <strong class='text-indigo-400'>King Vulnerability:</strong> Black's king shield is broken. Watch for tactics!")
    elif black_safety == "center_stuck":
        tactical_findings.append("👑 <strong class='text-indigo-400'>King Stuck:</strong> Black's king remains uncastled and vulnerable in the center.")

    # Rooks on 7th or open files
    white_rook_ins = get_rook_insights(active_board, chess.WHITE)
    black_rook_ins = get_rook_insights(active_board, chess.BLACK)
    if "rook_on_7th" in white_rook_ins:
        tactical_findings.append("🏰 <strong class='text-emerald-400'>White Rook on 7th:</strong> A monster on the 7th rank! Paralyzes the opponent's pieces.")
    if "rook_on_7th" in black_rook_ins:
        tactical_findings.append("🏰 <strong class='text-indigo-400'>Black Rook on 7th:</strong> Black has established a highly dangerous rook on the 7th rank.")

    # 5. Strategic general tips matching the current position
    tips = []
    open_files = []
    for f in range(8):
        has_pawn = False
        for r in range(8):
            pc = active_board.piece_at(chess.square(f, r))
            if pc and pc.piece_type == chess.PAWN:
                has_pawn = True
                break
        if not has_pawn:
            open_files.append(chr(97 + f))
            
    if open_files:
        tips.append(f"Strategic Hint: The {', '.join(open_files[:2])}-files are fully open. Placing your rooks on these open files can trigger deep incursions.")
    else:
        tips.append("Strategic Hint: With the board closed, Knights are extremely valuable. Position them on central outposts.")
        
    outposts = []
    for sq in chess.SQUARES:
        pc = active_board.piece_at(sq)
        if pc and pc.piece_type == chess.KNIGHT:
            rank = chess.square_rank(sq)
            if (pc.color == chess.WHITE and 3 <= rank <= 5) or (pc.color == chess.BLACK and 2 <= rank <= 4):
                defenders = active_board.attackers(pc.color, sq)
                for def_sq in defenders:
                    def_pc = active_board.piece_at(def_sq)
                    if def_pc and def_pc.piece_type == chess.PAWN:
                        outposts.append(chess.square_name(sq))
                        break
    if outposts:
        tips.append(f"Outpost Found: An excellent knight anchor exists on {outposts[0]}. Keep the knight active there to restrict your opponent.")
    else:
        tips.append("Strategic Hint: Look to establish strong minor piece anchors on key central squares.")
        
    tip_idx = len(active_board.move_stack) % len(tips)
    strategic_tip = tips[tip_idx]
    
    # 6. Garry's Personal Advice Quotes
    eval_score = last_eval
    is_mate = False
    is_white_mate = False
    if isinstance(eval_score, str) and "M" in eval_score:
        is_mate = True
        is_white_mate = not eval_score.startswith("-")
        
    garry_quotes = []
    if is_mate:
        if is_white_mate:
            garry_quotes = [
                "The end is near! White has calculated a forced mate. Black is completely lost. Striking with absolute, ruthless power!",
                "Checkmate is on the horizon. White's attack is beautiful and unstoppable. This is how chess is meant to be finished!"
            ]
        else:
            garry_quotes = [
                "A forced mate for Black! White's defense has crumbled. Black is executing the mating attack with clinical precision.",
                "Inescapable mate! Black's tactical coordination is complete. The king has nowhere to hide."
            ]
    else:
        try:
            val_score = float(eval_score)
        except:
            val_score = 0.0
            
        if val_score > 2.0:
            garry_quotes = [
                "White is completely winning! The squeeze is absolute. When you have your opponent on the ropes, do not hesitate—strike with maximum energy!",
                "White holds a crushing advantage. Black is suffocating under the weight of White's pieces. Stay sharp, calculate to the end, and claim the point."
            ]
        elif val_score > 0.5:
            garry_quotes = [
                "White holds a distinct strategic advantage. Continue coordinating your forces, expand your space, and force the opponent into difficult defensive choices.",
                "Excellent positional pressure by White. Do not rush—increase the pressure, control the key files, and wait for the structural break."
            ]
        elif val_score < -2.0:
            garry_quotes = [
                "Black has seized total control of the board! White's coordination is in ruins. Attack with absolute aggression, victory is close!",
                "A dominating position for Black. White's pieces are completely disconnected. Keep your foot on the gas and look for the tactical knockout!"
            ]
        elif val_score < -0.5:
            garry_quotes = [
                "Black holds the advantage. White is forced onto the defensive. Focus on creating weaknesses in their camp and dominating the center.",
                "Black's piece placement is superior. Push your plans forward, establish firm outposts, and slowly restrict White's activity."
            ]
        else:
            garry_quotes = [
                "The position remains highly balanced, but balance in chess is a dynamic illusion! One careless step and the dam breaks. Calculate and play with courage.",
                "A tense, maneuvering struggle. Look for pawn levers, establish strong minor piece anchors, and prepare to seize any small tactical slip by your opponent.",
                "Both sides are fighting with immense energy. In balanced positions, psychology is everything. Play with concrete, active plans—never pass passive moves!"
            ]
            
    if current_opponent_name and "FireStorm" in current_opponent_name:
        garry_quotes = [f"🔥 [FIRESTORM ENGINE ACTIVE] {q}" for q in garry_quotes]
            
    seed_val = len(active_board.move_stack)
    advisory_quote = garry_quotes[seed_val % len(garry_quotes)]

    # Build a magnificent, highly-formatted coaching layout
    verdict_html = ""
    if 0 <= current_move_idx < len(move_history):
        verdict_html = f"""
        <div class="border-b border-[#2D3343]/50 pb-3">
            <span class="block text-[10px] font-medium text-indigo-400 uppercase tracking-wider mb-1">🎯 Last Move Verdict</span>
            <p class="text-xs text-gray-300 leading-relaxed mb-1.5">{move_desc}</p>
            {f'<p class="text-xs leading-relaxed {class_color}">{class_text}</p>' if class_text else ''}
        </div>
        """
        
    tactical_html = ""
    if tactical_findings:
        findings_li = "".join([f"<li class='text-[11px] text-gray-300 list-none mb-1.5'>{f}</li>" for f in tactical_findings[:4]])
        tactical_html = f"""
        <div class="border-b border-[#2D3343]/50 pb-3">
            <span class="block text-[10px] font-medium text-indigo-400 uppercase tracking-wider mb-1.5">🔬 Tactical & Structural Scanner</span>
            <ul class="space-y-1 pl-0">
                {findings_li}
            </ul>
        </div>
        """
        
    # Build material balance element
    white_mat = sum(len(active_board.pieces(pt, chess.WHITE)) * PIECE_VALUES[pt] for pt in PIECE_VALUES)
    black_mat = sum(len(active_board.pieces(pt, chess.BLACK)) * PIECE_VALUES[pt] for pt in PIECE_VALUES)
    material_diff = (white_mat - black_mat) / 100.0
    if material_diff == 0:
        mat_text = "⚖️ <span class='text-gray-400 font-semibold'>Material is perfectly equal.</span>"
    elif material_diff > 0:
        mat_text = f"⚖️ <span class='text-emerald-400 font-medium'>White +{material_diff:.1f} pawns</span> ahead in material."
    else:
        mat_text = f"⚖️ <span class='text-indigo-400 font-medium'>Black +{abs(material_diff):.1f} pawns</span> ahead in material."
        
    material_html = f"""
    <div class="border-b border-[#2D3343]/50 pb-3">
        <span class="block text-[10px] font-medium text-indigo-400 uppercase tracking-wider mb-1">⚖️ Material Balance</span>
        <p class="text-xs text-gray-300 leading-relaxed">{mat_text}</p>
    </div>
    """

    advisory_title = "FireStorm Alpha's Advisory" if (current_opponent_name and "FireStorm" in current_opponent_name) else "Garry's Advisory"

    html_commentary = f"""
    <div class="flex flex-col gap-3.5 text-left">
        <!-- Section 1: Strategic Context -->
        <div class="border-b border-[#2D3343]/50 pb-3">
            <span class="block text-[10px] font-medium text-indigo-400 uppercase tracking-wider mb-1">♟️ Strategic Context</span>
            <p class="text-xs text-gray-300 leading-relaxed">{context_text}</p>
        </div>
        
        <!-- Section 2: Last Move Verdict -->
        {verdict_html}
        
        <!-- Section 3: Material Balance -->
        {material_html}
        
        <!-- Section 4: Tactical Scanner -->
        {tactical_html}
        
        <!-- Section 5: Advisory -->
        <div>
            <span class="block text-[10px] font-medium text-indigo-400 uppercase tracking-wider mb-1">💬 {advisory_title}</span>
            <p class="text-xs text-gray-200 leading-relaxed italic border-l-2 border-indigo-500 pl-2.5 py-0.5">
                "{advisory_quote}"
            </p>
        </div>
    </div>
    """
    
    document.getElementById("coach-text").innerHTML = html_commentary
    
    coach_eval = document.getElementById("coach-eval")
    coach_rating = document.getElementById("coach-rating")
    
    eval_score = last_eval
    is_mate = False
    is_white_mate = False
    mate_moves = 0
    
    if isinstance(eval_score, str) and "M" in eval_score:
        is_mate = True
        is_white_mate = not eval_score.startswith("-")
        try:
            import re
            m_match = re.search(r'\d+', eval_score)
            mate_moves = int(m_match.group()) if m_match else 1
        except:
            mate_moves = 1
            
    if is_mate:
        coach_eval.innerText = eval_score
        if is_white_mate:
            coach_eval.className = "text-3xl font-semibold font-mono text-emerald-400"
            coach_rating.innerText = f"White has forced mate in {mate_moves}"
            coach_rating.className = "text-sm font-semibold text-emerald-400"
        else:
            coach_eval.className = "text-3xl font-semibold font-mono text-indigo-400"
            coach_rating.innerText = f"Black has forced mate in {mate_moves}"
            coach_rating.className = "text-sm font-semibold text-indigo-400"
    else:
        # Standard numeric score
        if eval_score > 0:
            coach_eval.innerText = f"+{eval_score:.2f}"
            coach_eval.className = "text-3xl font-semibold font-mono text-emerald-400"
        else:
            coach_eval.innerText = f"{eval_score:.2f}"
            coach_eval.className = "text-3xl font-semibold font-mono text-indigo-400"
            
        if eval_score > 2.0:
            coach_rating.innerText = "White is winning"
            coach_rating.className = "text-sm font-semibold text-emerald-400"
        elif eval_score > 0.5:
            coach_rating.innerText = "White holds advantage"
            coach_rating.className = "text-sm font-semibold text-emerald-300"
        elif eval_score < -2.0:
            coach_rating.innerText = "Black is winning"
            coach_rating.className = "text-sm font-semibold text-indigo-400"
        elif eval_score < -0.5:
            coach_rating.innerText = "Black holds advantage"
            coach_rating.className = "text-sm font-semibold text-indigo-300"
        else:
            coach_rating.innerText = "Balanced Position"
            coach_rating.className = "text-sm font-semibold text-gray-300"

    try:
        window.updateEvaluationBar(last_eval)
    except Exception as e:
        print("Error updating visual evaluation bar:", e)

    try:
        # Construct list of evaluations from move_analyses
        evals = [parse_eval_to_float(ana.get("evaluation", 0.0)) for ana in move_analyses]
        # Include initial 0.0 score at move 0
        window.updateMomentumChart(json.dumps([0.0] + evals))
    except Exception as e:
        print("Error updating momentum chart:", e)


def update_rl_ui():
    rl_data = load_rl_memory()
    
    document.getElementById("rl-games").innerText = rl_data.get("games_played", 0)
    document.getElementById("rl-wins").innerText = rl_data.get("bot_wins", 0)
    document.getElementById("rl-losses").innerText = rl_data.get("bot_losses", 0)
    document.getElementById("rl-draws").innerText = rl_data.get("bot_draws", 0)
    
    # Games total header bar
    try:
        import js_helper
        js_helper.update_games_stat(rl_data.get("games_played", 0))
    except Exception:
        pass
        
    recent_container = document.getElementById("rl-recent-container")
    recent_learnings = rl_data.get("recent_learnings", [])
    
    if recent_learnings:
        recent_container.innerHTML = ""
        for item in recent_learnings:
            div = document.createElement("div")
            div.className = "text-xs bg-[#0E0F11] border border-[#2D3343]/60 p-2.5 rounded-lg flex flex-col gap-1"
            
            ts = item.get("timestamp", "")
            time_part = ts[-13:-4] if len(ts) > 13 else ""
            
            div.innerHTML = f"""
                <div class="flex justify-between items-center font-semibold text-gray-300">
                    <span>Move <code class="bg-[#1E212A] px-1.5 py-0.5 rounded text-indigo-400">{item['move']}</code></span>
                    <span class="text-emerald-400">{item['adjustment']:+.1f} pts</span>
                </div>
                <div class="flex justify-between text-[10px] text-gray-500">
                    <span>{item['reason']}</span>
                    <span>{time_part}</span>
                </div>
            """
            recent_container.appendChild(div)
    else:
        recent_container.innerHTML = '<div class="text-xs text-gray-500 py-4 text-center">No temporal difference corrections recorded yet. Complete games to train.</div>'


def analyze_historic_match(match_id):
    history_list = load_matches_history()
    match_item = None
    for h in history_list:
        if str(h.get("id")) == str(match_id):
            match_item = h
            break
            
    if not match_item:
        print("Match not found in history:", match_id)
        return
        
    global board, move_history, move_analyses, last_eval, game_over_saved, self_play_autoplay, mode, player_color, bot_elo, current_opponent_name, game_time_limit, selected_square, premove_obj, last_rendered_fen, view_index, is_historic_analysis
    
    is_historic_analysis = True
    # Initialize variables
    board = chess.Board()
    move_history = []
    move_analyses = []
    selected_square = None
    premove_obj = None
    last_rendered_fen = None
    last_eval = 0.0
    game_over_saved = True # Prevent saving this analyzed game as a new game
    self_play_autoplay = False
    mode = "human"
    view_index = None # Reset view index to live position initially
    
    p_color_str = match_item.get("playerColor", "White")
    player_color = chess.WHITE if p_color_str == "White" else chess.BLACK
    bot_elo = match_item.get("botElo", 1600)
    current_opponent_name = match_item.get("opponent", "Opponent")
    game_time_limit = 0 # Untimed during analysis
    
    # Play each move on the board to rebuild state
    hist_moves = match_item.get("history", [])
    for m in hist_moves:
        from_sq = chess.parse_square(m.get("from"))
        to_sq = chess.parse_square(m.get("to"))
        promo_piece = None
        moving_pc = board.piece_at(from_sq)
        if moving_pc and moving_pc.piece_type == chess.PAWN:
            to_rank = chess.square_rank(to_sq)
            if (moving_pc.color == chess.WHITE and to_rank == 7) or (moving_pc.color == chess.BLACK and to_rank == 0):
                san = m.get("san", "")
                if "R" in san: promo_piece = chess.ROOK
                elif "B" in san: promo_piece = chess.BISHOP
                elif "N" in san: promo_piece = chess.KNIGHT
                else: promo_piece = chess.QUEEN
                
        move_obj = chess.Move(from_sq, to_sq, promotion=promo_piece)
        if move_obj in board.legal_moves:
            board_before = board.copy()
            san_move = board.san(move_obj)
            
            # Analyze move
            try:
                analysis_res = analyze_move(board_before, move_obj)
                move_analyses.append(analysis_res)
            except Exception as ex:
                print("Error analyzing historic move:", ex)
                move_analyses.append({"classification": "Good Move", "loss": 0.0, "best_move_san": "", "evaluation": 0.0})
                
            move_history.append({
                "before": board_before.fen(),
                "from": m.get("from"),
                "to": m.get("to"),
                "color": m.get("color"),
                "san": san_move
            })
            board.push(move_obj)
            
    # Synchronize UI input values
    document.getElementById("select-mode").value = "human"
    document.getElementById("select-color").value = "white" if player_color == chess.WHITE else "black"
    document.getElementById("range-elo").value = str(bot_elo)
    on_elo_change(None)
    
    # Update HTML layouts
    document.getElementById("human-color-section").classList.remove("hidden")
    document.getElementById("self-play-section").classList.add("hidden")
    
    # Render board
    render_board()
    
    # Automatically switch tab to Coach Commentary so the user sees the analysis
    try:
        tab_coach = document.getElementById("tab-coach")
        if tab_coach:
            tab_coach.click()
    except Exception as e:
        print("Error switching tab:", e)

    is_historic_analysis = False


def import_pgn_game(pgn_str):
    import io
    import chess.pgn
    global board, move_history, move_analyses, last_eval, game_over_saved, self_play_autoplay, mode, player_color, bot_elo, current_opponent_name, game_time_limit, selected_square, premove_obj, last_rendered_fen, view_index
    
    pgn_str = pgn_str.strip()
    if not pgn_str:
        return "Please paste a PGN string first."
        
    try:
        pgn_io = io.StringIO(pgn_str)
        game = chess.pgn.read_game(pgn_io)
        if not game:
            return "No valid chess game found in PGN."
            
        board = game.board()
        move_history = []
        move_analyses = []
        selected_square = None
        premove_obj = None
        last_rendered_fen = None
        last_eval = 0.0
        game_over_saved = True # Analytical view
        self_play_autoplay = False
        view_index = None # Start at the end position
        mode = "human"
        
        # Parse names from headers
        white_player = game.headers.get("White", "").strip()
        black_player = game.headers.get("Black", "").strip()
        if white_player and black_player:
            current_opponent_name = f"{white_player} vs {black_player}"
        elif white_player:
            current_opponent_name = f"{white_player} (White)"
        elif black_player:
            current_opponent_name = f"{black_player} (Black)"
        else:
            current_opponent_name = "Imported PGN Game"
            
        try:
            document.getElementById("opponent-name-display").innerText = current_opponent_name
        except Exception:
            pass
            
        # Rebuild and analyze every move
        node = game
        while node.variations:
            next_node = node.variation(0)
            move_obj = next_node.move
            board_before = node.board()
            
            try:
                analysis_res = fast_analyze_move(board_before, move_obj)
            except Exception as ex:
                print("Error analyzing imported move:", ex)
                analysis_res = {"classification": "Good Move", "loss": 0.0, "best_move_san": "", "evaluation": 0.0}
                
            move_analyses.append(analysis_res)
            
            # Extract piece and capture details explicitly
            moving_pc = board_before.piece_at(move_obj.from_square)
            pc_sym = moving_pc.symbol().upper() if moving_pc else ""
            
            captured_sym = ""
            if board_before.is_capture(move_obj):
                if board_before.is_en_passant(move_obj):
                    captured_sym = "P"
                else:
                    cap_pc = board_before.piece_at(move_obj.to_square)
                    captured_sym = cap_pc.symbol().upper() if cap_pc else ""
            
            san_move = board_before.san(move_obj)
            move_history.append({
                "before": board_before.fen(),
                "from": chess.square_name(move_obj.from_square),
                "to": chess.square_name(move_obj.to_square),
                "color": "w" if board_before.turn == chess.WHITE else "b",
                "san": san_move,
                "piece": pc_sym,
                "captured": captured_sym
            })
            
            node = next_node
            
        board = node.board()
        
        # Synchronize select mode value
        try:
            document.getElementById("select-mode").value = "human"
        except:
            pass
            
        render_board()
        
        # Automatically switch to Coach Commentary tab
        try:
            tab_coach = document.getElementById("tab-coach")
            if tab_coach:
                tab_coach.click()
        except:
            pass
            
        return "SUCCESS"
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"PGN Parse Error: {str(e)}"


def import_fen_game(fen_str):
    global board, move_history, move_analyses, last_eval, game_over_saved, self_play_autoplay, mode, player_color, bot_elo, current_opponent_name, game_time_limit, selected_square, premove_obj, last_rendered_fen, view_index
    
    fen_str = fen_str.strip()
    if not fen_str:
        return "Please paste a FEN string first."
        
    try:
        # Validate FEN
        test_board = chess.Board(fen_str)
        
        board = test_board
        move_history = []
        move_analyses = []
        selected_square = None
        premove_obj = None
        last_rendered_fen = None
        last_eval = 0.0
        game_over_saved = True # Analytical view
        self_play_autoplay = False
        view_index = None
        mode = "human"
        current_opponent_name = "Custom FEN Position"
        
        # Orient board to current side's turn
        player_color = board.turn
        
        try:
            document.getElementById("opponent-name-display").innerText = current_opponent_name
            document.getElementById("select-mode").value = "human"
            document.getElementById("select-color").value = "white" if player_color == chess.WHITE else "black"
        except Exception:
            pass
            
        render_board()
        
        # Automatically switch to Coach Commentary tab
        try:
            tab_coach = document.getElementById("tab-coach")
            if tab_coach:
                tab_coach.click()
        except:
            pass
            
        return "SUCCESS"
    except Exception as e:
        return f"Invalid FEN: {str(e)}"


def set_view_index(idx):
    global view_index
    idx_str = str(idx)
    if idx_str == "none" or idx_str == "" or idx_str == "-1":
        view_index = None
    else:
        view_index = int(idx)
    render_board()


def on_analysis_prev_click(event):
    global view_index
    if view_index is not None:
        if view_index > 0:
            set_view_index(view_index - 1)
    elif move_history:
        set_view_index(len(move_history) - 1)


def on_analysis_next_click(event):
    global view_index
    if view_index is not None:
        if view_index < len(move_history) - 1:
            set_view_index(view_index + 1)
        else:
            set_view_index(-1)


def on_analysis_live_click(event):
    set_view_index(-1)


def on_analysis_first_click(event):
    if move_history:
        set_view_index(0)


def on_analysis_last_click(event):
    if move_history:
        set_view_index(len(move_history) - 1)


def update_history_ui():
    history_list = load_matches_history()
    container = document.getElementById("history-container")
    
    if history_list:
        container.innerHTML = ""
        for idx, h in enumerate(reversed(history_list[-5:])):
            div = document.createElement("div")
            div.className = "bg-[#0E0F11] border border-[#2D3343] p-3 rounded-xl flex flex-col gap-2"
            
            outcome_color = "text-emerald-400" if h['result'] == 'won' else "text-indigo-400" if h['result'] == 'lost' else "text-gray-400"
            
            san_sequence = " ".join([m.get("san", "") for m in h.get("history", [])])
            
            div.innerHTML = f"""
                <div class="flex justify-between items-center text-xs">
                    <span class="font-medium text-white">Match #{h['id']}</span>
                    <span class="text-[10px] text-gray-500">{h['date']}</span>
                </div>
                <div class="text-xs text-gray-400">
                    Opponent: <span class="text-gray-300 font-semibold">{h['opponent']}</span>
                </div>
                <div class="text-xs">
                    Result: <span class="font-medium {outcome_color}">{h['result'].upper()}</span> ({h['outcomeDetail']})
                </div>
                <div class="flex flex-col gap-1">
                    <span class="text-[10px] text-gray-500 font-medium uppercase">Move Sequence:</span>
                    <textarea class="w-full bg-[#1E212A] border border-[#2D3343] rounded-lg p-1.5 text-[10px] text-gray-300 font-mono h-12 resize-none" readonly>{san_sequence}</textarea>
                </div>
                <div class="flex gap-2 mt-1">
                    <button onclick="window.analyzeHistoricMatch('{h['id']}')" class="flex-grow py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-lg text-[11px] transition duration-200">
                        🔬 Analyze with GM Garry
                    </button>
                    <button onclick="window.copyHistoricPgn('{h['id']}')" class="px-3 py-1.5 bg-[#2D3343] hover:bg-[#3E465B] text-gray-300 hover:text-white font-medium rounded-lg text-[11px] transition duration-200" title="Copy PGN to Clipboard">
                        📋 Copy PGN
                    </button>
                </div>
            """
            container.appendChild(div)
    else:
        container.innerHTML = '<div class="text-xs text-gray-500 py-4 text-center">No historic records saved yet. Complete a full match!</div>'


def copy_historic_pgn(match_id):
    history_list = load_matches_history()
    for h in history_list:
        if str(h.get("id")) == str(match_id):
            saved_pgn = h.get("pgn")
            if not saved_pgn:
                # Dynamically construct PGN
                date_str = h.get("date", "").split(" ")[0].replace("-", ".") if h.get("date") else "2026.07.15"
                p_col = h.get("playerColor", "White")
                white_name = "Human" if p_col == "White" else h.get("opponent", "Opponent")
                black_name = "Human" if p_col == "Black" else h.get("opponent", "Opponent")
                game_result = "1-0" if h.get("result") == "won" and p_col == "White" else "0-1" if h.get("result") == "won" and p_col == "Black" else "0-1" if h.get("result") == "lost" and p_col == "White" else "1-0" if h.get("result") == "lost" and p_col == "Black" else "1/2-1/2"
                san_sequence = " ".join([m.get("san", "") for m in h.get("history", [])])
                saved_pgn = f"""[Event "Firestorm Chess Match"]
[Site "Local Browser"]
[Date "{date_str}"]
[Round "1"]
[White "{white_name}"]
[Black "{black_name}"]
[Result "{game_result}"]

{san_sequence}"""
            
            # call window.copyToClipboard in javascript
            window.copyToClipboard(saved_pgn)
            return True
    return False


def update_pgn():
    current_pgn_moves = [m.get("san", "") for m in move_history]
    
    date_str = datetime.datetime.now().strftime('%Y.%m.%d')
    
    white_name = "Human" if mode == "human" and player_color == chess.WHITE else "Firestorm Bot"
    black_name = "Human" if mode == "human" and player_color == chess.BLACK else "Firestorm Bot"
    
    res = get_game_result(board)
    
    pgn_text = f"""[Event "Firestorm Match"]
[Site "Wasm Browser Sandboxed Sandbox"]
[Date "{date_str}"]
[Round "1"]
[White "{white_name}"]
[Black "{black_name}"]
[Result "{res}"]

{" ".join(current_pgn_moves)}"""
    
    document.getElementById("pgn-output").value = pgn_text


# --- Game Loop & Bot Handlers ---

def check_trigger_bot_move():
    if mode == "human" and board.turn != player_color and not check_game_over(board):
        status_badge = document.getElementById("status-badge")
        status_badge.className = "px-4 py-2 rounded-xl border font-semibold flex items-center gap-2 text-sm bg-cyan-500/10 border-cyan-500/30 text-cyan-400 animate-pulse"
        status_badge.innerHTML = "⚡ Bot calculation in progress..."
        
        # Use setTimeout to yield the execution context to browser
        window.setTimeout(create_proxy(run_bot_move), 150)


def run_bot_move():
    import asyncio
    asyncio.ensure_future(run_bot_move_async())

async def run_bot_move_async():
    global last_eval
    rl_mem = load_rl_memory()
    board_before = board.copy()
    
    b_move = None
    b_eval = 0.0
    
    # Try fetching from the multi-core backend server first
    try:
        from pyodide.http import pyfetch
        response = await pyfetch(
            "/api/bot_move",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps({
                "fen": board.fen(),
                "elo": bot_elo,
                "q_table": rl_mem.get("q_table", {})
            })
        )
        if response.status == 200:
            data = await response.json()
            if "best_move" in data and data["best_move"]:
                b_move = chess.Move.from_uci(data["best_move"])
                b_eval = data.get("eval_score", 0.0)
                print("Using multi-core backend bot move:", b_move, "eval:", b_eval)
    except Exception as e:
        print("Server-side search not available, falling back to local engine:", e)
        
    # Fallback to local engine if server search failed or is offline
    if not b_move:
        b_move, b_eval = get_bot_move(board, bot_elo, rl_mem.get("q_table", {}))
        print("Using local engine bot move:", b_move, "eval:", b_eval)
        
    if b_move:
        san_move = board.san(b_move)
        move_history.append({
            "before": board.fen(),
            "from": chess.square_name(b_move.from_square),
            "to": chess.square_name(b_move.to_square),
            "color": "w" if board.turn == chess.WHITE else "b",
            "san": san_move
        })
        
        # Analyze bot move in real-time with GM Garry
        try:
            analysis_res = analyze_move(board_before, b_move)
            move_analyses.append(analysis_res)
        except Exception as ex:
            print("Error analyzing bot move:", ex)
            move_analyses.append({"classification": "Good Move", "loss": 0.0, "best_move_san": "", "evaluation": 0.0})
            
        board.push(b_move)
        render_board()
        
        # Check and play premove if one is queued
        try:
            check_trigger_premove()
        except Exception as e:
            print("Error triggering premove:", e)


def handle_game_over(result, outcome_str):
    global game_over_saved
    if game_over_saved:
        return
        
    global self_play_autoplay
    self_play_autoplay = False
    
    res_str = "draw"
    if result == "1-0":
        res_str = "win" if (mode == "human" and player_color == chess.WHITE) else "loss" if (mode == "human") else "white_win"
    elif result == "0-1":
        res_str = "win" if (mode == "human" and player_color == chess.BLACK) else "loss" if (mode == "human") else "black_win"
        
    # Temporal difference weights updates
    if mode == "human":
        learn_from_game(move_history, res_str, "black" if player_color == chess.WHITE else "white")
    else:
        learn_from_game(move_history, "win" if res_str == "white_win" else "loss" if res_str == "black_win" else "draw", "both")

    # Match Archive
    import random
    m_history = load_matches_history()
    
    pgn_moves = [m.get("san", "") for m in move_history]
    white_name = "Human" if mode == "human" and player_color == chess.WHITE else f"{current_opponent_name} ({bot_elo})" if mode == "human" else "Self-Play White"
    black_name = "Human" if mode == "human" and player_color == chess.BLACK else f"{current_opponent_name} ({bot_elo})" if mode == "human" else "Self-Play Black"
    game_res_str = result if result else "*"
    date_str = datetime.datetime.now().strftime("%Y.%m.%d")
    match_pgn = f"""[Event "Firestorm Chess Match"]
[Site "Local Browser"]
[Date "{date_str}"]
[Round "1"]
[White "{white_name}"]
[Black "{black_name}"]
[Result "{game_res_str}"]

{" ".join(pgn_moves)}"""

    m_history.append({
        "id": str(random.randint(100000, 999999)),
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "opponent": f"{current_opponent_name} ({bot_elo})" if mode == "human" else "Self-Play",
        "botElo": bot_elo,
        "playerColor": "White" if mode == "human" and player_color == chess.WHITE else "Black" if mode == "human" else "Spectator",
        "result": "won" if res_str == "win" or res_str == "white_win" else "lost" if res_str == "loss" or res_str == "black_win" else "draw",
        "outcomeDetail": outcome_str,
        "history": list(move_history),
        "pgn": match_pgn
    })
    save_matches_history(m_history)
    
    game_over_saved = True
    update_history_ui()
    update_rl_ui()


# --- Event Listeners callbacks ---

def on_from_change(event):
    update_coordinate_selects()


def check_trigger_premove():
    global premove_obj, selected_square, last_eval, move_history, move_analyses
    if premove_obj is not None:
        temp_premove = premove_obj
        premove_obj = None
        
        if temp_premove in board.legal_moves:
            board_before = board.copy()
            san_move = board.san(temp_premove)
            from_str = chess.square_name(temp_premove.from_square)
            to_str = chess.square_name(temp_premove.to_square)
            
            move_history.append({
                "before": board.fen(),
                "from": from_str,
                "to": to_str,
                "color": "w" if board.turn == chess.WHITE else "b",
                "san": san_move
            })
            
            # Analyze move in real-time with GM Garry
            try:
                analysis_res = analyze_move(board_before, temp_premove)
                move_analyses.append(analysis_res)
            except Exception as ex:
                print("Error analyzing premove:", ex)
                move_analyses.append({"classification": "Good Move", "loss": 0.0, "best_move_san": "", "evaluation": 0.0})
                
            board.push(temp_premove)
            
            # Clear selects
            select_from = document.getElementById("select-from")
            if select_from:
                select_from.value = ""
            select_to = document.getElementById("select-to")
            if select_to:
                select_to.value = ""
                
            render_board()
            
            # Since player moved, check/trigger bot move
            check_trigger_bot_move()
        else:
            # Stale/illegal premove, just re-render to clear highlights
            render_board()


def handle_square_click(sq):
    global selected_square, premove_obj, last_eval, move_history, move_analyses
    
    is_player_turn = (board.turn == player_color)
    piece = board.piece_at(sq)
    
    # 1. OPPONENT'S TURN: PREMOVE LOGIC
    if not is_player_turn:
        if check_game_over(board):
            return
            
        if selected_square is None:
            # Select own piece for premove
            if piece and piece.color == player_color:
                selected_square = sq
                select_from = document.getElementById("select-from")
                if select_from:
                    select_from.value = chess.square_name(sq)
                update_coordinate_selects()
                render_board()
        else:
            # A piece was already selected
            if sq == selected_square:
                selected_square = None
                select_from = document.getElementById("select-from")
                if select_from:
                    select_from.value = ""
                update_coordinate_selects()
                render_board()
            elif piece and piece.color == player_color:
                selected_square = sq
                select_from = document.getElementById("select-from")
                if select_from:
                    select_from.value = chess.square_name(sq)
                update_coordinate_selects()
                render_board()
            else:
                # Store premove (pawn promotion defaults)
                promo_char = ""
                moving_piece = board.piece_at(selected_square)
                if moving_piece and moving_piece.piece_type == chess.PAWN:
                    if (player_color == chess.WHITE and chess.square_rank(sq) == 7) or \
                       (player_color == chess.BLACK and chess.square_rank(sq) == 0):
                        promo_select = document.getElementById("select-promo")
                        promo_char = promo_select.value if promo_select else "q"
                        
                promo_piece = None
                if promo_char:
                    if promo_char == "q": promo_piece = chess.QUEEN
                    elif promo_char == "r": promo_piece = chess.ROOK
                    elif promo_char == "b": promo_piece = chess.BISHOP
                    elif promo_char == "n": promo_piece = chess.KNIGHT
                    
                premove_obj = chess.Move(selected_square, sq, promotion=promo_piece)
                selected_square = None
                select_from = document.getElementById("select-from")
                if select_from:
                    select_from.value = ""
                update_coordinate_selects()
                render_board()
                
    # 2. PLAYER'S TURN: NORMAL MOVE LOGIC
    else:
        if check_game_over(board):
            return
            
        if selected_square is None:
            # Select own piece
            if piece and piece.color == player_color:
                selected_square = sq
                select_from = document.getElementById("select-from")
                if select_from:
                    select_from.value = chess.square_name(sq)
                update_coordinate_selects()
                render_board()
        else:
            # A piece was already selected
            if sq == selected_square:
                selected_square = None
                select_from = document.getElementById("select-from")
                if select_from:
                    select_from.value = ""
                update_coordinate_selects()
                render_board()
            elif piece and piece.color == player_color:
                selected_square = sq
                select_from = document.getElementById("select-from")
                if select_from:
                    select_from.value = chess.square_name(sq)
                update_coordinate_selects()
                render_board()
            else:
                # Try to execute move
                promo_char = ""
                moving_piece = board.piece_at(selected_square)
                if moving_piece and moving_piece.piece_type == chess.PAWN:
                    if (player_color == chess.WHITE and chess.square_rank(sq) == 7) or \
                       (player_color == chess.BLACK and chess.square_rank(sq) == 0):
                        promo_select = document.getElementById("select-promo")
                        promo_char = promo_select.value if promo_select else "q"
                        
                promo_piece = None
                if promo_char:
                    if promo_char == "q": promo_piece = chess.QUEEN
                    elif promo_char == "r": promo_piece = chess.ROOK
                    elif promo_char == "b": promo_piece = chess.BISHOP
                    elif promo_char == "n": promo_piece = chess.KNIGHT
                    
                move_obj = chess.Move(selected_square, sq, promotion=promo_piece)
                if move_obj in board.legal_moves:
                    board_before = board.copy()
                    san_move = board.san(move_obj)
                    from_str = chess.square_name(selected_square)
                    to_str = chess.square_name(sq)
                    
                    move_history.append({
                        "before": board.fen(),
                        "from": from_str,
                        "to": to_str,
                        "color": "w" if board.turn == chess.WHITE else "b",
                        "san": san_move
                    })
                    
                    # Analyze move in real-time with GM Garry
                    try:
                        analysis_res = analyze_move(board_before, move_obj)
                        move_analyses.append(analysis_res)
                    except Exception as ex:
                        print("Error analyzing move:", ex)
                        move_analyses.append({"classification": "Good Move", "loss": 0.0, "best_move_san": "", "evaluation": 0.0})
                        
                    board.push(move_obj)
                    
                    selected_square = None
                    select_from = document.getElementById("select-from")
                    if select_from:
                        select_from.value = ""
                    select_to = document.getElementById("select-to")
                    if select_to:
                        select_to.value = ""
                    update_coordinate_selects()
                    render_board()
                    
                    # Check bot response
                    check_trigger_bot_move()
                else:
                    # Not a legal move, select new piece if own, else deselect
                    if piece and piece.color == player_color:
                        selected_square = sq
                        select_from = document.getElementById("select-from")
                        if select_from:
                            select_from.value = chess.square_name(sq)
                    else:
                        selected_square = None
                        select_from = document.getElementById("select-from")
                        if select_from:
                            select_from.value = ""
                    update_coordinate_selects()
                    render_board()


def on_board_click(event):
    global selected_square, premove_obj
    
    if mode != "human":
        return
        
    svg_el = document.querySelector("#board-container svg")
    if not svg_el:
        return
        
    try:
        point = svg_el.createSVGPoint()
        point.x = event.clientX
        point.y = event.clientY
        svg_point = point.matrixTransform(svg_el.getScreenCTM().inverse())
        svg_x = svg_point.x
        svg_y = svg_point.y
    except Exception as ex:
        print("Error translating coordinates:", ex)
        return
        
    if 15 <= svg_x <= 375 and 15 <= svg_y <= 375:
        file_idx = int((svg_x - 15) // 45)
        rank_idx = int((svg_y - 15) // 45) # 0 is top, 7 is bottom
        
        orientation = player_color if mode == "human" else chess.WHITE
        if orientation == chess.WHITE:
            file = file_idx
            rank = 7 - rank_idx
        else:
            file = 7 - file_idx
            rank = rank_idx
            
        sq = chess.square(file, rank)
        handle_square_click(sq)


def on_board_right_click(event):
    global selected_square, premove_obj
    event.preventDefault()
    
    if selected_square is not None or premove_obj is not None:
        selected_square = None
        premove_obj = None
        select_from = document.getElementById("select-from")
        if select_from:
            select_from.value = ""
        update_coordinate_selects()
        render_board()


def on_push_move_click(event):
    global last_eval
    select_from = document.getElementById("select-from")
    select_to = document.getElementById("select-to")
    select_promo = document.getElementById("select-promo")
    
    if not select_from.value or not select_to.value:
        window.alert("Please complete the move coordinates!")
        return
        
    from_str = select_from.value
    to_str = select_to.value
    
    # Check promotion
    promo_char = ""
    promo_section = document.getElementById("promo-section")
    if not promo_section.classList.contains("hidden"):
        promo_char = select_promo.value
        
    try:
        move_obj = chess.Move.from_uci(from_str + to_str + promo_char)
        if move_obj in board.legal_moves:
            board_before = board.copy()
            san_move = board.san(move_obj)
            move_history.append({
                "before": board.fen(),
                "from": from_str,
                "to": to_str,
                "color": "w" if board.turn == chess.WHITE else "b",
                "san": san_move
            })
            
            # Analyze move in real-time with GM Garry
            try:
                analysis_res = analyze_move(board_before, move_obj)
                move_analyses.append(analysis_res)
            except Exception as ex:
                print("Error analyzing move:", ex)
                move_analyses.append({"classification": "Good Move", "loss": 0.0, "best_move_san": "", "evaluation": 0.0})
                
            board.push(move_obj)
            
            # Reset dropdowns
            select_from.value = ""
            select_to.value = ""
            
            render_board()
            
            # Check bot response
            check_trigger_bot_move()
        else:
            window.alert("Illegal move coordinates!")
    except Exception as e:
        window.alert(f"Invalid Move: {str(e)}")


def on_quick_move_click(event):
    global last_eval
    select_san = document.getElementById("select-quick-san")
    quick_move = select_san.value
    
    if not quick_move:
        window.alert("Please select a SAN move first!")
        return
        
    try:
        move_obj = board.parse_san(quick_move)
        board_before = board.copy()
        move_history.append({
            "before": board.fen(),
            "from": chess.square_name(move_obj.from_square),
            "to": chess.square_name(move_obj.to_square),
            "color": "w" if board.turn == chess.WHITE else "b",
            "san": quick_move
        })
        
        # Analyze move in real-time with GM Garry
        try:
            analysis_res = analyze_move(board_before, move_obj)
            move_analyses.append(analysis_res)
        except Exception as ex:
            print("Error analyzing move:", ex)
            move_analyses.append({"classification": "Good Move", "loss": 0.0, "best_move_san": "", "evaluation": 0.0})
            
        board.push(move_obj)
        
        render_board()
        check_trigger_bot_move()
    except Exception as e:
        window.alert(f"Failed to push quick move: {str(e)}")


def on_undo_click(event):
    global game_over_saved, self_play_autoplay, move_history, move_analyses, selected_square, premove_obj, last_rendered_fen
    self_play_autoplay = False
    selected_square = None
    premove_obj = None
    last_rendered_fen = None
    
    # Pop white and black moves
    if len(board.move_stack) >= 2:
        board.pop()
        board.pop()
        if len(move_history) >= 2:
            move_history = move_history[:-2]
        if len(move_analyses) >= 2:
            move_analyses = move_analyses[:-2]
            
        game_over_saved = False
        render_board()
    elif len(board.move_stack) == 1:
        board.pop()
        move_history = []
        move_analyses = []
        game_over_saved = False
        render_board()


def on_reset_click(event):
    global board, move_history, move_analyses, last_eval, game_over_saved, self_play_autoplay, selected_square, premove_obj, last_rendered_fen, manual_result, manual_outcome_str
    board = chess.Board()
    move_history = []
    move_analyses = []
    selected_square = None
    premove_obj = None
    last_rendered_fen = None
    last_eval = 0.0
    game_over_saved = False
    self_play_autoplay = False
    manual_result = None
    manual_outcome_str = None
    render_board()
    try:
        window.initClocks(game_time_limit)
    except Exception:
        pass


def on_draw_click(event):
    global manual_result, manual_outcome_str
    if check_game_over(board):
        return
        
    if board.can_claim_draw():
        manual_result = "1/2-1/2"
        manual_outcome_str = "Draw claimed"
    else:
        # Default to agreed draw if clicked
        manual_result = "1/2-1/2"
        manual_outcome_str = "Agreed Draw"
        
    render_board()


def on_resign_click(event):
    global manual_result, manual_outcome_str, resign_confirm_active
    if check_game_over(board):
        return
        
    btn = document.getElementById("btn-resign")
    if not resign_confirm_active:
        resign_confirm_active = True
        if btn:
            btn.innerHTML = '<span class="text-rose-400 font-bold">⚠️ Confirm?</span>'
            btn.className = "px-3 py-2 bg-rose-600/20 text-rose-300 rounded-xl transition duration-200 border border-rose-500/40 flex items-center gap-1.5 text-xs font-semibold animate-pulse"
        
        # Reset after 3 seconds
        def reset_resign():
            global resign_confirm_active
            if resign_confirm_active:
                resign_confirm_active = False
                cur_btn = document.getElementById("btn-resign")
                if cur_btn:
                    cur_btn.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3l18 18M3 21L21 3" /></svg>Resign'
                    cur_btn.className = "px-3 py-2 bg-indigo-600/10 hover:bg-indigo-600 hover:text-white text-indigo-400 rounded-xl transition duration-200 border border-indigo-500/20 flex items-center gap-1.5 text-xs font-semibold"
        
        try:
            window.setTimeout(create_proxy(reset_resign), 3000)
        except Exception:
            pass
        return
        
    resign_confirm_active = False
    if btn:
        btn.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3l18 18M3 21L21 3" /></svg>Resign'
        btn.className = "px-3 py-2 bg-indigo-600/10 hover:bg-indigo-600 hover:text-white text-indigo-400 rounded-xl transition duration-200 border border-indigo-500/20 flex items-center gap-1.5 text-xs font-semibold"

    if mode == "human":
        if player_color == chess.WHITE:
            manual_result = "0-1"
            manual_outcome_str = "White resigned"
        else:
            manual_result = "1-0"
            manual_outcome_str = "Black resigned"
    else:
        manual_result = "0-1"
        manual_outcome_str = "White resigned"
        
    render_board()


def on_mode_change(event):
    global mode
    mode = document.getElementById("select-mode").value
    
    human_color_section = document.getElementById("human-color-section")
    self_play_section = document.getElementById("self-play-section")
    
    if mode == "human":
        human_color_section.classList.remove("hidden")
        self_play_section.classList.add("hidden")
    else:
        human_color_section.classList.add("hidden")
        self_play_section.classList.remove("hidden")
        
    on_reset_click(None)


def on_color_change(event):
    global player_color
    color_val = document.getElementById("select-color").value
    player_color = chess.WHITE if color_val == "white" else chess.BLACK
    on_reset_click(None)


def on_elo_change(event):
    global bot_elo, current_opponent_name
    bot_elo = int(document.getElementById("range-elo").value)
    badge = document.getElementById("elo-badge")
    
    if bot_elo == 1000:
        current_opponent_name = "Beginner Beth"
        badge.innerText = "1000 (Beginner)"
        badge.className = "text-xs px-2.5 py-1 bg-emerald-500/10 text-emerald-400 rounded-lg border border-emerald-500/20 font-mono font-medium"
    elif bot_elo == 1600:
        current_opponent_name = "Coach Nakamura"
        badge.innerText = "1600 (Intermediate)"
        badge.className = "text-xs px-2.5 py-1 bg-cyan-500/10 text-cyan-400 rounded-lg border border-cyan-500/20 font-mono font-medium"
    elif bot_elo == 2000:
        current_opponent_name = "GM Garry"
        badge.innerText = "2000 (Grandmaster)"
        badge.className = "text-xs px-2.5 py-1 bg-indigo-500/10 text-indigo-400 rounded-lg border border-indigo-500/20 font-mono font-medium"
    elif bot_elo >= 2200:
        current_opponent_name = "FireStorm GM Alpha"
        badge.innerText = "2400 (FireStorm Alpha) 🔥"
        badge.className = "text-xs px-2.5 py-1 bg-red-500/10 text-red-400 rounded-lg border border-red-500/20 font-mono font-medium"

    try:
        document.getElementById("opponent-name-display").innerText = current_opponent_name
    except Exception:
        pass


def on_speed_change(event):
    global autoplay_speed
    autoplay_speed = float(document.getElementById("range-speed").value)
    document.getElementById("speed-val").innerText = f"{autoplay_speed:.1f}s"


def on_autoplay_play(event):
    global self_play_autoplay
    if mode == "self" and not check_game_over(board):
        self_play_autoplay = True
        run_self_play_step()


def on_autoplay_pause(event):
    global self_play_autoplay
    self_play_autoplay = False


def run_self_play_step():
    global last_eval
    if not self_play_autoplay or check_game_over(board) or mode != "self":
        return
        
    rl_mem = load_rl_memory()
    board_before = board.copy()
    b_move, b_eval = get_bot_move(board, bot_elo, rl_mem.get("q_table", {}))
    
    if b_move:
        san_move = board.san(b_move)
        move_history.append({
            "before": board.fen(),
            "from": chess.square_name(b_move.from_square),
            "to": chess.square_name(b_move.to_square),
            "color": "w" if board.turn == chess.WHITE else "b",
            "san": san_move
        })
        
        # Analyze move in real-time with GM Garry
        try:
            analysis_res = analyze_move(board_before, b_move)
            move_analyses.append(analysis_res)
        except Exception as ex:
            print("Error analyzing self-play move:", ex)
            move_analyses.append({"classification": "Good Move", "loss": 0.0, "best_move_san": "", "evaluation": 0.0})
            
        board.push(b_move)
        
        render_board()
        
        # Schedule next step with dynamic delay adjusted by remaining time and time control
        current_delay = autoplay_speed
        if game_time_limit > 0:
            time_remaining = window.getWhiteTime() if board.turn == chess.WHITE else window.getBlackTime()
            try:
                time_remaining = float(time_remaining)
            except Exception:
                time_remaining = float(game_time_limit)
            
            # Dynamic calculation: scale down speed/thinking delay as time gets low
            if time_remaining < 10:
                current_delay = 0.15 # Panic rapid play
            elif time_remaining < 30:
                current_delay = 0.35 # Fast-paced play
            elif time_remaining < 60:
                current_delay = 0.6  # Moderately fast play
            elif time_remaining < 120:
                current_delay = 0.8  # Alert play
            else:
                # Proportional speed calculation based on estimated moves remaining
                allocated = time_remaining / 45.0
                # Capped at the base autoplay speed chosen by the user
                current_delay = min(autoplay_speed, allocated)
            
            # Keep speed bounded between 0.1s and maximum delay (3.0s or autoplay_speed)
            current_delay = max(0.1, min(3.0, current_delay))

        delay_ms = int(current_delay * 1000)
        window.setTimeout(create_proxy(run_self_play_step), delay_ms)


def on_clear_rl_click(event):
    reset_mem = {
        "games_played": 0,
        "bot_wins": 0,
        "bot_losses": 0,
        "bot_draws": 0,
        "q_table": {},
        "recent_learnings": []
    }
    save_rl_memory(reset_mem)
    update_rl_ui()
    window.alert("Reinforcement Learning Q-Table wiped successfully!")


def on_toggle_coach_click(event):
    global coach_enabled
    coach_enabled = not coach_enabled
    btn = document.getElementById("btn-toggle-coach")
    if btn:
        if coach_enabled:
            btn.innerHTML = "📴 Disable Coach Help"
            btn.className = "px-3.5 py-2 bg-rose-600/10 hover:bg-rose-600 hover:text-white text-rose-400 border border-rose-500/20 rounded-xl font-semibold text-xs transition duration-200 flex items-center gap-1.5 shadow-lg shadow-rose-600/5"
        else:
            btn.innerHTML = "💡 Enable Coach Help"
            btn.className = "px-3.5 py-2 bg-indigo-600/10 hover:bg-indigo-600 hover:text-white text-indigo-400 border border-indigo-500/20 rounded-xl font-semibold text-xs transition duration-200 flex items-center gap-1.5 shadow-lg shadow-indigo-600/5"
    generate_positional_coach_commentary()


def start_lobby_match(opponent_name, opponent_elo, player_color_str, time_control_seconds):
    global board, move_history, move_analyses, last_eval, game_over_saved, self_play_autoplay, mode, player_color, bot_elo, current_opponent_name, game_time_limit, selected_square, premove_obj, last_rendered_fen
    board = chess.Board()
    move_history = []
    move_analyses = []
    selected_square = None
    premove_obj = None
    last_rendered_fen = None
    last_eval = 0.0
    game_over_saved = False
    self_play_autoplay = False
    mode = "human"
    
    bot_elo = int(opponent_elo)
    current_opponent_name = opponent_name
    player_color = chess.WHITE if player_color_str == "white" else chess.BLACK
    game_time_limit = int(time_control_seconds)
    
    # Synchronize UI input values
    document.getElementById("select-mode").value = "human"
    document.getElementById("select-color").value = player_color_str
    document.getElementById("range-elo").value = str(bot_elo)
    document.getElementById("select-time-control").value = str(game_time_limit)
    on_elo_change(None)
    
    # Update HTML layouts
    document.getElementById("human-color-section").classList.remove("hidden")
    document.getElementById("self-play-section").classList.add("hidden")
    
    # Render board
    render_board()
    
    # Initialize clocks in JavaScript
    try:
        window.initClocks(game_time_limit)
    except Exception as e:
        print("Clock init error:", e)
        
    # Trigger first move if player is Black (since White bot goes first)
    if player_color == chess.BLACK:
        check_trigger_bot_move()


def declare_timeout(loser_color_str):
    global board, game_over_saved
    if game_over_saved:
        return
        
    result = "0-1" if loser_color_str == "w" else "1-0"
    outcome_str = "Black won on time" if loser_color_str == "w" else "White won on time"
    
    # Update status badge
    status_badge = document.getElementById("status-badge")
    status_badge.className = "px-4 py-2 rounded-xl border font-semibold flex items-center gap-2 text-sm bg-indigo-500/10 border-indigo-500/30 text-indigo-400"
    status_badge.innerHTML = f"🏆 Game Over! {result} ({outcome_str})"
    
    handle_game_over(result, outcome_str)


def on_time_control_change(event):
    global game_time_limit
    game_time_limit = int(document.getElementById("select-time-control").value)
    try:
        document.getElementById("lobby-time-control").value = str(game_time_limit)
    except Exception:
        pass
    on_reset_click(None)


# Expose these functions to JS window
window.start_lobby_match = create_proxy(start_lobby_match)
window.declare_timeout = create_proxy(declare_timeout)
window.analyzeHistoricMatch = create_proxy(analyze_historic_match)
window.setViewIndex = create_proxy(set_view_index)
window.importPgnGame = create_proxy(import_pgn_game)
window.importFenGame = create_proxy(import_fen_game)
window.renderBoard = create_proxy(render_board)
window.copyHistoricPgn = create_proxy(copy_historic_pgn)


# --- Bootstrapping Event Listeners Setup ---

def setup_event_listeners():
    # Board-container clicks
    document.getElementById("board-container").addEventListener("click", create_proxy(on_board_click))
    document.getElementById("board-container").addEventListener("contextmenu", create_proxy(on_board_right_click))
    
    # Analysis navigation banner
    document.getElementById("btn-analysis-prev").addEventListener("click", create_proxy(on_analysis_prev_click))
    document.getElementById("btn-analysis-next").addEventListener("click", create_proxy(on_analysis_next_click))
    document.getElementById("btn-analysis-live").addEventListener("click", create_proxy(on_analysis_live_click))
    
    # Board-under navigation buttons
    document.getElementById("btn-board-first").addEventListener("click", create_proxy(on_analysis_first_click))
    document.getElementById("btn-board-prev").addEventListener("click", create_proxy(on_analysis_prev_click))
    document.getElementById("btn-board-next").addEventListener("click", create_proxy(on_analysis_next_click))
    document.getElementById("btn-board-last").addEventListener("click", create_proxy(on_analysis_last_click))
    document.getElementById("btn-board-live").addEventListener("click", create_proxy(on_analysis_live_click))
    
    # Dropdowns & Forms
    document.getElementById("select-from").addEventListener("change", create_proxy(on_from_change))
    document.getElementById("btn-push-move").addEventListener("click", create_proxy(on_push_move_click))
    document.getElementById("btn-quick-move").addEventListener("click", create_proxy(on_quick_move_click))
    
    # Left controls
    document.getElementById("btn-draw").addEventListener("click", create_proxy(on_draw_click))
    document.getElementById("btn-resign").addEventListener("click", create_proxy(on_resign_click))
    document.getElementById("btn-undo").addEventListener("click", create_proxy(on_undo_click))
    document.getElementById("btn-reset").addEventListener("click", create_proxy(on_reset_click))
    
    # Setup controls
    document.getElementById("select-mode").addEventListener("change", create_proxy(on_mode_change))
    document.getElementById("select-color").addEventListener("change", create_proxy(on_color_change))
    document.getElementById("select-time-control").addEventListener("change", create_proxy(on_time_control_change))
    document.getElementById("range-elo").addEventListener("change", create_proxy(on_elo_change))
    document.getElementById("range-elo").addEventListener("input", create_proxy(on_elo_change))
    
    # Self-play automation controls
    document.getElementById("range-speed").addEventListener("input", create_proxy(on_speed_change))
    document.getElementById("btn-play-autoplay").addEventListener("click", create_proxy(on_autoplay_play))
    document.getElementById("btn-pause-autoplay").addEventListener("click", create_proxy(on_autoplay_pause))
    
    # RL Clear Weights Button
    document.getElementById("btn-clear-rl").addEventListener("click", create_proxy(on_clear_rl_click))
    
    # Toggle Coach Button
    document.getElementById("btn-toggle-coach").addEventListener("click", create_proxy(on_toggle_coach_click))


# --- Initialize UI ---
setup_event_listeners()
render_board()
update_rl_ui()
update_history_ui()

# Notify JavaScript that Python is fully ready to dismiss the loading screen
try:
    import js_helper
    js_helper.on_ready()
except Exception:
    pass
