import chess
import chess.pgn
import re
import numpy as np

PIECE_ENCODING = {"P": 1, "R": 4, "N": 5, "B": 6, "Q": 8, "K": 10,
                  "p": 11, "r": 14, "n": 15, "b": 16, "q": 18, "k": 20}

# input: LIST of pgn file paths
# output: LIST of TUPLES of positions with evaluations
def convert_pgn_to_SC(pgn_file_paths):
    output = []
    for f in pgn_file_paths:
        pgn = open(f)
        game = chess.pgn.read_game(pgn)
        while game is not None:
            node = game.variations[0]
            while node is not None:
                # print(f"Node: {node}")
                # print(f"Next move: " + node.move.__str__())
                if not node.comment:
                    if node.variations:
                        node = node.variations[0]
                    else:
                        node = None
                    continue
                b = node.board()
                if b.is_checkmate():
                    sc_board = node.board().fen()
                    eval = 100 * chess.WHITE
                    mate_score = 1 / (int(re.findall('\d+', score)[0]) + 1) * (2 * chess.WHITE - 1)
                    output.append((sc_board, eval, mate_score))
                    break
                sc_board = b.fen()
                # print(node.comment)
                score = node.comment.split(" ")[1][:-1]
                mate_score = 0
                if "#" in score:
                    eval = 100 - 100 * ("-" in score)
                    mate_score = 1 / (int(re.findall('\d+', score)[0]) + 1) * ("-" in score)
                else:
                    eval = 1 / (1 + np.e ** (-0.00368208 * float(score) * 100))
                    mate_score = 0
                output.append((sc_board, eval, mate_score))
                # print(output[-1])
                if node.variations:
                    node = node.variations[0]
                else:
                    node = None
            game = chess.pgn.read_game(pgn)

    return output


