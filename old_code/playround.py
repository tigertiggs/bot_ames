from PIL import Image, GifImagePlugin, ImageDraw, ImageSequence, ImageOps, ImageFont
from io import BytesIO
import requests
import random

"""gif
police_base = Image.open('police.gif')
response = requests.get('https://cdn.discordapp.com/avatars/272389727800524803/86b15aa90cee39f875773adec49e76dc.jpg')
avatar = Image.open(BytesIO(response.content))
avatar = avatar.resize((120,120),Image.ANTIALIAS)
size = (120, 120)
mask = Image.new('L', size, 0)
draw = ImageDraw.Draw(mask) 
draw.ellipse((0, 0) + size, fill=255)
avatar = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
avatar.putalpha(mask)

frames = []
for frame in ImageSequence.Iterator(police_base):
    print(frame.mode)
    frame = frame.copy()#convert(mode="P")
    frame.paste((avatar.convert(mode="RGB")).quantize(palette=frame), (320,150), avatar)
    frames.append(frame)

frames[0].save('test.gif',
                   format='GIF',
                   append_images=frames[1:],
                   save_all=True,
                   duration=60,
                   loop=0)
    
#print(imageObject.is_animated)
#print(imageObject.n_frames)
"""

"""
font = ImageFont.truetype("arial.ttf", 22)
loc = Image.open('location.png')
draw = ImageDraw.Draw(loc)
draw.text((35, 45),"Sample Text LOOOOOOOOOOOOOL"+" wants to",(0,0,0),font=font)
loc.save('sample-out.png')
"""

"""
def gacha_result(t=10):
    ssr_pool, sr_pool, r_pool = read_pool()
    ssr_rate = 0.025
    sr_rate = 0.18
    r_rate = 0.79
    rolls = []
    for i in range(t):
        roll = random.randint(0,1000)
        if (i+1) != 10:
            if roll <= r_rate * 1000:
                chara = random.choice(r_pool)
                rolls.append((chara,1))
            elif roll <= (r_rate + sr_rate) * 1000:
                chara = random.choice(sr_pool)
                rolls.append((chara,2))
            else:
                chara = random.choice(ssr_pool)
                rolls.append((chara,3))
        else:
            if roll <= (r_rate + sr_rate) * 1000:
                chara = random.choice(sr_pool)
                rolls.append((chara,2))
            else:
                rolls.append((chara,3))
    return rolls

def read_pool():
    with open('r.txt') as file:
        r_pool = file.read().splitlines() 
    with open('sr.txt') as file:
        sr_pool = file.read().splitlines()
    with open('ssr.txt') as file:
        ssr_pool = file.read().splitlines()
    return r_pool, sr_pool, ssr_pool
    
print(gacha_result())

# open images
gacha = Image.open('gbg2.png')
rare = Image.open('r2.png')
srare = Image.open('sr2.png')
ssrare = Image.open('ssr2.png')
new = Image.open('new.png')

# sizes
row1 = 80
row2 = 370
spacing = 221
psize = (197,270)
csize = (141,141)
nsize = (80,80)
rs = Image.ANTIALIAS

pxstart = 200
cxstart = 227
cos = 79
nos = -25

# resize
rare = rare.resize(psize, resample=rs)
srare = srare.resize(psize, resample=rs)
ssrare = ssrare.resize(psize, resample=rs)
testchara = Image.open('tp.png')
testchara = testchara.resize(csize, resample=rs)
new = new.resize(nsize, resample=rs)

for i in range(5):
    
    gacha.paste(ssrare, (pxstart + i*spacing, row1), ssrare)
    gacha.paste(testchara, (cxstart + i*spacing, row1 + cos), testchara)
    gacha.paste(new, (pxstart - 25 + i*spacing, row1 - 25), new)
    
    gacha.paste(ssrare, (pxstart + i*spacing, row2),ssrare)
    gacha.paste(testchara, (cxstart + i*spacing, row2 + cos), testchara)
    gacha.paste(new, (pxstart - 25 + i*spacing, row2 - 25), new)

size =  gacha.size
gacha = gacha.resize((round(size[0]*0.5),round(size[1]*0.5)), Image.ANTIALIAS)
gacha.save('gresult.png')
"""

"""
#text = 'the quick brown fox jumped over the panda '*4
#text = "123456789 "*3
#text = "a "*30
text = 'test'
text = 'you have no power here'
length = len(text)
print(length)
if length <= 30:
    limit = 15
    fontsize = 40
elif length <= 60:
    limit = 18
    fontsize = 35
elif length <= 120:
    limit = 20
    fontsize = 22
else:
    limit = 35
    fontsize = 18

breaks = []
words = text.strip().split(" ")
templine = words[0]
lines = 1
for word in words[1:]:
    if len(templine + word + " ") >= limit:
        breaks.append(words.index(word))
        templine = word
        lines += 1
    else:
        templine += (" " + word)

print(breaks)
print(templine)

pos = 0
line = []
if breaks:
    for _break in breaks:
        line.append(" ".join(words[pos:_break]))
        pos = _break
    line.append(" ".join(words[pos:]))
    temptext = "\n".join(line)
else:
    temptext = templine

print(line)
pos = (25, -10*lines+80)
text = temptext
        
        
nero = Image.open('nero.jpg')
font = ImageFont.truetype("arial.ttf", fontsize)

#txt = Image.new('RGBA',(350,200),"blue")
txt = Image.new('L', (350,200))
dtxt = ImageDraw.Draw(txt)
w, h = dtxt.textsize(text,font=font)
#print(w, h)
dtxt.text(((350-w)/2,(200-h)/2), text, font=font, fill=255)
dtxt2 = txt.rotate(10, expand=1)

nero.paste(ImageOps.colorize(dtxt2, (0,0,0), (0,0,0)), (-10,-20), dtxt2)
#nero.paste(dtxt2,(-10,-20),dtxt2)
nero.save('nerosays.jpg')
"""

"""
def test(t:int, *args:int, mode=0):
    print(t)
    print(args, len(args))
    if len(args) > 3:
        return
    for things in args:
        print(things)
        print(type(things))
    print(mode)
    return

test(10,10,10,10,mode=1)
"""

"""
threat = Image.open('threaten/threaten.png')
threater = Image.open('test.png')
threatened = Image.open('test.png')

if threater.is_animated:
    threater.seek(threater.n_frames//2)
    threater = threater.convert(mode="RGB")
if threatened.is_animated:
    threatened.seek(threatened.n_frames//2)
    threatened = threatened.convert(mode="RGB")

size = (90, 90)
threater.resize(size,resample=Image.ANTIALIAS)
threatened.resize(size,resample=Image.ANTIALIAS)

mask = Image.new('L', size, 0)
draw = ImageDraw.Draw(mask) 
draw.ellipse((0, 0) + size, fill=255)

threater = ImageOps.fit(threater, mask.size, centering=(0.5, 0.5))
threater.putalpha(mask)
threatened = ImageOps.fit(threatened, mask.size, centering=(0.5, 0.5))
threatened.putalpha(mask)

threat.paste(threater, (20,100), threater)
threat.paste(threatened, (210,50), threatened)

threat.save('threaten/threat.png')

"""

"""
text = 'WA20 is the best rifle in GFL'*2
#text = "123456789 "*3
#text = "a "*30

length = len(text)

change = Image.open('mind/change.jpg')
author = Image.open('test.png')
if author.is_animated:
    threater.seek(threater.n_frames//2)
    threater = threater.convert(mode="RGB")

# find good font and size set depending on text length
print(length)
if length <= 30:
    limit = 22
    fontsize = 22
elif length <= 60:
    limit = 22
    fontsize = 17
else:
    print('nero: input text length exceeds maximum allowable')

# breaking text up to fit
breaks = []
words = text.strip().split(" ")
templine = words[0]
lines = 1

for i in range(len(words[1:])):
    word = words[i+1]
    if len(templine + word + " ") >= limit:
        j = 0
        while words.index(word, j) < i:
            j += 1
        breaks.append(words.index(word, j))
        templine = word
        lines += 1
    else:
        templine += (" " + word)
        
pos = 0
line = []

# break text
if breaks:
    for _break in breaks:
        line.append(" ".join(words[pos:_break]))
        pos = _break
    line.append(" ".join(words[pos:]))
    temptext = "\n".join(line)
else:
    temptext = templine

#pos = (25, -10*lines+80)
text = temptext
font = ImageFont.truetype("arial.ttf", fontsize)

size = (100,100)
author.resize(size,resample=Image.ANTIALIAS)
mask = Image.new('L', size, 0)
draw = ImageDraw.Draw(mask) 
draw.ellipse((0, 0) + size, fill=255)
author = ImageOps.fit(author, mask.size, centering=(0.5, 0.5))
author.putalpha(mask)

#txt = Image.new('RGBA',(185,80),"blue")
txt = Image.new('L', (185,80))
dtxt = ImageDraw.Draw(txt)
w, h = dtxt.textsize(text,font=font)
print(w, h)
dtxt.text(((185-w)/2,(80-h)/2), text, font=font, fill=255)
dtxt2 = txt.rotate(6, expand=1)
change.paste(ImageOps.colorize(dtxt2, (0,0,0), (0,0,0)), (220,210), dtxt2)
change.paste(author, (140,5), author)
#change.paste(dtxt2,(220,210),dtxt2)
change.save('mind/changemymind.png')
change.close()
"""




















