"""
Port Scanner - Educational Tool
WARNING: Only scan systems you own or have explicit permission to test.
Unauthorized port scanning may be illegal in your jurisdiction.
"""

# Core networking library for sockets
import socket

# Used to terminate the program safely
import sys

# Colorized terminal output
from colorama import init, Fore, Back, Style

# Thread pool for concurrent port scanning
from concurrent.futures import ThreadPoolExecutor, as_completed

# Command-line argument parsing
import argparse

# Used to measure scan duration
import time


# Initialize colorama so colors reset automatically after each print
init(autoreset=True)


# Common well-known ports mapped to their typical services
# This is heuristic-based service identification, not guaranteed accuracy
COMMON_PORTS = {
    20: "FTP-DATA", 21: "FTP", 22: "SSH", 23: "Telnet",
    25: "SMTP", 53: "DNS", 80: "HTTP", 110: "POP3",
    143: "IMAP", 443: "HTTPS", 3306: "MySQL", 3389: "RDP",
    5432: "PostgreSQL", 5900: "VNC", 8080: "HTTP-Proxy",
}


# Stores Future objects representing each submitted scan task
ports_scanned = []

# Counter for open ports found during the scan
open_ports = 0


def scan(target, ports):
    """
    Creates a thread pool and submits scan tasks for each port.
    Waits until all threads finish before returning.
    """
    with ThreadPoolExecutor(max_workers=50) as executor:
        # Submit a scanning task for each port
        for port in range(1, ports + 1):
            ports_scanned.append(executor.submit(scan_port, target, port))

        # Block until all submitted tasks are completed
        for future in as_completed(ports_scanned):
            pass  # All output is handled inside scan_port()


def scan_port(target, port):
    """
    Attempts to connect to a single port.
    If successful, the port is considered OPEN.
    Optionally performs basic banner grabbing.
    """
    sock = socket.socket()

    # Timeout applies to connect() and recv()
    sock.settimeout(2.0)

    # Default service name if port is not in COMMON_PORTS
    service = "Not available in the common ports database"

    try:
        # Attempt TCP connection
        sock.connect((target, port))

        # Update global open port counter
        global open_ports
        open_ports += 1

        banner = None

        try:
            # Attempt banner grabbing (HTTP-style probe)
            sock.settimeout(2.0)
            sock.send(b'HEAD / HTTP/1.1\r\n\r\n')
            banner = sock.recv(1024).decode(errors="ignore").strip()
        except socket.timeout:
            # Many services do not send banners; this is normal
            pass

        # Assign service name if port is well-known
        if port in COMMON_PORTS:
            service = COMMON_PORTS[port]

        # Output formatted scan result
        if banner:
            print(
                f"\n{Fore.GREEN}[+]{Style.BRIGHT} "
                f"{Fore.CYAN}Port {port} "
                f"{Fore.GREEN}OPEN{Style.RESET_ALL} | "
                f"{Fore.YELLOW}Banner: {Fore.WHITE}{banner} | "
                f"{Fore.YELLOW}Service: {Fore.MAGENTA}{service}"
            )
        else:
            print(
                f"\n{Fore.GREEN}[+]{Style.BRIGHT} "
                f"{Fore.CYAN}Port {port} "
                f"{Fore.GREEN}OPEN{Style.RESET_ALL} | "
                f"{Fore.YELLOW}Banner: {Fore.WHITE}None | "
                f"{Fore.YELLOW}Service: {Fore.MAGENTA}{service}"
            )

    except ConnectionRefusedError:
        # Port is closed (RST received)
        pass

    except socket.timeout:
        # Port is filtered / silently dropped
        pass

    except PermissionError:
        # OS-level restriction (e.g., firewall or privilege issue)
        print(Fore.YELLOW + f"\n[-] Port {port}: blocked by OS/firewall")

    except KeyboardInterrupt:
        # Allow user to interrupt scan cleanly
        raise

    except Exception as e:
        # Catch-all for unexpected socket errors
        print(Fore.RED + f"\n[-] Port {port}: error ({e})")

    finally:
        # Always release socket resources
        sock.close()


# Command-line interface configuration
parser = argparse.ArgumentParser(description="Multi Threaded Port Scanner")
parser.add_argument("-t", "--target", required=True, help="Target IP address")
parser.add_argument("-p", "--ports", required=True, help="Number of ports to scan")

args = parser.parse_args()


# Legal and ethical warning prompt
print("=" * 60)
print(f"{Fore.RED}WARNING: Only scan authorized targets!")
print(f"{Fore.RED}Unauthorized scanning may be illegal.")
print("=" * 60)

confirm = input("Do you have permission to scan this target? (yes/no): ")
if confirm.lower() != 'yes':
    print("Scan cancelled.")
    sys.exit()


# Start scan
print(Fore.GREEN + f"Scanning ports of {args.target}")

# Record scan start time
start_time = time.time()

# Perform scan
scan(args.target, int(args.ports))

# Record scan end time
end_time = time.time()

# Calculate total scan duration
duration = end_time - start_time


# Final scan summary
print("=" * 60)
print("SCAN COMPLETE")
print("=" * 60)
print(
    f"Target: {args.target}\n"
    f"Total ports scanned: {len(ports_scanned)}\n"
    f"Open Ports Found: {open_ports}\n"
    f"Scan Duration: {duration:.2f} seconds"
)
