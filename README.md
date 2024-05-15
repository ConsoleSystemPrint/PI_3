# TCP и UDP Сканер Портов

Это скрипт на Python для сканирования TCP и UDP портов на заданном хосте. Он определяет, какие порты открыты в заданном диапазоне, поддерживает параллельную реализацию и включает функцию для определения работающего на порту протокола.

## Требования

- Python 3.x

### Примеры ввода и вывода

Пример ввода:

 IP адрес или доменное имя для сканирования: example.com

Введите начальный порт: 78

Введите конечный порт: 82


Пример вывода:

Сканирование хоста: 93.184.216.34

TCP порт 80 открыт (сканирование заняло 0.02 секунд).
Обнаружен протокол на TCP порту 80: HTTP

UDP порт 80 открыт или фильтруется (тайм-аут).
UDP порт 81 открыт или фильтруется (тайм-аут).
UDP порт 82 открыт или фильтруется (тайм-аут).

## Функции

1. **Сканирование TCP портов**:
    Попытка установить соединение с каждым портом в заданном диапазоне. Если порт открыт, производится определение протокола.

2. **Сканирование UDP портов**:
    Отправка пустого пакета и ожидание ответа (или таймаута). Сообщает, если порт открыт или фильтруется.

3. **Определение Протокола**:
    Для каждого открытого TCP порта отправляется предварительно определенное сообщение для определения такого протокола, как HTTP, SMTP, POP3, DNS и SNTP, на основе полученного ответа.

## Обработка ошибок

Программа обрабатывает следующие ошибки:
- Отсутствие доступа в Интернет
- Длительное ожидание ответа от сервера
- Невозможно разрешить доменное имя в IP адрес

### Дополнительные замечания

1. Добавление новых протоколов:
   Чтобы добавить новый протокол, просто добавьте соответствующее сообщение в словарь protocols:
   
   protocols = {
       "NEW_PROTOCOL": b"Message to identify new protocol",
       ...
   }
   

2. Изменение таймаутов:
   Вы можете настроить таймауты для повышения или понижения чувствительности сканера. Они установлены на 1 секунду в текущей реализации.

3. Параллельное выполнение:
   Использование потоков для обработки каждого типа портов (TCP и UDP) позволяет ускорить процесс.


## Описание структуры кода

### Импорты

```python
import socket
import threading
import time
import queue
```

Эти модули обеспечивают низкоуровневую работу с сетью (`socket`), поддержку многопоточности (`threading`), измерение времени (`time`) и очереди (`queue`).

### Очереди портов

```python
tcp_ports = queue.Queue()
udp_ports = queue.Queue()
```

Используем очереди для управления портами, которые должны быть проверены, многопоточными функциями.

### Протоколы для распознавания

```python
protocols = {
    "HTTP": b"GET / HTTP/1.0\r\n\r\n",
    "SMTP": b"HELO example.com\r\n",
    "POP3": b"USER example\r\n",
    "DNS": b"\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01",
    "SNTP": b'\xe3\x00\x06\xec\x00\x00\x00\x00\x00\x00\x00\x00' + 40 * b'\x00',
}
```

Содержит набор известных протоколов и соответствующие запросы для распознавания их на порту.

### Функции

#### `add_ports_to_queue(start_port, end_port)`

```python
def add_ports_to_queue(start_port, end_port):
    for port in range(start_port, end_port + 1):
        tcp_ports.put(port)
        udp_ports.put(port)
```

Добавляет диапазон портов в соответствующие очереди для TCP и UDP.

#### `scan_tcp_ports(host)`

```python
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
```

Сканирует порты для TCP, проверяя открытость каждого порта. Если порт открыт, пытается определить протокол, запускаемый на этом порту.

#### `scan_udp_ports(host)`

```python
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
```

Сканирует порты для UDP, проверяя, открыты ли они. Необходимо учитывать, что отсутствие ответа также может означать, что порт фильтруется.

#### `detect_protocol(host, port)`

```python
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
```

Пытается определить, какой протокол (например, HTTP, SMTP и т.д.) использует данный порт, отправляя соответствующий запрос и анализируя ответ.

### Главная функция

```python
def main():
    host = input("Введите IP адрес или доменное имя для сканирования: ")
    try:
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
```

В этой функции запрашивается ввод IP-адреса или доменного имени, диапазона портов и далее запускаются потоки для сканирования TCP и UDP портов. После завершения работы потоки соединяются.