# ESP32

The code requires valid AWS IoT thing and certificate.

1. Create directory lib in your device storage.
2. Upload lib/sds011.py to device.
3. Replace boot.py with the one provided here.
4. Upload main-sds011.py as main.py.
5. Upload thing's private key and certificate (DER format) as `32-01.key.der` and `32-01.cert.der`.
