document.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        const messageInput = document.getElementById('message');
        const locationSearchInput = document.getElementById('location-search');

        if (document.activeElement === messageInput) {
            event.preventDefault();
            sendMessage();
        } else if (document.activeElement === locationSearchInput) {
            event.preventDefault();
            searchLocation();
        }
    }
});

function searchLocation() {
    const locationName = document.getElementById('location-search').value.trim();
    if (!locationName) return;

    const BASE_URL = 'https://api.openweathermap.org/data/2.5/weather';

    const params = {
        q: locationName,
        appid: API_KEY
    };

    fetch(`${BASE_URL}?q=${encodeURIComponent(locationName)}&appid=${API_KEY}`)
        .then(response => response.json())
        .then(data => {
            if (data.cod === 200) {
                const lat = data.coord.lat;
                const lon = data.coord.lon;

                // Show coordinates and display the "Save" command
                const saveCommand = `save ${locationName.toLowerCase()} ${lat} ${lon}`;
                document.getElementById('coords-output').innerText = `${lat}, ${lon}`;
                document.getElementById('location-coords').style.display = 'block';
                document.getElementById('save-command').innerHTML = `Copy this command to save: <strong>${saveCommand}</strong>`;

                // Dynamically set the click event for the "Copy Command" button
                const copyButton = document.getElementById('copy-coords-button');
                if (copyButton) {
                    copyButton.onclick = function() {
                        copyCoords(saveCommand);
                    };
                } else {
                    console.error('Button with id "copy-coords-button" not found!');
                }
            } else {
                document.getElementById('coords-output').innerText = 'Location not found';
                document.getElementById('location-coords').style.display = 'none';
                document.getElementById('save-command').innerHTML = ''; // Clear the save command if no location is found
            }
        })
        .catch(error => {
            console.error('Error fetching location:', error);
            document.getElementById('coords-output').innerText = 'Error fetching location data';
            document.getElementById('location-coords').style.display = 'none';
            document.getElementById('save-command').innerHTML = ''; // Clear the save command on error
        });
}

const socket = io();

function sendMessage() {
    const messageInput = document.getElementById('message');
    const message = messageInput.value;
    if (message.trim() === '') return;

    appendMessage('You: ' + message);
    socket.emit('send_message', { message });
    messageInput.value = '';
}

socket.on('receive_message', function(data) {
    if (data.error) {
        appendMessage('Error: ' + data.error);
    } else if (data.message) {
        appendMessage('TravelBot: ' + data.message);
    }
});

function appendMessage(message) {
    const messageContainer = document.getElementById('messages');
    const messageElement = document.createElement('div');
    messageElement.innerHTML = message;
    messageContainer.appendChild(messageElement);
    messageContainer.scrollTop = messageContainer.scrollHeight;
}

function copyCoords(command) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(command).then(() => {
            const successMessage = document.getElementById('success-message');
            successMessage.innerText = 'Command copied successfully!';
            successMessage.style.display = 'inline';

            setTimeout(() => {
                successMessage.style.display = 'none';
            }, 3000);
        }).catch(err => {
            console.error('Failed to copy command: ', err);
        });
    } else {
        console.error('Clipboard API not available');
    }
}
