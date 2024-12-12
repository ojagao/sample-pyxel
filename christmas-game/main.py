import pyxel
import random

class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dx = 1
        self.direction = 1
        self.is_alive = True
        self.start_x = x  # 初期位置を保存
        self.move_range = 24  # 3マス分（8 * 3 = 24ピクセル）
        self.initial_direction = 1  # 初期の向きを保存

    def update(self):
        # 左右に移動
        self.x += self.dx

        # 初期位置から3マス分の範囲で往復
        if self.x >= self.start_x + self.move_range:
            self.x = self.start_x + self.move_range
            self.dx *= -1
            self.direction *= -1
        elif self.x <= self.start_x:
            self.x = self.start_x
            self.dx *= -1
            self.direction *= -1

    def draw(self):
        if self.direction == 1:
            pyxel.blt(self.x, self.y, 0, 16, 8, 8, 8)
        else:
            pyxel.blt(self.x, self.y, 0, 8, 0, 8, 8)


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dx = 0
        self.dy = 0
        self.is_falling = False
        self.on_ground = False
        self.direction = 1  # 1: 右向き, -1: 左向き
        self.move_speed = 1.5  # 移動速度
        
        # ジャンプパラメータの改善
        self.jump_count = 0
        self.max_jumps = 1  # ジャンプ
        self.jump_strength = -4.5  # ジャンプ力を調整
        self.jump_cut_off = -2.0  # ジャンプボタンを離した時の最小速度
        self.gravity = 0.35  # 重力を微調整
        self.max_fall_speed = 6  # 最大落下速度
        self.is_alive = True  # 生存フラグを追加

    def check_tile_collision(self, x, y):
        # タイルのサイズ（8x8）を考慮して、プレイヤーの四隅のタイル座標をチェック
        tile_coords = [
            (int(x / 8), int(y / 8)),  # 左上
            (int((x + 7) / 8), int(y / 8)),  # 右上
            (int(x / 8), int((y + 7) / 8)),  # 左下
            (int((x + 7) / 8), int((y + 7) / 8))  # 右下
        ]
        
        for tile_x, tile_y in tile_coords:
            # タイルマップの範囲内かチェック
            if 0 <= tile_x < 45 and 0 <= tile_y < 16:
                tile = pyxel.tilemap(0).pget(tile_x, tile_y)
                # 地面として扱うタイル（X: 0-1, Y: 1-2のタイルと0-1, Y: 2-3のタイル）をチェック
                if (tile[0] == 0 and tile[1] == 1) or (tile[0] == 0 and tile[1] == 2):
                    return True, tile_y * 8  # 衝突したタイルのY座標も返す
        return False, 0

    def update(self):
        # 左右移動（シンプルな移動に変更）
        if pyxel.btn(pyxel.KEY_LEFT):
            self.dx = -self.move_speed
            self.direction = -1
        elif pyxel.btn(pyxel.KEY_RIGHT):
            self.dx = self.move_speed
            self.direction = 1
        else:
            self.dx = 0

        # ジャンプ
        if pyxel.btnp(pyxel.KEY_SPACE):
            if self.on_ground:
                self.dy = self.jump_strength
                self.is_falling = True
                self.on_ground = False
                self.jump_count = 1
            elif self.jump_count < self.max_jumps:
                self.dy = self.jump_strength
                self.jump_count += 1
        
        # ジャンプカットオフ（ジャンプボタンを離したときの処理）
        if not pyxel.btn(pyxel.KEY_SPACE) and self.dy < self.jump_cut_off:
            self.dy = self.jump_cut_off

        # 重力の適用
        if not self.on_ground:
            self.dy += self.gravity
            self.dy = min(self.dy, self.max_fall_speed)  # 落下速度の制限

        # 座標の更新（X方向）
        next_x = self.x + self.dx
        next_y = self.y

        # X方向の当たり判定
        has_collision, _ = self.check_tile_collision(next_x, self.y)
        if not has_collision:
            self.x = next_x
        else:
            # 壁にぶつかった場合
            self.dx = 0

        # Y方向の更新と当たり判定
        next_y = self.y + self.dy
        
        has_collision, ground_y = self.check_tile_collision(self.x, next_y)
        if not has_collision:
            self.y = next_y
            # 下向きの移動中は地面との接触をチェック
            if self.dy > 0:
                # 次のフレームでの地面チェック
                next_has_collision, next_ground_y = self.check_tile_collision(self.x, next_y + 1)
                if next_has_collision:
                    # 地面との接触が近い場合、スナップする
                    self.y = next_ground_y - 8
                    self.dy = 0
                    self.is_falling = False
                    self.on_ground = True
                    self.jump_count = 0
                else:
                    self.on_ground = False
                    self.is_falling = True
            else:
                self.on_ground = False
                self.is_falling = True
        else:
            # 地面に着地した場合
            if self.dy > 0:  # 下向きの移動の場合
                # タイルの上端に正確に位置を合わせる
                self.y = ground_y - 8
                self.dy = 0
                self.is_falling = False
                self.on_ground = True
                self.jump_count = 0
            else:  # 上向きの移動の場合（天井にぶつかった）
                self.y = ground_y + 8
                self.dy = 0

        # マップ全体での移動制限（45タイル=360px）
        self.x = max(0, min(self.x, 360 - 8))  # マップの幅に合わせて制限

    def check_collision(self, enemy):
        # 敵との当たり判定
        if (abs(self.x - enemy.x) < 8 and
            abs(self.y - enemy.y) < 8):
            self.is_alive = False
            return True
        return False

    def draw(self):
        # プレイヤーの向きに応じて描画
        if self.direction == 1:
            pyxel.blt(self.x, self.y, 0, 8, 8, 8, 8, 0)
        else:
            pyxel.blt(self.x, self.y, 0, 8, 8, -8, 8, 0)  # 左向きの場合は反転


class Snow:
    def __init__(self):
        # 雪の初期位置をマップ全体の範囲でランダムに設定
        self.x = random.randint(0, 360)  # マップ幅内でランダム（45タイル × 8ピクセル）
        self.y = random.randint(16, 32)  # 画面上部の指定された範囲で生成
        # 雪の形状をランダムに選択 (24,24), (24,32), (32,24), (32,32)
        self.pattern = random.choice([(24, 24), (24, 32), (32, 24), (32, 32)])
        self.fall_speed = 0.5  # 落下速度
        self.is_active = True

    def update(self):
        if not self.is_active:
            return
        
        self.y += self.fall_speed
        
        # 地面との当たり判定（タイルマップを使用）
        tile_y = int((self.y + 1) / 8)
        tile_x = int(self.x / 8)
        
        if 0 <= tile_x < 45 and 0 <= tile_y < 16:
            tile = pyxel.tilemap(0).pget(tile_x, tile_y)
            if (tile[0] == 0 and tile[1] == 1) or (tile[0] == 0 and tile[1] == 2):
                self.is_active = False

    def draw(self, camera_x):
        if self.is_active:
            # カメラ位置を考慮して描画位置を調整
            screen_x = self.x - camera_x
            # 画面内の場合のみ描画
            if 0 <= screen_x <= 160:
                pyxel.blt(screen_x, self.y, 0, self.pattern[0], self.pattern[1], 8, 8, 0)


class App:
    def __init__(self):
        pyxel.init(160, 128)
        pyxel.load('my_resource.pyxres')
        self.init_game()
        pyxel.run(self.update, self.draw)

    def spawn_enemies(self):
        enemies = []
        # tilemapをスキャンして敵を配置
        for y in range(16):
            for x in range(45):  # 45タイル分スキャン
                tile = pyxel.tilemap(0).pget(x, y)
                if tile == (1, 0):  # 敵のタイル
                    enemies.append(Enemy(x * 8, y * 8))
                    # 敵の位置のタイルを透明なタイルに変更
                    pyxel.tilemap(0).pset(x, y, (0, 0))
        return enemies

    def init_game(self):
        # タイルマップを初期状態に戻す
        pyxel.load('my_resource.pyxres')
        self.player = Player(0, 0)
        self.enemies = self.spawn_enemies()  # tilemapから敵を生成
        self.snows = []  # 雪のリストを初期化
        self.snow_spawn_timer = 0
        self.game_over = False
        self.game_clear = False  # ゲームクリアフラグを追加
        self.camera_x = 0  # カメラのX位置を追加

    def update(self):
        if not self.game_over and not self.game_clear:
            self.player.update()
            
            # ゲームクリア判定を追加（312px = 39タイル目）
            if self.player.x >= 312:
                self.game_clear = True
            
            # カメラの位置をプレイヤーに追従（画面中央に表示）
            target_camera_x = self.player.x - pyxel.width // 2
            # カメラが0より左に行かないようにする（45タイル=360px）
            self.camera_x = max(0, min(target_camera_x, 360 - pyxel.width))
            
            # 敵の更新と当たり判定
            for enemy in self.enemies:
                # 画面から少し余裕を持った範囲の敵だけ更新する
                if -64 <= enemy.x - self.camera_x <= pyxel.width + 64:
                    enemy.update()
                    if self.player.check_collision(enemy):
                        self.game_over = True

            # 雪の生成と更新
            self.snow_spawn_timer += 1
            if self.snow_spawn_timer >= 7:  # 7フレームごとに新しい雪を生成（さらに2倍の頻度）
                self.snows.append(Snow())
                self.snow_spawn_timer = 0

            # 雪の更新と画面外の雪を削除
            for snow in self.snows[:]:
                snow.update()
                if not snow.is_active or snow.y > 128:  # 画面下まで落ちた雪も削除
                    self.snows.remove(snow)

        if self.game_over and pyxel.btnp(pyxel.KEY_R):
            self.init_game()

    def draw(self):
        pyxel.cls(0)
        # カメラ位置を考慮してマップを描画（45タイル=360px）
        pyxel.bltm(0, 0, 0, self.camera_x, 0, 360, 128)

        if not self.game_over and not self.game_clear:
            # プレイヤーの描画（実際の位置で描画）
            real_x = self.player.x - self.camera_x
            pyxel.blt(real_x, self.player.y, 0, 8, 8, 8 if self.player.direction == 1 else -8, 8, 0)

            # 敵の描画（実際の位置で描画）
            for enemy in self.enemies:
                real_x = enemy.x - self.camera_x
                # 画面内の敵だけ描画
                if -8 <= real_x <= pyxel.width + 8:
                    if enemy.direction == 1:
                        pyxel.blt(real_x, enemy.y, 0, 16, 8, 8, 8)
                    else:
                        pyxel.blt(real_x, enemy.y, 0, 8, 0, 8, 8)

            # 雪の描画
            for snow in self.snows:
                snow.draw(self.camera_x)

        elif self.game_clear:
            # ゲームクリア画面
            pyxel.text(60, 64, "GAME CLEAR!", 11)
            pyxel.text(45, 74, "PRESS R TO RESTART", 8)
        else:
            # ゲームオーバー画面
            pyxel.text(60, 64, "GAME OVER", 8)
            pyxel.text(45, 74, "PRESS R TO RESTART", 8)


App()
