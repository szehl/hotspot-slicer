var zmq = require('zmq');

module.exports = function(RED) {
  function Publisher(config) {
    RED.nodes.createNode(this, config);
    var node = this;
    var sock = zmq.socket(config.mode);

    if (config.server) {
      sock.bindSync(config.uri);
    } else {
      sock.connect(config.uri);
    }
    sock.on('error', function(err) {
      node.error(err);
    });
    node.on('close', function() {
      sock.close();
    });
    node.on('input', function(msg) {
      var payload = [];
      var topic = msg.topic;
      if (!topic) return;
      var msgType = msg.msgType;
      if (!msgType) return;
      var sourceUuid = msg.sourceUuid;
      if (!sourceUuid) return;
      var serializationType = msg.serializationType
      if (!serializationType) return;
      var event = msg.event
      if (!event) return;

      //Create and serialize Message Description
      var msgDesc = {"msgType": msgType,
                     "sourceUuid": sourceUuid,
                     "serializationType": msg.serializationType };
      msgDesc = JSON.stringify(msgDesc);
      //Set payload list (with proper ordering!)
      payload = [topic, msgDesc, event];
      sock.send(payload);
    });
  }
  RED.nodes.registerType("uniflex-pub", Publisher);
}
