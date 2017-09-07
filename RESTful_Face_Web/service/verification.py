from .base_service import BaseService
from PIL import Image
from . import settings
# feature
from .recognition import FeatureExtractor
# math
from numpy import linalg
import numpy as np
import json
# model
from company.models import Face, Feature, Subject, FeatureTemplate

import cv2


class VerificationService(BaseService):

    extractor = FeatureExtractor()

    def is_valid_input_data(self, data=None, app=None):
        assert(data is not None)
        assert(app is not None)

        if 'face' not in data:
            return False, 'Field <face> is required.'

        try:
            tmp_image = Image.open(data['face'])
            tmp_array = np.array(tmp_image)
            cv2.cvtColor(tmp_array, cv2.COLOR_RGB2BGR)
        except:
            return False, 'Face image wrong format or image data corrupted!'
 
        if 'subjectID' not in data:
            return False, 'Field <subjectID> is required.'

        face = Image.open(data['face'])
        subject_set = Subject.objects.using(app.appID).filter(subjectID=data['subjectID'])

        if not (tuple(face.size) == tuple(settings.face_size)):
            return False, 'Face image has a wrong size' + str(face.size) + '. It should be '+ str(settings.face_size) + '.'

        if len(subject_set) == 0:
            return False, 'Wrong subject ID'

        if 'threshold' in data and data['threshold'].lower() not in ['l', 'm', 'h']:
            return False, 'Threshold(%s) not understand.'%(data['threshold'])
        return True, ''


    def execute(self, *args, **kwargs):
        app = kwargs['app']
        data = kwargs['data']
        
        face_image = Image.open(data['face'])

        if 'threshold' in data:
            threshold = settings.openface_NN_Threshold[data['threshold'].upper()]
        else:
            threshold = settings.openface_NN_L_Threshold

        subject = Subject.objects.using(app.appID).get(subjectID=data['subjectID'])

        template = subject.templates.all().filter(feature_name=settings.default_name)
        assert(len(template)<2)
        if len(template) == 0:
            return {'info': 'Please enroll the gallery using /commands/enroll/ ', 'error_code': settings.NO_TEMPLATE_ERROR}

        template_data = np.array(json.loads(template[0].data))
        warning = template[0].modified_time < subject.modified_time

        prob_feature = self.extractor.extract(face_image, settings.default_name)

        distance = np.linalg.norm(template_data.reshape([-1, 1]) - prob_feature.reshape([-1, 1]))

        result = {'result': 1 if distance < threshold else 0, 'distance': distance}
        if warning:
            result['warning'] = 'Subject template has outdated. Pleaes update by /commands/enroll/ '
        return result 
