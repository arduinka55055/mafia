const $$ = (selector, node = document) => [...node.querySelectorAll(selector)];

const w = 9; //width (брать со стайлщита)
const h = 22; //height



function getGoogle() {
    var ret = localStorage.getItem("google");
    if (ret == null || ret == "") {
        //window.location.href = "/account";
    }
    return JSON.parse(ret);
}

function genPlayers(count) {
    for (let i = 0; i < count; i++) {
        var user = document.createElement('div')
        user.innerHTML = `
        <div class="name">???</div>
        <img src="img/mafia.png">
        <div class="role"></div>`
        document.querySelector(".G_gameContainer").appendChild(user);
    }
}

function distribute(count) {
    var x = 0; //итератор
    $$(".G_gameContainer>div").forEach(el => {
        var a = 2 * Math.PI * x / count;
        var adder = count % 2 ? Math.PI / count / 2 : 0;
        //стиль = писинус преобразовать из [-1 1] в [- 1]. и помножить на 100%(50 особенность работы) а потом отнять края
        el.style.left = (Math.cos(pisinus(a + adder)) + 1) * 50 * (1 - w / 100) + "%"; //тут эйлер переворачивается
        el.style.top = (1 - Math.sin(pisinus(a + adder))) * 50 * (1 - h / 100) + "%"; //в гробу
        x++;
    })
}

function pisinus(t) {
    var aa = 1;
    var MATH = Math;
    return t + (((aa ** 2) / 8) + ((aa ** 4) / 16) + ((71 * (aa ** 6)) / 2048)) * MATH.sin(2 * t) + ((5 * (aa ** 4)) / 256 + (5 * (aa ** 6)) / 256) * MATH.sin(4 * t) + ((29 * (aa ** 6)) / 6144) * MATH.sin(6 * t);
}


window.addEventListener("DOMContentLoaded", () => {

    const gid = window.location.href.slice(window.location.href.indexOf("?") + 4, window.location.href.indexOf("&"));
    const rid = window.location.href.slice(window.location.href.indexOf("&") + 4);
    var ws = new WebSocket("ws://" + location.host + "/pool");
    window.socket = new logic(ws, new MeRAW(gid + "", getGoogle().name, getGoogle().picture));
    window.socket.onperform = _ => { console.log("треба ходити"); };

    window.socket.onplayercheck = _ => { alert("DONE"); }
    var connflag = true;
    window.socket.onload = _ => {
        window.socket.getInfo().then(e => {
            window.socket.connect(rid);
            connflag = false;
        })
    };

    genPlayers(5);
    genPlayers(5);
    distribute(10);



})