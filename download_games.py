import requests
from datetime import datetime, timedelta
import os
import subprocess
import tempfile
from tqdm import tqdm

def process_lichess_pgns(start_date, output_dir, game_limit=230000, single_output=None):
    base_url = "https://database.lichess.org/standard/lichess_db_standard_rated_{}.pgn.zst"
    current_date = datetime.strptime(start_date, "%Y-%m")
    end_date = datetime.now().replace(day=1)  # First day of current month
    processed_games = 0
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with tqdm(total=game_limit, unit="game") as pbar:
        while current_date <= end_date and processed_games < game_limit:
            month_str = current_date.strftime("%Y-%m")
            url = base_url.format(month_str)
            print(f"\nProcessing file for date: {month_str}")
            if single_output is not None:
                output_file = single_output
            else:
                output_file = os.path.join(output_dir, f"lichess_{month_str}.pgn")
            
            with tempfile.TemporaryDirectory() as tmpdir:
                compressed_file = os.path.join(tmpdir, 'compressed.pgn.zst')
                decompressed_file = os.path.join(tmpdir, 'decompressed.pgn')
                
                response = requests.get(url, stream=True)
                if response.ok:
                    with open(compressed_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"Downloaded file size: {os.path.getsize(compressed_file)} bytes")
                    
                    try:
                        subprocess.run(['zstd', '-d', '-q', compressed_file, '-o', decompressed_file], check=True)
                        print(f"Decompressed file size: {os.path.getsize(decompressed_file)} bytes")
                    except subprocess.CalledProcessError as e:
                        print(f"Error decompressing file: {e}")
                        print("Attempting manual decompression for more info:")
                        result = subprocess.run(['zstd', '-d', '-v', compressed_file, '-o', decompressed_file], capture_output=True, text=True)
                        print(f"STDOUT: {result.stdout}")
                        print(f"STDERR: {result.stderr}")
                        current_date += timedelta(days=32)
                        current_date = current_date.replace(day=1)
                        continue
                    
                    with open(decompressed_file, 'r') as f, open(output_file, 'w') as out_f:
                        pgn = []
                        for line in f:
                            if line.strip(): pgn.append(line)
                            elif pgn and "[%eval" in ''.join(pgn):
                                out_f.write(''.join(pgn) + "\n\n")
                                processed_games += 1
                                pbar.update(1)
                                if processed_games >= game_limit:
                                    break
                                pgn = []
                            else: pgn = []
                        
                        if processed_games >= game_limit:
                            break
                else:
                    print(f"Failed to download {url}, status code: {response.status_code}")
            
            print(f"Total processed games so far: {processed_games}")
            print(f"Output file for {month_str}: {output_file}")
            print(f"File size: {os.path.getsize(output_file)} bytes")
            
            current_date += timedelta(days=32)
            current_date = current_date.replace(day=1)
    
    print(f"\nFinal number of processed games: {processed_games}")

if __name__ == "__main__":
    process_lichess_pgns('2013-01', output_dir=None, game_limit=3_000_000, single_output='chinchilla_optimal.pgn')
