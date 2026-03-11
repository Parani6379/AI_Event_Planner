from flask import Blueprint, render_template, redirect, url_for

pages_bp = Blueprint('pages', __name__)


# ════════════════════════════════════════════════════
# ADMIN PAGE ROUTES
# ════════════════════════════════════════════════════

@pages_bp.route('/admin/login')
def admin_login():
    return render_template('admin/login.html')


@pages_bp.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html')


# ── Labour Pages ─────────────────────────────────────
@pages_bp.route('/admin/labour')
def admin_labour_list():
    return render_template('admin/labour/list.html')


@pages_bp.route('/admin/labour/add')
def admin_labour_add():
    return render_template('admin/labour/add.html')


@pages_bp.route('/admin/labour/attendance')
def admin_labour_attendance():
    return render_template('admin/labour/attendance.html')


@pages_bp.route('/admin/labour/<int:labour_id>')
def admin_labour_detail(labour_id):
    return render_template(
        'admin/labour/detail.html',
        labour_id=labour_id
    )


# ── Expense Pages ─────────────────────────────────────
@pages_bp.route('/admin/expenses')
def admin_expense_list():
    return render_template('admin/expense/list.html')


@pages_bp.route('/admin/expenses/add')
def admin_expense_add():
    return render_template('admin/expense/add.html')


# ── Booking Pages ─────────────────────────────────────
@pages_bp.route('/admin/bookings')
def admin_booking_list():
    return render_template('admin/booking/list.html')


@pages_bp.route('/admin/bookings/add')
def admin_booking_add():
    return render_template('admin/booking/add.html')


@pages_bp.route('/admin/bookings/<int:booking_id>')
def admin_booking_detail(booking_id):
    return render_template(
        'admin/booking/detail.html',
        booking_id=booking_id
    )


# ── Billing Pages ─────────────────────────────────────
@pages_bp.route('/admin/billing')
def admin_billing_list():
    return render_template('admin/billing/list.html')


@pages_bp.route('/admin/billing/create')
def admin_billing_create():
    return render_template('admin/billing/create.html')


@pages_bp.route('/admin/billing/<int:billing_id>/invoice')
def admin_billing_invoice(billing_id):
    return render_template(
        'admin/billing/invoice.html',
        billing_id=billing_id
    )


# ── Design Pages ──────────────────────────────────────
@pages_bp.route('/admin/designs')
def admin_design_list():
    return render_template('admin/design/list.html')


@pages_bp.route('/admin/designs/upload')
def admin_design_upload():
    return render_template('admin/design/upload.html')


# ── Profile Page ──────────────────────────────────────
@pages_bp.route('/admin/profile')
def admin_profile():
    return render_template('admin/profile/edit.html')


# ── Redirect /admin → /admin/dashboard ───────────────
@pages_bp.route('/admin')
def admin_root():
    return redirect('/admin/dashboard')


# ── Customers Page ────────────────────────────────────
@pages_bp.route('/admin/customers')
def admin_customer_list():
    return render_template('admin/customers/list.html')