from .base_service import BaseService
from PIL import Image
from . import settings
# feature
from .recognition import FeatureExtractor
# math
from numpy import linalg
import numpy as np
import cv2


class CompareService(BaseService):
    def is_valid_input_data(self, data=None, app=None):
        assert(data is not None)
        assert(app is not None)

        if 'face1' not in data:
            return False, 'Field <face1> is required.'
        if 'face2' not in data:
            return False, 'Field <face2> is required.'

        try: 
            face1 = Image.open(data['face1'])
            face2 = Image.open(data['face2'])
            face1_array = np.array(face1)
            face2_array = np.array(face2)
            cv2.cvtColor(face1_array, cv2.COLOR_RGB2BGR)
            cv2.cvtColor(face2_array, cv2.COLOR_RGB2BGR)
        except:
            return False, 'Face image wrong format or image data corrupted!'

        if not (tuple(face1.size) == tuple(settings.face_size) and tuple(face2.size) == tuple(settings.face_size)):
            return False, 'Face image has a wrong size. It should be '+ str(settings.face_size) + '.'

        if 'threshold' in data and data['threshold'].lower() not in ['l', 'm', 'h']:
            return False, 'Threshold(%s) not understand.'%(data['threshold'])
        return True, ''


    def execute(self, *args, **kwargs):
        data = kwargs['data']

        assert('face1' in data)
        assert('face2' in data)

        threshold = settings.openface_NN_L_Threshold
        if 'threshold' in data:
            threshold = settings.openface_NN_Threshold[data['threshold'].upper()]

        extractor = FeatureExtractor()

        face1 = Image.open(data['face1'])
        face2 = Image.open(data['face2'])

        feature1 = extractor.extract(face1, 'DEFAULT')
        feature2 = extractor.extract(face2, 'DEFAULT')

        dis = linalg.norm(feature1.reshape([-1, 1]) - feature2.reshape([-1, 1]))

        if dis < threshold:
            result = 1
        else:
            result = 0
        print(result)
        return {'result': result}
