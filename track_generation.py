from math import pi
from typing import Optional, Literal

from direct.showbase.Loader import Loader
from panda3d.core import NodePath, Point3F, Quat, Vec3


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


class TrackCollectionGenerator:
    def __init__(self, render: NodePath, loader: Loader):
        self.render = render
        self.loader = loader

    def _generate_track_collection(
        self,
        num_tracks: int,
        start_pos: Point3F,
        del_pitch_deg: float,
        del_heading_deg: float,
        initial_direction: Vec3,
    ) -> TrackList:

        dummy = NodePath("dummy")
        dummy.lookAt(initial_direction, Vec3(0, 0, 1))

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
            heading_deg += del_heading_deg
            heading += del_heading

        return track_list

    def generate_straight(
        self, start_pos: Point3F, initial_direction: Vec3
    ) -> TrackList:
        return self._generate_track_collection(
            start_pos=start_pos,
            initial_direction=initial_direction,
            num_tracks=10,
            del_pitch_deg=0,
            del_heading_deg=0,
        )

    def generate_ramp(
        self, start_pos: Point3F, initial_direction: Vec3, type_: Literal["up", "down"]
    ) -> TrackList:
        return self._generate_track_collection(
            start_pos=start_pos,
            initial_direction=initial_direction,
            num_tracks=10,
            del_pitch_deg=10 if type_ == "up" else -10,
            del_heading_deg=0,
        )

    def generate_turn(
        self,
        start_pos: Point3F,
        initial_direction: Vec3,
        type_: Literal["left", "right"],
    ) -> TrackList:
        return self._generate_track_collection(
            start_pos=start_pos,
            initial_direction=initial_direction,
            num_tracks=10,
            del_pitch_deg=0,
            del_heading_deg=5 if type_ == "left" else -5,
        )

    def generate_loop(self, start_pos: Point3F, initial_direction: Vec3) -> TrackList:
        loop = self._generate_track_collection(
            start_pos=start_pos,
            initial_direction=initial_direction,
            num_tracks=10,
            del_pitch_deg=10,
            del_heading_deg=1,
        )
        loop.extend(
            self._generate_track_collection(
                start_pos=start_pos,
                initial_direction=initial_direction,
                num_tracks=10,
                del_pitch_deg=10,
                del_heading_deg=-1,
            )
        )
        return loop