<div align="center">

# 🎤 Voice Assistant - AI-Powered Voice Control

**Transform your PC into a smart, voice-controlled powerhouse**

[![Status](https://img.shields.io/badge/Status-In%20Development-yellow?style=for-the-badge)]()
[![Voice Assistant](https://img.shields.io/badge/Voice-Assistant-blue?style=for-the-badge)]()
[![Python](https://img.shields.io/badge/Python-3.8%2B-green?style=for-the-badge&logo=python)]()
[![Flask](https://img.shields.io/badge/Flask-Web%20Framework-red?style=for-the-badge&logo=flask)]()
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)]()

</div>

A sophisticated voice assistant that responds to your commands, plays music, controls your system, and learns from your voice patterns.

## 📑 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Voice Commands](#-voice-commands)
- [Training](#-training-your-voice-model)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Privacy & Security](#️-privacy--security)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 🎯 Core Functionality
- **Always Listening**: Activates when you say "**New**"
- **Voice Commands**: Control apps, files, web, and system functions
- **Smart Conversations**: Chat with natural language responses
- **Music Playback**: Play specific songs, artists, or genres
- **System Control**: Shutdown, restart, volume, screenshots
- **Time/Date Queries**: "What time is it?" responses

### 🎵 Enhanced Music Support
- **Specific Songs**: "Play Bohemian Rhapsody by Queen"
- **Artists**: "Play Taylor Swift" or "Play music by Mozart"
- **Genres**: "Play some jazz" or "Put on rock music"
- **Platforms**: YouTube, Spotify integration
- **Smart Search**: Automatically finds the best version

### 🧠 AI Learning System
- **Voice Training**: Learns your unique speech patterns
- **Correction Learning**: Improves from mistakes
- **Personalized Recognition**: Gets better over time
- **Pattern Analysis**: Understands your accent and style

### 🎨 Modern UI Design
- **Glassmorphism**: Frosted glass effects with blur
- **Animated Gradients**: Dynamic color-shifting backgrounds
- **Smooth Animations**: Hover effects and transitions
- **Responsive Design**: Works on all screen sizes
- **Professional Logo**: Modern star with sound waves

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Microphone access
- Modern browser (Chrome/Edge recommended)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/ADARSHBISWAL1/voice-to-action.git
cd voice-to-action
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the assistant**
```bash
# Option 1: Use the batch file (Windows)
run.bat

# Option 2: Run directly
python app.py
```

4. **Open your browser**
Navigate to: http://127.0.0.1:5000

### First Use
1. **Allow microphone permissions** when prompted
2. **Wait for voice system initialization** (2 seconds)
3. **Say "New"** to activate the assistant
4. **Try commands**: "Hello", "What time is it?", "Open youtube"

## 🎮 Voice Commands

### 🗣️ Activation
- **"New"** - Activates the assistant
- **"Hey New"** - Alternative activation

### 💬 Conversation
- **"Hello"**, **"Hi"**, **"Hey"** - Greetings
- **"How are you?"** - Status check
- **"What can you do?"** - Help and capabilities
- **"What time is it?"** - Current time
- **"What date is it?"** - Current date

### 🎵 Music & Media
- **"Play [song] by [artist]"** - Specific songs
- **"Play [artist]"** - Artist's music
- **"Play some [genre]"** - Genre-based music
- **"Play [song] on YouTube"** - Platform-specific
- **"Play music"** - Opens music app

### 🖥️ Applications
- **"Open [app]"** - Launch any application
- **"Open youtube"**, **"Open chrome"**, **"Open notepad"**
- **"Open documents"**, **"Open downloads"**, **"Open desktop"**

### 🌐 Web & Search
- **"Search for [query]"** - Google search
- **"Google [topic]"** - Quick search
- **"Open facebook"**, **"Open github"**, **"Open reddit"**

### ⚙️ System Control
- **"Volume up"**, **"Volume down"**, **"Mute"**
- **"Screenshot"**, **"Take screenshot"**
- **"Lock"**, **"Sleep"** (with confirmation)
- **"Control panel"**, **"Task manager"**

## 🧠 Training Your Voice Model

### Interactive Training
```bash
# Run the training system
python train_model.py
```

### Training Examples
```
hey new | new                    # I said "hey new", meant "new"
open youtub | open youtube       # Correction example
play jazz music | play jazz     # Pattern learning
```

### Benefits of Training
- **Better Recognition**: Understands your accent
- **Fewer Errors**: Corrects common mistakes
- **Personalized**: Adapts to your speech patterns
- **Continuous Learning**: Improves over time

## 📁 Project Structure

```
voice-to-action/
├── app.py                 # Main Flask application
├── train_model.py         # Voice training system
├── integrate_model.py     # Model integration
├── requirements.txt       # Python dependencies
├── run.bat               # Easy launch script
├── train.bat             # Training launcher
├── .gitignore            # Data protection
├── README.md             # This file
└── static/
    ├── index.html        # Modern UI interface
    ├── app.js           # Voice recognition logic
    └── style.css        # Glassmorphism styling
```

## 🔧 Configuration

### Environment Variables
```bash
# Optional: Set custom configurations
export VOICE_ASSISTANT_PORT=5000
export VOICE_ASSISTANT_DEBUG=false
```

### Customization
- **Activation Word**: Change "New" in `static/app.js`
- **UI Colors**: Modify CSS variables in `static/style.css`
- **Commands**: Add new commands in `app.py`

## 🛡️ Privacy & Security

### Data Protection
- **Local Processing**: All voice processing happens locally
- **No Cloud Storage**: Your voice data never leaves your computer
- **Git Protection**: `.gitignore` prevents sensitive data upload
- **Secure Defaults**: No API keys or external services required

### Protected Files
- Voice recordings and training data
- User preferences and command history
- API keys and configuration files
- Temporary files and caches

## 🐛 Troubleshooting

### Common Issues

**Microphone not working?**
- Check browser permissions
- Ensure microphone is not muted
- Try Chrome/Edge for best compatibility

**Voice recognition inaccurate?**
- Run the training system: `python train_model.py`
- Add corrections for misunderstood words
- Train with your specific accent patterns

**Server won't start?**
- Check if port 5000 is available
- Install dependencies: `pip install -r requirements.txt`
- Run as administrator if needed

**Music not playing?**
- Ensure YouTube/Spotify is accessible
- Check internet connection
- Try specific song names instead of genres

### Debug Mode
```bash
# Run with debug logging
python app.py --debug
```

## 🤝 Contributing

Contributions are welcome! Please:

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Run in development mode
python app.py --debug
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Web Speech API** - Browser voice recognition
- **Flask** - Web framework
- **Scikit-learn** - Machine learning for voice training
- **Modern CSS** - Glassmorphism design inspiration

## 👨‍💻 Author

**Created by [ADARSHBISWAL1](https://github.com/ADARSHBISWAL1)**

- 🌟 **GitHub**: [ADARSHBISWAL1](https://github.com/ADARSHBISWAL1)
- 📧 **Email**: Available through GitHub
- 💼 **Portfolio**: Check out other projects!

---

## 🎉 Get Started

Transform your PC into a smart, voice-controlled powerhouse. Just say "**New**" and let the magic happen! ✨

---

<div align="center">

**Made with ❤️ by [ADARSHBISWAL1](https://github.com/ADARSHBISWAL1)**

⭐ Star this repo if you find it helpful!

</div>
