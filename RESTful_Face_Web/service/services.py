'''
This file defines all the services available in this system.
(service ID, service Name)
'''
from .quality_check import QualityCheckService

SERVICES = []

QUALITY_CHECK = (0, 'Quality Check', QualityCheckService)
SERVICES.append(QUALITY_CHECK)

LANDMARK_DETECTION = (1, 'Landmark Detection', None)
SERVICES.append(LANDMARK_DETECTION)

ATTRIBUTE_PREDICATE = (2, 'Attribute Predicate', None)
SERVICES.append(ATTRIBUTE_PREDICATE)

RECOGNITION = (3, 'Recognition', None)
SERVICES.append(RECOGNITION)

FEATURE_EXTRACTION = (4, 'Feature Extraction', None)
SERVICES.append(FEATURE_EXTRACTION)

ENHANCEMENT = (5, 'Enhancement', None)
SERVICES.append(ENHANCEMENT)