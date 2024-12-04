# Import required libraries
from tkinter import *  # For creating the graphical user interface
from PIL import Image, ImageTk  # For handling images
import cv2 as cv  # For computer vision and video capture
import face_recognition  # For facial recognition capabilities
import dlib  # For facial landmark detection
import pandas as pd  # For data manipulation and analysis
import numpy as np  # For numerical operations
from datetime import datetime  # For handling dates and times
import os  # For file and directory operations
import winsound  # For playing alert sounds
import subprocess  # For running external programs
from tkinter import ttk, messagebox  # For modern UI widgets and message boxes
from ttkthemes import ThemedStyle  # For applying modern themes
import keyboard  # For keyboard input handling
from tkinter.font import Font  # For custom fonts
import time  # For time-related functions
import threading  # For running multiple tasks simultaneously
import win32api  # For Windows-specific functionality
import win32con  # For Windows constants
import win32gui  # For Windows GUI operations
import pyttsx3 # For text-to-speech
from gtts import gTTS # For Google text-to-speech
import playsound # For playing audio files

# Initialize text-to-speech engines
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id) # Set male voice
engine.setProperty('rate', 150) # Set speaking rate

def speak_pyttsx3(text):
    engine.say(text)
    engine.runAndWait()

def speak_gtts(text):
    tts = gTTS(text=text, lang='en')
    tts.save("temp.mp3")
    playsound.playsound("temp.mp3")
    os.remove("temp.mp3")

# Global variable to store camera object
cam = None

# Class to handle custom mouse cursor appearance
class CustomCursor:
    def __init__(self):
        # Load Windows system cursors
        self.default_cursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)  # Normal arrow cursor
        self.hand_cursor = win32gui.LoadCursor(0, win32con.IDC_HAND)  # Hand pointer cursor
        
    # Method to change cursor to hand pointer
    def set_hand_cursor(self):
        win32gui.SetCursor(self.hand_cursor)
        
    # Method to change cursor back to default arrow
    def set_default_cursor(self):
        win32gui.SetCursor(self.default_cursor)

# Create global cursor object
cursor = CustomCursor()

# Function to calculate how attentive a person is based on head position
def calculate_attention_score(yaw, pitch):
    # Maximum allowed head rotation angles
    MAX_YAW_THRESHOLD = 0.8   # Left-right head rotation limit
    MAX_PITCH_THRESHOLD = 0.8  # Up-down head rotation limit
    
    # Calculate scores based on head rotation
    # Score decreases as head turns away from center
    yaw_score = max(0, 1 - abs(yaw[0]) / MAX_YAW_THRESHOLD)
    pitch_score = max(0, 1 - abs(pitch[0]) / MAX_PITCH_THRESHOLD)
    
    # Calculate final score:
    # - Base score of 0.3 (30%) just for being present
    # - Additional 70% based on head position (60% weight to left-right, 40% to up-down)
    base_score = 0.3
    weighted_score = 0.7 * ((0.6 * yaw_score + 0.4 * pitch_score))
    
    # Return final score capped at 100%
    return min(1.0, base_score + weighted_score)

# Function to estimate head position in 3D space
def get_head_pose(landmarks):
    # Convert facial landmarks to 3D points
    image_points = np.array([
        landmarks[30],  # Nose tip
        landmarks[8],   # Chin
        landmarks[36],  # Left eye corner
        landmarks[45],  # Right eye corner
        landmarks[48],  # Left mouth corner
        landmarks[54]   # Right mouth corner
    ], dtype="double")
    
    # 3D model points corresponding to facial landmarks
    model_points = np.array([
        (0.0, 0.0, 0.0),         # Nose tip
        (0.0, -330.0, -65.0),    # Chin
        (-165.0, 170.0, -135.0), # Left eye corner
        (165.0, 170.0, -135.0),  # Right eye corner
        (-150.0, -150.0, -125.0),# Left mouth corner
        (150.0, -150.0, -125.0)  # Right mouth corner
    ])
    
    # Camera matrix for perspective projection
    camera_matrix = np.array([
        [320, 0, 320],
        [0, 320, 240],
        [0, 0, 1]], dtype="double")
    
    # Calculate head rotation and position
    success, rotation_vector, translation_vector = cv.solvePnP(
        model_points, image_points, camera_matrix, np.zeros((4,1))
    )
    return rotation_vector, translation_vector

# Main function to start the attention monitoring system
def start_program():
    global cam
    
    # Welcome message using text-to-speech
    speak_pyttsx3("Starting AI Enhanced Attention Monitoring System")
    
    # Try to load the facial landmark predictor model
    try:
        p = "D:\\workspace\\python codes\\shape_predictor_68_face_landmarks.dat"
        landmark_predictor = dlib.shape_predictor(p)
    except:
        speak_gtts("Error loading facial landmark predictor")
        messagebox.showerror("Error", "Could not load facial landmark predictor")
        return
        
    # Create directory for storing screenshots if it doesn't exist
    screenshots_dir = "C:\\Users\\Acer\\OneDrive\\Desktop\\attention_score\\screenshots_avg_attention-score"
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
        
    # Load the reference face image for comparison
    try:
        known_image = face_recognition.load_image_file(r"D:\workspace\python codes\my photos\IMG-20241025-WA0013.jpg")
        known_faces = face_recognition.face_encodings(known_image)[0]
    except:
        speak_gtts("Error loading reference face image")
        messagebox.showerror("Error", "Could not load reference face image")
        return
    
    # Initialize data storage
    columns = ['Name', 'Date', 'Time', 'Screenshot', 'Attentive', 'Attention Score']
    df = pd.DataFrame(columns=columns)  # For storing session data
    attention_scores = []  # For tracking attention scores
    
    # Initialize camera
    try:
        cam = cv.VideoCapture(0)  # Open default camera
        if not cam.isOpened():
            raise Exception("Camera not accessible")
    except Exception as e:
        speak_gtts("Camera error occurred")
        messagebox.showerror("Camera Error", str(e))
        return
        
    # Create fullscreen window for display
    window_name = "AI Attention Monitoring System"
    cv.namedWindow(window_name, cv.WINDOW_NORMAL)
    cv.setWindowProperty(window_name, cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
    
    # Get screen dimensions
    screen_width = cv.getWindowImageRect(window_name)[2]
    screen_height = cv.getWindowImageRect(window_name)[3]
    
    # Flag to control program termination
    terminate = False
    
    # Function to handle mouse clicks on terminate button
    def on_terminate(event, x, y, flags, param):
        nonlocal terminate
        button_width = 300  # Button dimensions
        button_height = 70
        button_x = (screen_width - button_width) // 2  # Center button horizontally
        button_y = screen_height - 100  # Position near bottom
        
        # Change cursor when hovering over button
        if (button_x <= x <= button_x + button_width and 
            button_y <= y <= button_y + button_height):
            cursor.set_hand_cursor()
            if event == cv.EVENT_LBUTTONDOWN:  # If clicked
                terminate = True
                speak_pyttsx3("Ending monitoring session")
        else:
            cursor.set_default_cursor()
            
    # Set mouse callback function
    cv.setMouseCallback(window_name, on_terminate)
    
    # Record start time for session duration
    start_time = datetime.now()
    frame_count = 0

    # Function to create gradient background
    def create_gradient(height, width):
        gradient = np.zeros((height, width, 3), dtype=np.uint8)
        for i in range(height):
            # Create dark gradient from top to bottom
            gradient[i] = [30 + (i/height)*10, 30 + (i/height)*10, 40 + (i/height)*10]
        return gradient

    # Main program loop
    try:
        while not terminate:
            frame_count += 1
            ret, frame = cam.read()  # Read frame from camera
            
            # Check if frame was captured successfully
            if not ret:
                speak_gtts("Camera feed interrupted")
                messagebox.showerror("Error", "Camera feed interrupted")
                break

            # Process every other frame to improve performance
            if frame_count % 2 == 0:
                continue

            # Create gradient background for UI
            canvas = create_gradient(screen_height, screen_width)
            
            # Resize camera frame while maintaining aspect ratio
            frame_height = int(screen_height * 0.7)
            frame_width = int(frame_height * frame.shape[1]/frame.shape[0])
            frame = cv.resize(frame, (frame_width, frame_height))
            
            # Position frame on left side of screen
            frame_y = (screen_height - frame.shape[0]) // 2
            frame_x = 50
            
            # Add decorative border around frame
            cv.rectangle(canvas, 
                        (frame_x-15, frame_y-15), 
                        (frame_x + frame.shape[1]+15, frame_y + frame.shape[0]+15), 
                        (70, 70, 80), -1)
            cv.rectangle(canvas, 
                        (frame_x-12, frame_y-12), 
                        (frame_x + frame.shape[1]+12, frame_y + frame.shape[0]+12), 
                        (55, 55, 65), 2)
            
            # Add inner shadow effect
            cv.rectangle(canvas,
                        (frame_x-5, frame_y-5),
                        (frame_x + frame.shape[1]+5, frame_y + frame.shape[0]+5),
                        (40, 40, 50), 1)
            
            # Place camera frame on canvas
            canvas[frame_y:frame_y+frame.shape[0], frame_x:frame_x+frame.shape[1]] = frame
            
            # Create info panel on right side
            info_panel_start = frame_x + frame.shape[1] + 40
            panel_width = screen_width - info_panel_start - 50
            
            # Add glass effect background for info panel
            cv.rectangle(canvas, 
                        (info_panel_start-5, frame_y-15), 
                        (info_panel_start + panel_width+5, frame_y + frame.shape[0]+15), 
                        (60, 60, 70), -1)
            cv.rectangle(canvas,
                        (info_panel_start-2, frame_y-12),
                        (info_panel_start + panel_width+2, frame_y + frame.shape[0]+12),
                        (50, 50, 60), 2)
            
            # Create gradient header
            header_height = 90
            for i in range(header_height):
                alpha = i / header_height
                color = (int(40 + alpha*20), int(40 + alpha*20), int(50 + alpha*20))
                cv.line(canvas, (0, i), (screen_width, i), color, 1)
                
            # Add title text with enhanced 3D effect and color-changing glow
            title_text = "AI Enhanced Attention Monitoring System"
            base_x, base_y = 50, header_height//2+10
            
            # Calculate dynamic colors for rainbow glow effect
            t = time.time()
            hue = (np.sin(t) + 1) / 2  # Oscillating value between 0-1
            
            # Convert HSV to BGR for rainbow effect
            color = tuple(reversed(cv.cvtColor(np.uint8([[[hue*180, 255, 255]]]), 
                                             cv.COLOR_HSV2BGR)[0][0].tolist()))
            
            # Enhanced 3D shadow layers with depth gradient
            shadow_depth = 8
            for offset in range(shadow_depth, 0, -1):
                shadow_intensity = offset / shadow_depth
                shadow_color = tuple(int(c * shadow_intensity * 0.3) for c in color)
                cv.putText(canvas, title_text,
                          (base_x + offset, base_y + offset),
                          cv.FONT_HERSHEY_DUPLEX, 1.3, shadow_color, 2)
            
            # Add bright edge highlight for enhanced 3D effect
            highlight_color = tuple(min(255, int(c * 1.5)) for c in color)
            cv.putText(canvas, title_text,
                      (base_x-1, base_y-1),
                      cv.FONT_HERSHEY_DUPLEX, 1.3, highlight_color, 2)
            
            # Main text with dynamic glow
            glow_intensity = abs(np.sin(t * 2))
            glow_color = tuple(int(c * (0.7 + 0.3 * glow_intensity)) for c in color)
            cv.putText(canvas, title_text,
                      (base_x, base_y),
                      cv.FONT_HERSHEY_DUPLEX, 1.3, glow_color, 2)
            
            # Add subtle outer glow
            blur_size = 3
            glow_layer = np.zeros_like(canvas)
            cv.putText(glow_layer, title_text,
                      (base_x, base_y),
                      cv.FONT_HERSHEY_DUPLEX, 1.3, glow_color, 4)
            glow_layer = cv.GaussianBlur(glow_layer, (blur_size, blur_size), 0)
            canvas = cv.addWeighted(canvas, 1, glow_layer, 0.3, 0)

            # Create terminate button with glowing effect
            button_width = 300
            button_height = 70
            button_x = (screen_width - button_width) // 2
            button_y = screen_height - 100
            
            # Button glow effect
            cv.rectangle(canvas, 
                        (button_x-5, button_y-5), 
                        (button_x + button_width+5, button_y + button_height+5), 
                        (220, 60, 60), -1)
            
            # Button gradient fill
            for i in range(button_height):
                alpha = i / button_height
                color = (int(200 - alpha*40), int(50 - alpha*10), int(50 - alpha*10))
                cv.line(canvas, 
                       (button_x, button_y+i), 
                       (button_x + button_width, button_y+i), 
                       color, 1)
            
            # Button border
            cv.rectangle(canvas,
                        (button_x, button_y),
                        (button_x + button_width, button_y + button_height),
                        (240, 70, 70), 2)
            
            # Add button text with shadow effect
            text = "END SESSION"
            text_size = cv.getTextSize(text, cv.FONT_HERSHEY_DUPLEX, 1.2, 2)[0]
            text_x = button_x + (button_width - text_size[0]) // 2
            text_y = button_y + (button_height + text_size[1]) // 2
            
            cv.putText(canvas, text, (text_x+2, text_y+2),
                      cv.FONT_HERSHEY_DUPLEX, 1.2, (100, 20, 20), 2)
            cv.putText(canvas, text, (text_x, text_y),
                      cv.FONT_HERSHEY_DUPLEX, 1.2, (255, 255, 255), 2)

            # Display current time and session info
            current_time = datetime.now()
            elapsed_time = (current_time - start_time).seconds
            
            y_offset = frame_y + 50
            spacing = 80
            
            # Show current time
            cv.putText(canvas, "CURRENT TIME", 
                      (info_panel_start+20, y_offset), 
                      cv.FONT_HERSHEY_DUPLEX, 0.8, (0, 200, 255), 1)
            time_text = current_time.strftime("%H:%M:%S")
            cv.putText(canvas, time_text, 
                      (info_panel_start+20, y_offset+35), 
                      cv.FONT_HERSHEY_DUPLEX, 1.2, (255, 255, 255), 2)
            
            # Show session duration
            cv.putText(canvas, "SESSION DURATION", 
                      (info_panel_start+20, y_offset+spacing*2), 
                      cv.FONT_HERSHEY_DUPLEX, 0.8, (0, 200, 255), 1)
            duration_text = f"{elapsed_time//3600:02d}:{(elapsed_time%3600)//60:02d}:{elapsed_time%60:02d}"
            cv.putText(canvas, duration_text, 
                      (info_panel_start+20, y_offset+spacing*2+35), 
                      cv.FONT_HERSHEY_DUPLEX, 1.2, (255, 255, 255), 2)
            
            # Show average attention score with circular progress indicator
            avg_score = np.mean(attention_scores) if attention_scores else 0.0
            cv.putText(canvas, "AVERAGE ATTENTION SCORE", 
                      (info_panel_start+20, y_offset+spacing*4), 
                      cv.FONT_HERSHEY_DUPLEX, 0.8, (0, 200, 255), 1)
            
            # Draw circular progress indicator
            center_x = info_panel_start + 100
            center_y = y_offset+spacing*4+60
            radius = 30
            
            cv.circle(canvas, (center_x, center_y), radius, (60, 60, 70), -1)
            cv.circle(canvas, (center_x, center_y), radius-2, (50, 50, 60), 2)
            
            # Draw progress arc based on score
            angle = 360 * avg_score
            start_angle = -90
            end_angle = start_angle + angle
            
            if angle > 0:
                cv.ellipse(canvas, (center_x, center_y), (radius-2, radius-2),
                          0, start_angle, end_angle, (0, 200, 255), 3)
            
            # Show score percentage
            score_text = f"{int(avg_score*100)}%"
            text_size = cv.getTextSize(score_text, cv.FONT_HERSHEY_DUPLEX, 0.7, 1)[0]
            cv.putText(canvas, score_text,
                      (center_x - text_size[0]//2, center_y + text_size[1]//2),
                      cv.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 1)
            
            # Process face detection
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            face_locations = face_recognition.face_locations(frame)
            
            # If faces are detected
            if face_locations:
                face_encodings = face_recognition.face_encodings(frame, face_locations)

                # Process each detected face
                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    # Compare with known face
                    distance = face_recognition.face_distance([known_faces], face_encoding)[0]

                    # If face matches known face (distance < 0.7)
                    if distance < 0.7:
                        now = datetime.now()
                        name = 'subham_sahoo_'
                        
                        # Get facial landmarks
                        face_landmarks = landmark_predictor(gray, dlib.rectangle(left, top, right, bottom))
                        landmarks = [(p.x, p.y) for p in face_landmarks.parts()]
                        
                        # Draw landmarks on face
                        for (x, y) in landmarks:
                            cv.circle(frame, (x, y), 1, (0, 255, 255), -1)

                        # Calculate head pose and attention score
                        rotation_vector, translation_vector = get_head_pose(landmarks)
                        yaw, pitch, roll = rotation_vector
                        
                        attention_score = calculate_attention_score(yaw, pitch)
                        attention_scores.append(attention_score)
                        attentive = 'Yes' if attention_score >= 0.5 else 'No'

                        # Display attention status
                        status_color = (0, 255, 0) if attentive == 'Yes' else (0, 0, 255)
                        cv.putText(canvas, "CURRENT STATUS", 
                                 (info_panel_start+20, y_offset+spacing*6), 
                                 cv.FONT_HERSHEY_DUPLEX, 0.8, (0, 200, 255), 1)
                        status_text = 'Attentive' if attentive == 'Yes' else 'Not Attentive'
                        cv.putText(canvas, status_text, 
                                 (info_panel_start+20, y_offset+spacing*6+35), 
                                 cv.FONT_HERSHEY_DUPLEX, 1.2, status_color, 2)
                        
                        # Draw attention score progress bar
                        bar_y = y_offset+spacing*7
                        bar_height = 20
                        
                        # Progress bar background
                        cv.rectangle(canvas, 
                                   (info_panel_start+20-2, bar_y-2), 
                                   (info_panel_start+222, bar_y+bar_height+2), 
                                   (70, 70, 80), -1)
                        cv.rectangle(canvas, 
                                   (info_panel_start+20, bar_y), 
                                   (info_panel_start+220, bar_y+bar_height), 
                                   (50, 50, 60), -1)
                        
                        # Progress bar fill
                        score_width = int(200 * attention_score)
                        if score_width > 0:
                            cv.rectangle(canvas, 
                                       (info_panel_start+20, bar_y), 
                                       (info_panel_start+20+score_width, bar_y+bar_height), 
                                       status_color, -1)
                            
                            # Add gradient effect to progress bar
                            alpha = np.linspace(0.7, 0.3, bar_height)
                            for i in range(bar_height):
                                cv.line(canvas,
                                       (info_panel_start+20, bar_y+i),
                                       (info_panel_start+20+score_width, bar_y+i),
                                       tuple(int(c*alpha[i]) for c in status_color), 1)
                        
                        # Show score percentage
                        cv.putText(canvas, f"{int(attention_score*100)}%", 
                                 (info_panel_start+230, bar_y+15), 
                                 cv.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 1)
                        
                        # Play alert sound and voice warning if not attentive
                        if attentive == 'No':
                            winsound.Beep(1000, 500)
                            speak_pyttsx3("Please pay attention")
                        
                        # Save screenshot and data
                        screenshot_filename = f"{screenshots_dir}/{name}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
                        cv.imwrite(screenshot_filename, frame)
                        new_entry = pd.DataFrame({
                            'Name': [name],
                            'Date': [now.strftime("%Y-%m-%d")],
                            'Time': [now.strftime("%H:%M:%S")],
                            'Screenshot': [screenshot_filename],
                            'Attentive': [attentive],
                            'Attention Score': [attention_score]
                        })
                        df = pd.concat([df, new_entry], ignore_index=True)

                        # Draw face rectangle with glow effect
                        cv.rectangle(frame, (left-2, top-2), (right+2, bottom+2), 
                                   tuple(int(c*0.7) for c in status_color), 3)
                        cv.rectangle(frame, (left, top), (right, bottom), 
                                   status_color, 2)
                        
                        # Add name label with modern styling
                        label_width = 150
                        label_height = 30
                        label_bg_pts = np.array([
                            [left-5, top-label_height-5],
                            [left-5, top],
                            [left+label_width, top],
                            [left+label_width, top-label_height-5]
                        ])
                        cv.fillPoly(frame, [label_bg_pts], (40, 40, 40))
                        cv.polylines(frame, [label_bg_pts], True, (60, 60, 60), 1)
                        
                        # Add name text with shadow
                        cv.putText(frame, name, (left+2, top - 12), 
                                 cv.FONT_HERSHEY_DUPLEX, 0.6, (0, 0, 0), 1)
                        cv.putText(frame, name, (left, top - 10), 
                                 cv.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
                        
                        # Update frame in canvas
                        canvas[frame_y:frame_y+frame.shape[0], 
                               frame_x:frame_x+frame.shape[1]] = frame

            # Display the final canvas
            cv.imshow(window_name, canvas)
            if cv.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        speak_gtts("An error occurred")
        messagebox.showerror("Error", f"An error occurred: {e}")

    finally:
        # Save final results
        if not df.empty:
            average_attention_score = np.mean(attention_scores) if attention_scores else 0.0
            print(f"Average Attention Score: {average_attention_score:.2f}")
            speak_pyttsx3(f"Session complete. Average attention score was {int(average_attention_score*100)} percent")

            # Add average score to dataframe
            avg_entry = pd.DataFrame({
                'Name': ['Average'],
                'Date': [''],
                'Time': [''],
                'Screenshot': [''],
                'Attentive': [''],
                'Attention Score': [average_attention_score]
            })
            df = pd.concat([df, avg_entry], ignore_index=True)

            # Save data to Excel and CSV
            try:
                df.to_excel('C:\\Users\\Acer\\OneDrive\\Desktop\\attention_score\\attendance_with_attention_and_average.xlsx', 
                           index=False)
                df.groupby('Name')['Attention Score'].mean().reset_index().to_csv(
                    'attendance_summary.csv', index=False)
                speak_pyttsx3("Data saved successfully")
            except Exception as e:
                speak_gtts("Could not save data")
                messagebox.showerror("Error", f"Could not save data: {e}")
            
        # Clean up
        if cam is not None:
            cam.release()
        cv.destroyAllWindows()

# Function to open Excel file with results
def openxcel():
    excel_path = r"C:\Users\Acer\OneDrive\Desktop\attention_score\attendance_with_attention_and_average.xlsx"
    try:
        os.startfile(excel_path)
        speak_pyttsx3("Opening Excel report")
    except Exception as e:
        speak_gtts("Error opening Excel file")
        messagebox.showerror("Error", f"Error opening Excel file: {e}")
        try:
            subprocess.Popen(['start', 'excel', excel_path], shell=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Excel file: {e}")

# Function to open screenshots folder
def open_screenshots():
    screenshots_dir = "C:\\Users\\Acer\\OneDrive\\Desktop\\attention_score\\screenshots_avg_attention-score"
    if os.path.exists(screenshots_dir):
        subprocess.Popen(f'explorer "{screenshots_dir}"')
        speak_pyttsx3("Opening screenshots folder")
    else:
        speak_gtts("Screenshots directory not found")
        messagebox.showerror("Error", "Screenshots directory not found")

# Main application class
class face_recognition_system:
    def __init__(self, root):
        self.root = root
        self.root.state('zoomed')  # Maximize window
        self.root.title("AI Enhanced Face Recognition System")
        
        # Welcome message
        speak_pyttsx3("Welcome to AI Enhanced Face Recognition System")
        
        # Apply modern dark theme
        style = ThemedStyle(root)
        style.set_theme("equilux")
        
        # Define colors
        bg_color = "#1E1E1E"  # Dark background
        accent_color = "#00A8E8"  # Blue accent
        self.root.configure(bg=bg_color)
        
        # Define custom fonts
        title_font = Font(family="Helvetica", size=36, weight="bold")
        subtitle_font = Font(family="Helvetica", size=16)
        button_font = Font(family="Helvetica", size=13, weight="bold")
        info_font = Font(family="Helvetica", size=12)
        
        # Create main window layout
        gradient_frame = Frame(root, bg=bg_color)
        gradient_frame.place(relwidth=1, relheight=1)
        
        main_frame = Frame(root, bg=bg_color)
        main_frame.place(relx=0.5, rely=0.5, anchor=CENTER)
        
        # Add title section with bold button effect
        title_frame = Frame(main_frame, bg=bg_color)
        title_frame.pack(pady=(0, 20))
        
        # Create raised button effect for title
        title_button = Frame(title_frame, relief=RAISED, bd=3, bg=accent_color)
        title_button.pack(padx=20, pady=10)
        
        title = Label(title_button, 
                     text="AI ENHANCED FACIAL RECOGNITION",
                     font=title_font,
                     fg="white",
                     bg=accent_color,
                     padx=20,
                     pady=10)
        title.pack()
        
        subtitle = Label(title_frame,
                        text="Advanced Attention Monitoring & Analysis",
                        font=subtitle_font,
                        fg="#888888",
                        bg=bg_color)
        subtitle.pack(pady=(10,0))

        # Add system information
        details_frame = Frame(main_frame, bg=bg_color)
        details_frame.pack(pady=(20,30))

        details_text = """
        System Features:
        • Real-time facial recognition and tracking
        • Advanced attention monitoring using head pose estimation
        • Continuous attention scoring and analysis
        • Automated screenshot capture and record keeping
        • Excel-based reporting and data visualization
        
        Developer: Subham Sahoo
        Version: 1.0.0
        """
        
        details_label = Label(details_frame,
                            text=details_text,
                            font=info_font,
                            fg="#AAAAAA",
                            bg=bg_color,
                            justify=LEFT)
        details_label.pack(padx=20)
        
        # Create button container
        button_frame = Frame(main_frame, bg=bg_color, padx=30, pady=30)
        button_frame.pack(fill=X, pady=20)
        
        # Function to create modern styled buttons
        def create_button(parent, text, command, color):
            btn_frame = Frame(parent, bg=color, relief=RAISED, bd=2)  # Add raised effect to frame
            btn = Label(btn_frame, 
                text=text,
                font=button_font,
                bg=color,
                fg='white',
                padx=30,
                pady=15,
                relief=RAISED,  # Add raised effect to button
                bd=3           # Subtle border width
            )

            btn.pack(fill=BOTH, expand=True)
            
            # Add hover effects
            def on_enter(e):
                btn_frame.config(bg=accent_color)
                btn.config(bg=accent_color)
                
            def on_leave(e):
                btn_frame.config(bg=color)
                btn.config(bg=color)
                
            def on_click(e):
                command()
                
            btn.bind('<Enter>', on_enter)
            btn.bind('<Leave>', on_leave)
            btn.bind('<Button-1>', on_click)
            
            return btn_frame
        
        # Create button grid
        button_grid = Frame(button_frame, bg=bg_color)
        button_grid.pack(expand=True)
        
        # Add main function buttons
        start_btn = create_button(button_grid, "Start Recognition", start_program, "#A020F0")
        start_btn.grid(row=0, column=0, padx=15, pady=15)
        
        excel_btn = create_button(button_grid,"View Records", openxcel, "#F0A020")
        excel_btn.grid(row=0, column=1, padx=15, pady=15)
        
        screenshots_btn = create_button(button_grid, "View Screenshots", open_screenshots, "#20F0A0")
        screenshots_btn.grid(row=0, column=2, padx=15, pady=15)
        
        # Add exit button
        exit_frame = Frame(root, bg="#FF4444")
        exit_frame.pack(side=BOTTOM, pady=30)
        
        exit_btn = Label(exit_frame,
                        text="Exit Application",
                        font=button_font,
                        bg="#FF4444",
                        fg='white',
                        padx=25,
                        pady=10)
        exit_btn.pack()
        
        def on_exit_enter(e):
            exit_frame.config(bg="#FF1111")
            exit_btn.config(bg="#FF1111")
            
        def on_exit_leave(e):
            exit_frame.config(bg="#FF4444")
            exit_btn.config(bg="#FF4444")
            
        def on_exit_click(e):
            root.destroy()
            
        exit_btn.bind('<Enter>', on_exit_enter)
        exit_btn.bind('<Leave>', on_exit_leave)
        exit_btn.bind('<Button-1>', on_exit_click)

if __name__ == "__main__":
    root = Tk()
    app = face_recognition_system(root)
    root.mainloop()
