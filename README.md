## Disclaimer

This tool is intended **for educational and authorized penetration testing purposes only**.  
The author is **NOT responsible** for any misuse or illegal activities conducted using this software.  
Always obtain explicit permission before testing any network or system. Unauthorized use is illegal and unethical.


# Winbox Brut3F0rc3r

A multithreaded Winbox (MikroTik) brute force tool with  Telegram notifications.

---

## Features

- AES encryption compatible with Mikrotik Winbox login
- Supports single user/password or username and password lists
- Option to try blank password
- Multithreaded for speed
- Real-time progress bar in terminal
- Telegram alert on successful login
- brute port 8291
---

## Installation

Requires Python 3.6+.

Install dependencies:

```bash
pip install -r requirements.txt

Usage:

python3 winbox-brute.py -t <target_ip> -U user.txt --dict pass.txt --blank -T 10

Arguments:

    -t, --target: Target IP address (required)

    -P, --port: Target port (default 8291)

    -u, --user: Single username

    -U, --userlist: File containing usernames, one per line

    -p, --passw: Single password

    --dict: File containing passwords, one per line

    --blank: Include blank password in the list

    -T, --threads: Number of threads (default 10)

Example

python3 winbox-brute.py -t 192.168.88.1 -U user.txt --dict pass.txt --blank -T 20

Disclaimer

Use responsibly and only against systems you have permission to test.
