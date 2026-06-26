from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from sqlalchemy import func
from app import db
from app.models import Pago, Odontologo, Trabajo

pagos_bp = Blueprint('pagos', __name__, url_prefix='/pagos')

METODO_LABELS = {
    'efectivo': 'Efectivo',
    'transferencia': 'Transferencia',
    'yape': 'Yape',
    'plin': 'Plin'
}


@pagos_bp.route('/')
@login_required
def lista():
    odontologos = Odontologo.query.filter_by(activo=True).order_by(Odontologo.nombre).all()

    resumen = []
    for o in odontologos:
        total_trabajos = db.session.query(func.sum(Trabajo.precio)).filter_by(odontologo_id=o.id).scalar() or 0
        total_pagado = db.session.query(func.sum(Pago.monto)).filter_by(odontologo_id=o.id).scalar() or 0
        num_trabajos = Trabajo.query.filter_by(odontologo_id=o.id).count()
        saldo = total_trabajos - total_pagado + (o.saldo_inicial or 0)
        resumen.append({
            'odontologo': o,
            'num_trabajos': num_trabajos,
            'total_trabajos': total_trabajos,
            'total_pagado': total_pagado,
            'saldo': saldo
        })

    pagos_recientes = Pago.query.order_by(Pago.fecha_pago.desc()).limit(20).all()

    return render_template('pagos/lista.html',
        resumen=resumen,
        pagos_recientes=pagos_recientes,
        metodo_labels=METODO_LABELS
    )


@pagos_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    odontologos = Odontologo.query.filter_by(activo=True).order_by(Odontologo.nombre).all()
    odontologo_id_pre = request.args.get('odontologo_id', '')
    trabajos_pre = []
    if odontologo_id_pre:
        trabajos_pre = Trabajo.query.filter_by(
            odontologo_id=int(odontologo_id_pre)
        ).filter(Trabajo.estado != 'entregado').order_by(Trabajo.fecha_pedido.desc()).all()

    if request.method == 'POST':
        try:
            odontologo_id = int(request.form['odontologo_id'])
            monto = float(request.form['monto'])
            fecha_pago = date.fromisoformat(request.form['fecha_pago'])
            metodo = request.form['metodo']
            trabajo_id_str = request.form.get('trabajo_id', '')
            trabajo_id = int(trabajo_id_str) if trabajo_id_str else None
            observaciones = request.form.get('observaciones', '').strip() or None

            p = Pago(
                odontologo_id=odontologo_id,
                monto=monto,
                fecha_pago=fecha_pago,
                metodo=metodo,
                trabajo_id=trabajo_id,
                observaciones=observaciones
            )
            db.session.add(p)
            db.session.commit()
            flash(f'Pago de S/ {monto:.2f} registrado correctamente.', 'success')
            return redirect(url_for('pagos.lista'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar el pago: {str(e)}', 'danger')

    return render_template('pagos/form.html',
        odontologos=odontologos,
        odontologo_id_pre=odontologo_id_pre,
        trabajos_pre=trabajos_pre,
        hoy=date.today().isoformat()
    )


@pagos_bp.route('/historial')
@login_required
def historial():
    pagos = Pago.query.order_by(Pago.fecha_pago.desc()).all()
    return render_template('pagos/historial.html', pagos=pagos, metodo_labels=METODO_LABELS)
