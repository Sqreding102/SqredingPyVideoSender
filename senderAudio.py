import socket
import struct
import time
import threading
import mss
import numpy as np
import cv2
import sounddevice as sd

sock = None
sock_lock = threading.Lock()
running = True

def list_audio_input_devices():
    """Выводит список устройств ввода и возвращает их список."""
    print("\nДоступные устройства ввода звука:")
    devices = sd.query_devices()
    input_devices = []
    for dev in devices:
        if dev['max_input_channels'] > 0:
            input_devices.append(dev)
    for i, dev in enumerate(input_devices):
        print(f"  [{i}] {dev['name']} (каналов: {dev['max_input_channels']})")
    return input_devices

def audio_callback(indata, frames, time_info, status, stream_context):
    """Callback, вызываемый sounddevice при появлении новых аудиоданных."""
    global running
    if status:
        print(f"Статус аудио: {status}")
    # indata: numpy array, shape = (frames, channels), dtype обычно float32
    if indata is not None:
        # Преобразуем float32 в int16
        int16_data = (indata * 32767).astype(np.int16).tobytes()
        try:
            with sock_lock:
                sock.sendall(b'A' + struct.pack('!I', len(int16_data)) + int16_data)
        except Exception as e:
            print(f"Ошибка отправки аудио: {e}")
            running = False

def send_screen(server_ip, server_port, local_ip=None, fps=15, jpeg_quality=50, monitor=1,
                audio_enabled=False, audio_device_index=None, sample_rate=44100,
                channels=1, block_size=1024):
    global sock, sock_lock, running
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if local_ip:
        sock.bind((local_ip, 0))
    sock.connect((server_ip, server_port))
    print(f"Подключён к {server_ip}:{server_port}")

    # Отправляем параметры видео
    sock.sendall(struct.pack('!fB', fps, jpeg_quality))
    # Отправляем параметры аудио
    if audio_enabled:
        sock.sendall(struct.pack('!i i i', sample_rate, channels, block_size))
    else:
        sock.sendall(struct.pack('!i i i', 0, 0, 0))

    # Захват экрана
    sct = mss.mss()
    monitors = sct.monitors
    if monitor >= len(monitors):
        print(f"Монитор {monitor} не найден, используется основной (1)")
        monitor = 1
    mon = monitors[monitor]
    print(f"Захват экрана {monitor}: {mon['width']}x{mon['height']}")

    audio_stream = None
    if audio_enabled:
        devices = list_audio_input_devices()
        if not devices:
            print("Нет доступных устройств ввода! Звук не будет передаваться.")
            audio_enabled = False
        else:
            if audio_device_index is None:
                audio_device_index = int(input("Введите номер устройства ввода: ") or 0)
            chosen_device = devices[audio_device_index]
            print(f"Используется: {chosen_device['name']}")
            # Создаём InputStream с callback
            audio_stream = sd.InputStream(
                samplerate=sample_rate,
                channels=channels,
                device=chosen_device['index'],
                callback=audio_callback,
                blocksize=block_size,
                dtype='float32'
            )
            audio_stream.start()

    frame_time = 1.0 / fps
    try:
        while running:
            start = time.time()
            img = sct.grab(mon)
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
            data = jpeg.tobytes()
            with sock_lock:
                sock.sendall(b'V' + struct.pack('!I', len(data)) + data)

            elapsed = time.time() - start
            sleep_time = frame_time - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
    except KeyboardInterrupt:
        print("\nОстановка передачи...")
    finally:
        running = False
        if audio_stream:
            audio_stream.stop()
            audio_stream.close()
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

    audio_choice = input("Передавать звук? (y/n) [n]: ").strip().lower()
    audio_enabled = audio_choice == 'y'
    if audio_enabled:
        sample_rate = int(input("Частота дискретизации (44100/48000) [44100]: ") or 44100)
        channels = int(input("Количество каналов (1 - моно, 2 - стерео) [1]: ") or 1)
        block_size = int(input("Размер блока (сэмплы) [1024]: ") or 1024)
        send_screen(server_ip, server_port, local_ip, fps, quality, monitor,
                    audio_enabled=True, audio_device_index=None,
                    sample_rate=sample_rate, channels=channels, block_size=block_size)
    else:
        send_screen(server_ip, server_port, local_ip, fps, quality, monitor, audio_enabled=False)пше