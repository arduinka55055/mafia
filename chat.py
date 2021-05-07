from types import MethodDescriptorType
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, emit, rooms
from flask_session import Session
from werkzeug import useragents


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = '.....'
app.config['SESSION TYPE'] = 'filesystem'

Session(app)

@app.route('/', methods=['GET','POST' ])
def index():
    return render_template("index.html")

@app.route('/pregamechat', methods=['GET','POST'])
def pregamechat():
    if(request.method = 'POST'):
        room = request.form['room'] 
        code = request.form['code']  
        #   
          

if __name__ == '__main__':  
    app.run()






