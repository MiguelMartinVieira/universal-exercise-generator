import os
import sys
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

def print_header():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(Fore.CYAN + Style.BRIGHT + "==========================================")
    print(Fore.CYAN + Style.BRIGHT + "   UNIVERSAL EXERCISE GENERATOR v2.5")
    print(Fore.CYAN + Style.BRIGHT + "==========================================\n")

def print_error(msg):
    print(Fore.RED + Style.BRIGHT + f"[ERROR] {msg}")

def print_success(msg):
    print(Fore.GREEN + Style.BRIGHT + f"[SUCCESS] {msg}")

def print_info(msg):
    print(Fore.YELLOW + f"[INFO] {msg}")

def input_text(prompt_text, default=None):
    if default:
        p = f"{prompt_text} [{default}]: "
    else:
        p = f"{prompt_text}: "
    
    val = input(Fore.WHITE + p).strip()
    return val if val else default

def input_int(prompt_text, default=None, min_val=None, max_val=None):
    while True:
        val_str = input_text(prompt_text, default)
        try:
            val = int(val_str)
            if min_val is not None and val < min_val:
                print_error(f"Value must be >= {min_val}")
                continue
            if max_val is not None and val > max_val:
                print_error(f"Value must be <= {max_val}")
                continue
            return val
        except ValueError:
            print_error("Please enter a valid number.")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
