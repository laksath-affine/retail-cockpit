// Function to send a query to the Flask API
async function sendQuery() {
    // Get the input text
    const query = document.getElementById('textInput').value;

    // Get the spinner element
    const spinner = document.getElementById('loadingSpinner');

    const progressBar = document.getElementById('progressBar');
    progressBar.style.width = '100%'; // Simulate loading
    setTimeout(() => {
        progressBar.style.width = '0'; // Reset
    }, 2000);

    // Validate input
    if (!query) {
        alert('Please enter a query before submitting.');
        return;
    }

    // API endpoint URL
    const apiUrl = 'http://127.0.0.1:5000/generate_data';

    try {
        // Show spinner before making the API call
        spinner.style.display = 'block';

        // Send POST request to Flask API
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query }),
        });

        // Handle the response
        if (response.ok) {
            const data = await response.json();
            console.log('Data received from API:', data);

            // Check if the API response contains a description
            if (data[0] && data[0].description) {
                // Update the HTML content with the description
                document.getElementById('apiResponse').textContent = data[0].description;

                // Display the image if the API provides an image URL
                if (data[0].image_path) {
                    const imagePath = data[0].image_path;
                    const imageContainer = document.getElementById('imageContainer');
                    const responseImage = document.getElementById('responseImage');

                    responseImage.src = imagePath; // Set the image source
                    imageContainer.style.display = 'flex'; // Make the image container visible
                } else {
                    alert('No image available.');
                }
            } else {
                document.getElementById('apiResponse').textContent = 'No description available.';
            }
        } else {
            document.getElementById('apiResponse').textContent = `Error: ${response.statusText}`;
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to connect to the API. Please check if the Flask server is running.');
    } finally {
        // Hide spinner after the API call completes (success or failure)
        spinner.style.display = 'none';
    }
}

// Attach event listener to the Submit button
document.getElementById('submitButton').addEventListener('click', sendQuery);

document.addEventListener('DOMContentLoaded', () => {
    // Get the toggle switch, form group, submit button, dashboard container, and response container
    const toggleSwitch = document.getElementById('toggleSwitch');
    const formGroup = document.querySelector('.form-group'); // Parent of the textbox
    const submitButton = document.getElementById('submitButton');
    const dashboardContainer = document.querySelector('.dashboard-container');
    const responseContainer = document.getElementById('responseContainer');

    // Function to toggle visibility and adjust widths
    const toggleChatBotFeatures = () => {
        if (toggleSwitch.checked) {
            // Chatbot is ON
            formGroup.classList.remove('hidden');
            submitButton.classList.remove('hidden');
            responseContainer.classList.remove('hidden');
            dashboardContainer.classList.remove('full-width'); // Restore original width
        } else {
            // Chatbot is OFF
            formGroup.classList.add('hidden');
            submitButton.classList.add('hidden');
            responseContainer.classList.add('hidden');
            dashboardContainer.classList.add('full-width'); // Take full width
        }
    };

    // Attach event listener to the toggle switch
    toggleSwitch.addEventListener('change', toggleChatBotFeatures);

    // Initialize the state on page load
    toggleChatBotFeatures();
});