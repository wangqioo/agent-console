# ESP32 Hardware Placeholder

The first hardware target is an ESP32-S3 board with:

- small SPI display
- two to four buttons
- optional rotary encoder
- USB serial or Wi-Fi connection to the local daemon

The daemon API will be stabilized before firmware is written.

Initial button mapping:

- Button 1: switch active session
- Button 2: continue active session
- Button 3: stop/cancel active session
- Button 4: send configured prompt

