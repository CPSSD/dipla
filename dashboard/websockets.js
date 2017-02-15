var s = new WebSocket("ws://localhost:8766");
s.onmessage = function(t){ alert(t); };
s.send("Yo I'm a client");
