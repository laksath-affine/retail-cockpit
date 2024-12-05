// Function to send a query to the Flask API
async function sendQuery() {
    // Get the input text
    const query = document.getElementById('textInput').value;

    // Validate input
    if (!query) {
        alert('Please enter a query before submitting.');
        return;
    }

    // API endpoint URL
    const apiUrl = 'http://127.0.0.1:5000/generate_data';

    try {
        // Send POST request to Flask API
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        });

        // Handle the response
        if (response.ok) {
            const data = await response.json();
            console.log('Data received from API:', data);

            // Check if the API response contains a description
            if (data[0] && data[0].description) {
                // Update the HTML content with the description
                document.getElementById('apiResponse').textContent = data[0].description;
            } else {
                document.getElementById('apiResponse').textContent = 'No description available.';
            }
        } else {
            alert(`Error: ${response.statusText}`);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to connect to the API. Please check if the Flask server is running.');
    }
}

// Attach event listener to the Submit button
document.getElementById('submitButton').addEventListener('click', sendQuery);
