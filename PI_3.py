import socket
import threading
import time
import queue

tcp_ports = queue.Queue()
udp_ports = queue.Queue()

protocols = {
    "HTTP": b"GET / HTTP/1.0\r\n\r\n",
    "SMTP": b"HELO example.com\r\n",
    "POP3": b"USER example\r\n",
    "DNS": b"\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01",
    "SNTP": b'\xe3\x00\x06\xec\x00\x00\x00\x00\x00\x00\x00\x00' + 40 * b'\x00',
}

def add_ports_to_queue(start_port, end_port):
    for port in range(start_port, end_port + 1):
        tcp_ports.put(port)
        udp_ports.put(port)

def scan_tcp_ports(host):
    while not tcp_ports.empty():
        port = tcp_ports.get()
        try:
            start_scan = time.time()
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.settimeout(1)
            conn.connect((host, port))
            conn.close()
            duration = time.time() - start_scan
            print(f"TCP порт {port} открыт (сканирование заняло {duration:.2f} секунд).")
            detect_protocol(host, port)
        except (socket.timeout, ConnectionRefusedError, socket.error):
            continue

def scan_udp_ports(host):
    while not udp_ports.empty():
        port = udp_ports.get()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1)
            sock.sendto(b"", (host, port))
            start_time = time.time()
            sock.recvfrom(1024)
        except socket.timeout:
            print(f"UDP порт {port} открыт или фильтруется (тайм-аут).")
        except (socket.error, socket.gaierror):
            continue
        finally:
            sock.close()

def detect_protocol(host, port):
    detected_protocol = None
    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.settimeout(1)
        conn.connect((host, port))
        conn.settimeout(1)

        for protocol, message in protocols.items():
            conn.sendall(message)
            response = conn.recv(1024)
            if response:
                detected_protocol = protocol
                break
        conn.close()
    except (socket.timeout, ConnectionRefusedError, socket.error):
        pass

    if detected_protocol:
        print(f"Обнаружен протокол на TCP порту {port}: {detected_protocol}")
    else:
        print(f"Протокол не обнаружен на TCP порту {port}")

def main():
    host = input("Введите IP адрес или доменное имя для сканирования: ")
    try:
        # Разрешение доменного имени в IP-адрес
        ip = socket.gethostbyname(host)
        print(f"Сканирование хоста: {ip}")
    except socket.gaierror:
        print(f"Ошибка: Не удалось разрешить {host}")
        return

    start_port = int(input("Введите начальный порт: "))
    end_port = int(input("Введите конечный порт: "))

    add_ports_to_queue(start_port, end_port)

    tcp_thread = threading.Thread(target=scan_tcp_ports, args=(host,))
    udp_thread = threading.Thread(target=scan_udp_ports, args=(host,))

    tcp_thread.start()
    udp_thread.start()

    tcp_thread.join()
    udp_thread.join()

if __name__ == "__main__":
    main()