from flask import Flask,redirect,Response,request,render_template,make_response # import framework flask
import socket # for networking interface

app=Flask(__name__)
@app.route('/')
def main(): # create main function and connect it with file "main.html"
    return open('main.html').read()

@app.route('/<path>',methods=['GET','POST'])
def pather(path):
    if path=='game':
        return open("index.html",rb.read())
    if path.endswith('zip'):
        return Response(open(path,'rb').read(),mimetype='application/zip')
    else:
        return open(path,'rb').read()
app.run(host="0.0.0.0", debug=True,port=80)