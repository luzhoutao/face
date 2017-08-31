from .base_service import BaseService
# image basic manipulation
from PIL import Image
# face detection
import dlib
# data structure
import numpy as np
# math and geometry
import math
# global settings
from . import settings
# try openface detection
import openface

class FaceAligner():
    def __init__(self, dest_sz, offset_pct):
        self.ler = [36, 42]  # left eye range
        self.rer = [42, 48]  # right eye range

        self.dest_sz = np.array(dest_sz)
        self.offset_pct = np.array(offset_pct)

        self.ref_dist = dest_sz[0] * (1 - 2 * offset_pct[0])

    def __affine_rotate(self, image, angle, center, resample=Image.BICUBIC):
        if center is None:
            image.rotate(angle=angle, resample=resample)
        (x0, y0) = center
        cosine = math.cos(angle)
        sine = math.sin(angle)
        a = cosine
        b = sine
        c = x0 - x0 * cosine - y0 * sine
        d = - sine
        e = cosine
        f = x0 * sine + y0 - y0 * cosine
        return image.transform(image.size, Image.AFFINE, (a, b, c, d, e, f), resample=resample)

    def align(self, image, landmarks):
        # find the eye
        left_eye = [landmarks[i] for i in range(self.ler[0], self.ler[1])]
        right_eye = [landmarks[i] for i in range(self.rer[0], self.rer[1])]

        # find the centroid of eyes
        lec = np.sum(left_eye, axis=0) / len(left_eye)
        rec = np.sum(right_eye, axis=0) / len(right_eye)

        # find the angle
        angle = - math.atan2(float(rec[1] - lec[1]), float(rec[0] - lec[0]))

        # find scale
        dis = np.sqrt(np.sum(np.array(lec - rec) ** 2))
        scale = dis / self.ref_dist

        # rotate the face
        rotated_image = self.__affine_rotate(image, angle, center=lec)

        # find the actual crop location
        crop_xy = (lec[0] - scale * self.dest_sz[0] * self.offset_pct[0], lec[1] - scale * self.dest_sz[1] * self.offset_pct[1])
        crop_sz = self.dest_sz * scale

        # crop the face from origin image
        face = rotated_image.crop(
            (int(crop_xy[0]), int(crop_xy[1]), int(crop_xy[0] + crop_sz[0]), int(crop_xy[1] + crop_sz[1])))
        resize_face = face.resize(self.dest_sz, Image.BICUBIC)

        return resize_face

class FaceDetectionService(BaseService):

    def is_valid_input_data(self, data=None):
        # check required user input
        has_image = ('image' in data)
        return has_image

    def execute(self, *args, **kwargs):
        """
        :param data: 
            image: the original image
        :return: 
            {
                'faces': image matrix as list
            }
            *** Decode ***
            import numpy as np
            from PIL import Image
            
            face_array = np.asarray(face)
            face_image = Image.fromarray(face_array, 'RGB')
        """

        # receive the input data
        assert('data' in kwargs)
        image_data = kwargs['data']['image']

        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor(settings.landmark_model_path)
        aligner = openface.AlignDlib(settings.openface_align_path)
        #aligner = FaceAligner(dest_sz=settings.face_size, offset_pct=settings.eye_offset_percentage)

        image = Image.open(image_data).convert('RGB')
        imarray = np.array(image)

        detections  = detector(imarray)

        faces = []
        for detection in detections:
            origin_size = (detection.right() - detection.left(), detection.bottom() - detection.top())

            shape = predictor(imarray, detection)
            landmarks = list(map(lambda p: (p.x, p.y), shape.parts()))

            #face = aligner.align(image, landmarks)
            
            face = aligner.align(settings.openface_imgDim, imarray, bb=detection)

            data = [(pixel[0], pixel[1], pixel[2]) for row in np.asarray(face) for pixel in row]
            faces.append({'data': data, 'origin_size': origin_size, 'size': settings.face_size})

        return {'faces': faces}
