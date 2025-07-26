from flask import Blueprint, session, redirect, url_for, render_template, request, flash
from app.extensions import mongo, bcrypt
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import json
import random
import os
from datetime import datetime
from bson import ObjectId

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained("SamLowe/roberta-base-go_emotions")
model = AutoModelForSequenceClassification.from_pretrained("SamLowe/roberta-base-go_emotions")
model.eval()  # Set model to eval mode

# Load emotion labels
LABELS_PATH = os.path.join("static", "data", "goemotions_labels.json")  # create this file with the 28 class names in order
with open(LABELS_PATH, "r") as f:
    emotion_labels = json.load(f)

# Load meme mapping
MEME_MAPPING_PATH = os.path.join("static", "data", "meme_mapping.json")
with open(MEME_MAPPING_PATH, "r") as f:
    meme_mapping = json.load(f)

# Mapping to 6 basic emotions
GOEMOTIONS_TO_BASIC = {
    "admiration": "happiness",
    "amusement": "happiness",
    "approval": "happiness",
    "caring": "happiness",
    "desire": "happiness",
    "excitement": "happiness",
    "gratitude": "happiness",
    "joy": "happiness",
    "love": "happiness",
    "optimism": "happiness",
    "pride": "happiness",
    "relief": "happiness",

    "anger": "anger",
    "annoyance": "anger",
    "disapproval": "anger",

    "disgust": "disgust",

    "curiosity": "surprise",
    "confusion": "surprise",
    "realization": "surprise",
    "surprise": "surprise",

    "fear": "fear",
    "nervousness": "fear",

    "sadness": "sadness",
    "disappointment": "sadness",
    "grief": "sadness",
    "remorse": "sadness",
    "embarrassment": "sadness",

    "neutral": "neutral"
}

dash_bp = Blueprint("dashboard", __name__)

@dash_bp.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.index"))

    user = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])})
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("auth.index"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()

        if title and content:
            # Tokenize and run through model
            inputs = tokenizer(content, return_tensors="pt", truncation=True, padding=True)
            with torch.no_grad():
                outputs = model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=-1).squeeze()

            # Get top emotion
            scored_labels = list(zip(emotion_labels, probs.tolist()))
            sorted_labels = sorted(scored_labels, key=lambda x: x[1], reverse=True)
            top_emotion_label = sorted_labels[0][0]
            basic_emotion = GOEMOTIONS_TO_BASIC.get(top_emotion_label, "neutral")

            print(f"[DEBUG] Basic Emotion Detected: {basic_emotion}")  # debug

            # Select meme
            meme_list = meme_mapping.get(basic_emotion, [])
            meme_path = random.choice(meme_list) if meme_list else ""

            # Save to MongoDB
            mongo.db.journal_entries.insert_one({
                "user_id": session["user_id"],
                "email": user.get("email"),
                "title": title,
                "content": content,
                "meme": meme_path,
                "emotion": basic_emotion,
                "date": datetime.now().strftime("%B %d, %Y %I:%M %p"),
                "isFavorite": False
            })

            flash(f"Entry created with {basic_emotion} meme!", "success")
            return redirect(url_for("dashboard.dashboard"))
        else:
            flash("Please fill in all fields", "error")

    search_query = request.args.get("search", "").strip()
    if search_query:
        entries = list(
            mongo.db.journal_entries.find({
                "user_id": session["user_id"],
                "title": {"$regex": search_query, "$options": "i"}
            }).sort("_id", -1)
        )
    else:
        entries = list(
            mongo.db.journal_entries.find({"user_id": session["user_id"]}).sort("_id", -1)
        )

    return render_template("dashboard.html", entries=entries, search_query=search_query)