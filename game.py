import pygame
import math
import random

# --- 초기화 및 설정 ---
pygame.init()
WIDTH, HEIGHT = 800, 400 # 모바일 가로 모드(Landscape)를 위한 해상도
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("LoS Aimbot Mobile")
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
RED = (255, 50, 50)
BLUE = (50, 150, 255)
YELLOW = (255, 200, 0)
GRAY = (100, 100, 100)
GREEN = (50, 255, 50)
DARK_GRAY = (50, 50, 50)

# --- 수학적 예측 계산 (에임봇) ---
def get_predictive_aim_velocity(px, py, ex, ey, evx, evy, bullet_speed):
    dx = ex - px
    dy = ey - py
    a = evx**2 + evy**2 - bullet_speed**2
    b = 2 * (dx * evx + dy * evy)
    c = dx**2 + dy**2
    t = -1 
    if a == 0:
        if b != 0: t = -c / b
    else:
        discriminant = b**2 - 4 * a * c
        if discriminant >= 0:
            t1 = (-b - math.sqrt(discriminant)) / (2 * a)
            t2 = (-b + math.sqrt(discriminant)) / (2 * a)
            if t1 > 0 and t2 > 0: t = min(t1, t2)
            elif t1 > 0: t = t1
            elif t2 > 0: t = t2
    if t <= 0:
        dist = math.hypot(dx, dy)
        if dist == 0: dist = 1
        return (dx/dist)*bullet_speed, (dy/dist)*bullet_speed
    target_x = ex + evx * t
    target_y = ey + evy * t
    tx = target_x - px
    ty = target_y - py
    dist = math.hypot(tx, ty)
    if dist == 0: dist = 1
    return (tx/dist)*bullet_speed, (ty/dist)*bullet_speed

class Enemy:
    def __init__(self):
        self.x = WIDTH // 2 + 100
        self.y = HEIGHT // 2
        self.radius = 15
        self.vx = random.choice([-2.5, 2.5])
        self.vy = random.choice([-2.5, 2.5])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.x - self.radius < 0 or self.x + self.radius > WIDTH:
            self.vx *= -1
            self.x = max(self.radius, min(self.x, WIDTH - self.radius))
        if self.y - self.radius < 0 or self.y + self.radius > HEIGHT:
            self.vy *= -1
            self.y = max(self.radius, min(self.y, HEIGHT - self.radius))

    def draw(self, surface):
        pygame.draw.circle(surface, RED, (int(self.x), int(self.y)), self.radius)

class Bullet:
    def __init__(self, x, y, vx, vy):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.radius, self.speed = 5, 12
    def update(self):
        self.x += self.vx
        self.y += self.vy
    def draw(self, surface):
        pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), self.radius)

class Player:
    def __init__(self):
        self.x, self.y = 100, HEIGHT // 2
        self.radius, self.speed = 15, 4
        self.bullets = []
        self.is_bursting = False
        self.burst_count, self.burst_timer = 0, 0
        self.bullet_speed = 12
        self.mirror_strafing_active = False
        self.target_distance = 0
        self.los_nx, self.los_ny = 0, 0

    def update(self, joy_vec, btn_in, btn_out, enemy):
        if self.mirror_strafing_active:
            # 버튼 입력을 통한 거리 조절
            if btn_in: self.target_distance = max(50, self.target_distance - self.speed)
            if btn_out: self.target_distance = min(700, self.target_distance + self.speed)
            # 타겟에 연동된 미러 스트레이핑
            self.x = enemy.x + self.los_nx * self.target_distance
            self.y = enemy.y + self.los_ny * self.target_distance
        else:
            # 조이스틱 입력을 통한 일반 이동
            self.x += joy_vec[0] * self.speed
            self.y += joy_vec[1] * self.speed

        self.x = max(self.radius, min(self.x, WIDTH - self.radius))
        self.y = max(self.radius, min(self.y, HEIGHT - self.radius))

        if self.is_bursting:
            self.burst_timer -= 1
            if self.burst_timer <= 0:
                b_vx, b_vy = get_predictive_aim_velocity(
                    self.x, self.y, enemy.x, enemy.y, enemy.vx, enemy.vy, self.bullet_speed)
                self.bullets.append(Bullet(self.x, self.y, b_vx, b_vy))
                self.burst_count += 1
                self.burst_timer = 5
                if self.burst_count >= 6: self.is_bursting = False

        for b in self.bullets[:]:
            b.update()
            if b.x < 0 or b.x > WIDTH or b.y < 0 or b.y > HEIGHT:
                self.bullets.remove(b)

    def draw(self, surface):
        pygame.draw.circle(surface, BLUE, (int(self.x), int(self.y)), self.radius)
        for b in self.bullets: b.draw(surface)

def draw_button(surface, rect, text, font, color):
    pygame.draw.rect(surface, color, rect, border_radius=15)
    pygame.draw.rect(surface, WHITE, rect, 2, border_radius=15)
    txt_surf = font.render(text, True, WHITE)
    txt_rect = txt_surf.get_rect(center=rect.center)
    surface.blit(txt_surf, txt_rect)

def main():
    player = Player()
    enemy = Enemy()
    font = pygame.font.SysFont(None, 24)
    big_font = pygame.font.SysFont(None, 36)

    # 모바일 조이스틱 상태
    joy_base = (100, HEIGHT - 100)
    joy_stick = [100, HEIGHT - 100]
    joy_touch_id = None
    joy_vec = (0, 0)
    
    # 모바일 버튼 영역
    rect_fire = pygame.Rect(WIDTH - 140, HEIGHT - 140, 110, 110)
    rect_in = pygame.Rect(WIDTH - 120, HEIGHT - 240, 90, 80)
    rect_out = pygame.Rect(WIDTH - 120, HEIGHT - 120, 90, 80)
    rect_cancel = pygame.Rect(WIDTH - 240, HEIGHT - 120, 100, 80)

    touches = {} # 터치된 위치 관리 {id: (x, y)}

    running = True
    while running:
        clock.tick(60)
        
        btn_in_pressed = False
        btn_out_pressed = False

        # --- 이벤트 처리 (모바일 멀티터치 및 PC 마우스 호환) ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            # 1. 모바일 멀티 터치 (FINGER) 이벤트
            elif event.type in [pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP]:
                tx, ty = event.x * WIDTH, event.y * HEIGHT
                tid = event.finger_id
                
                if event.type == pygame.FINGERDOWN:
                    touches[tid] = (tx, ty)
                    # 화면 좌측 절반: 조이스틱
                    if tx < WIDTH // 2 and joy_touch_id is None:
                        joy_touch_id = tid
                        joy_base = (tx, ty)
                        joy_stick = [tx, ty]
                    # 화면 우측: 버튼
                    if player.mirror_strafing_active:
                        if rect_cancel.collidepoint(tx, ty):
                            player.mirror_strafing_active = False
                    else:
                        if rect_fire.collidepoint(tx, ty) and not player.is_bursting:
                            player.is_bursting = True
                            player.burst_count, player.burst_timer = 0, 0
                            
                elif event.type == pygame.FINGERMOTION:
                    touches[tid] = (tx, ty)
                    if tid == joy_touch_id:
                        dist = math.hypot(tx - joy_base[0], ty - joy_base[1])
                        max_r = 50
                        if dist > max_r:
                            joy_stick[0] = joy_base[0] + (tx - joy_base[0]) / dist * max_r
                            joy_stick[1] = joy_base[1] + (ty - joy_base[1]) / dist * max_r
                        else:
                            joy_stick[0], joy_stick[1] = tx, ty
                            
                elif event.type == pygame.FINGERUP:
                    if tid in touches: del touches[tid]
                    if tid == joy_touch_id:
                        joy_touch_id = None
                        joy_base, joy_stick = (100, HEIGHT - 100), [100, HEIGHT - 100]

            # 2. PC 마우스 이벤트 (테스트용)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if not player.mirror_strafing_active and rect_fire.collidepoint(mx, my):
                    if not player.is_bursting:
                        player.is_bursting = True
                        player.burst_count, player.burst_timer = 0, 0
                elif player.mirror_strafing_active and rect_cancel.collidepoint(mx, my):
                    player.mirror_strafing_active = False
                elif mx < WIDTH // 2:
                    joy_touch_id = "mouse"
                    joy_base, joy_stick = (mx, my), [mx, my]
                    
            elif event.type == pygame.MOUSEMOTION and joy_touch_id == "mouse":
                mx, my = event.pos
                dist = math.hypot(mx - joy_base[0], my - joy_base[1])
                max_r = 50
                if dist > max_r:
                    joy_stick[0] = joy_base[0] + (mx - joy_base[0]) / dist * max_r
                    joy_stick[1] = joy_base[1] + (my - joy_base[1]) / dist * max_r
                else:
                    joy_stick[0], joy_stick[1] = mx, my
                    
            elif event.type == pygame.MOUSEBUTTONUP:
                if joy_touch_id == "mouse":
                    joy_touch_id = None
                    joy_base, joy_stick = (100, HEIGHT - 100), [100, HEIGHT - 100]

        # --- 상태 업데이트 ---
        # 조이스틱 방향 벡터 계산
        joy_vec = (0, 0)
        if joy_touch_id is not None:
            dx, dy = joy_stick[0] - joy_base[0], joy_stick[1] - joy_base[1]
            dist = math.hypot(dx, dy)
            if dist > 0: joy_vec = (dx/dist, dy/dist)

        # 미러 스트레이핑 모드에서 지속적으로 IN/OUT 버튼이 눌려있는지 확인
        if player.mirror_strafing_active:
            for tid, (tx, ty) in touches.items():
                if rect_in.collidepoint(tx, ty): btn_in_pressed = True
                if rect_out.collidepoint(tx, ty): btn_out_pressed = True
            if pygame.mouse.get_pressed()[0]:
                mx, my = pygame.mouse.get_pos()
                if rect_in.collidepoint(mx, my): btn_in_pressed = True
                if rect_out.collidepoint(mx, my): btn_out_pressed = True

        enemy.update()
        player.update(joy_vec, btn_in_pressed, btn_out_pressed, enemy)

        # 총알 충돌 처리
        for b in player.bullets[:]:
            if math.hypot(b.x - enemy.x, b.y - enemy.y) < enemy.radius + b.radius:
                player.bullets.remove(b)
                if not player.mirror_strafing_active:
                    player.mirror_strafing_active = True
                    dx, dy = player.x - enemy.x, player.y - enemy.y
                    cur_dist = math.hypot(dx, dy)
                    if cur_dist == 0: cur_dist = 1
                    player.los_nx, player.los_ny = dx / cur_dist, dy / cur_dist
                    player.target_distance = cur_dist

        # --- 화면 그리기 ---
        screen.fill(BLACK)
        
        # LOS 선 그리기
        if player.mirror_strafing_active:
            end_x, end_y = enemy.x + player.los_nx * 2000, enemy.y + player.los_ny * 2000
            pygame.draw.line(screen, GRAY, (enemy.x, enemy.y), (end_x, end_y), 2)
            pygame.draw.line(screen, GREEN, (enemy.x, enemy.y), (player.x, player.y), 4)

        enemy.draw(screen)
        player.draw(screen)

        # 모바일 UI 그리기
        if player.mirror_strafing_active:
            draw_button(screen, rect_in, "IN", big_font, DARK_GRAY)
            draw_button(screen, rect_out, "OUT", big_font, DARK_GRAY)
            draw_button(screen, rect_cancel, "CANCEL", font, RED)
            
            img = font.render("STATUS: Mirror Strafing ACTIVE!", True, GREEN)
            screen.blit(img, (10, 10))
        else:
            # 좌측: 조이스틱
            pygame.draw.circle(screen, DARK_GRAY, (int(joy_base[0]), int(joy_base[1])), 50, 2)
            pygame.draw.circle(screen, GRAY, (int(joy_stick[0]), int(joy_stick[1])), 25)
            # 우측: 파이어 버튼
            draw_button(screen, rect_fire, "FIRE", big_font, RED)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
