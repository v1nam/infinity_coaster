from math import sin, cos, pi

from direct.showbase.ShowBase import ShowBase
from direct.task.Task import Task
from panda3d.core import Vec3, NodePath, Point3F


class Game(ShowBase):
    def __init__(self):
        super().__init__()

        self.ground = self.loader.loadModel("models/ground.bam")
        self.ground.reparentTo(self.render)

        start_pos = Point3F(0, -10, 5)
        pitch_deg = 0
        pitch = 0
        heading_deg = 0
        heading = 0

        del_pitch_deg = 10
        del_pitch = del_pitch_deg * pi / 180
        del_heading_deg = 1
        del_heading = del_heading_deg * pi / 180

        track_length = 2
        for i in range(40):
            track_dummy_node = NodePath("track_dummy_node")
            track_dummy_node.reparentTo(self.render)

            track = self.loader.loadModel("models/trackcoloured.bam")
            track.reparentTo(track_dummy_node)
            track.set_pos(0, track_length / 2, 0)

            track_dummy_node.set_pos(start_pos)
            track_dummy_node.set_h(heading_deg)
            track_dummy_node.set_p(pitch_deg)

            track_direction = Vec3(track.getPos(self.render) - track_dummy_node.getPos(self.render)).normalized()

            start_pos = start_pos + track_direction * track_length
            pitch_deg += del_pitch_deg
            pitch += del_pitch
            if i < 20:
                heading_deg += del_heading_deg
                heading += del_heading
            else:
                heading_deg -= del_heading_deg
                heading -= del_heading
        self.taskMgr.add(self.spin_camera_task, "SpinCameraTask")

    def spin_camera_task(self, task):
        angle_degrees = task.time * 6.0
        angle_radians = angle_degrees * (pi / 180.0)
        self.camera.set_pos(30 * sin(angle_radians), -30 * cos(angle_radians), 30)
        self.camera.set_hpr(angle_degrees, -20, 0)
        return Task.cont


if __name__ == '__main__':
    game = Game()
    game.run()
