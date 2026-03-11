from flask import jsonify, request
from sqlalchemy import func, extract
from datetime import datetime, date
from app.extensions import db
from app.models.expense import Expense
from app.utils.file_handler import save_receipt


EXPENSE_TYPES = [
    'Labour Expenses',
    'Decoration Materials',
    'Transport Charges',
    'Equipment Rental',
    'Food / Miscellaneous'
]


class ExpenseController:

    @staticmethod
    def add_expense():
        try:
            # Accept form data (with file) or JSON
            if request.content_type and 'multipart' in request.content_type:
                data         = request.form.to_dict()
                receipt_file = request.files.get('receipt')
                receipt_path = None
                if receipt_file and receipt_file.filename:
                    receipt_path = save_receipt(receipt_file)
            else:
                data         = request.get_json() or {}
                receipt_path = None

            expense_type = (data.get('expense_type') or '').strip()
            amount       = data.get('amount')
            expense_date = data.get('expense_date', str(date.today()))
            description  = (data.get('description') or '').strip()
            notes        = (data.get('notes') or '').strip()
            booking_id   = data.get('booking_id')
            labour_id    = data.get('labour_id')

            if not expense_type or not amount:
                return jsonify({
                    'success': False,
                    'message': 'expense_type and amount are required.'
                }), 400

            # Derive category
            category = 'Labour' if expense_type == 'Labour Expenses' else 'Other'

            expense = Expense(
                expense_type = expense_type,
                category     = category,
                amount       = float(amount),
                expense_date = expense_date,
                description  = description,
                notes        = notes,
                receipt_path = receipt_path,
                booking_id   = int(booking_id) if booking_id else None,
                labour_id    = int(labour_id)  if labour_id  else None
            )
            db.session.add(expense)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Expense recorded.',
                'data':    expense.to_dict()
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_all_expenses():
        try:
            page        = int(request.args.get('page', 1))
            per_page    = int(request.args.get('per_page', 15))
            search      = request.args.get('search', '').strip()
            expense_type= request.args.get('expense_type', '').strip()
            category    = request.args.get('category', '').strip()
            month       = request.args.get('month', '')
            year_arg    = request.args.get('year', '')
            from_date   = request.args.get('from_date', '')
            to_date     = request.args.get('to_date', '')

            query = Expense.query

            if search:
                query = query.filter(
                    Expense.description.ilike(f'%{search}%') |
                    Expense.expense_type.ilike(f'%{search}%') |
                    Expense.notes.ilike(f'%{search}%')
                )
            if expense_type:
                query = query.filter(Expense.expense_type == expense_type)
            if category:
                query = query.filter(Expense.category == category)
            if month:
                query = query.filter(
                    extract('month', Expense.expense_date) == int(month)
                )
            if year_arg:
                query = query.filter(
                    extract('year', Expense.expense_date) == int(year_arg)
                )
            if from_date:
                query = query.filter(Expense.expense_date >= from_date)
            if to_date:
                query = query.filter(Expense.expense_date <= to_date)

            query      = query.order_by(Expense.expense_date.desc())
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)

            total_amount = db.session.query(
                func.sum(Expense.amount)
            ).scalar() or 0

            labour_total = db.session.query(
                func.sum(Expense.amount)
            ).filter(Expense.category == 'Labour').scalar() or 0

            other_total = db.session.query(
                func.sum(Expense.amount)
            ).filter(Expense.category == 'Other').scalar() or 0

            return jsonify({
                'success': True,
                'data': {
                    'expenses':     [e.to_dict() for e in pagination.items],
                    'total':        pagination.total,
                    'pages':        pagination.pages,
                    'page':         page,
                    'total_amount': float(total_amount),
                    'labour_total': float(labour_total),
                    'other_total':  float(other_total)
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_expense(expense_id):
        try:
            exp = Expense.query.get(expense_id)
            if not exp:
                return jsonify({'success': False, 'message': 'Expense not found.'}), 404
            return jsonify({'success': True, 'data': exp.to_dict()})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def update_expense(expense_id):
        try:
            exp = Expense.query.get(expense_id)
            if not exp:
                return jsonify({'success': False, 'message': 'Expense not found.'}), 404

            if exp.notes == 'Auto-generated from attendance':
                return jsonify({
                    'success': False,
                    'message': 'Auto-generated labour expenses cannot be edited.'
                }), 403

            data = request.get_json() or {}
            fields = ['expense_type', 'amount', 'expense_date', 'description', 'notes']
            for f in fields:
                if f in data:
                    val = float(data[f]) if f == 'amount' else data[f]
                    setattr(exp, f, val)

            if 'expense_type' in data:
                exp.category = (
                    'Labour' if data['expense_type'] == 'Labour Expenses' else 'Other'
                )

            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Expense updated.',
                'data':    exp.to_dict()
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def delete_expense(expense_id):
        try:
            exp = Expense.query.get(expense_id)
            if not exp:
                return jsonify({'success': False, 'message': 'Expense not found.'}), 404

            if exp.category == 'Labour' and exp.labour_id:
                return jsonify({
                    'success': False,
                    'message': 'Auto-generated labour expenses cannot be deleted.'
                }), 403

            db.session.delete(exp)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Expense deleted.'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_today_expenses():
        try:
            today   = str(date.today())
            records = Expense.query.filter_by(expense_date=today).all()

            labour_total = sum(
                float(e.amount) for e in records if e.category == 'Labour'
            )
            other_total = sum(
                float(e.amount) for e in records if e.category == 'Other'
            )
            grand_total = labour_total + other_total

            return jsonify({
                'success': True,
                'data': {
                    'date':     today,
                    'expenses': [e.to_dict() for e in records],
                    'summary': {
                        'labour_total': labour_total,
                        'other_total':  other_total,
                        'grand_total':  grand_total
                    }
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_monthly_statement():
        try:
            today = date.today()
            month = int(request.args.get('month', today.month))
            year  = int(request.args.get('year', today.year))

            records = Expense.query.filter(
                extract('month', Expense.expense_date) == month,
                extract('year',  Expense.expense_date) == year
            ).order_by(Expense.expense_date.asc()).all()

            labour_total = sum(float(e.amount) for e in records if e.category == 'Labour')
            other_total  = sum(float(e.amount) for e in records if e.category == 'Other')

            return jsonify({
                'success': True,
                'data': {
                    'month':         month,
                    'year':          year,
                    'expenses':      [e.to_dict() for e in records],
                    'labour_total':  labour_total,
                    'other_total':   other_total,
                    'grand_total':   labour_total + other_total
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_expense_types():
        return jsonify({'success': True, 'data': {'types': EXPENSE_TYPES}})