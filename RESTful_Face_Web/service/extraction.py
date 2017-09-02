'''
This file is to extract feature from an instance of Image class (PIL package).
Only need 2 input: image instance and feature name
The feature name can be one of {PCA, LDA, HOG, LBP} or left to be default which is extracted by Openface model.
'''

# service settings
from . import settings
# data structure
import numpy as np
# image manipulation
from PIL import Image
# lbp feature
from skimage.feature import local_binary_pattern
import skimage
import openface
import cv2

class FeatureExtractor:
    extractors = {}

    def __init__(self):
        self.extractors[settings.pca_name] = self._pca
        self.extractors[settings.lda_name] = self._lda
        self.extractors[settings.hog_name] = self._hog
        self.extractors[settings.lbp_name] = self._lbp
        self.extractors[settings.default_name] = self._default
        self.pca_mean = None
        self.pca_w = None
        self.lda_mean = None
        self.lda_w = None
        self.lbp_w = None
        self.openface_nn = None

    def extract(self, face, name):
        '''
        This is the public interface for call the extraction function
        :param face: 
            the Image object of cropped valid face
        :param name: 
            the method the extractor uses
        :return: 
            the representation vector. (Size is specific to different feature algorithms)
        '''
        return self.extractors[name](face)

    def _pca(self, face):
        assert (face.size == settings.face_size)
        face_array = np.array(face.convert('L'))
        face.close()

        if self.pca_mean is None:
            print('open pca mean')
            self.pca_mean = np.load(settings.pca_mean_path)
        if self.pca_w is None:
            print('open pca w')
            self.pca_w = np.load(settings.pca_w_path)[:, :settings.pca_k]
        feature = np.dot(self.pca_w.T, face_array.reshape([-1, 1]) - self.pca_mean)  # 206 x 1
        return feature


    def _lda(self, face):
        assert(face.size == settings.face_size)
        face_array = np.array(face.convert('L'))
        face.close()

        if self.lda_mean is None:
            self.lda_mean = np.load(settings.lda_mean_path)
        if self.lda_w is None:
            self.lda_w  = np.load(settings.lda_w_path)
        feature = np.dot(self.lda_w.T, face_array.reshape([-1, 1]) - self.lda_mean)  # 257 x 1
        return feature

    def _lbp(self, face):
        assert(face.size == settings.face_size)
        face_array = np.array(face.convert('L'))
        face.close()

        # extract lbp descriptor
        [per_width, per_height] = [int(settings.face_size[0] / settings.lbp_regions_num[0]),
                                   int(settings.face_size[1] / settings.lbp_regions_num[1])]
        regions = [face_array[r * per_height:(r + 1) * per_height, c * per_width:(c + 1) * per_width] for c in
                   range(settings.lbp_regions_num[0]) for r in range(settings.lbp_regions_num[1])]

        patterns = [local_binary_pattern(region, settings.lbp_neighbors, settings.lbp_radius, settings.lbp_method) for region in regions]

        bin_range = int(np.ceil(np.max(patterns)))
        hists = [np.histogram(pattern.ravel(), bins=bin_range)[0] for pattern in patterns]  # ? normalize
        feature = np.vstack(hists).reshape([-1, 1])  # row - region , column - labels

        # use lda to do dimensionality reduction
        if self.lbp_w is None:
            self.lbp_w = np.load(settings.lbp_lda_w_path)
        feature = np.dot(self.lbp_w.T, feature)  # 257 x 1
        return feature

    def _hog(self, face):
        assert(face.size == settings.face_size)
        face_array = np.array(face.convert('L'))
        face.close()

        hog = skimage.feature.hog(face_array, orientations=settings.hog_ori, pixels_per_cell=settings.hog_cell, cells_per_block=settings.hog_region)

        return hog.reshape([-1, 1])  # 288 x 1

    def _default(self, face):
        assert(face.size == settings.face_size)
        face_array = np.array(face)
        face.close()

        if self.openface_nn is None:
            self.openface_nn = openface.TorchNeuralNet(settings.openface_model_path, imgDim=settings.openface_imgDim)

        alignedFace = cv2.resize(face_array, (settings.openface_imgDim, settings.openface_imgDim))
        rep = self.openface_nn.forward(alignedFace)
        return rep.reshape([-1, 1])

