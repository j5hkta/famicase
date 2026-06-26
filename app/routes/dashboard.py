import os
import shutil
from datetime import date, timedelta, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required
from sqlalchemy import func
from app import db
from app.models import Trabajo, Odontologo, Material, Pago

dashboard_bp = Blueprint('dashboard', __name__)


def _backup_dir():
    return os.path.join(current_app.config['DATA_DIR'], 'backups')


def _db_path():
    uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    return uri.replace('sqlite:///', '')


def crear_backup():
    """Copia el archivo SQLite a la carpeta de backups. Conserva los últimos 10."""
    backup_dir = _backup_dir()
    os.makedirs(backup_dir, exist_ok=True)
    src = _db_path()
    if not os.path.exists(src):
        return None
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre = f'dental_backup_{ts}.db'
    dst = os.path.join(backup_dir, nombre)
    shutil.copy2(src, dst)

    # Conservar solo los últimos 10 backups
    backups = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith('.db')],
        reverse=True
    )
    for viejo in backups[10:]:
        try:
            os.remove(os.path.join(backup_dir, viejo))
        except OSError:
            pass

    return nombre


def listar_backups():
    backup_dir = _backup_dir()
    if not os.path.exists(backup_dir):
        return []
    archivos = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith('.db')],
        reverse=True
    )
    resultado = []
    for f in archivos:
        ruta = os.path.join(backup_dir, f)
        tam = os.path.getsize(ruta)
        resultado.append({
            'nombre': f,
            'fecha': f.replace('dental_backup_', '').replace('.db', ''),
            'tamano_kb': round(tam / 1024, 1)
        })
    return resultado


@dashboard_bp.route('/')
@login_required
def index():
    hoy = date.today()
    fin_semana = hoy + timedelta(days=7)

    trabajos_activos = Trabajo.query.filter(
        Trabajo.estado != 'entregado'
    ).count()

    trabajos_semana = Trabajo.query.filter(
        Trabajo.estado != 'entregado',
        Trabajo.fecha_entrega_estimada >= hoy,
        Trabajo.fecha_entrega_estimada <= fin_semana
    ).count()

    total_cobrado = db.session.query(func.sum(Trabajo.precio)).scalar() or 0
    total_pagado = db.session.query(func.sum(Pago.monto)).scalar() or 0
    saldo_pendiente = total_cobrado - total_pagado

    trabajos_recientes = Trabajo.query.order_by(
        Trabajo.created_at.desc()
    ).limit(10).all()

    backups = listar_backups()

    return render_template('dashboard/index.html',
        trabajos_activos=trabajos_activos,
        trabajos_semana=trabajos_semana,
        saldo_pendiente=saldo_pendiente,
        trabajos_recientes=trabajos_recientes,
        backups=backups,
        hoy=hoy
    )


ESTADO_CAL_LABELS = {
    'pendiente': 'Recibido',
    'en_proceso': 'En proceso',
    'pulido': 'En proceso',
    'terminado': 'Finalizado',
    'entregado': 'Finalizado'
}

ESTADO_CAL_COLORES = {
    'pendiente': '#6366f1',
    'en_proceso': '#2563eb',
    'pulido': '#2563eb',
    'terminado': '#10b981',
    'entregado': '#059669'
}


@dashboard_bp.route('/calendario')
@login_required
def calendario():
    hoy = date.today()
    trabajos_cal = Trabajo.query.filter(
        Trabajo.fecha_entrega_estimada != None,
        Trabajo.estado != 'entregado'
    ).order_by(Trabajo.fecha_entrega_estimada.asc()).all()

    eventos = []
    for t in trabajos_cal:
        eventos.append({
            'id': t.id,
            'title': f'{t.odontologo.nombre} — {t.tipo_trabajo.nombre}',
            'start': t.fecha_entrega_estimada.isoformat(),
            'color': ESTADO_CAL_COLORES.get(t.estado, '#6366f1'),
            'extendedProps': {
                'codigo': t.codigo,
                'odontologo': t.odontologo.nombre,
                'tipo': t.tipo_trabajo.nombre,
                'paciente': t.paciente or '',
                'estado_label': ESTADO_CAL_LABELS.get(t.estado, t.estado),
                'precio': f'{t.precio:.2f}' if t.precio else '0.00',
                'trabajo_id': t.id
            }
        })

    proximas = [t for t in trabajos_cal if t.fecha_entrega_estimada and t.fecha_entrega_estimada >= hoy][:15]

    return render_template('dashboard/calendario.html',
        eventos=eventos,
        proximas=proximas,
        hoy=hoy,
        estado_labels=ESTADO_CAL_LABELS,
        total=len(trabajos_cal)
    )


@dashboard_bp.route('/backup', methods=['POST'])
@login_required
def hacer_backup():
    nombre = crear_backup()
    if nombre:
        flash(f'Respaldo creado correctamente: {nombre}', 'success')
    else:
        flash('No se pudo crear el respaldo. Verifica que la base de datos existe.', 'danger')
    return redirect(url_for('dashboard.index'))


@dashboard_bp.route('/limpiar-datos', methods=['POST'])
@login_required
def limpiar_datos():
    from app.models import Pago, Trabajo
    crear_backup()
    Pago.query.delete()
    Trabajo.query.delete()
    db.session.commit()
    flash('Todos los trabajos y pagos han sido eliminados. Se creó un respaldo antes de limpiar.', 'success')
    return redirect(url_for('dashboard.index'))
