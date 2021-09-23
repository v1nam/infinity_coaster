import random
import sys
from functools import partial
from typing import Set

from direct.gui.DirectButton import DirectButton
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from direct.filter.CommonFilters import CommonFilters

from direct.showbase.ShowBase import ShowBase
from direct.task.Task import Task
from panda3d.core import ClockObject, NodePath, Point3F, Vec3, WindowProperties, TextNode, AmbientLight, DirectionalLight

from track_generation import Track, TrackCollectionGenerator, TrackList
from menu import Menu


class Game(ShowBase):
    def __init__(self):
        super().__init__()
        
        base.setBackgroundColor(0.05,0.05,0.05)
        self.filters = CommonFilters(base.win, base.cam)
        self.filters.setBloom(blend=(0, 0, 0, 1), desat=-0.5, intensity=3.0, size="small")
        alight = AmbientLight('alight')
        alnp = render.attachNewNode(alight)
        alight.setColor((0, 0.35, 0.5, 1))
        self.render.setLight(alnp)

        self.track_generator = TrackCollectionGenerator(self.render, self.loader)
        self.track_collections = {
            "straight": self.track_generator.generate_straight,
            "ramp_up": partial(self.track_generator.generate_ramp, type_="up"),
            "ramp_down": partial(self.track_generator.generate_ramp, type_="down"),
            "turn_left": partial(self.track_generator.generate_turn, type_="left"),
            "turn_right": partial(self.track_generator.generate_turn, type_="right"),
            "loop": self.track_generator.generate_loop,
        }
        self.start_menu = Menu(
            {"Start New Game": self.start_game, "ooga booga": self.show_credits}
        )
        self.start_menu.show()
        # self.start_game()

    def show_credits(self):
        _ = OnscreenText("maed by vinam & hsp")
        b = DirectButton(
            text="back",
            pos=(0, 0, -0.75),
            scale=(0.1, 1, 0.1),
            command=lambda: [b.destroy(), _.destroy(), self.start_menu.show()],
        )

    def show_pause_menu(self):
        b = DirectButton(
            text="Resume",
            pos=(0, 0, 0),
            scale=(0.1, 1, 0.1),
            command=lambda: [b.destroy(), self.unpause()],
        )

    def start_game(self):
        self.disable_mouse()
        props = WindowProperties()
        props.setCursorHidden(True)
        base.win.requestProperties(props)

        self.score = 0
        self.score_node = TextNode("score_node")
        self.score_node_path = self.aspect2d.attachNewNode(self.score_node)
        self.score_node_path.set_scale(0.1)
        self.score_node_path.set_pos((-1, 0, 0.75))

        self.speed = 12
        self.track_heading = 0

        self.tracks = TrackList(maxlen=100)
        self.set_tracks()

        self.player_node = NodePath("player_node")
        self.player_node.reparentTo(self.render)
        self.player_node.set_pos(self.current_track.start_pos)
        self.camera.reparentTo(self.player_node)
        self.camera.set_pos(self.tracks.head.normal)

        icon_bar_x = 1.33333 - 0.1 - 0.2
        self.icons = {
            icon_name: OnscreenImage(
                image=f"models/{icon_name}_icon.png",
                pos=(icon_bar_x, 0, ((7 - i) * 2 / 7) - 1),
                scale=(0.1, 1, 0.1),
            )
            for i, icon_name in enumerate(self.track_collections.keys(), start=1)
        }
        self.currently_active_collections = self.generate_active_collections()
        self.update_icon_tray()

        self.center = []
        self.set_center()
        self.rot_v = 0
        self.rot_h = 0
        self.mouse_sensitivity = 30

        # self.taskMgr.add(self.move_player_task, "MovePlayerTask")
        self.accept("aspectRatioChanged", self.set_center)
        self.accept("escape", sys.exit)
        self.unpause()

    def pause(self):
        self.taskMgr.remove("MovePlayerTask")
        self.show_pause_menu()
        props = WindowProperties()
        props.setCursorHidden(False)
        base.win.requestProperties(props)
        self.ignore("space")
        # self.accept("space", self.unpause)
        for i, _ in enumerate(self.track_collections.keys(), start=1):
            self.ignore(str(i))

    def unpause(self):
        self.taskMgr.add(self.move_player_task, "MovePlayerTask")
        self.taskMgr.add(self.update_score_task, "UpdateScoreTask")
        props = WindowProperties()
        props.setCursorHidden(True)
        base.win.requestProperties(props)
        self.ignore("space")
        self.accept("space", self.pause)

        for i, collection in enumerate(self.track_collections.keys(), start=1):
            self.accept(str(i), self.place_track, [collection])

    def place_track(self, collection: str):
        # if collection not in self.currently_active_collections:
        #     # TODO: commit die
        #     return

        new_tracks = self.track_collections[collection](
            start_pos=self.tracks.tail.end_pos,
            # initial_heading=self.tracks.tail.direction,
            initial_heading=self.track_heading,
        )
        self.tracks.extend(new_tracks)

        if collection == "turn_left":
            self.track_heading += 90
        if collection == "turn_right":
            self.track_heading -= 90
        self.currently_active_collections = self.generate_active_collections()
        self.update_icon_tray()

    def set_tracks(self):
        self.tracks.extend(self.track_generator.generate_straight(
            start_pos=Point3F(0, -10, 5),
            initial_heading=self.track_heading,
            num_tracks=30,
        ))
        self.current_track = self.tracks.head

    def move_player_task(self, _task):
        # print(self.track_heading)
        dt = ClockObject.getGlobalClock().dt

        if (
            self.player_node.get_pos() - self.current_track.start_pos
        ).length() > Track.LENGTH and self.current_track.next_track is not None:
            self.current_track = self.current_track.next_track
            self.score += 1

        self.player_node.set_pos(
            self.current_track.start_pos
            + (
                self.player_node.get_pos()
                + self.current_track.direction * self.speed * dt
                - self.current_track.start_pos
            ).project(self.current_track.direction)
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

    def update_score_task(self, _task):
        self.score_node.set_text(f"SCORE: {self.score}")
        return Task.cont

    def set_center(self):
        self.center = [base.win.getXSize() // 2, base.win.getYSize() // 2]

    def generate_active_collections(self) -> Set[str]:
        k = random.choices([1, 2, 3], weights=[0.1, 0.8, 0.1], k=1)[0]
        return set(random.choices(list(self.track_collections.keys()), k=k))

    def update_icon_tray(self):
        for icon_name, icon in self.icons.items():
            if icon_name in self.currently_active_collections:
                icon.set_color(0, 1, 0, 1)
            else:
                icon.set_color(1, 0, 0, 1)


if __name__ == "__main__":
    game = Game()
    game.run()
