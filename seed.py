import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import init_db, SessionLocal, Alumno, Representante, Direccion, Materia, Nota, Profesor, Usuario

def seed():
    init_db()
    db = SessionLocal()
    
    # Crear administrador por defecto
    admin = Usuario(username="admin", password="password")
    db.add(admin)
    db.commit()

    # Crear direccion institucional
    dir1 = Direccion(estado="La Guaira", municipio="Vargas", parroquia="Catia La Mar", detalle="Ciudad Caribia - Sector II")
    db.add(dir1)
    db.commit()

    # Representante 1
    rep1 = Representante(cedula="V-11642977", nombre="Norka", apellido="Hernandez", telefono="0412-9943683", correo="norka@example.com", id_direccion=dir1.id_direccion)
    # Representante 2
    rep2 = Representante(cedula="V-14555666", nombre="Pedro", apellido="Perez", telefono="0424-5551234", correo="pedro@example.com", id_direccion=dir1.id_direccion)
    db.add_all([rep1, rep2])
    db.commit()

    # Alumno 1 (3er Año - Sección A)
    alu1 = Alumno(
        cedula="V-30123456", 
        nombre="Juan Carlos", 
        apellido="Palacio", 
        fecha_nacimiento="15-05-2009", 
        anio="3er Año", 
        seccion="A", 
        id_representante=rep1.cedula
    )

    # Alumno 2 (5to Año - Sección B) - Mismo nombre, distinto nivel y cédula
    alu2 = Alumno(
        cedula="V-31987654", 
        nombre="Juan Carlos", 
        apellido="Pérez", 
        fecha_nacimiento="20-11-2007", 
        anio="5to Año", 
        seccion="B", 
        id_representante=rep2.cedula
    )

    db.add_all([alu1, alu2])
    db.commit()

    # Crear materias
    mat1 = Materia(nombre="Matemáticas", grado="3er Año")
    mat2 = Materia(nombre="Física", grado="5to Año")
    db.add_all([mat1, mat2])
    db.commit()

    # Crear notas
    n1 = Nota(cedula_alumno=alu1.cedula, id_materia=mat1.id_materia, calificacion=18.5, lapso=1)
    n2 = Nota(cedula_alumno=alu1.cedula, id_materia=mat1.id_materia, calificacion=15.0, lapso=2)
    n3 = Nota(cedula_alumno=alu2.cedula, id_materia=mat2.id_materia, calificacion=19.0, lapso=1)
    db.add_all([n1, n2, n3])
    db.commit()

    print("Base de datos sembrada correctamente con alumnos de 3er y 5to Año.")
    db.close()

if __name__ == "__main__":
    seed()
