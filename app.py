# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from datetime import datetime
import os

# ---------------------------
# Flask & DB-Konfiguration
# ---------------------------
app = Flask(__name__)
app.secret_key = "geheim"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "notes.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------------------
# Datenbankmodell
# ---------------------------
class Note(db.Model):
    __tablename__ = "notes"
    id = db.Column(db.Integer, primary_key=True)
    titel = db.Column(db.String(100), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)                # Erstellt am
    updated = db.Column(db.DateTime, onupdate=datetime.utcnow, nullable=True) # Zuletzt geändert

    def __repr__(self):
        return f"<Note {self.id} '{self.titel}'>"

# Tabellen anlegen, falls nicht vorhanden
with app.app_context():
    db.create_all()

# ---------------------------
# Routen
# ---------------------------
@app.route("/")
def startseite():
    """Startseite mit optionaler Suche (Titel/Text). Neueste zuerst."""
    q = (request.args.get("q") or "").strip()
    query = Note.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Note.titel.ilike(like), Note.text.ilike(like)))
    notes = query.order_by(Note.created.desc()).all()
    return render_template("index.html", notes=notes, q=q)

@app.route("/neu", methods=["GET", "POST"])
def neu():
    """Neue Notiz anlegen."""
    if request.method == "POST":
        titel = (request.form.get("titel") or "").strip()
        text  = (request.form.get("text") or "").strip()

        if not titel or not text:
            flash("Bitte Titel und Text eingeben.")
            return redirect(url_for("neu"))

        note = Note(titel=titel, text=text)
        db.session.add(note)
        db.session.commit()

        flash("Notiz gespeichert!")
        return redirect(url_for("startseite"))

    return render_template("new.html")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id: int):
    """Bestehende Notiz bearbeiten."""
    note = Note.query.get_or_404(id)

    if request.method == "POST":
        titel = (request.form.get("titel") or "").strip()
        text  = (request.form.get("text") or "").strip()

        if not titel or not text:
            flash("Bitte Titel und Text eingeben.")
            return redirect(url_for("edit", id=id))

        note.titel = titel
        note.text = text
        # updated wird automatisch per onupdate gesetzt
        db.session.commit()

        flash("Notiz aktualisiert!")
        return redirect(url_for("startseite"))

    return render_template("edit.html", note=note)

@app.route("/loeschen/<int:id>", methods=["POST"])
def loeschen(id: int):
    """Notiz löschen (POST)."""
    note = Note.query.get_or_404(id)
    db.session.delete(note)
    db.session.commit()
    flash("Notiz gelöscht!")
    return redirect(url_for("startseite"))

# ---------------------------
# App-Start
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
