import socket, struct

def send_msg(sock: socket.socket, msg: bytes):
    """Helper function to send a message (bytes)"""

    msg = struct.pack(">I", len(msg)) + msg

    sock.sendall(msg)

def recv_msg(sock: socket.socket) -> bytes | None:
    """Helper function to recv a full message (bytes) or return `None` if no length specified or EOF is hit"""

    raw_msg_len = recvall(sock, 4)
    
    if not raw_msg_len:
        return None
    
    msg_len = struct.unpack(">I", raw_msg_len)[0]

    return recvall(sock, msg_len)

def recvall(sock: socket.socket, n: int) -> bytes | None:
    """Helper function to recv `n` bytes or return `None` if EOF is hit"""
    
    data = b""
   
    while len(data) < n:
        packet = sock.recv(n - len(data))
        
        if not packet:
            return None
        
        data += packet
    
    return data