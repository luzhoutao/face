from .base_service import BaseService
from . import settings
import numpy as np
from numpy import linalg
# models
from company.models import Person, Face, Feature, ClassifierModel
from company.serializers import PersonSerializer
# image
from PIL import Image
# string-list convertor
import json
# hog feature
from skimage import feature
# lbp feature
from skimage.feature import local_binary_pattern
# svm classifier
from sklearn import svm
from sklearn.externals import joblib
# save file
import tempfile
from django.core.files import File
# logging
import logging
log = logging.getLogger(__name__)


class FeatureExtractor:
    _extractors = {}

    def __init__(self):
        self._extractors[settings.pca_name] = self._pca
        self._extractors[settings.lda_name] = self._lda
        self._extractors[settings.hog_name] = self._hog
        self._extractors[settings.lbp_name] = self._lbp
        self._extractors['DEFAULT'] = self._default

    def extract(self, face, name):
        '''
        This is the public interface for call the extraction function
        :param face: 
            the Image object of cropped valid face
        :param name: 
            the method the extractor uses
        :return: 
        '''
        return self._extractors[name](face)

    def _pca(self, face):
        assert (face.size == settings.face_size)
        face_array = np.array(face)
        face.close()

        mean = np.load(settings.pca_mean_path)
        W = np.load(settings.pca_w_path)[:, :settings.pca_k]
        return np.dot(W.T, face_array.reshape([-1, 1]) - mean)  # 206 x 1


    def _lda(self, face):
        assert(face.size == settings.face_size)
        face_array = np.array(face)
        face.close()

        mean = np.load(settings.lda_mean_path)
        W = np.load(settings.lda_w_path)
        return np.dot(W.T, face_array.reshape([-1, 1]) - mean)  # 257 x 1

    def _lbp(self, face):
        assert(face.size == settings.face_size)
        face_array = np.array(face)
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
        w = np.load(settings.lbp_lda_w_path)
        return np.dot(w.T, feature)  # 257 x 1


    def _hog(self, face):
        assert(face.size == settings.face_size)
        face_array = np.array(face)
        face.close()

        hog = feature.hog(face_array, orientations=settings.hog_ori, pixels_per_cell=settings.hog_cell, cells_per_block=settings.hog_region)

        return hog.reshape([-1, 1])  # 200 x 1

    def _default(self, face):
        assert(face.size == settings.face_size)
        face_array = np.array(face)
        face.close()

        return None


class Classifier():
    _classifiers = {}

    def __init__(self):
        self._classifiers[settings.nearest_neighbor_name] = self._nearest_neighbor
        self._classifiers[settings.svm_name] = self._svm
        self._classifiers[settings.naive_bayes_name] = self._naive_bayes
        self._classifiers['DEFAULT'] = self._default

    def classify(self, classifier_name, model_set, feature_name, gallery, probe_feature, ):
        '''
        This is the public interface to call all kinds of classifier
        :param classifier_name: the name of classifier
        :param model_set: the model set of classifiers
        :param gallery: te gallery of (features, persons)
            features[i] is the matrix (2-d array) formed from features of persona[i]'s all faces
            features[i] is with dimensionality of (d, m) where d is the size of feature per face and m is the number of samples
            persona[i] is the instance of Person model in company.models
        :param probe_feature: the feature of the probe image
            it is a vector of a single feature with size of d
        :return: 
            the multi-class classification result - person or person's info.
        '''
        return self._classifiers[classifier_name](model_set, feature_name, gallery, probe_feature)

    def _svm(self, model_set, feature_name, gallery, probe_feature):
        # TODO normalize
        model = model_set.filter(feature_name=feature_name, name=settings.svm_name)

        retrain = len(model) == 0
        if not retrain:
            assert(len(model)==1)
            retrain = gallery['update_time'] > model[0].modified_time

        print('SVM for %s: retrain[%s]'%(feature_name, 'v' if retrain else 'x'))

        if retrain:
            features = []
            labels = []
            for k, person in enumerate(gallery['person']):
                features_mat = gallery['feature'][k]
                feat_num = np.shape(features_mat)[1]
                features.extend([features_mat[:, i].tolist() for i in range(feat_num)])
                labels.extend(np.repeat(person.userID, feat_num))

            clf = svm.SVC(C=settings.svm_c, kernel=settings.svm_kernel)
            clf.fit(features, labels)

        else:
            clf = joblib.load(model[0].parameter_file)

        person = clf.predict([probe_feature[:, 0].tolist()])

        return {'userID': person}, clf

    def _nearest_neighbor(self, model_set, feature_name, gallery, probe_feature):
        templates = [ np.mean(features, axis=1) for features in gallery['feature'] ]
        dis = [ linalg.norm(template.reshape([-1, 1]) - probe_feature.reshape([-1, 1])) for template in templates ]

        # claim result
        person = gallery['person'][np.argmin(dis)]
        return {'userID': person.userID, 'name': person.name}, None

    def _naive_bayes(self, model_set, feature_name, gallery, probe_feature):
        pass

    def _default(self, model_set, feature_name, gallery, probe_feature):
        pass


class RecognitionService(BaseService):
    extractor = FeatureExtractor()
    classifiers = Classifier()

    def is_valid_input_data(self, data=None):
        '''
        :param data: 
            'face' The face image
        :return: 
            must contain face image with the specified size
        '''
        if 'face' in data:
            face = Image.open(data['face'])
            valid = tuple(face.size) == tuple(settings.face_size)
            if 'feature' in data:
                valid = valid and (data['feature'].upper() in settings.all_feature_names)
            if 'classifier' in data:
                valid = valid and (data['classifier'].upper() in settings.all_classifier_names)
            return valid
        return False

    def execute(self, *args, **kwargs):
        assert('data' in kwargs)
        assert('app' in kwargs)
        image = kwargs['data']['face']
        app = kwargs['app']
        request = kwargs['request']

        feature_name = 'DEFAULT'
        if 'feature' in kwargs['data']:
            feature_name = kwargs['data']['feature'].upper() # must valid feature name

        classifier_name = 'DEFAULT'
        if 'classifier' in kwargs['data']:
            classifier_name = kwargs['data']['classifier'].upper() # must valid classifier name

        # get input data
        persons = [p for p in Person.objects.using(app.appID).all()]
        faces_per_person = [ [face for face in Face.objects.using(app.appID).filter(person=p)] for p in persons]

        # remove person without face enrolled
        mask = [ len(faces)>0 for faces in faces_per_person]
        persons = np.array(persons)[mask]
        faces_per_person = np.array(faces_per_person)[mask]

        if len(persons) == 0:
            return {'info': 'No face enrolled!'}

        # do lda recognition
        probe_feature = self.extractor.extract(Image.open(image).convert('L'), name=feature_name).real
        gallery = {'feature':
                       [np.hstack([ self.get_face_features(app.appID, face, feature_name=feature_name)
                              for face in faces])
                          for faces in faces_per_person],
                   'person': persons,
                   'update_time': app.update_time}
        model_set = ClassifierModel.objects.using(app.appID)
        result, model = self.classifiers.classify(classifier_name, model_set, feature_name, gallery, probe_feature)

        # save the classifier model if needed
        if model is not None:
            tmpfile = tempfile.TemporaryFile(mode='w+b')
            joblib.dump(model, tmpfile)
            model, created = ClassifierModel.objects.db_manager(app.appID).update_or_create(feature_name=feature_name, name=classifier_name, appID=app.appID,
                                                                           defaults={'parameter_file': File(tmpfile)})
            tmpfile.close()
            print(created)

        return result


    def get_face_features(self, appID, face, feature_name):
        result = Feature.objects.using(appID).filter(face=face, name=feature_name)
        if len(result) == 0:  # if not found, calculate and save
            result = self.extractor.extract(Image.open(face.image).convert('L'), name=feature_name).real
            Feature.objects.db_manager(appID).create(face=face, name=feature_name, data=json.dumps(result.tolist()))
        else:  # if found, read
            result = np.array(json.loads(result[0].data))
        return result # numpy ndarray
