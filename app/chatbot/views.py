import os
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
import google.generativeai as genai

from . import chatbot
from .. import csrf
from .forms import ChatForm
from .. import db
from ..models import Resident, InventoryItem, UsageLog
from ..decorators import admin_required, caregiver_required

# Configure the Gemini API client
def get_gemini_api_key():
    return os.environ.get("GEMINI_API_KEY") or getattr(genai, 'API_KEY', None)

@chatbot.route('/', methods=['GET', 'POST'])
@login_required
@caregiver_required
def index():
    """Main chatbot interface."""
    form = ChatForm()
    return render_template('chatbot/index.html', form=form, show_sidebar=True)

@chatbot.route('/api/ask', methods=['POST'])
@csrf.exempt  # exempt this AJAX endpoint from CSRF to allow JSON POST
@login_required
@caregiver_required
def ask():
    """API endpoint for chatbot queries."""
    data = request.get_json()
    query = data.get('message', '')

    # Retrieve context: Residents, InventoryItems, UsageLogs for this caregiver
    residents = Resident.query.all()
    inventory_items = InventoryItem.query.all()
    usage_logs = UsageLog.query.order_by(UsageLog.timestamp.desc()).limit(20).all()

    # Build context string
    context = []
    for r in residents:
        context.append(f"Resident: {r.name}, DOB: {r.date_of_birth}")
    for i in inventory_items:
        context.append(f"Inventory: {i.name}, Qty: {i.quantity}, Schedule: {i.schedule_times}")
    for u in usage_logs:
        context.append(f"UsageLog: Resident {u.resident_id}, Item {u.inventory_item_id}, Status: {u.status}, Time: {u.scheduled_time}")
    context_str = "\n".join(context)

    # Gemini API call
    api_key = get_gemini_api_key()
    if not api_key:
        return jsonify({'answer': 'Gemini API key not configured.'})
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        prompt = f"Context:\n{context_str}\n\nUser question: {query}\nAnswer:"
        response = model.generate_content(prompt)
        answer = response.text if hasattr(response, 'text') else str(response)
    except Exception as e:
        answer = f"Error communicating with Gemini API: {e}"

    return jsonify({'answer': answer})
