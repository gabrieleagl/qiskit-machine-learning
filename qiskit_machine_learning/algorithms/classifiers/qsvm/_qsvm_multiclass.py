# This code is part of Qiskit.
#
# (C) Copyright IBM 2018, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""The multiclass classifier."""

import logging
import numpy as np

from ....utils.dataset_helper import map_label_to_class_name
from ._qsvm_abc import _QSVM_ABC

logger = logging.getLogger(__name__)

# pylint: disable=invalid-name


class _QSVM_Multiclass(_QSVM_ABC):
    """
    The multiclass classifier.

    the classifier is built by wrapping the estimator
    (for binary classification) with the multiclass extensions
    """

    def __init__(self, qalgo, multiclass_classifier):
        super().__init__(qalgo)
        self.multiclass_classifier = multiclass_classifier
        self.multiclass_classifier.params.append(qalgo)

    def train(self, data, labels):
        """ train """
        self.multiclass_classifier.train(data, labels)

    def test(self, data, labels):
        """ test """
        accuracy = self.multiclass_classifier.test(data, labels)
        self._ret['testing_accuracy'] = accuracy
        self._ret['test_success_ratio'] = accuracy
        return accuracy

    def predict(self, data):
        """ predict """
        predicted_labels = self.multiclass_classifier.predict(data)
        self._ret['predicted_labels'] = predicted_labels
        return predicted_labels

    def run(self):
        """
        put the train, test, predict together
        """
        self.train(self._qalgo.training_dataset[0], self._qalgo.training_dataset[1])
        if self._qalgo.test_dataset is not None:
            self.test(self._qalgo.test_dataset[0], self._qalgo.test_dataset[1])
        if self._qalgo.datapoints is not None:
            predicted_labels = self.predict(self._qalgo.datapoints)
            predicted_classes = \
                map_label_to_class_name(predicted_labels, self._qalgo.label_to_class)
            self._ret['predicted_classes'] = predicted_classes

        return self._ret

    def load_model(self, file_path):
        """ load model """
        model_npz = np.load(file_path, allow_pickle=True)  # pylint: disable=unexpected-keyword-arg
        for i in range(len(self.multiclass_classifier.estimators)):
            self.multiclass_classifier.estimators.ret['svm']['alphas'] = \
                model_npz['alphas_{}'.format(i)]
            self.multiclass_classifier.estimators.ret['svm']['bias'] = \
                model_npz['bias_{}'.format(i)]
            self.multiclass_classifier.estimators.ret['svm']['support_vectors'] = \
                model_npz['support_vectors_{}'.format(i)]
            self.multiclass_classifier.estimators.ret['svm']['yin'] = model_npz['yin_{}'.format(i)]
        try:
            self._qalgo.class_to_label = model_npz['class_to_label']
            self._qalgo.label_to_class = model_npz['label_to_class']
        except KeyError as ex:
            logger.warning("The model saved does not contain the mapping "
                           "between class names and labels. "
                           "Please setup them and save the model again "
                           "for further use. Error: %s", str(ex))

    def save_model(self, file_path):
        """ save model """
        model = {}
        for i, estimator in enumerate(self.multiclass_classifier.estimators):
            model['alphas_{}'.format(i)] = estimator.ret['svm']['alphas']
            model['bias_{}'.format(i)] = estimator.ret['svm']['bias']
            model['support_vectors_{}'.format(i)] = estimator.ret['svm']['support_vectors']
            model['yin_{}'.format(i)] = estimator.ret['svm']['yin']
        model['class_to_label'] = self._qalgo.class_to_label
        model['label_to_class'] = self._qalgo.label_to_class
        np.savez(file_path, **model)
