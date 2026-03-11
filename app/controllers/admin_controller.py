from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import func, extract
from datetime import datetime, date
from app.extensions import db
from app.models.admin import Admin
from app.models.customer import Customer
from app.models.booking import Booking
from app.models.billing import Billing
from app.models.expense import Expense
from app.models.labour import Labour
from app.models.attendance import Attendance
from app.utils.file_handler import save_uploaded_file


class AdminController:

    # ── Dashboard Stats ───────────────────────────────
    @staticmethod
    def get_dashboard_stats():
        try:
            today     = date.today()
            this_year = today.year
            this_month= today.month

            # Booking counts
            total_bookings   = Booking.query.count()
            pending_bookings = Booking.query.filter_by(status='Pending').count()
            today_events     = Booking.query.filter_by(
                event_date=today.strftime('%Y-%m-%d')
            ).count()

            # Revenue
            revenue_row = db.session.query(
                func.sum(Billing.grand_total)
            ).scalar() or 0

            advance_row = db.session.query(
                func.sum(Billing.advance_paid)
            ).scalar() or 0

            pending_payment = db.session.query(
                func.sum(Billing.pending_amount)
            ).scalar() or 0

            # Expenses
            total_expenses = db.session.query(
                func.sum(Expense.amount)
            ).scalar() or 0

            labour_wages = db.session.query(
                func.sum(Attendance.wage_amount)
            ).scalar() or 0

            # Customers
            total_customers = Customer.query.count()

            # Profit
            net_profit = float(revenue_row) - float(total_expenses)

            # Booking status counts
            accepted_bookings  = Booking.query.filter_by(status='Accepted').count()
            completed_bookings = Booking.query.filter_by(status='Completed').count()
            rejected_bookings  = Booking.query.filter_by(status='Rejected').count()

            return jsonify({
                'success': True,
                'data': {
                    'total_bookings':    total_bookings,
                    'pending_bookings':  pending_bookings,
                    'today_events':      today_events,
                    'total_customers':   total_customers,
                    'total_revenue':     float(revenue_row),
                    'advance_paid':      float(advance_row),
                    'advance_payments':  float(advance_row),   # alias for dashboard
                    'pending_payment':   float(pending_payment),
                    'pending_payments':  float(pending_payment), # alias for dashboard
                    'total_expenses':    float(total_expenses),
                    'labour_wages':      float(labour_wages),
                    'net_profit':        net_profit,
                    'profit':            net_profit,            # alias for dashboard
                    'booking_status': {
                        'pending':   pending_bookings,
                        'accepted':  accepted_bookings,
                        'completed': completed_bookings,
                        'rejected':  rejected_bookings
                    }
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_revenue_chart():
        try:
            today      = date.today()
            year       = int(request.args.get('year', today.year))
            revenue_by_month = [0.0] * 12
            advance_by_month = [0.0] * 12

            rows = db.session.query(
                extract('month', Billing.created_at).label('month'),
                func.sum(Billing.grand_total).label('revenue'),
                func.sum(Billing.advance_paid).label('advance')
            ).filter(
                extract('year', Billing.created_at) == year
            ).group_by('month').all()

            for row in rows:
                idx = int(row.month) - 1
                revenue_by_month[idx] = float(row.revenue or 0)
                advance_by_month[idx] = float(row.advance or 0)

            MONTHS = ['Jan','Feb','Mar','Apr','May','Jun',
                      'Jul','Aug','Sep','Oct','Nov','Dec']

            return jsonify({
                'success': True,
                'data': {
                    'revenue': revenue_by_month,
                    'advance': advance_by_month,
                    'year':    year,
                    'labels':  MONTHS
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_expense_chart():
        try:
            today = date.today()
            year  = int(request.args.get('year', today.year))
            labour_by_month = [0.0] * 12
            other_by_month  = [0.0] * 12

            rows = db.session.query(
                extract('month', Expense.expense_date).label('month'),
                Expense.category,
                func.sum(Expense.amount).label('total')
            ).filter(
                extract('year', Expense.expense_date) == year
            ).group_by('month', Expense.category).all()

            for row in rows:
                idx = int(row.month) - 1
                if row.category == 'Labour':
                    labour_by_month[idx] = float(row.total or 0)
                else:
                    other_by_month[idx] = float(row.total or 0)

            MONTHS = ['Jan','Feb','Mar','Apr','May','Jun',
                      'Jul','Aug','Sep','Oct','Nov','Dec']

            return jsonify({
                'success': True,
                'data': {
                    'labour':          labour_by_month,
                    'other':           other_by_month,
                    'labour_expenses': labour_by_month,  # alias
                    'other_expenses':  other_by_month,   # alias
                    'year':            year,
                    'labels':          MONTHS
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_booking_trends():
        try:
            today = date.today()
            year  = int(request.args.get('year', today.year))
            monthly_counts = [0] * 12

            rows = db.session.query(
                extract('month', Booking.created_at).label('month'),
                func.count(Booking.id).label('count')
            ).filter(
                extract('year', Booking.created_at) == year
            ).group_by('month').all()

            for row in rows:
                monthly_counts[int(row.month) - 1] = int(row.count)

            # Event type distribution
            type_rows = db.session.query(
                Booking.event_type,
                func.count(Booking.id).label('count')
            ).group_by(Booking.event_type).all()

            event_types = {r.event_type: int(r.count) for r in type_rows}

            return jsonify({
                'success': True,
                'data': {
                    'monthly': monthly_counts,
                    'by_type': event_types,
                    'year':    year
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_profit_chart():
        try:
            today = date.today()
            year  = int(request.args.get('year', today.year))
            profit_by_month = [0.0] * 12

            rev_rows = db.session.query(
                extract('month', Billing.created_at).label('month'),
                func.sum(Billing.grand_total).label('rev')
            ).filter(
                extract('year', Billing.created_at) == year
            ).group_by('month').all()

            exp_rows = db.session.query(
                extract('month', Expense.expense_date).label('month'),
                func.sum(Expense.amount).label('exp')
            ).filter(
                extract('year', Expense.expense_date) == year
            ).group_by('month').all()

            rev_map = {int(r.month): float(r.rev or 0) for r in rev_rows}
            exp_map = {int(r.month): float(r.exp or 0) for r in exp_rows}

            for m in range(1, 13):
                profit_by_month[m - 1] = rev_map.get(m, 0) - exp_map.get(m, 0)

            MONTHS = ['Jan','Feb','Mar','Apr','May','Jun',
                      'Jul','Aug','Sep','Oct','Nov','Dec']

            return jsonify({
                'success': True,
                'data': {'profit': profit_by_month, 'year': year, 'labels': MONTHS}
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_recent_activity():
        try:
            recent_bookings = Booking.query.order_by(
                Booking.created_at.desc()
            ).limit(5).all()

            recent_customers = Customer.query.order_by(
                Customer.created_at.desc()
            ).limit(5).all()

            recent_billings = Billing.query.order_by(
                Billing.created_at.desc()
            ).limit(5).all()

            return jsonify({
                'success': True,
                'data': {
                    'recent_bookings':  [b.to_dict() for b in recent_bookings],
                    'recent_customers': [c.to_dict() for c in recent_customers],
                    'recent_billings':  [b.to_dict() for b in recent_billings]
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    # ── Admin Profile ─────────────────────────────────
    @staticmethod
    def get_profile():
        try:
            admin_id = int(get_jwt_identity())
            admin    = Admin.query.get(admin_id)
            if not admin:
                return jsonify({'success': False, 'message': 'Admin not found.'}), 404
            return jsonify({'success': True, 'data': admin.to_dict()})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def update_profile():
        try:
            admin_id = int(get_jwt_identity())
            admin    = Admin.query.get(admin_id)
            if not admin:
                return jsonify({'success': False, 'message': 'Admin not found.'}), 404

            # Handle both JSON and form data
            if request.content_type and 'multipart' in request.content_type:
                data = request.form.to_dict()
                logo = request.files.get('logo')
                if logo and logo.filename:
                    logo_path = save_uploaded_file(logo, 'logo', max_size=(400, 400))
                    if logo_path:
                        admin.logo_path = logo_path
            else:
                data = request.get_json() or {}

            # Update fields
            fields = [
                'business_name', 'phone', 'email', 'office_address',
                'upi_id', 'bank_name', 'bank_account_number', 'bank_ifsc'
            ]
            for field in fields:
                if field in data and data[field] is not None:
                    setattr(admin, field, data[field])

            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Profile updated.',
                'data': admin.to_dict()
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    # ── Customers ─────────────────────────────────────
    @staticmethod
    def get_all_customers():
        try:
            page      = int(request.args.get('page', 1))
            per_page  = int(request.args.get('per_page', 15))
            search    = request.args.get('search', '').strip()
            is_active = request.args.get('is_active', '').strip()

            query = Customer.query
            if search:
                query = query.filter(
                    Customer.full_name.ilike(f'%{search}%') |
                    Customer.phone.ilike(f'%{search}%') |
                    Customer.email.ilike(f'%{search}%')
                )
            if is_active != '':
                query = query.filter(
                    Customer.is_active == (is_active.lower() == 'true')
                )

            query      = query.order_by(Customer.created_at.desc())
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)

            return jsonify({
                'success': True,
                'data': {
                    'customers': [c.to_dict() for c in pagination.items],
                    'total':     pagination.total,
                    'pages':     pagination.pages,
                    'page':      page
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def toggle_customer_status(customer_id):
        try:
            customer = Customer.query.get(customer_id)
            if not customer:
                return jsonify({'success': False, 'message': 'Customer not found.'}), 404

            customer.is_active = not customer.is_active
            db.session.commit()

            status = 'activated' if customer.is_active else 'deactivated'
            return jsonify({
                'success': True,
                'message': f'Customer {status}.',
                'data': {'is_active': customer.is_active}
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def delete_customer(customer_id):
        try:
            customer = Customer.query.get(customer_id)
            if not customer:
                return jsonify({'success': False, 'message': 'Customer not found.'}), 404

            # Check if customer has bookings
            from app.models.booking import Booking
            booking_count = Booking.query.filter_by(customer_id=customer_id).count()
            if booking_count > 0:
                # Soft delete: deactivate instead of hard delete
                customer.is_active = False
                db.session.commit()
                return jsonify({
                    'success': True,
                    'message': f'Customer deactivated (has {booking_count} booking(s), cannot permanently delete).'
                })

            db.session.delete(customer)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Customer deleted successfully.'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500