from flask import Blueprint, session, redirect, url_for, render_template, request, flash
from app.extensions import mongo, bcrypt
from transformers import pipeline
import json
import random
import os
from datetime import datetime
from bson import ObjectId

# Load the model using HuggingFace pipeline
classifier = pipeline(
    task="text-classification",
    model="SamLowe/roberta-base-go_emotions",
    top_k=None  # Return all label probabilities (multi-label)
)

# Basic emotion mapping dictionary (6 basic emotions + neutral)
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

# Load meme mapping from JSON file once
MEME_MAPPING_PATH = os.path.join("static", "data", "meme_mapping.json")
with open(MEME_MAPPING_PATH, "r") as f:
    meme_mapping = json.load(f)


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
            # Step 1: Run classifier on content
            model_outputs = classifier([content])
            predicted = sorted(model_outputs[0], key=lambda x: x['score'], reverse=True)
            top_emotion_label = predicted[0]['label'].lower()
            basic_emotion = GOEMOTIONS_TO_BASIC.get(top_emotion_label, "neutral")

            print(f"[DEBUG] Basic Emotion Detected: {basic_emotion}") # debugging output

            # Step 2: Select random meme path from loaded JSON
            meme_list = meme_mapping.get(basic_emotion, [])
            meme_path = random.choice(meme_list) if meme_list else ""

            # Step 3: Save to MongoDB
            mongo.db.journal_entries.insert_one({
                "user_id": session["user_id"],
                "email": user.get("email"),
                "title": title,
                "content": content,
                "meme": meme_path,
                "emotion": basic_emotion,
                "date": datetime.now().strftime("%B %d, %Y %I:%M %p"),
                "isFavorite": False  # default state
            })

            flash(f"Entry created with {basic_emotion} meme!", "success")
            return redirect(url_for("dashboard.dashboard"))
        else:
            flash("Please fill in all fields", "error")

    # entries = list(mongo.db.journal_entries.find({"user_id": session["user_id"]}))
    # return render_template("dashboard.html", entries=entries)

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