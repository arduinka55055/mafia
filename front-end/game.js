const $$ = (selector, node = document) => [...node.querySelectorAll(selector)];
        const hw = 12.6; //halfwidth (брать со стайлщита)
        const hh = 10; //halfheight
        var count = 8; //количество карточек
        var x = 0; //итератор

        window.addEventListener("DOMContentLoaded", () => {

            $$(".G_gameContainer>div").forEach(el => {
                var a = 2 * Math.PI * x / count;
                //стиль = писинус преобразовать из [-1 1] в [- 1]. и помножить на 100%(50 особенность работы) а потом отнять края
                el.style.left = (Math.cos(a) + 1.1) * 50 * (1 - hw / 50) + "%"; //тут эйлер переворачивается
                el.style.top = (1.1 - Math.sin(a)) * 50 * (1 - hh / 50) + "%"; //в гробу
                x++;
            })

        })

function toggle(){
    let blur = document.getElementById('blur');
    blur.classList.toggle('active');
    let popup = document.getElementById('popup');
    popup.classList.toggle('active');
}        