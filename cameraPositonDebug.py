import pigpio
import time
import keyboard

ip = input('Please enter the raspberry pi ip: ')
hP = int(input('Please enter the horizontal GPIO pin number: '))
vP = int(input('Please enter the vertical GPIO pin number: '))

currentX = 1000
currentY = 1000
lerpX = 1000
lerpY = 1000

pi = pigpio.pi(ip, 8888)

def clip(value, lower, upper):
    return lower if value < lower else upper if value > upper else value

def lerp(a, b, time):
    time = 1-time
    value = (time * a) + ((1-time) * b)
    return value

rotate = True
print('Please use WASD to rotate the camera to the desired center position. Press (ENTER) to set the position')
while(rotate):
    if keyboard.is_pressed('w'):
        lerpY += 1
    if keyboard.is_pressed('d'):
        lerpX += 1
    if keyboard.is_pressed('a'):
        lerpX -= 1
    if keyboard.is_pressed('s'):
        lerpY -= 1
    if keyboard.is_pressed('enter'):
        rotate = False

    currentX = lerp(currentX, lerpX, 0.5)
    currentY = lerp(currentY, lerpY, 0.5)

    pi.set_servo_pulsewidth(hP, int(currentX))
    pi.set_servo_pulsewidth(vP, int(currentY))

pi.set_servo_pulsewidth(hP, 0)
pi.set_servo_pulsewidth(vP, 0)

print('Please edit turret.py global variables as such horizontalRest = ' + str(currentX) + ' and verticalRest = ' + str(currentY))
