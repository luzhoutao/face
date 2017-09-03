from .base_service import BaseService
from . import settings
import numpy as np
from numpy import linalg
import os
# models
from company.models import Subject, Face, Feature, ClassifierModel, FeatureTemplate
from company.serializers import SubjectSerializer
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
# image
from PIL import Image
# string-list convertor
import json
# feature
from .extraction import FeatureExtractor
# classifier
from .classification import Classifier
# save file
import tempfile
# logging
import logging
log = logging.getLogger(__name__)
# openface
import openface
import cv2
import dlib
# time
from datetime import datetime

class RecognitionService(BaseService):
    extractor = FeatureExtractor()
    classifiers = Classifier()

    def is_valid_input_data(self, data=None, app=None):
        '''
        :param data: 
            'face' The face image
        :return: 
            must contain face image with the specified size
        '''
        assert(data is not None)
        assert(app is not None)

        if 'face' not in data:
            return False, '<face> is required.'

        try:
            face = Image.open(data['face'])
            face_array = np.array(face)
            cv2.cvtColor(face_array, cv2.COLOR_RGB2BGR)
        except:
            return False, 'Face image wrong format or image data corrupted!'

        if not (tuple(face.size) == tuple(settings.face_size)):
            return False, 'Face image has a wrong size' + str(face.size) + '. It should be '+ str(settings.face_size) + '.'

        if 'feature' in data and (data['feature'].upper() not in settings.all_feature_names):
            return False, 'Feature name is invalid. Valid options: ' + ', '.join(settings.all_feature_names) + '.'
        
        if 'classifier' in data and (data['classifier'].upper() not in settings.all_classifier_names):
            return False, 'Classifier name is invalid. Valid options: ' + ','.join(settings.all_classifier_names) + '.'

        if 'k' in data:
            try:
               k = int(data['k'])
               if len(Subject.objects.using(app.appID).all()) < k and k <= 0:
                   return False, 'k is invalid. Must within [1, len(subjects)]'
            except ValueError:
                return False, 'k should be a integer.'

        if 'threshold' in data and data['threshold'].lower() not in ['l', 'm', 'h']:
            return False, 'Threshold(%s) not understand.'%(data['threshold'])
        return True, ''


    def execute(self, *args, **kwargs):
        assert('data' in kwargs)
        assert('app' in kwargs)

        face_image = Image.open(kwargs['data']['face'])
        app = kwargs['app']
        request = kwargs['request']

        # top k 
        k = 1 if 'k' not in kwargs['data'] else int(kwargs['data']['k'])

        # feature
        feature_name = 'DEFAULT'
        if 'feature' in kwargs['data']:
            feature_name = kwargs['data']['feature'].upper() # must valid feature name

        log.info('Use feature "%s".'%(feature_name))

        # classifier
        classifier_name = 'DEFAULT'
        if 'classifier' in kwargs['data']:
            classifier_name = kwargs['data']['classifier'].upper() # must valid classifier name

        log.info('Use classifier "%s".'%(classifier_name))

        # threshold
        threshold = None
        if 'threshold' in kwargs['data']:
            threshold = settings.openface_NN_Threshold[kwargs['data']['threshold'].upper()]

        # get input data
        probe_feature = self.extractor.extract(face_image, name=feature_name).real
        log.info('probe_feature shape: %s'%(str(np.shape(probe_feature))))

        # retrieve model and classify
        gallery = None
        template_outdate = False
        classifier_outdate = False
        if classifier_name in settings.need_template_classifiers:
            templates = FeatureTemplate.objects.using(app.appID).filter(feature_name=feature_name) # check if outdated

            if len(templates) == 0:
                return {'info': 'No template found. Please upload face images and enroll them.', 'error_code': settings.NO_TEMPLATE_ERROR}

            gallery = {'templates': [], 'subjects': []}
            for template in templates:
                if template.modified_time < template.subject.modified_time:
                    template_outdate = True
                gallery['templates'].append(np.array(json.loads(template.data)))
                gallery['subjects'].append(template.subject.subjectID)

        classifier_models = ClassifierModel.objects.using(app.appID).filter(feature_name=feature_name, classifier_name=classifier_name, appID=app.appID)
        assert(len(classifier_models)<2)
        if len(classifier_models) == 0:
            model = None
        else:
            model = classifier_models[0]
            if model.modified_time < app.update_time:
                classifier_outdate = True
        
        results = self.classifiers.classify(probe_feature, classifier_name, k, model=model, gallery=gallery, threshold=threshold)
        
        tmp = []
        if template_outdate:
            tmp.append('template')
        if classifier_outdate:
            tmp.append('classifier ' + classifier_name)
        if len(tmp) != 0:
            warning = ' and '.join(tmp) + ' outdated. Please use /command/enroll/ to update!'
            results['warning'] = warning
        return results

        
