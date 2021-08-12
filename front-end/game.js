const $$ = (selector, node = document) => [...node.querySelectorAll(selector)];
const isDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches; //TODO:


const w = 9; //width (брать со стайлщита)
const h = 22; //height

var sheriffArray = [];

function getGoogle() {
    var ret = localStorage.getItem("google");
    if (ret == null || ret == "") {
        //window.location.href = "/account";
    }
    return JSON.parse(ret);
}
//getTargetInfo
/*
Object { 
​
data: [
    ​​Object{
        avatar: "https://i.imgur.com/Tqfp3MA.png"    ​​​
        id: "3506f266-9b99-4aaf-a257-795a1e70d8c6"
        isKilled: false
    ​​​    name: "Gameplayer 55055"
        }
    ]
    pck: "InfoT"
}
а больше вам знать не положено
*/
function genPlayers(t) {
    document.querySelector(".G_gameContainer").innerHTML = "";
    t.data.forEach(player => {
        console.warn(player);
        var user = document.createElement('div');
        //FIXME: аватаркой можно провести xss атаку*html*/ 
        if (player.role === undefined) player.role = "";
        user.innerHTML = `
        <input type="hidden" value="${player.id}">
        <div class="name">${player.name}</div>
        <img class="ava" src="${player.avatar}"> 
        <div class="role">${player.role}</div>
        <img class="cbg" src="img/card-back.svg"> 
        `;
        user.onclick = e => { select(`${player.id}`); };
        document.querySelector(".G_gameContainer").appendChild(user);

        if (player.isKilled) {
            user.classList.add("dead");
            user.onclick = null;
        }
    });
}


function distribute(count) {
    var x = 0; //итератор
    $$(".G_gameContainer>div").forEach(el => {
        var a = 2 * Math.PI * x / count;
        var adder = count % 2 ? Math.PI / count / 2 : 0;
        //стиль = писинус преобразовать из [-1 1] в [0 1]. и помножить на 100%(50 особенность работы) а потом отнять края
        el.style.left = (Math.cos(pisinus(a + adder)) + 1) * 50 * (1 - w / 100) + "%"; //тут эйлер переворачивается
        el.style.top = (1 - Math.sin(pisinus(a + adder, 1.2))) * 50 * (1 - h / 100) + "%"; //в гробу
        x++;
    });
}

function pisinus(t, aa = 1) {
    return t + (((aa ** 2) / 8) + ((aa ** 4) / 16) + ((71 * (aa ** 6)) / 2048)) * Math.sin(2 * t) + ((5 * (aa ** 4)) / 256 + (5 * (aa ** 6)) / 256) * Math.sin(4 * t) + ((29 * (aa ** 6)) / 6144) * Math.sin(6 * t);
}


function distribute4() {
    el = document.querySelector(".G_chat");
    var adder = Math.PI / 4;

    var x = (Math.cos(pisinus(Math.PI - adder)) + 1) * 50 + w / 2; //тут эйлер переворачивается
    var y = (1 - Math.sin((Math.PI - adder))) * 50 + h / 2; //в гробу

    el.style.left = x + "%";
    el.style.top = y + "%";
    el.style.right = x + "%";
    el.style.bottom = y + "%";
}

function tid2el(tid) {
    for (let e of $$(".G_gameContainer>div")) {
        if (e.children[0].value == tid) return e;
    }
    return null;
}

function select(tid) {
    $$(".G_gameContainer>div").forEach(e => e.classList.remove("selected"));
    tid2el(tid).classList.add("selected");
    sendtarget(tid);
}



function chat() {
    socket.sendChat(window.rid, document.querySelector('#text').value);
    document.querySelector('#text').value = '';
}

function onchat(data) {
    document.querySelector('#chat').innerHTML += /*html*/ `
    <span>
    <img src="${data.ava}"/> ${data.nick}: ${data.data}
    </span>`;
    document.querySelector("#chat").scrollTo(0, document.querySelector("#chat").scrollTopMax);
}
window.addEventListener("DOMContentLoaded", () => {
    test(); //DEBUG:\
    distribute4();
    const gid = window.location.href.slice(window.location.href.indexOf("?") + 4, window.location.href.indexOf("&"));
    const rid = window.location.href.slice(window.location.href.indexOf("&") + 4);
    window.rid = rid;
    var ws = new WebSocket(GetWS());
    window.socket = new logic(ws, new MeRAW(gid + "", getGoogle().name, getGoogle().avatar));

    sendtarget = tid => window.socket.perform(rid, tid); //FIXME:

    window.socket.onperform = _ => {
        sendtarget = tid => window.socket.perform(rid, tid);
    };
    window.socket.onvote = _ => {
        sendtarget = tid => window.socket.vote(rid, tid);
    };

    window.socket.onsheriff = data => {
        var el = tid2el(data.player);
        el.children[3].innerHTML = data.data[1];
        el.classList.add("spy");
        sheriffArray.push([data.player, data.data[1]]);
    };
    window.socket.onplayercheck = () => console.log("DONE"); //DEBUG:
    window.socket.onupdate = () => loadEssentials(rid);
    window.socket.errorDialog = modal;
    window.socket.onchat = onchat;
    window.socket.onload = () => {
        window.socket.connect(rid).then(() => {
            loadEssentials(rid);

        });
    };
    setInterval(() => document.querySelector(".status").innerHTML = window.timer.state + ": " + Math.round(window.timer.timer - Date.now() / 1000) + 'с <span><img src="img/timer.gif"></div></span>', 500);
});


async function loadEssentials(rid) {
    var targets = await window.socket.getTargetInfo(rid);
    genPlayers(targets);
    distribute(targets.data.length);
    sheriffArray.forEach(data => {
        tid2el(data[0]).children[3].innerHTML = data[1];
        tid2el(data[0]).classList.add("spy");
    });

    //FIXME: запрашувати у сервака статус

    /*{id, role, desc, isKilled} */
    var me = await window.socket.getme(rid);
    var el = tid2el(me.id);
    el.children[3].innerHTML = me.desc; //FIXME:
    el.classList.add("you");

    window.timer = await window.socket.getstatus(rid);
    document.querySelector(".status").innerHTML = window.timer.state + ": " + Math.round(window.timer.timer - Date.now() / 1000) + 'с <span><img src="img/timer.gif"></div></span>';
}

async function modal(msg) {
    let toggle = state => {
        document.querySelector("#popup-1").classList.toggle("active", state);
        document.querySelector(".G_gameContainer").classList.toggle("blurred", state);
        document.querySelector(".chat_window").classList.toggle("blurred", state);
    };
    toggle(true);
    document.querySelector("#popup-1 h1").innerHTML = msg;

    return new Promise((resolve, reject) => {
        document.querySelector("#popup-1 .close-btn").addEventListener('click', function shit(e) {
            resolve(false);
            toggle(false);
            this.removeEventListener('click', shit, false);
        });
        document.querySelector("#popup-1 button").addEventListener('click', function shit(e) {
            resolve(true);
            toggle(false);
            this.removeEventListener('click', shit, false);
        });
    });
}

function test() { //DEBUG:
    var fakedata = {
        data: [
            { avatar: "https://lh3.googleusercontent.com/a-/AOh14GjubdFKBR3eLD6pIteIIUdCOTSFF6qbC2XaFUVB=s96-c", id: "123", isKilled: false, name: "gameplayer55" },
            { avatar: "img/doctor.png", id: "1", isKilled: false, name: "Admin" },
            { avatar: "img/doctor.png", id: "2", isKilled: false, name: "maksikos" },
            { avatar: "img/doctor.png", id: "3", isKilled: false, name: "Test4" },
            { avatar: "img/doctor.png", id: "4", isKilled: false, name: "Test5" },
            { avatar: "img/doctor.png", id: "5", isKilled: false, name: "Test6" },
            { avatar: "img/doctor.png", id: "6", isKilled: false, name: "Test1" },
            { avatar: "img/doctor.png", id: "7", isKilled: false, name: "Test2" },
            { avatar: "img/doctor.png", id: "8", isKilled: false, name: "Test3" },
            { avatar: "img/doctor.png", id: "9", isKilled: false, name: "Test4" },
            { avatar: "img/doctor.png", id: "10", isKilled: false, name: "Test5" },
            { avatar: "img/doctor.png", id: "11", isKilled: false, name: "Test1" },
            { avatar: "img/doctor.png", id: "12", isKilled: false, name: "Test2" },
            { avatar: "img/doctor.png", id: "13", isKilled: false, name: "Test3" },
            { avatar: "img/doctor.png", id: "14", isKilled: false, name: "Test4" },
            { avatar: "img/doctor.png", id: "15", isKilled: false, name: "Test5" },
        ]
    };
    genPlayers(fakedata);
    distribute(fakedata.data.length);
    var el = $$(".G_gameContainer>div")[0];
    el.children[3].innerHTML = "мафія"; //FIXME:
    el.classList.add("you");
    el.onclick = e => { e.preventDefault(); };
    el = $$(".G_gameContainer>div")[1];
    el.children[3].innerHTML = "шериф"; //FIXME:
    el.classList.add("dead");
    el.onclick = e => { e.preventDefault(); };
}