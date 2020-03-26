# AWS-IoT

You must generate DER files from AWS thing certificate and the private key:
```
openssl x509 -in 7eecf5046f-certificate.pem.crt -out 8266-01.cert.der -outform DER
openssl rsa -in 7eecf5046f-private.pem.key -out 8266-01.key.der -outform DER
```
Make sure to use the micropython binaries in ESP32 and ESP8266 directories since they're the ones tested with the source code provided. This is especially true for ESP32 because the latest micropython binary has problems with SSL/TLS.
