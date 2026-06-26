from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models import Odontologo, Trabajo, Pago

odontologos_bp = Blueprint('odontologos', __name__, url_prefix='/odontologos')


@odontologos_bp.route('/')
@login_required
def lista():
    odontologos = Odontologo.query.filter_by(activo=True).order_by(Odontologo.nombre).all()
    return render_template('odontologos/lista.html', odontologos=odontologos)


@odontologos_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        if not nombre:
            flash('El nombre es obligatorio.', 'danger')
            return render_template('odontologos/form.html', odontologo=None)

        pin = request.form.get('pin_acceso', '').strip() or None
        o = Odontologo(
            nombre=nombre,
            clinica=request.form.get('clinica', '').strip(),
            telefono=request.form.get('telefono', '').strip(),
            correo=request.form.get('correo', '').strip(),
            direccion=request.form.get('direccion', '').strip(),
            pin_acceso=pin
        )
        db.session.add(o)
        db.session.commit()
        flash(f'Odontólogo "{nombre}" registrado correctamente.', 'success')
        return redirect(url_for('odontologos.lista'))

    return render_template('odontologos/form.html', odontologo=None)


@odontologos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    o = Odontologo.query.get_or_404(id)

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        if not nombre:
            flash('El nombre es obligatorio.', 'danger')
            return render_template('odontologos/form.html', odontologo=o)

        o.nombre = nombre
        o.clinica = request.form.get('clinica', '').strip()
        o.telefono = request.form.get('telefono', '').strip()
        o.correo = request.form.get('correo', '').strip()
        o.direccion = request.form.get('direccion', '').strip()
        pin = request.form.get('pin_acceso', '').strip()
        o.pin_acceso = pin if pin else None
        db.session.commit()
        flash('Odontólogo actualizado correctamente.', 'success')
        return redirect(url_for('odontologos.detalle', id=o.id))

    return render_template('odontologos/form.html', odontologo=o)


@odontologos_bp.route('/<int:id>')
@login_required
def detalle(id):
    o = Odontologo.query.get_or_404(id)
    trabajos = Trabajo.query.filter_by(odontologo_id=id).order_by(Trabajo.fecha_pedido.desc()).all()
    pagos = Pago.query.filter_by(odontologo_id=id).order_by(Pago.fecha_pago.desc()).all()

    total_trabajos = sum(t.precio for t in trabajos if t.precio)
    total_pagado = sum(p.monto for p in pagos if p.monto)
    saldo = total_trabajos - total_pagado

    return render_template('odontologos/detalle.html',
        odontologo=o,
        trabajos=trabajos,
        pagos=pagos,
        total_trabajos=total_trabajos,
        total_pagado=total_pagado,
        saldo=saldo
    )


@odontologos_bp.route('/<int:id>/desactivar', methods=['POST'])
@login_required
def desactivar(id):
    o = Odontologo.query.get_or_404(id)
    o.activo = False
    db.session.commit()
    flash(f'Odontólogo "{o.nombre}" desactivado.', 'warning')
    return redirect(url_for('odontologos.lista'))
