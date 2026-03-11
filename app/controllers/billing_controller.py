from flask import jsonify, request, make_response
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import func, extract
from datetime import datetime, date
from app.extensions import db
from app.models.billing import Billing, BillingItem
from app.models.booking import Booking
from app.utils.pdf_generator import generate_invoice_pdf
import uuid


def _generate_invoice_number():
    year   = datetime.now().year
    unique = str(uuid.uuid4().int)[:6].upper()
    return f"INV-{year}-{unique}"


class BillingController:

    @staticmethod
    def create_billing():
        try:
            data       = request.get_json()
            booking_id = data.get('booking_id')

            if not booking_id:
                return jsonify({
                    'success': False,
                    'message': 'booking_id is required.'
                }), 400

            booking = Booking.query.get(booking_id)
            if not booking:
                return jsonify({
                    'success': False,
                    'message': 'Booking not found.'
                }), 404

            # Check duplicate
            existing = Billing.query.filter_by(booking_id=booking_id).first()
            if existing:
                return jsonify({
                    'success': False,
                    'message': 'Invoice already exists for this booking.',
                    'data': {'id': existing.id}
                }), 409

            # Calculate labour cost
            n_lab   = float(data.get('number_of_labours', 0))
            l_wage  = float(data.get('labour_daily_wage', 0))
            l_days  = float(data.get('labour_days', 1))
            labour_cost = n_lab * l_wage * l_days

            # Material costs
            flower    = float(data.get('flower_cost', 0))
            cloth     = float(data.get('cloth_banner_cost', 0))
            elec      = float(data.get('electrical_materials_cost', 0))
            rental    = float(data.get('rental_items_cost', 0))
            other_mat = float(data.get('other_material_cost', 0))

            # Service items total
            items_data     = data.get('items', [])
            services_total = sum(
                float(i.get('total_price', 0)) for i in items_data
            )

            # Subtotal
            subtotal = (
                services_total + labour_cost +
                flower + cloth + elec + rental + other_mat
            )

            discount  = float(data.get('discount', 0))
            tax_rate  = float(data.get('tax_rate', 0))
            tax_amt   = (subtotal - discount) * tax_rate / 100
            grand     = subtotal - discount + tax_amt
            advance   = float(data.get('advance_paid', 0))
            pending   = max(0.0, grand - advance)

            # Payment status
            if advance >= grand:
                status = 'Paid'
            elif advance > 0:
                status = 'Partially Paid'
            else:
                status = 'Pending'

            billing = Billing(
                invoice_number            = _generate_invoice_number(),
                booking_id                = booking_id,
                customer_name             = data.get('customer_name', booking.customer_name),
                customer_phone            = data.get('customer_phone', booking.customer_phone),
                customer_email            = data.get('customer_email', booking.customer_email),
                customer_address          = data.get('customer_address', booking.event_location),
                event_type                = data.get('event_type', booking.event_type),
                event_date                = data.get('event_date', str(booking.event_date)),
                event_duration            = int(data.get('event_duration', booking.event_duration)),
                decoration_package        = data.get('decoration_package', booking.decoration_package),
                number_of_labours         = int(n_lab),
                labour_daily_wage         = l_wage,
                labour_days               = int(l_days),
                total_labour_cost         = labour_cost,
                flower_cost               = flower,
                cloth_banner_cost         = cloth,
                electrical_materials_cost = elec,
                rental_items_cost         = rental,
                other_material_cost       = other_mat,
                subtotal                  = subtotal,
                discount                  = discount,
                tax_rate                  = tax_rate,
                tax_amount                = tax_amt,
                grand_total               = grand,
                advance_paid              = advance,
                pending_amount            = pending,
                billing_status            = status,
                payment_mode              = data.get('payment_mode', 'Cash'),
                notes                     = data.get('notes', '')
            )
            db.session.add(billing)
            db.session.flush()

            # Add line items
            for item in items_data:
                bi = BillingItem(
                    billing_id   = billing.id,
                    service_name = item.get('service_name', ''),
                    quantity     = float(item.get('quantity', 1)),
                    unit_price   = float(item.get('unit_price', 0)),
                    total_price  = float(item.get('total_price', 0))
                )
                db.session.add(bi)

            # Sync booking payment
            booking.total_amount  = grand
            booking.advance_paid  = advance
            booking.pending_amount= pending
            if status == 'Paid':
                booking.payment_status = 'Paid'
            elif status == 'Partially Paid':
                booking.payment_status = 'Advance Paid'
            else:
                booking.payment_status = 'Pending'

            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Invoice created successfully!',
                'data':    billing.to_dict()
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_all_billings():
        try:
            page     = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 10))
            search   = request.args.get('search', '').strip()
            status   = request.args.get('status', '').strip()
            month    = request.args.get('month', '')
            year_arg = request.args.get('year', '')

            query = Billing.query

            if search:
                query = query.filter(
                    Billing.invoice_number.ilike(f'%{search}%') |
                    Billing.customer_name.ilike(f'%{search}%') |
                    Billing.customer_phone.ilike(f'%{search}%')
                )
            if status:
                query = query.filter(Billing.billing_status == status)
            if month:
                query = query.filter(
                    extract('month', Billing.created_at) == int(month)
                )
            if year_arg:
                query = query.filter(
                    extract('year', Billing.created_at) == int(year_arg)
                )

            query      = query.order_by(Billing.created_at.desc())
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)

            # Summary totals
            total_revenue = db.session.query(
                func.sum(Billing.grand_total)
            ).scalar() or 0
            total_advance = db.session.query(
                func.sum(Billing.advance_paid)
            ).scalar() or 0
            total_pending = db.session.query(
                func.sum(Billing.pending_amount)
            ).scalar() or 0

            return jsonify({
                'success': True,
                'data': {
                    'billings': [b.to_dict() for b in pagination.items],
                    'total':    pagination.total,
                    'pages':    pagination.pages,
                    'page':     page,
                    'summary': {
                        'total_revenue': float(total_revenue),
                        'total_advance': float(total_advance),
                        'total_pending': float(total_pending)
                    }
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_billing(billing_id):
        try:
            billing = Billing.query.get(billing_id)
            if not billing:
                return jsonify({'success': False, 'message': 'Invoice not found.'}), 404

            data          = billing.to_dict()
            data['items'] = [i.to_dict() for i in billing.items]

            # Business info for PDF
            from app.models.admin import Admin
            admin = Admin.query.first()
            if admin:
                data['business_name'] = admin.business_name
                data['business_phone']= admin.phone
                data['business_email']= admin.email
                data['business_address'] = admin.office_address

            return jsonify({'success': True, 'data': data})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_billing_by_booking(booking_id):
        try:
            billing = Billing.query.filter_by(booking_id=booking_id).first()
            if not billing:
                return jsonify({'success': False, 'message': 'No invoice for this booking.'}), 404

            data          = billing.to_dict()
            data['items'] = [i.to_dict() for i in billing.items]
            return jsonify({'success': True, 'data': data})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def update_billing(billing_id):
        try:
            billing = Billing.query.get(billing_id)
            if not billing:
                return jsonify({'success': False, 'message': 'Invoice not found.'}), 404

            data = request.get_json()

            # Simple field updates
            simple_fields = [
                'notes', 'payment_mode', 'decoration_package',
                'number_of_labours', 'labour_daily_wage', 'labour_days'
            ]
            for f in simple_fields:
                if f in data:
                    setattr(billing, f, data[f])

            # Recalculate if financial fields changed
            financial = [
                'flower_cost', 'cloth_banner_cost', 'electrical_materials_cost',
                'rental_items_cost', 'other_material_cost', 'discount', 'tax_rate'
            ]
            recalc = any(f in data for f in financial)

            if recalc:
                for f in financial:
                    if f in data:
                        setattr(billing, f, float(data[f]))

                n_lab   = float(billing.number_of_labours or 0)
                l_wage  = float(billing.labour_daily_wage or 0)
                l_days  = float(billing.labour_days or 1)
                billing.total_labour_cost = n_lab * l_wage * l_days

                items_total = sum(
                    i.total_price for i in billing.items
                )
                billing.subtotal = (
                    items_total +
                    billing.total_labour_cost +
                    float(billing.flower_cost or 0) +
                    float(billing.cloth_banner_cost or 0) +
                    float(billing.electrical_materials_cost or 0) +
                    float(billing.rental_items_cost or 0) +
                    float(billing.other_material_cost or 0)
                )
                billing.tax_amount = (
                    (billing.subtotal - float(billing.discount or 0))
                    * float(billing.tax_rate or 0) / 100
                )
                billing.grand_total = (
                    billing.subtotal
                    - float(billing.discount or 0)
                    + billing.tax_amount
                )
                billing.pending_amount = max(
                    0.0,
                    billing.grand_total - float(billing.advance_paid or 0)
                )
                _update_billing_status(billing)

            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Invoice updated.',
                'data':    billing.to_dict()
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def update_payment(billing_id):
        try:
            billing = Billing.query.get(billing_id)
            if not billing:
                return jsonify({'success': False, 'message': 'Invoice not found.'}), 404

            data    = request.get_json()
            advance = float(data.get('advance_paid', billing.advance_paid or 0))
            mode    = data.get('payment_mode', billing.payment_mode)

            billing.advance_paid  = advance
            billing.pending_amount= max(0.0, float(billing.grand_total) - advance)
            billing.payment_mode  = mode
            _update_billing_status(billing)

            # Sync booking
            if billing.booking_id:
                booking = Booking.query.get(billing.booking_id)
                if booking:
                    booking.advance_paid   = advance
                    booking.pending_amount = billing.pending_amount
                    booking.payment_status = billing.billing_status

            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Payment updated.',
                'data':    billing.to_dict()
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def delete_billing(billing_id):
        try:
            billing = Billing.query.get(billing_id)
            if not billing:
                return jsonify({'success': False, 'message': 'Invoice not found.'}), 404

            # Reset booking payment info
            if billing.booking_id:
                booking = Booking.query.get(billing.booking_id)
                if booking:
                    booking.total_amount   = 0
                    booking.advance_paid   = 0
                    booking.pending_amount = 0
                    booking.payment_status = 'Pending'

            # Cascade deletes items via relationship
            db.session.delete(billing)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Invoice deleted.'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def download_pdf(billing_id):
        try:
            billing = Billing.query.get(billing_id)
            if not billing:
                return jsonify({'success': False, 'message': 'Invoice not found.'}), 404

            data          = billing.to_dict()
            data['items'] = [i.to_dict() for i in billing.items]

            from app.models.admin import Admin
            admin = Admin.query.first()
            if admin:
                data['business_name']    = admin.business_name or 'Event Planner Pro'
                data['business_phone']   = admin.phone or ''
                data['business_email']   = admin.email or ''
                data['business_address'] = admin.office_address or ''

            pdf_bytes = generate_invoice_pdf(data)

            if not pdf_bytes:
                return jsonify({
                    'success': False,
                    'message': 'PDF generation failed. Install reportlab.'
                }), 500

            response = make_response(pdf_bytes)
            response.headers['Content-Type']        = 'application/pdf'
            response.headers['Content-Disposition'] = (
                f'inline; filename="{billing.invoice_number}.pdf"'
            )
            return response

        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_payment_statement():
        try:
            today    = date.today()
            month    = int(request.args.get('month', today.month))
            year_arg = int(request.args.get('year', today.year))

            billings = Billing.query.filter(
                extract('month', Billing.created_at) == month,
                extract('year',  Billing.created_at) == year_arg
            ).all()

            paid         = [b for b in billings if b.billing_status == 'Paid']
            partial      = [b for b in billings if b.billing_status == 'Partially Paid']
            pending_list = [b for b in billings if b.billing_status == 'Pending']

            return jsonify({
                'success': True,
                'data': {
                    'month':        month,
                    'year':         year_arg,
                    'total':        len(billings),
                    'paid_count':   len(paid),
                    'partial_count':len(partial),
                    'pending_count':len(pending_list),
                    'total_revenue':sum(float(b.grand_total or 0) for b in billings),
                    'total_collected': sum(float(b.advance_paid or 0) for b in billings),
                    'total_pending': sum(float(b.pending_amount or 0) for b in billings)
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_booking_for_billing(booking_id):
        """Fetch booking details to pre-fill billing form."""
        try:
            booking = Booking.query.get(booking_id)
            if not booking:
                return jsonify({'success': False, 'message': 'Booking not found.'}), 404

            has_billing = Billing.query.filter_by(booking_id=booking_id).first() is not None
            data = booking.to_dict()
            data['has_billing'] = has_billing
            return jsonify({'success': True, 'data': data})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500


# ── Helper ────────────────────────────────────────────
def _update_billing_status(billing):
    grand   = float(billing.grand_total or 0)
    advance = float(billing.advance_paid or 0)
    if advance >= grand > 0:
        billing.billing_status = 'Paid'
    elif advance > 0:
        billing.billing_status = 'Partially Paid'
    else:
        billing.billing_status = 'Pending'