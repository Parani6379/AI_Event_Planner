from flask import jsonify, request, current_app
import requests
import os
import uuid
import base64
import json
from io import BytesIO
from app.utils.file_handler import save_uploaded_file, save_base64_image


# ── Stability AI Config (image-to-image) ─────────────
STABILITY_API_URL = 'https://api.stability.ai/v2beta/stable-image/generate/sd3'

# ── Gemini API Config (text chat only) ────────────────
GEMINI_BASE_URL   = 'https://generativelanguage.googleapis.com/v1beta/models'
GEMINI_CHAT_MODEL = 'gemini-2.5-flash'


THEMES = {
    'Wedding': [
        {
            'theme_name': 'Royal Rose',
            'description': 'Elegant roses with gold accents and fairy lights',
            'colors': ['#FF6B6B', '#FFD700', '#FFFFFF'],
            'prompt': 'Wedding stage decorated with red and pink roses, gold accents, fairy lights, elegant backdrop'
        },
        {
            'theme_name': 'Garden Paradise',
            'description': 'Lush greenery with white flowers and natural elements',
            'colors': ['#90EE90', '#FFFFFF', '#228B22'],
            'prompt': 'Wedding stage with lush green garden theme, white orchids, tropical leaves, natural wood accents'
        },
        {
            'theme_name': 'Golden Luxury',
            'description': 'Opulent gold and cream with crystal chandeliers',
            'colors': ['#FFD700', '#FFFAF0', '#C0C0C0'],
            'prompt': 'Luxury wedding stage with gold draping, crystal chandeliers, cream flowers, royal backdrop'
        }
    ],
    'Temple Festival': [
        {
            'theme_name': 'Traditional Marigold',
            'description': 'Vibrant marigolds with banana leaves and diyas',
            'colors': ['#FF8C00', '#FFD700', '#228B22'],
            'prompt': 'Temple festival decoration with marigold flowers, banana leaves, oil lamps, traditional Indian style'
        },
        {
            'theme_name': 'Colorful Puja Mandap',
            'description': 'Bright colors with traditional patterns and flowers',
            'colors': ['#FF4500', '#9932CC', '#FFD700'],
            'prompt': 'Colorful temple puja mandap with silk draping, flower garlands, rangoli, traditional lamps'
        },
        {
            'theme_name': 'Floral Chariot',
            'description': 'Flower-covered chariot with jasmine and roses',
            'colors': ['#FFFFFF', '#FF69B4', '#90EE90'],
            'prompt': 'Festival chariot covered in white jasmine and pink roses, traditional South Indian style'
        }
    ],
    'Reception': [
        {
            'theme_name': 'Modern Chic',
            'description': 'Contemporary LED backdrop with minimalist floral',
            'colors': ['#1C1C1C', '#FFFFFF', '#C0C0C0'],
            'prompt': 'Modern reception hall with LED backdrop, minimalist white flower arrangements, ambient lighting'
        },
        {
            'theme_name': 'Romantic Pink',
            'description': 'Blush pink with roses and fairy light canopy',
            'colors': ['#FFB6C1', '#FF69B4', '#FFFFFF'],
            'prompt': 'Romantic reception with blush pink draping, rose walls, fairy light ceiling canopy'
        },
        {
            'theme_name': 'Royal Blue',
            'description': 'Navy and gold with elegant white flowers',
            'colors': ['#000080', '#FFD700', '#FFFFFF'],
            'prompt': 'Royal blue reception with gold accents, white flower centerpieces, grand chandelier'
        }
    ]
}


class AIController:

    # ── AI Decorate (Gemini Vision + Stability AI Image-to-Image) ─────
    @staticmethod
    def decorate_image():
        try:
            event_type = (request.form.get('event_type') or 'Wedding').strip()
            image_file = request.files.get('image')

            api_key          = current_app.config.get('STABILITY_API_KEY', '')
            gemini_api_key   = current_app.config.get('GEMINI_API_KEY', '')

            if not image_file or not image_file.filename:
                return jsonify({'success': False, 'message': 'No image uploaded.'}), 400

            image_file.seek(0)
            img_bytes = image_file.read()
            img_b64   = base64.b64encode(img_bytes).decode('utf-8')

            # ── Step 1: Gemini Vision — Analyze image & generate 3 smart themes ──
            themes = []

            if gemini_api_key:
                try:
                    gemini_url = (
                        f"{GEMINI_BASE_URL}/gemini-2.5-flash"
                        f":generateContent?key={gemini_api_key}"
                    )

                    gemini_payload = {
                        "contents": [
                            {
                                "parts": [
                                    {
                                        "inline_data": {
                                            "mime_type": "image/jpeg",
                                            "data": img_b64
                                        }
                                    },
                                    {
                                        "text": (
                                            f"You are an expert event decoration designer. "
                                            f"Analyze this venue image carefully — observe the space size, "
                                            f"structure, lighting, indoor or outdoor setting, existing elements. "
                                            f"The event type is: {event_type}. "
                                            f"Based on what you actually see in this image, generate exactly 3 "
                                            f"unique and creative decoration themes that would beautifully suit "
                                            f"this specific venue for a {event_type}. "
                                            f"Respond ONLY with a valid JSON array, no explanation, no markdown. "
                                            f"Format: "
                                            f"["
                                            f"  {{"
                                            f"    \"theme_name\": \"short catchy name\","
                                            f"    \"description\": \"one line description\","
                                            f"    \"colors\": [\"#hex1\", \"#hex2\", \"#hex3\"],"
                                            f"    \"prompt\": \"detailed stable diffusion image-to-image prompt "
                                            f"describing how to decorate this exact venue with flowers, lights, "
                                            f"draping, and props for {event_type}, photorealistic, professional\""
                                            f"  }}"
                                            f"]"
                                        )
                                    }
                                ]
                            }
                        ],
                        "generationConfig": {
                            "temperature": 0.8,
                            "maxOutputTokens": 1000
                        }
                    }

                    gemini_resp = requests.post(
                        gemini_url,
                        headers={'Content-Type': 'application/json'},
                        json=gemini_payload,
                        timeout=30
                    )

                    if gemini_resp.status_code == 200:
                        gemini_data = gemini_resp.json()
                        raw_text = (
                            gemini_data
                            .get('candidates', [{}])[0]
                            .get('content', {})
                            .get('parts', [{}])[0]
                            .get('text', '')
                            .strip()
                        )
                        # Strip markdown code fences if present
                        clean = raw_text.replace('```json', '').replace('```', '').strip()
                        themes = json.loads(clean)

                except Exception as e:
                    print(f"Gemini Vision error: {e}")

            # ── Fallback to hardcoded themes if Gemini fails ──
            if not themes:
                themes = THEMES.get(event_type, THEMES['Wedding'])

            # ── Step 2: Stability AI — image-to-image for each theme ──
            result_themes = []

            for theme in themes[:3]:
                generated  = False
                image_url  = None

                if api_key:
                    try:
                        prompt_text = (
                            f"Transform this venue into a stunning {event_type} decoration. "
                            f"Theme: {theme['prompt']}. "
                            f"Keep the original venue structure intact. "
                            f"Add beautiful decorations, flowers, lighting, draping. "
                            f"Photorealistic, professional photography style."
                        )

                        response = requests.post(
                            STABILITY_API_URL,
                            headers={
                                'Authorization': f'Bearer {api_key}',
                                'Accept': 'image/*'
                            },
                            files={
                                'image': ('venue.jpg', BytesIO(img_bytes), 'image/jpeg')
                            },
                            data={
                                'prompt':        prompt_text,
                                'mode':          'image-to-image',
                                'strength':      0.65,
                                'output_format': 'jpeg',
                                'model':         'sd3.5-large-turbo'
                            },
                            timeout=120
                        )

                        if response.status_code == 200:
                            result_b64 = base64.b64encode(response.content).decode('utf-8')
                            saved_path = save_base64_image(result_b64, 'ai_results')
                            if saved_path:
                                image_url = f'/static/{saved_path}'
                                generated = True
                        else:
                            print(f"Stability AI error {response.status_code}: {response.text[:200]}")

                    except Exception as e:
                        print(f"Stability AI request error: {e}")

                result_themes.append({
                    **theme,
                    'image_url': image_url,
                    'status':    'generated' if generated else 'suggestion'
                })

            return jsonify({
                'success': True,
                'data': {
                    'event_type': event_type,
                    'themes':     result_themes,
                    'ai_mode':    'generated' if api_key else 'suggestions'
                }
            })

        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    # ── AI Chat (Gemini Text) ─────────────────────────
    @staticmethod
    def chat():
        try:
            data       = request.get_json()
            message    = (data.get('message') or '').strip()
            event_type = (data.get('event_type') or '').strip()
            history    = data.get('history', [])

            if not message:
                return jsonify({'success': False, 'message': 'Message is required.'}), 400

            api_key = current_app.config.get('GEMINI_API_KEY', '')
            reply   = None

            if api_key:
                try:
                    # Build conversation for Gemini
                    system_text = (
                        "You are a helpful event decoration assistant for an Indian event "
                        "decoration business. You help customers with wedding, temple festival, "
                        "and reception decorations. Give practical advice about flowers, themes, "
                        "budgets in Indian Rupees, and decoration ideas. Be friendly and concise."
                    )
                    if event_type:
                        system_text += f" The customer is interested in {event_type} decoration."

                    # Build contents array with history
                    contents = []
                    for h in history[-4:]:
                        role = 'user' if h.get('role') == 'user' else 'model'
                        contents.append({
                            'role': role,
                            'parts': [{'text': h.get('content', '')}]
                        })
                    contents.append({
                        'role': 'user',
                        'parts': [{'text': message}]
                    })

                    url = f"{GEMINI_BASE_URL}/{GEMINI_CHAT_MODEL}:generateContent"
                    payload = {
                        'system_instruction': {
                            'parts': [{'text': system_text}]
                        },
                        'contents': contents,
                        'generationConfig': {
                            'maxOutputTokens': 500,
                            'temperature': 0.7
                        }
                    }

                    response = requests.post(
                        url,
                        headers={'Content-Type': 'application/json'},
                        params={'key': api_key},
                        json=payload,
                        timeout=30
                    )

                    if response.status_code == 200:
                        resp_data = response.json()
                        candidates = resp_data.get('candidates', [])
                        if candidates:
                            parts = candidates[0].get('content', {}).get('parts', [])
                            for part in parts:
                                if part.get('text'):
                                    reply = part['text'].strip()
                                    break
                except Exception:
                    pass

            # Fallback: rule-based responses
            if not reply:
                reply = _rule_based_reply(message.lower(), event_type)

            return jsonify({
                'success': True,
                'data': {'message': reply}
            })

        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    # ── Theme Suggestions ─────────────────────────────
    @staticmethod
    def get_themes():
        try:
            event_type = request.args.get('event_type', '').strip()
            if event_type and event_type in THEMES:
                themes = {event_type: THEMES[event_type]}
            else:
                themes = THEMES

            return jsonify({'success': True, 'data': {'themes': themes}})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    # ── Budget Calculator ─────────────────────────────
    @staticmethod
    def budget_calculator():
        try:
            data       = request.get_json()
            event_type = data.get('event_type', 'Wedding')
            guests     = int(data.get('guest_count', 100))
            duration   = int(data.get('duration_days', 1))
            package    = data.get('package', 'Standard')

            # Base prices
            base = {
                'Wedding':        {'Basic': 25000, 'Standard': 75000,
                                   'Premium': 200000, 'Royal': 500000},
                'Temple Festival':{'Basic': 10000, 'Standard': 35000,
                                   'Premium': 100000, 'Royal': 250000},
                'Reception':      {'Basic': 30000, 'Standard': 80000,
                                   'Premium': 250000, 'Royal': 450000}
            }

            event_base = base.get(event_type, base['Wedding'])
            pkg_base   = event_base.get(package, event_base['Standard'])

            # Guest multiplier
            guest_mult = 1.0
            if guests > 500:
                guest_mult = 1.8
            elif guests > 300:
                guest_mult = 1.5
            elif guests > 200:
                guest_mult = 1.25

            total = pkg_base * guest_mult * duration

            breakdown = {
                'Stage Decoration': int(total * 0.30),
                'Flowers':          int(total * 0.25),
                'Lighting':         int(total * 0.15),
                'Labour':           int(total * 0.15),
                'Transport':        int(total * 0.08),
                'Miscellaneous':    int(total * 0.07),
            }

            return jsonify({
                'success': True,
                'data': {
                    'event_type':      event_type,
                    'guest_count':     guests,
                    'duration_days':   duration,
                    'package':         package,
                    'estimated_total': int(total),
                    'breakdown':       breakdown
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500


# ── Helpers ───────────────────────────────────────────
def _rule_based_reply(msg, event_type=''):
    if any(w in msg for w in ['budget', 'cost', 'price', 'rupee', 'rs', '₹']):
        if 'wedding' in msg or event_type == 'Wedding':
            return (
                "For **Wedding Decoration**, budgets typically range:\n"
                "• Basic: ₹25,000 – ₹50,000\n"
                "• Standard: ₹75,000 – ₹1,50,000\n"
                "• Premium: ₹2,00,000 – ₹5,00,000\n\n"
                "Factors include venue size, flower choices, and lighting. "
                "Use our Budget Calculator for a precise estimate!"
            )
        elif 'temple' in msg or event_type == 'Temple Festival':
            return (
                "For **Temple Festival Decoration**, budgets typically range:\n"
                "• Basic: ₹10,000 – ₹25,000\n"
                "• Standard: ₹35,000 – ₹75,000\n"
                "• Premium: ₹1,00,000+\n\n"
                "Traditional flowers like marigold and jasmine are budget-friendly!"
            )
        elif 'reception' in msg or event_type == 'Reception':
            return (
                "For **Reception Decoration**, budgets typically range:\n"
                "• Basic: ₹30,000 – ₹60,000\n"
                "• Standard: ₹80,000 – ₹1,50,000\n"
                "• Premium: ₹2,50,000+\n\n"
                "LED backdrops and modern themes can enhance the look!"
            )
        return (
            "Our decoration packages start from ₹10,000. "
            "Please share your event type and guest count for a detailed estimate!"
        )

    elif any(w in msg for w in ['flower', 'floral', 'rose', 'marigold', 'jasmine']):
        return (
            "🌸 **Popular Flowers for Events:**\n\n"
            "• **Wedding:** Red roses, white lilies, orchids, baby's breath\n"
            "• **Temple Festival:** Marigold, jasmine, lotus, chrysanthemum\n"
            "• **Reception:** Mixed bouquets, carnations, gerbera daisies\n\n"
            "We source fresh flowers daily for every event!"
        )

    elif any(w in msg for w in ['theme', 'color', 'style', 'design']):
        themes_text = {
            'Wedding': 'Royal Rose 🌹, Garden Paradise 🌿, Golden Luxury ✨',
            'Temple Festival': 'Traditional Marigold 🌼, Colorful Puja Mandap 🪔, Floral Chariot 🌺',
            'Reception': 'Modern Chic ⚡, Romantic Pink 💕, Royal Blue 👑'
        }
        if event_type and event_type in themes_text:
            return (
                f"🎨 **{event_type} Decoration Themes:**\n\n"
                f"{themes_text[event_type]}\n\n"
                "Try our AI Decoration Preview to see how your venue could look!"
            )
        return (
            "🎨 **Popular Decoration Themes:**\n\n"
            "• **Wedding:** Royal Rose, Garden Paradise, Golden Luxury\n"
            "• **Temple:** Traditional Marigold, Colorful Mandap\n"
            "• **Reception:** Modern Chic, Romantic Pink, Royal Blue\n\n"
            "Tell me your event type for more specific suggestions!"
        )

    elif any(w in msg for w in ['book', 'booking', 'reserve', 'schedule']):
        return (
            "📅 **How to Book:**\n\n"
            "1. Fill in the booking form above\n"
            "2. Select event type, date and location\n"
            "3. Choose your decoration package\n"
            "4. Submit — we'll confirm within 24 hours!\n\n"
            "You can also **WhatsApp us** directly using the button below 💬"
        )

    elif any(w in msg for w in ['contact', 'phone', 'call', 'whatsapp', 'reach']):
        return (
            "📞 **Contact Us:**\n\n"
            "You can reach us via:\n"
            "• Phone / WhatsApp (see the Contact Us button)\n"
            "• Booking form on this page\n"
            "• Visit our Contact page\n\n"
            "We're available Mon–Sat, 9 AM to 7 PM!"
        )

    elif any(w in msg for w in ['hello', 'hi', 'hey', 'namaste', 'good']):
        return (
            "👋 **Hello! Welcome to Event Planner Pro!**\n\n"
            "I can help you with:\n"
            "• 🌸 Decoration ideas and themes\n"
            "• 💰 Budget estimates\n"
            "• 📅 Booking information\n"
            "• 🌺 Flower suggestions\n\n"
            "What type of event are you planning? 😊"
        )

    return (
        "Thank you for your question! 😊\n\n"
        "I can help you with decoration themes, budget estimates, "
        "flower suggestions, and booking information.\n\n"
        "Could you tell me more about your event type "
        "(Wedding, Temple Festival, or Reception)?"
    )