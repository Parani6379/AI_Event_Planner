from flask import jsonify
from app.extensions import db
from app.models.admin import Admin
from app.models.design import Design
from app.models.booking import Booking


class CustomerController:

    @staticmethod
    def get_home_data():
        """Public homepage data: featured designs + stats."""
        try:
            featured = Design.query.filter_by(
                is_featured=True,
                is_active=True
            ).order_by(Design.view_count.desc()).limit(8).all()

            total_designs = Design.query.filter_by(is_active=True).count()

            return jsonify({
                'success': True,
                'data': {
                    'featured_designs': [d.to_dict() for d in featured],
                    'stats': {
                        'total_designs': total_designs,
                    }
                }
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500

    @staticmethod
    def get_contact_info():
        """Public business contact info."""
        try:
            admin = Admin.query.first()
            if not admin:
                return jsonify({
                    'success': True,
                    'data': {
                        'business_name': 'Event Planner Pro',
                        'phone': '',
                        'email': '',
                        'address': '',
                        'upi_id': ''
                    }
                })

            return jsonify({
                'success': True,
                'data': {
                    'business_name': admin.business_name or 'Event Planner Pro',
                    'phone':   admin.phone or '',
                    'email':   admin.email or '',
                    'address': admin.office_address or '',
                    'upi_id':  admin.upi_id or ''
                }
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500