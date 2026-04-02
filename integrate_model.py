"""
Integrate trained voice model with the main voice assistant
"""

import json
import pickle
import os
from train_model import VoiceModelTrainer

class EnhancedVoiceAssistant:
    def __init__(self):
        self.trainer = VoiceModelTrainer()
        self.model_loaded = False
        self.load_trained_model()
        
    def load_trained_model(self):
        """Load the trained model if available"""
        self.model_loaded = self.trainer.load_model()
        if self.model_loaded:
            print("✅ Trained voice model loaded successfully!")
        else:
            print("⚠️ No trained model found - using default recognition")
    
    def process_command(self, spoken_text):
        """Process spoken command with trained model enhancement"""
        if not self.model_loaded:
            return None, 0.0
        
        # Use trained model to predict intended command
        predicted_command, confidence = self.trainer.predict_command(spoken_text)
        
        return predicted_command, confidence
    
    def add_user_correction(self, misheard, correct):
        """Add user correction to improve future recognition"""
        self.trainer.add_correction(misheard, correct)
        self.trainer.save_training_data()
        
        # Retrain model if we have enough new data
        if len(self.trainer.training_data["corrections"]) % 10 == 0:
            print("🔄 Retraining model with new corrections...")
            success = self.trainer.train_model()
            if success:
                self.model_loaded = self.trainer.load_model()
                print("✅ Model retrained successfully!")
    
    def get_training_status(self):
        """Get current training status"""
        stats = self.trainer.get_training_stats()
        return {
            "model_loaded": self.model_loaded,
            "training_examples": stats.get("total_examples", 0),
            "corrections": stats.get("total_corrections", 0),
            "patterns": stats.get("unique_patterns", 0),
            "last_updated": stats.get("last_updated")
        }

# Global instance for the voice assistant
enhanced_assistant = EnhancedVoiceAssistant()

def enhance_command_recognition(spoken_text):
    """Enhance command recognition with trained model"""
    if enhanced_assistant.model_loaded:
        predicted, confidence = enhanced_assistant.process_command(spoken_text)
        if predicted and confidence > 0.7:  # High confidence threshold
            return predicted, confidence
    return spoken_text, 0.0

def add_training_feedback(spoken_text, intended_command):
    """Add feedback for continuous learning"""
    if spoken_text != intended_command:
        enhanced_assistant.add_user_correction(spoken_text, intended_command)
        return True
    return False

def get_model_info():
    """Get model information for display"""
    return enhanced_assistant.get_training_status()
