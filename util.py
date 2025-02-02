import socket, struct

# def recv_all(sock: socket.socket) -> bytes:
#     BUFF_SIZE = 8192 # 4 KiB
#     data = b""

#     while True:
#         part = sock.recv(BUFF_SIZE)
#         data += part
    
#         if len(part) < BUFF_SIZE:
#             # either 0 or end of data
#             break
    
#     return data

def send_msg(sock: socket.socket, msg: bytes):
    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack(">I", len(msg)) + msg

    sock.sendall(msg)

def recv_msg(sock: socket.socket) -> bytes | None:
    # Read message length and unpack it into an integer
    raw_msg_len = recvall(sock, 4)
    
    if not raw_msg_len:
        return None
    
    msg_len = struct.unpack(">I", raw_msg_len)[0]

    # Read the message data
    return recvall(sock, msg_len)

def recvall(sock: socket.socket, n: int) -> bytes | None:
    # Helper function to recv n bytes or return None if EOF is hit
    data = b""
   
    while len(data) < n:
        packet = sock.recv(n - len(data))
        
        if not packet:
            return None
        
        data += packet
    
    return data