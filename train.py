import os
import time
import math
import torch
import torch.nn as nn
import yaml

from torch.nn import functional as F

from model import *
from dataloader import get_chess_position_dataloader, PIECE_TO_TOKEN

with open('model_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

out_dir = 'out'
log_interval = 1
save_interval = 1000
learning_rate = 1e-5
max_iters = float('inf')
weight_decay=0.0
beta1 = 0.9
beta2 = 0.95
grad_clip = 1.0
batch_size = 1024
device = 'cuda' 
dtype = 'float32'

model_args = dict(
    vocab_size=config['vocab_size'],
    d_model=config['d_model'],
    n_head=config['n_head'],
    num_layers=config['num_layers'],
    dim_feedforward=config['dim_feedforward'],
    max_seq_length=config['max_seq_length'],
    num_classes=config['num_classes'],
    test_mode=False
)

model = Model(**model_args).to(device)

total_params = sum(p.numel() for p in model.parameters())
print(f"Total number of parameters: {total_params:,}")

optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, betas=(beta1, beta2), weight_decay=weight_decay)

criterion = nn.MSELoss()

dataloader = get_chess_position_dataloader('chinchilla_optimal.pgn', batch_size=batch_size, alpha=0.1, chunk_size=10000)

iter_num = 0

def save_checkpoint(filename):
    checkpoint = {
        'model': model.state_dict(),
        'optimizer': optimizer.state_dict(),
        'model_args': model_args,
        'iter_num': iter_num,
    }
    torch.save(checkpoint, filename)
    print(f"Checkpoint saved to {filename}")


while True:
    model.train()
    total_loss = 0
    for tokens, scores in dataloader:
        tokens, scores = tokens.to(device), scores.to(device).float().unsqueeze(1)
        scores -= scores.mean()
        scores /= scores.std()

        for param_group in optimizer.param_groups:
            param_group['lr'] = learning_rate
        
        logits = model(tokens)
        loss = criterion(logits, scores)
        total_loss += loss

        optimizer.zero_grad()
        loss.backward()
        if grad_clip != 0.0:
            nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
        optimizer.step()
        
        if iter_num % log_interval == 0:
            print(f"iter {iter_num}: loss {loss.item():.4f}")

        if iter_num % save_interval == 0:
            save_checkpoint(os.path.join(out_dir, f'checkpoint_{iter_num}.pt'))
            print(f"iter {iter_num}: Total Loss {total_loss.item():.4f}")
            total_loss = 0


        iter_num += 1
        if iter_num >= max_iters:
            break
    
    if iter_num >= max_iters:
        break
