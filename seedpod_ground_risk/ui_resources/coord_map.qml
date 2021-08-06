import QtLocation 5.6
import QtPositioning 5.6
import QtQuick 2.0
import QtQuick.Controls 2.0
import QtQuick.Controls.Material 2.0
import QtQuick.Controls.Universal 2.0

Item {
    width: 600
    height: 600

    Map {
        id: map

        anchors.fill: parent
        zoomLevel: 6
        center: QtPositioning.coordinate(53.4822497,-2.2493423)

        MapCircle {
            id: circle
            radius: 50
            border.width: 1
            color: 'green'
        }

        MouseArea {
            id: mouse

            anchors.fill: parent
            onClicked: {
                var pos = map.toCoordinate(Qt.point(mouse.x, mouse.y));
                circle.center = pos;
                controller.update_from_map(pos);
            }
        }

        plugin: Plugin {
            name: "osm"
        }

    }

}