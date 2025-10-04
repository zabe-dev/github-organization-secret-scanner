#!/usr/bin/env python3

import argparse
import os
import random
import signal
import string
import sys
from datetime import datetime

from config import CONFIG, Colors
from scanner import GitHubScanner
from ui import get_arrow_key_selection
from utils import (cleanup_temp_files, log_error, save_results_to_files,
                   signal_handler)


def main():
    ghoss_dir = os.path.join(os.getcwd(), 'ghoss')
    os.makedirs(ghoss_dir, exist_ok=True)

    parser = argparse.ArgumentParser(description='GitHub organization secret scanner')
    parser.add_argument('-l', '--list', metavar='FILE', help='Path to file containing organization names')
    parser.add_argument('-t', '--target', metavar='ORGANIZATION', help='Single organization name to scan')
    args = parser.parse_args()
    if not args.list and not args.target:
        print(f'[{Colors.RED}!{Colors.END}] Either --list/-l or --target/-t must be provided')
        sys.exit(1)
    if args.list and args.target:
        print(f'[{Colors.RED}!{Colors.END}] Cannot use both --list/-l and --target/-t together')
        sys.exit(1)
    scanner = GitHubScanner(CONFIG['TH_GITHUB_TOKEN'], CONFIG['KF_GITHUB_TOKEN'])
    temp_files = []
    signal.signal(signal.SIGINT, lambda sig, frame: signal_handler(sig, frame, temp_files))
    if args.target:
        organizations = [args.target]
    else:
        try:
            with open(args.list, 'r', encoding='utf-8') as f:
                organizations = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            log_error(f'Organization file {args.list} not found')
            print(f'[{Colors.RED}!{Colors.END}] Failed loading organizations from file')
            sys.exit(1)
    used_random_strings = set()
    total_organizations = len(organizations)
    successful_scans = 0
    failed_scans = 0
    skipped_scans = 0
    all_results = {
        'scan_info': {
            'timestamp': datetime.now().isoformat(),
            'total_organizations': total_organizations,
            'organizations_file': args.list if args.list else args.target,
            'successful_scans': 0,
            'failed_scans': 0,
            'skipped_scans': 0,
            'trufflehog_secrets_found': 0,
            'kingfisher_secrets_found': 0
        },
        'results': []
    }
    while True:
        global_random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        if global_random_string not in used_random_strings:
            used_random_strings.add(global_random_string)
            break
    th_output_filename = f'ghoss/output/trufflehog_{global_random_string}.json'
    kf_output_filename = f'ghoss/output/kingfisher_{global_random_string}.json'
    combined_output_filename = f'ghoss/output/scan_results_{global_random_string}.json'
    all_th_secrets = []
    all_kf_secrets = []
    print()
    print(f'[{Colors.BLUE}ℹ{Colors.END}] Loaded {Colors.BOLD}{total_organizations}{Colors.END} organization(s)')
    if CONFIG['TH_GITHUB_TOKEN']:
        print(f'[{Colors.GREEN}✓{Colors.END}] TruffleHog GitHub token supplied')
    else:
        print(f'[{Colors.YELLOW}!{Colors.END}] No TruffleHog GitHub token supplied')
    if CONFIG['KF_GITHUB_TOKEN']:
        print(f'[{Colors.GREEN}✓{Colors.END}] Kingfisher GitHub token supplied')
    else:
        print(f'[{Colors.YELLOW}!{Colors.END}] No Kingfisher GitHub token supplied')
    print()
    try:
        for i, organization in enumerate(organizations, 1):
            while True:
                random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
                if random_string not in used_random_strings:
                    used_random_strings.add(random_string)
                    break
            temp_th_output = f'ghoss/temp/temp_trufflehog_{random_string}.json'
            temp_kf_output = f'ghoss/temp/temp_kingfisher_{random_string}.json'
            temp_files.extend([temp_th_output, temp_kf_output])
            print(f'[{Colors.PURPLE}#{Colors.END}] [{i}/{total_organizations}] Processing {Colors.BOLD}{organization}{Colors.END}')
            orgs = scanner.search_orgs(organization)
            if orgs:
                print(f'[{Colors.GREEN}✓{Colors.END}] Found {Colors.BOLD}{len(orgs)}{Colors.END} organizations')
                best_match = scanner.find_best_matching_org(organization, orgs)
                if best_match:
                    best_match_index = orgs.index(best_match) if best_match in orgs[:10] else 0
                    print(f'[{Colors.GREEN}✓{Colors.END}] Best match: {Colors.BOLD}{best_match}{Colors.END}')
                    print(f'[{Colors.BLUE}?{Colors.END}] Use arrow keys to select organization:')

                    selected_index = get_arrow_key_selection(orgs, best_match_index)
                    selected_org = orgs[selected_index]

                    if selected_org in orgs:
                        print(f'[{Colors.BLUE}*{Colors.END}] Scanning organization: {Colors.BOLD}{selected_org}{Colors.END}')
                        th_success, th_secrets = scanner.run_trufflehog(selected_org, temp_th_output)
                        th_secrets = th_secrets if th_success else []
                        kf_success, kf_secrets = scanner.run_kingfisher(selected_org, organization, temp_kf_output)
                        kf_secrets = kf_secrets if kf_success and isinstance(kf_secrets, list) else []
                        all_th_secrets.extend(th_secrets)
                        all_kf_secrets.extend(kf_secrets)
                        org_result = {
                            'organization': selected_org or organization or 'unknown',
                            'scan_status': 'success' if (th_success or kf_success) else 'failed',
                            'trufflehog_secrets_count': len(th_secrets),
                            'trufflehog_secrets': th_secrets,
                            'kingfisher_secrets_count': len(kf_secrets),
                            'kingfisher_secrets': kf_secrets
                        }
                        all_results['results'].append(org_result)
                        if not th_secrets and not kf_secrets:
                            if th_success:
                                print(f'[{Colors.YELLOW}!{Colors.END}] TruffleHog found no secrets')
                            if kf_success:
                                print(f'[{Colors.YELLOW}!{Colors.END}] Kingfisher found no secrets')
                        else:
                            if th_secrets:
                                print(f'[{Colors.GREEN}✓{Colors.END}] TruffleHog found {Colors.BOLD}{len(th_secrets)}{Colors.END} secrets')
                            if kf_secrets:
                                print(f'[{Colors.GREEN}✓{Colors.END}] Kingfisher found {Colors.BOLD}{len(kf_secrets)}{Colors.END} secrets')
                        if th_success or kf_success:
                            successful_scans += 1
                        else:
                            failed_scans += 1
                    else:
                        print(f'[{Colors.RED}!{Colors.END}] Organization "{Colors.BOLD}{selected_org}{Colors.END}" not found')
                        all_results['results'].append({
                            'organization': selected_org or organization or 'unknown',
                            'scan_status': 'org_not_found',
                            'trufflehog_secrets_count': 0,
                            'trufflehog_secrets': [],
                            'kingfisher_secrets_count': 0,
                            'kingfisher_secrets': []
                        })
                        failed_scans += 1
                else:
                    print(f'[{Colors.YELLOW}!{Colors.END}] No matching organizations, skipping')
                    all_results['results'].append({
                        'organization': organization or 'unknown',
                        'scan_status': 'no_matching_orgs',
                        'trufflehog_secrets_count': 0,
                        'trufflehog_secrets': [],
                        'kingfisher_secrets_count': 0,
                        'kingfisher_secrets': [],
                        'available_orgs': orgs[:5]
                    })
                    skipped_scans += 1
            else:
                print(f'[{Colors.RED}!{Colors.END}] No organizations found')
                all_results['results'].append({
                    'organization': organization or 'unknown',
                    'scan_status': 'no_orgs_found',
                    'trufflehog_secrets_count': 0,
                    'trufflehog_secrets': [],
                    'kingfisher_secrets_count': 0,
                    'kingfisher_secrets': []
                })
                failed_scans += 1
            print()
        all_results['scan_info'].update({
            'successful_scans': successful_scans,
            'failed_scans': failed_scans,
            'skipped_scans': skipped_scans,
            'trufflehog_secrets_found': sum(result.get('trufflehog_secrets_count', 0) for result in all_results['results']),
            'kingfisher_secrets_found': sum(result.get('kingfisher_secrets_count', 0) for result in all_results['results'])
        })
        save_results_to_files(all_th_secrets, all_kf_secrets, all_results, th_output_filename, kf_output_filename, combined_output_filename)
        print(f'[{Colors.BLUE}ℹ{Colors.END}] Scan Summary:')
        print(f'[{Colors.BLUE}ℹ{Colors.END}] Total organizations scanned: {Colors.BOLD}{total_organizations}{Colors.END}')
        print(f'[{Colors.GREEN}✓{Colors.END}] Successful scans: {successful_scans}')
        print(f'[{Colors.YELLOW}⚠{Colors.END}] Skipped scans: {skipped_scans}')
        print(f'[{Colors.RED}✗{Colors.END}] Failed scans: {failed_scans}')
        total_secrets = all_results['scan_info']['trufflehog_secrets_found'] + all_results['scan_info']['kingfisher_secrets_found']
        if total_secrets > 0:
            print(f'[{Colors.GREEN}✓{Colors.END}] Total secrets found: {Colors.BOLD}{total_secrets}{Colors.END}')
            print(f'[{Colors.GREEN}✓{Colors.END}] TruffleHog secrets: {Colors.BOLD}{all_results["scan_info"]["trufflehog_secrets_found"]}{Colors.END}')
            print(f'[{Colors.GREEN}✓{Colors.END}] Kingfisher secrets: {Colors.BOLD}{all_results["scan_info"]["kingfisher_secrets_found"]}{Colors.END}')
        if total_organizations > 0:
            success_rate = (successful_scans/total_organizations*100)
            color = Colors.GREEN if success_rate >= 70 else Colors.YELLOW if success_rate >= 50 else Colors.RED
            print(f'[{Colors.BLUE}ℹ{Colors.END}] Success rate: {color}{success_rate:.1f}%{Colors.END}')
    finally:
        print(f'[{Colors.BLUE}*{Colors.END}] Cleaning up temporary files...')
        cleanup_temp_files(temp_files)
        print(f'[{Colors.GREEN}✓{Colors.END}] Scan process completed.\n')

if __name__ == '__main__':
    main()
