from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models import Material

inventario_bp = Blueprint('inventario', __name__, url_prefix='/inventario')


@inventario_bp.route('/')
@login_required
def lista():
    materiales = Material.query.filter_by(activo=True).order_by(Material.nombre).all()
    return render_template('inventario/lista.html', materiales=materiales)


@inventario_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        if not nombre:
            flash('El nombre es obligatorio.', 'danger')
            return render_template('inventario/form.html', material=None)
        try:
            m = Material(
                nombre=nombre,
                stock=float(request.form.get('stock', 0) or 0),
                unidad=request.form.get('unidad', '').strip(),
                stock_minimo=float(request.form.get('stock_minimo', 0) or 0),
                proveedor=request.form.get('proveedor', '').strip() or None
            )
            db.session.add(m)
            db.session.commit()
            flash(f'Material "{nombre}" agregado correctamente.', 'success')
            return redirect(url_for('inventario.lista'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    return render_template('inventario/form.html', material=None)


@inventario_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    m = Material.query.get_or_404(id)

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        if not nombre:
            flash('El nombre es obligatorio.', 'danger')
            return render_template('inventario/form.html', material=m)
        try:
            m.nombre = nombre
            m.stock = float(request.form.get('stock', 0) or 0)
            m.unidad = request.form.get('unidad', '').strip()
            m.stock_minimo = float(request.form.get('stock_minimo', 0) or 0)
            m.proveedor = request.form.get('proveedor', '').strip() or None
            db.session.commit()
            flash('Material actualizado correctamente.', 'success')
            return redirect(url_for('inventario.lista'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    return render_template('inventario/form.html', material=m)


@inventario_bp.route('/<int:id>/entrada', methods=['POST'])
@login_required
def entrada_stock(id):
    m = Material.query.get_or_404(id)
    try:
        cantidad = float(request.form.get('cantidad', 0) or 0)
        if cantidad <= 0:
            flash('La cantidad debe ser mayor a cero.', 'danger')
        else:
            m.stock += cantidad
            db.session.commit()
            flash(f'Stock de "{m.nombre}" actualizado a {m.stock} {m.unidad}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('inventario.lista'))
