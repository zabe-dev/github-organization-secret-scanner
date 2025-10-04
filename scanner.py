import json
import os
import subprocess
import time

import requests

from config import Colors
from utils import log_error


class GitHubScanner:
    def __init__(self, github_token=None, kf_github_token=None):
        self.github_token = github_token
        self.kf_github_token = kf_github_token
        self.headers = {'Accept': 'application/vnd.github.v3+json'}
        if github_token:
            self.headers['Authorization'] = f'token {github_token}'

    def search_orgs(self, organization):
        url = f'https://api.github.com/search/users?q={organization.replace(" ", "+")}+type:org'
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 403:
                print(f'[{Colors.YELLOW}!{Colors.END}] Rate limit hit, waiting 60 seconds...')
                time.sleep(60)
                response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                return [item['login'] for item in response.json().get('items', []) if item.get('type') == 'Organization']
            return []
        except Exception as e:
            log_error(f'Error searching organizations: {str(e)}')
            return []

    def find_best_matching_org(self, organization, orgs):
        if not orgs:
            return None
        organization_lower = organization.lower().replace(' ', '').replace('-', '').replace('_', '')
        for org in orgs:
            org_lower = org.lower().replace('-', '').replace('_', '')
            if organization_lower in org_lower or org_lower in organization_lower:
                return org
        return None

    def parse_trufflehog_output(self, output):
        secrets = []
        if not output or not output.strip():
            return secrets
        for line in output.strip().split('\n'):
            if line.strip():
                try:
                    secrets.append(json.loads(line.strip()))
                except json.JSONDecodeError as e:
                    log_error(f'Invalid JSON in TruffleHog output: {line[:100]}... Error: {str(e)}')
                    continue
        return secrets

    def run_trufflehog(self, org, output_file):
        abs_output_file = os.path.abspath(output_file)
        os.makedirs(os.path.dirname(abs_output_file), exist_ok=True)
        cmd = [
            "trufflehog", "github",
            "--results=verified",
            "--include-members",
            "--include-forks",
            f"--org={org}",
            "-j"
        ]

        if self.github_token:
            cmd.append(f'--token={self.github_token}')
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10800
            )
            if result.returncode != 0:
                log_error(f'TruffleHog failed with return code {result.returncode}: {result.stderr.strip() or result.stdout.strip() or "Unknown error"}')
                print(f'[{Colors.RED}!{Colors.END}] TruffleHog completed scan with errors')
                return False, []
            with open(abs_output_file, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            with open(abs_output_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            secrets = self.parse_trufflehog_output(content)
            return True, secrets
        except subprocess.TimeoutExpired:
            log_error('TruffleHog scan timed out after 3 hours')
            print(f'[{Colors.RED}!{Colors.END}] TruffleHog completed scan with errors')
            return False, []
        except Exception as e:
            log_error(f'TruffleHog error: {str(e)}')
            print(f'[{Colors.RED}!{Colors.END}] TruffleHog completed scan with errors')
            return False, []

    def run_kingfisher(self, org, _, output_file):
        abs_output_file = os.path.abspath(output_file)
        os.makedirs(os.path.dirname(abs_output_file), exist_ok=True)

        cmd = [
            "kingfisher", "scan",
            "--github-organization", org,
            "--self-update",
            "--quiet",
            "--only-valid",
            "--format", "json",
            "--output", abs_output_file
        ]

        env = os.environ.copy()
        env["KF_GITHUB_TOKEN"] = self.kf_github_token

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10800, env=env
            )
            if result.returncode not in (0, 200, 205):
                error_msg = result.stderr.strip() if result.stderr else result.stdout.strip() or 'Unknown error'
                log_error(f'Kingfisher failed: {error_msg}')
                print(f'[{Colors.RED}!{Colors.END}] Kingfisher completed scan with errors')
                return False, []
            with open(abs_output_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return True, []
                try:
                    secrets = json.loads(content)
                    if not isinstance(secrets, list):
                        secrets = [secrets] if secrets else []
                    valid_secrets = []
                    for group in secrets:
                        if isinstance(group, dict):
                            if 'matches' in group:
                                for match in group.get('matches', []):
                                    if isinstance(match, dict) and match.get('rule') and match.get('finding'):
                                        valid_secrets.append(match)
                            elif group.get('rule') and group.get('finding'):
                                valid_secrets.append(group)
                    return True, valid_secrets
                except json.JSONDecodeError as e:
                    log_error(f'Kingfisher JSON parsing error: {str(e)}')
                    print(f'[{Colors.RED}!{Colors.END}] Kingfisher completed scan with errors')
                    return False, []
        except subprocess.TimeoutExpired:
            log_error('Kingfisher scan timed out after 3 hours')
            print(f'[{Colors.RED}!{Colors.END}] Kingfisher completed scan with errors')
            return False, []
        except Exception as e:
            log_error(f'Kingfisher error: {str(e)}')
            print(f'[{Colors.RED}!{Colors.END}] Kingfisher completed scan with errors')
            return False, []
