from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    activo = db.Column(db.Boolean, default=True)

    def get_id(self):
        return str(self.id)


class Odontologo(db.Model):
    __tablename__ = 'odontologos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    clinica = db.Column(db.String(120))
    telefono = db.Column(db.String(30))
    correo = db.Column(db.String(120))
    direccion = db.Column(db.String(200))
    activo = db.Column(db.Boolean, default=True)
    pin_acceso = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    trabajos = db.relationship('Trabajo', backref='odontologo', lazy='dynamic')
    pagos = db.relationship('Pago', backref='odontologo', lazy='dynamic')

    def saldo_pendiente(self):
        total_trabajos = sum(t.precio for t in self.trabajos if t.precio)
        total_pagado = sum(p.monto for p in self.pagos if p.monto)
        return total_trabajos - total_pagado


class TipoTrabajo(db.Model):
    __tablename__ = 'tipos_trabajo'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    complejidad = db.Column(db.Enum('complejo', 'sencillo', name='complejidad_enum'), nullable=False)
    precio_base = db.Column(db.Float, default=0.0)

    trabajos = db.relationship('Trabajo', backref='tipo_trabajo', lazy='dynamic')


class Trabajo(db.Model):
    __tablename__ = 'trabajos'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    odontologo_id = db.Column(db.Integer, db.ForeignKey('odontologos.id'), nullable=False)
    tipo_trabajo_id = db.Column(db.Integer, db.ForeignKey('tipos_trabajo.id'), nullable=False)
    paciente = db.Column(db.String(120))
    num_piezas = db.Column(db.Integer)
    precio = db.Column(db.Float, default=0.0)
    fecha_pedido = db.Column(db.Date, nullable=False)
    fecha_entrega_estimada = db.Column(db.Date)
    fecha_entrega_real = db.Column(db.Date)
    estado = db.Column(
        db.Enum('pendiente', 'en_proceso', 'pulido', 'terminado', 'entregado', name='estado_enum'),
        default='pendiente',
        nullable=False
    )
    tecnico = db.Column(db.String(20), nullable=True)
    observaciones = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    pagos = db.relationship('Pago', backref='trabajo', lazy='dynamic')

    @staticmethod
    def generar_codigo(year):
        ultimo = Trabajo.query.filter(
            Trabajo.codigo.like(f'LAB-{year}-%')
        ).order_by(Trabajo.id.desc()).first()
        if ultimo:
            num = int(ultimo.codigo.split('-')[2]) + 1
        else:
            num = 1
        return f'LAB-{year}-{num:03d}'


class Pago(db.Model):
    __tablename__ = 'pagos'
    id = db.Column(db.Integer, primary_key=True)
    odontologo_id = db.Column(db.Integer, db.ForeignKey('odontologos.id'), nullable=False)
    trabajo_id = db.Column(db.Integer, db.ForeignKey('trabajos.id'), nullable=True)
    monto = db.Column(db.Float, nullable=False)
    fecha_pago = db.Column(db.Date, nullable=False)
    metodo = db.Column(
        db.Enum('efectivo', 'transferencia', 'yape', 'plin', name='metodo_enum'),
        nullable=False
    )
    observaciones = db.Column(db.Text)


class Material(db.Model):
    __tablename__ = 'materiales'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    stock = db.Column(db.Float, default=0.0)
    unidad = db.Column(db.String(30), nullable=False)
    stock_minimo = db.Column(db.Float, default=0.0)
    proveedor = db.Column(db.String(120))
    activo = db.Column(db.Boolean, default=True)

    @property
    def stock_bajo(self):
        return self.stock <= self.stock_minimo
