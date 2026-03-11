from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, get_jwt
from sqlalchemy import func, extract
from datetime import datetime, date
from app.extensions import db
from app.models.booking import Booking
from app.models.customer import Customer
from app.models.labour import Labour
import uuid


def _booking_number():
    year   = datetime.now().year
    suffix = str(uuid.uuid4().int)[:5].upper()
    return f"BK-{year}-{suffix}"


class BookingController:

    @staticmethod
    def create_booking():
        try:
            claims     = get_jwt()
            role       = claims.get('role')
            user_id    = int(get_jwt_identity())
            data       = request.get_json() or {}

            event_type = (data.get('event_type') or '').strip()
            event_date = (data.get('event_date') or '').strip()
            location   = (data.get('event_location') or '').strip()

            if not all([event_type, event_date, location]):
                return jsonify({'success': False,
                                'message': 'event_type, event_date and event_location are required.'}), 400

            # Validate future date
            try:
                evt_dt = datetime.strptime(event_date, '%Y-%m-%d').date()
                if evt_dt <= date.today():
                    return jsonify({'success': False,
                                    'message': 'Event date must be a future date.'}), 400
            except ValueError:
                return jsonify({'success': False, 'message': 'Invalid date format (use YYYY-MM-DD).'}), 400

            if role == 'customer':
                customer = Customer.query.get(user_id)
                if not customer:
                    return jsonify({'success': False, 'message': 'Customer not found.'}), 404
                customer_name  = customer.full_name
                customer_phone = customer.phone
                customer_email = customer.email
                cust_id        = customer.id
            else:
                customer_name  = (data.get('customer_name') or '').strip()
                customer_phone = (data.get('customer_phone') or '').strip()
                customer_email = (data.get('customer_email') or '').strip()
                cust_id        = data.get('customer_id')
                if not customer_name or not customer_phone:
                    return jsonify({'success': False,
                                    'message': 'customer_name and customer_phone are required.'}), 400

            booking = Booking(
                booking_number        = _booking_number(),
                customer_id           = cust_id,
                customer_name         = customer_name,
                customer_phone        = customer_phone,
                customer_email        = customer_email,
                event_type            = event_type,
                event_date            = event_date,
                event_duration        = int(data.get('event_duration', 1)),
                event_location        = location,
                decoration_package    = data.get('decoration_package', ''),
                special_requirements  = data.get('special_requirements', ''),
                status                = 'Pending',
                payment_status        = 'Pending',
                total_amount          = 0,
                advance_paid          = 0,
                pending_amount        = 0,
            )
            db.session.add(booking)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Booking submitted! We will confirm within 24 hours.',
                'data':    booking.to_dict()
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_all_bookings():
        try:
            page     = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 10))
            search   = request.args.get('search', '').strip()
            status   = request.args.get('status', '').strip()
            evt_type = request.args.get('event_type', '').strip()
            month    = request.args.get('month', '')
            year_arg = request.args.get('year', '')

            query = Booking.query

            if search:
                query = query.filter(
                    Booking.customer_name.ilike(f'%{search}%')  |
                    Booking.customer_phone.ilike(f'%{search}%') |
                    Booking.booking_number.ilike(f'%{search}%') |
                    Booking.event_location.ilike(f'%{search}%')
                )
            if status:
                query = query.filter(Booking.status == status)
            if evt_type:
                query = query.filter(Booking.event_type == evt_type)
            if month:
                query = query.filter(extract('month', Booking.created_at) == int(month))
            if year_arg:
                query = query.filter(extract('year', Booking.created_at) == int(year_arg))

            pagination = query.order_by(Booking.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False)

            return jsonify({'success': True, 'data': {
                'bookings': [b.to_dict() for b in pagination.items],
                'total': pagination.total, 'pages': pagination.pages, 'page': page
            }})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_booking(booking_id):
        try:
            booking = Booking.query.get(booking_id)
            if not booking:
                return jsonify({'success': False, 'message': 'Booking not found.'}), 404
            data = booking.to_dict()
            assigned = []
            for bl in booking.assigned_labours:
                lab = Labour.query.get(bl.labour_id)
                if lab:
                    assigned.append({
                        'labour_id': lab.id, 'labour_name': lab.name,
                        'labour_phone': lab.phone, 'daily_wage': lab.daily_wage
                    })
            data['assigned_labours'] = assigned
            return jsonify({'success': True, 'data': data})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def update_booking(booking_id):
        try:
            booking = Booking.query.get(booking_id)
            if not booking:
                return jsonify({'success': False, 'message': 'Booking not found.'}), 404
            data = request.get_json() or {}
            for f in ['event_type','event_date','event_duration',
                      'event_location','decoration_package','special_requirements']:
                if f in data:
                    setattr(booking, f, data[f])
            db.session.commit()
            return jsonify({'success': True, 'message': 'Booking updated.', 'data': booking.to_dict()})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def update_status(booking_id):
        try:
            booking = Booking.query.get(booking_id)
            if not booking:
                return jsonify({'success': False, 'message': 'Booking not found.'}), 404
            data   = request.get_json() or {}
            status = data.get('status', '').strip()
            valid  = ['Pending', 'Accepted', 'Rejected', 'Completed', 'Cancelled']
            if status not in valid:
                return jsonify({'success': False,
                                'message': f'Status must be one of: {", ".join(valid)}'}), 400
            booking.status      = status
            booking.admin_notes = data.get('admin_notes', booking.admin_notes)
            db.session.commit()
            return jsonify({'success': True, 'message': f'Booking {status}.', 'data': booking.to_dict()})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def update_payment(booking_id):
        try:
            booking = Booking.query.get(booking_id)
            if not booking:
                return jsonify({'success': False, 'message': 'Booking not found.'}), 404
            data    = request.get_json() or {}
            total   = float(data.get('total_amount',  booking.total_amount  or 0))
            advance = float(data.get('advance_paid',  booking.advance_paid  or 0))
            pending = max(0.0, total - advance)
            booking.total_amount   = total
            booking.advance_paid   = advance
            booking.pending_amount = pending
            if advance >= total > 0:
                booking.payment_status = 'Paid'
            elif advance > 0:
                booking.payment_status = 'Advance Paid'
            else:
                booking.payment_status = 'Pending'
            db.session.commit()
            return jsonify({'success': True, 'message': 'Payment updated.', 'data': booking.to_dict()})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def assign_labour(booking_id):
        try:
            from app.models.booking import BookingLabour
            booking = Booking.query.get(booking_id)
            if not booking:
                return jsonify({'success': False, 'message': 'Booking not found.'}), 404
            data       = request.get_json() or {}
            labour_ids = data.get('labour_ids', [])
            added = 0
            for lid in labour_ids:
                if not BookingLabour.query.filter_by(booking_id=booking_id, labour_id=lid).first():
                    db.session.add(BookingLabour(booking_id=booking_id, labour_id=lid))
                    added += 1
            db.session.commit()
            return jsonify({'success': True, 'message': f'{added} labour(s) assigned.'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def remove_labour(booking_id, labour_id):
        try:
            from app.models.booking import BookingLabour
            bl = BookingLabour.query.filter_by(booking_id=booking_id, labour_id=labour_id).first()
            if not bl:
                return jsonify({'success': False, 'message': 'Assignment not found.'}), 404
            db.session.delete(bl)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Labour removed.'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_my_bookings():
        try:
            customer_id = int(get_jwt_identity())
            page        = int(request.args.get('page', 1))
            per_page    = int(request.args.get('per_page', 10))
            pagination  = Booking.query.filter_by(customer_id=customer_id)\
                .order_by(Booking.created_at.desc())\
                .paginate(page=page, per_page=per_page, error_out=False)
            return jsonify({'success': True, 'data': {
                'bookings': [b.to_dict() for b in pagination.items],
                'total': pagination.total, 'pages': pagination.pages
            }})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def cancel_booking(booking_id):
        try:
            customer_id = int(get_jwt_identity())
            booking     = Booking.query.get(booking_id)
            if not booking:
                return jsonify({'success': False, 'message': 'Booking not found.'}), 404
            if booking.customer_id != customer_id:
                return jsonify({'success': False, 'message': 'Unauthorized.'}), 403
            if booking.status != 'Pending':
                return jsonify({'success': False,
                                'message': 'Only pending bookings can be cancelled.'}), 400
            booking.status = 'Cancelled'
            db.session.commit()
            return jsonify({'success': True, 'message': 'Booking cancelled.'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_today_bookings():
        try:
            today   = str(date.today())
            records = Booking.query.filter(Booking.event_date == today).all()
            return jsonify({'success': True, 'data': {
                'date': today, 'bookings': [b.to_dict() for b in records], 'count': len(records)
            }})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_upcoming_bookings():
        try:
            today   = str(date.today())
            records = Booking.query.filter(
                Booking.event_date > today,
                Booking.status.in_(['Pending', 'Accepted'])
            ).order_by(Booking.event_date.asc()).limit(10).all()
            return jsonify({'success': True, 'data': {'bookings': [b.to_dict() for b in records]}})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_stats():
        try:
            today = str(date.today())
            return jsonify({'success': True, 'data': {
                'total':     Booking.query.count(),
                'pending':   Booking.query.filter_by(status='Pending').count(),
                'accepted':  Booking.query.filter_by(status='Accepted').count(),
                'completed': Booking.query.filter_by(status='Completed').count(),
                'rejected':  Booking.query.filter_by(status='Rejected').count(),
                'today':     Booking.query.filter(Booking.event_date == today).count()
            }})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
