from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class Direccion(Base):
    __tablename__ = 'direccion'
    id_direccion = Column(Integer, primary_key=True, autoincrement=True)
    estado = Column(String(50), nullable=False)
    municipio = Column(String(50), nullable=False)
    parroquia = Column(String(50), nullable=False)
    detalle = Column(String(200), nullable=False)

    representantes = relationship("Representante", back_populates="direccion")

class Representante(Base):
    __tablename__ = 'representante'
    cedula = Column(String(15), primary_key=True)
    nombre = Column(String(50), nullable=False)
    apellido = Column(String(50), nullable=False)
    telefono = Column(String(20), nullable=False)
    correo = Column(String(100), nullable=False)
    id_direccion = Column(Integer, ForeignKey('direccion.id_direccion'))

    direccion = relationship("Direccion", back_populates="representantes")
    alumnos = relationship("Alumno", back_populates="representante")

class Profesor(Base):
    __tablename__ = 'profesor'
    cedula = Column(String(15), primary_key=True)
    nombre = Column(String(50), nullable=False)
    apellido = Column(String(50), nullable=False)
    telefono = Column(String(20), nullable=False)
    especialidad = Column(String(50), nullable=False)

class Alumno(Base):
    __tablename__ = 'alumno'
    cedula = Column(String(15), primary_key=True)
    nombre = Column(String(50), nullable=False)
    apellido = Column(String(50), nullable=False)
    fecha_nacimiento = Column(String(15), nullable=True) # DD-MM-AAAA
    anio = Column(String(20), default="1er Año", nullable=False)
    seccion = Column(String(10), default="A", nullable=False)
    id_representante = Column(String(15), ForeignKey('representante.cedula'))

    representante = relationship("Representante", back_populates="alumnos")
    notas = relationship("Nota", back_populates="alumno")

class Usuario(Base):
    __tablename__ = 'usuario'
    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False) # Usar hashes en prod

class Materia(Base):
    __tablename__ = 'materia'
    id_materia = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False)
    grado = Column(String(20), nullable=False)

class Nota(Base):
    __tablename__ = 'nota'
    id_nota = Column(Integer, primary_key=True, autoincrement=True)
    cedula_alumno = Column(String(15), ForeignKey('alumno.cedula'))
    id_materia = Column(Integer, ForeignKey('materia.id_materia'))
    cedula_profesor = Column(String(15), ForeignKey('profesor.cedula'))
    calificacion = Column(Float, nullable=False)
    lapso = Column(Integer, nullable=False) # 1, 2, 3

    alumno = relationship("Alumno", back_populates="notas")
    materia = relationship("Materia")
    profesor = relationship("Profesor")

# Configuración de SQLite local
engine = create_engine('sqlite:///sice.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
