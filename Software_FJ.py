"""
Sistema Integral de Gestión de Clientes, Servicios y Reservas
Empresa: Software FJ
Principios: Abstracción, Herencia, Polimorfismo, Encapsulación, Manejo de Excepciones
Sin uso de bases de datos - gestión mediante objetos, listas y archivos de logs
"""

from abc import ABC, abstractmethod
from datetime import datetime, date
import os

# ============================================================
# MANEJO DE EXCEPCIONES PERSONALIZADAS
# ============================================================

class SoftwareFJException(Exception):
    """Excepción base del sistema Software FJ."""
    pass

class ClienteInvalidoError(SoftwareFJException):
    """Se lanza cuando los datos del cliente son inválidos."""
    pass

class ServicioNoDisponibleError(SoftwareFJException):
    """Se lanza cuando el servicio solicitado no está disponible."""
    pass

class ReservaInvalidaError(SoftwareFJException):
    """Se lanza cuando los datos de la reserva son incorrectos."""
    pass

class OperacionNoPermitidaError(SoftwareFJException):
    """Se lanza cuando se intenta una operación no permitida."""
    pass

class ParametroFaltanteError(SoftwareFJException):
    """Se lanza cuando falta un parámetro requerido."""
    pass

class CalculoInconsistenteError(SoftwareFJException):
    """Se lanza cuando hay inconsistencias en cálculos."""
    pass


# ============================================================
# LOGGER - Registro de eventos y errores en archivo
# ============================================================

class Logger:
    """Gestiona el registro de eventos y errores en un archivo de logs."""

    LOG_FILE = "softwarefj_logs.txt"

    @staticmethod
    def _escribir(nivel: str, mensaje: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linea = f"[{timestamp}] [{nivel}] {mensaje}\n"
        try:
            with open(Logger.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(linea)
        except IOError as e:
            print(f"[ADVERTENCIA] No se pudo escribir en el log: {e}")
        print(linea.strip())

    @staticmethod
    def info(mensaje: str):
        Logger._escribir("INFO", mensaje)

    @staticmethod
    def error(mensaje: str):
        Logger._escribir("ERROR", mensaje)

    @staticmethod
    def advertencia(mensaje: str):
        Logger._escribir("ADVERTENCIA", mensaje)

    @staticmethod
    def evento(mensaje: str):
        Logger._escribir("EVENTO", mensaje)


# ============================================================
# CLASE ABSTRACTA BASE - Entidad
# ============================================================

class Entidad(ABC):
    """Clase abstracta que representa entidades generales del sistema."""

    def __init__(self, id_entidad: int):
        if not isinstance(id_entidad, int) or id_entidad <= 0:
            raise ParametroFaltanteError(f"El ID de entidad debe ser un entero positivo. Recibido: {id_entidad}")
        self.__id_entidad = id_entidad

    @property
    def id_entidad(self):
        return self.__id_entidad

    @abstractmethod
    def describir(self) -> str:
        pass

    @abstractmethod
    def validar(self) -> bool:
        pass

    def __str__(self):
        return self.describir()


# ============================================================
# CLASE CLIENTE
# ============================================================

class Cliente(Entidad):
    """Clase con validaciones robustas y encapsulación de datos personales."""

    def __init__(self, id_cliente: int, nombre: str, email: str, telefono: str):
        super().__init__(id_cliente)
        self.__nombre = None
        self.__email = None
        self.__telefono = None
        self.nombre = nombre
        self.email = email
        self.telefono = telefono

    # --- Propiedades con validación ---

    @property
    def nombre(self):
        return self.__nombre

    @nombre.setter
    def nombre(self, valor: str):
        if not valor or not isinstance(valor, str) or len(valor.strip()) < 2:
            raise ClienteInvalidoError(f"Nombre inválido: '{valor}'. Debe tener al menos 2 caracteres.")
        self.__nombre = valor.strip().title()

    @property
    def email(self):
        return self.__email

    @email.setter
    def email(self, valor: str):
        if not valor or "@" not in valor or "." not in valor.split("@")[-1]:
            raise ClienteInvalidoError(f"Email inválido: '{valor}'.")
        self.__email = valor.strip().lower()

    @property
    def telefono(self):
        return self.__telefono

    @telefono.setter
    def telefono(self, valor: str):
        digitos = valor.replace("+", "").replace("-", "").replace(" ", "")
        if not digitos.isdigit() or len(digitos) < 7:
            raise ClienteInvalidoError(f"Teléfono inválido: '{valor}'. Debe contener al menos 7 dígitos.")
        self.__telefono = valor.strip()

    def describir(self) -> str:
        return (f"Cliente[ID={self.id_entidad}, Nombre={self.__nombre}, "
                f"Email={self.__email}, Tel={self.__telefono}]")

    def validar(self) -> bool:
        return bool(self.__nombre and self.__email and self.__telefono)


# ============================================================
# CLASE ABSTRACTA SERVICIO + ESPECIALIZACIONES
# ============================================================

class Servicio(Entidad, ABC):
    """Clase abstracta para todos los servicios de Software FJ."""

    def __init__(self, id_servicio: int, nombre: str, precio_base: float, disponible: bool = True):
        super().__init__(id_servicio)
        if not nombre or len(nombre.strip()) < 3:
            raise ParametroFaltanteError("El nombre del servicio debe tener al menos 3 caracteres.")
        if precio_base < 0:
            raise CalculoInconsistenteError("El precio base no puede ser negativo.")
        self.__nombre = nombre.strip()
        self.__precio_base = precio_base
        self.__disponible = disponible

    @property
    def nombre(self):
        return self.__nombre

    @property
    def precio_base(self):
        return self.__precio_base

    @property
    def disponible(self):
        return self.__disponible

    @disponible.setter
    def disponible(self, valor: bool):
        self.__disponible = valor

    def validar(self) -> bool:
        return self.__disponible and self.__precio_base >= 0

    @abstractmethod
    def calcular_costo(self, duracion_horas: float, **kwargs) -> float:
        pass

    @abstractmethod
    def describir_servicio(self) -> str:
        pass

    def describir(self) -> str:
        estado = "Disponible" if self.__disponible else "No disponible"
        return (f"Servicio[ID={self.id_entidad}, Nombre={self.__nombre}, "
                f"Precio base=${self.__precio_base:.2f}/h, Estado={estado}] - {self.describir_servicio()}")

    def verificar_disponibilidad(self):
        if not self.__disponible:
            raise ServicioNoDisponibleError(
                f"El servicio '{self.__nombre}' (ID={self.id_entidad}) no está disponible actualmente."
            )


# --- Servicio 1: Reserva de Sala ---

class ServicioReservaSala(Servicio):
    """Servicio de reserva de salas de reuniones o conferencias."""

    def __init__(self, id_servicio: int, nombre: str, precio_base: float,
                 capacidad: int, disponible: bool = True):
        super().__init__(id_servicio, nombre, precio_base, disponible)
        if capacidad <= 0:
            raise ParametroFaltanteError("La capacidad de la sala debe ser mayor a 0.")
        self.__capacidad = capacidad

    @property
    def capacidad(self):
        return self.__capacidad

    def calcular_costo(self, duracion_horas: float, descuento: float = 0.0, **kwargs) -> float:
        """Calcula costo con descuento opcional."""
        if duracion_horas <= 0:
            raise CalculoInconsistenteError("La duración debe ser mayor a 0 horas.")
        if not (0 <= descuento <= 1):
            raise CalculoInconsistenteError("El descuento debe estar entre 0 y 1 (0% a 100%).")
        costo = self.precio_base * duracion_horas
        costo_final = costo * (1 - descuento)
        return round(costo_final, 2)

    def describir_servicio(self) -> str:
        return f"Sala con capacidad para {self.__capacidad} personas."

    def validar(self) -> bool:
        return super().validar() and self.__capacidad > 0


# --- Servicio 2: Alquiler de Equipos ---

class ServicioAlquilerEquipo(Servicio):
    """Servicio de alquiler de equipos tecnológicos."""

    def __init__(self, id_servicio: int, nombre: str, precio_base: float,
                 tipo_equipo: str, disponible: bool = True):
        super().__init__(id_servicio, nombre, precio_base, disponible)
        if not tipo_equipo:
            raise ParametroFaltanteError("El tipo de equipo es requerido.")
        self.__tipo_equipo = tipo_equipo

    @property
    def tipo_equipo(self):
        return self.__tipo_equipo

    def calcular_costo(self, duracion_horas: float, impuesto: float = 0.19, **kwargs) -> float:
        """Calcula costo con impuesto (por defecto 19% IVA)."""
        if duracion_horas <= 0:
            raise CalculoInconsistenteError("La duración debe ser mayor a 0 horas.")
        if impuesto < 0:
            raise CalculoInconsistenteError("El impuesto no puede ser negativo.")
        costo = self.precio_base * duracion_horas
        costo_final = costo * (1 + impuesto)
        return round(costo_final, 2)

    def describir_servicio(self) -> str:
        return f"Alquiler de equipo: {self.__tipo_equipo}."

    def validar(self) -> bool:
        return super().validar() and bool(self.__tipo_equipo)


# --- Servicio 3: Asesoría Especializada ---

class ServicioAsesoria(Servicio):
    """Servicio de asesorías especializadas por expertos."""

    AREAS_VALIDAS = ["tecnologia", "legal", "financiera", "marketing", "rrhh"]

    def __init__(self, id_servicio: int, nombre: str, precio_base: float,
                 area: str, disponible: bool = True):
        super().__init__(id_servicio, nombre, precio_base, disponible)
        if area.lower() not in self.AREAS_VALIDAS:
            raise ParametroFaltanteError(
                f"Área de asesoría inválida: '{area}'. Válidas: {self.AREAS_VALIDAS}"
            )
        self.__area = area.lower()

    @property
    def area(self):
        return self.__area

    def calcular_costo(self, duracion_horas: float, nivel_experto: int = 1, **kwargs) -> float:
        """Calcula costo según nivel del experto (1=junior, 2=senior, 3=lead)."""
        if duracion_horas <= 0:
            raise CalculoInconsistenteError("La duración debe ser mayor a 0 horas.")
        if nivel_experto not in [1, 2, 3]:
            raise CalculoInconsistenteError("Nivel de experto inválido. Debe ser 1, 2 o 3.")
        multiplicadores = {1: 1.0, 2: 1.5, 3: 2.2}
        costo = self.precio_base * duracion_horas * multiplicadores[nivel_experto]
        return round(costo, 2)

    def describir_servicio(self) -> str:
        return f"Asesoría especializada en área: {self.__area.capitalize()}."

    def validar(self) -> bool:
        return super().validar() and self.__area in self.AREAS_VALIDAS


# ============================================================
# CLASE RESERVA
# ============================================================

class Reserva(Entidad):
    """Integra cliente, servicio, duración y estado con manejo de excepciones."""

    ESTADOS_VALIDOS = ["pendiente", "confirmada", "cancelada"]

    def __init__(self, id_reserva: int, cliente: Cliente, servicio: Servicio,
                 duracion_horas: float, fecha: date = None):
        super().__init__(id_reserva)
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("Se requiere un objeto Cliente válido.")
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("Se requiere un objeto Servicio válido.")
        if duracion_horas <= 0:
            raise ReservaInvalidaError("La duración de la reserva debe ser mayor a 0 horas.")

        self.__cliente = cliente
        self.__servicio = servicio
        self.__duracion_horas = duracion_horas
        self.__fecha = fecha or date.today()
        self.__estado = "pendiente"
        self.__costo = None

    @property
    def cliente(self):
        return self.__cliente

    @property
    def servicio(self):
        return self.__servicio

    @property
    def estado(self):
        return self.__estado

    @property
    def costo(self):
        return self.__costo

    @property
    def duracion_horas(self):
        return self.__duracion_horas

    def confirmar(self, **kwargs_costo):
        """Confirma la reserva verificando disponibilidad y calculando costo."""
        try:
            if self.__estado == "confirmada":
                raise OperacionNoPermitidaError(
                    f"La reserva ID={self.id_entidad} ya está confirmada."
                )
            if self.__estado == "cancelada":
                raise OperacionNoPermitidaError(
                    f"No se puede confirmar la reserva ID={self.id_entidad} porque está cancelada."
                )
            self.__servicio.verificar_disponibilidad()
            if not self.__cliente.validar():
                raise ClienteInvalidoError("El cliente asociado no tiene datos válidos.")
            self.__costo = self.__servicio.calcular_costo(self.__duracion_horas, **kwargs_costo)
            self.__estado = "confirmada"
            Logger.evento(
                f"Reserva ID={self.id_entidad} confirmada | "
                f"Cliente: {self.__cliente.nombre} | "
                f"Servicio: {self.__servicio.nombre} | "
                f"Costo: ${self.__costo:.2f}"
            )
        except (ServicioNoDisponibleError, ClienteInvalidoError,
                OperacionNoPermitidaError, CalculoInconsistenteError) as e:
            Logger.error(f"Error al confirmar reserva ID={self.id_entidad}: {e}")
            raise

    def cancelar(self):
        """Cancela la reserva si está en estado válido para cancelación."""
        try:
            if self.__estado == "cancelada":
                raise OperacionNoPermitidaError(
                    f"La reserva ID={self.id_entidad} ya está cancelada."
                )
            self.__estado = "cancelada"
            Logger.evento(
                f"Reserva ID={self.id_entidad} cancelada | "
                f"Cliente: {self.__cliente.nombre} | Servicio: {self.__servicio.nombre}"
            )
        except OperacionNoPermitidaError as e:
            Logger.error(f"Error al cancelar reserva ID={self.id_entidad}: {e}")
            raise

    def describir(self) -> str:
        costo_str = f"${self.__costo:.2f}" if self.__costo else "No calculado"
        return (
            f"Reserva[ID={self.id_entidad} | "
            f"Cliente: {self.__cliente.nombre} | "
            f"Servicio: {self.__servicio.nombre} | "
            f"Duración: {self.__duracion_horas}h | "
            f"Estado: {self.__estado.upper()} | "
            f"Costo: {costo_str} | "
            f"Fecha: {self.__fecha}]"
        )

    def validar(self) -> bool:
        return (self.__cliente.validar() and
                self.__servicio.validar() and
                self.__duracion_horas > 0 and
                self.__estado in self.ESTADOS_VALIDOS)


# ============================================================
# SISTEMA PRINCIPAL - Gestión integral
# ============================================================

class SistemaGestionFJ:
    """Controlador principal que gestiona clientes, servicios y reservas."""

    def __init__(self):
        self.__clientes: list[Cliente] = []
        self.__servicios: list[Servicio] = []
        self.__reservas: list[Reserva] = []
        self.__contador_reserva = 1
        Logger.info("Sistema Software FJ iniciado correctamente.")

    # --- Gestión de Clientes ---

    def registrar_cliente(self, id_c: int, nombre: str, email: str, telefono: str) -> Cliente:
        try:
            cliente = Cliente(id_c, nombre, email, telefono)
            self.__clientes.append(cliente)
            Logger.evento(f"Cliente registrado: {cliente.describir()}")
            return cliente
        except (ClienteInvalidoError, ParametroFaltanteError) as e:
            Logger.error(f"No se pudo registrar cliente '{nombre}': {e}")
            raise

    def buscar_cliente(self, id_c: int) -> Cliente:
        for c in self.__clientes:
            if c.id_entidad == id_c:
                return c
        raise ClienteInvalidoError(f"Cliente con ID={id_c} no encontrado.")

    # --- Gestión de Servicios ---

    def agregar_servicio(self, servicio: Servicio):
        try:
            if not isinstance(servicio, Servicio):
                raise ParametroFaltanteError("Se requiere un objeto Servicio válido.")
            self.__servicios.append(servicio)
            Logger.evento(f"Servicio agregado: {servicio.describir()}")
        except ParametroFaltanteError as e:
            Logger.error(f"No se pudo agregar servicio: {e}")
            raise

    def buscar_servicio(self, id_s: int) -> Servicio:
        for s in self.__servicios:
            if s.id_entidad == id_s:
                return s
        raise ServicioNoDisponibleError(f"Servicio con ID={id_s} no encontrado.")

    # --- Gestión de Reservas ---

    def crear_reserva(self, id_cliente: int, id_servicio: int,
                      duracion_horas: float) -> Reserva:
        try:
            cliente = self.buscar_cliente(id_cliente)
            servicio = self.buscar_servicio(id_servicio)
            reserva = Reserva(self.__contador_reserva, cliente, servicio, duracion_horas)
            self.__reservas.append(reserva)
            self.__contador_reserva += 1
            Logger.evento(f"Reserva creada (pendiente): {reserva.describir()}")
            return reserva
        except (ClienteInvalidoError, ServicioNoDisponibleError, ReservaInvalidaError) as e:
            Logger.error(f"Error al crear reserva: {e}")
            raise

    def confirmar_reserva(self, id_reserva: int, **kwargs):
        try:
            reserva = self.__buscar_reserva(id_reserva)
            reserva.confirmar(**kwargs)
        except SoftwareFJException as e:
            Logger.error(f"Fallo al confirmar reserva ID={id_reserva}: {e}")
            raise

    def cancelar_reserva(self, id_reserva: int):
        try:
            reserva = self.__buscar_reserva(id_reserva)
            reserva.cancelar()
        except SoftwareFJException as e:
            Logger.error(f"Fallo al cancelar reserva ID={id_reserva}: {e}")
            raise

    def __buscar_reserva(self, id_reserva: int) -> Reserva:
        for r in self.__reservas:
            if r.id_entidad == id_reserva:
                return r
        raise ReservaInvalidaError(f"Reserva con ID={id_reserva} no encontrada.")

    def listar_reservas(self):
        if not self.__reservas:
            Logger.advertencia("No hay reservas registradas.")
            return
        print("\n" + "="*70)
        print("  LISTADO DE RESERVAS - SOFTWARE FJ")
        print("="*70)
        for r in self.__reservas:
            print(f"  {r.describir()}")
        print("="*70 + "\n")


# ============================================================
# DEMOSTRACIÓN: 10 OPERACIONES COMPLETAS
# ============================================================

def ejecutar_demo():
    print("\n" + "="*70)
    print("  SISTEMA INTEGRAL - SOFTWARE FJ  |  DEMO 10 OPERACIONES")
    print("="*70 + "\n")

    sistema = SistemaGestionFJ()

    # ---- Crear servicios ----
    sala_a = ServicioReservaSala(1, "Sala Ejecutiva A", 50.0, capacidad=10)
    equipo_laptop = ServicioAlquilerEquipo(2, "Laptop HP ProBook", 15.0, tipo_equipo="Laptop")
    asesoria_tech = ServicioAsesoria(3, "Asesoría Tecnológica", 80.0, area="tecnologia")
    sala_indisponible = ServicioReservaSala(4, "Sala B (en mantenimiento)", 30.0,
                                            capacidad=5, disponible=False)

    sistema.agregar_servicio(sala_a)
    sistema.agregar_servicio(equipo_laptop)
    sistema.agregar_servicio(asesoria_tech)
    sistema.agregar_servicio(sala_indisponible)

    # ================================================================
    # OPERACIÓN 1: Registro de cliente válido
    # ================================================================
    print("\n>>> OPERACIÓN 1: Registrar cliente válido")
    try:
        c1 = sistema.registrar_cliente(1, "Ana García", "ana@empresa.com", "3001234567")
        print(f"    OK -> {c1.describir()}")
    except SoftwareFJException as e:
        print(f"    ERROR: {e}")

    # ================================================================
    # OPERACIÓN 2: Registro de cliente inválido (email incorrecto)
    # ================================================================
    print("\n>>> OPERACIÓN 2: Registrar cliente con email inválido")
    try:
        c_malo = sistema.registrar_cliente(2, "Pedro", "correo_sin_arroba", "3009999999")
        print(f"    OK -> {c_malo.describir()}")
    except ClienteInvalidoError as e:
        print(f"    ERROR esperado (ClienteInvalidoError): {e}")

    # ================================================================
    # OPERACIÓN 3: Registro de segundo cliente válido
    # ================================================================
    print("\n>>> OPERACIÓN 3: Registrar segundo cliente válido")
    try:
        c2 = sistema.registrar_cliente(3, "Luis Martínez", "luis@correo.com", "3107654321")
        print(f"    OK -> {c2.describir()}")
    except SoftwareFJException as e:
        print(f"    ERROR: {e}")

    # ================================================================
    # OPERACIÓN 4: Crear y confirmar reserva de sala con descuento
    # ================================================================
    print("\n>>> OPERACIÓN 4: Crear y confirmar reserva de sala con 20% descuento")
    try:
        r1 = sistema.crear_reserva(id_cliente=1, id_servicio=1, duracion_horas=3)
        sistema.confirmar_reserva(r1.id_entidad, descuento=0.20)
        print(f"    OK -> {r1.describir()}")
    except SoftwareFJException as e:
        print(f"    ERROR: {e}")

    # ================================================================
    # OPERACIÓN 5: Crear y confirmar reserva de equipo con IVA
    # ================================================================
    print("\n>>> OPERACIÓN 5: Crear y confirmar reserva de equipo (con IVA 19%)")
    try:
        r2 = sistema.crear_reserva(id_cliente=3, id_servicio=2, duracion_horas=8)
        sistema.confirmar_reserva(r2.id_entidad, impuesto=0.19)
        print(f"    OK -> {r2.describir()}")
    except SoftwareFJException as e:
        print(f"    ERROR: {e}")

    # ================================================================
    # OPERACIÓN 6: Crear y confirmar asesoría con experto nivel 3
    # ================================================================
    print("\n>>> OPERACIÓN 6: Reservar asesoría con experto nivel 3 (Lead)")
    try:
        r3 = sistema.crear_reserva(id_cliente=1, id_servicio=3, duracion_horas=2)
        sistema.confirmar_reserva(r3.id_entidad, nivel_experto=3)
        print(f"    OK -> {r3.describir()}")
    except SoftwareFJException as e:
        print(f"    ERROR: {e}")

    # ================================================================
    # OPERACIÓN 7: Intentar reservar servicio no disponible
    # ================================================================
    print("\n>>> OPERACIÓN 7: Intentar reservar servicio NO disponible (Sala en mantenimiento)")
    try:
        r4 = sistema.crear_reserva(id_cliente=3, id_servicio=4, duracion_horas=1)
        sistema.confirmar_reserva(r4.id_entidad)
        print(f"    OK -> {r4.describir()}")
    except ServicioNoDisponibleError as e:
        print(f"    ERROR esperado (ServicioNoDisponibleError): {e}")
    except SoftwareFJException as e:
        print(f"    ERROR: {e}")

    # ================================================================
    # OPERACIÓN 8: Cancelar una reserva confirmada
    # ================================================================
    print("\n>>> OPERACIÓN 8: Cancelar la reserva #1 (confirmada)")
    try:
        sistema.cancelar_reserva(1)
        print(f"    OK -> {r1.describir()}")
    except SoftwareFJException as e:
        print(f"    ERROR: {e}")

    # ================================================================
    # OPERACIÓN 9: Intentar confirmar una reserva ya cancelada
    # ================================================================
    print("\n>>> OPERACIÓN 9: Intentar confirmar reserva ya cancelada (#1)")
    try:
        sistema.confirmar_reserva(1)
        print("    OK -> Confirmada (no debería llegar aquí)")
    except OperacionNoPermitidaError as e:
        print(f"    ERROR esperado (OperacionNoPermitidaError): {e}")

    # ================================================================
    # OPERACIÓN 10: Intentar crear reserva con duración inválida
    # ================================================================
    print("\n>>> OPERACIÓN 10: Crear reserva con duración negativa (inválida)")
    try:
        r5 = sistema.crear_reserva(id_cliente=1, id_servicio=2, duracion_horas=-5)
        print(f"    OK -> {r5.describir()}")
    except ReservaInvalidaError as e:
        print(f"    ERROR esperado (ReservaInvalidaError): {e}")

    # ---- Resumen final ----
    sistema.listar_reservas()
    print(f"\n  Logs guardados en: {os.path.abspath(Logger.LOG_FILE)}")
    print("\n" + "="*70)
    print("  FIN DE DEMOSTRACIÓN - SISTEMA SOFTWARE FJ")
    print("="*70 + "\n")


if __name__ == "__main__":
    ejecutar_demo()
