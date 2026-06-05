import socket
import struct
import cv2
import numpy as np

def receive_screen(listen_ip, listen_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((listen_ip, listen_port))
    sock.listen(1)
    print(f"Ожидание подключения на {listen_ip}:{listen_port}...")
    conn, addr = sock.accept()
    print(f"Подключён {addr}")

    # Получаем настройки потока: 4 байта fps + 1 байт quality
    header = b''
    while len(header) < 5:
        packet = conn.recv(5 - len(header))
        if not packet:
            break
        header += packet
    if len(header) < 5:
        print("Ошибка: не получены настройки потока")
        conn.close()
        return

    fps, quality = struct.unpack('!fB', header)
    print(f"Параметры потока: fps={fps:.1f}, quality={quality}")

    cv2.namedWindow("Screen Receiver", cv2.WINDOW_NORMAL)
    try:
        while True:
            # Длина кадра
            length_data = b''
            while len(length_data) < 4:
                packet = conn.recv(4 - len(length_data))
                if not packet:
                    break
                length_data += packet
            if len(length_data) < 4:
                break
            length = struct.unpack('!I', length_data)[0]

            # JPEG-данные
            jpeg_data = b''
            while len(jpeg_data) < length:
                chunk = conn.recv(min(4096, length - len(jpeg_data)))
                if not chunk:
                    break
                jpeg_data += chunk
            if len(jpeg_data) < length:
                break

            # Декодируем и показываем
            frame = cv2.imdecode(np.frombuffer(jpeg_data, np.uint8), cv2.IMREAD_COLOR)
            if frame is not None:
                cv2.imshow("Screen Receiver", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        conn.close()
        sock.close()

if __name__ == '__main__':
    print("=== Настройка приёма видео с экрана ===")
    listen_ip = input("IP для прослушивания (0.0.0.0 — все интерфейсы, 127.0.0.1 — только локально): ").strip()
    listen_port = int(input("Порт для прослушивания: ").strip())
    receive_screen(listen_ip, listen_port)