# base class
from .base_service import BaseService
from company.models import Subject, Face, Feature, FeatureTemplate, ClassifierModel
# image operation
from PIL import Image
# service settings
from . import settings
# feature
from .extraction import FeatureExtractor
# classification
from .classification import Classifier
# math
from numpy import linalg
import json
import numpy as np
from functools import reduce
from sklearn.externals import joblib
from django.core.files import File


class EnrollmentService(BaseService):
    extractor = FeatureExtractor()
    classifier = Classifier()

    def is_valid_input_data(self, data=None, app=None):
        assert(data is not None)
        assert(app is not None)

        valid = True
        if 'feature' in data and (data['feature'].upper() not in settings.all_feature_names):
            return False, 'Feature not found.'
        if 'classifier' in data and (data['classifier'].upper() not in settings.all_classifier_names):
            return False, 'Classifier not found'
        return True, ''


    def execute(self, *args, **kwargs):
        app = kwargs['app']
        data = kwargs['data']

        feature_name = 'DEFAULT'
        if 'feature' in data:
            feature_name = data['feature'].upper()

        classifier_name = 'DEFAULT'
        if 'classifier' in data:
            classifier_name = data['classifier'].upper()

        subjects = Subject.objects.using(app.appID).all()

        gallery = {'features': [], 'subjects': []}
        is_updated = False
        for subject in subjects:
            # get subject's avaliable templates and faces
            template = subject.templates.all().filter(feature_name=feature_name)
            faces = subject.faces.all()

            if len(faces) == 0:
                continue

            # get feature of each face to append the gallery
            temp = []
            for face in faces:
                feature_data = self._get_face_feature(app.appID, face, feature_name)
                temp.append(feature_data.reshape([-1, 1]))
            gallery['features'].extend(temp)
            gallery['subjects'].extend(np.repeat(subject.subjectID, len(faces)) )

            # check if template exists and is valid
            assert(len(template)<=1)
            if len(template) == 1 and template[0].modified_time > subject.modified_time:
                continue

            # there are some new face image uploaded
            is_updated = True

            template, created = FeatureTemplate.objects.db_manager(app.appID).get_or_create(feature_name=feature_name, subject=subject)
            print('created: ', created)

            num  = len(temp)
            template_data = reduce(lambda x, y: x + y, temp) / num

            template.data = json.dumps(template_data.real.tolist())
            template.save()
            print(template.modified_time)

        # if the classification need training
        if classifier_name in settings.need_training_classifiers:
            classifier_model, created = ClassifierModel.objects.db_manager(app.appID).get_or_create(appID=app.appID, feature_name=feature_name, classifier_name=classifier_name)
            
            # check if the classification model is outdated
            if not created and classifier_model.modified_time > app.update_time:
                assert(is_updated==False)
                return {'Updated time': classifier_model.modified_time}

            if len(np.unique(gallery['subjects'])) < 2:
                return {'info': 'At least, you need to have 2 subject enrolled with at least one face iamge.', 'error_code': settings.NOT_ENOUGH_SUBJECT_ERROR}

            # get classification model of json format
            model_file = self.classifier.train(gallery, classifier_name)
            classifier_model.parameter_file = File(model_file)
            classifier_model.save()
            model_file.close()
            return {'Updated time': classifier_model.modified_time}
        return {'Updated time': app.update_time}
        
            
    def _get_face_feature(self, appID, face, feature_name):
        result = face.features.filter(feature_name=feature_name)
        if len(result) == 0:  # if not found, calculate and save
            with Image.open(face.image) as face_image:
                result = self.extractor.extract(face_image, name=feature_name).real
                face.image.close()
            Feature.objects.db_manager(appID).create(face=face, feature_name=feature_name, data=json.dumps(result.tolist()))
        else:  # if found, read
            result = np.array(json.loads(result[0].data))
        return result # numpy ndarray
