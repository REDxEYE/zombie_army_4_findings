from pathlib import Path

from PIL.Image import open

root = Path(r'D:\SteamLibrary\steamapps\common\ZombieArmy4\UNPACK\graphics\characters\zap_characters\zombies\zombie_shark\final')

for file in root.glob('*.dds'):
    try:
        im = open(file)
        im.save(file.with_suffix('.tga'))
    except NotImplementedError as e:
        print(f'Failed to fix {file}, {e}')
