"""
Clipboard and selection model for Femto.

All mutations call buffer.touch() so buffer.revision stays the single
source of truth for cache invalidation (PR #29 contract).
"""


class Clipboard:
    def __init__(self):
        self.text = ""

    @property
    def empty(self):
        return self.text == ""

    def store(self, text):
        self.text = text

    def paste_into(self, buffer, x, y):
        text = self.text
        if not text:
            return x, y
        chunks = text.split("\n")
        if len(chunks) == 1:
            buffer.lines[y] = buffer.lines[y][:x] + text + buffer.lines[y][x:]
            buffer.touch()
            return x + len(text), y
        first = buffer.lines[y][:x] + chunks[0]
        last = chunks[-1] + buffer.lines[y][x:]
        middle = chunks[1:-1]
        buffer.lines[y:y + 1] = [first] + middle + [last]
        buffer.touch()
        return len(chunks[-1]), y + len(chunks) - 1


class Selection:
    def __init__(self):
        self.active = False
        self.start_x = 0
        self.start_y = 0

    def toggle(self, x, y):
        if self.active:
            self.clear()
        else:
            self.active = True
            self.start_x = x
            self.start_y = y

    def clear(self):
        self.active = False

    def bounds(self, buffer, cx, cy):
        sx, sy = self.start_x, self.start_y
        ex, ey = cx, cy
        if (sy, sx) > (ey, ex):
            sx, sy, ex, ey = ex, ey, sx, sy
        max_y = len(buffer.lines) - 1
        sy = max(0, min(sy, max_y))
        ey = max(0, min(ey, max_y))
        sx = max(0, min(sx, len(buffer.lines[sy])))
        ex = max(0, min(ex, len(buffer.lines[ey])))
        return ((sx, sy), (ex, ey))

    def extract(self, buffer, bounds):
        (sx, sy), (ex, ey) = bounds
        if sy == ey:
            return buffer.lines[sy][sx:ex]
        out = [buffer.lines[sy][sx:]]
        out.extend(buffer.lines[sy + 1:ey])
        out.append(buffer.lines[ey][:ex])
        return "\n".join(out)

    def delete_range(self, buffer, bounds):
        (sx, sy), (ex, ey) = bounds
        if sy == ey:
            line = buffer.lines[sy]
            buffer.lines[sy] = line[:sx] + line[ex:]
            buffer.touch()
            return sx, sy
        top = buffer.lines[sy][:sx]
        bot = buffer.lines[ey][ex:]
        buffer.lines[sy:ey + 1] = [top + bot]
        buffer.touch()
        return sx, sy
