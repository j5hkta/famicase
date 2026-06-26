from datetime import date, timedelta
from calendar import month_abbr
from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func, extract
from app import db
from app.models import Trabajo, Pago, Odontologo, TipoTrabajo

reportes_bp = Blueprint('reportes', __name__, url_prefix='/reportes')

MESES_ES = ['', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
            'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']


@reportes_bp.route('/')
@login_required
def index():
    hoy = date.today()

    # --- Ingresos por mes (últimos 6 meses) ---
    meses_labels = []
    meses_data = []
    for i in range(5, -1, -1):
        if hoy.month - i <= 0:
            mes = hoy.month - i + 12
            anio = hoy.year - 1
        else:
            mes = hoy.month - i
            anio = hoy.year
        total = db.session.query(func.sum(Pago.monto)).filter(
            extract('month', Pago.fecha_pago) == mes,
            extract('year', Pago.fecha_pago) == anio
        ).scalar() or 0
        meses_labels.append(f'{MESES_ES[mes]} {anio}')
        meses_data.append(round(float(total), 2))

    # --- Trabajos por tipo ---
    tipos_data = db.session.query(
        TipoTrabajo.nombre,
        func.count(Trabajo.id).label('total')
    ).join(Trabajo).group_by(TipoTrabajo.id).order_by(func.count(Trabajo.id).desc()).all()
    tipos_labels = [r[0] for r in tipos_data]
    tipos_counts = [r[1] for r in tipos_data]

    # --- Odontólogos con más trabajos ---
    top_odontologos = db.session.query(
        Odontologo.nombre,
        func.count(Trabajo.id).label('total'),
        func.sum(Trabajo.precio).label('monto')
    ).join(Trabajo).group_by(Odontologo.id).order_by(func.count(Trabajo.id).desc()).limit(10).all()

    # --- Trabajos pendientes de entrega ---
    pendientes = Trabajo.query.filter(
        Trabajo.estado != 'entregado'
    ).order_by(Trabajo.fecha_entrega_estimada.asc()).all()

    return render_template('reportes/index.html',
        meses_labels=meses_labels,
        meses_data=meses_data,
        tipos_labels=tipos_labels,
        tipos_counts=tipos_counts,
        top_odontologos=top_odontologos,
        pendientes=pendientes,
        hoy=hoy
    )
