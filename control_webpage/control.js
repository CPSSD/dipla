var globalConnection;

//-------------------------------------------------------------------------

function initialiseConnection() {
    const serverAddress = getServerAddress();
    const connection = new WebSocket(serverAddress);
    setupButtonHighlighting(connection);
    setupLogging(connection);
    globalConnection = connection;
}

function getServerAddress() {
    const address = document.getElementById("server-address").value;
    const port = document.getElementById("server-port").value;
    return 'ws://' + address + ':' + port;
}

function setupButtonHighlighting(connection) {
    connection.onopen = function() {
        highlightDomElements(["start-server", "stop-server"], true);
        highlightDomElements(["connect"], false);
    };
    connection.onclose = function() {
        highlightDomElements(["start-server", "stop-server"], false);
        highlightDomElements(["connect"], true);
    }
}

function setupLogging(connection) {
    const LOGGING_FUNCTION = console.log;
    connection.onmessage = LOGGING_FUNCTION;
    connection.onerror = LOGGING_FUNCTION;
}

//-------------------------------------------------------------------------

function highlightDomElements(ids, truthiness) {
    ids.map(function(id) {
        return document.getElementById(id);
    }).forEach(function(element) {
        element.disabled = !truthiness;
    });
}

//-------------------------------------------------------------------------

function startServer() {
    globalConnection.send(
        buildLabelledMessage('start_server')
    );
}

function stopServer() {
    globalConnection.send(
        buildLabelledMessage('stop_server')
    );
}

function buildLabelledMessage(label) {
    return JSON.stringify({
        'label': label,
        'data': 'None'
    });
}

//-------------------------------------------------------------------------
