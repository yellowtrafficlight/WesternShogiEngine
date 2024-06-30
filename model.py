import torch
import torch.nn as nn
import chess
from typing import Tuple, List, Iterator

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

PIECE_TO_TOKEN = {
    '<PAD>': 0, 'P': 1, 'N': 2, 'B': 3, 'R': 4, 'Q': 5, 'K': 6,
    'p': 7, 'n': 8, 'b': 9, 'r': 10, 'q': 11, 'k': 12,
    '-': 13, 'a': 14, 'b': 15, 'c': 16, 'd': 17, 
    'e': 18, 'f': 19, 'g': 20, 'h': 21,
    '0': 22, '1': 23, '2': 24, '3': 25, '4': 26, '5': 27, '6': 28, '7': 29, '8': 30, '9': 31,
    ' ': 32, '/': 33, '.': 34
}

def encode(fen):
    tokens = []
    parts = fen.split()
    board = parts[0]
    
    # Encode the board part
    for char in board:
        if char.isdigit():
            tokens.extend([PIECE_TO_TOKEN['.']] * int(char))
        else:
            tokens.append(PIECE_TO_TOKEN[char])

    tokens.append(PIECE_TO_TOKEN[' '])
    # Encode the rest of the FEN
    for char in ' '.join(parts[1:]):
        tokens.append(PIECE_TO_TOKEN[char])
    
    return tokens

def pad_fens(fens):
    encoded_fens = [encode(fen) for fen in fens]
    
    # Find the maximum length of encoded FENs
    max_len = max(len(tokens) for tokens in encoded_fens)
    
    # Pad all encoded FENs to the maximum length
    padded_fens = [tokens + [PIECE_TO_TOKEN['<PAD>']] * (max_len - len(tokens)) for tokens in encoded_fens]
    
    return torch.tensor(padded_fens)

class Model(nn.Module):
    def __init__(self, vocab_size=35, d_model=256, n_head=16, num_layers=16, dim_feedforward=256, max_seq_length=100, num_classes=1, test_mode=True):
        super(Model, self).__init__()
        
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoding = nn.Parameter(torch.zeros(max_seq_length, d_model))
        
        transformer_layer = nn.TransformerEncoderLayer(d_model, n_head, dim_feedforward)
        self.transformer = nn.TransformerEncoder(transformer_layer, num_layers)
        
        self.fc = nn.Linear(d_model, num_classes)
        self.test_mode = test_mode
        
    def forward(self, x):
        if self.test_mode:
            x = pad_fens([convert_torch_to_fen(x[i, :]) for i in range(x.shape[0])])

        seq_length = x.size(1)
        
        x = self.embedding(x)
        x = x + self.pos_encoding[:seq_length, :]
        
        x = x.permute(1, 0, 2)
        x = self.transformer(x)
        
        x = x[-1, :, :]
        x = self.fc(x)
        if self.test_mode:
            return x.reshape(x.shape[0],)
        else:
            return x[:, 0]
