hypercorn --quic-bind 0.0.0.0:4433 --certfile .deploycrt.pem --keyfile .deploykey.pem --bind 0.0.0.0:4433 fastserver:app
