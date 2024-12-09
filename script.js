async function sendQuery() {
    const query = document.getElementById('textInput').value;
    // const progressBar = document.getElementById('progressBar');
    const spinner = document.getElementById('loadingSpinner');

    // Simulate a loading progress bar
    // progressBar.style.width = '100%';
    // setTimeout(() => {
    //     progressBar.style.width = '0';
    // }, 2000);

    if (!query) {
        alert('Please enter a query before submitting.');
        return;
    }

    // The local Flask proxy endpoint that will forward requests to the external API
    const apiUrl = 'http://127.0.0.1:5000/generate_data';

    try {
        spinner.style.display = 'block';

        // Send POST request to Flask API
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query }),
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error response from proxy:', errorText);
            alert(`Error: ${response.statusText}`);
            return;
        }

        // Expecting an HTML string from the proxy
        let htmlResponse = await response.text();
        if (htmlResponse.startsWith('"') && htmlResponse.endsWith('"')) {
            htmlResponse = htmlResponse.slice(1, -1);
        }
        htmlResponse = htmlResponse.replace(/\\n/g, '\n').replace(/\\"/g, '"');          
        console.log('HTML Response received:', htmlResponse);

        const responseIframe = document.getElementById('responseIframe');
        responseIframe.srcdoc = htmlResponse;

    } catch (error) {
        console.error('Network or fetch error:', error);
        alert('Failed to connect to the API. Please ensure the Flask server is running.');
    } finally {
        spinner.style.display = 'none';
    }
}

document.getElementById('submitButton').addEventListener('click', sendQuery);

document.addEventListener('DOMContentLoaded', () => {
    const toggleSwitch = document.getElementById('toggleSwitch');
    const formGroup = document.querySelector('.form-group'); 
    const submitButton = document.getElementById('submitButton');
    const dashboardContainer = document.querySelector('.dashboard-container');
    const responseContainer = document.getElementById('responseContainer');

    const toggleChatBotFeatures = () => {
        if (toggleSwitch.checked) {
            // Chatbot is ON
            formGroup.classList.remove('hidden');
            submitButton.classList.remove('hidden');
            responseContainer.classList.remove('hidden');
            dashboardContainer.classList.remove('full-width');
            responseContainer.classList.add('chatbot-on');
        } else {
            // Chatbot is OFF
            formGroup.classList.add('hidden');
            submitButton.classList.add('hidden');
            responseContainer.classList.add('hidden');
            dashboardContainer.classList.add('full-width');
            responseContainer.classList.remove('chatbot-on');
        }
    };

    toggleSwitch.addEventListener('change', toggleChatBotFeatures);
    toggleChatBotFeatures();
});
