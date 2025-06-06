from PIL import Image, ImageDraw

class BaseEyeDrawer:
    def draw_eye(self, box, image, fill):
        raise NotImplementedError

class SquareEyeDrawer(BaseEyeDrawer):
    def draw_eye(self, box, image, fill):
        draw = ImageDraw.Draw(image)
        draw.rectangle(box, fill=fill)

class RoundedEyeDrawer(BaseEyeDrawer):
    def draw_eye(self, box, image, fill):
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle(box, radius=6, fill=fill)

class HorizontalBarsEyeDrawer(BaseEyeDrawer):
    def draw_eye(self, box, image, fill):
        draw = ImageDraw.Draw(image)
        x0, y0, x1, y1 = box
        bar_height = (y1 - y0) // 3
        for i in range(3):
            y_start = y0 + i * bar_height
            y_end = y_start + bar_height - 1
            draw.rectangle([x0, y_start, x1, y_end], fill=fill)
