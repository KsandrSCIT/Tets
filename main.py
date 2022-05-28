import math
import os
from tracemalloc import stop
import arcade
import arcade.gui


SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 650
SCREEN_TITLE = "GeometricMadness"

TILE_SCALING = 3
CHARACTER_SCALING = TILE_SCALING//2.5
SPRITE_PIXEL_SIZE = 128
GRID_PIXEL_SIZE = SPRITE_PIXEL_SIZE * TILE_SCALING

PLAYER_MOVEMENT_SPEED = 13
GRAVITY = 1.5
PLAYER_JUMP_SPEED = 30
PLAYER_JUMP_SPRITE = 0
COUNT_LVLS = 2
PLAYER_START_X = 2
PLAYER_START_Y = 1
LAYER_NAME_MOVING_PLATFORMS = "Moving Platforms"
LAYER_NAME_PLATFORMS = "Platforms"
LAYER_NAME_BACKGROUND = "Background"
LAYER_NAME_PLAYER = "Player"
LAYER_NAME_ENEMIES = "Enemies"
LAYER_NAME_WINNERS = "Winner"
LAYER_NAME_TURNOVER = "Turnover"



class QuitButton(arcade.gui.UIFlatButton):
    def on_click(self, event: arcade.gui.UIOnClickEvent):
        arcade.exit()
class MainMenu(arcade.View):

    def on_show(self):
        self.manager = arcade.gui.UIManager()
        self.manager.enable()
        self.background = arcade.load_texture(":resources:images/backgrounds/abstract_1.jpg")
        self.v_box = arcade.gui.UIBoxLayout()
        start_button = arcade.gui.UIFlatButton(text="Start Game", width=200)
        self.v_box.add(start_button.with_space_around(bottom=20))
        start_button.on_click = self.on_click_start
        quit_button = QuitButton(text="Quit", width=200)
        self.v_box.add(quit_button)
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                anchor_y="center_y",
                child=self.v_box)
        )        
    def on_draw(self):
        self.clear()
        arcade.draw_lrwh_rectangle_textured(0, 0,
                                            SCREEN_WIDTH, SCREEN_HEIGHT,
                                            self.background)
        self.manager.draw()

    def on_click_start(self, event):
        self.manager.disable()
        game_view = GameView()
        self.window.show_view(game_view)

    def on_mouse_press(self, _x, _y, _button, _modifiers):
        game_view = GameView()
        self.window.show_view(game_view)

class PlayerCharacter(arcade.Sprite):

    def __init__(self):
        super().__init__("Persona_0.png", CHARACTER_SCALING)
        self.jumping = False
        self.idle_texture_pair = []
        for i in range(4):
            texture = arcade.load_texture(f"Persona_{i}.png")
            self.idle_texture_pair.append(texture)  

class GameView(arcade.View):

    def __init__(self):

        super().__init__()

        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)
        smex = 0
        self.up_pressed = False
        self.jump_needs_reset = False
        
        self.tile_map = None
        self.scene = None
        self.player_sprite = None
        self.physics_engine = None
        self.camera = None
        self.gui_camera = None

        self.end_of_map = 0
        self.score = 0
        self.dead = 0
        self.backgroundmusic = arcade.load_sound("Dark.mp3")
        self.jump_sound = arcade.load_sound("jump.mp3")
        self.savetime = 0
    def setup(self):
        self.camera = arcade.Camera(self.window.width, self.window.height)
        self.gui_camera = arcade.Camera(self.window.width, self.window.height)

        try:
            with open('nowlvl') as fin:
                i = int(fin.read())
                if i>=COUNT_LVLS:
                    i=0
        except IOError:
            i = 0

        map_name = f"map{i}.json"
        layer_options = {
            LAYER_NAME_PLATFORMS: {
                "use_spatial_hash": True,
            },
            LAYER_NAME_MOVING_PLATFORMS: {
                "use_spatial_hash": False,
            },
            LAYER_NAME_WINNERS: {
                "use_spatial_hash": True,
            },
            LAYER_NAME_TURNOVER: {
                "use_spatial_hash": True,
            },              
        }
        self.tile_map = arcade.load_tilemap(map_name, TILE_SCALING, layer_options)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        self.score = 0
        self.num_texture = 0

        self.player_sprite = PlayerCharacter()
        self.player_sprite.center_x = (
            self.tile_map.tile_width * TILE_SCALING * PLAYER_START_X
        )
        self.player_sprite.center_y = (
            self.tile_map.tile_height * TILE_SCALING * PLAYER_START_Y
        )
        
        self.scene.add_sprite(LAYER_NAME_PLAYER, self.player_sprite)
        
        self.end_of_map = self.tile_map.width * GRID_PIXEL_SIZE
        
        if self.tile_map.background_color:
            arcade.set_background_color(self.tile_map.background_color)

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            player_sprite = self.player_sprite,
            platforms=self.scene[LAYER_NAME_MOVING_PLATFORMS],
            gravity_constant=GRAVITY,
            walls=self.scene[LAYER_NAME_PLATFORMS]
        )

    def on_show(self):
        self.setup()
        self.audioPlayer = arcade.play_sound(self.backgroundmusic)
        self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED

    def on_draw(self):

        self.clear()
        self.camera.use()

        self.scene.draw()

        self.gui_camera.use()

        score_text = f"Score: {self.score}"
        arcade.draw_text(
            score_text,
            10,
            10,
            arcade.csscolor.WHITE,
            20,
        )
        
    def process_keychange(self):

        if (self.physics_engine.can_jump(y_distance=10) and not self.jump_needs_reset):
                self.player_sprite.change_y = PLAYER_JUMP_SPEED
                self.jump_needs_reset = True
                arcade.play_sound(self.jump_sound)
        elif (self.physics_engine.can_jump(y_distance=-10) and not self.jump_needs_reset):
                self.player_sprite.change_y = -PLAYER_JUMP_SPEED
                self.jump_needs_reset = True
                arcade.play_sound(self.jump_sound)

    def on_key_press(self, key, modifiers):

        if key == arcade.key.SPACE or key == arcade.key.W:
            self.up_pressed = True
            self.player_sprite.jumping = True
            self.physics_engine.player_sprite = None
            self.physics_engine.player_sprite = self.player_sprite
            if self.num_texture == 0 or self.num_texture <3:
                self.num_texture += 1
            else:
                self.num_texture = 0
            self.player_sprite.texture = self.player_sprite.idle_texture_pair[self.num_texture]
        elif key == arcade.key.ESCAPE:
            pause = PauseView(self)
            arcade.stop_sound(self.audioPlayer)
            self.window.show_view(pause)
            
        self.process_keychange()

    def on_key_release(self, key, modifiers):

        if key == arcade.key.SPACE or key == arcade.key.W:
            self.up_pressed = False
            self.jump_needs_reset = False
            self.change_angle = 0
            # self.physics_engine.gravity_constant *= -1

        self.process_keychange()

    def center_camera_to_player(self, speed=0.2):
        screen_center_x = self.camera.scale * (self.player_sprite.center_x - (self.camera.viewport_width / 2))
        screen_center_y = self.camera.scale * (self.player_sprite.center_y - (self.camera.viewport_height / 2))
        if screen_center_x < 0:
            screen_center_x = 0
        if screen_center_y < 0:
            screen_center_y = 0
        player_centered = (screen_center_x, screen_center_y)    

        self.camera.move_to(player_centered, speed)

    def on_update(self, delta_time):
        self.physics_engine.update()
        self.score = int(self.player_sprite.center_x//100)
        if self.dead == self.player_sprite.center_x:
            self.savetime += 1
        else:
            self.savetime = 0
        if self.savetime >= 60:
            with open('Score.txt', 'w') as fout:
                fout.write(str(self.score))            
            arcade.stop_sound(self.audioPlayer)
            game_over = GameOverView()
            self.window.show_view(game_over) 
        self.dead = self.player_sprite.center_x

    
        
        if self.physics_engine.can_jump():
            self.player_sprite.can_jump = False
            
        else:
            self.player_sprite.can_jump = True

        self.scene.update_animation(
            delta_time,
            [
                LAYER_NAME_BACKGROUND,
                LAYER_NAME_PLAYER,
                LAYER_NAME_ENEMIES,
            ],
        )

        self.scene.update(
            [LAYER_NAME_MOVING_PLATFORMS, LAYER_NAME_ENEMIES]
        )


        player_collision_list = arcade.check_for_collision_with_lists(
            self.player_sprite,
            [
                self.scene[LAYER_NAME_ENEMIES],
                self.scene[LAYER_NAME_WINNERS],
                self.scene[LAYER_NAME_TURNOVER],
            ],
        )

        for collision in player_collision_list:

            if self.scene[LAYER_NAME_ENEMIES] in collision.sprite_lists:
                with open('Score.txt', 'w') as fout:
                    fout.write(str(self.score))                    
                arcade.stop_sound(self.audioPlayer)
                game_over = GameOverView()
                self.window.show_view(game_over) 
                return
            else:
                if "Teleport" in collision.properties:
                    self.physics_engine.gravity_constant *= -1
                    collision.remove_from_sprite_lists()

                elif "Points" in collision.properties:
                    with open('Score.txt', 'w') as fout:
                        fout.write(str(self.score))    
                    arcade.stop_sound(self.audioPlayer)  
                    game_win = GameWinView()
                    self.window.show_view(game_win)
        self.center_camera_to_player()

class PauseView(arcade.View):
    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view

    def on_show_view(self):
        arcade.set_background_color(arcade.color.ORANGE)


    def on_draw(self):
        self.clear()

        player_sprite = self.game_view.player_sprite
        player_sprite.draw()



        arcade.draw_text("PAUSED", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50,
                         arcade.color.BLACK, font_size=50, anchor_x="center")

        arcade.draw_text("Press Esc. to return",
                         SCREEN_WIDTH / 2,
                         SCREEN_HEIGHT / 2,
                         arcade.color.BLACK,
                         font_size=20,
                         anchor_x="center")


    def on_key_press(self, key, _modifiers):
        if key == arcade.key.ESCAPE: 
            self.window.show_view(self.game_view)


class GameOverView(arcade.View):

    def on_show(self):
        arcade.set_background_color(arcade.color.WHITE)
        self.background = arcade.load_texture(":resources:images/backgrounds/abstract_1.jpg")
        self.game_over = arcade.load_sound("Looser.mp3")
        self.gameover = arcade.play_sound(self.game_over)
        try:
            with open('Score.txt') as fin:
                self.print_score = fin.read()
        except IOError:
            self.print_score = "0"    
        

  

    def on_draw(self):
        self.clear()
        arcade.draw_lrwh_rectangle_textured(0, 0,
                                            SCREEN_WIDTH, SCREEN_HEIGHT,
                                            self.background)
        
        arcade.draw_text( "Looser, kek - Click to restart", SCREEN_WIDTH / 2,SCREEN_HEIGHT / 2, arcade.color.WHITE, 30, anchor_x="center")
        arcade.draw_text("Score: " + self.print_score, SCREEN_WIDTH / 2,SCREEN_HEIGHT / 2-35, arcade.color.WHITE, 30, anchor_x="center")

    def on_mouse_press(self, _x, _y, _button, _modifiers):
        game_view = GameView()
        arcade.stop_sound(self.gameover)
        
        self.window.show_view(game_view)
        

class GameWinView(arcade.View):

    def on_show(self):
        arcade.set_background_color(arcade.color.WHITE)
        self.background = arcade.load_texture(":resources:images/backgrounds/abstract_1.jpg")
        self.game_Win = arcade.load_sound("MusicWin.mp3")
        self.Win_mus = arcade.play_sound(self.game_Win)
        try:
            with open('nowlvl') as fin:
                i = int(fin.read())
                if i>=COUNT_LVLS:
                    i=0
        except IOError:
            i = 0

        i+=1

        if i<COUNT_LVLS:
            with open('nowlvl','w') as fout:
                fout.write(str(i))
        else:
            with open('nowlvl','w') as fout:
                fout.write(str(0))

        try:
            with open('Score.txt') as fin:
                self.print_score = fin.read()
        except IOError:
            self.print_score = "0"    

    def on_draw(self):
        self.clear()
        arcade.draw_lrwh_rectangle_textured(0, 0,
                                            SCREEN_WIDTH, SCREEN_HEIGHT,
                                            self.background)
        arcade.draw_text("U winner! Click to next lvl", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, arcade.color.WHITE, 30, anchor_x="center")
        arcade.draw_text("Score: " + self.print_score, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2-35, arcade.color.WHITE, 30, anchor_x="center")


    def on_mouse_press(self, _x, _y, _button, _modifiers):
        
        game_view = GameView()
        arcade.stop_sound(self.Win_mus)
        
        self.window.show_view(game_view)
        

def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    menu_view = MainMenu()
    window.show_view(menu_view)
    arcade.run()


if __name__ == "__main__":
    main()