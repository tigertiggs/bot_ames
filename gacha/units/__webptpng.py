import os
import glob
from PIL import Image

def webptpng():
    for webp in glob.glob("*.webp"):
        im = Image.open(webp)
        im.save("png/{:s}.png".format(webp[:-5]))
        im.close()

webptpng()
