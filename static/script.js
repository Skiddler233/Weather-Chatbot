const socket = io();

function sendMessage() {
    const messageInput = document.getElementById('message');
    const message = messageInput.value;
    if (message.trim() === '') return;

    appendMessage('You: ' + message);
    socket.emit('send_message', { message: message });
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
    messageElement.innerHTML = message;  // Render messages with HTML support
    messageContainer.appendChild(messageElement);
    messageContainer.scrollTop = messageContainer.scrollHeight;
}

// Trigger sendMessage() when Enter is pressed
document.getElementById('message').addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault();  // Prevents the default action of the Enter key
        sendMessage();
    }
});
