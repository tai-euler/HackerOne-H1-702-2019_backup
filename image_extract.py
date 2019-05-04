import sys
from PIL import Image, ImageOps, ImageDraw

charwidth = (4, 10)
charheight = 10
linepadding = 8
centerthreshold = 100
linechars = 112


def minindex(arr):
    minindex = 0
    for i, x in enumerate(arr):
        if x < arr[minindex]:
            minindex = i
    return minindex

im = Image.open(sys.argv[1])
pix = im.load()

output = {}
for x in range(26):
    xoffset = 0
    offset = 6 + (x * (charheight + linepadding))
    chars = []
    output[x] = []

    col = xoffset
    while col < im.size[0]:
        try:
            charstart = col
            charlen = minindex([sum(sum(pix[col + z, offset + y]) for y in range(charheight)) for z in range(*charwidth)]) + charwidth[0]
            chars.append((charstart, charlen))
            col += charlen + 1
        except Exception as e:
            chars.append((charstart, im.size[0] - charstart - 1))
            break

    for i, char in enumerate(chars):
        charstart, charlen = char
        charend = charstart + charlen

        # Center the character width around the character
        while sum(sum(pix[charstart, offset + y]) for y in range(charheight)) / charheight < centerthreshold:
            charstart += 1
        while sum(sum(pix[charend, offset + y]) for y in range(charheight)) / charheight < centerthreshold:
            charend -= 1

        for y in range(charheight):
            pix[charstart, offset + y] = (0, 0, 255)
            pix[charend, offset + y] = (255, 0, 0)
            # Mark every 8 characters with a white border (for my sanity)
            if i % 8 == 7:
                pix[charend, offset + y] = (255, 255, 255)

        if charend - charstart <= 4:
            pix[charstart, offset] = (255, 255, 0)
            output[x].append(1)
        else:
            pix[charstart, offset] = (0, 255, 255)
            output[x].append(0)

print("Extracted output:")
for x in output.keys():
    print("\t{:02}: {}".format(x, "".join(str(y) for y in output[x])))

annotated_name = sys.argv[1].split(".")
annotated_name[-2] = annotated_name[-2] + "_annotated"
annotated_name = ".".join(annotated_name)
im.save(annotated_name)
