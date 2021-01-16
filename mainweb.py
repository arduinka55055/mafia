from flask import Flask, render_template, Response,request,jsonify
import random,hashlib,mafia,socket,time
app = Flask(__name__)
try:
    hostIP=socket.gethostbyname_ex(socket.gethostname())[2][1]
except:
    hostIP=socket.gethostbyname_ex(socket.gethostname())[2][0]
players=[]
players2show=[]
starttrigger=6
game=None;
isstarted=False

gamepointer=0

#  0 1 2   3 4 5 6 7 8 9
## INIT    /\--LOOP----{}

##    0reserved          1          2              3      4     5     6      7        8             9
#просыпаются мафия, знакомство\день,голосовалка\ мафия\маньяк\шериф\доктор\путана\инфо по килам\голосовалка 
def initgame():
    global game
    global isstarted
    if not isstarted:
        isstarted=True
        game=mafia.Game(players)
    

@app.route('/' ,methods=['GET', 'POST'])
def mafiagamestart():
    return render_template('index.html')

@app.route('/register' ,methods=['GET', 'POST'])
def mafiareg():
    if len(players2show)>=starttrigger:
        return '403',403 
    else:
        name=request.form['name']
        data='%s[supermafia]%s' % (name,random.random())
        players.append([name,str(hashlib.sha1(data.encode(encoding="utf-8")).hexdigest())])
        players2show.append(name)
        print(players)
        return str(hashlib.sha1(data.encode(encoding="utf-8")).hexdigest())
@app.route('/antisocketio',methods=['POST'])
def antisocketio():
    global gamepointer
    argument=request.values['arg']
    if argument=='table':
        return jsonify(players2show)
    if argument=='start':
        if len(players2show)>=starttrigger:
            initgame();
            return "1"
        return "0"
    if argument=='action':
        if gamepointer==0:
            pass#ERROR!
        elif gamepointer==1:#якщо гравець - мафія, показати список товаришів.
            if game.info(request.values['uuid'])['type']=='m':
                return game.role2names('m')
        elif gamepointer==2:#ГОЛОСОВАЛКА
            
            
        elif gamepointer==3:
            if game.info(request.values['uuid'])['type']=='m':
                if len(game.role2names('m'))==1:
                    game.mafkill(request.values['data'])
                else:
                    #?????
        elif gamepointer==4:
            if game.info(request.values['uuid'])['type']=='k':
                game.killer(request.values['data'])
        elif gamepointer==5:
            if game.info(request.values['uuid'])['type']=='s':
                return game.sherif(request.values['data'])
        elif gamepointer==6:
            if game.info(request.values['uuid'])['type']=='d':
                game.doctor(request.values['data'])
        elif gamepointer==7:
            if game.info(request.values['uuid'])['type']=='g':
                game.girl(request.values['data'])
        elif gamepointer==8:
        elif gamepointer==9:
        
    return 'Bad Request',400
@app.route('/game' ,methods=['GET', 'POST'])
def maingame(): 
    print(players)#
    return render_template('indexgame.html',players=players2show)
@app.route('/getrole' ,methods=['POST'])
def roleget(): 
    return game.info(request.values['uuid'])['type']
@app.route('/favicon.ico')
def icon():
    return open('favicon.jpg','rb').read()  
if __name__ == '__main__':
   app.run(ssl_context=('d:/PEM/certificate.crt','d:/PEM/private.key'),host=hostIP, debug=True,port=443)
