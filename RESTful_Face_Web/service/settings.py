from RESTful_Face_Web import settings
import os

# landmark
landmark_model_path = os.path.join(settings.BASE_DIR, 'service', 'shape_predictor_68_face_landmarks.dat')

# openface settings
openface_model_path = os.path.join(settings.BASE_DIR, 'service', 'openface', 'nn4.small2.v1.t7')
openface_imgDim = 96
openface_align_path = landmark_model_path

# face alignment (keep same as experiment)
face_size = (openface_imgDim, openface_imgDim) # have to be a tuple
eye_offset_percentage = [0.25, 0.25]

# face feature dimension
feature_dimension = [100, 1]

# feature names
pca_name = 'PCA'
lda_name = 'LDA'
hog_name = 'HOG'
lbp_name = 'LBP'
default_name = 'DEFAULT'
all_feature_names = [pca_name, lda_name, hog_name, lbp_name, default_name]

# classifier name
nearest_neighbor_name = 'NEAREST_NEIGHBOR'
naive_bayes_name = 'NAIVE_BAYES'
svm_name = 'SVM'
default_name = 'DEFAULT'
all_classifier_names = [nearest_neighbor_name, svm_name, default_name]
need_template_classifiers = [nearest_neighbor_name, default_name]
need_training_classifiers = [svm_name, ]

# HOG settings
hog_ori = 8
hog_cell = (16, 16)
hog_region = (1, 1)

# model path
pca_w_path = os.path.join(settings.BASE_DIR, 'service', 'pca', 'Wnorm.npy') # 25500 x 13145
pca_mean_path = os.path.join(settings.BASE_DIR, 'service', 'pca', 'mean.npy') # 25500 x 1
lda_w_path = os.path.join(settings.BASE_DIR, 'service', 'lda', 'final_w.npy') # 25500 x 257
lda_mean_path = os.path.join(settings.BASE_DIR, 'service', 'lda', 'mean.npy') # 25500 x 1

# PCA principle component
pca_k = 206 # cumulative 95%

# LBP settings
lbp_regions_num = [6, 6]
lbp_neighbors = 8
lbp_radius = 2
lbp_method = 'nri_uniform'
lbp_lda_w_path = os.path.join(settings.BASE_DIR, 'service', 'lbp', 'W.npy') # 3480 x 257

# SVM settings
svm_c = 1
svm_kernel = 'linear'

# verification threshold
openface_NN_H_Threshold = 0.68
openface_NN_M_Threshold = 0.76
openface_NN_L_Threshold = 0.85
openface_NN_Threshold = {'H': openface_NN_H_Threshold, 'M': openface_NN_M_Threshold, 'L': openface_NN_L_Threshold}


# error code
NO_TEMPLATE_ERROR = 4501
NO_CLASSIFIER_ERROR = 4502
NOT_ENOUGH_SUBJECT_ERROR = 4503
