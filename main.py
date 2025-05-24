import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
pygame.display.set_caption("3D Game")

# Player and camera settings
player_pos = [0.0, 0.0, -5.0]
camera_angle = [25.0, 25.0, 0.0]  # Pitch, Yaw, Roll
move_speed = 0.1
mouse_sensitivity = 0.1
CUBE_SIZE = 2.0 # Cubes are drawn from px-1 to px+1, so size is 2

# Initialize OpenGL
glMatrixMode(GL_PROJECTION)
gluPerspective(45, (WIDTH / HEIGHT), 0.1, 50.0)
glMatrixMode(GL_MODELVIEW)
glEnable(GL_DEPTH_TEST) # Enable depth testing
glEnable(GL_CULL_FACE)  # Enable face culling
glCullFace(GL_BACK)     # Cull back faces
glFrontFace(GL_CCW)     # Front face is counter-clockwise

# Cube positions for a grid
cube_positions = []
for x_coord in range(-1, 2): # X-coordinates from -1 to 1
    for z_coord in range(-1, 2): # Z-coordinates from -1 to 1
        cube_positions.append([x_coord * CUBE_SIZE, -2.0, z_coord * CUBE_SIZE]) # Use list for mutability

# Hide mouse cursor and grab input
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left mouse button
                mx, my = event.pos
                # Get matrices
                projection_matrix = glGetDoublev(GL_PROJECTION_MATRIX)
                modelview_matrix = glGetDoublev(GL_MODELVIEW_MATRIX)
                viewport = glGetIntegerv(GL_VIEWPORT)

                # Unproject mouse click
                winX, winY = float(mx), float(viewport[3] - my) # Pygame Y is inverted
                
                # Near plane
                world_near_x, world_near_y, world_near_z = gluUnProject(winX, winY, 0.0, modelview_matrix, projection_matrix, viewport)
                # Far plane
                world_far_x, world_far_y, world_far_z = gluUnProject(winX, winY, 1.0, modelview_matrix, projection_matrix, viewport)

                ray_origin = [world_near_x, world_near_y, world_near_z]
                
                ray_dir_x = world_far_x - world_near_x
                ray_dir_y = world_far_y - world_near_y
                ray_dir_z = world_far_z - world_near_z
                
                # Normalize direction vector
                length = math.sqrt(ray_dir_x**2 + ray_dir_y**2 + ray_dir_z**2)
                ray_direction = [ray_dir_x/length, ray_dir_y/length, ray_dir_z/length]

                # Ray-cube intersection test
                for i, cube_pos in enumerate(cube_positions):
                    if ray_intersects_cube(ray_origin, ray_direction, cube_pos, CUBE_SIZE):
                        cube_positions.pop(i)
                        break # Remove one cube per click

        if event.type == pygame.MOUSEMOTION:
            dx, dy = event.rel
            camera_angle[1] += dx * mouse_sensitivity  # Yaw
            camera_angle[0] -= dy * mouse_sensitivity  # Pitch
            # Clamp pitch
            camera_angle[0] = max(-90, min(90, camera_angle[0]))
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                # Move forward
                player_pos[0] -= move_speed * math.sin(math.radians(camera_angle[1]))
                player_pos[2] += move_speed * math.cos(math.radians(camera_angle[1]))
            if event.key == pygame.K_s:
                # Move backward
                player_pos[0] += move_speed * math.sin(math.radians(camera_angle[1]))
                player_pos[2] -= move_speed * math.cos(math.radians(camera_angle[1]))
            if event.key == pygame.K_a:
                # Strafe left
                player_pos[0] -= move_speed * math.cos(math.radians(camera_angle[1]))
                player_pos[2] -= move_speed * math.sin(math.radians(camera_angle[1]))
            if event.key == pygame.K_d:
                # Strafe right
                player_pos[0] += move_speed * math.cos(math.radians(camera_angle[1]))
                player_pos[2] += move_speed * math.sin(math.radians(camera_angle[1]))

    # OpenGL transformations
    glLoadIdentity()  # Reset transformations
    glRotatef(camera_angle[0], 1, 0, 0)  # Pitch
    glRotatef(camera_angle[1], 0, 1, 0)  # Yaw
    glRotatef(camera_angle[2], 0, 0, 1)  # Roll
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])

    # Clear buffers
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Set cube color (e.g., green)
    glColor3fv((0, 1, 0))

    for position in cube_positions:
        draw_cube(position)  # Render each cube at its position

    pygame.display.flip()  # Update the full display

# Quit Pygame
pygame.quit()

def ray_intersects_cube(ray_origin, ray_direction, cube_center, cube_size):
    """
    Checks if a ray intersects with an AABB cube.
    Returns (t_enter, intersection_point, face_normal) if intersection, else (None, None, None).
    """
    half_size = cube_size / 2.0
    min_bounds = [cube_center[0] - half_size, cube_center[1] - half_size, cube_center[2] - half_size]
    max_bounds = [cube_center[0] + half_size, cube_center[1] + half_size, cube_center[2] + half_size]

    t_min = [0.0, 0.0, 0.0]
    t_max = [0.0, 0.0, 0.0]
    t_enter = -float('inf')
    t_exit = float('inf')

    for i in range(3):
        if abs(ray_direction[i]) < 1e-6: # Ray is parallel to slab
            if ray_origin[i] < min_bounds[i] or ray_origin[i] > max_bounds[i]:
                return None, None, None # No intersection
        else:
            t1 = (min_bounds[i] - ray_origin[i]) / ray_direction[i]
            t2 = (max_bounds[i] - ray_origin[i]) / ray_direction[i]
            
            current_t_min = min(t1, t2)
            current_t_max = max(t1, t2)

            t_enter = max(t_enter, current_t_min)
            t_exit = min(t_exit, current_t_max)

    if t_enter >= t_exit or t_exit < 0: # No intersection or intersection is behind the ray
        return None, None, None

    # Intersection point
    intersection_point = [
        ray_origin[0] + ray_direction[0] * t_enter,
        ray_origin[1] + ray_direction[1] * t_enter,
        ray_origin[2] + ray_direction[2] * t_enter
    ]

    # Determine face normal
    face_normal = [0, 0, 0]
    epsilon = 1e-4 # For floating point comparison

    for i in range(3):
        if abs(intersection_point[i] - min_bounds[i]) < epsilon:
            face_normal[i] = -1
            break
        if abs(intersection_point[i] - max_bounds[i]) < epsilon:
            face_normal[i] = 1
            break
    
    # This normal calculation might be too simplistic if the intersection point is exactly on an edge or corner.
    # A more robust way would be to check which t_min[i] corresponds to t_enter.
    # For example, if t_enter == t_min[0], then the intersection is on the X-slab.
    # Then check if ray_direction[0] is positive or negative to determine if it's min_bounds[0] or max_bounds[0].
    
    # More robust normal calculation:
    # The face normal is determined by the axis for which t_min was maximal.
    best_axis = -1
    max_t_min_val = -float('inf')
    for i in range(3):
        if abs(ray_direction[i]) > 1e-6: # Avoid division by zero if parallel
            t1 = (min_bounds[i] - ray_origin[i]) / ray_direction[i]
            t2 = (max_bounds[i] - ray_origin[i]) / ray_direction[i]
            current_t_min_for_axis = min(t1, t2)
            if current_t_min_for_axis > max_t_min_val:
                max_t_min_val = current_t_min_for_axis
                best_axis = i
    
    face_normal = [0,0,0]
    if best_axis != -1: # Should always find an axis if there's an intersection
        # Check if the intersection point is on the min or max bound for the best_axis
        if abs(intersection_point[best_axis] - min_bounds[best_axis]) < epsilon:
            face_normal[best_axis] = -1.0
        elif abs(intersection_point[best_axis] - max_bounds[best_axis]) < epsilon:
            face_normal[best_axis] = 1.0
        else: 
            # Fallback if not perfectly on a face (should not happen with AABB)
            # This can happen if ray_direction[best_axis] is very small.
            # The previous simpler method might be more reliable here or a check on ray_direction sign.
            # If ray_direction[best_axis] > 0, normal is -1, else 1 for that axis.
            if ray_direction[best_axis] > 0:
                face_normal[best_axis] = -1.0
            else:
                face_normal[best_axis] = 1.0


    return t_enter, intersection_point, face_normal

def draw_cube(position):
    """Draws a solid cube at the given position."""
    px, py, pz = position
    half_cube_size = CUBE_SIZE / 2.0
    vertices = [
        [px + half_cube_size, py - half_cube_size, pz - half_cube_size],  # 0
        [px + half_cube_size, py + half_cube_size, pz - half_cube_size],  # 1
        [px - half_cube_size, py + half_cube_size, pz - half_cube_size],  # 2
        [px - half_cube_size, py - half_cube_size, pz - half_cube_size],  # 3
        [px + half_cube_size, py - half_cube_size, pz + half_cube_size],  # 4
        [px + half_cube_size, py + half_cube_size, pz + half_cube_size],  # 5
        [px - half_cube_size, py - half_cube_size, pz + half_cube_size],  # 6
        [px - half_cube_size, py + half_cube_size, pz + half_cube_size]   # 7
    ]

    # Define faces (quads) by vertex indices (counter-clockwise order)
    faces = [
        (0, 3, 2, 1),  # Back face
        (4, 5, 7, 6),  # Front face
        (3, 6, 7, 2),  # Left face
        (0, 1, 5, 4),  # Right face
        (1, 2, 7, 5),  # Top face
        (0, 6, 3, 4)   # Bottom face - corrected order (was 0,4,6,3)
    ]
    
    # Re-evaluate bottom face for CCW from outside
    # If looking from +Y towards -Y (down at the bottom face):
    # Original: 0, 4, 6, 3 -> (1,-1,-1), (1,-1,1), (-1,-1,1), (-1,-1,-1)
    # This is CW. For CCW, it should be 0, 3, 6, 4
    faces = [
        (0, 3, 2, 1),  # Back
        (4, 5, 7, 6),  # Front
        (3, 6, 7, 2),  # Left
        (0, 1, 5, 4),  # Right
        (1, 2, 7, 5),  # Top
        (0, 3, 6, 4)   # Bottom
    ]

    glBegin(GL_QUADS)
    for face in faces:
        for vertex_index in face:
            glVertex3fv(vertices[vertex_index])
    glEnd()
