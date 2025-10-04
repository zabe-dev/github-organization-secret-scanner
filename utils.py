import json
import os
import sys
from datetime import datetime

from config import Colors


def log_error(message):
    with open('ghoss/errorlogs.txt', 'a', encoding='utf-8') as f:
        f.write(f'[{datetime.now().isoformat()}] {message}\n')

def save_results_to_files(th_secrets, kf_secrets, combined_results, th_output_filename, kf_output_filename, combined_output_filename):
    try:
        os.makedirs(os.path.dirname(th_output_filename), exist_ok=True)
        os.makedirs(os.path.dirname(kf_output_filename), exist_ok=True)
        os.makedirs(os.path.dirname(combined_output_filename), exist_ok=True)
        with open(th_output_filename, 'w', encoding='utf-8') as f:
            json.dump(th_secrets, f, indent=2, ensure_ascii=False)
        with open(kf_output_filename, 'w', encoding='utf-8') as f:
            json.dump(kf_secrets, f, indent=2, ensure_ascii=False)
        with open(combined_output_filename, 'w', encoding='utf-8') as f:
            json.dump(combined_results, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        log_error(f'Error saving results: {str(e)}')
        print(f'[{Colors.RED}!{Colors.END}] Failed to save results')
        return False

def cleanup_temp_files(temp_files):
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception as e:
                log_error(f'Failed to delete temporary file {temp_file}: {str(e)}')
                print(f'[{Colors.RED}!{Colors.END}] Failed to delete temporary file')

def signal_handler(sig, frame, temp_files):
    print(f'\n[{Colors.RED}*{Colors.END}] Script interrupted, cleaning up temporary files...')
    cleanup_temp_files(temp_files)
    sys.exit(1)
