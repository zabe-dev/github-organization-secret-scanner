# GHOSS - GitHub Organization Secret Scanner

A Python tool for scanning GitHub organizations to detect exposed secrets using TruffleHog and Kingfisher.

## Prerequisites

**Required Tools:**

-   Python 3.7+ with `requests` library
-   TruffleHog - [https://github.com/trufflesecurity/trufflehog](https://github.com/trufflesecurity/trufflehog)
-   Kingfisher - [https://github.com/mongodb/kingfisher](https://github.com/mongodb/kingfisher)

**GitHub Tokens (recommended):**

```bash
export TH_GITHUB_TOKEN="your_token"
export KF_GITHUB_TOKEN="your_token"
```

## Installation

1. Ensure all dependencies are installed
2. Make executable: `chmod +x main.py`

## Usage

**Single organization:**

```bash
./main.py -t "organization-name"
```

**Multiple organizations:**

```bash
./main.py -l organizations.txt
```

## Output

Results are saved in `ghoss/output/`:

-   `trufflehog_<id>.json` - TruffleHog findings
-   `kingfisher_<id>.json` - Kingfisher findings
-   `scan_results_<id>.json` - Combined results with statistics

## How It Works

1. Searches GitHub API for matching organizations
2. Interactive selection with arrow keys (5s timeout)
3. Runs both TruffleHog and Kingfisher scans
4. Combines results and generates reports
5. Automatic cleanup of temporary files

## Project Structure

```
config.py     # Configuration and colors
utils.py      # Utility functions
ui.py         # Interactive UI
scanner.py    # Scanning logic
main.py       # Entry point
```

## Notes

-   Scans can take up to 3 hours per organization
-   Errors logged to `ghoss/errorlogs.txt`
-   Use Ctrl+C to interrupt and cleanup

## Disclaimer

Use responsibly. Only scan organizations you have permission to audit.
