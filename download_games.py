import requests
from datetime import datetime, timedelta
import os, subprocess, tempfile
from tqdm import tqdm

def process_lichess_pgns(start_date, output_file, file_size_limit=80*1024*1024*1024):
    base_url = "https://database.lichess.org/standard/lichess_db_standard_rated_{}.pgn.zst"
    current_date = datetime.strptime(start_date, "%Y-%m")
    end_date = datetime.now().replace(day=1)  # First day of current month
    processed_games = 0
    
    # Estimating games from 2021 onwards (adjust as needed)
    total_expected_games = 3_000_000_000 * 0.06  # Estimate for games from 2021, 6% with evals
    
    with tqdm(total=total_expected_games, unit="game") as pbar:
        while current_date <= end_date:
            url = base_url.format(current_date.strftime("%Y-%m"))
            print(f"\nProcessing file for date: {current_date.strftime('%Y-%m')}")
            
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
                    
                    with open(decompressed_file, 'r') as f, open(output_file, 'a') as out_f:
                        pgn = []
                        for line in f:
                            if line.strip(): pgn.append(line)
                            elif pgn and "[%eval" in ''.join(pgn):
                                out_f.write(''.join(pgn) + "\n\n")
                                processed_games += 1
                                pbar.update(1)
                                pgn = []
                            else: pgn = []
                else:
                    print(f"Failed to download {url}, status code: {response.status_code}")
            
            current_size = os.path.getsize(output_file)
            print(f"Current output file size: {current_size} bytes")
            print(f"Total processed games so far: {processed_games}")
            
            if current_size >= file_size_limit:
                print(f"File size limit reached: {file_size_limit} bytes")
                break

            current_date += timedelta(days=32)
            current_date = current_date.replace(day=1)

    print(f"\nFinal number of processed games: {processed_games}")
    print(f"Final output file size: {os.path.getsize(output_file)} bytes")

if __name__ == "__main__":
    #process_lichess_pgns("2016-01", "lichess_games_with_evals_from_2016.pgn", 80*1024*1024*1024)
    process_lichess_pgns("2013-01", "sample.pgn", 1*1024*1024*1024)
