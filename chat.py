from flask import Flask

chat = Flask(__name__)

@app.route('/')
def index():
    return "ЧТо-то"

if __name__ == '__main__':  
    chat.run()






