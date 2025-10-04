import os

CONFIG = {
    'TH_GITHUB_TOKEN': os.getenv('TH_GITHUB_TOKEN', ''),
    'KF_GITHUB_TOKEN': os.getenv('KF_GITHUB_TOKEN', '')
}

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'
