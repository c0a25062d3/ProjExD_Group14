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
GREEN = (120, 120, 120)
RED = (255, 100, 100)
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)  # ゴールブロック用の金色

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
        
        self._is_clear = False  # ゴールしたかどうかのフラグ

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

    # --- セッター ---
    def set_vel_x(self, value): self._vel_x = value
    def set_vel_y(self, value): self._vel_y = value
    def set_on_ground(self, value): self._on_ground = value
    def set_is_charging(self, value): self._is_charging = value
    def set_charge_power(self, value): self._charge_power = value
    def set_direction(self, value): self._direction = value
    def set_is_clear(self, value): self._is_clear = value


class Platform:
    # 足場ごとに色を変えられるように引数追加
    def __init__(self, x, y, w, h, color):
        self._image = pygame.Surface((w, h))
        self._image.fill(color)
        self._rect = self._image.get_rect(topleft=(x, y))

    def get_image(self): return self._image
    def get_rect(self): return self._rect


# ==========================================
# 2. クラスを操作する関数
# ==========================================

def update_player(player, keys, platforms, goal_block):
    """プレイヤーの物理挙動と状態を更新する関数"""
    
    # ゴール済みの場合は入力を受け付けない（重力で落ちるだけ）
    if not player.get_is_clear():
        # 1. 地面にいる時の処理
        if player.get_on_ground():
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
    
    # 2. 重力の適用
    if not player.get_on_ground():
        player.set_vel_y(player.get_vel_y() + GRAVITY)

    rect = player.get_rect()

    # 座標の更新 (X軸) と壁の跳ね返り
    rect.x += player.get_vel_x()
    if rect.left < 0:
        rect.left = 0
        player.set_vel_x(player.get_vel_x() * -0.5)
        player.set_direction(1)
    if rect.right > WIDTH:
        rect.right = WIDTH
        player.set_vel_x(player.get_vel_x() * -0.5)
        player.set_direction(-1)

    # 座標の更新 (Y軸)
    rect.y += int(player.get_vel_y())

    # --- 3. ゴール（天井）との当たり判定 ---
    goal_rect = goal_block.get_rect()
    if rect.colliderect(goal_rect):
        # 上昇中に天井の底にぶつかったらゴール
        if player.get_vel_y() < 0:
            rect.top = goal_rect.bottom
            player.set_vel_y(0)
            player.set_is_clear(True)

    # --- 4. 足場との当たり判定 ---
    player.set_on_ground(False)
    if player.get_vel_y() > 0:
        for plat in platforms:
            plat_rect = plat.get_rect()
            if rect.colliderect(plat_rect):
                if rect.bottom <= plat_rect.top + player.get_vel_y() + 1:
                    rect.bottom = plat_rect.top
                    player.set_vel_y(0)
                    player.set_vel_x(0)
                    player.set_on_ground(True)
                    break


# ==========================================
# 3. メインループ
# ==========================================

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Jump King - 10 Floors to Goal")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)
    large_font = pygame.font.SysFont(None, 72)

    player = Player()
    
    bg_large = pygame.image.load("background_all.png")
    bg_large = pygame.transform.scale(bg_large, (600, 2400))
    
    # --- 10層分のマップ生成 ---
    platforms = []
    platforms.append(Platform(0, HEIGHT - 40, WIDTH, 40, GREEN)) # スタート床

    TOTAL_FLOORS = 10
    # ゴール（天井）のY座標：スタート床から 10層分(800px * 10) 上へ
    goal_y = (HEIGHT - 40) - (HEIGHT * TOTAL_FLOORS)
    
    # 金色の天井ブロックを生成
    goal_block = Platform(0, goal_y, WIDTH, 40, GOLD)

    # ゴールに到達するまで足場を生成し続ける
    platform_y = HEIGHT - 150
    while platform_y > goal_y + 100:
        w = random.randint(60, 130)
        x = random.randint(0, WIDTH - w)
        platforms.append(Platform(x, platform_y, w, 20, GREEN))
        gap_y = random.randint(80, 130)
        platform_y -= gap_y

    camera_y = 0
    max_height = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        
        # 関数呼び出し (ゴールブロックも渡して判定させる)
        update_player(player, keys, platforms, goal_block)

        p_rect = player.get_rect()

        # --- カメラ処理 ---
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

        # --- スコア・階層計算 ---
        current_height = (HEIGHT - 40) - p_rect.bottom
        if current_height > max_height:
            max_height = current_height
            
        # 今いる階層 (800px を 1階 とする)
        current_floor = min((current_height // HEIGHT) + 1, TOTAL_FLOORS)

        # --- 描画処理 ---
        bg_y = (1600 + camera_y) % 2400
        src_rect = pygame.Rect(0, bg_y, 600, 800)
        screen.blit(bg_large, (0, 0), src_rect)

        # ゴールの描画
        goal_rect = goal_block.get_rect()
        goal_draw_y = goal_rect.y - camera_y
        if -100 < goal_draw_y < HEIGHT + 100:
            screen.blit(goal_block.get_image(), (goal_rect.x, goal_draw_y))

        # 足場の描画
        for plat in platforms:
            plat_rect = plat.get_rect()
            draw_y = plat_rect.y - camera_y
            if -50 < draw_y < HEIGHT + 50:
                screen.blit(plat.get_image(), (plat_rect.x, draw_y))

        # プレイヤーの描画
        player_draw_y = p_rect.y - camera_y
        screen.blit(player.get_image(), (p_rect.x, player_draw_y))

        # チャージゲージと方向指示器
        if player.get_is_charging() and not player.get_is_clear():
            gauge_width = (player.get_charge_power() / player.get_max_charge()) * 40
            pygame.draw.rect(screen, RED, (p_rect.centerx - 20, player_draw_y - 15, gauge_width, 8))
        
        arrow_x = p_rect.right + 5 if player.get_direction() == 1 else p_rect.left - 10
        pygame.draw.rect(screen, WHITE, (arrow_x, player_draw_y + 15, 5, 5))

        # 情報表示 (UI)
        ui_text = font.render(f"Floor: {current_floor} / {TOTAL_FLOORS}   Max: {max_height // 10}m", True, WHITE)
        screen.blit(ui_text, (10, 10))

        # ゴールした時の演出
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