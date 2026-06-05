import socket
import struct
import time
import mss
import numpy as np
import cv2

def send_screen(server_ip, server_port, local_ip=None, fps=15, jpeg_quality=50, monitor=1):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if local_ip:
        sock.bind((local_ip, 0))       # привязка к выбранному интерфейсу
    sock.connect((server_ip, server_port))
    print(f"Подключён к {server_ip}:{server_port}")

    # Отправляем настройки потока: частота кадров (float) + качество JPEG (int)
    sock.sendall(struct.pack('!fB', fps, jpeg_quality))

    # Настройка захвата экрана
    sct = mss.mss()
    monitors = sct.monitors
    if monitor >= len(monitors):
        print(f"Монитор {monitor} не найден, используется основной (1)")
        monitor = 1
    mon = monitors[monitor]
    print(f"Захват экрана {monitor}: {mon['width']}x{mon['height']}")

    frame_time = 1.0 / fps
    try:
        while True:
            start = time.time()
            img = sct.grab(mon)
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            # Сжатие в JPEG
            _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
            data = jpeg.tobytes()
            # Отправка: длина (4 байта) + данные
            sock.sendall(struct.pack('!I', len(data)) + data)

            elapsed = time.time() - start
            sleep_time = frame_time - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
    except KeyboardInterrupt:
        print("\nОстановка по Ctrl+C")
    finally:
        sock.close()

if __name__ == '__main__':
    print("=== Настройка отправки видео с экрана ===")
    server_ip = input("IP-адрес получателя: ").strip()
    server_port = int(input("Порт получателя: ").strip())
    local = input("Локальный IP для привязки (Enter — не привязывать): ").strip()
    local_ip = local if local else None
    fps = int(input("Частота кадров [15]: ") or 15)
    quality = int(input("Качество JPEG (1-100) [50]: ") or 50)
    monitor = int(input("Номер монитора (1, 2, ...) [1]: ") or 1)

    send_screen(server_ip, server_port, local_ip, fps, quality, monitor)