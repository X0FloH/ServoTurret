import numpy as np 
import cv2
import sys
import time
import pigpio
from threading import Thread

#This could be the most disgusting code you have ever seen but it seems to work, any help on performance would be greatly appreciated

#CONFIGURE THESE VARIABLES:
global ip = '192.168.1.27'
global horizontalRest = 1300
global verticalRest = 1500
global horizontalPin = 17
global verticalPin = 27


#Useful Functions
def reMap(value, maxInput, minInput, maxOutput, minOutput):

	value = maxInput if value > maxInput else value
	value = minInput if value < minInput else value

	inputSpan = maxInput - minInput
	outputSpan = maxOutput - minOutput

	scaledThrust = float(value - minInput) / float(inputSpan)

	return minOutput + (scaledThrust * outputSpan)

def clip(value, lower, upper):
    return lower if value < lower else upper if value > upper else value

def lerp(a, b, time):
    time = 1-time
    value = (time * a) + ((1-time) * b)
    return value

#Camera Class
class ThreadedCamera(object):
    def __init__(self, src=0):

        #Define Variables
        self.lastX = 0
        self.lastY = 0

        self.currentH = horizontalRest
        self.currentV = verticalRest

        self.lerpH = horizontalRest
        self.lerpV = verticalRest

        self.servoHozPIN = horizontalPin
        self.servoVerPIN = verticalPin

        self.pi = pigpio.pi(ip, 8888)
        self.faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        self.capture = cv2.VideoCapture(src)
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 2)

        # FPS = 1/X
        # X = desired FPS
        self.FPS = 1/60
        self.FPS_MS = int(self.FPS * 1000)

        # Start frame retrieval thread
        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()

    def update(self):
        while True:
            if self.capture.isOpened():
                (self.status, self.frame) = self.capture.read()
            time.sleep(self.FPS)

    def show_frame(self):
        if(hasattr(self, 'frame')):
                gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)

                faces = self.faceCascade.detectMultiScale(
                        gray,
                        scaleFactor=1.1,
                        minNeighbors=5,
                        minSize=(2, 2),
                        flags=cv2.CASCADE_SCALE_IMAGE
                )

                for (x, y, w, h) in faces:
                        cv2.rectangle(self.frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

                if(len(faces) > 0):
                        # Get First Face
                        person = faces[0]
                        cv2.circle(self.frame, (int(person[0] + (person[2]/2)), int(person[1] + (person[3]/2))), 5, (255, 0, 0), 2)
                        x = person[0] + (person[2]/2)
                        y = person[1] + (person[3]/2)

                        #check if the frame has updated
                        if x != self.lastX:
                            #Calculate the pixel difference
                            pixelDifference = x - 250
                            #If it is to the left
                            if pixelDifference < 0:
                                #Convert pixels to pulsewidth difference
                                servoDifference = reMap(-pixelDifference, 255, 0, 400, 0)
                                #Move 1/3 of the way
                                servoDifference /= 3
                                self.currentH += servoDifference
                            else:
                                #Convert pixels to pulsewidth difference
                                servoDifference = reMap(pixelDifference, 255, 0, 400, 0)
                                #Move 1/3 of the way
                                servoDifference /= 3
                                self.currentH -= servoDifference
                            self.lastX = x
                            
                        #check if the frame has updated
                        if y != self.lastY:
                            #Calculate the pixel difference
                            pixelDifference = y - 250
                            #If it is up
                            if pixelDifference < 0:
                                #Convert pixels to pulsewidth difference
                                servoDifference = reMap(-pixelDifference, 255, 0, 400, 0)
                                #Move 1/3 of the way
                                servoDifference /= 3
                                self.currentV += servoDifference
                            else:
                                #Convert pixels to pulsewidth difference
                                servoDifference = reMap(pixelDifference, 255, 0, 400, 0)
                                #Move 1/3 of the way
                                servoDifference /= 3
                                self.currentV -= servoDifference
                            self.lastY = y

                #Make sure the servos dont collide with the build
                self.currentV = clip(self.currentV, 1000, 1800)
                self.currentH = clip(self.currentH, 800, 1900)

                #Smooth servo movement
                self.lerpH = lerp(self.lerpH, self.currentH, 0.5)
                self.lerpV = lerp(self.lerpV, self.currentV, 0.5)

                #Set the pulsewidth
                self.pi.set_servo_pulsewidth(self.servoHozPIN, self.lerpH)
                self.pi.set_servo_pulsewidth(self.servoVerPIN, self.lerpV)

                # Display the resulting frame
                cv2.imshow('Video', self.frame)
                cv2.waitKey(self.FPS_MS)

if __name__ == '__main__':
    src = 'http://' + ip + '/stream.mjpg'
    threaded_camera = ThreadedCamera(src)
    while True:
        threaded_camera.show_frame()

        #Escape key pressed
        k = cv2.waitKey(30) & 0xff
        if k==27:
                break
    threaded_camera.pi.set_servo_pulsewidth(horizontalPin, horizontalRest)
    threaded_camera.pi.set_servo_pulsewidth(verticalPin, verticalRest)
    time.sleep(2)
    threaded_camera.pi.set_servo_pulsewidth(horizontalPin, 0)
    threaded_camera.pi.set_servo_pulsewidth(verticalPin, 0)
    # When everything done, release the capture 
    cv2.destroyAllWindows()
    threaded_camera.pi.stop()

    


