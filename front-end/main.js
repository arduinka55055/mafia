//import Vue from '/static/vue.min.js';


document.addEventListener("DOMContentLoaded", () => {
    window.app = new Vue({
        el: '.rooms',
        data: {
            message: 'Hello Vue!'
        }
    })
    app.data.message = "петух"
})