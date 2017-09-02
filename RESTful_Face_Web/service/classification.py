# service settings
from . import settings
# svm
from sklearn import svm
from sklearn.externals import joblib  # serialization
# data
import numpy as np
# temporary files
import tempfile

class Classifier():
    _classifiers = {}
    _trainers = {}

    def __init__(self):
        self._classifiers[settings.nearest_neighbor_name] = self._nearest_neighbor
        self._classifiers[settings.svm_name] = self._svm
        self._classifiers[settings.naive_bayes_name] = self._naive_bayes
        self._classifiers['DEFAULT'] = self._default

        self._trainers[settings.svm_name] = self._train_svm

    def classify(self, probe_feature, classifier_name='DEFAULT', k=1, model=None, gallery=None, threshold=None):
        return self._classifiers[classifier_name](gallery, probe_feature, k, model, threshold)

    def train(self, gallery, classifier_name):
        assert(classifier_name in settings.need_training_classifiers)
        return self._trainers[classifier_name](gallery)

    def _train_svm(self, gallery):
        features = [f.reshape(-1) for f in gallery['features']]
        labels = gallery['subjects']

        clf = svm.SVC(C=settings.svm_c, kernel=settings.svm_kernel, probability=True, decision_function_shape='ovr')

        assert( len(np.unique(labels)) >= 2 )

        clf.fit(features, labels)

        tmpfile = tempfile.TemporaryFile(mode='w+b')
        joblib.dump(clf, tmpfile)

        return tmpfile

    def _svm(self, gallery, probe_feature, k, model, threshold):
        assert(gallery is None)

        if model is None:
            return {'info': 'SVM classifier not found. Please train it using /commands/enroll/ .', 'error_code': settings.NO_CLASSIFIAR_ERROR}

        clf = joblib.load(model.parameter_file)
        model.parameter_file.close()

        distance = clf.decision_function([probe_feature[:, 0].tolist(), ])

        if len(np.shape(distance)) == 1:
            if k == 1:
                return {'subjectID': clf.classes_[int(distance[0]<0)], 'distance': [np.abs(distance[0])]}
            if k == 2:
                return {'subjectID': clf.classes_ if distance[0]>0 else clf.classes_[::-1], 'distance': [np.abs(distance[0]), - np.abs(distance[0])]}

        topk_indices = np.argsort(distance[0])[::-1][:k]

        return { 'subjectID': clf.classes_[topk_indices], 'distance': np.array(distance[0])[topk_indices].tolist() } # if retrain, then save the new model


    def _nearest_neighbor(self, gallery, probe_feature, k, model, threshold):
        # the gallery should be the list of template, the vector of mean feature
        assert(model is None)
        assert(gallery is not None)

        distance = [ np.linalg.norm(template.reshape([-1, 1]) - probe_feature.reshape([-1, 1])) for template in gallery['templates']]

        topk_indices = np.argsort(distance)[:k]

        result = {'subjectID': np.array(gallery['subjects'])[topk_indices].tolist(), 'distance': np.array(distance)[topk_indices].tolist()}

        # the threshold only support openface embeddings with nearest neighbor classifier
        if threshold is None:
            return result

        mask = np.array(result['distance']) < threshold
        result['subjectID'] = np.array(result['subjectID'])[mask].tolist()
        result['distance'] = np.array(result['distance'])[mask].tolist()

        return result

    def _naive_bayes(self, gallery, probe_feature, k, model, threshold):
        pass


    def _default(self, gallery, probe_feature, k, model, threshold):
        return self._nearest_neighbor(gallery, probe_feature, k, model, threshold)
