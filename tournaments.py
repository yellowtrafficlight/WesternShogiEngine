# imports
import torch
import yaml
import time
from model import Model
from utils.chess_gameplay import Agent, play_game

checkpoints = [0, 1000, 2000, 4000, 8000]
points = [0 for _ in range(len(checkpoints))]
total_points = [0 for _ in range(len(checkpoints))]
model_config = yaml.safe_load(open("model_config.yaml"))
models = []
for ckpt in checkpoints:
    model = Model(**model_config)
    checkpoint = torch.load(f"out/checkpoint_{ckpt}.pt", map_location=torch.device('cpu'))
    model.load_state_dict(checkpoint["model"])
    models.append(model)

while True:
    for model_0_idx in range(len(checkpoints)):
        for model_1_idx in range(len(checkpoints)):
            if model_0_idx != model_1_idx:
                agent0, agent1 = Agent(models[model_0_idx]), Agent(models[model_1_idx])
                gameplay_kwargs = {
                    "table": 1,
                    "agents": {'white': agent0, 'black': agent1},
                    "max_moves": 50,
                    "min_seconds_per_move": 0.0,
                    "verbose": True,
                    "poseval": True
                }
                print(f'White: ckpt-{checkpoints[model_0_idx]}')
                print(f'Black: ckpt-{checkpoints[model_1_idx]}')
                game_result = play_game(**gameplay_kwargs)
                points[model_0_idx] += (game_result['white']['points'] + 1)/2
                points[model_1_idx] += (game_result['black']['points'] + 1)/2
                total_points[model_0_idx] += 1
                total_points[model_1_idx] += 1

                print('Tournament Scoreboard')
                for ckpt, point, num_games in zip(checkpoints, points, total_points):
                    print(f'checkpoint_{ckpt}.pt: {round(point, 2)}/{num_games}')
