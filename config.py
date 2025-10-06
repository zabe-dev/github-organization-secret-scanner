import os

CONFIG = {
    'TH_GITHUB_TOKEN': os.getenv('TH_GITHUB_TOKEN', ''),
    'KF_GITHUB_TOKEN': os.getenv('KF_GITHUB_TOKEN', '')
}

class Colors:
    RED = ''
    GREEN = ''
    YELLOW = ''
    BLUE = ''
    PURPLE = ''
    CYAN = ''
    END = ''
    BOLD = ''
    DIM = '\033[2m'
