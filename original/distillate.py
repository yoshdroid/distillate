
BLOCK_LIFE = 200
WATER_SPEED = 1
MAX_WATER = 300

######################################################

import pyxel
import random

DEBUG_MODE = True

SIZE_UNIT = 8
WIDTH     = 256 - (SIZE_UNIT-1) # 31
HEIGHT    = 192 - (SIZE_UNIT-1) # 23

MAX_X = WIDTH//SIZE_UNIT
MAX_Y = HEIGHT//SIZE_UNIT

# マップ配列を使わないでどのくらい速度が出るのか試したい 
# 20211212 さすがに存在判定のループが重そう
# blockだけだとそんなことないのだが、いややっぱりおもいか？

#map_array = [[0 for j in range(MAX_Y)] for i in range(MAX_X)]

stage_array = [[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
               [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
               [0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0],
               [0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0],
               [0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0],
               [0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0],
               [0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0],
               [0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1,0],
               [0,1,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,1,0],
               [0,1,0,0,0,0,0,1,1,0,0,1,0,0,0,0,0,0,0,1,0,0,1,1,0,0,0,0,0,1,0],
               [0,1,0,0,0,0,1,0,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0,0,1,0,0,0,0,1,0],
               [0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,1,0],
               [0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0],
               [0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0],
               [0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0],
               [0,1,0,0,0,0,0,0,0,0,0,0,0,1,1,0,1,1,0,0,0,0,0,0,0,0,0,0,0,1,0],
               [0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,3,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0],
               [0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0],
               [0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,1,0],
               [0,1,0,3,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,1,0],
               [0,1,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,1,1,1,1,1,0,0,0,0,0,1,0],
               [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
               [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],]

C_GRAY = 13
C_PALE = 15
C_GREEN = 3
C_BLACK = 0
C_WHITE = 7
C_BROWN = 4
C_YELLOW = 10

C_RED = 14
C_BLUE = 6


water_list = []
block_list = []


def update_list(list):
    for elem in list:
        elem.update()

def draw_list(list):
    for elem in list:
        elem.draw()

def exist_list(list, x, y):
    for elem in list:
        if elem.x==x and elem.y==y:
            return True
    else:
        return False

def draw_bg():
    for y, unit_line in enumerate(stage_array):
        for x, unit in enumerate(unit_line):
            unit = unit & 0xf
            if unit == 1:
                pyxel.rect(x*SIZE_UNIT, y*SIZE_UNIT, SIZE_UNIT, SIZE_UNIT, C_BROWN)
            elif unit == 2:
                pyxel.tri(x*SIZE_UNIT+1, y*SIZE_UNIT+2, (x+1)*SIZE_UNIT-1, y*SIZE_UNIT+2, x*SIZE_UNIT+SIZE_UNIT//2, (y+1)*SIZE_UNIT-2, C_YELLOW)
            elif unit == 3:
                pyxel.tri(x*SIZE_UNIT+1, y*SIZE_UNIT+2, (x+1)*SIZE_UNIT-1, y*SIZE_UNIT+2, x*SIZE_UNIT+SIZE_UNIT//2, (y+1)*SIZE_UNIT-2, C_RED)
    for x in range(WIDTH//SIZE_UNIT + 1):
        pyxel.line(x*SIZE_UNIT, 0, x*SIZE_UNIT, HEIGHT-1, C_GREEN)
    for y in range(HEIGHT//SIZE_UNIT + 1):
        pyxel.line(0, y*SIZE_UNIT, WIDTH-1, y*SIZE_UNIT, C_GREEN)

def generate_water():
    for y, unit_line in enumerate(stage_array):
        for x, unit in enumerate(unit_line):
            if unit == 2:
                count_water = len(water_list)
                if count_water < MAX_WATER:
                    Water(x,y)

def remove_water():
    for y, unit_line in enumerate(stage_array):
        for x, unit in enumerate(unit_line):
            if unit == 3:
                for elem in water_list:
                    if elem.x==x-1 and elem.y==y or elem.x==x+1 and elem.y==y or \
                       elem.x==x and elem.y==y-1 or elem.x==x and elem.y==y+1 :
                        water_list.remove(elem)

def remove_water_all():
    for water in water_list:
        water_list.remove(water)
    for water in water_list:
        water_list.remove(water)

def get_around(x, y):
    around = [False, False, False, False]
    if stage_array[y-1][x] != 0 or exist_list(block_list, x, y-1) or exist_list(water_list, x, y-1):
        around[0] = True
    if stage_array[y+1][x] != 0 or exist_list(block_list, x, y+1) or exist_list(water_list, x, y+1):
        around[1] = True
    if stage_array[y][x-1] != 0 or exist_list(block_list, x-1, y) or exist_list(water_list, x-1, y):
        around[2] = True
    if stage_array[y][x+1] != 0 or exist_list(block_list, x+1, y) or exist_list(water_list, x+1, y):
        around[3] = True
    return around
                
class Water:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.status = 0
        self.vect = [0,0]
        self.stress = 0
        self.around = [True, True, True, True]
        self.birth = pyxel.frame_count
        
        if not exist_list(water_list, x, y):
            water_list.append(self)

    def update(self):
        around = get_around(self.x, self.y)
        if not around[1]: # down
            self.vect = [0,1]
        else:
            self.vect[1] = 0
            if self.vect[0] == 0:
                self.vect[0] = random.randrange(2)*2 - 1
            if self.vect[0] == -1:
                if around[2]: # left exist
                    self.vect[0] = 0
#                if not around[3]:
#                    self.vect[0] = 1
            elif around[3]: # right exist
                self.vect[0] = 0
#                if not around[2]:
#                    self.vect[0] = -1

        self.x = self.x + self.vect[0]
        self.y = self.y + self.vect[1]
    
    def draw(self):
        water_color = C_RED if self.status == 1 else C_BLUE
        dx = self.x * SIZE_UNIT
        dy = self.y * SIZE_UNIT
        pyxel.rect(dx, dy, SIZE_UNIT, SIZE_UNIT, water_color)
        if DEBUG_MODE:
#            pyxel.text(dx+2, dy+2, str(self.vect[0]), 9)
            pass
    
class Block:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.anime = 0
        self.life = BLOCK_LIFE
        self.birth = pyxel.frame_count
        
        if not exist_list(block_list, x, y):
            if x<MAX_X and y<MAX_Y and stage_array[y][x] == 0:
                block_list.append(self)
                
    def update(self):
        if self.life > 0:
            self.life = self.life - 1
            if self.life < (BLOCK_LIFE//8)*1:
                self.anime = 2
            elif self.life < (BLOCK_LIFE//8)*3:
                self.anime = 1
        else:
            block_list.remove(self)

    def draw(self):
        block_color = C_GRAY
        if self.anime == 2:
            block_color = C_GRAY if (pyxel.frame_count % 2) else C_PALE
        elif self.anime == 1:
            block_color = C_GRAY if (pyxel.frame_count % 4 > 0) else C_PALE
        dx = self.x * SIZE_UNIT
        dy = self.y * SIZE_UNIT
        pyxel.rect(dx, dy, SIZE_UNIT, SIZE_UNIT, block_color)
        if DEBUG_MODE:
#            pyxel.text(dx, dy+SIZE_UNIT*1, str(self.anime), 9)
#            pyxel.text(dx, dy+SIZE_UNIT*2, str(self.birth), 9)
#            pyxel.text(dx, dy+SIZE_UNIT*3, str(self.life), 9)
            pass

class App:
    def __init__(self):
#        pyxel.init(WIDTH, HEIGHT, caption="Distillate")
        pyxel.init(WIDTH, HEIGHT, title="Distillate")
        pyxel.mouse(True)
        self.mouse_drug = False
        self.pre_glid_x = 0
        self.pre_glid_y = 0
        self.cool_down = 0
        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        if (self.mouse_drug == True):
#            if pyxel.btnr(pyxel.MOUSE_LEFT_BUTTON):
            if pyxel.btnr(pyxel.MOUSE_BUTTON_LEFT):
                self.mouse_drug = False
        x = pyxel.mouse_x-(pyxel.mouse_x%SIZE_UNIT)
        y = pyxel.mouse_y-(pyxel.mouse_y%SIZE_UNIT)
        glid_x = x // SIZE_UNIT
        glid_y = y // SIZE_UNIT
#        if pyxel.btnp(pyxel.MOUSE_LEFT_BUTTON) or (self.mouse_drug == True):
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) or (self.mouse_drug == True):
            # Bresenham's line algorithm
            x0 = glid_x
            x1 = self.pre_glid_x
            dx = x0 - x1
            sx = 1 if dx < 0 else -1
            dx = -1 * dx if dx < 0 else dx
            y0 = glid_y
            y1 = self.pre_glid_y
            dy = y0 - y1
            sy = 1 if dy < 0 else -1
            dy = -1 * dy if dy < 0 else dy
            err = dx - dy
            while True:
                Block(x0, y0)
                if (x0 == x1) and (y0 == y1):
                    break
                e2 = 2*err
                if e2 > -dy:
                    err = err - dy
                    x0 = x0 + sx
                if e2 < dx:
                    err = err + dx
                    y0 = y0 + sy
            
            self.mouse_drug = True
        self.pre_glid_x = glid_x
        self.pre_glid_y = glid_y
        update_list(block_list)
        if pyxel.btnp(pyxel.KEY_W):
            remove_water_all()
            self.cool_down = 10
        elif self.cool_down > 0:
            self.cool_down = self.cool_down - 1
        elif pyxel.frame_count % WATER_SPEED == 0:
            remove_water()
            generate_water()
            update_list(water_list)


    def draw(self):
        pyxel.cls(0)
        draw_list(block_list)
        draw_list(water_list)
        draw_bg()
        if DEBUG_MODE:
            self.draw_system(0, 0)
        
    def draw_system(self, x, y):
        s = "Elapsed frame count is {}\n" "Current mouse position is ({},{})\n" \
            "Block's list length is {}\n" "Mouse Drug is {}\n" \
            "Water's list length is {}\n".format(
            pyxel.frame_count, pyxel.mouse_x, pyxel.mouse_y, len(block_list), self.mouse_drug,
            len(water_list)
        )
        pyxel.text(x + 1, y, s, 4)
        pyxel.text(x, y, s, 9)
    
App()