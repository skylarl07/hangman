#!/usr/bin/env python

import os
import pygame as pg
from pygame.sprite import Sprite
from enum import Enum


# ---------- Static data ----------
main_dir = os.path.split(os.path.abspath(__file__))[0]
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (252, 3, 3)
RECT_X = 740
RECT_Y = 580
SCREENRECT = pg.Rect(0, 0, RECT_X, RECT_Y)
ANSWER = 'Ada Lovelace'
MAX_CHANCE = 6
RETURN_MSG = "Return to main menu"

# ---------- mutable var ----------
LETTERS = []
NUM_GUESSES = 0
GAMEOVER = False
WINNING = False 


def load_image(file):
    """loads an image, prepares it for play"""
    file = os.path.join(main_dir, "src", file)
    try:
        surface = pg.image.load(file)
    except pg.error:
        raise SystemExit('Could not load image "%s" %s' % (file, pg.get_error()))
    return surface.convert()


def create_surface_with_text(text, font_size, text_rgb, bg_rgb):
    """ Returns surface with text written on """
    font = pg.freetype.SysFont("Courier", font_size, bold=True) # font used
    surface, _ = font.render(text=text, fgcolor=text_rgb, bgcolor=bg_rgb)
    return surface.convert_alpha()


class GameState(Enum):
    QUIT = -1
    TITLE = 0
    NEW_GAME = 1
    GAME_OVER = 2
    WON = 3
    

class OpeningText(Sprite):
    """ An user interface element that can be added to a surface """
    def __init__(self, center_pos, text, font_size, bg_rgb, text_rgb, action=None):
        """
        Args:
            center_position - tuple (x, y)
            text - string of text to write
            font_size - int
            bg_rgb (background colour) - tuple (r, g, b)
            text_rgb (text colour) - tuple (r, g, b)
        """
        # calls the init method of the parent sprite class
        Sprite.__init__(self)
        self.mouse_over = False  # indicates if the mouse is over the element
        self.action = action

        # create the default image
        default_text = create_surface_with_text(
            text=text, font_size=font_size, text_rgb=text_rgb, bg_rgb=bg_rgb
        )

        # create the image that shows when mouse is over the element
        hovered_text = create_surface_with_text(
            text=text, font_size=font_size * 1.2, text_rgb=text_rgb, bg_rgb=bg_rgb
        )

        # add both images and their rects to lists
        self.text_imgs = [default_text, hovered_text]
        self.text_rects = [
            default_text.get_rect(center=center_pos),
            hovered_text.get_rect(center=center_pos),
        ]

    # properties that vary the image and its rect when the mouse is over the element
    @property
    def image(self):
        return self.text_imgs[1] if self.mouse_over else self.text_imgs[0]

    @property
    def rect(self):
        return self.text_rects[1] if self.mouse_over else self.text_rects[0]

    def update(self, mouse_pos, mouse_up):
        if self.rect.collidepoint(mouse_pos):
            self.mouse_over = True
            if mouse_up:
                return self.action
        else:
            self.mouse_over = False
        
    def draw(self, surface):
        """ Draws element onto a surface """
        surface.blit(self.image, self.rect)


class InputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pg.Rect(x, y, w, h)
        self.color = BLACK
        self.text = text
        self.txt_surface = create_surface_with_text(self.text, 30, self.color, None)
        self.disable = False
        self.num_gusses = 0

    def handle_event(self, event):
        global LETTERS
        global NUM_GUESSES
        global GAMEOVER
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_RETURN:
                if self.text in ANSWER: # is guessed right
                    LETTERS.append(self.text)
                else:
                    NUM_GUESSES += 1
                    if NUM_GUESSES == MAX_CHANCE:
                        GAMEOVER = True
                self.text = ''
                self.disable= False
            elif event.key == pg.K_BACKSPACE:
                self.text = self.text[:-1]
                self.disable= False
            elif not self.disable:
                self.text += event.unicode
                self.disable = True
            self.txt_surface = create_surface_with_text(self.text, 30, self.color, None)

    def draw(self, screen):
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        pg.draw.rect(screen, self.color, self.rect, 2)


def title_screen(screen, pic):
    pic_center = (RECT_X/2, RECT_Y/2-70)
    front_img_rect = pic.get_rect(center=pic_center)

    start_btn = OpeningText(
        center_pos=(RECT_X/2, 3*RECT_Y/4+30),
        font_size=30,
        bg_rgb=WHITE,
        text_rgb=BLACK,
        text="Start",
        action=GameState.NEW_GAME,
    )
    quit_btn = OpeningText(
        center_pos=(RECT_X/2, 3*RECT_Y/4+100),
        font_size=30,
        bg_rgb=WHITE,
        text_rgb=BLACK,
        text="Quit",
        action=GameState.QUIT,
    )

    buttons = [start_btn, quit_btn]

    while True:
        mouse_up = False
        for event in pg.event.get():
            if event.type == pg.MOUSEBUTTONUP and event.button == 1:
                mouse_up = True
        screen.fill(WHITE)
        screen.blit(pic, front_img_rect) # render the title picture

        for button in buttons:
            ui_action = button.update(pg.mouse.get_pos(), mouse_up)
            if ui_action is not None:
                return ui_action
            button.draw(screen)
        pg.display.flip()


# Function to display the random word on the screen
def display_word(word, letters, surface):
    global WINNING
    curr_won = True
    hidden_word = ""
    for char in word:
        if char in letters or char.lower() in letters:
            hidden_word += " "+char+" "
        else:
            if char == " ": # display space regardless
                hidden_word += "   "
            else:
                curr_won = False
                hidden_word += " _ "
    WINNING = curr_won

    word_text = create_surface_with_text(
        text=hidden_word, 
        font_size=30,
        bg_rgb=WHITE,
        text_rgb=BLACK)
    word_rect = word_text.get_rect(center=(RECT_X/2, 3*RECT_Y/4))
    surface.blit(word_text, word_rect)


def game_level(screen):
    action_list = []
    input_box = InputBox(
        x = RECT_X/2 - (RECT_X-100)/2,
        y = (3*RECT_Y/4 + 50) - 25,
        w=RECT_X-100, 
        h=50
    )

    for i in range(7):
        img = load_image(f"action{i+1}.jpg")
        img = pg.transform.scale(img, (500, 400))
        action_list.append(img)
    
    pic_center = (RECT_X/2, RECT_Y/2-70)
    front_img_rect = action_list[0].get_rect(center=pic_center)

    return_btn = OpeningText(
        center_pos=(140, RECT_Y-10),
        font_size=20,
        bg_rgb=WHITE,
        text_rgb=BLACK,
        text=RETURN_MSG,
        action=GameState.TITLE,
    )

    while True:
        mouse_up = False
        for event in pg.event.get():
            input_box.handle_event(event)
            if event.type == pg.MOUSEBUTTONUP and event.button == 1:
                mouse_up = True
        if GAMEOVER or WINNING:
            break

        screen.fill(WHITE)
        screen.blit(action_list[0], front_img_rect)
        screen.blit(action_list[NUM_GUESSES], front_img_rect)
        input_box.draw(screen)
        display_word(ANSWER, LETTERS, screen)

        ui_action = return_btn.update(pg.mouse.get_pos(), mouse_up)
        if ui_action is not None:
            return ui_action
        return_btn.draw(screen)
        pg.display.flip()


def display_winning(screen, img):
    pic_center = (RECT_X/2, RECT_Y/2-70)
    img_rect = img.get_rect(center=pic_center)

    name_text = create_surface_with_text(
        text="Ada Lovelace", font_size=30, text_rgb=BLACK, bg_rgb=WHITE
    )
    year_text = create_surface_with_text(
        text="1815 - 1852", font_size=30, text_rgb=BLACK, bg_rgb=WHITE
    )

    name_rect = name_text.get_rect(center=(RECT_X/2, 3*RECT_Y/4+30))
    year_rect = year_text.get_rect(center=(RECT_X/2, 3*RECT_Y/4+80))

    return_btn = OpeningText(
        center_pos=(140, RECT_Y-10),
        font_size=20,
        bg_rgb=WHITE,
        text_rgb=BLACK,
        text=RETURN_MSG,
        action=GameState.TITLE,
    )

    while True:
        mouse_up = False
        for event in pg.event.get():
            if event.type == pg.MOUSEBUTTONUP and event.button == 1:
                mouse_up = True
        screen.fill(WHITE)
        screen.blit(name_text, name_rect)
        screen.blit(year_text, year_rect)
        screen.blit(img, img_rect) # render the title picture

        ui_action = return_btn.update(pg.mouse.get_pos(), mouse_up)
        if ui_action is not None:
            return ui_action
        return_btn.draw(screen)
        pg.display.flip()


def display_gameover(screen):
    img = load_image("action7.jpg")
    img = pg.transform.scale(img, (500, 400))
    pic_center = (RECT_X/2, RECT_Y/2-70)
    img_rect = img.get_rect(center=pic_center)

    gameover_text = create_surface_with_text(
        text="Game Over", font_size=50, text_rgb=RED, bg_rgb=WHITE
    )
    gameover_rect = gameover_text.get_rect(center=(RECT_X/2, RECT_Y/2))

    return_btn = OpeningText(
        center_pos=(140, RECT_Y-10),
        font_size=20,
        bg_rgb=WHITE,
        text_rgb=BLACK,
        text="Return to main menu",
        action=GameState.TITLE,
    )

    while True:
        mouse_up = False
        for event in pg.event.get():
            if event.type == pg.MOUSEBUTTONUP and event.button == 1:
                mouse_up = True
        screen.fill(WHITE)
        screen.blit(img, img_rect)
        screen.blit(gameover_text, gameover_rect)

        ui_action = return_btn.update(pg.mouse.get_pos(), mouse_up)
        if ui_action is not None:
            return ui_action
        return_btn.draw(screen)
        pg.display.flip()


def main(winstyle=0):
# def main():
    global WINNING
    global GAMEOVER
    global NUM_GUESSES
    global LETTERS
    # ---------- Init game ----------
    if pg.get_sdl_version()[0] == 2:
        pg.mixer.pre_init(44100, 32, 2, 1024)
    pg.init()

    # ---------- Init screen settings ----------
    # Set the display mode
    winstyle = 0  # |FULLSCREEN
    bestdepth = pg.display.mode_ok(SCREENRECT.size, winstyle, 32)
    screen = pg.display.set_mode(SCREENRECT.size, winstyle, bestdepth)

    # ---------- Load images for sprite classes ----------
    # Load images, assign to sprite classes
    img = load_image("open_logo.jpg")
    img = pg.transform.scale(img, (450, 350))
    me = load_image("me.jpg")
    me = pg.transform.scale(me, (314, 410))

    # ---------- decorate game window ----------
    # set the icon image for the game 
    icon = pg.transform.scale(load_image("icon.jpg"), (25, 25))
    pg.display.set_icon(icon)
    # set the window caption
    pg.display.set_caption("Mathematician Hangman")
    screen.fill(WHITE) # don't need to render pixel by pixel, just fill with white
    game_state = GameState.TITLE # initialize game state to be the title

    # main loop
    while True:
        if game_state == GameState.TITLE:
            game_state = title_screen(screen, img)

        if game_state == GameState.NEW_GAME:
            game_state = game_level(screen)
        
        if GAMEOVER:
            game_state = GameState.GAME_OVER
            GAMEOVER = False

        if WINNING:
            game_state = GameState.WON
            WINNING = False

        if game_state == GameState.WON:
            game_state = display_winning(screen, me)
            NUM_GUESSES = 0
            LETTERS = []

        if game_state == GameState.GAME_OVER:
            game_state = display_gameover(screen)
            NUM_GUESSES = 0
            LETTERS = []

        if game_state == GameState.QUIT:
            pg.quit()
            return


# call main when the script is run
if __name__ == "__main__":
    main()
