import pygame
import sys
import os
import random

# カレントディレクトリの固定
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ==========================================
# 設計方針・共通ルール
# 1. クラス内の変数は、すべて「get_変数名」というメソッドを介してアクセスする
# 2. クラスに関係するすべての操作関数は、クラスの外部で定義する
# ==========================================

# 画面・物理設定
WIDTH, HEIGHT = 600, 800
FPS = 60
GRAVITY = 0.6

# カラー定義
BLACK = (20, 20, 25)
BLUE = (100, 150, 255)
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)

DARK_PANEL = (35, 35, 45)
PANEL_BORDER = (90, 90, 110)
LIGHT_BLUE = (120, 200, 255)                # ステータスUI用（青）
ORANGE = (255, 170, 80)                     # ベスト記録UI用（オレンジ）

# ギミック床の色定義
COLOR_NORMAL = (120, 120, 120)       # 通常の床（灰色）
COLOR_FAKE = (180, 0, 180)           # すり抜ける床（紫）
COLOR_ICE = (100, 200, 255)          # 滑る床（水色）
COLOR_TRAMPOLINE = (255, 140, 0)     # 大ジャンプする床（オレンジ）
COLOR_TRAP = (255, 50, 50)           # 最初に戻る床（赤）
COLOR_RED_UI = (255, 100, 100)       # チャージゲージ用（赤）

# 種類から色を取得するマッピング辞書
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
        # 画像・位置情報
        self.image_original = pygame.image.load("9.png")
        self.image_original = pygame.transform.scale(self.image_original, (30, 40))
        self._image = self.image_original
        self._rect = self._image.get_rect(center=(WIDTH // 2, HEIGHT - 100))
        
        # 移動・物理状態
        self._vel_x = 0
        self._vel_y = 0
        self._on_ground = False
        
        # ジャンプチャージ設定
        self._is_charging = False
        self._charge_power = 0
        self._max_charge = 20.0
        self._direction = 1                  # 1: 右, -1: 左
        
        # ゲーム状態
        self._is_clear = False
        self._on_ice = False      
        self._is_reset = False    
        
        # クリエイティブモード設定
        self._is_creative = False
        self._has_cheated = False            # クリエイティブ使用履歴（記録更新不可フラグ）

    # --- ゲッターメソッド ---
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
    def get_is_creative(self): return self._is_creative
    def get_has_cheated(self): return self._has_cheated

    # --- セッターメソッド ---
    def set_vel_x(self, value): self._vel_x = value
    def set_vel_y(self, value): self._vel_y = value
    def set_on_ground(self, value): self._on_ground = value
    def set_is_charging(self, value): self._is_charging = value
    def set_charge_power(self, value): self._charge_power = value
    def set_direction(self, value): self._direction = value
    def set_is_clear(self, value): self._is_clear = value
    def set_on_ice(self, value): self._on_ice = value
    def set_is_reset(self, value): self._is_reset = value
    def set_is_creative(self, value): self._is_creative = value
    def set_has_cheated(self, value): self._has_cheated = value


class Platform:
    def __init__(self, x, y, w, h, color, plat_type="normal"):
        self._image = pygame.Surface((w, h))
        self._image.fill(color)
        self._rect = self._image.get_rect(topleft=(x, y))
        self._type = plat_type

    # --- ゲッターメソッド ---
    def get_image(self): return self._image
    def get_rect(self): return self._rect
    def get_type(self): return self._type


# ==========================================
# 2. クラスを操作する関数（クラス外部定義）
# ==========================================

def update_player(player, keys, platforms, goal_block, jump_sound):
    """プレイヤーの移動、入力、衝突判定などの状態を更新する関数"""
    if not player.get_is_clear():
        
        # --- クリエイティブモードの切り替え制御 ---
        if keys[pygame.K_LSHIFT] and keys[pygame.K_c]:
            player.set_is_creative(True)
            player.set_has_cheated(True)  # チート履歴をON（トラップを踏むまで記録更新をストップ）
            player.set_vel_x(0)
            player.set_vel_y(0)
            player.set_is_charging(False)
            player.set_charge_power(0)
        elif keys[pygame.K_LSHIFT] and keys[pygame.K_a]:
            player.set_is_creative(False)

        # --- クリエイティブモード中の自由移動処理 ---
        if player.get_is_creative():
            speed = 10
            rect = player.get_rect()
            
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                rect.x -= speed
                player.set_direction(-1)
                player._image = pygame.transform.flip(player.image_original, True, False)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                rect.x += speed
                player.set_direction(1)
                player._image = player.image_original
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                rect.y -= speed
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                rect.y += speed

            # 画面左右端の移動制限
            if rect.left < 0: rect.left = 0
            if rect.right > WIDTH: rect.right = WIDTH
                
            return  # クリエイティブ中は物理演算や通常の当たり判定をスキップ

        # --- 通常モード：地上での移動とチャージ処理 ---
        if player.get_on_ground():
            if player.get_on_ice():
                player.set_vel_x(player.get_vel_x() * 0.96) # 氷の上は徐々に減速（滑る）
            else:
                player.set_vel_x(0)
            
            # 向きの変更
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player.set_direction(-1)
                player._image = pygame.transform.flip(player.image_original, True, False)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player.set_direction(1)
                player._image = player.image_original

            # ジャンプチャージ
            if keys[pygame.K_SPACE]:
                player.set_is_charging(True)
                current_power = player.get_charge_power()
                if current_power < player.get_max_charge():
                    player.set_charge_power(current_power + 0.4)
            else:
                # スペースキーが離されたらジャンプを実行
                if player.get_is_charging():
                    power = player.get_charge_power()
                    direction = player.get_direction()
                    
                    player.set_vel_y(-power * 0.9 - 5)
                    player.set_vel_x(direction * (power * 0.4 + 2))
                    
                    if jump_sound:
                        jump_sound.play()
                    
                    player.set_is_charging(False)
                    player.set_charge_power(0)
                    player.set_on_ground(False)
                    player.set_on_ice(False)
    
    # 空中にいる場合は重力を適用
    if not player.get_on_ground():
        player.set_vel_y(player.get_vel_y() + GRAVITY)

    rect = player.get_rect()

    # --- X軸方向の移動と壁・足場の側面衝突判定 ---
    rect.x += player.get_vel_x()
    if rect.left < 0:
        rect.left = 0
        player.set_vel_x(player.get_vel_x() * -0.5) # 跳ね返り
        player.set_direction(1)
    if rect.right > WIDTH:
        rect.right = WIDTH
        player.set_vel_x(player.get_vel_x() * -0.5) # 跳ね返り
        player.set_direction(-1)

    for plat in platforms:
        if plat.get_type() == "fake":
            continue # 紫の床（fake）は側面判定もスルー

        plat_rect = plat.get_rect()
        if rect.colliderect(plat_rect):
            if player.get_vel_x() > 0:    # 右移動中に衝突
                rect.right = plat_rect.left
                player.set_vel_x(player.get_vel_x() * -0.5)
                player.set_direction(-1)
            elif player.get_vel_x() < 0:  # 左移動中に衝突
                rect.left = plat_rect.right
                player.set_vel_x(player.get_vel_x() * -0.5)
                player.set_direction(1)

    # --- Y軸方向の移動と天井・着地判定 ---
    rect.y += int(player.get_vel_y())

    # ゴールブロックとの衝突判定（通常モード時のみクリア可能）
    goal_rect = goal_block.get_rect()
    if rect.colliderect(goal_rect):
        if player.get_vel_y() < 0:
            rect.top = goal_rect.bottom
            player.set_vel_y(0)
            player.set_is_clear(True)
            pygame.mixer.music.fadeout(2000) # BGMをフェードアウト

    player.set_on_ground(False)
    player.set_on_ice(False)

    # 通常の足場に対する上下の衝突判定ループ
    for plat in platforms:
        if plat.get_type() == "fake":
            continue # 紫の床（fake）は上下判定も完全にスルー

        plat_rect = plat.get_rect()
        if rect.colliderect(plat_rect):
            # 落下中の着地判定
            if player.get_vel_y() > 0:
                if rect.bottom <= plat_rect.top + player.get_vel_y() + 1:
                    
                    # トランポリン床（オレンジ）
                    if plat.get_type() == "trampoline":
                        rect.bottom = plat_rect.top
                        player.set_vel_y(-25) 
                        player.set_on_ground(False)
                        break
                    
                    # トラップ床（赤）
                    if plat.get_type() == "trap":
                        rect.center = (WIDTH // 2, HEIGHT - 100) 
                        player.set_vel_y(0)
                        player.set_vel_x(0)
                        player.set_is_reset(True) 
                        player.set_has_cheated(False) # スタートに戻ったらペナルティを解除
                        break

                    # 通常の着地処理
                    rect.bottom = plat_rect.top
                    player.set_vel_y(0)
                    
                    if plat.get_type() == "ice":
                        player.set_on_ice(True)
                    else:
                        player.set_on_ice(False)

                    player.set_on_ground(True)
                    break

            # 上昇中に天井（足場の裏側）に頭をぶつけた判定
            elif player.get_vel_y() < 0:
                rect.top = plat_rect.bottom
                player.set_vel_y(0)
                break


def draw_ui(screen, font, player, current_floor, total_floors, current_height, max_height):
    """画面左上のステータスUIを描画する関数"""
    panel_x = 10
    panel_y = 10
    panel_w = 300
    panel_h = 120

    # UIの枠組み
    panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
    pygame.draw.rect(screen, DARK_PANEL, panel_rect, border_radius=12)
    pygame.draw.rect(screen, PANEL_BORDER, panel_rect, 2, border_radius=12)
    
    # テキストレンダリングと配置
    title_text = font.render("STATUS", True, GOLD)
    screen.blit(title_text, (panel_x + 15, panel_y + 10))

    floor_text = font.render(f"Floor {current_floor} / {total_floors}", True, WHITE)
    screen.blit(floor_text, (panel_x + 15, panel_y + 42))

    height_text = font.render(f"Height: {current_height // 10} m", True, LIGHT_BLUE)
    screen.blit(height_text, (panel_x + 15, panel_y + 70))

    # クリエイティブ使用中はベスト記録の色を変更（更新停止中を表現）
    max_color = ORANGE if not player.get_has_cheated() else (150, 150, 150)
    max_text = font.render(f"Best: {max_height // 10} m", True, max_color)
    screen.blit(max_text, (panel_x + 180, panel_y + 70))

    # クリエイティブモード稼働中のテキスト表示
    if player.get_is_creative():
        creative_text = font.render("[ CREATIVE MODE ]", True, (255, 100, 255))
        screen.blit(creative_text, (panel_x + 5, panel_y + panel_h + 5))


# ==========================================
# 3. メインループ
# ==========================================

def main():
    pygame.init()
    pygame.mixer.init()
    
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("koukaton UP!!")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)
    large_font = pygame.font.SysFont(None, 72)

    # サウンドの読み込み
    jump_sound = None
    if os.path.exists("jump.wav"):
        jump_sound = pygame.mixer.Sound("jump.wav")
        jump_sound.set_volume(0.4)

    if os.path.exists("BGM.mp3"):
        pygame.mixer.music.load("BGM.mp3")
        pygame.mixer.music.set_volume(0.25)
        pygame.mixer.music.play(-1)

    player = Player()
    
    # 背景画像の読み込みとサイズ調整
    bg_large = pygame.image.load("background_all.png")
    bg_large = pygame.transform.scale(bg_large, (600, 2400))
    
    TOTAL_FLOORS = 10
    platforms = []
    
    # 初期位置の床（一番下）
    platforms.append(Platform(0, HEIGHT - 40, WIDTH, 40, COLOR_NORMAL, "normal")) 
    
    # 固定ステージデータ（下から順にすべての床の番号をコメントアウトで記載）
    # 形式: (x座標, y座標, 幅, ギミック種類)
    fixed_level_data = [
        # Floor 1 (Easy - 広くて近い)
        (100, 600, 150, "normal"),     # 床1
        (400, 450, 150, "normal"),     # 床2
        (150, 300, 150, "normal"),     # 床3
        (350, 150, 150, "normal"),     # 床4
        (250, 0, 150, "normal"),       # 床5
        
        # Floor 2 (Easy - 少し狭くなる)
        (50, -150, 120, "normal"),     # 床6
        (400, -300, 120, "normal"),    # 床7
        (100, -450, 120, "normal"),    # 床8
        (350, -600, 120, "normal"),    # 床9
        (200, -750, 120, "normal"),    # 床10
        
        # Floor 3 (氷の床 初登場)
        (450, -900, 100, "normal"),    # 床11
        (150, -1050, 100, "ice"),      # 床12
        (400, -1200, 100, "normal"),   # 床13
        (200, -1350, 100, "ice"),      # 床14
        (100, -1500, 100, "normal"),   # 床15
        
        # Floor 4 (トランポリン 初登場)
        (350, -1650, 100, "trampoline"), # 床16
        (100, -2100, 120, "normal"),   # 床17
        (400, -2250, 100, "normal"),   # 床18
        (200, -2400, 100, "normal"),   # 床19
        
        # Floor 5 (すり抜ける罠 初登場)
        (50, -2550, 100, "normal"),    # 床20
        (300, -2600, 100, "fake"),     # 床21
        (400, -2700, 100, "normal"),   # 床22
        (150, -2850, 100, "ice"),      # 床23
        (50, -3000, 100, "fake"),      # 床24
        (350, -3050, 100, "normal"),   # 床25
        (100, -3200, 100, "normal"),   # 床26
        
        # Floor 6 (幅が狭くなる)
        (450, -3350, 80, "normal"),    # 床27
        (200, -3500, 80, "ice"),       # 床28
        (50, -3650, 80, "trampoline"), # 床29
        (350, -4100, 80, "normal"),    # 床30
        
        # Floor 7 (トラップ床 初登場)
        (150, -4250, 80, "normal"),    # 床31
        (400, -4400, 80, "trap"),      # 床32
        (450, -4500, 80, "normal"),    # 床33
        (100, -4650, 80, "normal"),    # 床34
        (250, -4800, 80, "ice"),       # 床35
        
        # Floor 8 (複合ギミック)
        (450, -4950, 70, "normal"),    # 床36
        (50, -5100, 70, "fake"),       # 床37
        (150, -5200, 70, "normal"),    # 床38
        (300, -5350, 70, "trap"),      # 床39
        (50, -5450, 70, "normal"),     # 床40
        (400, -5600, 70, "trampoline"), # 床41
        
        # 41番目と42番目の間の追加床（左寄り）
        (80, -5850, 70, "normal"),     # 床42
        
        # Floor 9 (終盤・かなり狭い)
        (75, -6050, 70, "normal"),     # 床43
        (400, -6200, 70, "ice"),       # 床44
        (150, -6350, 70, "trap"),      # 床45
        (200, -6450, 70, "normal"),    # 床46
        
        # Floor 10 (最後の関門)
        (450, -6600, 60, "normal"),    # 床47
        (250, -6750, 60, "ice"),       # 床48
        (50, -6900, 60, "trampoline"), # 床49
    ]

    # 固定ステージデータを読み込んでリスト化
    for data in fixed_level_data:
        x, y, w, plat_type = data
        platforms.append(Platform(x, y, w, 20, COLOR_MAP[plat_type], plat_type))

    # ゴールブロックの設定
    goal_y = (HEIGHT - 40) - (HEIGHT * TOTAL_FLOORS)
    goal_block = Platform(0, goal_y, WIDTH, 40, GOLD, "goal")

    camera_y = 0
    max_height = 0
    clear_time = None  # クリアした瞬間のゲームティック記録用

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        
        # プレイヤー状態のアップデート
        update_player(player, keys, platforms, goal_block, jump_sound)

        p_rect = player.get_rect()

        # 赤いトラップ床を踏んでリセットされた場合のカメラ同期
        if player.get_is_reset():
            camera_y = 0
            player.set_is_reset(False) 

        # カメラの上方向スクロール処理
        SCROLL_TOP_MARGIN = 200
        if p_rect.y - camera_y < SCROLL_TOP_MARGIN:
            camera_y = p_rect.y - SCROLL_TOP_MARGIN

        # カメラの下方向滑らかな追従スクロール処理
        SCROLL_BOTTOM_MARGIN = 150
        camera_easing_down = 0.08
        if p_rect.bottom - camera_y > HEIGHT - SCROLL_BOTTOM_MARGIN:
            target_camera_y = p_rect.bottom - (HEIGHT - SCROLL_BOTTOM_MARGIN)
            camera_y += (target_camera_y - camera_y) * camera_easing_down

        if camera_y > 0:
            camera_y = 0

        # 高さ計算とベスト記録の保存（クリエイティブ使用中は記録更新をブロック）
        current_height = (HEIGHT - 40) - p_rect.bottom
        if current_height > max_height and not player.get_has_cheated():
            max_height = current_height
            
        current_floor = min((current_height // HEIGHT) + 1, TOTAL_FLOORS)
        display_floor = max(1, current_floor)

        # 背景描画（パララックス効果付き）
        bg_y = 1600 + (camera_y * 0.2)
        if bg_y < 0: bg_y = 0
        src_rect = pygame.Rect(0, int(bg_y), 600, 800)
        screen.blit(bg_large, (0, 0), src_rect)

        # ゴールブロックの描画
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

        # 通常モードかつジャンプチャージ中のみゲージを描画
        if player.get_is_charging() and not player.get_is_clear() and not player.get_is_creative():
            gauge_width = (player.get_charge_power() / player.get_max_charge()) * 40
            pygame.draw.rect(screen, COLOR_RED_UI, (p_rect.centerx - 20, player_draw_y - 15, gauge_width, 8))
        
        # プレイヤーの向きを示すガイドドットの描画
        arrow_x = p_rect.right + 5 if player.get_direction() == 1 else p_rect.left - 10
        pygame.draw.rect(screen, WHITE, (arrow_x, player_draw_y + 15, 5, 5))

        # 情報表示 (UIの描画)
        draw_ui(screen, font, player, current_floor, TOTAL_FLOORS, current_height, max_height)
        
        # クリア時の演出および10秒後の自動シャットダウン処理
        if player.get_is_clear():
            if clear_time is None:
                clear_time = pygame.time.get_ticks()

            # クリアテキスト描画
            clear_text = large_font.render("CLEAR!!", True, GOLD)
            text_rect = clear_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
            screen.blit(clear_text, text_rect)
            
            sub_text = font.render("CONGRATULATIONS!", True, WHITE)
            sub_rect = sub_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10))
            screen.blit(sub_text, sub_rect)
            
            # 自動終了までの秒数カウントダウン表示
            elapsed = pygame.time.get_ticks() - clear_time
            remaining = max(0, 10 - (elapsed // 1000))
            close_text = font.render(f"Closing in {remaining} seconds...", True, LIGHT_BLUE)
            close_rect = close_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))
            screen.blit(close_text, close_rect)
            
            # 10秒（10000ミリ秒）経過でループを終了
            if elapsed >= 10000:
                running = False

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()