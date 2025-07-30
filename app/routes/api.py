from flask import Blueprint, request, jsonify, Response, current_app
from flask_login import login_required, current_user
import cv2
import base64
import numpy as np
import json
import threading
import time
from app.models.sign_language_model import SignLanguageRecognizer
from app.models.tts_service import TTSService, GestureToSpeechManager
from app.models.user import User, UserSession, GestureLog
from app import db

api = Blueprint('api', __name__)

# Global instances
recognizer = None
tts_service = None
gesture_manager = None

def init_ml_services():
    """Initialize ML services"""
    global recognizer, tts_service, gesture_manager
    
    if recognizer is None:
        recognizer = SignLanguageRecognizer()
    
    if tts_service is None:
        tts_service = TTSService(engine_type='pyttsx3')
    
    if gesture_manager is None:
        gesture_manager = GestureToSpeechManager(tts_service)

@api.route('/predict', methods=['POST'])
@login_required
def predict_gesture():
    """Predict gesture from uploaded image"""
    try:
        init_ml_services()
        
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Decode base64 image
        image_data = base64.b64decode(data['image'].split(',')[1])
        np_array = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'error': 'Invalid image data'}), 400
        
        # Process frame
        annotated_frame, gesture, confidence = recognizer.process_frame(frame)
        
        # Add gesture to speech manager
        if gesture and confidence > 0.7:
            accumulated_text = gesture_manager.add_gesture(gesture)
            
            # Log gesture if we have an active session
            # TODO: Implement session tracking
        
        # Encode processed frame back to base64
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        processed_image = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'gesture': gesture,
            'confidence': float(confidence),
            'accumulated_text': gesture_manager.get_text(),
            'processed_image': f'data:image/jpeg;base64,{processed_image}'
        })
    
    except Exception as e:
        current_app.logger.error(f"Error in predict_gesture: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/speak', methods=['POST'])
@login_required
def speak_text():
    """Convert text to speech"""
    try:
        init_ml_services()
        
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({'error': 'Empty text provided'}), 400
        
        success = tts_service.speak(text, async_mode=True)
        
        return jsonify({
            'success': success,
            'message': 'Text sent to speech synthesis' if success else 'Failed to speak text'
        })
    
    except Exception as e:
        current_app.logger.error(f"Error in speak_text: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/clear_text', methods=['POST'])
@login_required
def clear_accumulated_text():
    """Clear accumulated text"""
    try:
        init_ml_services()
        gesture_manager.clear_text()
        
        return jsonify({
            'success': True,
            'message': 'Text cleared successfully'
        })
    
    except Exception as e:
        current_app.logger.error(f"Error in clear_text: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/tts_settings', methods=['GET', 'POST'])
@login_required
def tts_settings():
    """Get or update TTS settings"""
    try:
        init_ml_services()
        
        if request.method == 'GET':
            voices = tts_service.get_voices()
            return jsonify({
                'voices': voices,
                'engine_type': tts_service.engine_type
            })
        
        elif request.method == 'POST':
            data = request.get_json()
            
            if 'rate' in data:
                tts_service.set_rate(int(data['rate']))
            
            if 'volume' in data:
                tts_service.set_volume(float(data['volume']))
            
            if 'voice_id' in data:
                tts_service.set_voice(data['voice_id'])
            
            return jsonify({'success': True, 'message': 'Settings updated'})
    
    except Exception as e:
        current_app.logger.error(f"Error in tts_settings: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/model_info', methods=['GET'])
@login_required
def model_info():
    """Get information about the current model"""
    try:
        init_ml_services()
        
        return jsonify({
            'labels': recognizer.labels,
            'confidence_threshold': recognizer.confidence_threshold,
            'model_type': 'Neural Network with MediaPipe landmarks',
            'input_features': 42,  # 21 landmarks * 2 coordinates
            'total_classes': len(recognizer.labels)
        })
    
    except Exception as e:
        current_app.logger.error(f"Error in model_info: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/start_session', methods=['POST'])
@login_required
def start_session():
    """Start a new recognition session"""
    try:
        # End any existing active sessions
        active_sessions = UserSession.query.filter_by(
            user_id=current_user.id,
            session_end=None
        ).all()
        
        for session in active_sessions:
            session.session_end = db.func.now()
        
        # Create new session
        new_session = UserSession(user_id=current_user.id)
        db.session.add(new_session)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'session_id': new_session.id,
            'message': 'Session started successfully'
        })
    
    except Exception as e:
        current_app.logger.error(f"Error in start_session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/end_session', methods=['POST'])
@login_required
def end_session():
    """End the current recognition session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id') if data else None
        
        if session_id:
            session = UserSession.query.filter_by(
                id=session_id,
                user_id=current_user.id
            ).first()
        else:
            # Find the most recent active session
            session = UserSession.query.filter_by(
                user_id=current_user.id,
                session_end=None
            ).order_by(UserSession.session_start.desc()).first()
        
        if session:
            session.session_end = db.func.now()
            if gesture_manager:
                session.text_generated = gesture_manager.get_text()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Session ended successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No active session found'
            })
    
    except Exception as e:
        current_app.logger.error(f"Error in end_session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/user_stats', methods=['GET'])
@login_required
def user_stats():
    """Get user statistics"""
    try:
        # Get session count
        session_count = UserSession.query.filter_by(user_id=current_user.id).count()
        
        # Get total gestures recognized
        total_gestures = db.session.query(db.func.sum(UserSession.gestures_recognized)).filter_by(
            user_id=current_user.id
        ).scalar() or 0
        
        # Get recent sessions
        recent_sessions = UserSession.query.filter_by(
            user_id=current_user.id
        ).order_by(UserSession.session_start.desc()).limit(5).all()
        
        sessions_data = []
        for session in recent_sessions:
            sessions_data.append({
                'id': session.id,
                'start': session.session_start.isoformat(),
                'end': session.session_end.isoformat() if session.session_end else None,
                'gestures': session.gestures_recognized,
                'text': session.text_generated[:100] + '...' if session.text_generated and len(session.text_generated) > 100 else session.text_generated
            })
        
        return jsonify({
            'session_count': session_count,
            'total_gestures': total_gestures,
            'recent_sessions': sessions_data,
            'member_since': current_user.created_at.isoformat()
        })
    
    except Exception as e:
        current_app.logger.error(f"Error in user_stats: {str(e)}")
        return jsonify({'error': str(e)}), 500