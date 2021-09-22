import sys
from functools import partial
from math import pi
from typing import Optional

from direct.showbase.ShowBase import ShowBase
from direct.task.Task import Task
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import ClockObject, NodePath, Point3F, Quat, Vec3, WindowProperties


class Track:
    LENGTH = 2

    def __init__(self, direction: Vec3, normal: Vec3, start_pos: Point3F):
        self.direction = direction
        self.normal = normal
        self.next_track = None
        self.prev_track = None
        self.start_pos = start_pos
        self.end_pos = self.start_pos + self.direction * self.LENGTH


class TrackList:
    def __init__(self, head: Optional[Track] = None, tail: Optional[Track] = None):
        self.head = head
        self.tail = tail

    def append(self, track: Track) -> None:
        track.prev_track = self.tail
        if self.tail:
            self.tail.next_track = track
        track.next_track = None
        self.tail = track
        if self.head is None:
            self.head = track

    def extend(self, other: "TrackList") -> None:
        self.tail.next_track = other.head
        other.head.prev_track = self.tail
        self.tail = other.tail


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

        self.set_tracks()

        self.player_node = NodePath("player_node")
        self.player_node.reparentTo(self.render)
        self.player_node.set_pos(self.current_track.start_pos)
        self.camera.reparentTo(self.player_node)
        self.camera.set_pos(self.tracks.head.normal)

        self.track_collections = {
            "straight": partial(
                self.generate_loop_tracks,
                num_tracks=10,
                del_pitch_deg=0,
                del_heading_deg=0,
            ),
            "ramp_up": partial(
                self.generate_loop_tracks,
                num_tracks=10,
                del_pitch_deg=10,
                del_heading_deg=0,
            ),
            "ramp_down": partial(
                self.generate_loop_tracks,
                num_tracks=10,
                del_pitch_deg=-10,
                del_heading_deg=0,
            ),
            "turn_left": partial(
                self.generate_loop_tracks,
                num_tracks=10,
                del_pitch_deg=0,
                del_heading_deg=10,
            ),
            "turn_right": partial(
                self.generate_loop_tracks,
                num_tracks=10,
                del_pitch_deg=0,
                del_heading_deg=-10,
            ),
            "loop": partial(
                self.generate_loop_tracks,
                num_tracks=0,
                del_pitch_deg=0,
                del_heading_deg=-10,
            ),
        }

        icon_bar_x = 1.33333 - 0.1 - 0.2
        self.icons = [
            OnscreenImage(
                image=f"models/{icon_name}_icon.png",
                pos=(icon_bar_x, 0, (i * 2 / 7) - 1),
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
        self.tracks = self.generate_loop_tracks(
            num_tracks=20,
            start_pos=Point3F(0, -10, 5),
            del_pitch_deg=0,
            del_heading_deg=0,
            initial_direction=Vec3(0, 1, 0),
        )

        self.tracks.extend(
            self.generate_loop_tracks(
                num_tracks=40,
                start_pos=self.tracks.tail.end_pos,
                del_pitch_deg=10,
                del_heading_deg=1,
                initial_direction=Vec3(0, 1, 0),
            )
        )
        self.tracks.extend(
            self.generate_loop_tracks(
                num_tracks=20,
                start_pos=self.tracks.tail.end_pos,
                del_pitch_deg=0,
                del_heading_deg=0,
                initial_direction=Vec3(0, 1, 0),
            )
        )
        self.tracks.extend(
            self.generate_loop_tracks(
                num_tracks=10,
                start_pos=self.tracks.tail.end_pos,
                del_pitch_deg=0,
                del_heading_deg=10,
                initial_direction=Vec3(0, 1, 0),
            )
        )
        self.tracks.extend(
            self.generate_loop_tracks(
                num_tracks=10,
                start_pos=self.tracks.tail.end_pos,
                del_pitch_deg=-5,
                del_heading_deg=0,
                initial_direction=Vec3(0, 1, 0),
            )
        )
        self.tracks.extend(
            self.generate_loop_tracks(
                num_tracks=10,
                start_pos=self.tracks.tail.end_pos,
                del_pitch_deg=5,
                del_heading_deg=0,
                initial_direction=Vec3(0, 1, 0),
            )
        )
        self.tracks.extend(
            self.generate_loop_tracks(
                num_tracks=10,
                start_pos=self.tracks.tail.end_pos,
                del_pitch_deg=0,
                del_heading_deg=0,
                initial_direction=Vec3(0, 1, 0),
            )
        )

        self.current_track = self.tracks.head

    def generate_loop_tracks(
        self,
        num_tracks: int,
        start_pos: Point3F,
        del_pitch_deg: float,
        del_heading_deg: float,
        initial_direction: Vec3,
    ) -> TrackList:

        dummy = NodePath("dummy")
        # dummy.setPos(start_pos)
        dummy.lookAt(initial_direction)

        pitch_deg = dummy.get_p()
        pitch = pitch_deg * pi / 180
        heading_deg = dummy.get_h()
        heading = heading_deg * pi / 180

        del_pitch = del_pitch_deg * pi / 180
        del_heading = del_heading_deg * pi / 180

        track_list = TrackList()

        normal_rotation_quat = Quat()
        normal_rotation_quat.setFromAxisAngleRad(-del_pitch, Vec3(-1, 0, 0))
        track_normal = Vec3(0, 0, 1)

        for i in range(num_tracks):
            track_dummy_node = NodePath("track_dummy_node")
            track_dummy_node.reparentTo(self.render)

            track = self.loader.loadModel("models/trackcoloured.bam")
            track.reparentTo(track_dummy_node)
            track.set_pos(0, Track.LENGTH / 2, 0)

            track_dummy_node.set_pos(start_pos)
            track_dummy_node.set_h(heading_deg)
            track_dummy_node.set_p(pitch_deg)

            track_direction = Vec3(
                track.getPos(self.render) - track_dummy_node.getPos(self.render)
            ).normalized()
            track_list.append(
                Track(
                    track_direction, track_normal, track_dummy_node.getPos(self.render)
                )
            )

            start_pos = start_pos + track_direction * Track.LENGTH
            track_normal = normal_rotation_quat.xform(track_normal)
            pitch_deg += del_pitch_deg
            pitch += del_pitch
            if i < num_tracks / 2:
                heading_deg += del_heading_deg
                heading += del_heading
            else:
                heading_deg -= del_heading_deg
                heading -= del_heading

        return track_list

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
