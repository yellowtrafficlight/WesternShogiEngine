import chess
import chess.pgn
import re
import numpy as np
import torch
from torch.utils.data import IterableDataset, DataLoader
from typing import Tuple, List, Iterator
import random


PIECE_TO_TOKEN = {
    '<PAD>': 0, 'P': 1, 'N': 2, 'B': 3, 'R': 4, 'Q': 5, 'K': 6,
    'p': 7, 'n': 8, 'b': 9, 'r': 10, 'q': 11, 'k': 12,
    '-': 13, 'a': 14, 'b': 15, 'c': 16, 'd': 17, 
    'e': 18, 'f': 19, 'g': 20, 'h': 21,
    '0': 22, '1': 23, '2': 24, '3': 25, '4': 26, '5': 27, '6': 28, '7': 29, '8': 30, '9': 31,
    ' ': 32, '/': 33, '.': 34
}


TOKEN_TO_PIECE = {v: k for k, v in PIECE_TO_TOKEN.items()}

class ChessPositionDataset(IterableDataset):
    def __init__(self, pgn_file_path: str = 'sample.pgn', alpha: float = 0.1, chunk_size: int = 10000):
        self.pgn_file_path = pgn_file_path
        self.alpha = alpha
        self.chunk_size = chunk_size
        self.current_chunk = []
        self.pgn = open(self.pgn_file_path)
        self.game = chess.pgn.read_game(self.pgn)

    def __iter__(self) -> Iterator[Tuple[str, float]]:
        return self

    def __next__(self) -> Tuple[str, float]:
        if not self.current_chunk:
            self.load_chunk()
        
        if not self.current_chunk:
            raise StopIteration

        return self.current_chunk.pop()

    def load_chunk(self):
        self.current_chunk = []
        while len(self.current_chunk) < self.chunk_size:
            if self.game is None:
                break
            self.current_chunk.extend(self.process_game(self.game))
            self.game = chess.pgn.read_game(self.pgn)
        
        random.shuffle(self.current_chunk)

    def process_game(self, game) -> List[Tuple[str, float]]:
        positions = []
        node = game.variations[0] if game.variations else None
        while node is not None:
            b = node.board()
            ### START FEN SECTION
            fen = b.fen()
            if b.turn == chess.BLACK:
                fen = fen.swapcase()
            temp = fen.split(' ')[:-2]
            del temp[-3]
            if temp[-1] != "-" and b.turn == chess.BLACK:
                temp[-1] = temp[-1][:1].swapcase() + str(6)
            fen = ' '.join(temp)
            ### END FEN SECTION
            
            if b.is_checkmate():
                eval = -self.alpha
            elif not node.comment:
                node = node.variations[0] if node.variations else None
                continue
            else:
                score = node.comment.split(" ")[1][:-1]
                if "#" in score:
                    winning_color = chess.BLACK if '-' in score else chess.WHITE
                    moves_left = int(re.findall(r'\d+', score)[0])
                    eval = (1 + self.alpha / (moves_left + 1)) if winning_color == b.turn else (-self.alpha / (moves_left + 1))
                else:
                    eval = 1 / (1 + np.exp(-0.00368208 * float(score) * 100))
                    if b.turn == chess.BLACK:
                        eval = 1 - eval
            
            assert -self.alpha <= eval <= 1 + self.alpha
            positions.append((fen, eval))
            
            node = node.variations[0] if node.variations else None
        
        return positions

    def __del__(self):
        self.pgn.close()

def encode(fen: str) -> List[int]:
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

def decode(tokens: List[int]) -> str:
    return ''.join(TOKEN_TO_PIECE[token] for token in tokens if token != PIECE_TO_TOKEN['<PAD>'])

def collate_fn(batch: List[Tuple[str, float]]) -> Tuple[torch.Tensor, torch.Tensor]:
    fens, evals = zip(*batch)
    encoded_fens = [encode(fen) for fen in fens]
    
    # Find the maximum length of encoded FENs
    max_len = max(len(tokens) for tokens in encoded_fens)
    
    # Pad all encoded FENs to the maximum length
    padded_fens = [tokens + [PIECE_TO_TOKEN['<PAD>']] * (max_len - len(tokens)) for tokens in encoded_fens]
    
    return torch.tensor(padded_fens), torch.tensor(evals)

def get_chess_position_dataloader(pgn_file_path: str = 'sample.pgn', batch_size: int = 32, alpha: float = 0.1, chunk_size: int = 10000) -> DataLoader:
    dataset = ChessPositionDataset(pgn_file_path, alpha=alpha, chunk_size=chunk_size)
    return DataLoader(dataset, batch_size=batch_size, collate_fn=collate_fn)

# Example usage:
# dataloader = get_chess_position_dataloader('sample.pgn', batch_size=64, alpha=0.1, chunk_size=1000)
# for tokens, evaluations in dataloader:
#     # Your training loop here
#     pass

# Example of encode and decode usage:
# original_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
# encoded = encode(original_fen)
# decoded = decode(encoded)
# Note: The decoded string will now be different from the original FEN due to the simplified decoding
