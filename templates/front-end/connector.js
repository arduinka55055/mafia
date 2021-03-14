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
    "GetRooms": () => { return { pck: "GetRooms" } },
    "GetInfo": (rid) => { return { pck: "GetInfo", data: { rid: rid } }; },
    "ClientHello": (rid, gid, nick, avatar) => { return { pck: "ClientHello", data: { rid: rid, gid: gid, nick: nick, avatar: avatar } }; },
    "Perform": (rid, gid, pid) => { return { pck: "Perform", data: { rid: rid, gid: gid, pid: pid } }; },
    "Vote": (rid, gid, pid) => { return { pck: "Vote", data: { rid: rid, gid: gid, pid: pid } }; }
}
class connector {
    constructor(sock, meraw) {
        this.sock = sock
        this.me = meraw;

        this.sock.onopen = (e) => {
            console.log("[open] Соединение установлено");
            console.log("Отправляем данные на сервер");
            this.sock.send("Меня зовут Джон");
        }

        this.sock.onmessage = function (event) {
            alert(`[message] Данные получены с сервера: ${event.data}`);
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
    getInfo(rid, callback) {
        this.sock.send(JSON.stringify(packets.GetInfo(rid)));
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

let socket = new connector(new WebSocket("ws://localhost:8000/pool"), new MeRAW(1234, "gamer", "http://example.com"))

