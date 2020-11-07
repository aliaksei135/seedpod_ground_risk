var backend = null;
window.onload = function () {
    new QWebChannel(qt.webChannelTransport, function (channel) {
        backend = channel.objects.backend;
    });
}

window.onload = function () {
    var last_script = document.createElement("script")
    last_script.innerHTML = "function onMapMove() { \
        backend.on_map_move(the_map.getCenter().lat, the_map.getCenter().lng); \
        alert(\"Move\"); \
        the_map.on('move', onMapMove); \
        onMapMove();";
};