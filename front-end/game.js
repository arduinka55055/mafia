const $$ = (selector, node = document) => [...node.querySelectorAll(selector)];
        const hw = 4.5; //halfwidth (брать со стайлщита)
        const hh = 11; //halfheight
        var count = 8; //количество карточек
        var x = 0; //итератор

        window.addEventListener("DOMContentLoaded", () => {

            $$(".G_gameContainer>div").forEach(el => {
                var a = 2 * Math.PI * x / count;
                //стиль = писинус преобразовать из [-1 1] в [- 1]. и помножить на 100%(50 особенность работы) а потом отнять края
                el.style.left = (Math.cos(a) + 1) * 50 * (1 - hw / 50) + "%"; //тут эйлер переворачивается
                el.style.top = (1 - Math.sin(a)) * 50 * (1 - hh / 50) + "%"; //в гробу
                x++;
            })

        })