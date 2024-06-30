import chess
import chess.pgn
import re
import numpy as np
import torch

ALPHA = 0.1

PIECE_MAP = {1: "P", 2: "P", 3: "R", 4: "R", 5: "N", 6: "B", 7: "B", 8: "Q", 9: "K", 10: "K",
             11: "p", 12: "p", 13: "r", 14: "r", 15: "n", 16: "b", 17: "b", 18: "q", 19: "k", 20: "k"}

# input: 8x8 Torch tensor
# output: FEN string
def convert_torch_to_fen(tensor):
    board = tensor.tolist()
    fen = ""

    en_passant_str = "-"
    empty_count = 0
    for row in range(8):
        for col in range(8):
            if board[row][col] == 0:
                empty_count += 1
                if col == 7:
                    fen += str(empty_count)
                    empty_count = 0
            else:
                if empty_count > 0:
                    fen += str(empty_count)
                    empty_count = 0
                fen += PIECE_MAP[board[row][col]]
            if board[row][col] == 12:
                if col > 0 and board[row][col - 1] == 1:
                    en_passant_str = chr(ord("a") + col) + "6"
                elif col < 7 and board[row][col + 1] == 1:
                    en_passant_str = chr(ord("a") + col) + "6"
        if row != 7:
            fen += "/"
        else:
            fen += " "
    
    castling_is_legal = False
    if board[7][3] == 9:
        # checking if "black" can castle
        if board[7][0] == 3:
            castling_is_legal = True
            fen += "K"
        if board[7][7] == 3:
            castling_is_legal = True
            fen += "Q"

    if board[7][4] == 9:
        # checking if white can castle
        if board[7][7] == 3:
            castling_is_legal = True
            fen += "K"
        if board[7][0] == 3:
            castling_is_legal = True
            fen += "Q"
    
    if board[0][3] == 9:
        # checking if "white" can castle
        if board[0][0] == 3:
            castling_is_legal = True
            fen += "k"
        if board[0][7] == 3:
            castling_is_legal = True
            fen += "q"

    if board[0][3] == 9:
        # checking if black can castle
        if board[0][7] == 3:
            castling_is_legal = True
            fen += "k"
        if board[0][0] == 3:
            castling_is_legal = True
            fen += "q"
    
    if not castling_is_legal:
        fen += "-"

    fen += " "
    fen += en_passant_str
    return fen

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
                fen = fen.swapcase()
            # fen = ' '.join(fen.split(' ')[:-2])
            temp = fen.split(' ')[:-2]
            del temp[-3]
            if temp[-1] != "-" and b.turn == chess.BLACK:
                temp[-1] = temp[-1][:1].swapcase() + str(6)
                # print(' '.join(temp))
            fen = ' '.join(temp)
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


