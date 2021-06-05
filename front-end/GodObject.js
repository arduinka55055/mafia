//global vars. как же без них?
window.gdata = null;
window.pinger = null;

function getGoogle() {
    var ret = localStorage.getItem("google");
    if (ret == null || ret == "") {
        //window.location.href = "/account";
    }
    return JSON.parse(ret);
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

function OnPingFunc(data) {
    var time = Math.round(Date.now() / 1000 - data.timestamp);
    document.querySelector(".G_ping").innerHTML = time + " ms";
    document.querySelector(".G_players").innerHTML = data.players;
    document.querySelector(".G_rooms").innerHTML = data.rooms;
}

function updateRooms() {
    /*
    rooms: Array(13) [ {…}, {…}, {…}, … ]​​
    0: Object { rid: "1b3e2f48-4cba-432b-86a6-23d8d32cd004", name: "shit", isStarted: false, … }
    isStarted: false
    name: "shit"
    players: Array []
    rid: "1b3e2f48-4cba-432b-86a6-23d8d32cd004" */

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
        console.log(newrooms);
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
                    })

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
    document.querySelector(".G_ava").src = getGoogle().picture;
    document.querySelector(".G_nick").innerHTML = getGoogle().name;
    //http://ip-api.com/json
    getGeoIP().then(region => { document.querySelector(".G_geo").innerHTML = region; });
    window.socket = new logic(new WebSocket("ws://" + location.host + "/pool"), new MeRAW(getGoogle().id, getGoogle().name, getGoogle().picture));
    window.socket.onping = OnPingFunc;

    setInterval(updateRooms, 3000);
}



document.addEventListener("DOMContentLoaded", loadEssentials);