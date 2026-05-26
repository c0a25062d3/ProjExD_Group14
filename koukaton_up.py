import pygame
import sys
import os
import random

# カレントディレクトリの固定
os.chdir(os.path.dirname(os.path.abspath(__file__)))

WIDTH, HEIGHT = 600, 800
FPS = 60
GRAVITY = 0.6

BLACK = (20, 20, 25)
BLUE = (100, 150, 255)
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)

DARK_PANEL = (35, 35, 45)
PANEL_BORDER = (90, 90, 110)
LIGHT_BLUE = (120, 200, 255)                #左上UI
ORANGE = (255, 170, 80)

# ギミック床の色定義を復活
COLOR_NORMAL = (120, 120, 120)       # 緑（通常）
COLOR_FAKE = (180, 0, 180)           # 紫（すり抜ける）
COLOR_ICE = (100, 200, 255)          # 水色（滑る）
COLOR_TRAMPOLINE = (255, 140, 0)     # オレンジ（大ジャンプ）
COLOR_TRAP = (255, 50, 50)           # 赤（最初に戻る）
COLOR_RED_UI = (255, 100, 100)       # UI用赤

# 種類から色を取得する辞書
COLOR_MAP = {
    "normal": COLOR_NORMAL,
    "fake": COLOR_FAKE,
    "ice": COLOR_ICE,
    "trampoline": COLOR_TRAMPOLINE,
    "trap": COLOR_TRAP
}

# ==========================================
# 1. データ構造（クラス）の定義
# ==========================================

class Player:
    def __init__(self):

        self.image_original = pygame.image.load("9.png")#背景読み込み
        self.image_original = pygame.transform.scale(self.image_original, (30, 40))
        self._image = self.image_original
        self._rect = self._image.get_rect(center=(WIDTH // 2, HEIGHT - 100))
        
        self._vel_x = 0
        self._vel_y = 0
        self._on_ground = False
        
        self._is_charging = False
        self._charge_power = 0
        self._max_charge = 20.0
        self._direction = 1
        
        self._is_clear = False
        self._on_ice = False      
        self._is_reset = False    

    # --- ゲッター ---
    def get_image(self): return self._image
    def get_rect(self): return self._rect
    def get_vel_x(self): return self._vel_x
    def get_vel_y(self): return self._vel_y
    def get_on_ground(self): return self._on_ground
    def get_is_charging(self): return self._is_charging
    def get_charge_power(self): return self._charge_power
    def get_max_charge(self): return self._max_charge
    def get_direction(self): return self._direction
    def get_is_clear(self): return self._is_clear
    def get_on_ice(self): return self._on_ice
    def get_is_reset(self): return self._is_reset

    # --- セッター ---
    def set_vel_x(self, value): self._vel_x = value
    def set_vel_y(self, value): self._vel_y = value
    def set_on_ground(self, value): self._on_ground = value
    def set_is_charging(self, value): self._is_charging = value
    def set_charge_power(self, value): self._charge_power = value
    def set_direction(self, value): self._direction = value
    def set_is_clear(self, value): self._is_clear = value
    def set_on_ice(self, value): self._on_ice = value
    def set_is_reset(self, value): self._is_reset = value


class Platform:
    def __init__(self, x, y, w, h, color, plat_type="normal"):
        self._image = pygame.Surface((w, h))
        self._image.fill(color)
        self._rect = self._image.get_rect(topleft=(x, y))
        self._type = plat_type

    def get_image(self): return self._image
    def get_rect(self): return self._rect
    def get_type(self): return self._type


# ==========================================
# 2. クラスを操作する関数
# ==========================================

def update_player(player, keys, platforms, goal_block):
    if not player.get_is_clear():
        if player.get_on_ground():
            
            if player.get_on_ice():
                player.set_vel_x(player.get_vel_x() * 0.96) 
            else:
                player.set_vel_x(0)
            
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player.set_direction(-1)
                player._image = pygame.transform.flip(player.image_original, True, False)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player.set_direction(1)
                player._image = player.image_original

            if keys[pygame.K_SPACE]:
                player.set_is_charging(True)
                current_power = player.get_charge_power()
                if current_power < player.get_max_charge():
                    player.set_charge_power(current_power + 0.4)
            else:
                if player.get_is_charging():
                    power = player.get_charge_power()
                    direction = player.get_direction()
                    
                    player.set_vel_y(-power * 0.9 - 5)
                    player.set_vel_x(direction * (power * 0.4 + 2))
                    
                    player.set_is_charging(False)
                    player.set_charge_power(0)
                    player.set_on_ground(False)
                    player.set_on_ice(False)
    
    if not player.get_on_ground():
        player.set_vel_y(player.get_vel_y() + GRAVITY)

    rect = player.get_rect()

    # X軸方向の移動と、足場の【左右】の当たり判定
    rect.x += player.get_vel_x()
    if rect.left < 0:
        rect.left = 0
        player.set_vel_x(player.get_vel_x() * -0.5)
        player.set_direction(1)
    if rect.right > WIDTH:
        rect.right = WIDTH
        player.set_vel_x(player.get_vel_x() * -0.5)
        player.set_direction(-1)

    # 追加：足場の左右側面との衝突をチェック
    for plat in platforms:
        plat_rect = plat.get_rect()
        if rect.colliderect(plat_rect):
            if player.get_vel_x() > 0:  # 右移動中に衝突
                rect.right = plat_rect.left
                player.set_vel_x(player.get_vel_x() * -0.5)
                player.set_direction(-1)
            elif player.get_vel_x() < 0:  # 左移動中に衝突
                rect.left = plat_rect.right
                player.set_vel_x(player.get_vel_x() * -0.5)
                player.set_direction(1)

    # Y軸方向の移動
    rect.y += int(player.get_vel_y())

    goal_rect = goal_block.get_rect()
    if rect.colliderect(goal_rect):
        if player.get_vel_y() < 0:
            rect.top = goal_rect.bottom
            player.set_vel_y(0)
            player.set_is_clear(True)

    player.set_on_ground(False)
    player.set_on_ice(False)

    # 足場の判定ループ（インデントを修正して中に一括で格納）
    for plat in platforms:
        if plat.get_type() == "fake":
            continue
                
        plat_rect = plat.get_rect()
        if rect.colliderect(plat_rect):
            # もともとの上面判定（落下中の着地判定）
            if player.get_vel_y() > 0:
                if rect.bottom <= plat_rect.top + player.get_vel_y() + 1:
                    
                    # トランポリン床
                    if plat.get_type() == "trampoline":
                        rect.bottom = plat_rect.top
                        player.set_vel_y(-25) 
                        player.set_on_ground(False)
                        break
                    
                    # トラップ床
                    if plat.get_type() == "trap":
                        rect.center = (WIDTH // 2, HEIGHT - 100) 
                        player.set_vel_y(0)
                        player.set_vel_x(0)
                        player.set_is_reset(True) 
                        break

                    # 通常の足場の着地処理
                    rect.bottom = plat_rect.top
                    player.set_vel_y(0)
                    
                    if plat.get_type() == "ice":
                        player.set_on_ice(True)
                    else:
                        player.set_on_ice(False)

                    player.set_on_ground(True)
                    break

            # 追加：上昇中に足場の【下側（天井部分）】に頭をぶつけた判定
            elif player.get_vel_y() < 0:
                rect.top = plat_rect.bottom
                player.set_vel_y(0)  # 上昇を止める
                break

def draw_ui(screen, font, player, current_floor, total_floors, current_height, max_height):

    # UIのサイズ
    panel_x = 10
    panel_y = 10
    panel_w = 300
    panel_h = 120

    # 背景のパネル
    panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
    pygame.draw.rect(screen, DARK_PANEL, panel_rect, border_radius=12)
    pygame.draw.rect(screen, PANEL_BORDER, panel_rect, 2, border_radius=12)
    # タイトル
    title_text = font.render("STATUS", True, GOLD)
    screen.blit(title_text, (panel_x + 15, panel_y + 10))

    # 階層
    floor_text = font.render(f"Floor {current_floor} / {total_floors}", True, WHITE)
    screen.blit(floor_text, (panel_x + 15, panel_y + 42))

    # 高さ
    height_text = font.render(f"Height: {current_height // 10} m", True, LIGHT_BLUE)
    screen.blit(height_text, (panel_x + 15, panel_y + 70))

    # 最高到達点
    max_text = font.render(f"Best: {max_height // 10} m", True, ORANGE)
    screen.blit(max_text, (panel_x + 180, panel_y + 70))


# ==========================================
# 3. メインループ
# ==========================================

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Jump King - Colored Gimmicks")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)
    large_font = pygame.font.SysFont(None, 72)

    player = Player()
    
    bg_large = pygame.image.load("background_all.png")
    bg_large = pygame.transform.scale(bg_large, (600, 2400))
    platforms = []
    
    platforms.append(Platform(0, HEIGHT - 40, WIDTH, 40, COLOR_NORMAL, "normal")) 

    TOTAL_FLOORS = 10
    goal_y = (HEIGHT - 40) - (HEIGHT * TOTAL_FLOORS)
    goal_block = Platform(0, goal_y, WIDTH, 40, GOLD, "goal")

    for f in range(TOTAL_FLOORS):
        floor_bottom = HEIGHT - (f * HEIGHT)
        floor_top = HEIGHT - ((f + 1) * HEIGHT)
        
        floor_plats = []
        plat_y = floor_bottom - 150
        
        while plat_y > floor_top + 50:
            w = random.randint(60, 130)
            x = random.randint(0, WIDTH - w)
            floor_plats.append(Platform(x, plat_y, w, 20, COLOR_NORMAL, "normal"))
            gap_y = random.randint(80, 130)
            plat_y -= gap_y
            
        if len(floor_plats) >= 2:
            special_type = random.choice(["fake", "ice", "trampoline"])
            
            # 10階の場合：ランダム特殊床1つ ＋ トラップ床1つ
            if f == TOTAL_FLOORS - 1:
                specials = random.sample(range(len(floor_plats)), 2)
                
                p_spec = floor_plats[specials[0]]
                # 種類に応じた色（COLOR_MAP[special_type]）を適用
                floor_plats[specials[0]] = Platform(p_spec.get_rect().x, p_spec.get_rect().y, p_spec.get_rect().width, 20, COLOR_MAP[special_type], special_type)
                
                p_trap = floor_plats[specials[1]]
                # 赤色を適用
                floor_plats[specials[1]] = Platform(p_trap.get_rect().x, p_trap.get_rect().y, p_trap.get_rect().width, 20, COLOR_TRAP, "trap")
            
            # 1〜9階の場合：ランダム特殊床1つ
            else:
                special_idx = random.choice(range(len(floor_plats)))
                p_spec = floor_plats[special_idx]
                floor_plats[special_idx] = Platform(p_spec.get_rect().x, p_spec.get_rect().y, p_spec.get_rect().width, 20, COLOR_MAP[special_type], special_type)
                
        platforms.extend(floor_plats)

    camera_y = 0
    max_height = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        
        update_player(player, keys, platforms, goal_block)

        p_rect = player.get_rect()

        if player.get_is_reset():
            camera_y = 0
            player.set_is_reset(False) 

        SCROLL_TOP_MARGIN = 200
        if p_rect.y - camera_y < SCROLL_TOP_MARGIN:
            camera_y = p_rect.y - SCROLL_TOP_MARGIN

        SCROLL_BOTTOM_MARGIN = 150
        camera_easing_down = 0.08
        if p_rect.bottom - camera_y > HEIGHT - SCROLL_BOTTOM_MARGIN:
            target_camera_y = p_rect.bottom - (HEIGHT - SCROLL_BOTTOM_MARGIN)
            camera_y += (target_camera_y - camera_y) * camera_easing_down

        if camera_y > 0:
            camera_y = 0

        current_height = (HEIGHT - 40) - p_rect.bottom
        if current_height > max_height:
            max_height = current_height
            
        current_floor = min((current_height // HEIGHT) + 1, TOTAL_FLOORS)
        display_floor = max(1, current_floor)

        bg_y = (1600 + camera_y) % 2400
        src_rect = pygame.Rect(0, bg_y, 600, 800)
        screen.blit(bg_large, (0, 0), src_rect)

        goal_rect = goal_block.get_rect()
        goal_draw_y = goal_rect.y - camera_y
        if -100 < goal_draw_y < HEIGHT + 100:
            screen.blit(goal_block.get_image(), (goal_rect.x, goal_draw_y))

        for plat in platforms:
            plat_rect = plat.get_rect()
            draw_y = plat_rect.y - camera_y
            if -50 < draw_y < HEIGHT + 50:
                screen.blit(plat.get_image(), (plat_rect.x, draw_y))

        player_draw_y = p_rect.y - camera_y
        screen.blit(player.get_image(), (p_rect.x, player_draw_y))

        if player.get_is_charging() and not player.get_is_clear():
            gauge_width = (player.get_charge_power() / player.get_max_charge()) * 40
            pygame.draw.rect(screen, COLOR_RED_UI, (p_rect.centerx - 20, player_draw_y - 15, gauge_width, 8))
        
        arrow_x = p_rect.right + 5 if player.get_direction() == 1 else p_rect.left - 10
        pygame.draw.rect(screen, WHITE, (arrow_x, player_draw_y + 15, 5, 5))

        ui_text = font.render(f"Floor: {display_floor} / {TOTAL_FLOORS}   Max: {max_height // 10}m", True, WHITE)
        screen.blit(ui_text, (10, 10))

        # 情報表示 (UI)
        draw_ui(screen, font, player, current_floor, TOTAL_FLOORS, current_height, max_height)
        if player.get_is_clear():
            clear_text = large_font.render("CLEAR!!", True, GOLD)
            text_rect = clear_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
            screen.blit(clear_text, text_rect)
            
            sub_text = font.render("CONGRATULATIONS!", True, WHITE)
            sub_rect = sub_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10))
            screen.blit(sub_text, sub_rect)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()