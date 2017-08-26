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
pca_name = 'PCA'
lda_name = 'LDA'
hog_name = 'HOG'
lbp_name = 'LBP'
all_feature_names = [pca_name, lda_name, hog_name, lbp_name]

# classifier name
nearest_neighbor_name = 'NEAREST_NEIGHBOR'
naive_bayes_name = 'NAIVE_BAYES'
svm_name = 'SVM'
all_classifier_names = [nearest_neighbor_name, naive_bayes_name, svm_name]

# HOG settings
hog_ori = 8
hog_cell = (30, 34)
hog_region = (1, 1)

# model path
pca_w_path = os.path.join(settings.BASE_DIR, 'service', 'pca', 'Wnorm.npy') # 25500 x 13145
pca_mean_path = os.path.join(settings.BASE_DIR, 'service', 'pca', 'mean.npy') # 25500 x 1
lda_w_path = os.path.join(settings.BASE_DIR, 'service', 'lda', 'final_w.npy') # 25500 x 257
lda_mean_path = os.path.join(settings.BASE_DIR, 'service', 'lda', 'mean.npy') # 25500 x 1

# PCA principle component
pca_k = 206 # cumulative 95%

# LBP settings
lbp_regions_num = [6, 10]
lbp_neighbors = 8
lbp_radius = 2
lbp_method = 'nri_uniform'
lbp_lda_w_path = os.path.join(settings.BASE_DIR, 'service', 'lbp', 'W.npy') # 3480 x 257

# SVM settings
svm_c = 1
svm_kernel = 'rbf'


# openface settings
openface_model_path = os.path.join(settings.BASE_DIR, 'service', 'openface', 'nn4.small2.v1.t7')
openface_imgDim = 96

