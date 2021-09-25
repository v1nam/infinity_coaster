import random
import sys
from functools import partial
from textwrap import dedent
from typing import Set

from direct.gui.DirectButton import DirectButton
from direct.gui import DirectGuiGlobals as DDG
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from direct.filter.CommonFilters import CommonFilters

from direct.showbase.ShowBase import ShowBase
from direct.task.Task import Task
from panda3d.core import (
    ClockObject,
    NodePath,
    Point3F,
    Vec3,
    WindowProperties,
    TextNode,
    AmbientLight,
    DirectionalLight,
    TextureStage,
    TexGenAttrib,
    TransparencyAttrib,
)

from track_generation import Track, TrackCollectionGenerator, TrackList
from menu import Menu


class Game(ShowBase):
    def __init__(self):
        super().__init__()
        props = WindowProperties()
        props.set_title("Infinity Coaster")
        props.icon_filename = "models/logo.ico"
        base.win.requestProperties(props)

        cube_map = self.loader.loadCubeMap("models/sky_#.png")
        self.sky_box = self.loader.loadModel("models/coaster.bam")
        self.sky_box.setScale(50)
        self.sky_box.setBin("background", 0)
        self.sky_box.setDepthWrite(0)
        self.sky_box.setTwoSided(True)
        self.sky_box.setTexGen(TextureStage.getDefault(), TexGenAttrib.MWorldCubeMap)
        self.sky_box.setTexture(cube_map, 1)
        self.sky_box.reparentTo(self.render)

        self.filters = CommonFilters(base.win, base.cam)
        self.filters.setBloom(
            blend=(0, 0, 0, 1), desat=-0.5, intensity=2.0, size="small"
        )

        alight = AmbientLight("alight")
        alnp = self.render.attachNewNode(alight)
        alight.setColor((0, 0.7, 1.0, 1))
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
        self.accept("escape", sys.exit)

        self.music = self.loader.loadMusic("models/Guitar-Mayhem-3.wav")
        self.music.setVolume(0.5)
        self.music.setLoop(True)
        self.music.play()
        self.show_start_menu()

    def show_start_menu(self):
        im = OnscreenImage("models/logo.png", pos=(0, 0, 0.6), scale=(0.8, 1, 0.4))
        title = OnscreenImage("models/title.png", pos=(0, 0, 0.1), scale=(0.8, 1, 0.12))
        title.setTransparency(TransparencyAttrib.MAlpha)
        Menu(
            {
                "NEW GAME": (lambda: [self.start_game(), im.destroy(), title.destroy()], (0, -0.2)),
                "HOW TO PLAY": (lambda: [self.show_instructions(), im.destroy(), title.destroy()], (0, -0.39)),
                "CREDITS": (lambda: [self.show_credits(), im.destroy(), title.destroy()], (0, -0.57)),
                "QUIT": (sys.exit, (-1.18, 0.89)),
                "LEADERBOARD": (lambda: ..., (0, -0.8))
            }
        )

    def show_instructions(self):
        text = OnscreenText(
            dedent(
                """\
        • Welcome to Infinity Coaster! 
        
        • We hope you enjoy the ride we have prepared for you-
          Oh wait. You have to make your own ride. As you go.
        
        • There are 6 varieties of tracks you can place.
        
        • Random combinations of these will appear when you're close to the end of the track.
        
        • Press numbers between 1 and 6 to place the corresponding track.
        
        • If you place a track that is currently active, good job! You get to live.
        
        • If you cannot press a number in time, or try to place an inactive track, you lose.
          
        • Have fun!\
        """
            ),
            fg=(1, 1, 1, 1),
            pos=(0, 0.7),
            wordwrap=35,
        )
        b = DirectButton(
            text="Back",
            pos=(0, 0, -0.75),
            scale=(0.1, 1, 0.1),
            command=lambda: [
                b.destroy(),
                text.destroy(),
                self.show_start_menu(),
            ],
            # scale=(0.12, 1, 0.12),
            text_scale=(0.9, 0.9),
            text_bg=(0, 0.085, 0.125, 1),
            text_fg=(0, 0.7, 1, 1),
            relief=DDG.GROOVE,
            frameColor=(0, 0.35, 0.5, 1),
            text_shadow=(0, 0.0425, 0.0625, 1),
        )

    def show_credits(self):
        text1 = OnscreenText("Made by vinam & hsp", fg=(1, 1, 1, 1), pos=(0, 0.2))
        text2 = OnscreenText(
            "Music by Eric Matyas \n www.soundimage.org", fg=(1, 1, 1, 1), pos=(0, -0.2)
        )
        b = DirectButton(
            text="Back",
            pos=(0, 0, -0.75),
            scale=(0.1, 1, 0.1),
            command=lambda: [
                b.destroy(),
                text1.destroy(),
                text2.destroy(),
                self.show_start_menu()
            ],
            # scale=(0.12, 1, 0.12),
            text_scale=(0.9, 0.9),
            text_bg=(0, 0.085, 0.125, 1),
            text_fg=(0, 0.7, 1, 1),
            relief=DDG.GROOVE,
            frameColor=(0, 0.35, 0.5, 1),
            text_shadow=(0, 0.0425, 0.0625, 1),
        )

    def start_game(self):
        self.disable_mouse()
        props = WindowProperties()
        props.setCursorHidden(True)
        base.win.requestProperties(props)

        self.score_node = TextNode("score_node")
        self.score_node_path = self.aspect2d.attachNewNode(self.score_node)
        self.score_node_path.set_scale(0.1)
        self.score_node_path.set_pos((-1, 0, 0.75))

        self.speed = 9
        self.acceleration = 0.4
        self.track_generator.total_tracks_placed = 0
        self.current_track_index = 0
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
                scale=(0.15, 15, 0.15),
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

        self.ambient_sound = base.loader.loadSfx("models/ambient.wav")
        self.ambient_sound.setVolume(0.5)
        self.ambient_sound.setLoop(True)
        self.ambient_sound.play()
        self.place_track_sound = self.loader.loadSfx("models/place.wav")
        self.death_sound = self.loader.loadSfx("models/death.wav")

        self.accept("aspectRatioChanged", self.set_center)
        self.unpause()

    def pause(self, show_resume: bool = True):
        self.taskMgr.remove("MovePlayerTask")
        self.taskMgr.remove("UpdateScoreTask")
        self.taskMgr.remove("PositionSkyBoxTask")
        self.ambient_sound.stop()
        if show_resume:
            b = DirectButton(
                text="Resume",
                pos=(0, 0, 0),
                scale=(0.1, 1, 0.1),
                command=lambda: [b.destroy(), self.unpause()],
                text_scale=(0.9, 0.9),
                text_bg=(0, 0.085, 0.125, 1),
                text_fg=(0, 0.7, 1, 1),
                relief=DDG.GROOVE,
                frameColor=(0, 0.35, 0.5, 1),
                text_shadow=(0, 0.0425, 0.0625, 1),
            )
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
        self.taskMgr.add(self.position_skybox_task, "PositionSkyBoxTask")
        self.ambient_sound.play()
        props = WindowProperties()
        props.setCursorHidden(True)
        base.win.requestProperties(props)
        self.ignore("space")
        self.accept("space", self.pause)

        for i, collection in enumerate(self.track_collections.keys(), start=1):
            self.accept(str(i), self.place_track, [collection])

    def die(self, cause: str):
        self.death_sound.play()
        self.pause(show_resume=False)
        for track in self.tracks:
            track.node_path.removeNode()
        for icon in self.icons.values():
            icon.destroy()
        self.score_node_path.removeNode()

        t1 = OnscreenText(
            text=cause,
            pos=(0, 0.5, 0),
            bg=(0, 0, 0, 0),
            fg=(0, 0.7, 1, 1),
            shadow=(0, 0.0425, 0.0625, 1),
            scale=0.1,
        )
        t2 = OnscreenText(
            text=f"Final Score: {self.current_track_index}",
            pos=(0, 0.3, 0),
            bg=(0, 0, 0, 0),
            fg=(0, 0.7, 1, 1),
            shadow=(0, 0.0425, 0.0625, 1),
            scale=0.09,
        )

        Menu(
            {
                "PLAY AGAIN": (
                    lambda: [
                        self.start_game(),
                        t1.destroy(),
                        t2.destroy(),
                    ],
                    (0, -0.2),
                ),
                "START SCREEN": (
                    lambda: [
                        self.show_start_menu(),
                        t1.destroy(),
                        t2.destroy(),
                    ],
                    (0, -0.4),
                ),
                "QUIT": (sys.exit, (0, -0.6)),
            }
        )

    def place_track(self, collection: str):
        if collection not in self.currently_active_collections:
            self.die("You tried to press an inactive track and died!")
            return
        self.place_track_sound.play()
        new_tracks = self.track_collections[collection](
            start_pos=self.tracks.tail.end_pos,
            initial_heading=self.track_heading,
        )
        self.tracks.extend(new_tracks)

        if collection == "turn_left":
            self.track_heading += 90
        if collection == "turn_right":
            self.track_heading -= 90
        self.currently_active_collections = []
        self.update_icon_tray()

    def set_tracks(self):
        self.tracks.extend(
            self.track_generator.generate_straight(
                start_pos=Point3F(0, -10, 5),
                initial_heading=self.track_heading,
                num_tracks=30,
            )
        )
        self.current_track = self.tracks.head

    def move_player_task(self, _task):
        # print(self.track_heading)
        dt = ClockObject.getGlobalClock().dt

        if (
            self.player_node.get_pos() - self.current_track.start_pos
        ).length() > Track.LENGTH:
            if self.current_track.next_track is not None:
                self.current_track = self.current_track.next_track
                self.current_track_index += 1
            else:
                self.die("You didn't place a track in time and died!")
                return
        if (
            self.current_track_index >= self.track_generator.total_tracks_placed - 10
            and not self.currently_active_collections
        ):
            self.currently_active_collections = self.generate_active_collections()
            self.update_icon_tray()

        self.player_node.set_pos(
            self.current_track.start_pos
            + (
                self.player_node.get_pos()
                + self.current_track.direction * self.speed * dt
                - self.current_track.start_pos
            ).project(self.current_track.direction)
        )
        self.camera.set_pos(self.current_track.normal * 2)
        if self.speed < 20:
            self.speed += self.acceleration * dt

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
        self.score_node.set_text(f"SCORE: {self.current_track_index}")
        return Task.cont

    def position_skybox_task(self, _task):
        self.sky_box.set_pos(self.camera.get_pos(self.render))
        return Task.cont

    def set_center(self):
        self.center = [base.win.getXSize() // 2, base.win.getYSize() // 2]

    def generate_active_collections(self) -> Set[str]:
        k = random.choices([1, 2, 3], weights=[0.1, 0.8, 0.1], k=1)[0]
        return set(
            random.choices(
                list(self.track_collections.keys()),
                weights=[0.18, 0.18, 0.18, 0.18, 0.18, 0.07],
                k=k,
            )
        )

    def update_icon_tray(self):
        for icon_name, icon in self.icons.items():
            if icon_name in self.currently_active_collections:
                # icon.set_color(0, 1, 0, 1)
                icon.show()
            else:
                icon.hide()
                # icon.set_color(0, 0, 0, 1)


if __name__ == "__main__":
    game = Game()
    game.run()
