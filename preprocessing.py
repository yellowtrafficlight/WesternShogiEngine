import chess
import chess.pgn
import re
import numpy as np

ALPHA = 0.1

# input: LIST of pgn file paths
# output: LIST of TUPLES of positions with evaluations
def convert_pgn_to_fen(pgn_file_path):
    output = []
    pgn = open(pgn_file_path)
    game = chess.pgn.read_game(pgn)
    while game is not None:
        if not game.variations:
            continue
        node = game.variations[0]
        while node is not None:
            # print(f"Node: {node}")
            # print(f"Next move: " + node.move.__str__())
            b = node.board()
            fen = b.fen()
            if b.turn == chess.BLACK:
                fen = b.mirror().fen()
            fen = ' '.join(fen.split(' ')[:-2])
            # print(f"FEN: {fen}")

            if b.is_checkmate():
                # print("Checkmate!")
                eval = -ALPHA

            else:
                if not node.comment:
                    break
                # print(node.comment)
                score = node.comment.split(" ")[1][:-1]
                if "#" in score:
                    if '-' in score:
                        winning_color = chess.BLACK
                    else:
                        winning_color = chess.WHITE
                    moves_left = int(re.findall('\d+', score)[0])
                    if winning_color == b.turn:
                        eval = 1 + ALPHA / (moves_left + 1)
                    else:
                        eval = -ALPHA / (moves_left + 1)
                    # eval = (1 + ALPHA / (moves_left + 1)) * (2 * (winning_color == b.turn) - 1)
                    # print(f"Checkmate eval: {eval}")
                else:
                    eval = 1 / (1 + np.e ** (-0.00368208 * float(score) * 100))
                    # print(f"Position eval: {score} => {eval} winning probability")
                    if b.turn == chess.BLACK:
                        eval = 1 - eval
            


            # if b.turn == chess.WHITE:

            #     if b.is_checkmate():
            #         eval = int(b.outcome().winner)
            #         mate_score = -1
            #     else:
            #         score = 

            # else:

            
            # eval = 


            # if not node.comment:
            #     if node.variations:
            #         node = node.variations[0]
            #     else:
            #         node = None
            #     continue
            # b = node.board()

            # if b.is_checkmate():
            #     sc_board = node.board().fen()
            #     eval = b.turn
            #     mate_score = 1 / (int(re.findall('\d+', score)[0]) + 1) * (2 * b.turn - 1)
            #     output.append((sc_board, eval, mate_score))
            #     break
            # sc_board = b.fen()
            # # print(node.comment)
            # score = node.comment.split(" ")[1][:-1]
            # mate_score = 0
            # if "#" in score:
            #     eval = 1 - ("-" in score)
            #     mate_score = 1 / (int(re.findall('\d+', score)[0]) + 1) * ("-" in score)
            # else:
            #     eval = 1 / (1 + np.e ** (-0.00368208 * float(score) * 100))
            #     mate_score = 0


            # print((fen, eval))
            assert -ALPHA <= eval <= 1 + ALPHA
            output.append((fen, eval))
            # output.append((sc_board, eval, mate_score))
            # print(output[-1])
            if node.variations:
                node = node.variations[0]
            else:
                node = None
        game = chess.pgn.read_game(pgn)

    return output


