import arcade
from PIL import Image
from random import randint
import threading
import math

FRACTAL_ITERATIONS = 100
FRACTAL_ESCAPE = 1.5
WORKER_THREADS = 5
WINDOW_HEIGHT = 400
WINDOW_WIDTH = 400
INIT_VIRTUAL_GRID_XMIN = -2.0
INIT_VIRTUAL_GRID_XMAX = 2.0
INIT_VIRTUAL_GRID_YMIN = -2.0
INIT_VIRTUAL_GRID_YMAX = 2.0
FRACTAL_COLOR_SCHEME = lambda iter : (min(255,iter*10), iter, iter)

class Mandelbrot(arcade.Window):

    def __init__(self):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.set_caption("Mandelbrot - Python")
        self.xmin = INIT_VIRTUAL_GRID_XMIN
        self.xmax = INIT_VIRTUAL_GRID_XMAX
        self.ymin = INIT_VIRTUAL_GRID_YMIN
        self.ymax = INIT_VIRTUAL_GRID_YMAX
        self.image = None
        self.calculating = False

    @staticmethod
    def _calc_mandelbrot_point(coord):
        prev_x = coord[0]
        prev_y = coord[1]
        for count in range(1,FRACTAL_ITERATIONS+1):
            x = (prev_x ** 2) - (prev_y ** 2) + coord[0]
            y = (2 * (prev_x * prev_y)) + coord[1]
            dist = math.sqrt(x**2 + y**2)
            prev_x = x
            prev_y = y
            if dist > FRACTAL_ESCAPE:
                break
        if count == FRACTAL_ITERATIONS:
            color = (0,0,0)
        else:
            color = FRACTAL_COLOR_SCHEME(count)
        return (coord[0], coord[1], color)

    @staticmethod
    def _calc_mandelbrot_worker(points_subset, results):
        for coord in points_subset:
            calc_point = Mandelbrot._calc_mandelbrot_point(coord)
            results.append(calc_point)

    def _save_results(self, results):
        pil_image = Image.new("RGB", (self.width,self.height)) 
        for coord_x, coord_y, color in results:
            if color != (0,0,0):
                clamp = lambda n, minn, maxn: max(min(maxn, n), minn)
                screen_x = clamp(int(((coord_x - self.xmin) / (self.xmax - self.xmin)) * self.width), 0, self.width - 1)
                screen_y = clamp(int(((coord_y - self.ymin) / (self.ymax - self.ymin)) * self.height), 0, self.height - 1)
                pil_image.putpixel((screen_x, screen_y), color)
        self.image = arcade.Texture(None, pil_image)
        self.calculating = False            

    def _calc_mandelbrot(self):
        points = []
        delta_x = ((self.xmax - self.xmin) / self.width)
        delta_y = ((self.ymax - self.ymin) / self.height)
        x = self.xmin
        while x <= self.xmax:
            y = self.ymin
            while y <= self.ymax:
                points.append((x,y))
                y += delta_y
            x += delta_x
        threads = []
        results = []
        for block in range(WORKER_THREADS):
            start_range = (len(points) // WORKER_THREADS) * block
            end_range = (len(points) // WORKER_THREADS) * (block+1) 
            subset = points[start_range:end_range]
            result = []
            thread = threading.Thread(target=Mandelbrot._calc_mandelbrot_worker, args=(subset,result))
            threads.append(thread)
            results.append(result)
            thread.start()
        for thread in threads:
            thread.join()
        combined_results = []
        for result in results:
            combined_results += result
        self._save_results(combined_results)
    
    def calc_mandelbrot(self):
        self.calculating = True
        thread = threading.Thread(target=self._calc_mandelbrot)
        thread.start()
        
    def zoom(self, screen_x, screen_y, ratio):
        # Calculate the size of the virtual grid using the ratio
        virtual_grid_x_size = ((self.xmax - self.xmin)/2.0) * ratio
        virtual_grid_y_size = ((self.ymax - self.ymin)/2.0) * ratio
        # Calculate the (x,y) of the virtual grid based on the screen (x,y)
        virtual_x = (((screen_x / self.width)) * (self.xmax - self.xmin)) + self.xmin
        virtual_y = (((screen_y / self.height)) * (self.ymax - self.ymin)) + self.ymin
        # Recalculate the virtual grid based centered on virtual (x,y)
        self.xmin = virtual_x - virtual_grid_x_size
        self.xmax = virtual_x + virtual_grid_x_size
        self.ymin = virtual_y - virtual_grid_y_size
        self.ymax = virtual_y + virtual_grid_y_size

    def on_draw(self):
        self.clear()
        if self.image is not None:
            self.image.draw_scaled(self.width//2, self.height//2)
        if self.calculating:
            arcade.draw_text("Calculating ... Please Wait", 5, 5, arcade.color.YELLOW)
            
    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.zoom(x, self.height - y, 0.5)
            self.calc_mandelbrot()        

if __name__ == "__main__":
    mandelbrot = Mandelbrot()
    mandelbrot.calc_mandelbrot()
    arcade.run()





