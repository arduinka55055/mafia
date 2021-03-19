/*
methods to communicate

..... means blocking request(awaiting users input)
##############################
|client                Server|
|                            |
|         data get           |                    
|                            |
|GetInfo request -------->   |                  
|  <----------- Info response| #Number of players, their nicks and avatars
|                            |
|         negotiation        |
|                            |
|ClientHello ------------>   | #sending PlayerRAW
|  <------------- ServerHello| #receiving ok status, start pinging
|(periodical GetInfo)        |
|                            |
|          Game start        |
|                            |
|StartGame master request--> |
|  <--------------- StartGame| #receiving targets UUID's, nicks, avatars, my role, creating me class
|Reply to check connection-> |
|           .....            |
|  <----------- Is Successful| #if true, redirect to Game window
|                            |
|          Game itself       |
|  <--------------- DoPerform| #signal packet to start awaiting user input. ignore for civilian
|Target ----------------->   | #packet with target
|           .....            | 
|  <--------------------Stats| #killed players, healed players, fucked players, Is game finished
|  Vote target ---------->   | #packet with target
|           .....            |
|  <---------------VoteResult| #killed player
|                            |
|#############################
*/
class MeRAW {
    constructor(gid, name, avatar) {
        this.gid = gid;
        this.name = name;
        this.avatar = avatar;
    }
}
let packets = {
    //RoomID PlayerID GoogleID
    "GidInject": (meraw) => { return { gid: meraw.gid, nick: meraw.name, avatar: meraw.avatar } },
    "GetInfo": () => { return { pck: "GetInfo" } },
    "ClientHello": (rid) => { return { pck: "ClientHello", rid: rid } },
    "MakeRoom": (roomName, count) => { return { pck: "MakeRoom", data: [roomName, count] } },
    "StartGame": (rid) => {return { pck:"StartGame",rid:rid }} ,
    "Perform": (rid, pid) => { return { pck: "Perform", rid: rid, pid: pid } },
    "Vote": (rid, pid) => { return { pck: "Vote", rid: rid, pid: pid } }
}
function makePacket(meraw, type) {
    return { ...packets.GidInject(meraw), ...type };
}
class connector {//this class is more like abstract + WS logic
    constructor(sock, meraw) {
        this.sock = sock
        this.me = meraw;

        this.sock.onopen = (e) => {
            this.sock.send(JSON.stringify(makePacket(this.me)));
            this.onload();
        }
        this.sock.onmessage = (event) => {
            this._consume(JSON.parse(event.data));
        };

        this.sock.onclose = function (event) {
            if (event.wasClean) {
                alert(`[close] Соединение закрыто чисто, код=${event.code} причина=${event.reason}`);
            } else {
                // например, сервер убил процесс или сеть недоступна
                // обычно в этом случае event.code 1006
                alert('[close] Соединение прервано');
                //TODO:реконнект
            }
        };

        this.sock.onerror = function (error) {
            alert(`[error] ${error.message}`);
        };
    }
    _consume(data) {
        console.error("NotImplementedConsumePacket!")
    }
    onload(){
        console.error("NotImplementedOnload!")
    }
    send(data) {
        this.sock.send(JSON.stringify(data));
    }
    async get(pck,epck=null) {
        var self=this;
        return new Promise((resolve,reject)=> {
            self.sock.addEventListener('message', function shit(e) {
                var json=JSON.parse(e.data);
                if(json.pck==pck){
                    resolve(json);
                    this.removeEventListener('message',shit,false);
                }
                else if(json.pck=="Error"){
                    if(!epck || json.msg==epck) reject(json);this.removeEventListener('message',shit,false);
                }
            });
        });
    }
}

class ReceiverLogic extends connector {
    constructor(sock, meraw) {
        super(sock, meraw);
    }
    _consume(data) {
        if (data.pck == "GameStart") {
            console.log("Почалася нова гра за айді:"+data);
        }
        else if (data.pck == "RSV") { }
        else if (data.pck == "RSV") { }
        else if (data.pck == "RSV") { }
    }
}
class logic extends ReceiverLogic {
    constructor(sock, meraw) {
        super(sock, meraw);
    }
    async newRoom(name, count) {
        this.send(makePacket(this.me, packets.MakeRoom(name, count)));
        return await this.get("ack");
    }
    async connect(rid){
        this.send(makePacket(this.me, packets.ClientHello(rid)));
        var result= await this.get("ServerHello","RoomNotFound");
        return result
    }
    async getInfo(rid) {
        this.send(makePacket(this.me, packets.GetInfo(rid)));
        var result= await this.get("Info");
        return result
    }
    async start(rid) {
        this.send(makePacket(this.me, packets.StartGame(rid)));
        var result= await this.get("GameStarted","GameStartError");//too few players or denied
        return result
    }
}
var socket = new logic(new WebSocket("ws://localhost:8000/pool"), new MeRAW(1234, "gamer", "http://example.com"))
socket.onload=()=>{
    console.log("Загрузилися!");
    socket.newRoom("foo", 100).then(e=>{
        console.log("Створили кімнату!",e);
        socket.getInfo().then(f=>{
            console.log("Отримали інфу!",f);
            socket.connect(f.rooms[0].rid).then(g=>{
                console.log("Зайшли в кімнату!", g);
                socket.start(f.rooms[0].rid).then((h)=>{
                    console.log("Отримали",h);
                }).catch((h)=>{
                    console.log("Сука, їбана помилка",h);
                });
            });
        });
    });
}