from flask import jsonify, request
from sqlalchemy import func, extract
from datetime import datetime, date
from app.extensions import db
from app.models.labour import Labour
from app.models.attendance import Attendance
from app.models.expense import Expense
from app.utils.file_handler import save_uploaded_file
import uuid


class LabourController:

    # ── Add Labour ────────────────────────────────────
    @staticmethod
    def add_labour():
        try:
            name       = (request.form.get('name') or '').strip()
            phone      = (request.form.get('phone') or '').strip()
            daily_wage = request.form.get('daily_wage', 0)
            age        = request.form.get('age', 0)
            address    = (request.form.get('address') or '').strip()
            bank_name  = (request.form.get('bank_name') or '').strip()
            bank_acc   = (request.form.get('bank_account_number') or '').strip()
            bank_holder= (request.form.get('bank_account_name') or '').strip()

            if not name or not phone or not daily_wage:
                return jsonify({
                    'success': False,
                    'message': 'Name, phone and daily wage are required.'
                }), 400

            if Labour.query.filter_by(phone=phone).first():
                return jsonify({
                    'success': False,
                    'message': 'Phone number already registered.'
                }), 409

            photo_path = None
            photo_file = request.files.get('photo')
            if photo_file and photo_file.filename:
                photo_path = save_uploaded_file(
                    photo_file, 'labour_photos', max_size=(400, 400)
                )

            labour = Labour(
                name               = name,
                phone              = phone,
                daily_wage         = float(daily_wage),
                age                = int(age) if age else None,
                address            = address,
                photo_path         = photo_path,
                bank_name          = bank_name,
                bank_account_number= bank_acc,
                bank_account_name  = bank_holder
            )
            db.session.add(labour)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Labour added successfully!',
                'data':    labour.to_dict()
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    # ── Get All Labour ────────────────────────────────
    @staticmethod
    def get_all_labour():
        try:
            page      = int(request.args.get('page', 1))
            per_page  = int(request.args.get('per_page', 9))
            search    = request.args.get('search', '').strip()
            is_active = request.args.get('is_active', '')

            query = Labour.query

            if search:
                query = query.filter(
                    Labour.name.ilike(f'%{search}%') |
                    Labour.phone.ilike(f'%{search}%')
                )
            if is_active != '':
                active_bool = is_active.lower() == 'true'
                query = query.filter(Labour.is_active == active_bool)

            query      = query.order_by(Labour.name.asc())
            pagination = query.paginate(
                page=page, per_page=per_page, error_out=False
            )

            labours_data = []
            for l in pagination.items:
                d = l.to_dict()

                # Wage stats
                stats = db.session.query(
                    func.sum(Attendance.wage_amount).label('total_earned'),
                    func.sum(Attendance.advance_amount).label('total_advance'),
                    func.count(Attendance.id).label('days_worked')
                ).filter(
                    Attendance.labour_id == l.id,
                    Attendance.is_present == True
                ).first()

                d['total_earned']     = float(stats.total_earned or 0)
                d['total_advance']    = float(stats.total_advance or 0)
                d['total_days_worked']= int(stats.days_worked or 0)
                d['pending_balance']  = max(
                    0.0,
                    float(stats.total_earned or 0) - float(stats.total_advance or 0)
                )
                labours_data.append(d)

            return jsonify({
                'success': True,
                'data': {
                    'labours': labours_data,
                    'total':   pagination.total,
                    'pages':   pagination.pages,
                    'page':    page
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    # ── Get Single Labour ─────────────────────────────
    @staticmethod
    def get_labour(labour_id):
        try:
            labour = Labour.query.get(labour_id)
            if not labour:
                return jsonify({'success': False, 'message': 'Labour not found.'}), 404

            data = labour.to_dict()

            # Wage stats
            stats = db.session.query(
                func.sum(Attendance.wage_amount).label('total_earned'),
                func.sum(Attendance.advance_amount).label('total_advance'),
                func.count(Attendance.id).label('days_worked')
            ).filter(
                Attendance.labour_id == labour_id,
                Attendance.is_present == True
            ).first()

            data['total_earned']     = float(stats.total_earned or 0)
            data['total_advance']    = float(stats.total_advance or 0)
            data['total_days_worked']= int(stats.days_worked or 0)
            data['pending_balance']  = max(
                0.0,
                float(stats.total_earned or 0) - float(stats.total_advance or 0)
            )

            # Recent attendance (last 30 records)
            recent = Attendance.query.filter_by(
                labour_id=labour_id
            ).order_by(Attendance.date.desc()).limit(30).all()

            data['recent_attendance'] = [a.to_dict() for a in recent]

            return jsonify({'success': True, 'data': data})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    # ── Update Labour ─────────────────────────────────
    @staticmethod
    def update_labour(labour_id):
        try:
            labour = Labour.query.get(labour_id)
            if not labour:
                return jsonify({'success': False, 'message': 'Labour not found.'}), 404

            # Handle form or JSON
            if request.content_type and 'multipart' in request.content_type:
                data = request.form.to_dict()
                photo = request.files.get('photo')
                if photo and photo.filename:
                    path = save_uploaded_file(photo, 'labour_photos', max_size=(400,400))
                    if path:
                        labour.photo_path = path
            else:
                data = request.get_json() or {}

            fields = [
                'name', 'phone', 'daily_wage', 'age',
                'address', 'bank_name', 'bank_account_number', 'bank_account_name',
                'is_active'
            ]
            for f in fields:
                if f in data and data[f] is not None:
                    val = data[f]
                    if f in ('daily_wage',):
                        val = float(val)
                    elif f in ('age',):
                        val = int(val) if val else None
                    elif f == 'is_active':
                        # Accept bool or string 'true'/'false'
                        if isinstance(val, str):
                            val = val.lower() == 'true'
                        else:
                            val = bool(val)
                    setattr(labour, f, val)

            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Labour updated.',
                'data':    labour.to_dict()
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    # ── Delete Labour (soft) ──────────────────────────
    @staticmethod
    def delete_labour(labour_id):
        try:
            labour = Labour.query.get(labour_id)
            if not labour:
                return jsonify({'success': False, 'message': 'Labour not found.'}), 404

            labour.is_active = False
            db.session.commit()
            return jsonify({'success': True, 'message': 'Labour deactivated.'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    # ── Mark Attendance ───────────────────────────────
    @staticmethod
    def mark_attendance():
        try:
            data       = request.get_json()
            labour_id  = data.get('labour_id')
            att_date   = data.get('date', str(date.today()))
            is_present = data.get('is_present', True)
            half_day   = data.get('half_day', False)
            advance    = float(data.get('advance_amount', 0))

            labour = Labour.query.get(labour_id)
            if not labour:
                return jsonify({'success': False, 'message': 'Labour not found.'}), 404

            # Wage calculation
            if is_present:
                wage = labour.daily_wage / 2 if half_day else labour.daily_wage
            else:
                wage = 0.0

            # Upsert attendance
            existing = Attendance.query.filter_by(
                labour_id=labour_id, date=att_date
            ).first()

            if existing:
                existing.is_present     = is_present
                existing.half_day       = half_day
                existing.wage_amount    = wage
                existing.advance_amount = advance
                att = existing
            else:
                att = Attendance(
                    labour_id     = labour_id,
                    date          = att_date,
                    is_present    = is_present,
                    half_day      = half_day,
                    wage_amount   = wage,
                    advance_amount= advance
                )
                db.session.add(att)

            # Auto-create Labour Expense for wage
            if is_present and wage > 0:
                _upsert_labour_expense(labour_id, labour.name, att_date, wage)

            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Attendance marked.',
                'data':    att.to_dict()
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    # ── Bulk Attendance ───────────────────────────────
    @staticmethod
    def bulk_attendance():
        try:
            data     = request.get_json()
            att_date = data.get('date', str(date.today()))
            att_list = data.get('attendance_list', [])

            if not att_list:
                return jsonify({'success': False, 'message': 'attendance_list is empty.'}), 400

            updated = 0
            for item in att_list:
                labour_id  = item.get('labour_id')
                is_present = item.get('is_present', False)
                half_day   = item.get('half_day', False)
                advance    = float(item.get('advance_amount', 0))

                labour = Labour.query.get(labour_id)
                if not labour:
                    continue

                wage = 0.0
                if is_present:
                    wage = labour.daily_wage / 2 if half_day else labour.daily_wage

                existing = Attendance.query.filter_by(
                    labour_id=labour_id, date=att_date
                ).first()

                if existing:
                    existing.is_present     = is_present
                    existing.half_day       = half_day
                    existing.wage_amount    = wage
                    existing.advance_amount = advance
                else:
                    att = Attendance(
                        labour_id     = labour_id,
                        date          = att_date,
                        is_present    = is_present,
                        half_day      = half_day,
                        wage_amount   = wage,
                        advance_amount= advance
                    )
                    db.session.add(att)

                if is_present and wage > 0:
                    _upsert_labour_expense(labour_id, labour.name, att_date, wage)

                updated += 1

            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'Attendance saved for {updated} labours.'
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    # ── Get Attendance by Labour ──────────────────────
    @staticmethod
    def get_attendance(labour_id):
        try:
            labour = Labour.query.get(labour_id)
            if not labour:
                return jsonify({'success': False, 'message': 'Labour not found.'}), 404

            month = request.args.get('month', '')
            year  = request.args.get('year', str(date.today().year))

            query = Attendance.query.filter_by(labour_id=labour_id)
            if month:
                query = query.filter(
                    extract('month', Attendance.date) == int(month)
                )
            if year:
                query = query.filter(
                    extract('year', Attendance.date) == int(year)
                )

            records = query.order_by(Attendance.date.desc()).all()

            present_days   = sum(1 for r in records if r.is_present and not r.half_day)
            half_days      = sum(1 for r in records if r.is_present and r.half_day)
            total_wages    = sum(float(r.wage_amount or 0) for r in records)
            total_advance  = sum(float(r.advance_amount or 0) for r in records)
            pending_balance= max(0.0, total_wages - total_advance)

            return jsonify({
                'success': True,
                'data': {
                    'labour':          labour.to_dict(),
                    'attendance':      [r.to_dict() for r in records],
                    'present_days':    present_days,
                    'half_days':       half_days,
                    'total_wages':     total_wages,
                    'total_advance':   total_advance,
                    'pending_balance': pending_balance
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    # ── Daily Summary ─────────────────────────────────
    @staticmethod
    def get_daily_summary():
        try:
            att_date = request.args.get('date', str(date.today()))

            records = db.session.query(Attendance, Labour).join(
                Labour, Attendance.labour_id == Labour.id
            ).filter(Attendance.date == att_date).all()

            details = []
            for att, lab in records:
                d = att.to_dict()
                d['labour_name']  = lab.name
                d['labour_phone'] = lab.phone
                d['daily_wage']   = lab.daily_wage
                details.append(d)

            present_count = sum(1 for a, _ in records if a.is_present)
            absent_count  = sum(1 for a, _ in records if not a.is_present)
            total_wages   = sum(float(a.wage_amount or 0) for a, _ in records)

            return jsonify({
                'success': True,
                'data': {
                    'date':          att_date,
                    'details':       details,
                    'present_count': present_count,
                    'absent_count':  absent_count,
                    'total_wages':   total_wages
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    # ── Labour Statement ──────────────────────────────
    @staticmethod
    def get_statement(labour_id):
        try:
            labour = Labour.query.get(labour_id)
            if not labour:
                return jsonify({'success': False, 'message': 'Labour not found.'}), 404

            from_date = request.args.get('from_date', '')
            to_date   = request.args.get('to_date', '')

            query = Attendance.query.filter_by(labour_id=labour_id)
            if from_date:
                query = query.filter(Attendance.date >= from_date)
            if to_date:
                query = query.filter(Attendance.date <= to_date)

            records       = query.order_by(Attendance.date.asc()).all()
            total_wages   = sum(float(r.wage_amount or 0) for r in records)
            total_advance = sum(float(r.advance_amount or 0) for r in records)

            return jsonify({
                'success': True,
                'data': {
                    'labour':        labour.to_dict(),
                    'records':       [r.to_dict() for r in records],
                    'total_wages':   total_wages,
                    'total_advance': total_advance,
                    'balance':       max(0.0, total_wages - total_advance)
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    # ── Add Advance Payment ───────────────────────────
    @staticmethod
    def add_advance(labour_id):
        try:
            labour = Labour.query.get(labour_id)
            if not labour:
                return jsonify({'success': False, 'message': 'Labour not found.'}), 404

            data   = request.get_json()
            amount = float(data.get('amount', 0))
            note   = data.get('note', 'Advance payment')
            pay_date = data.get('date', str(date.today()))

            if amount <= 0:
                return jsonify({'success': False, 'message': 'Amount must be > 0.'}), 400

            # Add as standalone attendance advance record
            att = Attendance(
                labour_id     = labour_id,
                date          = pay_date,
                is_present    = False,
                half_day      = False,
                wage_amount   = 0,
                advance_amount= amount,
                notes         = note
            )
            db.session.add(att)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': f'Advance ₹{amount} recorded for {labour.name}.'
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500


# ── Helper ────────────────────────────────────────────
def _upsert_labour_expense(labour_id, labour_name, exp_date, wage):
    """Auto-create/update Labour Expense when attendance is marked."""
    existing = Expense.query.filter_by(
        labour_id=labour_id,
        expense_date=exp_date,
        category='Labour'
    ).first()

    if existing:
        existing.amount      = wage
        existing.description = f'Daily wage for {labour_name}'
    else:
        exp = Expense(
            expense_type = 'Labour Expenses',
            category     = 'Labour',
            amount       = wage,
            expense_date = exp_date,
            description  = f'Daily wage for {labour_name}',
            labour_id    = labour_id,
            notes        = 'Auto-generated from attendance'
        )
        db.session.add(exp)