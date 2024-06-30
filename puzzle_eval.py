import pandas as pd
import random
import chess

PUZZLES = pd.read_csv("puzzles.csv")
eval_func = lambda fen: random.random()
SAMPLE_PUZZLE = ['4r3/1k6/pp3r2/1b2P2p/3R1p2/P1R2P2/1P4PP/6K1 w - - 0 35', 'e5f6', 1.33, eval_func]

def eval_mate(fen, sol, true_eval, eval_func):
    eval_error = abs(eval_func(fen) - true_eval)
    b = chess.Board(fen)
    legal_moves = b.legal_moves
    max_eval = 0
    best_move = None
    for m in legal_moves:
        diagram = b.copy()
        diagram.push(m)
        v = eval_func(diagram)
        if v > max_eval:
            max_eval = v
            best_move = m
    return eval_error, best_move == sol

# eval_mate(*SAMPLE_PUZZLE)