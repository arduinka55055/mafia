const signInBtn = document.querySelector("#signin-btn");
const signUpBtn = document.querySelector("#signup-btn");
const pidorskiyContainer = document.querySelector(".container");


signUpBtn.addEventListener('click', () => {
	pidorskiyContainer.classList.add("signup-mode")
});

signInBtn.addEventListener('click', () => {
	pidorskiyContainer.classList.remove("signup-mode")
});