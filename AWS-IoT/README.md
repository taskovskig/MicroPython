# AWS-IoT

You must generate DER files from AWS thing certificate and the private key:

openssl x509 -in 7eecf5046f-certificate.pem.crt -out 8266-01.cert.der -outform DER
openssl rsa -in 7eecf5046f-private.pem.key -out 8266-01.key.der -outform DER
