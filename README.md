# SqredingPyVideoSender

Cross-platform tool for real-time video streaming over a network.  
⚠️ **Audio receiver is currently unstable** – manual push/restart may be needed.

## Requirements

- Python 3.10 or newer
- Works on Windows, Linux, macOS

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/SqredingPyVideoSender.git
cd SqredingPyVideoSender
Install dependencies
Configure your sender/receiver addresses in the script before starting.

    🔇 Audio notice
    Audio capture/receive can be unstable. If you experience issues, try:

        Restarting the audio stream manually

        Checking your microphone permissions

        Ensuring your audio device is correctly selected in the system settings

Features

    Screen capture and video streaming in real time

    Lightweight – built with MSS, OpenCV and NumPy

    Cross-platform support

    (Experimental) Audio streaming via SoundDevice

Troubleshooting

    ModuleNotFoundError → Run pip install -r requirements.txt

    Audio glitches → The audio part is still experimental; contributions are welcome!

    Network issues → Verify your firewall settings and IP/port configuration

Contributing

Pull requests and bug reports are welcome. Please open an issue first to discuss what you would like to change.
License

This project is provided "as is", without any warranty. Use at your own risk.
