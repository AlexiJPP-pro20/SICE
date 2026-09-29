import sys
import os
import hashlib

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import init_db, SessionLocal, Base, engine, Alumno, Representante, Direccion, Materia, Nota, Profesor, Usuario

# ------------------------------------------------------------------
# PENSUM - Plan de Estudio Bachiller (31059) - Medio Turno
# Fuente: Ministerio del Poder Popular para la Educacion
# ------------------------------------------------------------------
PENSUM = {
    "1er Año": [
        "Castellano",
        "Inglés y Otras Lenguas Extranjeras",
        "Matemáticas",
        "Educación Física",
        "Arte y Patrimonio",
        "Ciencias Naturales",
        "Geografía, Historia y Ciudadanía",
        "Orientación y Convivencia",
        "Participación en Grupos de Creación, Recreación y Producción",
    ],
    "2do Año": [
        "Castellano",
        "Inglés y Otras Lenguas Extranjeras",
        "Matemáticas",
        "Educación Física",
        "Arte y Patrimonio",
        "Ciencias Naturales",
        "Geografía, Historia y Ciudadanía",
        "Orientación y Convivencia",
        "Participación en Grupos de Creación, Recreación y Producción",
    ],
    "3er Año": [
        "Castellano",
        "Inglés y Otras Lenguas Extranjeras",
        "Matemáticas",
        "Educación Física",
        "Física",
        "Química",
        "Biología",
        "Geografía, Historia y Ciudadanía",
        "Orientación y Convivencia",
        "Participación en Grupos de Creación, Recreación y Producción",
    ],
    "4to Año": [
        "Castellano",
        "Inglés y Otras Lenguas Extranjeras",
        "Matemáticas",
        "Educación Física",
        "Física",
        "Química",
        "Biología",
        "Geografía, Historia y Ciudadanía",
        "Formación para la Soberanía Nacional",
        "Orientación y Convivencia",
        "Participación en Grupos de Creación, Recreación y Producción",
    ],
    "5to Año": [
        "Castellano",
        "Inglés y Otras Lenguas Extranjeras",
        "Matemáticas",
        "Educación Física",
        "Física",
        "Química",
        "Biología",
        "Ciencias de la Tierra",
        "Geografía, Historia y Ciudadanía",
        "Formación para la Soberanía Nacional",
        "Orientación y Convivencia",
        "Participación en Grupos de Creación, Recreación y Producción",
    ],
}


def seed():
    # Borrar y recrear todas las tablas desde cero
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # ------------------------------------------------------------------
    # Usuario administrador
    # ------------------------------------------------------------------
    pwd_hash = hashlib.sha256("SICE".encode()).hexdigest()
    admin = Usuario(username="SICE", password=pwd_hash, rol="admin")
    db.add(admin)
    db.commit()

    # ------------------------------------------------------------------
    # Ubicacion
    # ------------------------------------------------------------------
    dir1 = Direccion(
        estado="La Guaira",
        municipio="Vargas",
        parroquia="Catia La Mar",
        detalle="Ciudad Caribia - Sector II",
    )
    db.add(dir1)
    db.commit()

    # ------------------------------------------------------------------
    # Representante
    # ------------------------------------------------------------------
    rep1 = Representante(
        cedula="V-11642977",
        nombre="Norka",
        apellido="Hernandez",
        telefono="0412-9943683",
        correo="norka@example.com",
        id_direccion=dir1.id_direccion,
    )
    db.add(rep1)
    db.commit()

    # ------------------------------------------------------------------
    # Alumno de prueba - 3er Año, Seccion A
    # ------------------------------------------------------------------
    alumno_prueba = Alumno(
        cedula="V-30123456",
        nombre="Juan Carlos",
        apellido="Palacio",
        fecha_nacimiento="15-05-2009",
        anio="3er Año",
        seccion="A",
        inasistencias=2,
        id_representante=rep1.cedula,
    )
    db.add(alumno_prueba)
    db.commit()

    # ------------------------------------------------------------------
    # Materias del pensum completo (51 combinaciones materia-grado)
    # ------------------------------------------------------------------
    materias_db = {}  # {(nombre, grado): Materia}
    total = 0
    for grado, lista in PENSUM.items():
        for nombre in lista:
            m = Materia(nombre=nombre, grado=grado)
            db.add(m)
            db.flush()
            materias_db[(nombre, grado)] = m
            total += 1
    db.commit()

    # ------------------------------------------------------------------
    # Notas de prueba para el alumno (3er Año - los 3 lapsos)
    # Quimica aplazada (promedio 8.16 < 10), resto aprobado
    # ------------------------------------------------------------------
    notas_prueba = [
        ("Castellano",                                                      1, 16.0),
        ("Castellano",                                                      2, 14.5),
        ("Castellano",                                                      3, 17.0),
        ("Inglés y Otras Lenguas Extranjeras",                              1, 12.0),
        ("Inglés y Otras Lenguas Extranjeras",                              2, 11.5),
        ("Inglés y Otras Lenguas Extranjeras",                              3, 13.0),
        ("Matemáticas",                                                     1, 18.5),
        ("Matemáticas",                                                     2, 15.0),
        ("Matemáticas",                                                     3, 16.0),
        ("Educación Física",                                                1, 20.0),
        ("Educación Física",                                                2, 19.0),
        ("Educación Física",                                                3, 20.0),
        ("Física",                                                          1, 14.0),
        ("Física",                                                          2, 13.5),
        ("Física",                                                          3, 15.0),
        ("Química",                                                         1,  8.0),
        ("Química",                                                         2,  7.5),
        ("Química",                                                         3,  9.0),
        ("Biología",                                                        1, 11.0),
        ("Biología",                                                        2, 12.0),
        ("Biología",                                                        3, 10.5),
        ("Geografía, Historia y Ciudadanía",                                1, 15.0),
        ("Geografía, Historia y Ciudadanía",                                2, 14.0),
        ("Geografía, Historia y Ciudadanía",                                3, 16.0),
        ("Orientación y Convivencia",                                       1, 18.0),
        ("Orientación y Convivencia",                                       2, 17.0),
        ("Orientación y Convivencia",                                       3, 19.0),
        ("Participación en Grupos de Creación, Recreación y Producción",    1, 16.0),
        ("Participación en Grupos de Creación, Recreación y Producción",    2, 15.0),
        ("Participación en Grupos de Creación, Recreación y Producción",    3, 17.0),
    ]

    for nombre_mat, lapso, calif in notas_prueba:
        mat = materias_db.get((nombre_mat, "3er Año"))
        if mat:
            nota = Nota(
                cedula_alumno=alumno_prueba.cedula,
                id_materia=mat.id_materia,
                calificacion=calif,
                lapso=lapso,
            )
            db.add(nota)

    db.commit()
    db.close()

    print(f"Pensum cargado: {total} combinaciones materia-grado.")
    print("Alumno de prueba: Juan Carlos Palacio (V-30123456) - 3er Año, Seccion A.")
    print("  - Quimica aplazada (promedio 8.16 < 10)")
    print("  - Resto de materias aprobadas.")
    print("Base de datos lista.")


if __name__ == "__main__":
    seed()
