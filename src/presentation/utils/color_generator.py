import random, colorsys, math

class UniqueColorGenerator:
    GOLDEN_STEP = 0.61803398875
    MIN_RGB_DIST = 0.30
    BLUE_RANGE  = (0.55, 0.75)

    def __init__(self):
        self.h = random.random()
        self.rgb_used = []

    @staticmethod
    def _rgb_dist(c1, c2):
        return math.sqrt(sum((a-b)**2 for a, b in zip(c1, c2)))

    def _next_hue(self):
        self.h = (self.h + self.GOLDEN_STEP) % 1.0
        return self.h

    def get_color(self):
        for _ in range(360):
            h = self._next_hue()

            if self.BLUE_RANGE[0] <= h <= self.BLUE_RANGE[1]:
                continue

            rgb = colorsys.hsv_to_rgb(h, 0.7, 0.95)
            if all(self._rgb_dist(rgb, prev) >= self.MIN_RGB_DIST for prev in self.rgb_used):
                self.rgb_used.append(rgb)
                return rgb

        h = random.uniform(0.0, self.BLUE_RANGE[0])
        return colorsys.hsv_to_rgb(h, 0.7, 0.95)
    
    def add_used_color(self, color):
        self.rgb_used.append(color)

    def release_color(self, color):
        try:
            self.rgb_used.remove(color)
        except ValueError:
            pass

    def clear_used(self):
        self.rgb_used.clear()
