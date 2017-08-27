from .base_service import BaseService
from . import settings
import numpy as np
from numpy import linalg
import os
# models
from company.models import Person, Face, Feature, ClassifierModel, FeatureGallery
from company.serializers import PersonSerializer
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
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
# openface
import openface
import cv2
import dlib
# time
from datetime import datetime

class FeatureExtractor:
    _extractors = {}

    def __init__(self):
        self._extractors[settings.pca_name] = self._pca
        self._extractors[settings.lda_name] = self._lda
        self._extractors[settings.hog_name] = self._hog
        self._extractors[settings.lbp_name] = self._lbp
        self._extractors['DEFAULT'] = self._default
        self.pca_mean = None
        self.pca_w = None
        self.lda_mean = None
        self.lda_w = None
        self.lbp_w = None
        self.openface_nn = None
        self.openface_align = None

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

        hog = feature.hog(face_array, orientations=settings.hog_ori, pixels_per_cell=settings.hog_cell, cells_per_block=settings.hog_region)

        return hog.reshape([-1, 1])  # 200 x 1

    def _default(self, face):
        assert(face.size == settings.face_size)
        face_array = np.array(face)
        face.close()

        if self.openface_nn is None:
            self.openface_nn = openface.TorchNeuralNet(settings.openface_model_path, imgDim=settings.openface_imgDim)
        if self.openface_align is None:
            self.openface_align = openface.AlignDlib(settings.openface_align_path)
 
        '''
        bb = self.openface_align.getLargestFaceBoundingBox(face_array)
        if bb is None:
            import pylab
            pylab.figure()
            pylab.imshow(face_array)
            pylab.show()
            detector = dlib.get_frontal_face_detector()
            dets = detector(face_array, 1)
            print(dets)
        alignedFace = self.openface_align.align(settings.openface_imgDim, face_array, bb,
                              landmarkIndices=openface.AlignDlib.OUTER_EYES_AND_NOSE)
        '''
        alignedFace = cv2.resize(face_array, (settings.openface_imgDim, settings.openface_imgDim))
        rep = self.openface_nn.forward(alignedFace)
        return rep.reshape([-1, 1])


class Classifier():
    _classifiers = {}

    def __init__(self):
        self._classifiers[settings.nearest_neighbor_name] = self._nearest_neighbor
        self._classifiers[settings.svm_name] = self._svm
        self._classifiers[settings.naive_bayes_name] = self._naive_bayes
        self._classifiers['DEFAULT'] = self._default

    def classify(self, classifier_name, model_set, feature_name, probe_feature, service):
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
        return self._classifiers[classifier_name](model_set, feature_name, probe_feature, service)

    def _svm(self, model_set, feature_name, probe_feature, service):
        print('doing svm')
        model = model_set.filter(feature_name=feature_name, name=settings.svm_name)

        retrain = len(model) == 0
        if not retrain:
            assert(len(model)==1)
            retrain = service.app.update_time > model[0].modified_time

        print('SVM for %s: retrain[%s]'%(feature_name, 'v' if retrain else 'x'))

        if retrain:
            start = datetime.now()
            gallery = service.get_gallery(need_template=False)
            print('Retrieve gallery time: ', datetime.now() - start)
            print('SVM gallery feature: ', len(gallery['feature']), [np.shape(g) for g in gallery['feature']])
            print('SVM gallery persons: ', gallery['person'])
            print('SVM gallery update time: ', gallery['update_time'])
            features = []
            labels = []
            for k, person in enumerate(gallery['person']):
                features_mat = gallery['feature'][k]
                feat_num = np.shape(features_mat)[1]
                features.extend([features_mat[:, i].tolist() for i in range(feat_num)])
                labels.extend(np.repeat(person.userID, feat_num))

            clf = svm.SVC(C=settings.svm_c, kernel=settings.svm_kernel, probability=True, decision_function_shape='ovr')
            start = datetime.now()
            clf.fit(features, labels)
            print("SVM (feature shape: %s)training time: %s"%(np.shape(features), datetime.now() - start))

        else:
            clf = joblib.load(model[0].parameter_file)
            #mean = joblib.load(model[0].additional_data)
            model[0].parameter_file.close()
            #model[0].additional_data.close()

        person = clf.predict([probe_feature[:, 0].tolist(), ])
        print(clf.decision_function([probe_feature[:, 0].tolist(), ]))

        return {'userID': person[0]}, clf if retrain else None # if retrain, then save the new model

    def _nearest_neighbor(self, model_set, feature_name, probe_feature, service):
        gallery = service.get_gallery(need_template=True)
        print('NN gallery feature: ', len(gallery['feature']), [np.shape(g) for g in gallery['feature']])
        print('NN gallery persons: ', gallery['person'])
        print('NN gallery update time: ', gallery['update_time'])
        dis = [ linalg.norm(template.reshape([-1, 1]) - probe_feature.reshape([-1, 1])) for template in gallery['feature'] ]

        print('NN dis: ', dis)

        # claim result
        person = gallery['person'][np.argmin(dis)]
        return {'userID': person.userID, 'name': person.name}, None

    def _naive_bayes(self, model_set, feature_name, probe_feature, service):
        pass

    def _default(self, model_set, feature_name, probe_feature, service):
        pass


class RecognitionService(BaseService):
    extractor = FeatureExtractor()
    classifiers = Classifier()
    app = None
    feature_name = None
    classifier_name = None

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

        # parse arguments
        assert('data' in kwargs)
        assert('app' in kwargs)
        image = kwargs['data']['face']
        self.app = kwargs['app']
        request = kwargs['request']

        self.feature_name = 'DEFAULT'
        if 'feature' in kwargs['data']:
            self.feature_name = kwargs['data']['feature'].upper() # must valid feature name
  
        print('feature name: ', self.feature_name)

        self.classifier_name = 'DEFAULT'
        if 'classifier' in kwargs['data']:
            self.classifier_name = kwargs['data']['classifier'].upper() # must valid classifier name

        print('classifier name: ', self.classifier_name)

        # get input data
        probe_feature = self.extractor.extract(Image.open(image), name=self.feature_name).real
        print('probe_feature: ', np.shape(probe_feature))

        # retrieve model and classify
        model_set = ClassifierModel.objects.using(self.app.appID)
        result, model = self.classifiers.classify(self.classifier_name, model_set, self.feature_name, probe_feature, self)

        # save the classifier model if needed
        if model is not None:
            print('saving model...')
            tmpfile = tempfile.TemporaryFile(mode='w+b')
            joblib.dump(model, tmpfile)
            model, created = ClassifierModel.objects.db_manager(self.app.appID).update_or_create(feature_name=self.feature_name, name=self.classifier_name, appID=self.app.appID,
                                                                           defaults={'parameter_file': File(tmpfile)})
            tmpfile.close()
            print('is created? ', created)

        return result

    def get_gallery(self, need_template):
        print('get gallery')
        persons = [p for p in Person.objects.using(self.app.appID).all()]
        print('get_gallery(): person - ', persons)

        galleries = []

        mask = np.empty(len(persons), dtype=np.bool)
        mask.fill(True)
        for k, person in enumerate(persons):
            if not need_template:
                gallery = self._get_person_gallery(person=person, feature_name=self.feature_name, app=self.app, need_mean=False)
                if gallery is None:
                    mask[k] = False
                else:
                    galleries.append(gallery)
                continue

            # need template
            try:
                gallery = FeatureGallery.objects.using(self.app.appID).get(person=person, name=self.feature_name)
                if gallery.modified_time < person.modified_time:
                    print('\tperson gallery is outdated.')
                    template = self._get_person_gallery(person=person, feature_name=self.feature_name, app=self.app,
                                                       need_mean=True)
                    if template is None:  # gallery is updated and no faces left
                        print('\tperson has no face left.')
                        mask[k] = False
                    else:
                        print('\tperson gallery is updated.')
                        gallery.data = json.dumps(template.tolist())
                        gallery.save()
                        galleries.append(template)
                else:
                    # no need to re-calculate
                    print('\tuse saved person gallery.')
                    galleries.append(np.array(json.loads(gallery.data)))
            except ObjectDoesNotExist:
                print('\tno gallery, first calculation.')
                template = self._get_person_gallery(person=person, feature_name=self.feature_name, app=self.app, need_mean=True)
                if template is None:
                    mask[k] = False
                else:
                    print('\tperson gallery is generated.')
                    gallery = FeatureGallery.objects.db_manager(self.app.appID).create(person=person, name=self.feature_name,
                                                                                  data=json.dumps(template.tolist()))
                    galleries.append(template)
            except MultipleObjectsReturned as e:
                print(person, self.feature_name)
                print(FeatureGallery.objects.using(self.app.appID).filter(person=person, name=self.feature_name))
                raise e

        persons = np.array(persons)[mask]
        #print('\tresult:')
        #print('\t\tpersons: ', persons)
        #print('\t\tgalleries: ', len(galleries), [np.shape(template) for template in galleries])
        if len(persons) == 0:
            return {'info': 'No face enrolled!'}

        return {'feature': galleries,
                   'person': persons,
                   'update_time': self.app.update_time}

    def _get_person_gallery(self, person=None, feature_name=None, app=None, need_mean=True):
        if person is None or feature_name is None or app is None:
            return None

        faces= [face for face in Face.objects.using(app.appID).filter(person=person)]

        if len(faces)==0:
            return None

        features = np.hstack([self._get_face_features(app.appID, face, feature_name=feature_name)
                                   for face in faces])
        if need_mean:
            features = np.mean(features, axis=1).reshape([-1, 1])

        return features

    def _get_face_features(self, appID, face, feature_name):
        result = Feature.objects.using(appID).filter(face=face, name=feature_name)
        if len(result) == 0:  # if not found, calculate and save
            print(face.image, face.id)
            with Image.open(face.image) as face_image:
                result = self.extractor.extract(face_image, name=feature_name).real
                face.image.close()
            #'For checking currently opened files'
            # import psutil
            # p = psutil.Process(os.getpid())
            # print(p.open_files())
            Feature.objects.db_manager(appID).create(face=face, name=feature_name, data=json.dumps(result.tolist()))
        else:  # if found, read
            result = np.array(json.loads(result[0].data))
        return result # numpy ndarray
