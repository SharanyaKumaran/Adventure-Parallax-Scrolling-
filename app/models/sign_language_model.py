import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
import pickle
import os
from typing import List, Tuple, Optional
import logging

class SignLanguageRecognizer:
    """
    Sign Language Recognition system using MediaPipe for hand detection
    and a trained model for gesture classification
    """
    
    def __init__(self, model_path: Optional[str] = None, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
        self.current_prediction = ""
        self.prediction_history = []
        self.stable_prediction_count = 0
        self.required_stable_frames = 5
        
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # ASL alphabet labels (expandable)
        self.labels = [
            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
            'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
            'Hello', 'Thank you', 'Please', 'Sorry', 'Yes', 'No'
        ]
        
        # Load or create model
        self.model = self._load_or_create_model(model_path)
        
        logging.info("Sign Language Recognizer initialized successfully")
    
    def _load_or_create_model(self, model_path: Optional[str]) -> tf.keras.Model:
        """Load existing model or create a new one"""
        if model_path and os.path.exists(model_path):
            try:
                model = tf.keras.models.load_model(model_path)
                logging.info(f"Loaded existing model from {model_path}")
                return model
            except Exception as e:
                logging.warning(f"Failed to load model: {e}. Creating new model.")
        
        # Create a simple CNN model for demonstration
        model = self._create_model()
        logging.info("Created new model")
        return model
    
    def _create_model(self) -> tf.keras.Model:
        """Create a simple neural network model for gesture classification"""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(128, activation='relu', input_shape=(42,)),  # 21 landmarks * 2 coordinates
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(len(self.labels), activation='softmax')
        ])
        
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def extract_landmarks(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Extract hand landmarks from frame using MediaPipe"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        if results.multi_hand_landmarks:
            # Use the first detected hand
            hand_landmarks = results.multi_hand_landmarks[0]
            
            # Extract landmark coordinates
            landmarks = []
            for landmark in hand_landmarks.landmark:
                landmarks.extend([landmark.x, landmark.y])
            
            return np.array(landmarks)
        
        return None
    
    def predict_gesture(self, landmarks: np.ndarray) -> Tuple[str, float]:
        """Predict gesture from hand landmarks"""
        if landmarks is None:
            return "No hand detected", 0.0
        
        # Reshape for model input
        landmarks = landmarks.reshape(1, -1)
        
        # Make prediction
        prediction = self.model.predict(landmarks, verbose=0)
        confidence = np.max(prediction)
        
        if confidence > self.confidence_threshold:
            predicted_label = self.labels[np.argmax(prediction)]
            return predicted_label, confidence
        
        return "Uncertain", confidence
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, str, float]:
        """Process a single frame and return annotated frame with prediction"""
        # Extract landmarks
        landmarks = self.extract_landmarks(frame)
        
        # Make prediction
        gesture, confidence = self.predict_gesture(landmarks)
        
        # Stabilize predictions
        stable_gesture = self._stabilize_prediction(gesture)
        
        # Draw landmarks and prediction on frame
        annotated_frame = self._draw_annotations(frame, landmarks, stable_gesture, confidence)
        
        return annotated_frame, stable_gesture, confidence
    
    def _stabilize_prediction(self, current_gesture: str) -> str:
        """Stabilize predictions by requiring consistent results"""
        if current_gesture == self.current_prediction:
            self.stable_prediction_count += 1
        else:
            self.stable_prediction_count = 0
            self.current_prediction = current_gesture
        
        if self.stable_prediction_count >= self.required_stable_frames:
            return current_gesture
        
        return ""  # Return empty string if not stable
    
    def _draw_annotations(self, frame: np.ndarray, landmarks: Optional[np.ndarray], 
                         gesture: str, confidence: float) -> np.ndarray:
        """Draw hand landmarks and prediction text on frame"""
        annotated_frame = frame.copy()
        
        # Draw hand landmarks if detected
        if landmarks is not None:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_drawing.draw_landmarks(
                        annotated_frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
        
        # Draw prediction text
        if gesture and gesture != "No hand detected":
            cv2.putText(annotated_frame, f"Gesture: {gesture}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(annotated_frame, f"Confidence: {confidence:.2f}", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(annotated_frame, "No gesture detected", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        return annotated_frame
    
    def train_model(self, training_data: List[Tuple[np.ndarray, str]], 
                   validation_data: Optional[List[Tuple[np.ndarray, str]]] = None,
                   epochs: int = 50, batch_size: int = 32):
        """Train the model with provided data"""
        if not training_data:
            raise ValueError("Training data cannot be empty")
        
        # Prepare data
        X_train = np.array([data[0] for data in training_data])
        y_train = self._encode_labels([data[1] for data in training_data])
        
        validation_split = 0.2
        if validation_data:
            X_val = np.array([data[0] for data in validation_data])
            y_val = self._encode_labels([data[1] for data in validation_data])
            validation_split = None
        
        # Train model
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_val, y_val) if validation_data else None,
            validation_split=validation_split,
            verbose=1
        )
        
        return history
    
    def _encode_labels(self, labels: List[str]) -> np.ndarray:
        """Encode string labels to one-hot vectors"""
        encoded = np.zeros((len(labels), len(self.labels)))
        for i, label in enumerate(labels):
            if label in self.labels:
                encoded[i, self.labels.index(label)] = 1
        return encoded
    
    def save_model(self, path: str):
        """Save the trained model"""
        self.model.save(path)
        logging.info(f"Model saved to {path}")
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'hands'):
            self.hands.close()


class DataCollector:
    """Helper class for collecting training data"""
    
    def __init__(self, recognizer: SignLanguageRecognizer):
        self.recognizer = recognizer
        self.collected_data = []
    
    def collect_gesture_data(self, label: str, num_samples: int = 100) -> List[np.ndarray]:
        """Collect training data for a specific gesture"""
        cap = cv2.VideoCapture(0)
        collected_samples = []
        sample_count = 0
        
        print(f"Collecting data for gesture: {label}")
        print("Press SPACE to capture samples, ESC to finish")
        
        while sample_count < num_samples and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Extract landmarks
            landmarks = self.recognizer.extract_landmarks(frame)
            
            # Draw instructions
            cv2.putText(frame, f"Gesture: {label}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Samples: {sample_count}/{num_samples}", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "Press SPACE to capture", (10, 110), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow('Data Collection', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' ') and landmarks is not None:
                collected_samples.append(landmarks)
                sample_count += 1
                print(f"Captured sample {sample_count}")
            elif key == 27:  # ESC key
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        return collected_samples