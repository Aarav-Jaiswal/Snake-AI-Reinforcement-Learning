import pygame
import random
import numpy as np
import torch
import os
import sys
from collections import namedtuple
from model import Linear_QNet

Point = namedtuple('Point', 'x, y')

# Design Token Colors
WHITE = (255, 255, 255)
RED = (200, 0, 0)
BLUE1 = (30, 144, 255)   # AI Snake Blue
BLUE2 = (0, 0, 128)
GREEN1 = (50, 205, 50)   # Human Player Green
GREEN2 = (0, 100, 0)
BLACK = (15, 15, 15)

BLOCK_SIZE = 20
SPEED = 10  
MAX_TOTAL_APPLES = 30  

class PlaygroundArena:
    def __init__(self, w=640, h=480):
        self.w = w
        self.h = h
        pygame.init()
        self.font = pygame.font.SysFont('arial', 20, bold=True)
        self.display = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption('Human vs AI: Playground')
        self.clock = pygame.time.Clock()
        self.reset()

    def reset(self):
        self.apples_left = MAX_TOTAL_APPLES
        self.frame_iteration = 0
        
        # Setup AI Snake (Blue)
        self.head1 = Point(self.w / 4, self.h / 2)
        self.snake1 = [self.head1, Point(self.head1.x - BLOCK_SIZE, self.head1.y), Point(self.head1.x - (2 * BLOCK_SIZE), self.head1.y)]
        self.dir1 = "RIGHT"
        self.score1 = 0
        self.alive1 = True
        
        # Setup Human Snake (Green)
        self.head2 = Point((3 * self.w) / 4, self.h / 2)
        self.snake2 = [self.head2, Point(self.head2.x + BLOCK_SIZE, self.head2.y), Point(self.head2.x + (2 * BLOCK_SIZE), self.head2.y)]
        self.dir2 = "LEFT"
        self.score2 = 0
        self.alive2 = True

        self.food = None
        self._place_food()

    def _place_food(self):
        if self.apples_left <= 0:
            self.food = None
            return
        x = random.randint(0, (self.w - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
        y = random.randint(0, (self.h - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
        self.food = Point(x, y)
        if self.food in self.snake1 or self.food in self.snake2:
            self._place_food()

    def play_step(self, ai_action, human_dir_input):
        self.frame_iteration += 1
        
        # Check human keyboard direction overrides
        if self.alive2 and human_dir_input:
            if human_dir_input == "UP" and self.dir2 != "DOWN": self.dir2 = human_dir_input
            elif human_dir_input == "DOWN" and self.dir2 != "UP": self.dir2 = human_dir_input
            elif human_dir_input == "LEFT" and self.dir2 != "RIGHT": self.dir2 = human_dir_input
            elif human_dir_input == "RIGHT" and self.dir2 != "LEFT": self.dir2 = human_dir_input

        # Update AI direction based on model output
        if self.alive1:
            self.dir1 = self._get_direction(self.dir1, ai_action)
            self.head1 = self._move_head(self.head1, self.dir1)
            self.snake1.insert(0, self.head1)

        # Update Human structural step
        if self.alive2:
            self.head2 = self._move_head(self.head2, self.dir2)
            self.snake2.insert(0, self.head2)

        # Collision assessment
        if self.alive1 and self.is_collision(self.head1, 1):
            self.alive1 = False

        if self.alive2 and self.is_collision(self.head2, 2):
            self.alive2 = False

        # Prevent endless stalling
        if self.frame_iteration > 300 * (len(self.snake1) + len(self.snake2)):
            return True

        # Process Eating Mechanics
        food_eaten = False
        if self.alive1 and self.head1 == self.food:
            self.score1 += 1
            self.apples_left -= 1
            food_eaten = True

        if self.alive2 and self.head2 == self.food:
            self.score2 += 1
            self.apples_left -= 1
            food_eaten = True

        # Trim Tails if empty forward steps
        if self.alive1 and not (food_eaten and self.head1 == self.food):
            self.snake1.pop()
        elif not self.alive1 and len(self.snake1) > 0:
            self.snake1.pop()

        if self.alive2 and not (food_eaten and self.head2 == self.food):
            self.snake2.pop()
        elif not self.alive2 and len(self.snake2) > 0:
            self.snake2.pop()

        if food_eaten:
            self._place_food()

        self._update_ui()
        self.clock.tick(SPEED)

        # END CONFLICT IMMEDIATELY IF EITHER DIES OR APPLES DEPLOYED OUT
        match_over = (not self.alive1 or not self.alive2) or (self.apples_left <= 0)
        return match_over

    def is_collision(self, pt, snake_id):
        if pt.x > self.w - BLOCK_SIZE or pt.x < 0 or pt.y > self.h - BLOCK_SIZE or pt.y < 0:
            return True
        if snake_id == 1:
            if pt in self.snake1[1:] or pt in self.snake2:
                return True
        elif snake_id == 2:
            if pt in self.snake2[1:] or pt in self.snake1:
                return True
        return False

    def _get_direction(self, current_dir, action):
        clock_wise = ["UP", "RIGHT", "DOWN", "LEFT"]
        idx = clock_wise.index(current_dir)
        if np.array_equal(action, [1, 0, 0]): 
            return clock_wise[idx]
        elif np.array_equal(action, [0, 1, 0]): 
            return clock_wise[(idx + 1) % 4]
        else: 
            return clock_wise[(idx - 1) % 4]

    def _move_head(self, head, direction):
        x, y = head.x, head.y
        if direction == "RIGHT": x += BLOCK_SIZE
        elif direction == "LEFT": x -= BLOCK_SIZE
        elif direction == "DOWN": y += BLOCK_SIZE
        elif direction == "UP": y -= BLOCK_SIZE
        return Point(x, y)

    def _update_ui(self):
        self.display.fill(BLACK)
        if self.alive1:
            for pt in self.snake1:
                pygame.draw.rect(self.display, BLUE1, pygame.Rect(pt.x, pt.y, BLOCK_SIZE, BLOCK_SIZE))
        if self.alive2:
            for pt in self.snake2:
                pygame.draw.rect(self.display, GREEN1, pygame.Rect(pt.x, pt.y, BLOCK_SIZE, BLOCK_SIZE))
        if self.food:
            pygame.draw.rect(self.display, RED, pygame.Rect(self.food.x, self.food.y, BLOCK_SIZE, BLOCK_SIZE))

        text = self.font.render(f"AI: {self.score1}  |  YOU: {self.score2}  |  Apples Left: {self.apples_left}", True, WHITE)
        self.display.blit(text, [15, 15])
        pygame.display.flip()

def get_ai_vision(game):
    head = game.head1
    current_direction = game.dir1
    point_l = Point(head.x - BLOCK_SIZE, head.y)
    point_r = Point(head.x + BLOCK_SIZE, head.y)
    point_u = Point(head.x, head.y - BLOCK_SIZE)
    point_d = Point(head.x, head.y + BLOCK_SIZE)
    
    dir_l, dir_r, dir_u, dir_d = current_direction == "LEFT", current_direction == "RIGHT", current_direction == "UP", current_direction == "DOWN"
    food_x = game.food.x if game.food else head.x
    food_y = game.food.y if game.food else head.y

    state = [
        (dir_r and game.is_collision(point_r, 1)) or (dir_l and game.is_collision(point_l, 1)) or (dir_u and game.is_collision(point_u, 1)) or (dir_d and game.is_collision(point_d, 1)),
        (dir_u and game.is_collision(point_r, 1)) or (dir_d and game.is_collision(point_l, 1)) or (dir_l and game.is_collision(point_u, 1)) or (dir_r and game.is_collision(point_d, 1)),
        (dir_d and game.is_collision(point_r, 1)) or (dir_u and game.is_collision(point_l, 1)) or (dir_r and game.is_collision(point_u, 1)) or (dir_l and game.is_collision(point_d, 1)),
        dir_l, dir_r, dir_u, dir_d,
        food_x < head.x, food_x > head.x, food_y < head.y, food_y > head.y
    ]
    return np.array(state, dtype=int)

def run_playground():
    arena = PlaygroundArena()
    model_ai = Linear_QNet(11, 256, 3)
    
    path_options = ['./model/model_blue.pth', './model/model.pth']
    loaded = False

    # Initialize joystick subsystem
    pygame.joystick.init()

    # Check if any controller is plugged in
    if pygame.joystick.get_count() > 0:
        controller = pygame.joystick.Joystick(0)
        controller.init()
        print(f"🎮 Connected to controller: {controller.get_name()}")
    else:
        print("⚠️ No controller detected! Defaulting to Keyboard controls.")

    
    for path in path_options:
        if os.path.exists(path):
            checkpoint = torch.load(path)
            model_ai.load_state_dict(checkpoint['state_dict'])
            model_ai.eval()
            print(f"Loaded AI Brain weights from '{path}' successfully!")
            loaded = True
            break
            
    if not loaded:
        print("ERROR: Could not find any trained model weights in the './model/' directory!")
        return

    print("\nPLAYGROUND ACTIVE: Use ARROW KEYS to move your Green Snake!\n")
    match_finished = False
    human_dir_input = "LEFT"
    
    while not match_finished:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            # 1. Keyboard Listeners
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP: human_dir_input = "UP"
                elif event.key == pygame.K_DOWN: human_dir_input = "DOWN"
                elif event.key == pygame.K_LEFT: human_dir_input = "LEFT"
                elif event.key == pygame.K_RIGHT: human_dir_input = "RIGHT"

            # 2. PS4 D-Pad Listeners
            if event.type == pygame.JOYHATMOTION:
                hat_x, hat_y = event.value
                if hat_y == 1: human_dir_input = "UP"
                elif hat_y == -1: human_dir_input = "DOWN"
                elif hat_x == -1: human_dir_input = "LEFT"
                elif hat_x == 1: human_dir_input = "RIGHT"

            # 3. PS4 Left Analog Stick Listeners
            if event.type == pygame.JOYAXISMOTION:
                if event.axis == 0:  
                    if event.value < -0.5: human_dir_input = "LEFT"
                    elif event.value > 0.5: human_dir_input = "RIGHT"
                elif event.axis == 1:  
                    if event.value < -0.5: human_dir_input = "UP"
                    elif event.value > 0.5: human_dir_input = "DOWN"

        # AI evaluates the state to make a decision
        state_ai = get_ai_vision(arena)
        with torch.no_grad():
            ai_move_idx = torch.argmax(model_ai(torch.tensor(state_ai, dtype=torch.float))).item()
        
        # Initialize action array and apply decision
        ai_action = [0, 0, 0]
        ai_action[ai_move_idx] = 1
        
        # Advance the game step
        match_finished = arena.play_step(ai_action, human_dir_input)



    print("\n" + "═" * 50)
    print(" PLAYGROUND MATCH CONCLUDED ")
    print(f"AI Snake (Blue): {arena.score1} points " + ("(CRASHED)" if not arena.alive1 else "(SURVIVED)"))
    print(f"You (Green): {arena.score2} points " + ("(CRASHED)" if not arena.alive2 else "(SURVIVED)"))
    print("═" * 50)
    
    if arena.score2 > arena.score1 and arena.alive2:
        print("  CONGRATULATIONS! You beat your own creation! ")
    elif arena.score1 > arena.score2 and arena.alive1:
        print("  THE MACHINE WINS! Your AI outplayed you! ")
    else:
        print("  DRAW / CONFLICT TERMINATED! ")
    print("═" * 50 + "\n")
    
    pygame.time.wait(1000)
    pygame.quit()

if __name__ == '__main__':
    run_playground()
