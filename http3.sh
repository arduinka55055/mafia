hypercorn --quic-bind 0.0.0.0:443 --certfile fakecert.pem --keyfile fakekey.pem --bind 0.0.0.0:443 fastserver:app
