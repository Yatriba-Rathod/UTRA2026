import cv2
import numpy as np

def get_largest_contour(mask, min_area=500):
    """
    Helper to find the largest contour in a mask.
    Returns None if no contour usually large enough is found.
    """
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < min_area:
        return None
    return largest

# Initialize Webcam
cap = cv2.VideoCapture(1) # Change to 0 if 1 doesn't work

if not cap.isOpened():
    print("Error: Could not access the camera.")
    exit()

# Define Font for text
font = cv2.FONT_HERSHEY_SIMPLEX

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 1. Image Preprocessing
    # Blur to remove noise (crucial for clean masks)
    blurred = cv2.GaussianBlur(frame, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # 2. Define Color Ranges (HSV)
    # NOTE: You may need to tune these values for your specific lighting!
    
    # Green Mask
    mask_green = cv2.inRange(hsv, np.array([40, 70, 70]), np.array([80, 255, 255]))
    
    # Blue Mask
    mask_blue = cv2.inRange(hsv, np.array([90, 70, 70]), np.array([130, 255, 255]))
    
    # Red Mask (wrapping around 180)
    mask_red1 = cv2.inRange(hsv, np.array([0, 70, 70]), np.array([10, 255, 255]))
    mask_red2 = cv2.inRange(hsv, np.array([170, 70, 70]), np.array([180, 255, 255]))
    mask_red = mask_red1 + mask_red2

    # Black Mask (Ball) - Low Value (brightness)
    mask_black = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 60]))

    # 3. Find Region Contours
    # We find the largest contour for each color to ignore small background noise
    cnt_green = get_largest_contour(mask_green)
    cnt_red = get_largest_contour(mask_red)
    cnt_blue = get_largest_contour(mask_blue)
    
    # Draw region contours for visual feedback
    if cnt_green is not None: cv2.drawContours(frame, [cnt_green], -1, (0, 255, 0), 2)
    if cnt_red is not None:   cv2.drawContours(frame, [cnt_red], -1, (0, 0, 255), 2)
    if cnt_blue is not None:  cv2.drawContours(frame, [cnt_blue], -1, (255, 0, 0), 2)

    # 4. Find the Ball and Check Location
    ball_contour = get_largest_contour(mask_black, min_area=300)
    current_zone = "NONE"
    
    if ball_contour is not None:
        # Get the bounding box of the ball to check for square shape
        peri = cv2.arcLength(ball_contour, True)
        approx = cv2.approxPolyDP(ball_contour, 0.04 * peri, True)
        
        # Check if it has 4 corners (Square/Rectangle)
        if len(approx) == 4:
            # Calculate Center (Moments)
            M = cv2.moments(ball_contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                center_point = (cx, cy)

                # Draw the ball
                cv2.drawContours(frame, [ball_contour], -1, (255, 255, 255), 2)
                cv2.circle(frame, center_point, 5, (255, 255, 255), -1)

                # --- HIT DETECTION LOGIC ---
                # We use pointPolygonTest to see if the center is inside the contours.
                # The measure > 0 means inside, < 0 means outside.
                # We check Inner -> Outer (Green -> Red -> Blue)
                
                is_in_green = False
                is_in_red = False
                is_in_blue = False

                if cnt_green is not None:
                    if cv2.pointPolygonTest(cnt_green, center_point, False) >= 0:
                        is_in_green = True
                
                if cnt_red is not None:
                    if cv2.pointPolygonTest(cnt_red, center_point, False) >= 0:
                        is_in_red = True

                if cnt_blue is not None:
                    if cv2.pointPolygonTest(cnt_blue, center_point, False) >= 0:
                        is_in_blue = True

                # Determine Zone Priority
                if is_in_green:
                    current_zone = "GREEN"
                    color_disp = (0, 255, 0)
                elif is_in_red:
                    current_zone = "RED"
                    color_disp = (0, 0, 255)
                elif is_in_blue:
                    current_zone = "BLUE"
                    color_disp = (255, 0, 0)
                else:
                    current_zone = "OUTSIDE"
                    color_disp = (255, 255, 255)
                
                # Display Text on Screen
                cv2.putText(frame, f"ZONE: {current_zone}", (cx - 40, cy - 20), font, 0.8, color_disp, 2)
                print(f"Ball Center: {center_point} | Zone: {current_zone}")

    # Display status in top left corner
    cv2.rectangle(frame, (0,0), (200, 50), (0,0,0), -1)
    cv2.putText(frame, f"Hit: {current_zone}", (10, 35), font, 1, (255, 255, 255), 2)

    cv2.imshow('Biathlon Referee', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()