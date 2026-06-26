from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, make_response
from flask_login import login_required
from app import db
from app.models import Trabajo, Odontologo, TipoTrabajo, Pago
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import io

trabajos_bp = Blueprint('trabajos', __name__, url_prefix='/trabajos')

ESTADO_LABELS = {
    'pendiente': 'Recibido',
    'en_proceso': 'En proceso',
    'pulido': 'En proceso',
    'terminado': 'Finalizado',
    'entregado': 'Finalizado'
}

ESTADO_SIGUIENTE = {
    'pendiente': 'en_proceso',
    'en_proceso': 'entregado',
    'pulido': 'entregado',
    'terminado': 'entregado'
}


@trabajos_bp.route('/')
@login_required
def lista():
    estado_filtro = request.args.get('estado', '')
    odontologo_filtro = request.args.get('odontologo_id', '')

    q = Trabajo.query
    if estado_filtro:
        q = q.filter_by(estado=estado_filtro)
    if odontologo_filtro:
        q = q.filter_by(odontologo_id=int(odontologo_filtro))

    trabajos = q.order_by(Trabajo.fecha_pedido.desc()).all()
    odontologos = Odontologo.query.filter_by(activo=True).order_by(Odontologo.nombre).all()

    return render_template('trabajos/lista.html',
        trabajos=trabajos,
        odontologos=odontologos,
        estado_filtro=estado_filtro,
        odontologo_filtro=odontologo_filtro,
        estado_labels=ESTADO_LABELS
    )


@trabajos_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    odontologos = Odontologo.query.filter_by(activo=True).order_by(Odontologo.nombre).all()
    tipos = TipoTrabajo.query.order_by(TipoTrabajo.nombre).all()
    odontologo_id_pre = request.args.get('odontologo_id', '')

    if request.method == 'POST':
        try:
            odontologo_id = int(request.form['odontologo_id'])
            tipo_id = int(request.form['tipo_trabajo_id'])
            precio = float(request.form.get('precio', 0) or 0)
            fecha_pedido = date.fromisoformat(request.form['fecha_pedido'])
            fecha_entrega_str = request.form.get('fecha_entrega_estimada', '')
            fecha_entrega = date.fromisoformat(fecha_entrega_str) if fecha_entrega_str else None
            num_piezas_str = request.form.get('num_piezas', '')
            num_piezas = int(num_piezas_str) if num_piezas_str else None

            codigo = Trabajo.generar_codigo(fecha_pedido.year)

            t = Trabajo(
                codigo=codigo,
                odontologo_id=odontologo_id,
                tipo_trabajo_id=tipo_id,
                paciente=request.form.get('paciente', '').strip() or None,
                precio=precio,
                fecha_pedido=fecha_pedido,
                fecha_entrega_estimada=fecha_entrega,
                hora_acordada=request.form.get('hora_acordada', '').strip() or None,
                estado='pendiente',
                observaciones=request.form.get('observaciones', '').strip() or None
            )
            db.session.add(t)
            db.session.commit()
            flash(f'Trabajo {codigo} registrado correctamente.', 'success')
            return redirect(url_for('trabajos.detalle', id=t.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar el trabajo: {str(e)}', 'danger')

    return render_template('trabajos/form.html',
        trabajo=None,
        odontologos=odontologos,
        tipos=tipos,
        odontologo_id_pre=odontologo_id_pre,
        hoy=date.today().isoformat()
    )


@trabajos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    t = Trabajo.query.get_or_404(id)
    odontologos = Odontologo.query.filter_by(activo=True).order_by(Odontologo.nombre).all()
    tipos = TipoTrabajo.query.order_by(TipoTrabajo.nombre).all()

    if request.method == 'POST':
        try:
            t.odontologo_id = int(request.form['odontologo_id'])
            t.tipo_trabajo_id = int(request.form['tipo_trabajo_id'])
            t.precio = float(request.form.get('precio', 0) or 0)
            t.fecha_pedido = date.fromisoformat(request.form['fecha_pedido'])
            fecha_entrega_str = request.form.get('fecha_entrega_estimada', '')
            t.fecha_entrega_estimada = date.fromisoformat(fecha_entrega_str) if fecha_entrega_str else None
            t.paciente = request.form.get('paciente', '').strip() or None
            t.hora_acordada = request.form.get('hora_acordada', '').strip() or None
            t.observaciones = request.form.get('observaciones', '').strip() or None
            db.session.commit()
            flash('Trabajo actualizado correctamente.', 'success')
            return redirect(url_for('trabajos.detalle', id=t.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')

    return render_template('trabajos/form.html',
        trabajo=t,
        odontologos=odontologos,
        tipos=tipos,
        odontologo_id_pre='',
        hoy=date.today().isoformat()
    )


@trabajos_bp.route('/<int:id>')
@login_required
def detalle(id):
    t = Trabajo.query.get_or_404(id)
    return render_template('trabajos/detalle.html',
        trabajo=t,
        estado_labels=ESTADO_LABELS,
        estado_siguiente=ESTADO_SIGUIENTE.get(t.estado)
    )


@trabajos_bp.route('/<int:id>/cambiar-estado', methods=['POST'])
@login_required
def cambiar_estado(id):
    t = Trabajo.query.get_or_404(id)
    nuevo_estado = request.form.get('estado')
    estados_validos = ['pendiente', 'en_proceso', 'pulido', 'terminado', 'entregado']

    estados_validos = ['pendiente', 'en_proceso', 'entregado']
    if nuevo_estado in estados_validos:
        t.estado = nuevo_estado
        if nuevo_estado == 'entregado' and not t.fecha_entrega_real:
            t.fecha_entrega_real = date.today()
        db.session.commit()
        flash(f'Estado actualizado a "{ESTADO_LABELS[nuevo_estado]}".', 'success')
    else:
        flash('Estado no válido.', 'danger')

    return redirect(url_for('trabajos.detalle', id=t.id))


@trabajos_bp.route('/<int:id>/entregar', methods=['POST'])
@login_required
def marcar_entregado(id):
    t = Trabajo.query.get_or_404(id)
    t.estado = 'entregado'
    t.fecha_entrega_real = date.today()
    db.session.commit()
    flash(f'Trabajo {t.codigo} marcado como entregado.', 'success')
    return redirect(url_for('trabajos.detalle', id=t.id))


@trabajos_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar(id):
    t = Trabajo.query.get_or_404(id)
    codigo = t.codigo
    Pago.query.filter_by(trabajo_id=id).delete()
    db.session.delete(t)
    db.session.commit()
    flash(f'Trabajo {codigo} eliminado correctamente.', 'success')
    return redirect(url_for('trabajos.lista'))


@trabajos_bp.route('/<int:id>/pdf')
@login_required
def generar_pdf(id):
    t = Trabajo.query.get_or_404(id)
    cfg = current_app.config

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    ancho, alto = A4

    # Encabezado
    c.setFillColor(colors.HexColor('#0d6efd'))
    c.rect(0, alto - 4*cm, ancho, 4*cm, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 20)
    c.drawCentredString(ancho/2, alto - 1.8*cm, cfg.get('LAB_NOMBRE', 'GlobalDental'))
    c.setFont('Helvetica', 11)
    c.drawCentredString(ancho/2, alto - 2.6*cm, cfg.get('LAB_PROPIETARIOS', ''))
    c.drawCentredString(ancho/2, alto - 3.3*cm,
        f"{cfg.get('LAB_CIUDAD', 'Lima, Perú')}  |  Tel: {cfg.get('LAB_TELEFONO', '')}")

    # Título del documento
    c.setFillColor(colors.HexColor('#212529'))
    c.setFont('Helvetica-Bold', 14)
    c.drawCentredString(ancho/2, alto - 5*cm, 'ORDEN DE TRABAJO / PRESUPUESTO')

    # Línea separadora
    c.setStrokeColor(colors.HexColor('#0d6efd'))
    c.setLineWidth(2)
    c.line(2*cm, alto - 5.5*cm, ancho - 2*cm, alto - 5.5*cm)

    # Datos principales
    y = alto - 6.5*cm
    c.setFont('Helvetica-Bold', 10)
    c.setFillColor(colors.HexColor('#6c757d'))

    def fila(etiqueta, valor, ypos):
        c.setFont('Helvetica-Bold', 10)
        c.setFillColor(colors.HexColor('#6c757d'))
        c.drawString(2*cm, ypos, etiqueta)
        c.setFont('Helvetica', 10)
        c.setFillColor(colors.HexColor('#212529'))
        c.drawString(7*cm, ypos, str(valor))

    fila('Código:', t.codigo, y)
    fila('Fecha:', t.fecha_pedido.strftime('%d/%m/%Y'), y - 0.7*cm)
    fila('Odontólogo:', t.odontologo.nombre + (' — ' + t.odontologo.clinica if t.odontologo.clinica else ''), y - 1.4*cm)
    fila('Paciente:', t.paciente or 'No especificado', y - 2.1*cm)

    # Detalle del trabajo
    y2 = y - 3.2*cm
    c.setFillColor(colors.HexColor('#e9ecef'))
    c.rect(2*cm, y2 - 0.3*cm, ancho - 4*cm, 0.7*cm, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#212529'))
    c.setFont('Helvetica-Bold', 11)
    c.drawString(2.3*cm, y2, 'DETALLE DEL TRABAJO')

    y3 = y2 - 1.0*cm
    fila('Tipo:', t.tipo_trabajo.nombre, y3)
    fila('N° de piezas:', str(t.num_piezas) if t.num_piezas else '—', y3 - 0.7*cm)
    fila('Técnico:', t.tecnico, y3 - 1.4*cm)
    fila('Estado:', ESTADO_LABELS.get(t.estado, t.estado), y3 - 2.1*cm)
    if t.observaciones:
        fila('Observaciones:', '', y3 - 2.8*cm)
        c.setFont('Helvetica', 9)
        c.setFillColor(colors.HexColor('#212529'))
        c.drawString(2*cm, y3 - 3.5*cm, t.observaciones[:100])

    # Precio
    y4 = y3 - 4.5*cm
    c.setFillColor(colors.HexColor('#0d6efd'))
    c.rect(2*cm, y4 - 0.5*cm, ancho - 4*cm, 1.5*cm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 14)
    c.drawString(2.5*cm, y4 + 0.2*cm, 'PRECIO TOTAL:')
    c.drawRightString(ancho - 2.5*cm, y4 + 0.2*cm, f'S/ {t.precio:.2f}')

    # Fecha estimada
    if t.fecha_entrega_estimada:
        c.setFillColor(colors.HexColor('#212529'))
        c.setFont('Helvetica', 10)
        c.drawCentredString(ancho/2, y4 - 1.5*cm,
            f'Fecha estimada de entrega: {t.fecha_entrega_estimada.strftime("%d/%m/%Y")}')

    # Pie
    c.setFillColor(colors.HexColor('#6c757d'))
    c.setFont('Helvetica', 8)
    c.drawCentredString(ancho/2, 1.5*cm, f'{cfg.get("LAB_NOMBRE","FamiCase")} — {cfg.get("LAB_CIUDAD", "Lima, Perú")} — Documento generado el {date.today().strftime("%d/%m/%Y")}')

    c.save()
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=OT-{t.codigo}.pdf'
    return response
