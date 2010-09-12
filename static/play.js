var ws = null;
$(document).ready(function() {
  ws = new WebSocket("ws://" + window.location.host + "/websocket/" + game_id);

  var play_div = $("#playdiv");
  ws.onopen = function() {  
    play_div.html("<iframe src=\"/static/socketopened.html\"/>");
  };  
  ws.onmessage = function (e) {
    var message = JSON.parse(e.data);
    if (message["type"] == "update") {
      play_div.html(message["html"]);
    } else {
      alert("Unknown message type " + message.type);
    }
  };  
  ws.onclose = function() {
    play_div.html("<iframe src=\"/static/socketclosed.html\"/>");
  };
});
