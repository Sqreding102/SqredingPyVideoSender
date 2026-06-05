import socket
import struct
import cv2
import numpy as np
import sounddevice as sd
import threading
import queue

running = True

def audio_player(audio_queue, sample_rate, channels):
    """Функция для отдельного потока воспроизведения через OutputStream."""
    global running
    stream = sd.OutputStream(samplerate=sample_rate, channels=channels, dtype='int16')
    stream.start()
    try:
        while running:
            try:
                data = audio_queue.get(timeout=0.1)
                # data это bytes, преобразуем в numpy int16
                int16_arr = np.frombuffer(data, dtype=np.int16).reshape(-1, channels)
                stream.write(int16_arr)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Ошибка воспроизведения: {e}")
                break
    finally:
        stream.stop()
        stream.close()

def receive_screen(listen_ip, listen_port):
    global running
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((listen_ip, listen_port))
    sock.listen(1)
    print(f"Ожидание подключения на {listen_ip}:{listen_port}...")
    conn, addr = sock.accept()
    print(f"Подключён {addr}")

    # Параметры видео
    header = conn.recv(5)
    fps, quality = struct.unpack('!fB', header)
    print(f"Параметры видео: fps={fps:.1f}, quality={quality}")

    # Параметры аудио
    audio_data = b''
    while len(audio_data) < 12:
        packet = conn.recv(12 - len(audio_data))
        if not packet:
            break
        audio_data += packet
    if len(audio_data) < 12:
        print("Ошибка получения параметров аудио")
        conn.close()
        return
    sample_rate, channels, block_size = struct.unpack('!i i i', audio_data)
    audio_enabled = (sample_rate > 0 and channels > 0)
    if audio_enabled:
        print(f"Параметры аудио: {sample_rate} Гц, каналов: {channels}")

    audio_queue = queue.Queue()
    player_thread = None
    if audio_enabled:
        player_thread = threading.Thread(target=audio_player, args=(audio_queue, sample_rate, channels))
        player_thread.daemon = True
        player_thread.start()

    cv2.namedWindow("Screen Receiver", cv2.WINDOW_NORMAL)
    try:
        while running:
            # Читаем тип пакета
            packet_type = b''
            while len(packet_type) < 1:
                chunk = conn.recv(1 - len(packet_type))
                if not chunk:
                    break
                packet_type += chunk
            if not packet_type:
                break
            ptype = packet_type[0]

            # Длина
            length_data = b''
            while len(length_data) < 4:
                chunk = conn.recv(4 - len(length_data))
                if not chunk:
                    break
                length_data += chunk
            if len(length_data) < 4:
                break
            length = struct.unpack('!I', length_data)[0]

            # Данные
            payload = b''
            while len(payload) < length:
                chunk = conn.recv(min(4096, length - len(payload)))
                if not chunk:
                    break
                payload += chunk
            if len(payload) < length:
                break

            if ptype == ord('V'):
                frame = cv2.imdecode(np.frombuffer(payload, np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    cv2.imshow("Screen Receiver", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        running = False
                        break
            elif ptype == ord('A'):
                if audio_enabled:
                    audio_queue.put(payload)
    except KeyboardInterrupt:
        pass
    finally:
        running = False
        if player_thread and player_thread.is_alive():
            player_thread.join(timeout=1)
        cv2.destroyAllWindows()
        conn.close()
        sock.close()

if __name__ == '__main__':
    print("=== Настройка приёма видео с экрана ===")
    listen_ip = input("IP для прослушивания (0.0.0.0 — все интерфейсы, 127.0.0.1 — только локально): ").strip()
    listen_port = int(input("Порт для прослушивания: ").strip())
    receive_screen(listen_ip, listen_port)