import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import init_db, SessionLocal, Alumno, Representante, Direccion, Materia, Nota, Profesor, Usuario

def seed():
    init_db()
    db = SessionLocal()
    
    # Administrador
    admin = Usuario(username="admin", password="password")
    db.add(admin)
    db.commit()

    # Ubicación
    dir1 = Direccion(estado="La Guaira", municipio="Vargas", parroquia="Catia La Mar", detalle="Ciudad Caribia - Sector II")
    db.add(dir1)
    db.commit()

    # Representantes
    rep1 = Representante(cedula="V-11642977", nombre="Norka", apellido="Hernandez", telefono="0412-9943683", correo="norka@example.com", id_direccion=dir1.id_direccion)
    rep2 = Representante(cedula="V-14555666", nombre="Pedro", apellido="Perez", telefono="0424-5551234", correo="pedro@example.com", id_direccion=dir1.id_direccion)
    rep3 = Representante(cedula="V-16777888", nombre="Elena", apellido="Gómez", telefono="0416-7778899", correo="elena@example.com", id_direccion=dir1.id_direccion)
    db.add_all([rep1, rep2, rep3])
    db.commit()

    # Alumno 1: APROBADO (Promedio 16.75, Inasistencias 2)
    alu1 = Alumno(
        cedula="V-30123456", 
        nombre="Juan Carlos", 
        apellido="Palacio", 
        fecha_nacimiento="15-05-2009", 
        anio="3er Año", 
        seccion="A", 
        inasistencias=2,
        id_representante=rep1.cedula
    )

    # Alumno 2: REPROBADO POR INASISTENCIAS (> 4 faltas)
    alu2 = Alumno(
        cedula="V-31987654", 
        nombre="Juan Carlos", 
        apellido="Pérez", 
        fecha_nacimiento="20-11-2007", 
        anio="5to Año", 
        seccion="B", 
        inasistencias=5,
        id_representante=rep2.cedula
    )

    # Alumno 3: REPROBADO POR PROMEDIO (< 10 pts)
    alu3 = Alumno(
        cedula="V-32111222", 
        nombre="Ana", 
        apellido="Gómez", 
        fecha_nacimiento="10-02-2010", 
        anio="2do Año", 
        seccion="C", 
        inasistencias=1,
        id_representante=rep3.cedula
    )

    db.add_all([alu1, alu2, alu3])
    db.commit()

    # Materias
    mat1 = Materia(nombre="Matemáticas", grado="3er Año")
    mat2 = Materia(nombre="Física", grado="5to Año")
    mat3 = Materia(nombre="Castellano", grado="2do Año")
    db.add_all([mat1, mat2, mat3])
    db.commit()

    # Notas
    # Alumno 1
    n1 = Nota(cedula_alumno=alu1.cedula, id_materia=mat1.id_materia, calificacion=18.5, lapso=1)
    n2 = Nota(cedula_alumno=alu1.cedula, id_materia=mat1.id_materia, calificacion=15.0, lapso=2)
    # Alumno 2
    n3 = Nota(cedula_alumno=alu2.cedula, id_materia=mat2.id_materia, calificacion=19.0, lapso=1)
    # Alumno 3 (Notas bajas: 8.0, 7.5, 9.0 -> Promedio 8.16 < 10)
    n4 = Nota(cedula_alumno=alu3.cedula, id_materia=mat3.id_materia, calificacion=8.0, lapso=1)
    n5 = Nota(cedula_alumno=alu3.cedula, id_materia=mat3.id_materia, calificacion=7.5, lapso=2)
    n6 = Nota(cedula_alumno=alu3.cedula, id_materia=mat3.id_materia, calificacion=9.0, lapso=3)
    db.add_all([n1, n2, n3, n4, n5, n6])
    db.commit()

    print("Base de datos sembrada correctamente con los 3 casos de prueba condicionales.")
    db.close()

if __name__ == "__main__":
    seed()
