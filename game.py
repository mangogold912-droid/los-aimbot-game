import pygame
import math
import random

# --- 초기화 및 설정 ---
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("LoS Aimbot & Mirror Strafing Game")
clock = pygame.time.Clock()

# 색상 정의
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
RED = (255, 50, 50)
BLUE = (50, 150, 255)
YELLOW = (255, 200, 0)
GRAY = (100, 100, 100)
GREEN = (50, 255, 50)

# --- 수학적 예측 계산 (에임봇) ---
def get_predictive_aim_velocity(px, py, ex, ey, evx, evy, bullet_speed):
    """
    적의 현재 위치, 속도와 총알의 속도를 기반으로 
    총알이 적과 정확히 교차할 미래의 지점을 예측하여 발사 속도 벡터를 반환합니다. (2차 방정식 활용)
    """
    dx = ex - px
    dy = ey - py
    
    # 2차 방정식 계수: a*t^2 + b*t + c = 0
    a = evx**2 + evy**2 - bullet_speed**2
    b = 2 * (dx * evx + dy * evy)
    c = dx**2 + dy**2
    
    t = -1 # 충돌까지 걸리는 시간
    
    if a == 0:
        if b != 0:
            t = -c / b
    else:
        discriminant = b**2 - 4 * a * c # 판별식
        if discriminant >= 0:
            t1 = (-b - math.sqrt(discriminant)) / (2 * a)
            t2 = (-b + math.sqrt(discriminant)) / (2 * a)
            # 가장 빨리 맞는 양수 시간(t)을 선택
            if t1 > 0 and t2 > 0:
                t = min(t1, t2)
            elif t1 > 0:
                t = t1
            elif t2 > 0:
                t = t2

    # 예측 가능한 시간이 없다면 현재 위치를 향해 발사
    if t <= 0:
        dist = math.hypot(dx, dy)
        if dist == 0: dist = 1
        return (dx/dist)*bullet_speed, (dy/dist)*bullet_speed
        
    # 예측된 미래 타겟 위치
    target_x = ex + evx * t
    target_y = ey + evy * t
    
    # 타겟을 향한 총알의 속도 벡터 계산
    tx = target_x - px
    ty = target_y - py
    dist = math.hypot(tx, ty)
    if dist == 0: dist = 1
    
    return (tx/dist)*bullet_speed, (ty/dist)*bullet_speed


# --- 게임 클래스 구현 ---
class Enemy:
    def __init__(self):
        self.x = WIDTH // 2 + 200
        self.y = HEIGHT // 2
        self.radius = 15
        self.vx = random.choice([-3, 3])
        self.vy = random.choice([-2, 2])
        self.speed = 3

    def update(self):
        # 적의 지속적인 이동 (벽에 부딪히면 튕김)
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
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = 5
        self.speed = 12

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def draw(self, surface):
        pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), self.radius)

class Player:
    def __init__(self):
        self.x = 100
        self.y = HEIGHT // 2
        self.radius = 15
        self.speed = 5
        
        # 사격(에임봇) 상태 변수
        self.bullets = []
        self.is_bursting = False
        self.burst_count = 0
        self.burst_timer = 0
        self.bullet_speed = 12
        
        # 미러 스트레이핑 (LOS) 상태 변수
        self.mirror_strafing_active = False
        self.target_distance = 0
        self.los_nx = 0
        self.los_ny = 0

    def update(self, keys, enemy):
        # 1. 미러 스트레이핑 상태 로직
        if self.mirror_strafing_active:
            # W, S 키로 적과의 거리만 조절 (축 위에서만 이동)
            if keys[pygame.K_w]:
                self.target_distance = max(50, self.target_distance - self.speed) # 가까워짐
            if keys[pygame.K_s]:
                self.target_distance = min(600, self.target_distance + self.speed) # 멀어짐
                
            # 스페이스바를 누르면 보조모드 해제
            if keys[pygame.K_SPACE]:
                self.mirror_strafing_active = False
                
            # 플레이어의 위치를 적의 위치를 기준으로 LOS 축과 설정된 거리에 강제 고정
            # -> 적이 움직여도 거리를 유지하며 똑같이 따라 움직임 (미러 스트레이핑)
            self.x = enemy.x + self.los_nx * self.target_distance
            self.y = enemy.y + self.los_ny * self.target_distance
            
        # 2. 일반 이동 로직
        else:
            if keys[pygame.K_w]: self.y -= self.speed
            if keys[pygame.K_s]: self.y += self.speed
            if keys[pygame.K_a]: self.x -= self.speed
            if keys[pygame.K_d]: self.x += self.speed

        # 화면 밖으로 나가지 않게 고정
        self.x = max(self.radius, min(self.x, WIDTH - self.radius))
        self.y = max(self.radius, min(self.y, HEIGHT - self.radius))

        # 3. 6연사 사격 처리 로직
        if self.is_bursting:
            self.burst_timer -= 1
            if self.burst_timer <= 0:
                # 에임봇 예측 알고리즘으로 탄환 발사 속도 계산
                b_vx, b_vy = get_predictive_aim_velocity(
                    self.x, self.y, 
                    enemy.x, enemy.y, 
                    enemy.vx, enemy.vy, 
                    self.bullet_speed
                )
                self.bullets.append(Bullet(self.x, self.y, b_vx, b_vy))
                self.burst_count += 1
                self.burst_timer = 5 # 다음 탄환까지의 프레임 대기 (연사 속도)
                
                if self.burst_count >= 6: # 6발을 다 쏘면 연사 종료
                    self.is_bursting = False

        # 총알 업데이트
        for b in self.bullets[:]:
            b.update()
            # 총알이 화면 밖을 나가면 삭제
            if b.x < 0 or b.x > WIDTH or b.y < 0 or b.y > HEIGHT:
                self.bullets.remove(b)

    def draw(self, surface):
        pygame.draw.circle(surface, BLUE, (int(self.x), int(self.y)), self.radius)
        for b in self.bullets:
            b.draw(surface)

# --- 메인 게임 루프 ---
def main():
    player = Player()
    enemy = Enemy()
    font = pygame.font.SysFont(None, 24)

    running = True
    while running:
        clock.tick(60) # 60 FPS
        
        # 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not player.is_bursting:
                    # 마우스 좌클릭 시 6연사 시작
                    player.is_bursting = True
                    player.burst_count = 0
                    player.burst_timer = 0

        keys = pygame.key.get_pressed()

        # 업데이트 로직
        enemy.update()
        player.update(keys, enemy)

        # 충돌 검사 (총알이 적을 맞췄을 때)
        for b in player.bullets[:]:
            dist = math.hypot(b.x - enemy.x, b.y - enemy.y)
            if dist < enemy.radius + b.radius:
                player.bullets.remove(b)
                # 맞추는 순간 LOS축을 계산하고 미러 스트레이핑 모드 진입
                if not player.mirror_strafing_active:
                    player.mirror_strafing_active = True
                    
                    # 적에서 플레이어를 향하는 LOS(시야선) 벡터 추출 및 정규화
                    dx = player.x - enemy.x
                    dy = player.y - enemy.y
                    cur_dist = math.hypot(dx, dy)
                    if cur_dist == 0: cur_dist = 1
                    
                    player.los_nx = dx / cur_dist
                    player.los_ny = dy / cur_dist
                    player.target_distance = cur_dist

        # 화면 그리기
        screen.fill(BLACK)
        
        # LOS 축 그리기 (미러 스트레이핑 모드일 때 선 표시)
        if player.mirror_strafing_active:
            # 적의 위치를 기준으로 무한한 축을 그리기 위해 계산
            end_x = enemy.x + player.los_nx * 2000
            end_y = enemy.y + player.los_ny * 2000
            pygame.draw.line(screen, GRAY, (enemy.x, enemy.y), (end_x, end_y), 2)
            pygame.draw.line(screen, GREEN, (enemy.x, enemy.y), (player.x, player.y), 4)

        enemy.draw(screen)
        player.draw(screen)

        # UI 텍스트 출력
        instructions = [
            "Mouse Left Click: Fire 6-round Burst (Predictive Aimbot)",
            "WASD: Normal Movement",
        ]
        
        if player.mirror_strafing_active:
            instructions.append("STATUS: Mirror Strafing ACTIVE!")
            instructions.append("W/S: Move along the LOS axis (Adjust Distance)")
            instructions.append("SPACE: Cancel Mirror Strafing")
            
        for i, text in enumerate(instructions):
            color = GREEN if "ACTIVE" in text else WHITE
            img = font.render(text, True, color)
            screen.blit(img, (10, 10 + i * 25))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
