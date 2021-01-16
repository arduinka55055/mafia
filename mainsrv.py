from flask import Flask,redirect,Response,request,render_template,make_response
import socket

app=Flask(__name__)
@app.route('/')
def main():
    return open('main.html').read()

@app.route('/<path>',methods=['GET','POST'])
def pather(path):
    if path=='game':
        return open("index.html",'rb').read()
    if path.endswith('zip'):
        return Response(open(path,'rb').read(),mimetype='application/zip')
    else:
        return open(path,'rb').read()
app.run(ssl_context=('/run/media/denis/01D57B7C59892920/PEM/certificate.crt','/run/media/denis/01D57B7C59892920/PEM/private.key'),host="192.168.0.100", debug=False,port=443)