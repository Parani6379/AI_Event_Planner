from flask import Blueprint
from app.controllers.ai_controller import AIController

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/decorate', methods=['POST'])
def decorate():
    return AIController.decorate_image()

@ai_bp.route('/chat', methods=['POST'])
def chat():
    return AIController.chat()

@ai_bp.route('/themes', methods=['GET'])
def themes():
    return AIController.get_themes()

@ai_bp.route('/budget-calculator', methods=['POST'])
def budget_calc():
    return AIController.budget_calculator()