import pygame
import math
import os
import random

pygame.init()
pygame.mixer.init()

# --------------------------------------------------
# НАСТРОЙКИ
# --------------------------------------------------

WIDTH, HEIGHT = 1100, 650
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Whispering Meadow")

clock = pygame.time.Clock()

# Пастельная палитра
SKY = (190, 220, 218)
SKY_LIGHT = (215, 235, 228)
CLOUD = (250, 245, 232)

GRASS = (150, 190, 142)
GRASS_DARK = (115, 160, 112)
GRASS_LIGHT = (180, 205, 145)

WOOD = (157, 112, 91)
WOOD_DARK = (116, 82, 73)
ROOF = (192, 137, 130)
ROOF_DARK = (158, 105, 105)

CREAM = (255, 245, 215)
PINK = (236, 170, 172)
TEXT = (83, 76, 84)
WHITE = (255, 255, 248)

# --------------------------------------------------
# ШРИФТ
# --------------------------------------------------

# Лучше использовать настоящий пиксельный шрифт:
# например: assets/fonts/pixel.ttf
#
# ВАЖНО: у pixel.ttf нет кириллицы, поэтому русский текст
# рисуется шрифтом handjet.ttf (пиксельный, с кириллицей).

FONT_PATH = "assets/fonts/pixel.ttf"
CYR_FONT_PATH = "assets/fonts/handjet.ttf"

TITLE_SIZE = 58
BUTTON_SIZE = 28
SMALL_SIZE = 18

CAP_PROBE_SIZE = 64

_font_cache = {}
_bbox_cache = {}
_cyr_size_cache = {}


def _glyph_bbox(path, char, size=CAP_PROBE_SIZE):
    """Прямоугольник глифа. Пустой, если глифа в шрифте нет."""

    key = (path, char, size)

    if key not in _bbox_cache:
        try:
            surf = pygame.font.Font(path, size).render(
                char, True, (255, 255, 255)
            )
            _bbox_cache[key] = surf.get_bounding_rect()
        except Exception:
            _bbox_cache[key] = pygame.Rect(0, 0, 0, 0)

    return _bbox_cache[key]


def _has_cyrillic(text):
    return any(
        "А" <= ch <= "я" or ch in "Ёё"
        for ch in text
    )


_base_cap = _glyph_bbox(FONT_PATH, "A").height
_cyr_cap = _glyph_bbox(CYR_FONT_PATH, "Л").height

if _glyph_bbox(FONT_PATH, "Л").height > 0:
    # В основном шрифте уже есть кириллица
    CYR_FONT_PATH = FONT_PATH
    CYR_FACTOR = 1.0
elif _base_cap > 0 and _cyr_cap > 0:
    # Шрифты дают разную высоту заглавных: подгоняем размер,
    # чтобы русский текст был той же высоты, что и латинский
    CYR_FACTOR = _base_cap / _cyr_cap
else:
    CYR_FONT_PATH = None
    CYR_FACTOR = 1.0


def get_font(size, path=FONT_PATH):
    """Возвращает шрифт нужного размера (с кэшем)."""

    key = (size, path)

    if key not in _font_cache:
        try:
            _font_cache[key] = pygame.font.Font(path, size)
        except Exception:
            _font_cache[key] = pygame.font.SysFont(
                "monospace", size, bold=True
            )

    return _font_cache[key]


def _cyr_size(size):
    """Размер кириллического шрифта с той же высотой заглавных."""

    if CYR_FONT_PATH is None or CYR_FONT_PATH == FONT_PATH:
        return size

    if size in _cyr_size_cache:
        return _cyr_size_cache[size]

    target = _glyph_bbox(FONT_PATH, "A", size).height
    matched = None

    if target > 0:
        for candidate in range(size, 7, -1):
            if _glyph_bbox(CYR_FONT_PATH, "Л", candidate).height <= target:
                matched = candidate
                break

    if matched is None:
        matched = max(8, int(round(size * CYR_FACTOR)))

    _cyr_size_cache[size] = matched
    return matched


def render_text(text, size, color):
    """Рисует строку тем шрифтом, в котором есть её символы."""

    if _has_cyrillic(text):
        return get_font(
            _cyr_size(size),
            CYR_FONT_PATH
        ).render(text, True, color)

    return get_font(size).render(text, True, color)

# --------------------------------------------------
# МУЗЫКА
# --------------------------------------------------

MUSIC_PATHS = [
    "assets/music/pixel_melody.wav",
    "assets/music/pixel_melody.ogg",
    "assets/music/pixel_melody.mp3",
]

for music_path in MUSIC_PATHS:

    if not os.path.exists(music_path):
        continue

    try:
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(0.35)
        pygame.mixer.music.play(-1)
        break
    except pygame.error as error:
        print(f"Не удалось проиграть {music_path}: {error}")

else:
    print("Файл музыки не найден.")
    print("Положи мелодию в assets/music/pixel_melody.wav")

# --------------------------------------------------
# ОБЛАКА
# --------------------------------------------------

clouds = [
    [120, 105, 0.8],
    [430, 70, 1.0],
    [820, 120, 0.7],
]

# --------------------------------------------------
# ЦВЕТЫ
# --------------------------------------------------

flowers = []

for _ in range(45):
    flowers.append({
        "x": random.randint(20, WIDTH - 20),
        "y": random.randint(450, HEIGHT - 20),
        "color": random.choice([
            (245, 183, 190),
            (249, 218, 145),
            (207, 184, 220),
            (255, 240, 180)
        ])
    })


# --------------------------------------------------
# ФУНКЦИИ РИСОВАНИЯ
# --------------------------------------------------

def draw_pixel_cloud(surface, x, y, scale):
    """Пиксельное облако."""

    color = CLOUD

    blocks = [
        (0, 12, 55, 20),
        (15, 2, 30, 28),
        (38, 8, 38, 24),
        (65, 15, 45, 17),
    ]

    for bx, by, w, h in blocks:
        pygame.draw.rect(
            surface,
            color,
            (
                int(x + bx * scale),
                int(y + by * scale),
                int(w * scale),
                int(h * scale)
            )
        )


def draw_tree(surface, x, y, scale=1):
    """Маленькое пиксельное дерево."""

    trunk = pygame.Rect(
        int(x - 10 * scale),
        int(y + 40 * scale),
        int(20 * scale),
        int(55 * scale)
    )

    pygame.draw.rect(surface, WOOD_DARK, trunk)

    # Тень
    pygame.draw.rect(
        surface,
        (105, 145, 102),
        (
            int(x - 45 * scale),
            int(y + 65 * scale),
            int(90 * scale),
            int(15 * scale)
        )
    )

    # Крона
    pygame.draw.rect(
        surface,
        GRASS_DARK,
        (
            int(x - 40 * scale),
            int(y + 5 * scale),
            int(80 * scale),
            int(60 * scale)
        )
    )

    pygame.draw.rect(
        surface,
        (135, 175, 125),
        (
            int(x - 30 * scale),
            int(y - 10 * scale),
            int(60 * scale),
            int(50 * scale)
        )
    )

    pygame.draw.rect(
        surface,
        GRASS_LIGHT,
        (
            int(x - 12 * scale),
            int(y - 22 * scale),
            int(25 * scale),
            int(25 * scale)
        )
    )


def draw_house(surface):
    """Домик в центре композиции."""

    x = WIDTH // 2
    y = 350

    # Тень
    pygame.draw.rect(
        surface,
        (111, 151, 106),
        (x - 150, y + 120, 300, 20)
    )

    # Стены
    pygame.draw.rect(
        surface,
        CREAM,
        (x - 125, y - 10, 250, 135)
    )

    # Деревянные балки
    pygame.draw.rect(
        surface,
        WOOD_DARK,
        (x - 125, y + 105, 250, 12)
    )

    pygame.draw.rect(
        surface,
        WOOD_DARK,
        (x - 120, y - 5, 10, 125)
    )

    pygame.draw.rect(
        surface,
        WOOD_DARK,
        (x + 110, y - 5, 10, 125)
    )

    # Крыша
    roof_points = [
        (x - 160, y),
        (x, y - 100),
        (x + 160, y),
    ]

    pygame.draw.polygon(
        surface,
        ROOF_DARK,
        roof_points
    )

    # Светлая часть крыши
    roof_inner = [
        (x - 140, y - 5),
        (x, y - 88),
        (x + 140, y - 5),
    ]

    pygame.draw.polygon(
        surface,
        ROOF,
        roof_inner
    )

    # Дверь
    pygame.draw.rect(
        surface,
        WOOD,
        (x - 28, y + 55, 56, 70)
    )

    pygame.draw.rect(
        surface,
        WOOD_DARK,
        (x - 28, y + 55, 56, 8)
    )

    # Окно
    pygame.draw.rect(
        surface,
        WOOD_DARK,
        (x + 55, y + 35, 55, 50)
    )

    pygame.draw.rect(
        surface,
        (178, 218, 217),
        (x + 62, y + 42, 41, 36)
    )

    pygame.draw.line(
        surface,
        WOOD_DARK,
        (x + 82, y + 42),
        (x + 82, y + 78),
        5
    )

    pygame.draw.line(
        surface,
        WOOD_DARK,
        (x + 62, y + 60),
        (x + 103, y + 60),
        5
    )


def draw_flower(surface, x, y, color):
    """Пиксельный цветок."""

    pygame.draw.rect(
        surface,
        (91, 145, 91),
        (x - 2, y + 5, 4, 14)
    )

    pygame.draw.rect(
        surface,
        color,
        (x - 7, y - 4, 6, 7)
    )

    pygame.draw.rect(
        surface,
        color,
        (x + 2, y - 4, 6, 7)
    )

    pygame.draw.rect(
        surface,
        color,
        (x - 3, y - 10, 7, 7)
    )

    pygame.draw.rect(
        surface,
        (248, 215, 112),
        (x - 2, y - 3, 5, 5)
    )


def draw_background(surface):
    # Небо
    surface.fill(SKY)

    # Солнце
    pygame.draw.rect(
        surface,
        (250, 221, 156),
        (80, 65, 65, 65)
    )

    # Облака
    for cloud in clouds:
        draw_pixel_cloud(
            surface,
            cloud[0],
            cloud[1],
            cloud[2]
        )

    # Дальние холмы
    pygame.draw.rect(
        surface,
        (165, 196, 153),
        (0, 360, WIDTH, 100)
    )

    # Основная трава
    pygame.draw.rect(
        surface,
        GRASS,
        (0, 440, WIDTH, HEIGHT - 440)
    )

    # Полосы пиксельной травы
    for x in range(0, WIDTH, 32):
        pygame.draw.rect(
            surface,
            GRASS_LIGHT,
            (x, 470, 16, 5)
        )

    # Деревья
    draw_tree(surface, 95, 310, 1.1)
    draw_tree(surface, 970, 320, 1.15)
    draw_tree(surface, 170, 355, 0.75)
    draw_tree(surface, 900, 350, 0.8)

    # Дом
    draw_house(surface)

    # Цветы
    for flower in flowers:
        draw_flower(
            surface,
            flower["x"],
            flower["y"],
            flower["color"]
        )


# --------------------------------------------------
# КНОПКИ
# --------------------------------------------------

class Button:

    def __init__(self, text, x, y, width, height):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.hover = False

    def update(self, mouse_pos):
        self.hover = self.rect.collidepoint(mouse_pos)

    def draw(self, surface):

        if self.hover:
            color = (255, 222, 213)
            border = (185, 128, 128)
        else:
            color = (255, 239, 218)
            border = (175, 132, 125)

        pygame.draw.rect(
            surface,
            border,
            self.rect
        )

        inner = self.rect.inflate(-6, -6)

        pygame.draw.rect(
            surface,
            color,
            inner
        )

        size = BUTTON_SIZE
        text_surface = render_text(self.text, size, TEXT)

        # Текст всегда должен помещаться в кнопку
        max_width = self.rect.width - 24

        while text_surface.get_width() > max_width and size > 10:
            size -= 1
            text_surface = render_text(self.text, size, TEXT)

        text_rect = text_surface.get_rect(
            center=self.rect.center
        )

        surface.blit(text_surface, text_rect)

    def clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


buttons = [
    Button("НОВАЯ ИГРА", WIDTH // 2 - 120, 470, 240, 58),
    Button("ЗАГРУЗИТЬ", WIDTH // 2 - 120, 540, 240, 58),
]

# --------------------------------------------------
# ВЫБОР СЛОЖНОСТИ
# --------------------------------------------------

DIFFICULTY_GAP = 20
DIFFICULTY_WIDTH = 240
DIFFICULTY_HEIGHT = 58
DIFFICULTY_ROW_X = WIDTH // 2 - (DIFFICULTY_WIDTH * 3 + DIFFICULTY_GAP * 2) // 2
DIFFICULTY_Y = 470

DIFFICULTY_LEVELS = ["ЛЕГКО", "СРЕДНЕ", "СЛОЖНО"]

difficulty_buttons = [
    Button(
        level,
        DIFFICULTY_ROW_X + i * (DIFFICULTY_WIDTH + DIFFICULTY_GAP),
        DIFFICULTY_Y,
        DIFFICULTY_WIDTH,
        DIFFICULTY_HEIGHT
    )
    for i, level in enumerate(DIFFICULTY_LEVELS)
]

back_button = Button("НАЗАД", WIDTH // 2 - 120, 540, 240, 58)

DIFFICULTY_TITLES = {
    "ЛЕГКО": "много ресурсов, враги слабы",
    "СРЕДНЕ": "сбалансированное прохождение",
    "СЛОЖНО": "мало ресурсов, враги сильны",
}

state = "menu"
selected_difficulty = None

exit_button = Button("ВЫЙТИ ИЗ ИГРЫ", WIDTH - 220, 20, 200, 48)


# --------------------------------------------------
# ЗАГОЛОВОК
# --------------------------------------------------

def draw_title(surface, title="WHISPERING MEADOW", y=75):

    size = TITLE_SIZE
    text = render_text(title, size, (255, 244, 220))

    # Заголовок всегда должен помещаться на экран
    while text.get_width() > WIDTH - 60 and size > 10:
        size -= 1
        text = render_text(title, size, (255, 244, 220))

    # Тень
    shadow = render_text(title, size, (151, 119, 126))

    shadow_rect = shadow.get_rect(
        center=(WIDTH // 2 + 4, y + 4)
    )

    surface.blit(shadow, shadow_rect)

    # Основной текст
    text_rect = text.get_rect(
        center=(WIDTH // 2, y)
    )

    surface.blit(text, text_rect)


# --------------------------------------------------
# АНИМАЦИЯ
# --------------------------------------------------

def draw_fireflies(surface, time):

    for i in range(14):

        x = 60 + (i * 83) % (WIDTH - 100)

        y = 410 + math.sin(
            time * 0.002 + i
        ) * 25

        brightness = int(
            150 + math.sin(
                time * 0.004 + i
            ) * 80
        )

        color = (
            255,
            230,
            brightness
        )

        pygame.draw.rect(
            surface,
            color,
            (int(x), int(y), 4, 4)
        )


# --------------------------------------------------
# СВЕТОВОЙ СЛЕД КУРСОРА
# --------------------------------------------------

TRAIL_LIFE = 750
TRAIL_SPARKS = 4
TRAIL_MIN_DISTANCE = 3
GLOW_RADIUS = 30
GLOW_LEVELS = 16


def _make_glow(level, radius=GLOW_RADIUS):
    """Радиальное свечение (для аддитивного блендинга)."""

    surf = pygame.Surface((radius * 2, radius * 2))
    surf.fill((0, 0, 0))

    for r in range(radius, 0, -1):
        falloff = (1 - r / radius) ** 2
        value = level * falloff
        pygame.draw.circle(
            surf,
            (
                int(150 * value),
                int(135 * value),
                int(95 * value)
            ),
            (radius, radius),
            r
        )

    return surf


glow_surfaces = [
    _make_glow(i / (GLOW_LEVELS - 1))
    for i in range(GLOW_LEVELS)
]

trail = []
trail_last_pos = None


def add_trail_point(x, y):
    """Точка следа с искрами, разлетающимися в разные стороны."""

    sparks = []

    for _ in range(TRAIL_SPARKS):
        angle = random.uniform(0, math.tau)
        distance = random.uniform(4, 15)
        sparks.append((
            math.cos(angle) * distance,
            math.sin(angle) * distance
        ))

    trail.append({
        "x": x,
        "y": y,
        "life": TRAIL_LIFE,
        "sparks": sparks
    })


def update_trail(dt, mouse_pos):
    """Добавляет новые точки и убирает погасшие."""

    global trail_last_pos

    if trail_last_pos is None:
        moved = math.inf
    else:
        moved = math.hypot(
            mouse_pos[0] - trail_last_pos[0],
            mouse_pos[1] - trail_last_pos[1]
        )

    if moved >= TRAIL_MIN_DISTANCE:
        add_trail_point(*mouse_pos)
        trail_last_pos = mouse_pos

    for point in trail:
        point["life"] -= dt

    trail[:] = [p for p in trail if p["life"] > 0]


def draw_trail(surface):
    """Полоса рассеянного света, которая постепенно исчезает."""

    for point in trail:

        t = point["life"] / TRAIL_LIFE
        x = point["x"]
        y = point["y"]

        # Мягкий ореол
        level = int(t * (GLOW_LEVELS - 1))

        if level > 0:
            glow = glow_surfaces[level]
            surface.blit(
                glow,
                glow.get_rect(center=(x, y)),
                special_flags=pygame.BLEND_RGB_ADD
            )

        # Искры: гаснут быстрее ореола и разлетаются сильнее
        spark_t = max(0.0, (t - 0.35) / 0.65)

        if spark_t <= 0:
            continue

        spread = 1 + (1 - t) * 1.6
        value = spark_t * spark_t
        color = (
            int(210 * value),
            int(190 * value),
            int(130 * value)
        )

        for dx, dy in point["sparks"]:
            surface.fill(
                color,
                (
                    int(x + dx * spread),
                    int(y + dy * spread),
                    3,
                    3
                ),
                special_flags=pygame.BLEND_RGB_ADD
            )


# --------------------------------------------------
# ГЛАВНЫЙ ЦИКЛ
# --------------------------------------------------

running = True

while running:

    dt = clock.tick(FPS)
    current_time = pygame.time.get_ticks()

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                if state == "difficulty":
                    state = "menu"
                else:
                    running = False

        # Выход из игры
        if exit_button.clicked(event):
            running = False

        if state == "menu":

            # Новая игра
            if buttons[0].clicked(event):
                state = "difficulty"

            # Загрузка
            if buttons[1].clicked(event):
                print("Открываем сохранения...")

        else:

            for difficulty_button in difficulty_buttons:
                if difficulty_button.clicked(event):
                    selected_difficulty = difficulty_button.text
                    print(f"Сложность: {selected_difficulty}")
                    state = "menu"

            if back_button.clicked(event):
                state = "menu"

    mouse_pos = pygame.mouse.get_pos()

    active_buttons = (
        buttons if state == "menu"
        else difficulty_buttons + [back_button]
    ) + [exit_button]

    for button in active_buttons:
        button.update(mouse_pos)

    # Световой след курсора
    update_trail(dt, mouse_pos)

    # Фон
    draw_background(screen)

    # Светлячки
    draw_fireflies(screen, current_time)

    if state == "menu":

        # Заголовок
        draw_title(screen)

        # Кнопки
        for button in buttons:
            button.draw(screen)

        # Подпись
        subtitle_text = "a quiet little place to call home"

    else:

        # Заголовок
        draw_title(screen, "ВЫБОР СЛОЖНОСТИ")

        # Кнопки
        for button in difficulty_buttons:
            button.draw(screen)

        back_button.draw(screen)

        # Подпись
        hovered = next(
            (b.text for b in difficulty_buttons if b.hover),
            selected_difficulty
        )

        subtitle_text = DIFFICULTY_TITLES.get(
            hovered,
            "выберите уровень сложности"
        )

    # Подпись
    subtitle = render_text(
        subtitle_text,
        SMALL_SIZE,
        TEXT
    )

    subtitle_rect = subtitle.get_rect(
        center=(WIDTH // 2, 620)
    )

    screen.blit(subtitle, subtitle_rect)

    # Кнопка выхода (правый верхний угол, на обоих экранах)
    exit_button.draw(screen)

    # След курсора поверх интерфейса
    draw_trail(screen)

    pygame.display.flip()


pygame.quit()
