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


class VerificationService(BaseService):

    extractor = FeatureExtractor()

    def is_valid_input_data(self, data=None, app=None):
        assert(data is not None)
        assert(app is not None)

        valid = 'face' in data and 'userID' in data


        if valid:
            face = Image.open(data['face'])
            subject_set = Subject.objects.using(app.appID).filter(userID=data['userID'])

            valid = tuple(face.size) == tuple(settings.face_size) and len(subject_set) == 1

            if valid and 'threshold' in data:
                valid = data['threshold'].lower() in ['l', 'm', 'h']
        return valid


    def execute(self, *args, **kwargs):
        app = kwargs['app']
        data = kwargs['data']

        if 'threshold' in data:
            threshold = settings.openface_NN_Threshold[data['threshold']]
        else:
            threshold = settings.openface_NN_L_Threshold

        subject = Subject.objects.using(app.appID).get(data['subjectID'])

        try:
            template = FeatureTemplate.objects.using(self.app.appID).get(subject=subject, feature_name='DEFAULT')
            if template.modified_time < subject.modified_time:
                self.log.info('\tUpdate person "%s" gallery.' % (subject.subjectID))
                template_data = self._get_subject_features(subject=subject, feature_name='DEFAULT', app=self.app,
                                                  need_mean=True)
                if template_data is None:  # gallery is updated and no faces left
                    return {'info': 'The subject has no face enrolled'}
                else:
                    template.data = json.dumps(template_data.tolist())
                    template.save()
            else:
                # no need to re-calculate
                # print('\tuse saved person gallery.')

                template_data = np.array(json.loads(template.data))
        except:
            template_data = self._get_subject_features(subject=subject, feature_name='DEFAULT', app=self.app,
                                                  need_mean=True)
            if template is None:
                mask[k] = False
            else:
                template = FeatureTemplate.objects.db_manager(self.app.appID).create(subject=subject,
                                                                                     feature_name=self.feature_name,
                                                                                     data=json.dumps(template.tolist()))
                gallery.append(template)


        face = Image.open(data['face'])
        feature = self.extractor.extract(face, 'DEFAULT')

        dis = linalg.norm(template.reshape([-1, 1]) - feature.reshape([-1, 1]))

        if dis < threshold:
            result = 1
        else:
            result = 0
        return {'result': result}


    def _get_person_gallery(self, person=None, feature_name='DEFAULT', app=None, need_mean=True):
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

    def _get_face_features(self, appID, face, feature_name='DEFAULT'):
        result = Feature.objects.using(appID).filter(face=face, name=feature_name)
        if len(result) == 0:  # if not found, calculate and save
            with Image.open(face.image) as face_image:
                result = self.extractor.extract(face_image, name=feature_name).real
                face.image.close()
            Feature.objects.db_manager(appID).create(face=face, name=feature_name, data=json.dumps(result.tolist()))
        else:  # if found, read
            result = np.array(json.loads(result[0].data))
        return result # numpy ndarray


