from math import pi
from typing import Optional, Literal
import random

from direct.showbase.Loader import Loader
from panda3d.core import NodePath, Point3F, Quat, Vec3


class Track:
    LENGTH = 2

    def __init__(
        self, direction: Vec3, normal: Vec3, start_pos: Point3F, node_path: NodePath
    ):
        self.direction = direction
        self.normal = normal
        self.next_track = None
        self.start_pos = start_pos
        self.end_pos = self.start_pos + self.direction * self.LENGTH
        self.node_path = node_path


class TrackList:
    def __init__(
        self,
        head: Optional[Track] = None,
        tail: Optional[Track] = None,
        maxlen: Optional[int] = None,
    ):
        self.maxlen = maxlen
        self._len = 0
        self.head = head
        self.tail = tail

    def append(self, track: Track) -> None:
        self._len += 1
        if self.tail:
            self.tail.next_track = track
        track.next_track = None
        self.tail = track
        if self.head is None:
            self.head = track
        if self.maxlen is not None and len(self) > self.maxlen:
            self.popleft()

    def extend(self, other: "TrackList") -> None:
        self._len += len(other)
        if self.tail:
            self.tail.next_track = other.head
        if self.head is None:
            self.head = other.head
        self.tail = other.tail
        while self.maxlen is not None and len(self) > self.maxlen:
            self.popleft()

    def popleft(self) -> None:
        if self.head is None:
            raise IndexError("Empty track list")
        self._len -= 1
        head = self.head
        self.head = self.head.next_track
        head.node_path.remove_node()

    def __iter__(self):
        current = self.head
        while current is not None:
            yield current
            current = current.next_track

    def __len__(self):
        return self._len


class TrackCollectionGenerator:
    def __init__(self, render: NodePath, loader: Loader):
        self.render = render
        self.loader = loader
        self.total_tracks_placed = 0

    def _generate_track_collection(
        self,
        num_tracks: int,
        start_pos: Point3F,
        del_pitch_deg: float,
        del_heading_deg: float,
        initial_heading: float,
        is_loop: bool = False,
    ) -> TrackList:

        pitch_deg = 0
        pitch = pitch_deg * pi / 180
        heading_deg = initial_heading % 360
        heading = heading_deg * pi / 180

        del_pitch = del_pitch_deg * pi / 180
        del_heading = del_heading_deg * pi / 180

        track_list = TrackList()

        normal_rotation_quat = Quat()
        normal_rotation_quat.setFromAxisAngleRad(
            del_pitch,
            {
                0.0: Vec3(1, 0, 0),
                90.0: Vec3(0, 1, 0),
                180.0: Vec3(-1, 0, 0),
                270.0: Vec3(0, -1, 0),
            }[heading_deg],
        )
        track_normal = Vec3(0, 0, 1)

        for i in range(num_tracks):
            self.total_tracks_placed += 1
            track_dummy_node = NodePath("track_dummy_node")
            track_dummy_node.reparentTo(self.render)

            track = self.loader.loadModel("assets/models/trackcoloured.bam")
            track.reparentTo(track_dummy_node)
            track.setColor((0, 0, 0, 1))
            track.set_pos(0, Track.LENGTH / 2, 0)

            track_dummy_node.set_pos(start_pos)
            track_dummy_node.set_h(heading_deg)
            track_dummy_node.set_p(pitch_deg)

            track_direction = Vec3(
                track.getPos(self.render) - track_dummy_node.getPos(self.render)
            ).normalized()
            track_list.append(
                Track(
                    track_direction,
                    track_normal,
                    track_dummy_node.getPos(self.render),
                    track_dummy_node,
                )
            )

            start_pos = start_pos + track_direction * Track.LENGTH
            track_normal = normal_rotation_quat.xform(track_normal)
            pitch_deg += del_pitch_deg
            pitch += del_pitch
            if not is_loop or i < num_tracks // 2:
                heading_deg += del_heading_deg
                heading += del_heading
            else:
                heading_deg -= del_heading_deg
                heading -= del_heading

        return track_list

    def generate_straight(
        self, start_pos: Point3F, initial_heading: float, num_tracks: int = 10
    ) -> TrackList:
        return self._generate_track_collection(
            start_pos=start_pos,
            initial_heading=initial_heading,
            num_tracks=random.randint(num_tracks, num_tracks + 10),
            del_pitch_deg=0,
            del_heading_deg=0,
        )

    def generate_ramp(
        self,
        start_pos: Point3F,
        initial_heading: float,
        type_: Literal["up", "down"],
        num_tracks: int = 10,
    ) -> TrackList:
        ramp = self._generate_track_collection(
            start_pos=start_pos,
            initial_heading=initial_heading,
            num_tracks=num_tracks,
            del_pitch_deg=5 if type_ == "up" else -5,
            del_heading_deg=0,
        )
        ramp.extend(
            self._generate_track_collection(
                start_pos=ramp.tail.end_pos,
                initial_heading=initial_heading,
                num_tracks=2,
                del_pitch_deg=0,
                del_heading_deg=0,
            )
        )
        return ramp

    def generate_turn(
        self,
        start_pos: Point3F,
        initial_heading: float,
        type_: Literal["left", "right"],
    ) -> TrackList:
        return self._generate_track_collection(
            start_pos=start_pos,
            initial_heading=initial_heading,
            num_tracks=18,
            del_pitch_deg=0,
            del_heading_deg=5 if type_ == "left" else -5,
        )

    def generate_loop(
        self, start_pos: Point3F, initial_heading: float, num_tracks: int = 40
    ) -> TrackList:
        loop = self._generate_track_collection(
            start_pos=start_pos,
            initial_heading=initial_heading,
            num_tracks=num_tracks,
            del_pitch_deg=10,
            del_heading_deg=1,
            is_loop=True,
        )
        loop.extend(
            self._generate_track_collection(
                start_pos=loop.tail.end_pos,
                initial_heading=initial_heading,
                num_tracks=2,
                del_pitch_deg=0,
                del_heading_deg=0,
            )
        )
        return loop
