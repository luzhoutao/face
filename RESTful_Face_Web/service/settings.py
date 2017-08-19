from RESTful_Face_Web import settings
import os

# landmark
landmark_model_path = os.path.join(settings.BASE_DIR, 'service', 'shape_predictor_68_face_landmarks.dat')

# face alignment (keep same as experiment)
face_size = (150, 170) # have to be a tuple
eye_offset_percentage = [0.25, 0.25]

# face feature dimension
feature_dimension = [100, 1]

# feature names
PCA_NAME = 'PCA'
LDA_NAME = 'LDA'

# model path
PCA_W_PATH = os.path.join(settings.BASE_DIR, 'service', 'pca', 'Wnorm.npy')
LDA_PCA_W_PATH = os.path.join(settings.BASE_DIR, 'service', 'lda', 'final_w.npy')