# GestureBridge AI 🤟

### Real-Time Hand Gesture Recognition with Voice Feedback

GestureBridge AI is a Python-based project that recognizes hand gestures using a webcam and provides voice feedback. It includes a Streamlit dashboard for viewing gesture history saved in MongoDB Atlas.

## ✨ Features

- Real-time hand gesture detection using a webcam
- Recognition of common gestures, including Thumbs Up, Open Palm, Fist, Peace Sign, and OK Sign
- Voice feedback for detected gestures
- Streamlit dashboard for gesture history and project information
- MongoDB Atlas integration for storing gesture records
- Hand landmark detection using MediaPipe

## 🛠️ Technologies Used

- Python
- OpenCV
- MediaPipe
- Streamlit
- MongoDB Atlas
- PyMongo
- Python-dotenv
- PowerShell System.Speech for Windows voice feedback

## 📁 Project Structure

```text
GestureBridge-AI/
├── models/
│   └── hand_landmarker.task
├── app.py
├── gesture_database.py
├── hand_test.py
├── mongo_test.py
├── webcam_test.py
├── .gitignore
└── README.md
```

## ⚙️ Setup and Installation

### 1. Clone the repository

```bash
git clone https://github.com/keerthanaradharapu2707/GestureBridge-AI.git
cd GestureBridge-AI
```

### 2. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
```

### 3. Install dependencies

Install the Python packages required by the project:

```powershell
pip install opencv-python mediapipe scikit-learn streamlit pymongo python-dotenv pyttsx3
```

### 4. Configure MongoDB Atlas

Create a `.env` file in the project root and add your MongoDB connection string:

```text
MONGODB_URI=your_mongodb_connection_string
```

Replace the placeholder with your own connection string. Never upload `.env` or share your database credentials.

### 5. Run the dashboard

```powershell
streamlit run app.py
```

### 6. Run the gesture recognition program

```powershell
python hand_test.py
```

The webcam and voice-feedback features are intended for a compatible local Windows environment.

## 🗄️ Database

GestureBridge AI uses MongoDB Atlas to store gesture history. Configure the correct database and collection names in the project code before running it.

## 🚀 Future Improvements

- Train and evaluate a dedicated gesture classification model
- Add more custom hand gestures
- Improve gesture detection accuracy
- Add charts and detailed gesture statistics
- Explore deployment options for the dashboard

## 👩‍💻 Author

**Keerthana Radharapu**

GitHub: [keerthanaradharapu2707](https://github.com/keerthanaradharapu2707)

---

*GestureBridge AI — Making human-computer interaction more accessible through hand gestures.*
