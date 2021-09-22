import sys
from functools import partial

from direct.gui.OnscreenImage import OnscreenImage
from direct.showbase.ShowBase import ShowBase
from direct.task.Task import Task
from panda3d.core import ClockObject, NodePath, Point3F, Vec3, WindowProperties

from track_generation import Track, TrackCollectionGenerator


class Game(ShowBase):
    def __init__(self):
        super().__init__()
        self.disable_mouse()
        props = WindowProperties()
        props.setCursorHidden(True)
        base.win.requestProperties(props)

        self.speed = 12

        self.ground = self.loader.loadModel("models/ground.bam")
        self.ground.reparentTo(self.render)

        self.track_generator = TrackCollectionGenerator(self.render, self.loader)

        self.set_tracks()

        self.player_node = NodePath("player_node")
        self.player_node.reparentTo(self.render)
        self.player_node.set_pos(self.current_track.start_pos)
        self.camera.reparentTo(self.player_node)
        self.camera.set_pos(self.tracks.head.normal)

        self.track_collections = {
            "straight": self.track_generator.generate_straight,
            "ramp_up": partial(self.track_generator.generate_ramp, type_="up"),
            "ramp_down": partial(self.track_generator.generate_ramp, type_="down"),
            "turn_left": partial(self.track_generator.generate_turn, type_="left"),
            "turn_right": partial(self.track_generator.generate_turn, type_="right"),
            "loop": self.track_generator.generate_loop,
        }

        icon_bar_x = 1.33333 - 0.1 - 0.2
        self.icons = [
            OnscreenImage(
                image=f"models/{icon_name}_icon.png",
                pos=(icon_bar_x, 0, ((7 - i) * 2 / 7) - 1),
                scale=(0.1, 1, 0.1),
            )
            for i, icon_name in enumerate(self.track_collections.keys(), start=1)
        ]

        self.center = []
        self.set_center()
        self.rot_v = 0
        self.rot_h = 0
        self.mouse_sensitivity = 30

        self.taskMgr.add(self.move_player_task, "MovePlayerTask")
        self.accept("aspectRatioChanged", self.set_center)
        self.accept("escape", sys.exit)

        for i, collection in enumerate(self.track_collections.keys(), start=1):
            self.accept(str(i), self.place_track, [collection])

    def place_track(self, collection):
        print(collection)
        new_tracks = self.track_collections[collection](
            start_pos=self.tracks.tail.end_pos,
            initial_direction=self.tracks.tail.direction,
        )
        self.tracks.extend(new_tracks)

    def set_tracks(self):
        self.tracks = self.track_generator.generate_straight(
            start_pos=Point3F(0, -10, 5), initial_direction=Vec3(0, 1, 0)
        )
        self.current_track = self.tracks.head

    def move_player_task(self, _task):
        dt = ClockObject.getGlobalClock().dt

        if (
            self.player_node.get_pos() - self.current_track.start_pos
        ).length() > Track.LENGTH and self.current_track.next_track is not None:
            self.current_track = self.current_track.next_track

        self.player_node.set_pos(
            self.player_node.get_pos() + self.current_track.direction * self.speed * dt
        )
        self.camera.set_pos(self.current_track.normal * 2)

        if base.mouseWatcherNode.hasMouse():
            mx = base.mouseWatcherNode.getMouseX()
            my = base.mouseWatcherNode.getMouseY()
            self.rot_h += -1 * self.mouse_sensitivity * mx
            self.rot_v += self.mouse_sensitivity * my
            self.rot_v = max(-90, self.rot_v)
            self.rot_v = min(90, self.rot_v)
            self.camera.setHpr(self.rot_h, self.rot_v, 0)
        base.win.movePointer(0, self.center[0], self.center[1])
        return Task.cont

    def set_center(self):
        self.center = [base.win.getXSize() // 2, base.win.getYSize() // 2]


if __name__ == "__main__":
    game = Game()
    game.run()
