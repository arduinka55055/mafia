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
|ClientHello ------------>   | #sending PlayerRAW
|  <------------- ServerHello| #receiving ok status, client in list, start pinging
|(periodical GetInfo)        |
|                            |
|          Game start        |
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
    "ClientHello": (rid) => { return { pck: "ClientHello", rid: rid, avatar: avatar } },
    "MakeRoom": (roomName, count) => { return { pck: "MakeRoom", data: [roomName, count] } },
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
            console.log("[open] Соединение установлено");
            console.log("Отправляем данные на сервер");
            this.sock.send(JSON.stringify(makePacket(this.me)));
        }
        this.sock.onping = (e) => {
            console.log(e);
        }
        this.sock.onmessage = function (event) {
            console.log(event.data);
            this.consume(JSON.parse(event.data));
            console.log(`[message] Данные получены с сервера: ${event.data}`);
        };

        this.sock.onclose = function (event) {
            if (event.wasClean) {
                alert(`[close] Соединение закрыто чисто, код=${event.code} причина=${event.reason}`);
            } else {
                // например, сервер убил процесс или сеть недоступна
                // обычно в этом случае event.code 1006
                alert('[close] Соединение прервано');
            }
        };

        this.sock.onerror = function (error) {
            alert(`[error] ${error.message}`);
        };
    }
    consume(data) {
        console.error("NotImplementedConsumePacket!")
    }
    send(data) {
        this.sock.send(JSON.stringify(data));
    }
    get(data,id) {
        return new Promise(function () {

            var id =(e)=>{console.log(e);};
            this.sock.addEventListener("message",id)
            this.consume(data);
        });
    }
}
/*
function connect() {
    return new Promise(function(resolve, reject) {
        var server = new WebSocket('ws://mysite:1234');
        server.onopen = function() {
            resolve(server);
        };
        server.onerror = function(err) {
            reject(err);
        };

    });
}
*/
class ReceiverLogic extends connector {
    constructor(sock, meraw) {
        super(sock, meraw);
    }
    consume(data) {
        data = JSON.parse(data);
        console.warn("data");//ackRoomID
        if (data.pck == "aRID") {
            return
        }
        else if (data.pck == "RSV") { }
        else if (data.pck == "RSV") { }
        else if (data.pck == "RSV") { }
        else { console.warn("Unknown type packet received!"); }
    }
}
class logic extends ReceiverLogic {
    constructor(sock, meraw) {
        super(sock, meraw);
    }
    async newRoom(name, count) {
        this.send(makePacket(this.me, packets.MakeRoom(name, count)));
        return await 
    }
    getInfo(rid) {
        this.send(makePacket(this.me, packets.GetInfo(rid)));
    }
}
/*
class Employee extends Person {
    constructor(name, salary) {
        super(name);
        this.salary = salary;
    }
}

const p1 = new Person('Nick');
// теперь можно сделать следующее:
console.log(
    `name: ${p1.name}`,
    `eyes: ${p1.eyes}`,
    `mouth: ${p1.mouth}`,
    p1.sleep()
);
*/

var socket = new logic(new WebSocket("ws://localhost:8000/pool"), new MeRAW(1234, "gamer", "http://example.com"))
var gid = socket.newRoom("foo", 100);
socket.getInfo();
socket.connect(gid);