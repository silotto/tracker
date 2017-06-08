#!/usr/local/bin/python3

import cv2
import numpy as np
from collections import Counter

from tracker.recognition import face_cascade


class Recognizer:
    """
    The recognizer class contains a recognizer object that predicts the label of a given photo
    Several methods are included such as reading an image from disk, from video source, from a URL, searching in social
    media...
    """
    def __init__(self, recognizer_filename, source, max_width, max_height, threshold=None):
        """
        Initialization of attributes
        :param recognizer_filename: Path of the file containing the exported trained model
        :param source: Video source to read from in case of reading from a camera
        :param threshold: Threshold between recognizing and not recognizing an input photo
        """
        self.recognizer_filename = recognizer_filename
        self.source = source
        self.video_capture = None
        self.max_width = max_width
        self.max_height = max_height
        self.lbph_rec = self.eigenface_rec = self.fisherface_rec = None
        self.reload()

    def reload(self):
        self.lbph_rec = cv2.face.createLBPHFaceRecognizer()
        self.eigenface_rec = cv2.face.createEigenFaceRecognizer()
        self.fisherface_rec = cv2.face.createFisherFaceRecognizer()
        for recognizer, name in zip((self.lbph_rec, self.eigenface_rec), ('lbph', 'eigenface', 'fisherface')):
            try:
                recognizer.load(self.recognizer_filename+'_'+name+'.yml')
            except: pass

    def open_source(self):
        """
        Opens the source of video
        :return: 
        """
        self.video_capture = cv2.VideoCapture(self.source)

    def read_image(self):
        """
        Read a single image from the source
        :return: A tuple containing the original image and a greyscale version of it
        """
        self.open_source()
        image = np.array(self.video_capture.read()[1])
        return image, cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def predict(self, *grays):
        res = []
        for gray in grays:
            faces = face_cascade.detectMultiScale(gray)
            for x, y, w, h in faces:
                if self.lbph_rec is not None: res.append(self.lbph_rec.predict(gray[y: y + h, x: x + w])[0])
            for recognizer in (self.eigenface_rec, ):
                faces = face_cascade.detectMultiScale(gray)
                for x, y, w, h in faces:
                    img = gray[y: y + h, x: x + w].copy()
                    img = cv2.resize(img, (self.max_height,self.max_width))
                    if recognizer is not None: res.append(recognizer.predict(img)[0])
        return Counter(res).most_common(1)[0][0]

    def get_image_label(self, *paths):
        """
        Gets the label of a saved photo on the disk
        :param path: Path of the photo
        :return: The predicted label of the photo
        """
        grays = []
        for path in paths:
            image = np.array(cv2.imread(path))
            grays.append(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))
        return self.predict(*grays)

    def recognize_from_video(self, num=10):
        """
        A generator the predicts the label of photos read from video source
        :param num: Number of iterations
        :return: The prediction of the photo
        """
        for i in range(num):
            image, gray = self.read_image()
            yield self.predict(gray)

    def get_label(self):
        for i in range(5):
            image, gray = self.read_image()
            yield self.predict(gray)

    def save_and_get_label(self):
        for i in range(5):
            self.read_image()
        grays, paths = [], []
        for i in range(5):
            grays.append(self.read_image()[1])
        for i, gray in enumerate(grays):
            faces = face_cascade.detectMultiScale(gray)
            for (x, y, w, h) in faces:
                paths.append('img'+str(i)+'.jpg')
                cv2.imwrite(paths[-1], gray[y:y + h, x:x + w])
        return self.get_image_label(*paths)
