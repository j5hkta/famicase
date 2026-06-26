import os
from app import create_app, db
from app.models import Usuario, Odontologo, TipoTrabajo
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    os.makedirs(app.config['DATA_DIR'], exist_ok=True)
    db.create_all()

    with db.engine.connect() as conn:
        for sql in [
            "ALTER TABLE odontologos ADD COLUMN pin_acceso VARCHAR(10)",
            "ALTER TABLE odontologos ADD COLUMN saldo_inicial FLOAT DEFAULT 0.0",
            "ALTER TABLE trabajos ADD COLUMN hora_acordada VARCHAR(5)",
        ]:
            try:
                conn.execute(db.text(sql))
                conn.commit()
            except Exception:
                pass

    if not Usuario.query.filter_by(username='admin').first():
        db.session.add(Usuario(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            nombre='Administrador',
            activo=True
        ))
        db.session.commit()

    if not TipoTrabajo.query.first():
        tipos = [
            TipoTrabajo(nombre='Juego de totales ivostar',                                  complejidad='complejo', precio_base=400),
            TipoTrabajo(nombre='Juego de totales',                                           complejidad='complejo', precio_base=300),
            TipoTrabajo(nombre='Parcial Removible (Con Wipla)',                              complejidad='sencillo', precio_base=120),
            TipoTrabajo(nombre='Base Metalica (inferior o superior)',                        complejidad='complejo', precio_base=250),
            TipoTrabajo(nombre='Base Metalica placa total o rejilla',                        complejidad='complejo', precio_base=300),
            TipoTrabajo(nombre='Base Metalica solo estructura metalica',                     complejidad='sencillo', precio_base=200),
            TipoTrabajo(nombre='Corona de Porcelana con hombro ceramico',                    complejidad='complejo', precio_base=100),
            TipoTrabajo(nombre='Corona de Porcelana y veneer',                               complejidad='complejo', precio_base=90),
            TipoTrabajo(nombre='Corona jacket (ivocron)',                                    complejidad='sencillo', precio_base=60),
            TipoTrabajo(nombre='Corona completa de metal y incrustacion',                    complejidad='sencillo', precio_base=60),
            TipoTrabajo(nombre='Perno directo e indirecto',                                  complejidad='sencillo', precio_base=25),
            TipoTrabajo(nombre='Falsa encia por pieza',                                      complejidad='sencillo', precio_base=30),
            TipoTrabajo(nombre='Maquillaje por pieza',                                       complejidad='sencillo', precio_base=20),
            TipoTrabajo(nombre='Rebasado sup. o inf. (Termocurable)',                        complejidad='sencillo', precio_base=60),
            TipoTrabajo(nombre='Reparacion simple',                                          complejidad='sencillo', precio_base=50),
            TipoTrabajo(nombre='Placas de contencion',                                       complejidad='sencillo', precio_base=80),
            TipoTrabajo(nombre='Repeticion de metal',                                        complejidad='sencillo', precio_base=20),
            TipoTrabajo(nombre='Carillas libres de metal e.max, monoliticas, incrustacion',  complejidad='complejo', precio_base=200),
            TipoTrabajo(nombre='Coronas de zirconio',                                        complejidad='complejo', precio_base=200),
            TipoTrabajo(nombre='Provisionales por pieza',                                    complejidad='sencillo', precio_base=20),
            TipoTrabajo(nombre='Flexible individuales hasta 4 dientes',                      complejidad='complejo', precio_base=200),
            TipoTrabajo(nombre='Flexibles parciales',                                        complejidad='complejo', precio_base=250),
            TipoTrabajo(nombre='Flexibles totales',                                          complejidad='complejo', precio_base=300),
        ]
        db.session.add_all(tipos)
        db.session.commit()

    if not Odontologo.query.first():
        odontologos = [
            Odontologo(nombre='Dr. Henry',      pin_acceso='7341'),
            Odontologo(nombre='Dr. Luigi',      pin_acceso='2856'),
            Odontologo(nombre='Dr. Joseph',     pin_acceso='9127'),
            Odontologo(nombre='Dra. Ginneth',   pin_acceso='4583'),
            Odontologo(nombre='Dra. Hernandez', pin_acceso='6219'),
            Odontologo(nombre='Dr. Angel',      pin_acceso='3748'),
            Odontologo(nombre='Dr. Neyra',      pin_acceso='5062'),
            Odontologo(nombre='Dra. Yuliana',   pin_acceso='8415'),
            Odontologo(nombre='Dr. Nino',       pin_acceso='1936'),
            Odontologo(nombre='Dr. Carlos',     pin_acceso='7284'),
            Odontologo(nombre='Dra. Ada',       pin_acceso='4651'),
            Odontologo(nombre='Dra. Delmira',   pin_acceso='2973'),
            Odontologo(nombre='Dra. Yudith',    pin_acceso='8340'),
            Odontologo(nombre='Dr. Glider',     pin_acceso='5187'),
            Odontologo(nombre='Dr. Quispe',     pin_acceso='3926'),
            Odontologo(nombre='Dra. Nakamoto',  pin_acceso='6043'),
            Odontologo(nombre='Dra. Medina',    pin_acceso='1758'),
            Odontologo(nombre='Dr. Harold',     pin_acceso='9432'),
            Odontologo(nombre='Dra. Ayala',     pin_acceso='4867'),
            Odontologo(nombre='Dra. Liliana',   pin_acceso='7195'),
        ]
        db.session.add_all(odontologos)
        db.session.commit()
