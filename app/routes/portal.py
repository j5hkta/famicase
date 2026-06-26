from datetime import date
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app import db, limiter
from app.models import Odontologo, Trabajo, Pago, TipoTrabajo

portal_bp = Blueprint('portal', __name__, url_prefix='/portal')

# Estados simplificados para el portal (3 fases)
ESTADO_PORTAL = {
    'pendiente': 'Pendiente',
    'en_proceso': 'En proceso',
    'pulido': 'En proceso',
    'terminado': 'Finalizado',
    'entregado': 'Finalizado'
}

ESTADO_PORTAL_CLASE = {
    'pendiente': 'pendiente',
    'en_proceso': 'en_proceso',
    'pulido': 'en_proceso',
    'terminado': 'finalizado',
    'entregado': 'finalizado'
}

# Aliases usados en el resto de la ruta (compatibilidad)
ESTADO_LABELS = ESTADO_PORTAL
ESTADO_CLASES = ESTADO_PORTAL_CLASE


def portal_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'portal_odontologo_id' not in session:
            return redirect(url_for('portal.login'))
        return f(*args, **kwargs)
    return decorated


def get_odontologo_actual():
    oid = session.get('portal_odontologo_id')
    if not oid:
        return None
    return Odontologo.query.get(oid)


@portal_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("8 per minute; 20 per hour", methods=["POST"])
def login():
    if 'portal_odontologo_id' in session:
        return redirect(url_for('portal.dashboard'))

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()[:80]
        pin = request.form.get('pin', '').strip()[:6]

        if not nombre or not pin:
            flash('Escribe tu nombre e ingresa tu PIN.', 'danger')
            return render_template('portal/login.html')

        o = Odontologo.query.filter(
            Odontologo.nombre.ilike(nombre),
            Odontologo.activo == True
        ).first()
        if o and o.pin_acceso and o.pin_acceso == pin:
            session['portal_odontologo_id'] = o.id
            session.permanent = True
            return redirect(url_for('portal.dashboard'))
        else:
            flash('PIN incorrecto. Consulta con el laboratorio.', 'danger')

    return render_template('portal/login.html')


@portal_bp.route('/logout')
def logout():
    session.pop('portal_odontologo_id', None)
    return redirect(url_for('portal.login'))


@portal_bp.route('/')
@portal_login_required
def dashboard():
    o = get_odontologo_actual()
    hoy = date.today()

    trabajos_activos = Trabajo.query.filter_by(odontologo_id=o.id).filter(
        Trabajo.estado.notin_(['terminado', 'entregado'])
    ).order_by(Trabajo.fecha_entrega_estimada.asc()).all()

    proximas_entregas = [t for t in trabajos_activos if t.fecha_entrega_estimada][:5]

    total_trabajos = sum(t.precio for t in o.trabajos if t.precio)
    total_pagado = sum(p.monto for p in o.pagos if p.monto)
    saldo = total_trabajos - total_pagado + (o.saldo_inicial or 0)

    return render_template('portal/dashboard.html',
        o=o,
        trabajos_activos=trabajos_activos,
        proximas_entregas=proximas_entregas,
        saldo=saldo,
        hoy=hoy,
        estado_labels=ESTADO_LABELS,
        estado_clases=ESTADO_CLASES
    )


@portal_bp.route('/mis-trabajos')
@portal_login_required
def mis_trabajos():
    o = get_odontologo_actual()
    hoy = date.today()
    filtro = request.args.get('estado', '')

    q = Trabajo.query.filter_by(odontologo_id=o.id)
    if filtro:
        q = q.filter_by(estado=filtro)

    trabajos = q.order_by(Trabajo.fecha_pedido.desc()).all()

    return render_template('portal/trabajos.html',
        o=o,
        trabajos=trabajos,
        filtro=filtro,
        hoy=hoy,
        estado_labels=ESTADO_LABELS,
        estado_clases=ESTADO_CLASES
    )


@portal_bp.route('/tarifas')
@portal_login_required
def tarifas():
    o = get_odontologo_actual()
    tipos = TipoTrabajo.query.order_by(TipoTrabajo.nombre).all()
    return render_template('portal/tarifas.html', o=o, tipos=tipos)


@portal_bp.route('/mi-saldo')
@portal_login_required
def mi_saldo():
    o = get_odontologo_actual()

    trabajos = Trabajo.query.filter_by(odontologo_id=o.id).order_by(Trabajo.fecha_pedido.desc()).all()
    pagos = Pago.query.filter_by(odontologo_id=o.id).order_by(Pago.fecha_pago.desc()).all()

    total_trabajos = sum(t.precio for t in trabajos if t.precio)
    total_pagado = sum(p.monto for p in pagos if p.monto)
    saldo = total_trabajos - total_pagado + (o.saldo_inicial or 0)

    # Trabajos sin pago completo (aproximado)
    trabajos_pendientes_pago = [t for t in trabajos if t.precio and t.precio > 0]

    return render_template('portal/saldo.html',
        o=o,
        trabajos=trabajos,
        pagos=pagos,
        total_trabajos=total_trabajos,
        total_pagado=total_pagado,
        saldo=saldo
    )


@portal_bp.route('/calendario')
@portal_login_required
def calendario():
    o = get_odontologo_actual()

    # TODOS los trabajos activos del laboratorio con fecha de entrega
    todos_trabajos = Trabajo.query.filter(
        Trabajo.fecha_entrega_estimada != None,
        Trabajo.estado != 'entregado'
    ).order_by(Trabajo.fecha_entrega_estimada.asc()).all()

    # Mis trabajos (para la lista de abajo)
    mis_trabajos = [t for t in todos_trabajos if t.odontologo_id == o.id]

    # Preparar eventos para FullCalendar
    eventos = []
    colores_propios = {
        'pendiente': '#6366f1',
        'en_proceso': '#2563eb',
        'pulido': '#2563eb',
        'terminado': '#10b981',
        'entregado': '#059669'
    }
    for t in todos_trabajos:
        es_mio = t.odontologo_id == o.id
        if es_mio:
            color = colores_propios.get(t.estado, '#6366f1')
            titulo = t.tipo_trabajo.nombre
            if t.paciente:
                titulo += f' — {t.paciente}'
        else:
            color = '#cbd5e1'
            titulo = t.tipo_trabajo.nombre

        eventos.append({
            'id': t.id,
            'title': titulo,
            'start': t.fecha_entrega_estimada.isoformat(),
            'color': color,
            'textColor': '#ffffff' if es_mio else '#475569',
            'extendedProps': {
                'estado': ESTADO_PORTAL.get(t.estado, t.estado),
                'doctor': t.odontologo.nombre,
                'paciente': t.paciente or '',
                'mio': es_mio,
                'codigo': t.codigo
            }
        })

    return render_template('portal/calendario.html',
        o=o,
        eventos=eventos,
        trabajos=mis_trabajos,
        estado_labels=ESTADO_PORTAL,
        estado_clases=ESTADO_PORTAL_CLASE,
        hoy=date.today()
    )
