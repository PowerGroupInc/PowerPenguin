import RPi.GPIO as GPIO
import time
from audioplayer import AudioPlayer
from rotary_class import RotaryEncoder
from threading import Thread, Event

# GPIO slot # contants:
# Rotary encoder
global KNOB_PIN_A
KNOB_PIN_A = 17
global KNOB_PIN_B
KNOB_PIN_B = 12
global KNOB_BUTTON
KNOB_BUTTON = 6

# SG90 servos
global SERVO_PIN_1
SERVO_PIN_1 = 20
global SERVO_PIN_2
SERVO_PIN_2 = 16

# LED arrays
global LEDARRAY_1_RED
LEDARRAY_1_RED = 23
global LEDARRAY_1_BLUE
LEDARRAY_1_BLUE = 24
global LEDARRAY_2_RED
LEDARRAY_2_RED = 19
global LEDARRAY_2_BLUE
LEDARRAY_2_BLUE = 26

# GPIO slot cleanup & configuration
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# GPIO assignments
GPIO.setup(SERVO_PIN_1, GPIO.OUT)
GPIO.setup(SERVO_PIN_2, GPIO.OUT)
GPIO.setup(LEDARRAY_1_RED, GPIO.OUT)
GPIO.setup(LEDARRAY_1_BLUE, GPIO.OUT)
GPIO.setup(LEDARRAY_2_RED, GPIO.OUT)
GPIO.setup(LEDARRAY_2_BLUE, GPIO.OUT)

# Global variables for storing the identity of the current sound ready to play
global soundPlayingInt
soundPlayingInt = 0
global soundPlayingPath
soundPlayingPath = "./sound/rick.mp3"
global soundPlayingBPM
soundPlayingBPM = 114

# Global audio player object
global currentSound
currentSound = AudioPlayer(soundPlayingPath)

# Method to globally alter the current sound based on its corresponding integer or filename.
def changeSound(newSound):
    global soundPlayingInt
    global soundPlayingPath
    global soundPlayingBPM
    global currentSound

    match newSound:
        case 0 | "rick":
            soundPlayingInt = 0
            soundPlayingPath = "./sound/rick.mp3"      # "Never Gonna Give You Up" / "Rickroll" (Rick Astley)
            soundPlayingBPM = 114
        case 1 | "nootnoot":
            soundPlayingInt = 1
            soundPlayingPath = "./sound/nootnoot.mp3"  # "Noot Noot!" (Pingu)
            soundPlayingBPM = 100
        case 2 | "wilhelm":
            soundPlayingInt = 2
            soundPlayingPath = "./sound/wilhelm.mp3"   # "Wilhelm Scream" (Warner Bros. stock sound library)
            soundPlayingBPM = 63
        case 3 | "fnaf2":
            soundPlayingInt = 3
            soundPlayingPath = "./sound/fnaf2.wav"     # "Hallway Ambience" (Five Nights at Freddy's 2)
            soundPlayingBPM = 120
        case 4 | "siren":
            soundPlayingInt = 4
            soundPlayingPath = "./sound/siren.mp3"     # American police car siren
            soundPlayingBPM = 175
        case 5 | "boom":
            soundPlayingInt = 5
            soundPlayingPath = "./sound/boom.mp3"      # "Vine Boom"
            soundPlayingBPM = 142
        case 6 | "cartoon":
            soundPlayingInt = 6
            soundPlayingPath = "./sound/cartoon.mp3"   # An assortment of 20th-century cartoon slapstick stock sound effects
            soundPlayingBPM = 175

    currentSound = AudioPlayer(soundPlayingPath)

# Method to call changeSound to rotate through the sounds as the rotary encorder does.
def rotateSound(right):     # boolean argument represents whether the encoder was turned clockwise or "right"
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

# Events to broadcast to make alarm threads and preview/"teast" threads respectively stop.
stop_event = Event()
stop_tease = Event()

# Servos are each rotated between 70 degrees and 30 degrees below the horizontal, mirrored across the penguin's body.
def wings(stop_event):
    global SERVO_PIN_1
    global SERVO_PIN_2

    # Setting up pulse-width modulation with 50Hz frequency
    pwm1 = GPIO.PWM(SERVO_PIN_1, 50)
    pwm1.start(0)
    pwm2 = GPIO.PWM(SERVO_PIN_2, 50)
    pwm2.start(0)

    def set_angle(angle):
        global SERVO_PIN_1
        global SERVO_PIN_2
        global soundPlayingBPM
        nonlocal pwm1
        nonlocal pwm2

        duty_cycle_1 = (angle / 18) + 2.5  # Convert angle to duty cycle
        duty_cycle_2 = ((180 - angle) / 18) + 2.5  # Angle is subtracted from 180 to mirror the other side
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
            time.sleep((120/soundPlayingBPM - 0.5) if (soundPlayingBPM < 240) else 0)  # time delay is set up to roughly time movements to every other beat

            set_angle(160)
            time.sleep((120/soundPlayingBPM - 0.5) if (soundPlayingBPM < 240) else 0)  # 0.5 is subtracted to account for the delay already present in set_angle()

    finally:  # Gracefully cease use of PWM when the stop event is received.
        pwm1.stop()
        pwm2.stop()
        
# Each of the two arrays takes its turn being entirely red or entirely blue.
def led(stop_event):
    global soundPlayingBPM
    global LEDARRAY_1_RED
    global LEDARRAY_1_BLUE
    global LEDARRAY_2_RED
    global LEDARRAY_2_BLUE
    GPIO.setup(LEDARRAY_1_RED, GPIO.OUT)
    GPIO.setup(LEDARRAY_1_BLUE, GPIO.OUT)
    GPIO.setup(LEDARRAY_2_RED, GPIO.OUT)
    GPIO.setup(LEDARRAY_2_BLUE, GPIO.OUT)

    # Accepts a boolean value for each color element of each array.
    def updateAll(a1r, a1b, a2r, a2b):
        GPIO.output(LEDARRAY_1_RED, a1r)
        GPIO.output(LEDARRAY_1_BLUE, a1b)
        GPIO.output(LEDARRAY_2_RED, a2r)
        GPIO.output(LEDARRAY_2_BLUE, a2b)

    try:
        while not stop_event.is_set():
            updateAll(True, False, False, True)
            time.sleep(60/soundPlayingBPM)       # time delay is set up to roughly time color swaps to every beat
            updateAll(False, True, True, False)
            time.sleep(60/soundPlayingBPM)

    finally:  # Gracefully cease use of LED-controlled GPIO pins when the stop event is received.
        updateAll(False, False, False, False)
        
# The current sound is loaded up and looped for the duration of the alarm.
def sound(stop_event):
    global currentSound
    currentSound.play(block=False, loop=True)

    try:
        while not stop_event.is_set():
            pass

    finally:  # The sound is stopped with the alarm.
        currentSound.stop()
        
# The *new* current sound is briefly teased when the user selects a new one on the rotary encoder.
def soundTease(stop_tease):
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

# Clears all stop events; creates new thread objects for each aspect of the alarm; starts the threads; waits before stopping them again
def triggerAlarm():
    stop_tease.set()
    stop_tease.clear()
    stop_event.clear()

    tLed = Thread(target=led, args=(stop_event,))
    tWings = Thread(target=wings, args=(stop_event,))
    tSound = Thread(target=sound, args=(stop_event,))

    tLed.start()
    tWings.start()
    tSound.start()

    time.sleep(10)

    stop_event.set()
    tLed.join()
    tWings.join()
    tSound.join()

# Rotary encoder shenanigans (much of the nitty-gritty is abstracted away with the RotaryEncoder class)
global count
count = 0
global previousEvent
previousEvent = 0

def switch_event(event):
    global count
    global previousEvent
    
    if event == RotaryEncoder.CLOCKWISE:
        
        if event == previousEvent or count >= 6:
            count += 1
            if count >= 4:
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

rswitch = RotaryEncoder(KNOB_PIN_A, KNOB_PIN_B, KNOB_BUTTON, switch_event)

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    GPIO.cleanup()
    print("Thanks for checking us out! Ten points please? ;)")
