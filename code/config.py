import configparser, ast

def tryeval(val):
    try:
        val = ast.literal_eval(val)
    except ValueError:
        pass
    return val

config = configparser.ConfigParser()
config.read('settings.ini')

SETTINGS = {}
for section in config.sections():
    for key in config[section]:
        SETTINGS[key] = tryeval(config[section][key])
        
def refresh_settings():
    from color import refresh_color
    from main import refresh_tileset
    global SETTINGS
    config = configparser.ConfigParser()
    config.read('settings.ini')
    for section in config.sections():
        for key in config[section]:
            SETTINGS[key] = tryeval(config[section][key])
    refresh_color()
    refresh_tileset()