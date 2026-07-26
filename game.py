import pygame
import math
import random

pygame.init()
WIDTH, HEIGHT = 1000, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Brawl Stars - Ultimate Colt (Pixel-Perfect Hitboxes & Buffies)")
clock = pygame.time.Clock()

# --- 색상 ---
WHITE, BLACK = (255, 255, 255), (20, 20, 20)
RED, BLUE, YELLOW = (255, 50, 50), (50, 150, 255), (255, 200, 0)
GREEN, GRAY, DARK_GRAY = (50, 255, 50), (100, 100, 100), (40, 40, 40)
PURPLE, CYAN, ORANGE, SILVER = (200, 0, 255), (0, 255, 255), (255, 165, 0), (192, 192, 192)

# --- 에임봇 수학 ---
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

# --- 스마트 훈련장 더미 ---
class SmartEnemy:
    def __init__(self):
        self.x, self.y = WIDTH // 2 + 100, HEIGHT // 2
        self.radius = 20
        self.speed = 3.5
        self.vx, self.vy = 0, 0
        self.target_x, self.target_y = self.x, self.y
        self.max_hp = 10000
        self.hp = self.max_hp
        
        # 픽셀 단위 히트박스 생성 (원형)
        self.image = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, RED, (self.radius, self.radius), self.radius)
        self.mask = pygame.mask.from_surface(self.image)

    def pick_new_waypoint(self):
        self.target_x = random.randint(WIDTH // 2, WIDTH - 50)
        self.target_y = random.randint(50, HEIGHT - 50)

    def update(self):
        # 목표 지점을 향해 부드럽게 무빙 (실제 유저의 회피 기동 시뮬레이션)
        dist = math.hypot(self.target_x - self.x, self.target_y - self.y)
        if dist < 10:
            self.pick_new_waypoint()
        else:
            self.vx = (self.target_x - self.x) / dist * self.speed
            self.vy = (self.target_y - self.y) / dist * self.speed
            self.x += self.vx
            self.y += self.vy
            
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        pygame.draw.rect(surface, DARK_GRAY, (self.x - 25, self.y - 35, 50, 6))
        pygame.draw.rect(surface, GREEN, (self.x - 25, self.y - 35, 50 * (self.hp / self.max_hp), 6))

# --- 정밀 회전 히트박스 총알 ---
class AdvancedBullet:
    def __init__(self, x, y, vx, vy, damage, width, height, pierce, color):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.damage = damage
        self.pierce = pierce
        self.hit_targets = set()
        
        # 유니티의 OBB처럼 각도에 따른 회전형 사각형(캡슐) 히트박스 생성
        self.angle = math.degrees(math.atan2(-vy, vx)) # Pygame 회전은 반시계방향
        
        base_image = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(base_image, color, (0, 0, width, height), border_radius=height//2)
        
        # 회전된 이미지 및 픽셀 마스크(히트박스) 추출
        self.image = pygame.transform.rotate(base_image, self.angle)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (self.x, self.y)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

# --- 완전체 콜트 ---
class UltimateColt:
    def __init__(self):
        self.x, self.y = 100, HEIGHT // 2
        self.radius = 18
        self.base_speed = 4.5
        self.base_damage = 720
        self.base_bullet_speed = 25
        
        self.ammo = 3.0 # 장전기 버피(소수점 장전)를 위해 float 사용
        self.reload_timer = 0
        self.reload_time_max = 78 
        
        self.super_charge, self.super_charge_max = 0, 12
        self.hc_charge, self.hc_charge_max = 0, 35
        self.hc_active, self.hc_timer = False, 0
        
        self.star_power = "Slick Boots" # or "Magnum Special"
        self.gadget = "Speedloader" # or "Silver Bullet"
        self.gadget_uses = 3
        self.silver_bullet_active = False
        
        # 버피 발동 상태
        self.sb_buffie_timer = 0 # 스피드 부츠 버피(적중 시 이속 증가) 타이머
        
        self.bullets = []
        self.is_bursting = False
        self.burst_type = "normal"
        self.burst_count, self.burst_timer = 0, 0
        
        self.mirror_strafing = False
        self.target_dist = 0
        self.los_nx, self.los_ny = 0, 0

    def get_current_stats(self):
        speed, b_speed, dmg_mult = self.base_speed, self.base_bullet_speed, 1.0
        
        if self.hc_active:
            speed *= 1.20; dmg_mult *= 1.05
            
        if self.star_power == "Slick Boots":
            speed *= 1.13
            # [버피] 적중 시 추가 이동 속도 버프
            if self.sb_buffie_timer > 0: speed *= 1.15
        elif self.star_power == "Magnum Special":
            b_speed *= 1.11
            
        return speed, b_speed, dmg_mult

    def update(self, joy_vec, btn_in, btn_out, enemy):
        cur_speed, cur_b_speed, cur_dmg_mult = self.get_current_stats()
        if self.sb_buffie_timer > 0: self.sb_buffie_timer -= 1
        
        # 1. 이동 (미러 스트레이핑 포함)
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

        # 2. 재장전
        if self.ammo < 3 and not self.is_bursting:
            self.reload_timer -= 1
            if self.reload_timer <= 0:
                self.ammo = min(3.0, self.ammo + 1)
                self.reload_timer = int(self.reload_time_max * (1.1 if self.hc_active else 1.0))

        if self.hc_active:
            self.hc_timer -= 1
            if self.hc_timer <= 0: self.hc_active = False

        # 3. 사격
        if self.is_bursting:
            self.burst_timer -= 1
            if self.burst_timer <= 0:
                b_vx, b_vy = get_predictive_aim_velocity(self.x, self.y, enemy.x, enemy.y, enemy.vx, enemy.vy, cur_b_speed)

                if self.burst_type == "silver":
                    # [버피] 실버 불렛: 훨씬 크고 강력함 (1440 -> 2100)
                    dmg = 2100 * cur_dmg_mult
                    b = AdvancedBullet(self.x, self.y, b_vx, b_vy, dmg, 40, 16, True, SILVER)
                    self.bullets.append(b)
                    self.is_bursting = False
                    self.silver_bullet_active = False
                    
                elif self.burst_type == "super":
                    size_w, size_h = (28, 12) if self.hc_active else (20, 8)
                    b = AdvancedBullet(self.x, self.y, b_vx, b_vy, 640 * cur_dmg_mult, size_w, size_h, True, YELLOW)
                    self.bullets.append(b)
                    self.burst_count += 1
                    self.burst_timer = 2
                    if self.burst_count >= 12: self.is_bursting = False
                        
                else: 
                    b = AdvancedBullet(self.x, self.y, b_vx, b_vy, self.base_damage * cur_dmg_mult, 16, 6, False, WHITE)
                    self.bullets.append(b)
                    self.burst_count += 1
                    self.burst_timer = 2 if self.hc_active else 4
                    if self.burst_count >= 6: self.is_bursting = False

        # 4. 픽셀-퍼펙트 충돌 처리
        for b in self.bullets[:]:
            b.update()
            if not screen.get_rect().collidepoint(b.x, b.y):
                if b in self.bullets: self.bullets.remove(b)
                continue
                
            # 마스크 기반 정밀 충돌 검사 (히트박스 각도 반영)
            offset_x, offset_y = enemy.rect.left - b.rect.left, enemy.rect.top - b.rect.top
            if b.mask.overlap(enemy.mask, (int(offset_x), int(offset_y))):
                if id(enemy) not in b.hit_targets:
                    b.hit_targets.add(id(enemy))
                    
                    final_damage = b.damage
                    
                    # [버피] 매그넘 스페셜: 먼 거리 적중 시 데미지 증가
                    dist_to_enemy = math.hypot(b.x - self.x, b.y - self.y)
                    if self.star_power == "Magnum Special" and dist_to_enemy > 300:
                        final_damage *= 1.2
                        
                    enemy.hp -= final_damage
                    
                    # [버피] 스피드 부츠: 적중 시 이속 증가 타이머 갱신
                    if self.star_power == "Slick Boots": self.sb_buffie_timer = 60
                        
                    # [버피] 장전기: 적중 시 탄창 0.5스톡 회복
                    if self.gadget == "Speedloader":
                        self.ammo = min(3.0, self.ammo + 0.5)

                    self.super_charge = min(self.super_charge_max, self.super_charge + 1)
                    if not self.hc_active: self.hc_charge = min(self.hc_charge_max, self.hc_charge + 1)
                    
                    # 미러 스트레이핑 트리거
                    if not self.mirror_strafing:
                        self.mirror_strafing = True
                        self.los_nx, self.los_ny = (self.x - enemy.x)/dist_to_enemy, (self.y - enemy.y)/dist_to_enemy
                        self.target_dist = dist_to_enemy
                        
                    if not b.pierce:
                        if b in self.bullets: self.bullets.remove(b)

    def draw(self, surface):
        color = PURPLE if self.hc_active else BLUE
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.radius)
        if self.hc_active: pygame.draw.circle(surface, CYAN, (int(self.x), int(self.y)), self.radius + 5, 2)
        if self.sb_buffie_timer > 0: pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), self.radius + 8, 1)
            
        for b in self.bullets: b.draw(surface)
            
        for i in range(3):
            c = YELLOW if i < int(self.ammo) else GRAY
            pygame.draw.rect(surface, c, (self.x - 15 + (i * 12), self.y - 30, 8, 5))
            if i == int(self.ammo) and self.ammo % 1 != 0: # 버피로 인한 소수점 탄창 표시
                pygame.draw.rect(surface, ORANGE, (self.x - 15 + (i * 12), self.y - 30, 8 * (self.ammo % 1), 5))

# --- UI 그리기 헬퍼 ---
def draw_btn(surface, rect, text, font, color, active=True):
    c = color if active else DARK_GRAY
    pygame.draw.rect(surface, c, rect, border_radius=10)
    pygame.draw.rect(surface, WHITE, rect, 2, border_radius=10)
    txt = font.render(text, True, WHITE if active else GRAY)
    tr = txt.get_rect(center=rect.center)
    surface.blit(txt, tr)

def main():
    player = UltimateColt()
    enemy = SmartEnemy()
    
    font = pygame.font.SysFont(None, 24)
    big_font = pygame.font.SysFont(None, 36)

    joy_base, joy_stick = (120, HEIGHT - 120), [120, HEIGHT - 120]
    joy_touch_id = None
    touches = {}

    r_fire = pygame.Rect(WIDTH - 130, HEIGHT - 130, 100, 100)
    r_super = pygame.Rect(WIDTH - 240, HEIGHT - 110, 80, 80)
    r_hyper = pygame.Rect(WIDTH - 220, HEIGHT - 220, 80, 80)
    r_gadget = pygame.Rect(WIDTH - 110, HEIGHT - 240, 70, 70)
    
    r_sp_toggle = pygame.Rect(WIDTH//2 - 200, 10, 190, 40)
    r_gd_toggle = pygame.Rect(WIDTH//2 + 10, 10, 190, 40)
    
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
                
            elif event.type in [pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP]:
                tx, ty = event.x * WIDTH, event.y * HEIGHT
                tid = event.finger_id
                
                if event.type == pygame.FINGERDOWN:
                    touches[tid] = (tx, ty)
                    if tx < WIDTH // 3 and joy_touch_id is None:
                        joy_touch_id = tid
                        joy_base, joy_stick = (tx, ty), [tx, ty]
                    else:
                        if r_sp_toggle.collidepoint(tx, ty):
                            player.star_power = "Magnum Special" if player.star_power == "Slick Boots" else "Slick Boots"
                        elif r_gd_toggle.collidepoint(tx, ty):
                            player.gadget = "Speedloader" if player.gadget == "Silver Bullet" else "Silver Bullet"
                            
                        if player.mirror_strafing and r_cancel.collidepoint(tx, ty):
                            player.mirror_strafing = False
                            
                        if not player.is_bursting:
                            if r_fire.collidepoint(tx, ty) and player.ammo >= 1:
                                player.is_bursting = True
                                player.burst_type = "silver" if player.silver_bullet_active else "normal"
                                player.ammo -= 1
                                player.burst_count, player.burst_timer = 0, 0
                            elif r_super.collidepoint(tx, ty) and player.super_charge >= player.super_charge_max:
                                player.is_bursting = True
                                player.burst_type = "super"
                                player.super_charge, player.burst_count, player.burst_timer = 0, 0, 0
                            elif r_hyper.collidepoint(tx, ty) and player.hc_charge >= player.hc_charge_max:
                                player.hc_active, player.hc_charge, player.hc_timer = True, 0, 60*7
                            elif r_gadget.collidepoint(tx, ty) and player.gadget_uses > 0:
                                player.gadget_uses -= 1
                                if player.gadget == "Speedloader":
                                    player.ammo = min(3.0, player.ammo + 2) # 장전기: 탄창 2개 즉시 회복
                                elif player.gadget == "Silver Bullet" and not player.silver_bullet_active:
                                    player.silver_bullet_active = True

                elif event.type == pygame.FINGERMOTION:
                    touches[tid] = (tx, ty)
                    if tid == joy_touch_id:
                        dist = math.hypot(tx - joy_base[0], ty - joy_base[1])
                        if dist > 50:
                            joy_stick[0] = joy_base[0] + (tx - joy_base[0]) / dist * 50
                            joy_stick[1] = joy_base[1] + (ty - joy_base[1]) / dist * 50
                        else: joy_stick[0], joy_stick[1] = tx, ty
                elif event.type == pygame.FINGERUP:
                    if tid in touches: del touches[tid]
                    if tid == joy_touch_id:
                        joy_touch_id = None
                        joy_base, joy_stick = (120, HEIGHT - 120), [120, HEIGHT - 120]

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if r_sp_toggle.collidepoint(mx, my): player.star_power = "Magnum Special" if player.star_power == "Slick Boots" else "Slick Boots"
                if r_gd_toggle.collidepoint(mx, my): player.gadget = "Speedloader" if player.gadget == "Silver Bullet" else "Silver Bullet"
                if player.mirror_strafing and r_cancel.collidepoint(mx, my): player.mirror_strafing = False
                
                if not player.is_bursting:
                    if r_fire.collidepoint(mx, my) and player.ammo >= 1:
                        player.is_bursting = True
                        player.burst_type = "silver" if player.silver_bullet_active else "normal"
                        player.ammo -= 1
                        player.burst_count, player.burst_timer = 0, 0
                    elif r_super.collidepoint(mx, my) and player.super_charge >= player.super_charge_max:
                        player.is_bursting, player.burst_type, player.super_charge = True, "super", 0
                        player.burst_count, player.burst_timer = 0, 0
                    elif r_hyper.collidepoint(mx, my) and player.hc_charge >= player.hc_charge_max:
                        player.hc_active, player.hc_charge, player.hc_timer = True, 0, 60*7
                    elif r_gadget.collidepoint(mx, my) and player.gadget_uses > 0:
                        player.gadget_uses -= 1
                        if player.gadget == "Speedloader": player.ammo = min(3.0, player.ammo + 2)
                        elif player.gadget == "Silver Bullet" and not player.silver_bullet_active: player.silver_bullet_active = True
                elif mx < WIDTH // 3:
                    joy_touch_id = "mouse"
                    joy_base, joy_stick = (mx, my), [mx, my]
            elif event.type == pygame.MOUSEMOTION and joy_touch_id == "mouse":
                mx, my = event.pos
                dist = math.hypot(mx - joy_base[0], my - joy_base[1])
                if dist > 50:
                    joy_stick[0] = joy_base[0] + (mx - joy_base[0]) / dist * 50
                    joy_stick[1] = joy_base[1] + (my - joy_base[1]) / dist * 50
                else: joy_stick[0], joy_stick[1] = mx, my
            elif event.type == pygame.MOUSEBUTTONUP:
                if joy_touch_id == "mouse":
                    joy_touch_id = None
                    joy_base, joy_stick = (120, HEIGHT - 120), [120, HEIGHT - 120]

        joy_vec = (0, 0)
        if joy_touch_id is not None:
            dx, dy = joy_stick[0] - joy_base[0], joy_stick[1] - joy_base[1]
            dist = math.hypot(dx, dy)
            if dist > 0: joy_vec = (dx/dist, dy/dist)

        if player.mirror_strafing:
            for tid, (tx, ty) in touches.items():
                if r_in.collidepoint(tx, ty): btn_in_pressed = True
                if r_out.collidepoint(tx, ty): btn_out_pressed = True
            if pygame.mouse.get_pressed()[0]:
                mx, my = pygame.mouse.get_pos()
                if r_in.collidepoint(mx, my): btn_in_pressed = True
                if r_out.collidepoint(mx, my): btn_out_pressed = True

        enemy.update()
        player.update(joy_vec, btn_in_pressed, btn_out_pressed, enemy)
        if enemy.hp <= 0: enemy.hp, enemy.x, enemy.y = enemy.max_hp, random.randint(WIDTH//2, WIDTH-50), random.randint(50, HEIGHT-50)

        # --- 그리기 ---
        screen.fill(BLACK)
        if player.mirror_strafing:
            pygame.draw.line(screen, GRAY, (enemy.x, enemy.y), (enemy.x + player.los_nx * 2000, enemy.y + player.los_ny * 2000), 2)
            pygame.draw.line(screen, GREEN, (enemy.x, enemy.y), (player.x, player.y), 4)

        enemy.draw(screen)
        player.draw(screen)

        pygame.draw.circle(screen, DARK_GRAY, (int(joy_base[0]), int(joy_base[1])), 50, 2)
        pygame.draw.circle(screen, GRAY, (int(joy_stick[0]), int(joy_stick[1])), 25)

        draw_btn(screen, r_fire, "FIRE" if not player.silver_bullet_active else "SILVER", font, SILVER if player.silver_bullet_active else RED, player.ammo >= 1)
        draw_btn(screen, r_super, "SUPER", font, YELLOW, player.super_charge >= player.super_charge_max)
        draw_btn(screen, r_hyper, "HYPER", font, PURPLE, player.hc_charge >= player.hc_charge_max)
        draw_btn(screen, r_gadget, f"GADGET({player.gadget_uses})", font, GREEN, player.gadget_uses > 0)
        
        draw_btn(screen, r_sp_toggle, f"SP: {player.star_power}", font, CYAN)
        draw_btn(screen, r_gd_toggle, f"GD: {player.gadget}", font, CYAN)
        
        if player.mirror_strafing:
            draw_btn(screen, r_in, "IN", big_font, ORANGE)
            draw_btn(screen, r_out, "OUT", big_font, ORANGE)
            draw_btn(screen, r_cancel, "CANCEL LoS", font, RED)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
