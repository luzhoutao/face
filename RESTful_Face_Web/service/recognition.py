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
        face_array = np.array(face)
        assert(np.shape(face_array) is settings.face_size)

        W = np.load(settings.PCA_W_PATH)
        return np.dot(W.T, face_array.reshape([-1, 1]))


    def extract_lda(self, face):
        pass


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
            return face.size == settings.face_size
        return False

    def execute(self, *args, **kwargs):
        assert('data' in kwargs)
        assert('app' in kwargs)
        image = kwargs['data']['image']
        app = kwargs['app']

        # get input data
        persons = [p for p in Person.object.using(app.appID).all()]
        faces_per_person = [ [face for face in Face.object.using(app.appID).filter(person=p)] for p in persons]

        # remove person without face enrolled
        mask = [ len(faces)>0 for faces in faces_per_person]
        persons = np.array(persons)[mask]
        faces_per_person = np.array(faces_per_person)[mask]

        # compute feature of face
        target_pca = self.extractor.extract_pca(Image.open(image))

        # retrieve all the feature; if not found, compute it
        pca_per_person = [np.array([ self.get_face_features(app.appID, face, feature_name=settings.PCA_NAME)
                              for face in faces])
                          for faces in faces_per_person]

        templates = [ np.mean(features, axis=1) for features in pca_per_person ]

        # do classification
        dis = [ linalg.norm(template - target_pca) for template in templates ]

        # claim result
        person = persons[np.argmin(dis)]
        serializer = PersonSerializer(person)

        return {'person': serializer.data}

    def get_face_features(self, appID, face, feature_name):
        result = Feature.objects.using(appID).filter(face=face, name=feature_name)
        if len(result) == 0:  # if not found, calculate and save
            result = self.extractor.extract(Image.open(face.image))
            Feature.objects.db_manager(appID).create(face=face, name=feature_name, data=json.dumps(result))
        else:  # if found, read
            result = json.loads(result[0])
        return result # numpy ndarray