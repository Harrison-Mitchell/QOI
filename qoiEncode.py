from sys import argv
from PIL import Image

if len(argv) != 3:
    exit(f"Usage: python3 {argv[0]} <in.png> <out.qoi>") 

qoi = open(argv[2], "wb")

QOI_OP_RGB   = 0b11111110
QOI_OP_RGBA  = 0b11111111
QOI_OP_INDEX = 0b00000000
QOI_OP_DIFF  = 0b01000000
QOI_OP_LUMA  = 0b10000000
QOI_OP_RUN   = 0b11000000

class Pixel:
    def __init__(self, r = 0, g = 0, b = 0):
        self.r = r
        self.g = g
        self.b = b
    def key(self):
        return (self.r * 3 + self.g * 5 + self.b * 7) % 64
    def __sub__(self, comp):
        return Pixel(self.r - comp.r, self.g - comp.g, self.b - comp.b)
    def __eq__(self, comp):
        return self.r == comp.r and self.g == comp.g and self.b == comp.b

def writeByte(val, n=1):
    qoi.write(val.to_bytes(n, 'big'))

# Parse PNG
image = Image.open(png_file_name)
pixels = image.getdata()
width, height = image.size

# Init encoding variables
seenPixels = [Pixel() for _ in range(64)]
previous = Pixel()
runLength = 0

# Write QOI file headers
writeByte(ord("q"))
writeByte(ord("o"))
writeByte(ord("i"))
writeByte(ord("f"))
writeByte(width, 4)
writeByte(height, 4)
writeByte(3) # 3 = 3 channels = RGB
writeByte(1) # 1 = linear channels

for r, g, b in pixels:
    current = Pixel(r, g, b)

    # Spec Case 1: "a run of the previous pixel"
    if current == previous:
        runLength += 1
        # Due to QOI_OP_RGB and QOI_OP_RGBA overlaps runs are limited to 62
        if runLength == 62:
            writeByte(QOI_OP_RUN | runLength - 1)
            previous = current
            runLength = 0
    else:
        # Dump run; new pixel or max run reached
        if runLength > 0:
            writeByte(QOI_OP_RUN | runLength - 1)
            runLength = 0

        # Spec Case 2: "an index into an array of previously seen pixels"
        key = current.key()
        if current == seenPixels[key]:
            writeByte(QOI_OP_INDEX | key)

        # Not a run, nor a previously seen pixel
        else:
            seenPixels[key] = current
            diff = current - previous
            diffRG = diff.r - diff.g
            diffBG = diff.b - diff.g

            # Spec Case 3.1: "a difference to the previous pixel value in r,g,b" (small)
            if (-2 <= diff.r <= 1 and -2 <= diff.g <= 1 and -2 <= diff.b <= 1):
                writeByte(QOI_OP_DIFF | diff.r + 2 << 4 | diff.g + 2 << 2 | diff.b + 2)

            # Spec Case 3.2: "a difference to the previous pixel value in r,g,b" (large)
            elif (-32 <= diff.g <= 31 and -8 <= diffRG <= 7 and -8 <= diffBG <= 7):
                writeByte(QOI_OP_LUMA | diff.g + 32)
                writeByte(diffRG + 8 << 4 | diffBG + 8)
            
            # Spec Case 4: "full r,g,b or r,g,b,a values"
            else:
                writeByte(QOI_OP_RGB)
                writeByte(current.r)
                writeByte(current.g)
                writeByte(current.b)

    previous = current