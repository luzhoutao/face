from .base_service import BaseService
from PIL import Image
from . import settings
# feature
from .recognition import FeatureExtractor
# math
from numpy import linalg


class CompareService(BaseService):
    def is_valid_input_data(self, data=None, app=None):
        assert(data is not None)
        assert(app is not None)

        valid = 'face1' in data and 'face2' in data

        if valid:
            face1 = Image.open(data['face1'])
            face2 = Image.open(data['face2'])
            valid = tuple(face1.size) == tuple(settings.face_size) and tuple(face2.size) == tuple(settings.face_size)

            if valid:
                if 'threshold' in data:
                    valid = data['threshold'].lower() in ['l', 'm', 'h']
        return valid


    def execute(self, *args, **kwargs):
        data = kwargs['data']

        assert('face1' in data)
        assert('face2' in data)

        if 'threshold' not in data:
            threshold = settings.openface_NN_L_Threshold
        else:
            threshold = settings.openface_NN_Threshold[data['threshold']]

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
        return {'result': result}