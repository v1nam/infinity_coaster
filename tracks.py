from math import sin, cos, pi
from typing import Optional

from direct.showbase.ShowBase import ShowBase
from direct.task.Task import Task
from panda3d.core import Vec3, NodePath, Point3F, ClockObject, Quat


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

        self.ground = self.loader.loadModel("models/ground.bam")
        self.ground.reparentTo(self.render)

        self.tracks = self.generate_loop_tracks(
            num_tracks=40,
            start_pos=Point3F(0, -10, 5),
            del_pitch_deg=10,
            del_heading_deg=1,
            initial_direction=Vec3(0, 1, 0),
        )
        self.tracks.extend(
            self.generate_loop_tracks(
                num_tracks=20,
                start_pos=self.tracks.tail.end_pos,
                del_pitch_deg=0,
                del_heading_deg=0,
                initial_direction=self.tracks.tail.end_pos + Vec3(0, 1, 0),
            )
        )
        self.tracks.extend(
            self.generate_loop_tracks(
                num_tracks=10,
                start_pos=self.tracks.tail.end_pos,
                del_pitch_deg=0,
                del_heading_deg=10,
                initial_direction=self.tracks.tail.end_pos + Vec3(0, 1, 0),
            )
        )
        self.tracks.extend(
            self.generate_loop_tracks(
                num_tracks=10,
                start_pos=self.tracks.tail.end_pos,
                del_pitch_deg=0,
                del_heading_deg=0,
                initial_direction=self.tracks.tail.end_pos + Vec3(-1, 0, 0),
            )
        )

        self.taskMgr.add(self.spin_camera_task, "SpinCameraTask")

    def generate_loop_tracks(
        self,
        num_tracks: int,
        start_pos: Point3F,
        del_pitch_deg: float,
        del_heading_deg: float,
        initial_direction: Vec3,
    ) -> TrackList:

        dummy = NodePath("dummy")
        dummy.setPos(start_pos)
        dummy.lookAt(initial_direction)

        pitch_deg = dummy.get_p()
        pitch = pitch_deg * pi / 180
        heading_deg = dummy.get_h()
        heading = heading_deg * pi / 180

        del_pitch = del_pitch_deg * pi / 180
        del_heading = del_heading_deg * pi / 180

        track_list = TrackList()

        normal_rotation_quat = Quat()
        normal_rotation_quat.setFromAxisAngleRad(del_pitch, Vec3(-1, 0, 0))
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

    def spin_camera_task(self, task):
        angle_degrees = task.time * 40.0
        angle_radians = angle_degrees * (pi / 180.0)
        self.camera.set_pos(50 * sin(angle_radians), -50 * cos(angle_radians), 30)
        self.camera.set_hpr(angle_degrees, -20, 0)
        return Task.cont


if __name__ == "__main__":
    game = Game()
    game.run()
