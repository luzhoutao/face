from .base_service import BaseService
from . import settings
from .settings import LDA_NAME, PCA_NAME, PCA_W_PATH
import numpy as np
from numpy import linalg
# models
from company.models import App, Person, Face, Feature
from company.serializers import PersonSerializer
# image
from PIL import Image
# string-list convertor
import json

class FeatureExtractor():
    extractors = {}
    def __init__(self):
        self.extractors[settings.PCA_NAME] = self.extract_pca
        self.extractors[settings.LDA_NAME] = self.extract_lda

    def extract(self, face, name):
        '''
        :param face: 
            the Image object of cropped valid face
        :param name: 
            the method the extractor uses
        :return: 
        '''
        return self.extractors[name](face)

    def extract_pca(self, face):
        assert (face.size == settings.face_size)
        face_array = np.array(face)
        face.close()

        W = np.load(settings.PCA_W_PATH)
        return np.dot(W.T, face_array.reshape([-1, 1]))


    def extract_lda(self, face):
        assert(face.size == settings.face_size)
        face_array = np.array(face)
        face.close()

        W = np.load(settings.LDA_PCA_W_PATH)
        return np.dot(W.T, face_array.reshape([-1, 1]))


class RecognitionService(BaseService):
    extractor = FeatureExtractor()

    def is_valid_input_data(self, data=None):
        '''
        :param data: 
            'face' The face image
        :return: 
            must contain face image with the specified size
        '''
        if 'face' in data:
            face = Image.open(data['face'])
            return tuple(face.size) == tuple(settings.face_size)
        return False

    def execute(self, *args, **kwargs):
        assert('data' in kwargs)
        assert('app' in kwargs)
        image = kwargs['data']['face']
        app = kwargs['app']
        request = kwargs['request']

        # get input data
        persons = [p for p in Person.objects.using(app.appID).all()]
        faces_per_person = [ [face for face in Face.objects.using(app.appID).filter(person=p)] for p in persons]

        # remove person without face enrolled
        mask = [ len(faces)>0 for faces in faces_per_person]
        persons = np.array(persons)[mask]
        faces_per_person = np.array(faces_per_person)[mask]

        if len(persons) == 0:
            return {'info': 'No face enrolled!'}

        # compute feature of face
        target_pca = self.extractor.extract_pca(Image.open(image).convert('L'))
        target_lda = self.extractor.extract_lda(Image.open(image).convert('L'))


        # retrieve all the feature; if not found, compute it
        pca_per_person = [np.hstack([ self.get_face_features(app.appID, face, feature_name=settings.PCA_NAME)
                              for face in faces])
                          for faces in faces_per_person]

        templates = [ np.mean(features, axis=1) for features in pca_per_person ]

        # do classification
        dis = [ linalg.norm(template.reshape([-1, 1]) - target_pca.reshape([-1, 1])) for template in templates ]

        # claim result
        person = persons[np.argmin(dis)]
        serializer = PersonSerializer(instance=person, context={'request': request})

        return {'person': serializer.data, 'dis': np.min(dis)}

    def get_face_features(self, appID, face, feature_name):
        result = Feature.objects.using(appID).filter(face=face, name=feature_name)
        if len(result) == 0:  # if not found, calculate and save
            result = self.extractor.extract(Image.open(face.image).convert('L'), name=feature_name)
            Feature.objects.db_manager(appID).create(face=face, name=feature_name, data=json.dumps(result.real.tolist()))
        else:  # if found, read
            result = np.array(json.loads(result[0].data))
        return result # numpy ndarray
