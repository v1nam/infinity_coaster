from math import sin, cos, pi

from direct.showbase.ShowBase import ShowBase
from direct.task.Task import Task
from panda3d.core import Vec3


class Game(ShowBase):
    def __init__(self):
        super().__init__()

        self.ground = self.loader.loadModel("models/ground.bam")
        self.ground.reparentTo(self.render)

        start_pos = (0, -10, 5)
        pitch_deg = 0
        pitch = 0

        del_pitch_deg = 10
        del_pitch = del_pitch_deg * pi / 180

        track_length = 2
        for i in range(20):
            track = self.loader.loadModel("models/trackcoloured.bam")
            track.set_pos(start_pos[0], start_pos[1] + track_length / 2, start_pos[2])
            parallel_vec = Vec3(0, cos(pitch), sin(pitch))
            normal_vec = Vec3(0, cos(pitch + pi / 2), sin(pitch + pi / 2))
            track.set_p(pitch_deg)
            track.set_pos(
                track.getPos()
                + normal_vec * track_length / 2 * sin(del_pitch)
                + parallel_vec * track_length / 2 * cos(del_pitch)
            )

            track.reparentTo(self.render)

            start_pos = (
                start_pos[0],
                start_pos[1] + track_length * cos(pitch),
                start_pos[2] + track_length * sin(pitch),
            )
            pitch_deg += del_pitch_deg
            pitch += del_pitch

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
