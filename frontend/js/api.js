
const API_URL = "https://foodwise-ai1-backend.onrender.com";
async function api(path, options = {}) {
const apiPath = path.startsWith("/api/") || path === "/api"
    ? path
    : `/api${path.startsWith("/") ? path : "/" + path}`;

const response = await fetch(`${API_URL}${apiPath}`, {
    ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
            `API Error (${response.status}): ${errorText}`
        );
    }

    if (response.status === 204) {
        return null;
    }

    return response.json();
}
