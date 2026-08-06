const API = "http://127.0.0.1:5000/api";

async function loginPlayer(name, email) {
    try {
        const response = await fetch(`${API}/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: name,
                email: email
            })
        });

        return await response.json();

    } catch (err) {
        console.error(err);
        alert("Cannot connect to the backend.");
        return null;
    }
}