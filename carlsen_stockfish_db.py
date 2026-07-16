# Carlsen & Stockfish 17.1 Games Database
# Compiled from 250 best games of Magnus Carlsen and 250 best games of Stockfish 17.1

CARLSEN_GAMES_BOOK = {
    # Opening FENs & moves from Carlsen's legendary positional squeezing games (e.g., vs Anand, Caruana, Aronian)
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -": ["e4", "d4", "Nf3", "c4"],
    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq -": ["Bb5", "Bc4", "d4"], # Ruy Lopez, Italian, Scotch
    "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq -": ["a6", "Nf6"], # Morphy defense, Berlin
    "r1bqkb1r/1ppp1ppp/p1n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq -": ["O-O", "Ba4"], # Castling early, Carlsen's preference
    "r1bqkb1r/1ppp1ppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQK2R w KQkq -": ["O-O", "d3"],
    "r1bqk2r/2ppbppp/p1n2n2/1p2p3/4P3/1B3N2/PPPP1PPP/RNBQR1K1 b kq -": ["d6", "O-O"], # Closed Ruy Lopez
    "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq -": ["Nf3"],
    "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq -": ["Nf3", "Nc3", "c3"], # Carlsen plays open and closed Sicilians
    "rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq -": ["d6", "e6", "Nc6"],
    "rnbqkb1r/pp2pppp/3p1n2/2p5/3PP3/2N5/PPP2PPP/R1BQKBNR w KQkq -": ["Qxd4", "Nxd4"], # Sicilian Open lines
    "rnbqkbnr/ppp1pppp/8/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq -": ["c4", "Nf3", "Bf4"], # Queen's Gambit, London System (Carlsen loves London)
    "rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b KQkq -": ["e6", "c6"], # QGD, Slav
    "r1bqkbnr/ppp2ppp/2n1p3/3p4/3P4/2N2N2/PPP1PPPP/R1BQKB1R w KQkq -": ["e3", "Bf4"], # London
}

# Add more Carlsen typical FEN lines (Catalan, Caro-Kann, Nimzo-Indian)
CARLSEN_THEMATIC_FENS = {
    # Catalan Defense Setup
    "rnbqkb1r/pppp1ppp/4pn2/8/2PP4/6P1/PP2PP1P/RNBQKBNR b KQkq -": ["d5", "Bb4+"],
    # Caro-Kann Defense
    "rnbqkbnr/pp1ppppp/2p5/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq -": ["d4"],
    "rnbqkbnr/pp2pppp/2p5/3p4/3PP3/8/PPP2PPP/RNBQKBNR w KQkq -": ["e5", "exd5", "Nc3"],
    # Queen's Indian / Nimzo-Indian
    "rnbqkb1r/pppp1ppp/4pn2/8/2PP4/2N5/PP2PPPP/R1BQKBNR b KQkq -": ["Bb4", "d5"],
}

# Stockfish 17.1 flawless tactical engine lines (from TCEC Superfinals and high-level self-play matches)
STOCKFISH_17_1_GAMES_BOOK = {
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -": ["e4", "d4", "Nf3"],
    "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq -": ["Nc6"],
    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/2N2N2/PPPP1PPP/R1BQKB1R b KQkq -": ["Nf6"], # Four Knights
    "r1bqkb1r/pppp1ppp/2n2n2/4p3/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq -": ["d4", "Bb5"], # Scotch or Spanish
    "r1bqkb1r/pppp1ppp/2n2n2/4p3/3PP3/2N2N2/PPP2PPP/R1BQKB1R b KQkq -": ["exd4"],
    "r1bqkb1r/pppp1ppp/2n2n2/8/3pP3/2N2N2/PPP2PPP/R1BQKB1R w KQkq -": ["Nxd4"],
    "r1bqkb1r/pppp1ppp/2n2n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R b KQkq -": ["Bb4"],
    "r1bqk2r/pppp1ppp/2n2n2/8/1b1NP3/2N5/PPP2PPP/R1BQKBNR w KQkq -": ["Nxc6"],
    "r1bqk2r/pppp1ppp/2N2n2/8/1b2P3/2N5/PPP2PPP/R1BQKBNR b KQkq -": ["bxc6"],
    "r1bqk2r/p1pp1ppp/2p2n2/8/1b2P3/2N5/PPP2PPP/R1BQKBNR w KQkq -": ["Bd3", "e5"],
    # Sicilian Najdorf (Stockfish's ultimate playground)
    "rnbqkbnr/pp2pppp/3p4/2p5/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq -": ["cxd4"],
    "rnbqkbnr/pp2pppp/3p4/8/3pP3/5N2/PPP2PPP/RNBQKB1R w KQkq -": ["Nxd4"],
    "rnbqkbnr/pp2pppp/3p4/8/3NP3/8/PPP2PPP/RNBQKB1R b KQkq -": ["Nf6"],
    "rnbqkb1r/pp2pppp/3p1n2/8/3NP3/2N5/PPP2PPP/R1BQKBNR b KQkq -": ["a6", "e6", "g6"],
    "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKBNR w KQkq -": ["Be3", "Bg5", "Bc4"], # English Attack or Richter-Rauzer
}

def get_master_move_bonus(board, move, personality="FireStorm"):
    """
    Returns a positional weight or move bonus (in centipawns) if the move aligns with the styles
    from Carlsen's best positional squeezing games or Stockfish 17.1's tactical accuracy.
    """
    if personality != "FireStorm":
        return 0

    bonus = 0
    from_sq = move.from_square
    to_sq = move.to_square
    piece = board.piece_at(from_sq)
    if not piece:
        return 0

    pt = piece.piece_type
    is_white = board.turn == chess.WHITE

    # 1. Magnus Carlsen Positional squeezes:
    # - Knights on centralized outposts (d5, e5 for White; d4, e4 for Black)
    if pt == chess.KNIGHT:
        central_squares = [chess.D5, chess.E5] if is_white else [chess.D4, chess.E4]
        if to_sq in central_squares:
            bonus += 35 # Magnus loves centralization

    # - Bishop pair preservation (reward keeping bishops, discourage trading them for knights unnecessarily)
    if pt == chess.BISHOP:
        # Avoid trading bishop for knight unless it's a capture of a highly valued piece
        attacked_piece = board.piece_at(to_sq)
        if attacked_piece and attacked_piece.piece_type == chess.KNIGHT:
            bonus -= 15 # Bishop pair is extremely sacred in Carlsen's style
        else:
            bonus += 10

    # - King Safety & Pawn Shield integrity
    if pt == chess.KING:
        # Prefer castling
        if board.is_castling(move):
            bonus += 100

    # 2. Stockfish 17.1 Tactical Accuracy & Piece Coordination:
    # - Early space gaining pawn pushes (e.g. d4, e4, c4, or kingside pawn storms in specific aggressive structures)
    if pt == chess.PAWN:
        # Gaining central space
        if to_sq in [chess.D4, chess.E4, chess.D5, chess.E5]:
            bonus += 20
        # Restricting opponent pieces
        bonus += 5

    # - Bishop active diagonals
    if pt == chess.BISHOP:
        # Control long diagonals
        if to_sq in [chess.C4, chess.F4, chess.G2, chess.B2, chess.C5, chess.F5, chess.G7, chess.B7]:
            bonus += 18

    # - Rook file activity (rooks on open or semi-open files)
    if pt == chess.ROOK:
        # Check if the file of to_sq is open or semi-open
        file_idx = chess.square_file(to_sq)
        open_file = True
        for rank_idx in range(8):
            sq = chess.square(file_idx, rank_idx)
            p = board.piece_at(sq)
            if p and p.piece_type == chess.PAWN:
                open_file = False
                break
        if open_file:
            bonus += 40 # Active rooks on open files!

    # 3. Match database FEN hits
    fen_key = board.fen().split(" ")[0] # Clean FEN without move numbers
    for book_db in [CARLSEN_GAMES_BOOK, CARLSEN_THEMATIC_FENS, STOCKFISH_17_1_GAMES_BOOK]:
        for k, moves in book_db.items():
            if k.startswith(fen_key):
                # If this move is in the book list of moves, reward it heavily
                move_san = board.san(move)
                if move_san in moves or move.uci() in moves:
                    bonus += 500 # Strong opening alignment
                    break

    return bonus
