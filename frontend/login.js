document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    let username = sanitize(document.getElementById("username").value);
    let password = sanitize(document.getElementById("password").value);

    if (!username || !password) {
        displayError("Fields cannot be empty");
        return;
    }

    try {
        let response = await fetch("http://127.0.0.1:8000/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
        });

        let data = await response.json();

        if (!response.ok) {
            displayError(data.detail);
            return;
        }

        // Save token & role
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("role", data.role);

        loadDashboard();

    } catch (err) {
        displayError("Server unreachable.");
    }
});

function sanitize(str) {
    return str.replace(/[<>$;]/g, "");
}

function displayError(msg) {
    document.getElementById("error-msg").textContent = msg;
}

function loadDashboard() {
    document.getElementById("login-container").classList.add("hidden");
    document.getElementById("dashboard").classList.remove("hidden");

    document.getElementById("welcome").textContent = `Welcome!`;
    document.getElementById("role").textContent = localStorage.getItem("role");
}

document.getElementById("logout").addEventListener("click", () => {
    localStorage.clear();
    location.reload();
});
