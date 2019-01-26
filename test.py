import json

from PIL import Image, ImageFilter


size = 250, 150
def createThumbnail(filepath):
    try:
        im = Image.open(filepath)
        im.thumbnail(size)
        outfile = filepath + ".thumbnail"
        im.save(outfile, "JPEG")
        return im
    except IOError:
        print "cannot create thumbnail"


filepath = 'images/00f53bc8-8f0a-8ca0-11e3-e0ff8c690a69.JPG'
new_img = createThumbnail(filepath)
new_img.show()
