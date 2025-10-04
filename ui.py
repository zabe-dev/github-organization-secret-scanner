import sys
import termios
import time
import tty

from config import Colors


def get_arrow_key_selection(orgs, best_match_index):
    selected_index = best_match_index
    num_lines = min(len(orgs), 10) + (1 if len(orgs) > 10 else 0)

    for i, org in enumerate(orgs[:10]):
        if i == selected_index:
            print(f'    {Colors.GREEN}► {i+1}. {org}{Colors.END}')
        else:
            print(f'      {Colors.CYAN}{i+1}.{Colors.END} {org}')
    if len(orgs) > 10:
        print(f'      {Colors.CYAN}...{Colors.END} and {Colors.BOLD}{len(orgs) - 10}{Colors.END} more')

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    start_time = time.time()

    try:
        tty.setraw(fd)
        import select

        sys.stdout.write(f'\033[{num_lines}A')
        sys.stdout.flush()

        while True:
            if time.time() - start_time >= 5:
                break

            if select.select([sys.stdin], [], [], 0.1)[0]:
                char = sys.stdin.read(1)

                if char == '\x1b':
                    next_chars = sys.stdin.read(2)
                    if next_chars == '[A':
                        new_index = max(0, selected_index - 1)
                        if new_index != selected_index:
                            selected_index = new_index
                            start_time = time.time()

                            for i, org in enumerate(orgs[:10]):
                                sys.stdout.write('\r\033[K')
                                if i == selected_index:
                                    sys.stdout.write(f'    {Colors.GREEN}► {i+1}. {org}{Colors.END}')
                                else:
                                    sys.stdout.write(f'      {Colors.CYAN}{i+1}.{Colors.END} {org}')
                                sys.stdout.write('\033[B\r')
                            if len(orgs) > 10:
                                sys.stdout.write('\r\033[K')
                                sys.stdout.write(f'      {Colors.CYAN}...{Colors.END} and {Colors.BOLD}{len(orgs) - 10}{Colors.END} more')
                                sys.stdout.write('\033[B\r')

                            sys.stdout.write(f'\033[{num_lines}A')
                            sys.stdout.flush()
                    elif next_chars == '[B':
                        new_index = min(len(orgs[:10]) - 1, selected_index + 1)
                        if new_index != selected_index:
                            selected_index = new_index
                            start_time = time.time()

                            for i, org in enumerate(orgs[:10]):
                                sys.stdout.write('\r\033[K')
                                if i == selected_index:
                                    sys.stdout.write(f'    {Colors.GREEN}► {i+1}. {org}{Colors.END}')
                                else:
                                    sys.stdout.write(f'      {Colors.CYAN}{i+1}.{Colors.END} {org}')
                                sys.stdout.write('\033[B\r')
                            if len(orgs) > 10:
                                sys.stdout.write('\r\033[K')
                                sys.stdout.write(f'      {Colors.CYAN}...{Colors.END} and {Colors.BOLD}{len(orgs) - 10}{Colors.END} more')
                                sys.stdout.write('\033[B\r')

                            sys.stdout.write(f'\033[{num_lines}A')
                            sys.stdout.flush()
                elif char == '\r' or char == '\n':
                    break
                elif char == '\x03':
                    raise KeyboardInterrupt
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        sys.stdout.write(f'\033[{num_lines}B')
        sys.stdout.flush()

    return selected_index
