# QSTP: Quantum Safe Transport Protocol

A proof of concept for an HTTP-like protocol that uses post-quantum asymmetric encryption.
This project uses the ML-KEM-512 key encapsulation mechanism as implemented by [liboqs](https://github.com/open-quantum-safe/liboqs-python) to securely transmit an AES key which is then used for further communication.
Information is transmitted in HTTP-like packets, with optional headers and data.