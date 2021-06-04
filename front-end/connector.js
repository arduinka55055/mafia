/*
___           ___         ____    ____ ____ ____ ___  ____ ___ ____ ____      |
|__] |__ |   |___ |  |  | |___    |  | |  | |___ |__  |___  |  |___ |    |__  |
|__] |__]|   |___ |__|__| |___    |  | |__| |___ |__] |___  |  |___ |___ |__] .
                        \/                                                    
     ____   __  
\_|  |__|  |__| |__| | /| 
 _| |    | |  |    | |/ |                       


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

TODO: Add to docs
GetTargets
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
    "GetTargets": (rid) => { return { pck: "GetTargets", rid: rid } },
    "Getme": (rid) => { return { pck: "Me", rid: rid } },
    "ClientHello": (rid) => { return { pck: "ClientHello", rid: rid } },
    "MakeRoom": (roomName, count) => { return { pck: "MakeRoom", data: [roomName, count] } },
    "StartGame": (rid) => { return { pck: "StartGame", rid: rid } },
    "Perform": (rid, pid) => { return { pck: "Perform", rid: rid, pid: pid } },
    "Vote": (rid, pid) => { return { pck: "Vote", rid: rid, pid: pid } }
}

function makePacket(meraw, type) {
    return {...packets.GidInject(meraw), ...type };
}
class connector { //this class is more like abstract + WS logic
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

        this.sock.onclose = function(event) {
            if (event.wasClean) {
                alert(`[close] Соединение закрыто чисто, код=${event.code} причина=${event.reason}`);
            } else {
                // например, сервер убил процесс или сеть недоступна
                // обычно в этом случае event.code 1006
                alert('[close] Соединение прервано');
                //TODO:реконнект 
            }
        };

        this.sock.onerror = function(error) {
            alert(`[error] ${error.message}`);
        };
    }
    _consume(data) {
        console.error("NotImplementedConsumePacket!");
    }
    onload() {
        console.error("NotImplementedOnload!");
    }
    send(data) {
        this.sock.send(JSON.stringify(data));
    }
    async get(pck, epck = null) {
        var self = this;
        return new Promise((resolve, reject) => {
            self.sock.addEventListener('message', function shit(e) {
                console.log(e.data);
                var json = JSON.parse(e.data);
                if (json.pck == pck) {
                    resolve(json);
                    this.removeEventListener('message', shit, false);
                } else if (json.pck == "Error") {
                    if (!epck || json.msg == epck) reject(json);
                    this.removeEventListener('message', shit, false);
                }
            });
        });
    }
}

class ReceiverLogic extends connector {
    constructor(sock, meraw) {
        super(sock, meraw);
    }
    onping(e) {
        console.warn("Not Implemented Ping!");
        console.log(e);
    }
    _consume(data) {
        if (data.pck == "GameStarted") {
            console.log("Почалася нова гра за айді:", data.rid);
        } else if (data.pck == "Ping") {
            this.onping(data);
        } else if (data.pck == "GameCast") {
            if (data.type == "DoPerform") {
                console.log("Треба ходити!");
            }
        }
    }
}
class logic extends ReceiverLogic {
    constructor(sock, meraw) {
        super(sock, meraw);
    }
    async newRoom(name, count) {
        this.send(makePacket(this.me, packets.MakeRoom(name, count)));
        return await this.get("MadeRoom");
    }
    async connect(rid) {
        this.send(makePacket(this.me, packets.ClientHello(rid)));
        var result = await this.get("ServerHello", "RoomNotFound");
        return result
    }
    async getInfo() {
        this.send(makePacket(this.me, packets.GetInfo()));
        var result = await this.get("Info");
        return result
    }
    async getTargetInfo(rid) {
        this.send(makePacket(this.me, packets.GetTargets(rid)));
        var result = await this.get("InfoT");
        return result
    }
    async getme(rid) {
        this.send(makePacket(this.me, packets.Getme(rid)));
        var result = await this.get("You");
        return result
    }
    async start(rid) {
        this.send(makePacket(this.me, packets.StartGame(rid)));
        var result = await this.get("GameStartSuccess", "GameStartError"); //too few players or denied
        return result
    }
    async perform(rid, pid) {
        this.send(makePacket(this.me, packets.Perform(rid, pid)));
        var result = await this.get("PerformACK", "PerformError"); //wrong role or player is dead
        return result
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


async function unittest() {
    console.log("Загрузилися!");
    var d = await socket.getInfo()
    if (d.rooms.length == 0) {
        var e = await socket.newRoom("foo", 100)
        console.log("Створили кімнату!", e);
    }
    var f = await socket.getInfo()
    console.log("Отримали інфу!", f);

    var g = await socket.connect(f.rooms[0].rid)
    console.log("Зайшли в кімнату!", g);
    while (d.rooms.length == 0) {
        var ff = await socket.getInfo()
        var a = ff.rooms.length != 0 && ff.rooms[0].players.length >= 6
        if (a) {
            break;
        }
        await new Promise(r => setTimeout(r, 2000));
        console.log("waiting...")
    }
    console.log("вихід з циклу");
    if (d.rooms.length == 0) {
        var h = await socket.start(f.rooms[0].rid);
        console.log("Отримали", h)
    }
    await socket.get("GameCast")
    var me = await socket.getme(f.rooms[0].rid);
    console.warn(me);

    var i = await socket.getTargetInfo(f.rooms[0].rid);
    console.log(i);
    socket.perform(f.rooms[0].rid, i.data[0].id).then((k) => {
        console.log("тип походилось", k)
    }).catch((h) => {
        console.log("Сука, їбана помилка", k);
    });
}
/*
var socket = new logic(new WebSocket("ws://localhost:8000/pool"), new MeRAW(Math.random(), "gamer", "http://example.com"))
socket.onload = () => {
    unittest();
}
*/