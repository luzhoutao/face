'''
This file defines all the services available in this system.
(service ID, service Name)
'''
from .quality_check import QualityCheckService
from .face_detection import FaceDetectionService
from .recognition import RecognitionService
from .compare import CompareService
from .verification import VerificationService
from .enrollment import EnrollmentService

from company.models import SERVICES

QUALITY_CHECK = (0, 'Quality Check', QualityCheckService)
SERVICES.append(QUALITY_CHECK)

LANDMARK_DETECTION = (1, 'Landmark Detection', None)
SERVICES.append(LANDMARK_DETECTION)

ATTRIBUTE_PREDICATE = (2, 'Attribute Predicate', None)
SERVICES.append(ATTRIBUTE_PREDICATE)

RECOGNITION = (3, 'Recognition', RecognitionService)
SERVICES.append(RECOGNITION)

FEATURE_EXTRACTION = (4, 'Feature Extraction', None)
SERVICES.append(FEATURE_EXTRACTION)

ENHANCEMENT = (5, 'Enhancement', None)
SERVICES.append(ENHANCEMENT)

FACE_DETECTION = (6, 'Face Detection', FaceDetectionService)
SERVICES.append(FACE_DETECTION)

COMPARE = (7, 'Face Comparison', CompareService)
SERVICES.append(COMPARE)

VERIFICATION = (8, 'Face Verification', VerificationService)
SERVICES.append(VERIFICATION)

ENROLLMENT = (9, 'Gallery Enrollment', EnrollmentService)
SERVICES.append(ENROLLMENT)
