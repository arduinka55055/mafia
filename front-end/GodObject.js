//global vars. как же без них?
window.gdata = null;
window.pinger = null;

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function noescape(val) {
    if (val.indexOf('\\') === -1) {
        return val; // not encoded
    }
    val = val.slice(1, -1).replace(/\\"/g, '"');
    val = val.replace(/\\(\d{3})/g, function(match, octal) {
        return String.fromCharCode(parseInt(octal, 8));
    });
    return val.replace(/\\\\/g, '\\');
}

function getGoogle() {
    try {

        var ret = noescape(getCookie("google").substr(0)) + '"}';
        localStorage.setItem("google", ret);
        return JSON.parse(ret);
    } catch (e) {
        window.location.href = "/login";
    }
}

function getGeoIP() {
    return new Promise((resolve, reject) => {
        let xhr = new XMLHttpRequest();
        xhr.open('GET', 'http://ip-api.com/json');
        xhr.responseType = 'json';
        xhr.onload = function() {
            let responseObj = xhr.response;
            resolve(xhr.response.country);
        };
        xhr.onerror = reject;
        xhr.send();
    });
}


function updateRooms() {
    /*
    rooms: Array(13) [ {…}, {…}, {…}, … ]​​
    0: Object { rid: "1b3e2f48-4cba-432b-86a6-23d8d32cd004", name: "shit", isStarted: false, … }
    isStarted: false
    name: "shit"
    players: Array []
    rid: "1b3e2f48-4cba-432b-86a6-23d8d32cd004" 
    timestamp: 1625064372.792588
    players:12
    */
    window.socket.getInfo().then(data => {
        var newrooms = "";
        data.rooms.forEach(room => {
            var htmltext = `
            <tr onclick="window.socket.connect('${room.rid}'); window.currentRoom = '${room.rid}';">
            <td>${room.name}</td>
            <td>${room.players.length}/${room.maxplayers}</td>
            <td><span class="status ${room.isStarted ? 'closed' : 'inviting'}">${room.isStarted ? 'Закрито' : 'Йде набір'}</span></td>
            </tr>
            `;
            newrooms += htmltext;
        });

        document.querySelector(".G_rooms").innerHTML = data.rooms.length;
        document.querySelector(".G_players").innerHTML = data.players;
        document.querySelector(".G_roomlist").innerHTML = newrooms;

        var newplayers = "";
        if (window.currentRoom) {
            data.rooms.forEach(room => {

                if (room.rid + "" == window.currentRoom + "") {
                    room.players.forEach(player => {
                        var htmltext = `
                        <tr>
                        <td width="60px"><div class="imgBx"><img src="${player[1]}"></div></td>
                        <td><h4>${player[0]}</h4></td>  
                        </tr> 
                        `;
                        newplayers += htmltext;
                    });

                }
            });
        }

        document.querySelector(".G_playerlist").innerHTML = newplayers;
    });
}

function loadEssentials() {
    //я заебусь настраивать гугл, да и на серве тоже нужен гугл айди
    //получу их из хитровыебанного костыля
    console.log(getGoogle());
    document.querySelector(".G_ava").src = getGoogle().avatar;
    document.querySelector(".G_nick").innerHTML = getGoogle().name;
    //http://ip-api.com/json
    getGeoIP().then(region => { document.querySelector(".G_geo").innerHTML = region; });
    window.rnd = Math.random();
    window.socket = new logic(new WebSocket(GetWS()), new MeRAW(window.rnd + "", getGoogle().name, getGoogle().avatar));
    window.socket.onnewgame = rid => { if (rid == window.currentRoom) { window.location.href = "game.html?id=" + window.rnd + "&rd=" + window.currentRoom; } };
    window.socket.onping = e => { document.querySelector(".G_ping").innerHTML = Math.round(e) + " ms"; };
    updateRooms();
    setInterval(updateRooms, 3000);
}



document.addEventListener("DOMContentLoaded", loadEssentials);