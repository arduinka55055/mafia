hypercorn --quic-bind localhost:4433 --certfile fakecert.pem --keyfile fakekey.pem --bind localhost:4433 fastserver:app
