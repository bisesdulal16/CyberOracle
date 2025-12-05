document.getElementById("login-form").addEventListener("submit", async function (e) {
    e.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    try {
        const res = await fetch("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: formData
        });

        const data = await res.json();

        if (!res.ok) {
            alert("Login failed: " + (data.detail || "Unknown error"));
            return;
        }

        // store the token
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("role", data.role);

        // redirect based on role
        if (data.role === "admin") {
            window.location.href = "/dashboard_admin.html";
        } else {
            window.location.href = "/dashboard_user.html";
        }

    } catch (err) {
        alert("Network error — could not reach server.");
        console.error(err);
    }
});

