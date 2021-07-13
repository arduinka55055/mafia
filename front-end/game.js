const $$ = (selector, node = document) => [...node.querySelectorAll(selector)];

const w = 9; //width (брать со стайлщита)
const h = 22; //height

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

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
    t.data.forEach(player => {
        var user = document.createElement('div');
        //FIXME: аватаркой можно провести xss атаку*html*/ 
        if (player.role === undefined) player.role = "";
        user.innerHTML = `
        <input type="hidden" value="${player.id}">
        <div class="name">${player.name}</div>
        <img class="ava" src="${player.avatar}"> 
        <div class="role">${player.role}</div>
        <img class="cbg" src="/img/card-back.svg"> 
        `;
        document.querySelector(".G_gameContainer").appendChild(user);
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
    var MATH = Math;
    return t + (((aa ** 2) / 8) + ((aa ** 4) / 16) + ((71 * (aa ** 6)) / 2048)) * MATH.sin(2 * t) + ((5 * (aa ** 4)) / 256 + (5 * (aa ** 6)) / 256) * MATH.sin(4 * t) + ((29 * (aa ** 6)) / 6144) * MATH.sin(6 * t);
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

function chat() {
    socket.sendChat(window.rid, document.querySelector('#text').value);
    document.querySelector('#text').value = '';
}

function onchat(data) {
    document.querySelector('#chat').innerHTML += /*html*/ `
    <span>
    <img src="${data.ava}"/> ${data.nick}: ${data.data}
    </span>`;
    document.querySelector("#chat").scrollTo(0, document.querySelector("#chat").scrollTop);
}
window.addEventListener("DOMContentLoaded", () => {
    test(); //DEBUG:\
    distribute4();
    const gid = window.location.href.slice(window.location.href.indexOf("?") + 4, window.location.href.indexOf("&"));
    const rid = window.location.href.slice(window.location.href.indexOf("&") + 4);
    window.rid = rid;
    var ws = new WebSocket(GetWS());
    window.socket = new logic(ws, new MeRAW(gid + "", getGoogle().name, getGoogle().picture));
    window.socket.onperform = _ => { console.log("треба ходити"); };

    window.socket.onplayercheck = _ => { alert("DONE"); };
    var connflag = true;
    window.socket.onupdate = _ => { loadEssentials(rid); };
    window.socket.onchat = onchat;
    window.socket.onload = () => {
        window.socket.connect(rid).then(() => {
            loadEssentials(rid);

        });
        connflag = false;
    };
});
async function loadEssentials(rid) {
    var targets = await window.socket.getTargetInfo(rid);
    genPlayers(targets);
    distribute(targets.data.length);
    /*{id, role, desc, isKilled} */
    var me = await window.socket.getme(rid);
    console.log(me);
    $$(".G_gameContainer>div").forEach(el => {
        if (el.children[0].value == me.id) {
            el.children[3].innerHTML = me.desc; //FIXME:
            el.classList.add("you");
        }
    });
}

function test() { //DEBUG:
    var fakedata = {
        data: [
            { avatar: "https://lh3.googleusercontent.com/a-/AOh14GjubdFKBR3eLD6pIteIIUdCOTSFF6qbC2XaFUVB=s96-c", id: "123", isKilled: false, name: "gameplayer55" },
            { avatar: "img/doctor.png", id: "123", isKilled: false, name: "Admin" },
            { avatar: "img/doctor.png", id: "123", isKilled: false, name: "maksikos" },
            { avatar: "img/doctor.png", id: "123", isKilled: false, name: "Test4" },
            { avatar: "img/doctor.png", id: "123", isKilled: false, name: "Test5" },
            { avatar: "img/doctor.png", id: "123", isKilled: false, name: "Test6" },
            { avatar: "img/doctor.png", id: "123", isKilled: false, name: "Test1" },
            { avatar: "img/doctor.png", id: "123", isKilled: false, name: "Test2" },
            { avatar: "img/doctor.png", id: "123", isKilled: false, name: "Test3" },
            { avatar: "img/doctor.png", id: "123", isKilled: false, name: "Test4" },
            { avatar: "img/doctor.png", id: "123", isKilled: false, name: "Test5" },
            { avatar: "img/doctor.png", id: "123", isKilled: false, name: "Test1" },
            { avatar: "img/doctor.png", id: "123", isKilled: false, name: "Test2" },
            { avatar: "img/doctor.png", id: "123", isKilled: false, name: "Test3" },
            { avatar: "img/doctor.png", id: "123", isKilled: false, name: "Test4" },
            { avatar: "img/doctor.png", id: "123", isKilled: false, name: "Test5" },
        ]
    };
    genPlayers(fakedata);
    distribute(fakedata.data.length);
}