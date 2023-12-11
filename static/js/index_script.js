function onSignIn(googleUser) {
    var profile = googleUser.getBasicProfile();
    console.log('ID: ' + profile.getId()); // Do not send to your backend! Use an ID token instead.
    console.log('Name: ' + profile.getName());
    console.log('Image URL: ' + profile.getImageUrl());
    console.log('Email: ' + profile.getEmail()); // This is null if the 'email' scope is not present.
}

function signOut() {
    var auth2 = gapi.auth2.getAuthInstance();
    auth2.signOut().then(function () {
      console.log('User signed out.');
    });
}

function auto_scroll_bottom() {
    const chat_list_container = document.getElementById("chat-list-container");
    if (chat_list_container !== null) {
        chat_list_container.scrollTop = chat_list_container.scrollHeight;
    }
}

function show_ellipses_menu(element) {
    const dialog = document.querySelector("#chat-list-container dialog");
    if (dialog.open) {
        dialog.close();
    } else {
        dialog.show();
    }
}

function m_move_divider(e) {
    e.preventDefault();
    const x = e.clientX;
    if (x >= 150 && x < 400) {
        // normal range
        const grid = document.getElementById("content");
        grid.style["grid-template-columns"] = x + "px 2px 1fr";
    } else if (x >= 10 && x < 150) {
        // snap open
        const grid = document.getElementById("content");
        grid.style["grid-template-columns"] = "150px 2px 1fr";
    } else if (x < 10) {
        // snap closed
        const grid = document.getElementById("content");
        grid.style["grid-template-columns"] = "0px 2px 1fr";
    }
}

function m_down_divider(e) {
    e.preventDefault();
    document.addEventListener("mousemove", m_move_divider, true);
}

function m_up_divider(e) {
    e.preventDefault();
    document.removeEventListener("mousemove", m_move_divider, true);
}

function setup_divider() {  
    const divider = document.getElementById("pane-divider");
    divider.addEventListener("mousedown", m_down_divider, true);
    document.addEventListener("mouseup", m_up_divider, true);
}

auto_scroll_bottom();
setup_divider();