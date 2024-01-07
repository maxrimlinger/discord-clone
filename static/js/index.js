function auto_scroll_bottom() {
    const chat_list_container = document.getElementById("chat-list-container");
    if (chat_list_container !== null) {
        chat_list_container.scrollTop = chat_list_container.scrollHeight;
    }
}

function m_move_divider(e) {
    e.preventDefault();
    const x = e.clientX;
    if (x >= 150 && x < 600) {
        // normal range
        const grid = document.getElementById("content");
        grid.style["grid-template-columns"] = x + "px 2px 1fr";
    } else if (x >= 20 && x < 150) {
        // snap open
        const grid = document.getElementById("content");
        grid.style["grid-template-columns"] = "150px 2px 1fr";
    } else if (x < 20) {
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

function toggle_message_dialog(id) {
    const dialog = document.getElementById("message-dialog");
    if (dialog.open) {
        dialog.close();
    } else {
        const message = document.getElementById(`${id}-message`)
        const messageRect = message.getBoundingClientRect();

        dialog.style.bottom = `${window.innerHeight - messageRect.y}px`;
        dialog.style.left = "0";
        dialog.show();
    }
}

function setup_message_options_buttons() {
    document.body.addEventListener("click", function() {
        document.getElementById("message-dialog").close();
    })
    const options_buttons = document.getElementsByClassName("options-button")
    for (let i = 0; i < options_buttons.length; i++) {
        options_buttons[i].addEventListener("click", (e) => {
            e.stopPropagation();
            toggle_message_dialog(options_buttons[i].id.slice(0, -15))
        })
    }
}

auto_scroll_bottom();
setup_divider();
setup_message_options_buttons();