import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

# Window setup
WIDTH, HEIGHT = 800, 600
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
pygame.display.set_caption("Mini Minecraft")

# OpenGL configuration
glMatrixMode(GL_PROJECTION)
gluPerspective(70, WIDTH / HEIGHT, 0.1, 100.0)
glMatrixMode(GL_MODELVIEW)

glEnable(GL_DEPTH_TEST)
glEnable(GL_CULL_FACE)

glClearColor(0.5, 0.7, 1.0, 1.0)  # Sky blue background

# Player and camera parameters
player_pos = [0.0, 0.0, -5.0]
camera_angle = [0.0, 0.0]  # pitch, yaw
move_speed = 0.1
mouse_sensitivity = 0.1
CUBE_SIZE = 1.0

# Build simple ground of cubes
cube_positions = []
for x in range(-4, 5):
    for z in range(-4, 5):
        cube_positions.append([x, -2, z])

pygame.event.set_grab(True)
pygame.mouse.set_visible(False)


def ray_intersects_cube(ray_origin, ray_direction, cube_center, cube_size):
    half_size = cube_size / 2.0
    min_bounds = [cube_center[0] - half_size, cube_center[1] - half_size, cube_center[2] - half_size]
    max_bounds = [cube_center[0] + half_size, cube_center[1] + half_size, cube_center[2] + half_size]

    t_enter = -float('inf')
    t_exit = float('inf')
    face_normal = [0, 0, 0]

    for i in range(3):
        if abs(ray_direction[i]) < 1e-6:
            if ray_origin[i] < min_bounds[i] or ray_origin[i] > max_bounds[i]:
                return None, None, None
        else:
            t1 = (min_bounds[i] - ray_origin[i]) / ray_direction[i]
            t2 = (max_bounds[i] - ray_origin[i]) / ray_direction[i]
            t_min_axis = min(t1, t2)
            t_max_axis = max(t1, t2)
            if t_min_axis > t_enter:
                t_enter = t_min_axis
                face_normal = [0, 0, 0]
                face_normal[i] = -1 if t1 > t2 else 1
            t_exit = min(t_exit, t_max_axis)
            if t_enter > t_exit or t_exit < 0:
                return None, None, None

    intersection = [ray_origin[i] + t_enter * ray_direction[i] for i in range(3)]
    return t_enter, intersection, face_normal


def draw_cube(position):
    x, y, z = position
    hs = CUBE_SIZE / 2.0
    vertices = [
        [x + hs, y - hs, z - hs],
        [x + hs, y + hs, z - hs],
        [x - hs, y + hs, z - hs],
        [x - hs, y - hs, z - hs],
        [x + hs, y - hs, z + hs],
        [x + hs, y + hs, z + hs],
        [x - hs, y - hs, z + hs],
        [x - hs, y + hs, z + hs],
    ]
    faces = [
        (0, 1, 2, 3),
        (4, 7, 5, 6),
        (0, 4, 5, 1),
        (3, 2, 7, 6),
        (1, 5, 7, 2),
        (0, 3, 6, 4),
    ]
    glBegin(GL_QUADS)
    for face in faces:
        for v in face:
            glVertex3fv(vertices[v])
    glEnd()


def cast_ray(mx, my):
    projection_matrix = glGetDoublev(GL_PROJECTION_MATRIX)
    modelview_matrix = glGetDoublev(GL_MODELVIEW_MATRIX)
    viewport = glGetIntegerv(GL_VIEWPORT)
    winX, winY = float(mx), float(viewport[3] - my)
    near = gluUnProject(winX, winY, 0.0, modelview_matrix, projection_matrix, viewport)
    far = gluUnProject(winX, winY, 1.0, modelview_matrix, projection_matrix, viewport)
    ray_origin = near
    direction = [far[i] - near[i] for i in range(3)]
    length = math.sqrt(sum(d*d for d in direction))
    ray_dir = [d/length for d in direction]
    best_t = float('inf')
    hit_index = None
    hit_normal = None
    for i, pos in enumerate(cube_positions):
        t, _, n = ray_intersects_cube(ray_origin, ray_dir, pos, CUBE_SIZE)
        if t is not None and t < best_t:
            best_t, hit_index, hit_normal = t, i, n
    return hit_index, hit_normal


running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = False
        if event.type == MOUSEBUTTONDOWN:
            mx, my = event.pos
            idx, normal = cast_ray(mx, my)
            if event.button == 1 and idx is not None:
                cube_positions.pop(idx)
            if event.button == 3 and idx is not None:
                x, y, z = cube_positions[idx]
                cube_positions.append([x + normal[0], y + normal[1], z + normal[2]])
        if event.type == MOUSEMOTION:
            dx, dy = event.rel
            camera_angle[0] -= dy * mouse_sensitivity
            camera_angle[1] += dx * mouse_sensitivity
            camera_angle[0] = max(-90, min(90, camera_angle[0]))
    keys = pygame.key.get_pressed()
    sin_yaw = math.sin(math.radians(camera_angle[1]))
    cos_yaw = math.cos(math.radians(camera_angle[1]))
    if keys[K_w]:
        player_pos[0] -= move_speed * sin_yaw
        player_pos[2] += move_speed * cos_yaw
    if keys[K_s]:
        player_pos[0] += move_speed * sin_yaw
        player_pos[2] -= move_speed * cos_yaw
    if keys[K_a]:
        player_pos[0] -= move_speed * cos_yaw
        player_pos[2] -= move_speed * sin_yaw
    if keys[K_d]:
        player_pos[0] += move_speed * cos_yaw
        player_pos[2] += move_speed * sin_yaw

    # Render scene
    glLoadIdentity()
    glRotatef(camera_angle[0], 1, 0, 0)
    glRotatef(camera_angle[1], 0, 1, 0)
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glColor3f(0.4, 0.8, 0.4)
    for pos in cube_positions:
        draw_cube(pos)
    pygame.display.flip()
    pygame.time.wait(10)

pygame.quit()
