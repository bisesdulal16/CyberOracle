document.getElementById("signup-form").addEventListener("submit", async function (e) {
    e.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    try {
        const res = await fetch("/auth/signup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();

        if (!res.ok) {
            alert("Signup failed: " + (data.detail || JSON.stringify(data)));
            return;
        }

        alert("Account created successfully! Please log in.");
        window.location.href = "/login.html";

    } catch (err) {
        alert("Network error — could not reach server.");
        console.error(err);
    }
});
