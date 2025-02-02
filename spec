-- overview --
QSTP quantum safe transfer protocol
use a quantum safe kem alg to generate and send AES key to server
use that key to encrypt both ways
req + resp architecture
stateless

-- client --
Generate client public key
send key to sv

-- server --
recv client key
server generates and encapsulates secret using client's public key
send ciphertext to cl

-- client --
recv ciphertext key
client decapsulates ciphertext getting the secret

-- both --
use shared secret with AES to encrypt data

-- client --
send AES encrypted data

-- server --
recv encrypted data
decrypt
do stuff with data
send encrypted response

-- client --
recv resp from server
decrypt and handle

-- req --
<version> [GET, POST, DELETE, PATCH] <path>
<headers>

<data>

-- resp --
<version> <status> <status message>
<headers>

<data>

-- status codes --
100: server
    100: server ok
    101: server error

200: client
    200: client ok
    201: malformed request
    202: unknown version
    203: unknown method
    204: unknown path
    205: unauthenticated
    206: unauthorized

-- example req --
QSTP/1 GET /
authorization: token
content-type: text/plaintext

example test data

-- example resp --
QSTP/1 200 OK
content-type: text/plaintext

example response data