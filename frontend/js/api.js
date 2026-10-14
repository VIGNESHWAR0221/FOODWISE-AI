
const API_URL = "https://foodwise-ai-backend.onrender.com";
async function api(path, options = {}) {
    const response = await fetch(`${API_URL}${path}`, {
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
