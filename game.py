import pygame
import math
import random

# --- 초기화 및 화면 설정 ---
pygame.init()
WIDTH, HEIGHT = 1000, 500  # 모바일 가로 환경을 위한 넉넉한 해상도
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Brawl Stars - Authentic Colt (2026 Meta) & LoS Aimbot")
clock = pygame.time.Clock()

# --- 색상 정의 ---
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
RED = (255, 50, 50)
BLUE = (50, 150, 255)
YELLOW = (255, 200, 0)
GRAY = (100, 100, 100)
GREEN = (50, 255, 50)
DARK_GRAY = (40, 40, 40)
PURPLE = (200, 0, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
SILVER = (192, 192, 192)

# --- 유틸리티 및 예측 사격(에임봇) 알고리즘 ---
def get_predictive_aim_velocity(px, py, ex, ey, evx, evy, bullet_speed):
    dx, dy = ex - px, ey - py
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
    tx, ty = ex + evx * t - px, ey + evy * t - py
    dist = math.hypot(tx, ty)
    if dist == 0: dist = 1
    return (tx/dist)*bullet_speed, (ty/dist)*bullet_speed

# --- 게임 오브젝트 ---
class Wall:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
    def draw(self, surface):
        pygame.draw.rect(surface, ORANGE, self.rect, border_radius=5)
        pygame.draw.rect(surface, DARK_GRAY, self.rect, 2, border_radius=5)

class Enemy:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.x = random.randint(WIDTH // 2, WIDTH - 50)
        self.y = random.randint(50, HEIGHT - 50)
        self.radius = 18
        self.vx = random.choice([-3, 3])
        self.vy = random.choice([-3, 3])
        self.max_hp = 10000
        self.hp = self.max_hp

    def update(self, walls):
        self.x += self.vx
        self.y += self.vy
        
        # 벽 튕기기
        rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)
        for w in walls:
            if rect.colliderect(w.rect):
                self.vx *= -1
                self.vy *= -1
                self.x += self.vx * 2
                self.y += self.vy * 2
                break

        # 화면 끝 튕기기
        if self.x - self.radius < 0 or self.x + self.radius > WIDTH:
            self.vx *= -1
            self.x = max(self.radius, min(self.x, WIDTH - self.radius))
        if self.y - self.radius < 0 or self.y + self.radius > HEIGHT:
            self.vy *= -1
            self.y = max(self.radius, min(self.y, HEIGHT - self.radius))

    def draw(self, surface):
        pygame.draw.circle(surface, RED, (int(self.x), int(self.y)), self.radius)
        # HP Bar
        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(surface, DARK_GRAY, (self.x - 20, self.y - 30, 40, 6))
        pygame.draw.rect(surface, GREEN, (self.x - 20, self.y - 30, 40 * hp_ratio, 6))

class Bullet:
    def __init__(self, x, y, vx, vy, damage, size, pierce, color):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.damage = damage
        self.radius = size
        self.pierce = pierce
        self.color = color
        self.active = True
        self.hit_targets = set() # 관통 메커니즘을 위한 피격 기록

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

class AuthenticColt:
    def __init__(self):
        self.x, self.y = 100, HEIGHT // 2
        self.radius = 18
        
        # --- 콜트 2026 메타 디컴파일 스탯 ---
        self.max_hp = 6200
        self.hp = self.max_hp
        self.base_speed = 4.5       # 기본 720
        self.base_damage = 720      # 11레벨 기준 1발당
        self.base_bullet_speed = 25 # 기본 탄속 (약 4000)
        
        # 탄창 & 장전 (Reload: 1.3초 = 78프레임)
        self.ammo = 3
        self.reload_timer = 0
        self.reload_time_max = 78 
        
        # 궁극기 (Bullet Storm) & 하이퍼차지 (Dual Wielding)
        self.super_charge = 0
        self.super_charge_max = 12  # 12대 적중 시 완충
        self.hc_charge = 0
        self.hc_charge_max = 35     # 35대 적중 시 완충
        
        self.hc_active = False
        self.hc_timer = 0
        self.hc_duration = 60 * 7   # 7초 지속
        
        # 스타파워 & 가젯
        self.star_power = "Slick Boots" # "Slick Boots" 또는 "Magnum Special"
        self.gadget_uses = 3
        self.silver_bullet_active = False
        
        # 발사 제어
        self.bullets = []
        self.is_bursting = False
        self.burst_type = "normal"
        self.burst_count = 0
        self.burst_timer = 0
        
        # 미러 스트레이핑
        self.mirror_strafing = False
        self.target_dist = 0
        self.los_nx, self.los_ny = 0, 0

    def get_current_stats(self):
        # 스타파워 및 하이퍼차지 버프 실시간 계산
        speed = self.base_speed
        b_speed = self.base_bullet_speed
        dmg_mult = 1.0
        
        if self.hc_active:
            speed *= 1.20 # 하이퍼차지 이속 +20%
            dmg_mult *= 1.05 # 하이퍼차지 딜 +5%
            
        if self.star_power == "Slick Boots":
            speed *= 1.13 # 이속 +13%
        elif self.star_power == "Magnum Special":
            b_speed *= 1.11 # 탄속 및 사거리 +11%
            
        return speed, b_speed, dmg_mult

    def update(self, joy_vec, btn_in, btn_out, enemy, walls):
        cur_speed, cur_b_speed, cur_dmg_mult = self.get_current_stats()
        
        # 1. 이동
        if self.mirror_strafing:
            if btn_in: self.target_dist = max(50, self.target_dist - cur_speed)
            if btn_out: self.target_dist = min(800, self.target_dist + cur_speed)
            self.x = enemy.x + self.los_nx * self.target_dist
            self.y = enemy.y + self.los_ny * self.target_dist
        else:
            self.x += joy_vec[0] * cur_speed
            self.y += joy_vec[1] * cur_speed

        self.x = max(self.radius, min(self.x, WIDTH - self.radius))
        self.y = max(self.radius, min(self.y, HEIGHT - self.radius))

        # 2. 재장전 시스템 (하이퍼차지 시 딜레이 약간 증가 반영)
        if self.ammo < 3 and not self.is_bursting:
            self.reload_timer -= 1
            if self.reload_timer <= 0:
                self.ammo += 1
                self.reload_timer = int(self.reload_time_max * (1.1 if self.hc_active else 1.0))

        # 3. 하이퍼차지 타이머
        if self.hc_active:
            self.hc_timer -= 1
            if self.hc_timer <= 0:
                self.hc_active = False

        # 4. 연사 발사 시스템
        if self.is_bursting:
            self.burst_timer -= 1
            if self.burst_timer <= 0:
                b_vx, b_vy = get_predictive_aim_velocity(
                    self.x, self.y, enemy.x, enemy.y, enemy.vx, enemy.vy, cur_b_speed)

                if self.burst_type == "silver":
                    # 가젯: 실버 불렛 (피해량 1440, 벽 관통)
                    b = Bullet(self.x, self.y, b_vx, b_vy, 1440 * cur_dmg_mult, 12, True, SILVER)
                    self.bullets.append(b)
                    self.is_bursting = False
                    self.silver_bullet_active = False
                    self.reload_timer = self.reload_time_max
                    
                elif self.burst_type == "super":
                    # 궁극기: 12연발, 관통, (하이퍼차지 시 크기 1.4배 증가)
                    size = 14 if self.hc_active else 10
                    b = Bullet(self.x, self.y, b_vx, b_vy, 640 * cur_dmg_mult, size, True, YELLOW)
                    self.bullets.append(b)
                    self.burst_count += 1
                    self.burst_timer = 2 # 궁극기는 더 빨리 쏟아냄
                    if self.burst_count >= 12: 
                        self.is_bursting = False
                        
                else: # normal (6연발)
                    b = Bullet(self.x, self.y, b_vx, b_vy, self.base_damage * cur_dmg_mult, 6, False, WHITE)
                    self.bullets.append(b)
                    self.burst_count += 1
                    # Buffie Effect: 하이퍼차지 시 언로드 속도 50% 단축
                    self.burst_timer = 2 if self.hc_active else 4
                    if self.burst_count >= 6: 
                        self.is_bursting = False
                        self.reload_timer = self.reload_time_max

        # 5. 총알 업데이트 및 충돌 처리
        for b in self.bullets[:]:
            b.update()
            
            # 화면 밖 삭제
            if b.x < 0 or b.x > WIDTH or b.y < 0 or b.y > HEIGHT:
                if b in self.bullets: self.bullets.remove(b)
                continue
                
            # 벽 충돌
            hit_wall = False
            for w in walls[:]:
                if w.rect.collidepoint(b.x, b.y):
                    if b.pierce:
                        walls.remove(w) # 궁/실버불렛은 벽을 파괴!
                    else:
                        hit_wall = True # 일반탄은 막힘
                        break
            if hit_wall:
                if b in self.bullets: self.bullets.remove(b)
                continue

            # 적 충돌
            if enemy.hp > 0 and math.hypot(b.x - enemy.x, b.y - enemy.y) < enemy.radius + b.radius:
                if id(enemy) not in b.hit_targets:
                    b.hit_targets.add(id(enemy))
                    enemy.hp -= b.damage
                    
                    # 궁/하차 게이지 충전
                    self.super_charge = min(self.super_charge_max, self.super_charge + 1)
                    if not self.hc_active:
                        self.hc_charge = min(self.hc_charge_max, self.hc_charge + 1)
                    
                    # 미러 스트레이핑 트리거 (LOS 고정)
                    if not self.mirror_strafing:
                        self.mirror_strafing = True
                        dx, dy = self.x - enemy.x, self.y - enemy.y
                        dist = math.hypot(dx, dy)
                        if dist == 0: dist = 1
                        self.los_nx, self.los_ny = dx/dist, dy/dist
                        self.target_dist = dist
                        
                    if not b.pierce:
                        if b in self.bullets: self.bullets.remove(b)

    def draw(self, surface):
        color = PURPLE if self.hc_active else BLUE
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.radius)
        
        # 하이퍼차지 실드 효과 (5%)
        if self.hc_active:
            pygame.draw.circle(surface, CYAN, (int(self.x), int(self.y)), self.radius + 5, 2)
            
        for b in self.bullets: 
            b.draw(surface)
            
        # 탄창 표시
        for i in range(3):
            c = YELLOW if i < self.ammo else GRAY
            pygame.draw.rect(surface, c, (self.x - 15 + (i * 12), self.y - 30, 8, 5))

# --- UI 그리기 헬퍼 ---
def draw_btn(surface, rect, text, font, color, active=True):
    c = color if active else DARK_GRAY
    pygame.draw.rect(surface, c, rect, border_radius=10)
    pygame.draw.rect(surface, WHITE, rect, 2, border_radius=10)
    txt = font.render(text, True, WHITE if active else GRAY)
    tr = txt.get_rect(center=rect.center)
    surface.blit(txt, tr)

def main():
    player = AuthenticColt()
    enemy = Enemy()
    
    # 맵에 파괴 가능한 벽들 생성
    walls = [
        Wall(400, 100, 40, 150),
        Wall(600, 250, 40, 150),
        Wall(200, 300, 100, 40)
    ]
    
    font = pygame.font.SysFont(None, 24)
    big_font = pygame.font.SysFont(None, 36)

    joy_base, joy_stick = (120, HEIGHT - 120), [120, HEIGHT - 120]
    joy_touch_id = None
    joy_vec = (0, 0)
    touches = {}

    # 우측 버튼 레이아웃
    r_fire = pygame.Rect(WIDTH - 130, HEIGHT - 130, 100, 100)
    r_super = pygame.Rect(WIDTH - 240, HEIGHT - 110, 80, 80)
    r_gadget = pygame.Rect(WIDTH - 110, HEIGHT - 240, 70, 70)
    r_hyper = pygame.Rect(WIDTH - 220, HEIGHT - 220, 80, 80)
    
    r_sp_toggle = pygame.Rect(WIDTH - 250, 20, 230, 40)
    
    # 미러 스트레이핑 IN/OUT 거리조절 버튼 (중앙 하단)
    r_in = pygame.Rect(WIDTH//2 - 100, HEIGHT - 90, 80, 70)
    r_out = pygame.Rect(WIDTH//2 + 20, HEIGHT - 90, 80, 70)
    r_cancel = pygame.Rect(WIDTH//2 - 60, HEIGHT - 180, 120, 60)

    running = True
    while running:
        clock.tick(60)
        btn_in_pressed, btn_out_pressed = False, False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            # 모바일 멀티 터치 (FINGER)
            elif event.type in [pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP]:
                tx, ty = event.x * WIDTH, event.y * HEIGHT
                tid = event.finger_id
                
                if event.type == pygame.FINGERDOWN:
                    touches[tid] = (tx, ty)
                    if tx < WIDTH // 3 and joy_touch_id is None:
                        joy_touch_id = tid
                        joy_base = (tx, ty)
                        joy_stick = [tx, ty]
                    else:
                        # 버튼 처리
                        if r_sp_toggle.collidepoint(tx, ty):
                            player.star_power = "Magnum Special" if player.star_power == "Slick Boots" else "Slick Boots"
                            
                        if player.mirror_strafing and r_cancel.collidepoint(tx, ty):
                            player.mirror_strafing = False
                            
                        if not player.is_bursting:
                            if r_fire.collidepoint(tx, ty) and player.ammo > 0:
                                player.is_bursting = True
                                player.burst_type = "silver" if player.silver_bullet_active else "normal"
                                player.ammo -= 1
                                player.burst_count, player.burst_timer = 0, 0
                                
                            elif r_super.collidepoint(tx, ty) and player.super_charge >= player.super_charge_max:
                                player.is_bursting = True
                                player.burst_type = "super"
                                player.super_charge = 0 # 궁 소모
                                player.burst_count, player.burst_timer = 0, 0
                                
                            elif r_gadget.collidepoint(tx, ty) and player.gadget_uses > 0 and not player.silver_bullet_active:
                                player.silver_bullet_active = True
                                player.gadget_uses -= 1
                                
                            elif r_hyper.collidepoint(tx, ty) and player.hc_charge >= player.hc_charge_max:
                                player.hc_active = True
                                player.hc_charge = 0
                                player.hc_timer = player.hc_duration

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
                        joy_base, joy_stick = (120, HEIGHT - 120), [120, HEIGHT - 120]

            # PC 마우스 지원
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if r_sp_toggle.collidepoint(mx, my):
                    player.star_power = "Magnum Special" if player.star_power == "Slick Boots" else "Slick Boots"
                if player.mirror_strafing and r_cancel.collidepoint(mx, my):
                    player.mirror_strafing = False
                if not player.is_bursting:
                    if r_fire.collidepoint(mx, my) and player.ammo > 0:
                        player.is_bursting = True
                        player.burst_type = "silver" if player.silver_bullet_active else "normal"
                        player.ammo -= 1
                        player.burst_count, player.burst_timer = 0, 0
                    elif r_super.collidepoint(mx, my) and player.super_charge >= player.super_charge_max:
                        player.is_bursting = True
                        player.burst_type = "super"
                        player.super_charge = 0
                        player.burst_count, player.burst_timer = 0, 0
                    elif r_gadget.collidepoint(mx, my) and player.gadget_uses > 0 and not player.silver_bullet_active:
                        player.silver_bullet_active = True
                        player.gadget_uses -= 1
                    elif r_hyper.collidepoint(mx, my) and player.hc_charge >= player.hc_charge_max:
                        player.hc_active = True
                        player.hc_charge = 0
                        player.hc_timer = player.hc_duration
                elif mx < WIDTH // 3:
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
                    joy_base, joy_stick = (120, HEIGHT - 120), [120, HEIGHT - 120]

        joy_vec = (0, 0)
        if joy_touch_id is not None:
            dx, dy = joy_stick[0] - joy_base[0], joy_stick[1] - joy_base[1]
            dist = math.hypot(dx, dy)
            if dist > 0: joy_vec = (dx/dist, dy/dist)

        # 미러 스트레이핑 IN/OUT 체크
        if player.mirror_strafing:
            for tid, (tx, ty) in touches.items():
                if r_in.collidepoint(tx, ty): btn_in_pressed = True
                if r_out.collidepoint(tx, ty): btn_out_pressed = True
            if pygame.mouse.get_pressed()[0]:
                mx, my = pygame.mouse.get_pos()
                if r_in.collidepoint(mx, my): btn_in_pressed = True
                if r_out.collidepoint(mx, my): btn_out_pressed = True

        # 상태 업데이트
        enemy.update(walls)
        player.update(joy_vec, btn_in_pressed, btn_out_pressed, enemy, walls)
        
        if enemy.hp <= 0:
            enemy.reset() # 적 죽으면 자동 리스폰

        # --- 화면 그리기 ---
        screen.fill(BLACK)
        
        # 바닥 그리드 및 LOS
        if player.mirror_strafing:
            pygame.draw.line(screen, GRAY, (enemy.x, enemy.y), (enemy.x + player.los_nx * 2000, enemy.y + player.los_ny * 2000), 2)
            pygame.draw.line(screen, GREEN, (enemy.x, enemy.y), (player.x, player.y), 4)

        for w in walls: w.draw(screen)
        enemy.draw(screen)
        player.draw(screen)

        # --- UI 렌더링 ---
        # 1. 조이스틱
        pygame.draw.circle(screen, DARK_GRAY, (int(joy_base[0]), int(joy_base[1])), 50, 2)
        pygame.draw.circle(screen, GRAY, (int(joy_stick[0]), int(joy_stick[1])), 25)

        # 2. 우측 스킬 버튼
        draw_btn(screen, r_fire, "FIRE" if not player.silver_bullet_active else "SILVER", font, SILVER if player.silver_bullet_active else RED, player.ammo > 0)
        draw_btn(screen, r_super, "SUPER", font, YELLOW, player.super_charge >= player.super_charge_max)
        draw_btn(screen, r_hyper, "HYPER", font, PURPLE, player.hc_charge >= player.hc_charge_max)
        draw_btn(screen, r_gadget, f"GADGET({player.gadget_uses})", font, GREEN, player.gadget_uses > 0)
        
        # 3. SP 토글 (상단)
        draw_btn(screen, r_sp_toggle, f"SP: {player.star_power}", font, CYAN)
        
        # 4. 미러 스트레이핑 조작부 (중앙)
        if player.mirror_strafing:
            draw_btn(screen, r_in, "IN", big_font, ORANGE)
            draw_btn(screen, r_out, "OUT", big_font, ORANGE)
            draw_btn(screen, r_cancel, "CANCEL LoS", font, RED)
            screen.blit(font.render("MIRROR STRAFING ACTIVE", True, GREEN), (WIDTH//2 - 100, HEIGHT - 220))

        # 게이지 UI (좌측 상단)
        screen.blit(font.render(f"Super: {player.super_charge}/{player.super_charge_max}", True, YELLOW), (20, 20))
        screen.blit(font.render(f"Hyper: {player.hc_charge}/{player.hc_charge_max}", True, PURPLE), (20, 50))
        if player.hc_active:
            screen.blit(font.render(f"HYPERCHARGE ACTIVE! ({player.hc_timer//60}s)", True, CYAN), (20, 80))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
