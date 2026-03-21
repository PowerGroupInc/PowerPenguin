import RPi.GPIO as GPIO
import time
from audioplayer import AudioPlayer
from rotary_class import RotaryEncoder
from threading import Thread, Event

global KNOB_PIN_A
KNOB_PIN_A = 17
global KNOB_PIN_B
KNOB_PIN_B = 12
global KNOB_BUTTON
KNOB_BUTTON = 6
global SERVO_PIN_1
SERVO_PIN_1 = 20
global SERVO_PIN_2
SERVO_PIN_2 = 16
global LEDARRAY_1_RED
LEDARRAY_1_RED = 23
global LEDARRAY_1_BLUE
LEDARRAY_1_BLUE = 24
global LEDARRAY_2_RED
LEDARRAY_2_RED = 19
global LEDARRAY_2_BLUE
LEDARRAY_2_BLUE = 26

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(SERVO_PIN_1, GPIO.OUT)
GPIO.setup(SERVO_PIN_2, GPIO.OUT)
GPIO.setup(LEDARRAY_1_RED, GPIO.OUT)
GPIO.setup(LEDARRAY_1_BLUE, GPIO.OUT)
GPIO.setup(LEDARRAY_2_RED, GPIO.OUT)
GPIO.setup(LEDARRAY_2_BLUE, GPIO.OUT)

global soundPlayingInt
soundPlayingInt = 0
global soundPlayingPath
soundPlayingPath = "./sound/rick.mp3"
global soundPlayingBPM
soundPlayingBPM = 114

global currentSound
#currentSound = AudioPlayer(soundPlayingPath)

def changeSound(newSound):
    global soundPlayingInt
    global soundPlayingPath

    match newSound:
        case 0 | "rick":
            soundPlayingInt = 0
            soundPlayingPath = "./sound/rick.mp3"
            soundPlayingBPM = 114
        case 1 | "nootnoot":
            soundPlayingInt = 1
            soundPlayingPath = "./sound/nootnoot.mp3"
            soundPlayingBPM = 100
        case 2 | "wilhelm":
            soundPlayingInt = 2
            soundPlayingPath = "./sound/wilhelm.mp3"
            soundPlayingBPM = 63
        case 3 | "fnaf2":
            soundPlayingInt = 3
            soundPlayingPath = "./sound/fnaf2.wav"
            soundPlayingBPM = 120
        case 4 | "siren":
            soundPlayingInt = 4
            soundPlayingPath = "./sound/siren.mp3"
            soundPlayingBPM = 175
        case 5 | "boom":
            soundPlayingInt = 5
            soundPlayingPath = "./sound/boom.mp3"
            soundPlayingBPM = 142
        case 6 | "cartoon":
            soundPlayingInt = 6
            soundPlayingPath = "./sound/cartoon.mp3"
            soundPlayingBPM = 175

def rotateSound(right):
    global soundPlayingInt

    if right:
        if soundPlayingInt == 6:
            soundPlayingInt = 0
        else:
            soundPlayingInt += 1
    else:
        if soundPlayingInt == 0:
            soundPlayingInt = 6
        else:
            soundPlayingInt -= 1

    changeSound(soundPlayingInt)

#changeSound(int(input("Enter an integer or the short name of a sound you'd like to hear!")))
#currentSound = AudioPlayer(soundPlayingPath)
#currentSound.play(block=False, loop=True)
#input("If you're reading and hearing this, it means the sound-player wasn't immediately garbage-collected!")

stop_event = Event()
stop_tease = Event()

def wings(stop_event):
    global SERVO_PIN_1
    global SERVO_PIN_2

    pwm1 = GPIO.PWM(SERVO_PIN_1, 50)
    pwm1.start(0)
    pwm2 = GPIO.PWM(SERVO_PIN_2, 50)
    pwm2.start(0)

    def set_angle(angle):
        global SERVO_PIN_1
        global SERVO_PIN_2
        #print(SERVO_PIN_1)
        #print(SERVO_PIN_2)
        #print(angle)
        nonlocal pwm1
        nonlocal pwm2

        duty_cycle_1 = (angle / 18) + 2.5
        duty_cycle_2 = ((180 - angle) / 18) + 2.5
        GPIO.output(SERVO_PIN_1, True)
        GPIO.output(SERVO_PIN_2, True)
        pwm1.ChangeDutyCycle(duty_cycle_1)
        pwm2.ChangeDutyCycle(duty_cycle_2)
        time.sleep(0.5)
        GPIO.output(SERVO_PIN_1, False)
        GPIO.output(SERVO_PIN_2, False)
        pwm1.ChangeDutyCycle(0)
        pwm2.ChangeDutyCycle(0)

    try:
        while not stop_event.is_set():
            set_angle(120)
            time.sleep((120/soundPlayingBPM - 0.5) if (soundPlayingBPM < 240) else 0)

            set_angle(160)
            time.sleep((120/soundPlayingBPM - 0.5) if (soundPlayingBPM < 240) else 0)

    finally:
        pwm1.stop()
        pwm2.stop()
        

def led(stop_event):
    global LEDARRAY_1_RED
    global LEDARRAY_1_BLUE
    global LEDARRAY_2_RED
    global LEDARRAY_2_BLUE
    GPIO.setup(LEDARRAY_1_RED, GPIO.OUT)
    GPIO.setup(LEDARRAY_1_BLUE, GPIO.OUT)
    GPIO.setup(LEDARRAY_2_RED, GPIO.OUT)
    GPIO.setup(LEDARRAY_2_BLUE, GPIO.OUT)

    #array1Blue = False
    #array2Blue = True

    def updateAll(a1r, a1b, a2r, a2b):
        GPIO.output(LEDARRAY_1_RED, a1r)
        GPIO.output(LEDARRAY_1_BLUE, a1b)
        GPIO.output(LEDARRAY_2_RED, a2r)
        GPIO.output(LEDARRAY_2_BLUE, a2b)

    try:
        while not stop_event.is_set():
            updateAll(True, False, False, True)
            time.sleep(60/soundPlayingBPM)
            updateAll(False, True, True, False)
            time.sleep(60/soundPlayingBPM)

    finally:
        updateAll(False, False, False, False)
        

def sound(stop_event):
    global currentSound
    currentSound = AudioPlayer(soundPlayingPath)
    currentSound.play(block=False, loop=True)

    try:
        while not stop_event.is_set():
            pass

    finally:
        currentSound.stop()
        

def soundTease(stop_tease):
    #print("King K. Rool")
    global currentSound
    currentSound = AudioPlayer(soundPlayingPath)
    currentSound.play(block=False, loop=False)

    try:
        while not stop_tease.is_set():
            time.sleep(1.5)
            currentSound.stop()
            return

    finally:
        return


def triggerAlarm():
    #print("trying to start the alarm")
    stop_tease.set()
    stop_tease.clear()
    stop_event.clear()
    tLed = Thread(target=led, args=(stop_event,))
    tWings = Thread(target=wings, args=(stop_event,))
    tSound = Thread(target=sound, args=(stop_event,))

    #print("ALARM!!")
    tLed.start()
    tWings.start()
    tSound.start()

    time.sleep(10)

    stop_event.set()
    tLed.join()
    tWings.join()
    tSound.join()

    #print("Alarm's over...")




global count
count = 0
global previousEvent
previousEvent = 0
#print("well we got in this far")
# This is the event callback routine to handle events
def switch_event(event):
    global count
    global previousEvent
    
    if event == RotaryEncoder.CLOCKWISE:
        
        if event == previousEvent or count >= 6:
            count += 1
            if count >= 4:
                #print(count)
                stop_tease.set()
                rotateSound(True)
                stop_tease.clear()
                tSoundTease = Thread(target=soundTease, args=(stop_tease,))
                tSoundTease.start()
                count = 0
        else:
            count += 1
        
        #print("Clockwise")
    elif event == RotaryEncoder.ANTICLOCKWISE:
        #print("Anticlockwise") 
        
        if event == previousEvent or count >= 6:
            count += 1
            if count >= 4:
                #print(count)
                stop_tease.set()
                rotateSound(False)
                stop_tease.clear()
                tSoundTease = Thread(target=soundTease, args=(stop_tease,))
                tSoundTease.start()
                count = 0
        else:
            count += 1
        
    elif event == RotaryEncoder.BUTTONDOWN:
        #print("button down!!")
        triggerAlarm()
    
    # elif event == RotaryEncoder.BUTTONUP:
    # 	print("Button up") 
    previousEvent = event
    
    return

# Define the switch
rswitch = RotaryEncoder(KNOB_PIN_A, KNOB_PIN_B, KNOB_BUTTON, switch_event)

#print("Pin A "+ str(KNOB_PIN_A))
#print("Pin B "+ str(KNOB_PIN_B))
#print("BUTTON "+ str(KNOB_BUTTON))

# Listen
while True:
    time.sleep(0.1)