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
BLUE1 = (30, 144, 255)   # Challenger 1 Blue
BLUE2 = (0, 0, 128)
GREEN1 = (50, 205, 50)   # Challenger 2 Green
GREEN2 = (0, 100, 0)
BLACK = (15, 15, 15)

BLOCK_SIZE = 20
SPEED = 15  #  Set to normal human speed so you can comfortably watch the match!
MAX_TOTAL_APPLES = 15  #  The strict tournament cap rule

class TournamentArena:
    def __init__(self, w=640, h=480):
        self.w = w
        self.h = h
        pygame.init()
        self.font = pygame.font.SysFont('arial', 22, bold=True)
        self.display = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption(' AI Snake Battle Royale: The Grand Finale ')
        self.clock = pygame.time.Clock()
        self.reset()

    def reset(self):
        # Tracker for strict total apples remaining
        self.apples_left = MAX_TOTAL_APPLES
        self.frame_iteration = 0
        
        # Setup Snake 1 (Blue)
        self.head1 = Point(self.w / 4, self.h / 2)
        self.snake1 = [self.head1, Point(self.head1.x - BLOCK_SIZE, self.head1.y), Point(self.head1.x - (2*BLOCK_SIZE), self.head1.y)]
        self.dir1 = "RIGHT"
        self.score1 = 0
        self.alive1 = True
        
        # Setup Snake 2 (Green)
        self.head2 = Point((3 * self.w) / 4, self.h / 2)
        self.snake2 = [self.head2, Point(self.head2.x + BLOCK_SIZE, self.head2.y), Point(self.head2.x + (2*BLOCK_SIZE), self.head2.y)]
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

    def play_step(self, action1, action2):
        self.frame_iteration += 1
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.display.quit()
                quit()

        # Update Directions relative to choices
        if self.alive1:
            self.dir1 = self._get_direction(self.dir1, action1)
            self.head1 = self._move_head(self.head1, self.dir1)
            self.snake1.insert(0, self.head1)

        if self.alive2:
            self.dir2 = self._get_direction(self.dir2, action2)
            self.head2 = self._move_head(self.head2, self.dir2)
            self.snake2.insert(0, self.head2)

        #  Collision rules against walls or opponent bodies
        if self.alive1 and self.is_collision(self.head1, 1):
            self.alive1 = False

        if self.alive2 and self.is_collision(self.head2, 2):
            self.alive2 = False

        # Stop match early if a snake times out without moving efficiently
        if self.frame_iteration > 200 * (len(self.snake1) + len(self.snake2)):
            return True

        # Process Apple Collection Mechanics
        food_eaten = False
        if self.alive1 and self.head1 == self.food:
            self.score1 += 1
            self.apples_left -= 1
            food_eaten = True

        if self.alive2 and self.head2 == self.food:
            self.score2 += 1
            self.apples_left -= 1
            food_eaten = True

        # Trim Tails if apple wasn't consumed
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

        # Match over if both dead, or no apples remaining
        match_over = (not self.alive1 and not self.alive2) or (self.apples_left <= 0)
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
        if np.array_equal(action, [1, 0, 0]): return clock_wise[idx]
        elif np.array_equal(action, [0, 1, 0]): return clock_wise[(idx + 1) % 4]
        else: return clock_wise[(idx - 1) % 4]

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

        text = self.font.render(f"BLUE: {self.score1}  |  GREEN: {self.score2}  |  APPLES REMAINING: {self.apples_left}", True, WHITE)
        self.display.blit(text, [15, 15])
        pygame.display.flip()

#  Helper function to get safe environment parameters for evaluation inputs
def get_snake_vision(game, snake_id):
    head = game.head1 if snake_id == 1 else game.head2
    current_direction = game.dir1 if snake_id == 1 else game.dir2
    point_l = Point(head.x - BLOCK_SIZE, head.y)
    point_r = Point(head.x + BLOCK_SIZE, head.y)
    point_u = Point(head.x, head.y - BLOCK_SIZE)
    point_d = Point(head.x, head.y + BLOCK_SIZE)
    dir_l, dir_r, dir_u, dir_d = current_direction == "LEFT", current_direction == "RIGHT", current_direction == "UP", current_direction == "DOWN"
    
    food_x = game.food.x if game.food else head.x
    food_y = game.food.y if game.food else head.y

    state = [
        (dir_r and game.is_collision(point_r, snake_id)) or (dir_l and game.is_collision(point_l, snake_id)) or (dir_u and game.is_collision(point_u, snake_id)) or (dir_d and game.is_collision(point_d, snake_id)),
        (dir_u and game.is_collision(point_r, snake_id)) or (dir_d and game.is_collision(point_l, snake_id)) or (dir_l and game.is_collision(point_u, snake_id)) or (dir_r and game.is_collision(point_d, snake_id)),
        (dir_d and game.is_collision(point_r, snake_id)) or (dir_u and game.is_collision(point_l, snake_id)) or (dir_r and game.is_collision(point_u, snake_id)) or (dir_l and game.is_collision(point_d, snake_id)),
        dir_l, dir_r, dir_u, dir_d,
        food_x < head.x, food_x > head.x, food_y < head.y, food_y > head.y
    ]
    return np.array(state, dtype=int)

def run_tournament():
    arena = TournamentArena()
    
    # 1. Initialize two separate neural networks
    model_blue = Linear_QNet(11, 256, 3)
    model_green = Linear_QNet(11, 256, 3)
    
    # Paths to the independent model checkpoints
        # Calculate the exact directory where this script resides
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path_blue = os.path.join(base_dir, 'model', 'model_blue.pth')
    path_green = os.path.join(base_dir, 'model', 'model_green.pth')
    path_fallback = os.path.join(base_dir, 'model', 'model.pth')

    
    # 2. Load the Blue Snake model weights safely
    if os.path.exists(path_blue):
        checkpoint_blue = torch.load(path_blue, map_location=torch.device('cpu'))
        model_blue.load_state_dict(checkpoint_blue['state_dict'])
        model_blue.eval() # Freeze brain layers
        print(" Loaded trained weights for BLUE Snake (model_blue.pth) successfully!")
    else:
        # Fallback to default model.pth if specific file isn't found
        if os.path.exists(path_fallback):
            checkpoint_blue = torch.load(path_fallback, map_location=torch.device('cpu'))
            model_blue.load_state_dict(checkpoint_blue['state_dict'])
            model_blue.eval()
            print(" Specific 'model_blue.pth' not found. Falling back to default 'model.pth'.")
        else:
            print(" ERROR: Missing weights file for the Blue Snake!")
            return

    # 3. Load the Green Snake model weights safely
    if os.path.exists(path_green):
        checkpoint_green = torch.load(path_green, map_location=torch.device('cpu'))
        model_green.load_state_dict(checkpoint_green['state_dict'])
        model_green.eval() # Freeze brain layers
        print(" Loaded trained weights for GREEN Snake (model_green.pth) successfully!")
    else:
        # Fallback to default model.pth if specific file isn't found
        if os.path.exists(path_fallback):
            checkpoint_green = torch.load(path_fallback, map_location=torch.device('cpu'))
            model_green.load_state_dict(checkpoint_green['state_dict'])
            model_green.eval()
            print(" Specific 'model_green.pth' not found. Falling back to default 'model.pth'.")
        else:
            print(" ERROR: Missing weights file for the Green Snake!")
            return

    print("\n THE DUAL-MODEL TOURNAMENT MATCH HAS BEGUN! \n")
    match_finished = False
    
    while not match_finished:
        state1 = get_snake_vision(arena, 1)
        state2 = get_snake_vision(arena, 2)
        
        # Calculate moves independently using their designated networks
        with torch.no_grad():
            move1_idx = torch.argmax(model_blue(torch.tensor(state1, dtype=torch.float))).item()
            move2_idx = torch.argmax(model_green(torch.tensor(state2, dtype=torch.float))).item()
        
        action1, action2 = [0, 0, 0], [0, 0, 0]
        action1[move1_idx] = 1
        action2[move2_idx] = 1
        
        match_finished = arena.play_step(action1, action2)

    # Declare the Final Champion Scoreboard
    print("\n" + "═"*50)
    print(" TOURNAMENT FINAL SCOREBOARD ")
    print(f"Blue Snake Score: {arena.score1} points " + ("(DIED)" if not arena.alive1 else "(SURVIVED)"))
    print(f"Green Snake Score: {arena.score2} points " + ("(DIED)" if not arena.alive2 else "(SURVIVED)"))
    print("═"*50)
    
    if arena.score1 > arena.score2:
        print(" CHAMPION: BLUE SNAKE WINS! ")
    elif arena.score2 > arena.score1:
        print(" CHAMPION: GREEN SNAKE WINS! ")
    else:
        print(" MATCH RESULT: IT'S A DRAW! ")
    print("═"*50 + "\n")

    pygame.display.quit()
    return

if __name__ == '__main__':
    run_tournament()
