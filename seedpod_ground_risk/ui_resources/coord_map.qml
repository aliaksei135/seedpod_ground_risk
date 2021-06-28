import QtLocation 5.15
import QtQuick 2.15

Item {
    width: 400
    height: 400

    Map {
        id: map

        anchors.fill: parent
        zoomLevel: 14

        MouseArea {
            id: mouse
            anchors.fill: parent
            onClicked: controller.update_from_map(map.toCoordinate(Qt.point(mouse.x, mouse.y)))
        }

        plugin: Plugin {
            name: "osm"
        }

    }

}