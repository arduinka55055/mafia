let data = `{
    "нік": "Max",
    "емеіл": "maksikos973@gmail.com"
}`;
//у тебя ровно карточки отображаются? Щас чекну
let jsonToObj = document.querySelector('#btn-jsonToObj');
let objToJson = document.querySelector('#btn-objToJson');
let username = document.querySelector('#username');  
let email = document.querySelector('#email');  

jsonToObj.addEventListener('click', () =>{
     let ourObj = JSON.parse(data);
     username.value = ourObj.username;
     email.value = ourObj.email;  
});

objToJson.addEventListener('click', () =>{
     let ourObj = {};
     ourObj.username = username.value;
     ourObj.email = email.value;     

     let json = JSON.stringify(ourObj)
     document.querySelector('#jsonData').innerText = json;
});
