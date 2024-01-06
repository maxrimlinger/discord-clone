// prevent the google sign-in button from actually doing google sign-in
document.querySelector(".g_id_signin").addEventListener("click", function(e) {
    e.preventDefault();
    window.location.href = "/login";
}, true);
