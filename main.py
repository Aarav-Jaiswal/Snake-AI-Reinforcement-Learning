import pygame
import sys
import os
import datetime

# Initialize Pygame and Font subsystems
pygame.init()
pygame.font.init()

# Window Configuration matching your game dimensions
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🐍 Snake AI Master Control Panel")
clock = pygame.time.Clock()

# Design Tokens (Colors)
BACKGROUND = (20, 24, 30)       # Deep slate cyan
TEXT_COLOR = (240, 244, 248)    # Clean off-white
ACCENT_BLUE = (30, 144, 255)    # AI Blue
ACCENT_GREEN = (50, 205, 50)    # Player Green
ACCENT_ORANGE = (255, 140, 0)   # Spectator Orange
BTN_BG = (35, 43, 53)           # Dark gray button
BTN_HOVER = (50, 60, 75)        # Light gray button

# Typography
title_font = pygame.font.SysFont('arial', 26, bold=True)
btn_font = pygame.font.SysFont('arial', 18, bold=True)

class ConsoleLogger:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 1. Determine the Model Name dynamically
        model_name = "Model"  # Fallback base name
        model_dir = os.path.join(base_dir, 'model')
        
        if os.path.exists(model_dir):
            files = os.listdir(model_dir)
            pth_files = [f for f in files if f.endswith('.pth')]
            if pth_files:
                # Target the main file, extracting "model" from "model.pth"
                model_name = os.path.splitext(pth_files[0])[0]
        
        # 2. Format file name to match exactly: ModelName_log_file.log
        filename = f"{model_name}_log_file.log"
        log_path = os.path.join(base_dir, filename)
        
        # Open in append mode ('a') so it saves history across menu switches
        self.log_file = open(log_path, "a", encoding="utf-8")
        self.terminal = sys.stdout
        self.is_newline = True

    def write(self, message):
        if message == '\n':
            self.terminal.write(message)
            self.log_file.write(message)
            self.is_newline = True
            return

        # Prepend time marker using the correct module reference syntax
        if self.is_newline and message.strip():
            timestamp = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
            self.terminal.write(timestamp)
            self.log_file.write(timestamp)
            self.is_newline = False

        self.terminal.write(message)
        self.log_file.write(message)
        self.log_file.flush()

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()

# Inject the logger globally
sys.stdout = ConsoleLogger()

class Button:
    def __init__(self, x, y, w, h, text, color, action_id):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.base_color = color
        self.action_id = action_id

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        # Hover effect handling
        is_hovered = self.rect.collidepoint(mouse_pos)
        current_bg = BTN_HOVER if is_hovered else BTN_BG
        border_color = self.base_color if is_hovered else (80, 90, 100)

        # Draw filled structural button body
        pygame.draw.rect(surface, current_bg, self.rect, border_radius=8)
        pygame.draw.rect(surface, border_color, self.rect, width=2, border_radius=8)

        # Draw visual indicator dot matching the mode color token
        pygame.draw.circle(surface, self.base_color, (self.rect.x + 20, self.rect.y + self.rect.h // 2), 6)

        # Render and center font elements inside button dimensions
        text_surf = btn_font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=(self.rect.x + self.rect.w // 2 + 10, self.rect.y + self.rect.h // 2))
        surface.blit(text_surf, text_rect)

        return is_hovered

def run_menu():
    global screen
    # Button placements aligned vertically down the screen layout
    buttons = [
        Button(140, 140, 360, 55, "Train Neural Network", ACCENT_BLUE, 1),
        Button(140, 215, 360, 55, "Play Against AI", ACCENT_GREEN, 2),
        Button(140, 290, 360, 55, "Watch AI Tournament", ACCENT_ORANGE, 3),
        Button(140, 375, 360, 45, "Exit App System", (200, 50, 50), 4)
    ]

    while True:
        screen.fill(BACKGROUND)

        # Render Header text overlay
        title_surf = title_font.render("SNAKE AI REINFORCEMENT LEARNING", True, TEXT_COLOR)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, 50))
        screen.blit(title_surf, title_rect)
        
        subtitle_font = pygame.font.SysFont('arial', 14, italic=True)
        sub_surf = subtitle_font.render("Select a core execution subsystem module", True, (130, 140, 150))
        sub_rect = sub_surf.get_rect(center=(WIDTH // 2, 85))
        screen.blit(sub_surf, sub_rect)

        # Event management loop processing mouse tracking controls
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn in buttons:
                    if btn.rect.collidepoint(event.pos):
                        if btn.action_id == 1:
                            from agent import train
                            train()
                            
                            # Clean Display reset chain
                            pygame.display.quit()
                            pygame.display.init()
                            pygame.font.init()  # Re-init fonts safely
                            screen = pygame.display.set_mode((WIDTH, HEIGHT))
                            pygame.display.set_caption("🐍 Snake AI Master Control Panel")
                            
                        elif btn.action_id == 2:
                            from playground import run_playground
                            run_playground()
                            
                            pygame.display.quit()
                            pygame.display.init()
                            pygame.font.init()
                            screen = pygame.display.set_mode((WIDTH, HEIGHT))
                            pygame.display.set_caption("🐍 Snake AI Master Control Panel")
                            
                        elif btn.action_id == 3:
                            from tournament import run_tournament
                            run_tournament()
                            
                            pygame.display.quit()
                            pygame.display.init()
                            pygame.font.init()
                            screen = pygame.display.set_mode((WIDTH, HEIGHT))
                            pygame.display.set_caption("🐍 Snake AI Master Control Panel")
                            
                        elif btn.action_id == 4:
                            pygame.quit()
                            sys.exit()

        # Update and frame draw execution step
        for btn in buttons:
            btn.draw(screen)

        pygame.display.flip()
        clock.tick(30)

if __name__ == '__main__':
    run_menu()
