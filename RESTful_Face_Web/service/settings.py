from RESTful_Face_Web import settings
import os

# landmark
landmark_model_path = os.path.join(settings.BASE_DIR, 'service', 'shape_predictor_68_face_landmarks.dat')

face_size = [150, 150]
eye_offset_percentage = [0.2, 0.2]