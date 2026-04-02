"""
Voice Model Training System
Trains a custom model to better recognize user's voice patterns and commands
"""

import json
import os
import pickle
import re
import time
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score

class VoiceModelTrainer:
    def __init__(self):
        self.training_data_file = "voice_training_data.json"
        self.model_file = "voice_command_model.pkl"
        self.vectorizer_file = "voice_vectorizer.pkl"
        
        # Load existing training data
        self.training_data = self.load_training_data()
        
        # Command categories for better classification
        self.command_categories = {
            "activation": ["new", "hey new", "ok new"],
            "greeting": ["hello", "hi", "hey", "good morning", "good evening"],
            "farewell": ["bye", "goodbye", "see you", "later"],
            "apps": ["open", "launch", "start"],
            "web": ["search", "google", "find", "look up"],
            "system": ["shutdown", "restart", "sleep", "lock", "volume"],
            "files": ["documents", "downloads", "desktop", "pictures"],
            "media": ["youtube", "play", "music", "video"],
            "questions": ["what", "how", "when", "where", "who", "why"],
            "time": ["time", "date", "clock"],
            "help": ["help", "what can you do", "commands"],
        }
        
        self.model = None
        self.vectorizer = None
        
    def load_training_data(self):
        """Load existing training data or create new"""
        if os.path.exists(self.training_data_file):
            try:
                with open(self.training_data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading training data: {e}")
        
        return {
            "commands": [],
            "corrections": [],
            "patterns": {},
            "user_voice_patterns": {},
            "last_updated": None
        }
    
    def save_training_data(self):
        """Save training data to file"""
        self.training_data["last_updated"] = datetime.now().isoformat()
        try:
            with open(self.training_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.training_data, f, indent=2, ensure_ascii=False)
            print(f"Training data saved to {self.training_data_file}")
        except Exception as e:
            print(f"Error saving training data: {e}")
    
    def add_training_example(self, spoken_text, intended_command, confidence=1.0):
        """Add a new training example"""
        example = {
            "spoken": spoken_text.lower().strip(),
            "intended": intended_command.lower().strip(),
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
        
        self.training_data["commands"].append(example)
        
        # Extract patterns
        self._extract_patterns(spoken_text, intended_command)
        
        print(f"Added training example: '{spoken_text}' -> '{intended_command}'")
        
    def add_correction(self, misheard_text, correct_text):
        """Add a correction when the assistant mishears something"""
        correction = {
            "misheard": misheard_text.lower().strip(),
            "correct": correct_text.lower().strip(),
            "timestamp": datetime.now().isoformat()
        }
        
        self.training_data["corrections"].append(correction)
        print(f"Added correction: '{misheard_text}' -> '{correct_text}'")
    
    def _extract_patterns(self, spoken, intended):
        """Extract common patterns from user speech"""
        spoken_words = spoken.split()
        intended_words = intended.split()
        
        # Find common word patterns
        for i, word in enumerate(spoken_words):
            if word not in self.training_data["patterns"]:
                self.training_data["patterns"][word] = {
                    "followed_by": Counter(),
                    "replaced_with": Counter(),
                    "contexts": []
                }
            
            # Track what words typically follow this word
            if i < len(spoken_words) - 1:
                next_word = spoken_words[i + 1]
                self.training_data["patterns"][word]["followed_by"][next_word] += 1
            
            # Track common replacements/corrections
            if i < len(intended_words):
                intended_word = intended_words[i]
                if word != intended_word:
                    self.training_data["patterns"][word]["replaced_with"][intended_word] += 1
            
            # Store context
            context = {
                "full_spoken": spoken,
                "full_intended": intended,
                "position": i
            }
            self.training_data["patterns"][word]["contexts"].append(context)
    
    def categorize_command(self, command):
        """Categorize a command into one of the predefined categories"""
        command_lower = command.lower()
        
        for category, keywords in self.command_categories.items():
            if any(keyword in command_lower for keyword in keywords):
                return category
        
        return "other"
    
    def prepare_training_dataset(self):
        """Prepare dataset for machine learning training"""
        if not self.training_data["commands"]:
            print("No training data available!")
            return None, None
        
        # Prepare features and labels
        texts = []
        labels = []
        
        for example in self.training_data["commands"]:
            texts.append(example["spoken"])
            labels.append(example["intended"])
        
        # Add corrections as additional training examples
        for correction in self.training_data["corrections"]:
            texts.append(correction["misheard"])
            labels.append(correction["correct"])
        
        return texts, labels
    
    def train_model(self):
        """Train the voice command recognition model"""
        texts, labels = self.prepare_training_dataset()
        
        if not texts or len(texts) < 5:
            print("Need at least 5 training examples to train the model!")
            return False
        
        print(f"Training model with {len(texts)} examples...")
        
        # Split data for training and testing
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.2, random_state=42
        )
        
        # Create a pipeline with TF-IDF vectorizer and Naive Bayes classifier
        self.model = Pipeline([
            ('vectorizer', TfidfVectorizer(
                ngram_range=(1, 3),  # Use 1-3 grams
                lowercase=True,
                stop_words='english',
                min_df=1,
                max_features=1000
            )),
            ('classifier', MultinomialNB(alpha=0.1))
        ])
        
        # Train the model
        self.model.fit(X_train, y_train)
        
        # Evaluate the model
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Model trained successfully!")
        print(f"Accuracy: {accuracy:.2f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        # Save the model
        self.save_model()
        
        return True
    
    def save_model(self):
        """Save the trained model and vectorizer"""
        if self.model:
            with open(self.model_file, 'wb') as f:
                pickle.dump(self.model, f)
            print(f"Model saved to {self.model_file}")
        
        if self.vectorizer:
            with open(self.vectorizer_file, 'wb') as f:
                pickle.dump(self.vectorizer, f)
            print(f"Vectorizer saved to {self.vectorizer_file}")
    
    def load_model(self):
        """Load a previously trained model"""
        try:
            with open(self.model_file, 'rb') as f:
                self.model = pickle.load(f)
            print(f"Model loaded from {self.model_file}")
            return True
        except FileNotFoundError:
            print("No trained model found. Please train the model first.")
            return False
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def predict_command(self, spoken_text):
        """Predict the intended command from spoken text"""
        if not self.model:
            print("Model not trained or loaded!")
            return None, 0.0
        
        try:
            # Get prediction probabilities
            probabilities = self.model.predict_proba([spoken_text])[0]
            classes = self.model.classes_
            
            # Get the best prediction
            max_prob_idx = np.argmax(probabilities)
            predicted_command = classes[max_prob_idx]
            confidence = probabilities[max_prob_idx]
            
            return predicted_command, confidence
        except Exception as e:
            print(f"Prediction error: {e}")
            return None, 0.0
    
    def get_training_stats(self):
        """Get statistics about the training data"""
        stats = {
            "total_examples": len(self.training_data["commands"]),
            "total_corrections": len(self.training_data["corrections"]),
            "unique_patterns": len(self.training_data["patterns"]),
            "last_updated": self.training_data.get("last_updated"),
            "command_categories": defaultdict(int)
        }
        
        # Count examples by category
        for example in self.training_data["commands"]:
            category = self.categorize_command(example["intended"])
            stats["command_categories"][category] += 1
        
        return dict(stats)
    
    def interactive_training(self):
        """Interactive training session"""
        print("=== Voice Model Training Session ===")
        print("Type 'quit' to finish training")
        print("Format: spoken_text | intended_command")
        print("Example: hey new | new")
        print("Or type 'correct: misheard | correct' for corrections")
        print()
        
        while True:
            user_input = input("Training example (or 'quit'): ").strip()
            
            if user_input.lower() == 'quit':
                break
            
            if user_input.startswith('correct:'):
                # Handle correction
                correction_part = user_input[9:].strip()
                if '|' in correction_part:
                    misheard, correct = [part.strip() for part in correction_part.split('|', 1)]
                    self.add_correction(misheard, correct)
                else:
                    print("Correction format: correct: misheard | correct")
            
            elif '|' in user_input:
                # Handle training example
                spoken, intended = [part.strip() for part in user_input.split('|', 1)]
                confidence = float(input("Confidence (0-1, default=1.0): ") or "1.0")
                self.add_training_example(spoken, intended, confidence)
            
            else:
                print("Format: spoken_text | intended_command")
                print("Or: correct: misheard | correct")
        
        # Save training data
        self.save_training_data()
        
        # Ask if user wants to train the model
        if input("Train model with this data? (y/n): ").lower() == 'y':
            self.train_model()

def main():
    trainer = VoiceModelTrainer()
    
    while True:
        print("\n=== Voice Model Trainer ===")
        print("1. Interactive training")
        print("2. Add single example")
        print("3. Add correction")
        print("4. Train model")
        print("5. Test model")
        print("6. View statistics")
        print("7. Load existing model")
        print("8. Quit")
        
        choice = input("Choose an option: ").strip()
        
        if choice == '1':
            trainer.interactive_training()
        
        elif choice == '2':
            spoken = input("Spoken text: ").strip()
            intended = input("Intended command: ").strip()
            confidence = float(input("Confidence (0-1, default=1.0): ") or "1.0")
            trainer.add_training_example(spoken, intended, confidence)
            trainer.save_training_data()
        
        elif choice == '3':
            misheard = input("Misheard text: ").strip()
            correct = input("Correct text: ").strip()
            trainer.add_correction(misheard, correct)
            trainer.save_training_data()
        
        elif choice == '4':
            trainer.train_model()
        
        elif choice == '5':
            if trainer.load_model():
                while True:
                    test_text = input("Test text (or 'quit'): ").strip()
                    if test_text.lower() == 'quit':
                        break
                    prediction, confidence = trainer.predict_command(test_text)
                    if prediction:
                        print(f"Predicted: '{prediction}' (confidence: {confidence:.2f})")
                    else:
                        print("Prediction failed")
        
        elif choice == '6':
            stats = trainer.get_training_stats()
            print("\nTraining Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        
        elif choice == '7':
            trainer.load_model()
        
        elif choice == '8':
            break
        
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()
