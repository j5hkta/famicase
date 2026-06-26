import os
from app import create_app, db
from app.models import Usuario, Odontologo, TipoTrabajo, Trabajo, Pago, Material
from werkzeug.security import generate_password_hash
from datetime import date

app = create_app()


def insertar_datos_iniciales():
    if TipoTrabajo.query.first():
        return  # Ya hay datos

    # Tipos de trabajo reales
    tipos = [
        TipoTrabajo(nombre='Juego de totales ivostar',                              complejidad='complejo', precio_base=400),
        TipoTrabajo(nombre='Juego de totales',                                       complejidad='complejo', precio_base=300),
        TipoTrabajo(nombre='Parcial Removible (Con Wipla)',                          complejidad='sencillo', precio_base=120),
        TipoTrabajo(nombre='Base Metálica (inferior o superior)',                    complejidad='complejo', precio_base=250),
        TipoTrabajo(nombre='Base Metálica placa total o rejilla',                    complejidad='complejo', precio_base=300),
        TipoTrabajo(nombre='Base Metálica solo estructura metálica',                 complejidad='sencillo', precio_base=200),
        TipoTrabajo(nombre='Corona de Porcelana con hombro cerámico',               complejidad='complejo', precio_base=100),
        TipoTrabajo(nombre='Corona de Porcelana y veneer',                           complejidad='complejo', precio_base=90),
        TipoTrabajo(nombre='Corona jacket (ivocron)',                                complejidad='sencillo', precio_base=60),
        TipoTrabajo(nombre='Corona completa de metal y incrustación',               complejidad='sencillo', precio_base=60),
        TipoTrabajo(nombre='Perno directo e indirecto',                              complejidad='sencillo', precio_base=25),
        TipoTrabajo(nombre='Falsa encía por pieza',                                  complejidad='sencillo', precio_base=30),
        TipoTrabajo(nombre='Maquillaje por pieza',                                   complejidad='sencillo', precio_base=20),
        TipoTrabajo(nombre='Rebasado sup. o inf. (Termocurable)',                    complejidad='sencillo', precio_base=60),
        TipoTrabajo(nombre='Reparación simple',                                      complejidad='sencillo', precio_base=50),
        TipoTrabajo(nombre='Placas de contención',                                   complejidad='sencillo', precio_base=80),
        TipoTrabajo(nombre='Repetición de metal',                                    complejidad='sencillo', precio_base=20),
        TipoTrabajo(nombre='Carillas libres de metal e.max, monolíticas, incrustación', complejidad='complejo', precio_base=200),
        TipoTrabajo(nombre='Coronas de zirconio',                                    complejidad='complejo', precio_base=200),
        TipoTrabajo(nombre='Provisionales por pieza',                                complejidad='sencillo', precio_base=20),
        TipoTrabajo(nombre='Flexible individuales hasta 4 dientes',                  complejidad='complejo', precio_base=200),
        TipoTrabajo(nombre='Flexibles parciales',                                    complejidad='complejo', precio_base=250),
        TipoTrabajo(nombre='Flexibles totales',                                      complejidad='complejo', precio_base=300),
    ]
    db.session.add_all(tipos)

    # Odontólogos reales con PINs seguros
    odontologos = [
        Odontologo(nombre='Dr. Henry',      pin_acceso='7341'),
        Odontologo(nombre='Dr. Luigi',      pin_acceso='2856'),
        Odontologo(nombre='Dr. Joseph',     pin_acceso='9127'),
        Odontologo(nombre='Dra. Ginneth',   pin_acceso='4583'),
        Odontologo(nombre='Dra. Hernández', pin_acceso='6219'),
        Odontologo(nombre='Dr. Ángel',      pin_acceso='3748'),
        Odontologo(nombre='Dr. Neyra',      pin_acceso='5062'),
        Odontologo(nombre='Dra. Yuliana',   pin_acceso='8415'),
        Odontologo(nombre='Dr. Niño',       pin_acceso='1936'),
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
    print("Datos iniciales insertados correctamente.")


def migrar_columnas():
    with db.engine.connect() as conn:
        try:
            conn.execute(db.text("ALTER TABLE odontologos ADD COLUMN pin_acceso VARCHAR(10)"))
            conn.commit()
        except Exception:
            pass


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        migrar_columnas()

        # Backup automático al arrancar (una vez al día)
        from app.routes.dashboard import crear_backup, listar_backups
        backups = listar_backups()
        hoy_str = __import__('datetime').date.today().strftime('%Y%m%d')
        ya_hay_backup_hoy = any(hoy_str in b['nombre'] for b in backups)
        if not ya_hay_backup_hoy:
            nombre = crear_backup()
            if nombre:
                print(f"Backup automático creado: {nombre}")

        # Admin por defecto
        if not Usuario.query.filter_by(username='admin').first():
            admin = Usuario(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                nombre='Administrador',
                activo=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Usuario admin creado.")

        insertar_datos_iniciales()

    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug, host='0.0.0.0', port=5000)
