from flask import jsonify, request
from sqlalchemy import func
from app.extensions import db
from app.models.design import Design
from app.utils.file_handler import save_uploaded_file, delete_file


class DesignController:

    @staticmethod
    def add_design():
        try:
            title       = (request.form.get('title') or '').strip()
            category    = (request.form.get('category') or '').strip()
            description = (request.form.get('description') or '').strip()
            is_featured = request.form.get('is_featured', 'false').lower() == 'true'

            if not title or not category:
                return jsonify({
                    'success': False,
                    'message': 'Title and category are required.'
                }), 400

            valid_cats = ['Wedding', 'Temple Festival', 'Reception']
            if category not in valid_cats:
                return jsonify({
                    'success': False,
                    'message': f'Category must be one of: {", ".join(valid_cats)}'
                }), 400

            image_path = None
            image_file = request.files.get('image')
            if image_file and image_file.filename:
                image_path = save_uploaded_file(image_file, 'designs')

            design = Design(
                title       = title,
                category    = category,
                description = description,
                is_featured = is_featured,
                image_path  = image_path
            )
            db.session.add(design)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Design uploaded successfully!',
                'data':    design.to_dict()
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_all_designs():
        try:
            page        = int(request.args.get('page', 1))
            per_page    = int(request.args.get('per_page', 12))
            search      = request.args.get('search', '').strip()
            category    = request.args.get('category', '').strip()
            is_featured = request.args.get('is_featured', '')
            is_active   = request.args.get('is_active', '')

            query = Design.query

            if search:
                query = query.filter(
                    Design.title.ilike(f'%{search}%') |
                    Design.description.ilike(f'%{search}%')
                )
            if category:
                query = query.filter(Design.category == category)
            if is_featured != '':
                query = query.filter(Design.is_featured == (is_featured == 'true'))
            if is_active != '':
                query = query.filter(Design.is_active == (is_active == 'true'))

            pagination = query.order_by(
                Design.is_featured.desc(),
                Design.created_at.desc()
            ).paginate(page=page, per_page=per_page, error_out=False)

            return jsonify({
                'success': True,
                'data': {
                    'designs': [d.to_dict() for d in pagination.items],
                    'total':   pagination.total,
                    'pages':   pagination.pages,
                    'page':    page
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_public_designs():
        """Customer-facing gallery — active designs only."""
        try:
            page     = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 12))
            category = request.args.get('category', '').strip()
            search   = request.args.get('search', '').strip()

            query = Design.query.filter_by(is_active=True)

            if category:
                query = query.filter(Design.category == category)
            if search:
                query = query.filter(
                    Design.title.ilike(f'%{search}%') |
                    Design.description.ilike(f'%{search}%')
                )

            pagination = query.order_by(
                Design.is_featured.desc(),
                Design.view_count.desc()
            ).paginate(page=page, per_page=per_page, error_out=False)

            # Category counts
            counts = {}
            for cat in ['Wedding', 'Temple Festival', 'Reception']:
                counts[cat] = Design.query.filter_by(
                    is_active=True, category=cat
                ).count()
            counts['All'] = Design.query.filter_by(is_active=True).count()

            return jsonify({
                'success': True,
                'data': {
                    'designs':         [d.to_dict() for d in pagination.items],
                    'total':           pagination.total,
                    'pages':           pagination.pages,
                    'page':            page,
                    'category_counts': counts
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_design(design_id):
        try:
            design = Design.query.get(design_id)
            if not design:
                return jsonify({'success': False, 'message': 'Design not found.'}), 404

            design.view_count = (design.view_count or 0) + 1
            db.session.commit()

            data     = design.to_dict()
            related  = Design.query.filter(
                Design.category == design.category,
                Design.id != design_id,
                Design.is_active == True
            ).limit(4).all()
            data['related'] = [r.to_dict() for r in related]

            return jsonify({'success': True, 'data': data})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def update_design(design_id):
        try:
            design = Design.query.get(design_id)
            if not design:
                return jsonify({'success': False, 'message': 'Design not found.'}), 404

            if request.content_type and 'multipart' in request.content_type:
                data = request.form.to_dict()
                img  = request.files.get('image')
                if img and img.filename:
                    if design.image_path:
                        delete_file(design.image_path)
                    design.image_path = save_uploaded_file(img, 'designs')
            else:
                data = request.get_json() or {}

            for f in ['title', 'category', 'description']:
                if f in data:
                    setattr(design, f, data[f])
            if 'is_featured' in data:
                design.is_featured = str(data['is_featured']).lower() == 'true'
            if 'is_active' in data:
                design.is_active = str(data['is_active']).lower() == 'true'

            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Design updated.',
                'data':    design.to_dict()
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def delete_design(design_id):
        try:
            design = Design.query.get(design_id)
            if not design:
                return jsonify({'success': False, 'message': 'Design not found.'}), 404

            if design.image_path:
                delete_file(design.image_path)

            db.session.delete(design)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Design deleted.'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def toggle_featured(design_id):
        try:
            design = Design.query.get(design_id)
            if not design:
                return jsonify({'success': False, 'message': 'Design not found.'}), 404

            design.is_featured = not design.is_featured
            db.session.commit()
            status = 'featured' if design.is_featured else 'unfeatured'
            return jsonify({
                'success': True,
                'message': f'Design {status}.',
                'data':    {'is_featured': design.is_featured}
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def toggle_active(design_id):
        try:
            design = Design.query.get(design_id)
            if not design:
                return jsonify({'success': False, 'message': 'Design not found.'}), 404

            design.is_active = not design.is_active
            db.session.commit()
            return jsonify({
                'success': True,
                'message': f'Design {"activated" if design.is_active else "deactivated"}.',
                'data':    {'is_active': design.is_active}
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    @staticmethod
    def get_stats():
        try:
            total    = Design.query.count()
            featured = Design.query.filter_by(is_featured=True).count()
            by_cat   = {}
            for cat in ['Wedding', 'Temple Festival', 'Reception']:
                by_cat[cat] = Design.query.filter_by(category=cat).count()

            top = Design.query.order_by(
                Design.view_count.desc()
            ).limit(5).all()

            return jsonify({
                'success': True,
                'data': {
                    'total':       total,
                    'featured':    featured,
                    'by_category': by_cat,
                    'top_viewed':  [d.to_dict() for d in top]
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500