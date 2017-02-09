var zmq = require('zmq');

module.exports = function(RED) {
  function Subscriber(config) {
    RED.nodes.createNode(this, config);
    var node = this;
    var sock = zmq.socket('sub');

    sock.connect(config.uri);

    if (config.mode === "sub") {
      var tps = config.topics.split(",").map(function(x) {
        return x.trim();
      }).filter(function(x) {
        return x.length > 0;
      }).map(function(x) {
        sock.subscribe(x);
      });
      if (tps.length == 0)
        sock.subscribe("");
    }
    sock.on('message', function() {
      var parts = [];
      for (var i = 0; i < arguments.length; ++i) {
        parts.push(arguments[i].toString());
      }
      var msgDesc = JSON.parse(parts[1]);
      node.send({
        topic: parts[0],
        msgType: msgDesc.msgType,
        sourceUuid: msgDesc.sourceUuid,
        serializationType: msgDesc.serializationType,
        event: parts[2],
        payload: parts[2]
      });
    });
    sock.on('error', function(err) {
      node.error(err);
    });
    node.on('close', function() {
      sock.close();
    });
  }
  RED.nodes.registerType("uniflex-sub", Subscriber);
}
