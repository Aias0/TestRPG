from config import SETTINGS

white = (0xFF, 0xFF, 0xFF)
black = (0x0, 0x0, 0x0)
red = (0xFF, 0x0, 0x0)
green = (255, 255, 255)
brown = (150, 75, 0)

player_atk = (0xE0, 0xE0, 0xE0)
enemy_atk = (0xFF, 0xC0, 0xC0)
prompt_player = (0x3F, 0xFF, 0xFF)
status_effect_applied = (0x3F, 0xFF, 0x3F)
descend = (0x9F, 0x3F, 0xFF)

player_die = (0xFF, 0x30, 0x30)
enemy_die = (0xFF, 0xA0, 0x30)

valid = (0x25, 0xAB, 0x0)
invalid = (0xFF, 0xFF, 0x00)
impossible = (0x80, 0x80, 0x80)
error = (0xFF, 0x40, 0x40)

welcome_text = (0x20, 0xA0, 0xFF)
health_recovered = (0x0, 0xFF, 0x0)

bar_text = white
hp_bar_filled = (0xC2, 0x8, 0x8)
hp_bar_empty = (0x5A, 0x8, 0x8)

mp_bar_filled = (0x8, 0x8, 0xC2)
mp_bar_empty = (0x8, 0x8, 0x5A)

sp_bar_filled = (0x8, 0xC2, 0x8)
sp_bar_empty = (0x8, 0x5A, 0x8)

ui_color = SETTINGS['ui_color']
ui_text_color = SETTINGS['ui_text_color']
ui_cursor_text_color = SETTINGS['ui_cursor_text_color']
ui_selected_text_color = SETTINGS['ui_selected_text_color']


menu_title = (255, 255, 63)
menu_text = white

def refresh_color() -> None:
    global ui_color, ui_text_color, ui_cursor_text_color, ui_selected_text_color
    ui_color = SETTINGS['ui_color']
    ui_text_color = SETTINGS['ui_text_color']
    ui_cursor_text_color = SETTINGS['ui_cursor_text_color']
    ui_selected_text_color = SETTINGS['ui_selected_text_color']