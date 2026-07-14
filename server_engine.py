#!/usr/bin/env python3
import chess
import random
import time

# --- Chess Engine Constants & Position Evaluation Tables ---
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

def get_clean_fen(fen: str) -> str:
    return " ".join(fen.split()[:4])

def check_game_over(b: chess.Board) -> bool:
    return b.is_game_over(claim_draw=True)

# 50 Famous Chess Openings
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
            except Exception:
                break
    return book

OPENING_BOOK = populate_opening_book()

class SearchTimeout(Exception):
    pass

GARRY_TRANSPOSITION_TABLE = {}

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

        # 1. BEGINNER BETH
        if personality == "Beth":
            white_king_sq = board.king(chess.WHITE)
            black_king_sq = board.king(chess.BLACK)
            
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
                                score -= 45

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
                                score += 45

        # 2. GM GARRY
        elif personality in ["Garry", "FireStorm"]:
            white_king_sq = board.king(chess.WHITE)
            black_king_sq = board.king(chess.BLACK)

            if white_king_sq is not None and not endgame:
                wk_file = chess.square_file(white_king_sq)
                wk_rank = chess.square_rank(white_king_sq)
                if wk_file >= 5 and wk_rank == 0:
                    for f_shield in [5, 6, 7]:
                        shield_sq = chess.square(f_shield, 1)
                        p = board.piece_at(shield_sq)
                        if p and p.piece_type == chess.PAWN and p.color == chess.WHITE:
                            score += 15
                        else:
                            score -= 25
                elif wk_file <= 2 and wk_rank == 0:
                    for f_shield in [0, 1, 2]:
                        shield_sq = chess.square(f_shield, 1)
                        p = board.piece_at(shield_sq)
                        if p and p.piece_type == chess.PAWN and p.color == chess.WHITE:
                            score += 15
                        else:
                            score -= 25

            if black_king_sq is not None and not endgame:
                bk_file = chess.square_file(black_king_sq)
                bk_rank = chess.square_rank(black_king_sq)
                if bk_file >= 5 and bk_rank == 7:
                    for f_shield in [5, 6, 7]:
                        shield_sq = chess.square(f_shield, 6)
                        p = board.piece_at(shield_sq)
                        if p and p.piece_type == chess.PAWN and p.color == chess.BLACK:
                            score -= 15
                        else:
                            score += 25
                elif bk_file <= 2 and bk_rank == 7:
                    for f_shield in [0, 1, 2]:
                        shield_sq = chess.square(f_shield, 6)
                        p = board.piece_at(shield_sq)
                        if p and p.piece_type == chess.PAWN and p.color == chess.BLACK:
                            score -= 15
                        else:
                            score += 25

            for sq in chess.SQUARES:
                piece = board.piece_at(sq)
                if piece and piece.piece_type != chess.KING:
                    is_attacked = board.is_attacked_by(not piece.color, sq)
                    is_defended = len(board.attackers(piece.color, sq)) > 0
                    if is_attacked:
                        p_val = PIECE_VALUES.get(piece.piece_type, 100)
                        if not is_defended:
                            penalty = int(p_val * 0.4)
                            if piece.color == chess.WHITE:
                                score -= penalty
                            else:
                                score += penalty
                        else:
                            penalty = int(p_val * 0.1)
                            if piece.color == chess.WHITE:
                                score -= penalty
                            else:
                                score += penalty

            center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
            for cs in center_squares:
                white_ctrl = len(board.attackers(chess.WHITE, cs))
                black_ctrl = len(board.attackers(chess.BLACK, cs))
                score += (white_ctrl - black_ctrl) * 10

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
                                score -= 15

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
                                score += 15

        # 3. COACH NAKAMURA
        else:
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
                        prio += 1200
                    elif personality in ["Garry", "FireStorm"]:
                        prio += 300
                    else:
                        prio += 800
            except Exception:
                pass

            if personality in ["Garry", "FireStorm"]:
                if board.is_castling(move):
                    prio += 900
                from_sq = move.from_square
                if board.is_attacked_by(not board.turn, from_sq):
                    prio += 500
                    
            scored.append((move, prio))
            
        scored.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in scored]

    def quiescence_search(self, board: chess.Board, alpha: int, beta: int, is_maximizing: bool, depth_left: int = 3) -> int:
        self.nodes_visited += 1
        if self.personality == "FireStorm" and depth_left == 3:
            depth_left = 3

        if self.time_limit and self.start_time:
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
        t0 = time.time()
        self.nodes_visited = 0
        self.start_time = t0
        
        if self.personality == "FireStorm":
            best_score = 0
            best_pv = []
            
            for d in range(1, depth + 1):
                try:
                    score, pv = self.minimax(board, d, alpha, beta, is_maximizing)
                    best_score = score
                    if pv:
                        best_pv = pv
                except SearchTimeout:
                    break
            
            if not best_pv:
                try:
                    score, pv = self.minimax(board, 1, alpha, beta, is_maximizing)
                    if pv:
                        best_pv = pv
                        best_score = score
                except SearchTimeout:
                    pass
            res = best_score, best_pv
        else:
            res = self.minimax(board, depth, alpha, beta, is_maximizing)
            
        return res

    def minimax(self, board: chess.Board, depth: int, alpha: int, beta: int, is_maximizing: bool) -> tuple[int, list[chess.Move]]:
        self.nodes_visited += 1
        if self.start_time is None:
            self.start_time = time.time()

        if self.time_limit and self.start_time:
            if time.time() - self.start_time >= self.time_limit:
                raise SearchTimeout()

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

def get_bot_move(board: chess.Board, elo: int, q_table: dict) -> tuple[chess.Move | None, float]:
    depth = 3
    use_quiescence = True
    randomize_chance = 0.0
    use_opening_book = True

    if elo <= 1000:
        depth = 1
        use_quiescence = False
        randomize_chance = 0.35
        use_opening_book = random.random() < 0.5
    elif elo <= 1600:
        depth = 3
        randomize_chance = 0.01
        use_quiescence = True
        use_opening_book = True
    else:
        depth = 4
        use_quiescence = True
        randomize_chance = 0.0
        use_opening_book = True

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

    personality = "Nakamura"
    if elo <= 1000:
        personality = "Beth"
    elif elo >= 2400:
        personality = "FireStorm"
    elif elo >= 2000:
        personality = "Garry"

    if not best_move:
        time_limit = 2.5 if personality == "FireStorm" else (10.0 if elo >= 2000 else None)
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
            except Exception:
                ordered = engine.order_moves(board, legal)
                best_move = ordered[0]

    # Handle random blunder/inaccuracy emulation
    legal = list(board.legal_moves)
    if randomize_chance > 0 and random.random() < randomize_chance and len(legal) > 1:
        scored_legal = []
        engine = PurePythonChessEngine(q_table=q_table, personality=personality)
        is_maximizing = board.turn == chess.WHITE
        for m in legal:
            board.push(m)
            scored_legal.append((m, engine.evaluate_board(board)))
            board.pop()
        
        scored_legal.sort(key=lambda x: x[1], reverse=is_maximizing)
        idx = min(random.randint(1, 2), len(scored_legal) - 1)
        best_move = scored_legal[idx][0]

    if not best_move:
        best_move = random.choice(legal) if legal else None

    eval_score = 0.0
    if best_move:
        board.push(best_move)
        engine_eval = PurePythonChessEngine(q_table=q_table, personality=personality)
        eval_score = round(engine_eval.evaluate_board(board) / 100.0, 2)
        board.pop()

    return best_move, eval_score

def get_backend_bot_move(fen: str, elo: int, q_table: dict) -> tuple[chess.Move | None, float]:
    board = chess.Board(fen)
    return get_bot_move(board, elo, q_table)
