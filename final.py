import cv2
import mediapipe as mp
import pyautogui
import serial
import time

# Initialize Arduino Serial Communication
arduino = serial.Serial('COM4', 9600)  # Adjust COM port as needed
time.sleep(2)  # Wait for Arduino to initialize

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Gesture recognition functions
def is_palm_gesture(landmarks):
    """Check if the palm is open (all fingers extended)"""
    finger_tips = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky tips
    finger_pips = [6, 10, 14, 18]  # Second joints
    thumb_tip = landmarks[4]
    
    # All fingers should be extended (tips above pips)
    fingers_extended = all(landmarks[tip].y < landmarks[pip].y for tip, pip in zip(finger_tips, finger_pips))
    
    # Thumb should be extended to the side
    thumb_extended = landmarks[4].x > landmarks[3].x
    
    # Fingers should be relatively straight and separated
    return fingers_extended and thumb_extended

def is_left_thumb(landmarks):
    """Detect thumb pointing left for previous track"""
    thumb_tip = landmarks[4]
    thumb_ip = landmarks[3]
    thumb_mcp = landmarks[2]
    
    # Check if thumb is extended to the left (previous track)
    is_extended_left = thumb_tip.x < thumb_ip.x < thumb_mcp.x
    # Other fingers must be curled
    fingers_curled = all(landmarks[tip].y > landmarks[pip].y 
                        for tip, pip in zip([8, 12, 16, 20], [6, 10, 14, 18]))
    
    return is_extended_left and fingers_curled

def is_right_thumb(landmarks):
    """Detect thumb pointing right for next track"""
    thumb_tip = landmarks[4]
    thumb_ip = landmarks[3]
    thumb_mcp = landmarks[2]
    
    # Check if thumb is extended to the right (next track)
    is_extended_right = thumb_tip.x > thumb_ip.x > thumb_mcp.x
    # Other fingers must be curled
    fingers_curled = all(landmarks[tip].y > landmarks[pip].y 
                        for tip, pip in zip([8, 12, 16, 20], [6, 10, 14, 18]))
    
    return is_extended_right and fingers_curled

def fingers_curled(landmarks):
    return all(landmarks[tip].y > landmarks[pip].y 
              for tip, pip in zip([8, 12, 16, 20], [6, 10, 14, 18]))
    
    return is_extended_right and fingers_curled

def send_media_command(command):
    # First handle system media control
    if command == "playpause":
        pyautogui.press("playpause")
        send_command_to_arduino('P')  # Send 'P' to Arduino
        print("Playback initiated/paused")
    elif command == "nexttrack":
        pyautogui.press("nexttrack")
        send_command_to_arduino('N')  # Send 'N' to Arduino
        print("Next Track")
    elif command == "prevtrack":
        pyautogui.press("prevtrack")
        send_command_to_arduino('B')  # Send 'B' to Arduino
        print("Previous Track")

def send_command_to_arduino(command):
    try:
        arduino.write(command.encode())
        time.sleep(0.1)  # Small delay to ensure command is processed
    except Exception as e:
        print(f"Error sending command to Arduino: {e}")

# Initialize video capture
cap = cv2.VideoCapture(0)
last_gesture = None  # To prevent duplicate commands from gestures
gesture_timeout = 1   # Minimum time between consecutive gesture commands in seconds
last_command_time = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame.")
        break

    frame = cv2.flip(frame, 1)  # Mirror the frame for better usability
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    current_time = time.time()

    # Handle gesture recognition
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Check for open palm gesture
            if is_palm_gesture(hand_landmarks.landmark):
                gesture = "playpause"
                print("Gesture recognized: playpause")
            # Check for next track gesture (thumb pointing right for next track)
            elif is_right_thumb(hand_landmarks.landmark):
                gesture = "nexttrack"
                print("Gesture recognized: nexttrack")
            # Check for previous track gesture (thumb pointing left for previous track)
            elif is_left_thumb(hand_landmarks.landmark):
                gesture = "prevtrack"
                print("Gesture recognized: prevtrack")
            else:
                gesture = None

            # Execute actions based on gesture
            if gesture and gesture != last_gesture and (current_time - last_command_time > gesture_timeout):
                send_media_command(gesture)
                send_command_to_arduino(gesture[0].upper())  # Send first letter of gesture to Arduino
                last_gesture = gesture
                last_command_time = current_time
    else:
        last_gesture = None  # Reset if no hand is detected

    # Display the video feed
    frame = cv2.resize(frame, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
    cv2.imshow("Gesture Control", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to exit
        break

cap.release()
cv2.destroyAllWindows()
arduino.close()
