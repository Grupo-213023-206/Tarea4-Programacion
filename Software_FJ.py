"""
Sistema Integral de Gestión de Clientes, Servicios y Reservas
Empresa: Software FJ
"""

import tkinter as tk
from tkinter import ttk, messagebox
from abc import ABC, abstractmethod
from datetime import datetime, date
import os

# ============================================================
# MANEJO DE EXCEPCIONES PERSONALIZADAS
# ============================================================

class SoftwareFJException(Exception): pass        # Excepción base del sistema
class ClienteInvalidoError(SoftwareFJException): pass  # Datos del cliente inválidos
class ServicioNoDisponibleError(SoftwareFJException): pass # Servicio no disponible
class ReservaInvalidaError(SoftwareFJException): pass  # Datos de reserva incorrectos
class OperacionNoPermitidaError(SoftwareFJException): pass # Operación no permitida
class ParametroFaltanteError(SoftwareFJException): pass # Falta un parámetro requerido
class CalculoInconsistenteError(SoftwareFJException): pass # Inconsistencia en cálculos


# ============================================================
# LOGGER - Registro de eventos y errores en archivo
# ============================================================

class Logger:
    """Gestiona el registro de eventos y errores en un archivo de logs."""

    LOG_FILE = "softwarefj_logs.txt"
    _widget = None  # referencia al Text widget de la GUI

    @staticmethod
    def _escribir(nivel: str, mensaje: str):
        ts = datetime.now().strftime("%H:%M:%S")
        linea = f"[{ts}] [{nivel}] {mensaje}\n"
        try:
            with open(Logger.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(linea + "\n")
        except IOError:
            pass
        if Logger._widget:
            Logger._widget(nivel, linea)

    @staticmethod
    def info(m): Logger._escribir("INFO", m)
    @staticmethod
    def error(m): Logger._escribir("ERROR", m)
    @staticmethod
    def advertencia(m): Logger._escribir("ADVERTENCIA", m)
    @staticmethod
    def evento(m): Logger._escribir("EVENTO", m)


# ============================================================
# CLASE ABSTRACTA BASE - Entidad
# ============================================================

class Entidad(ABC):
    """Clase abstracta que representa entidades generales del sistema."""

    def __init__(self, id_entidad: int):
        if not isinstance(id_entidad, int) or id_entidad <= 0:
            raise ParametroFaltanteError(f"ID inválido: {id_entidad}")
        self.__id = id_entidad

    @property
    def id_entidad(self): return self.__id

    @abstractmethod
    def describir(self) -> str: pass

    @abstractmethod
    def validar(self) -> bool: pass

    def __str__(self): return self.describir()


# ============================================================
# CLASE CLIENTE
# ============================================================

class Cliente(Entidad):
    """Clase con validaciones robustas y encapsulación de datos personales."""

    def __init__(self, id_c, nombre, email, telefono):
        super().__init__(id_c)
        self.__nombre = self.__email = self.__telefono = None
        self.nombre = nombre
        self.email = email
        self.telefono = telefono

    # --- Propiedades con validación ---

    @property
    def nombre(self): return self.__nombre
    @nombre.setter
    def nombre(self, v):
        if not v or len(v.strip()) < 2:
            raise ClienteInvalidoError(f"Nombre inválido: '{v}'")
        self.__nombre = v.strip().title()

    @property
    def email(self): return self.__email
    @email.setter
    def email(self, v):
        if not v or "@" not in v or "." not in v.split("@")[-1]:
            raise ClienteInvalidoError(f"Email inválido: '{v}'")
        self.__email = v.strip().lower()

    @property
    def telefono(self): return self.__telefono
    @telefono.setter
    def telefono(self, v):
        d = v.replace("+","").replace("-","").replace(" ","")
        if not d.isdigit() or len(d) < 7:
            raise ClienteInvalidoError(f"Teléfono inválido: '{v}'")
        self.__telefono = v.strip()

    def describir(self):
        return f"[{self.id_entidad}] {self.__nombre} | {self.__email} | {self.__telefono}"
    def validar(self): return bool(self.__nombre and self.__email and self.__telefono)

# ============================================================
# CLASE ABSTRACTA SERVICIO + ESPECIALIZACIONES
# ============================================================

class Servicio(Entidad, ABC):
    """Clase abstracta para todos los servicios de Software FJ."""

    def __init__(self, id_s, nombre, precio_base, disponible=True):
        super().__init__(id_s)
        if not nombre or len(nombre.strip()) < 3:
            raise ParametroFaltanteError("Nombre de servicio demasiado corto.")
        if precio_base < 0:
            raise CalculoInconsistenteError("Precio base negativo.")
        self.__nombre = nombre.strip()
        self.__precio_base = precio_base
        self.__disponible = disponible

    @property
    def nombre(self): return self.__nombre
    @property
    def precio_base(self): return self.__precio_base
    @property
    def disponible(self): return self.__disponible
    @disponible.setter
    def disponible(self, v: bool): self.__disponible = v

    def validar(self) -> bool: return self.__disponible and self.__precio_base >= 0

    @abstractmethod
    def calcular_costo(self, duracion_horas: float, **kwargs) -> float: pass
    @abstractmethod
    def describir_servicio(self) -> str: pass
    @abstractmethod
    def tipo(self) -> str: pass

    def describir(self):
        est = "Disponible" if self.__disponible else "No disponible"
        return f"[{self.id_entidad}] {self.__nombre} | ${self.__precio_base}/h | {est}"

    def verificar_disponibilidad(self):
        if not self.__disponible:
            raise ServicioNoDisponibleError(
                f"Servicio '{self.__nombre}' no está disponible.")

# --- Servicio 1: Reserva de Sala ---

class ServicioReservaSala(Servicio):
    """Servicio de reserva de salas de reuniones o conferencias."""

    def __init__(self, id_s, nombre, precio_base, capacidad, disponible=True):
        super().__init__(id_s, nombre, precio_base, disponible)
        if capacidad <= 0: raise ParametroFaltanteError("Capacidad inválida.")
        self.__capacidad = capacidad

    def tipo(self): return "Sala"
    def describir_servicio(self): return f"Sala p/{self.__capacidad} personas"

    def calcular_costo(self, duracion_horas, descuento=0.0, **kw):
        if duracion_horas <= 0: raise CalculoInconsistenteError("Duración inválida.")
        if not (0 <= descuento <= 1): raise CalculoInconsistenteError("Descuento inválido (0–1).")
        return round(self.precio_base * duracion_horas * (1 - descuento), 2)


# --- Servicio 2: Alquiler de Equipos ---

class ServicioAlquilerEquipo(Servicio):
    """Servicio de alquiler de equipos tecnológicos."""

    def __init__(self, id_s, nombre, precio_base, tipo_equipo, disponible=True):
        super().__init__(id_s, nombre, precio_base, disponible)
        if not tipo_equipo: raise ParametroFaltanteError("Tipo de equipo requerido.")
        self.__tipo_equipo = tipo_equipo

    def tipo(self): return "Equipo"
    def describir_servicio(self): return f"Equipo: {self.__tipo_equipo}"

    def calcular_costo(self, duracion_horas, impuesto=0.19, **kw):
        if duracion_horas <= 0: raise CalculoInconsistenteError("Duración inválida.")
        if impuesto < 0: raise CalculoInconsistenteError("Impuesto negativo.")
        return round(self.precio_base * duracion_horas * (1 + impuesto), 2)


# --- Servicio 3: Asesoría Especializada ---

class ServicioAsesoria(Servicio):
    """Servicio de asesorías especializadas por expertos."""

    AREAS_VALIDAS = ["tecnologia", "legal", "financiera", "marketing", "rrhh"]

    def __init__(self, id_s, nombre, precio_base, area, disponible=True):
        super().__init__(id_s, nombre, precio_base, disponible)
        if area.lower() not in self.AREAS:
            raise ParametroFaltanteError(f"Área inválida: '{area}'. Válidas: {self.AREAS}")
        self.__area = area.lower()

    def tipo(self): return "Asesoría"
    def describir_servicio(self): return f"Asesoría en {self.__area}"

    def calcular_costo(self, duracion_horas, nivel_experto=1, **kw):
        if duracion_horas <= 0: raise CalculoInconsistenteError("Duración inválida.")
        mult = {1: 1.0, 2: 1.5, 3: 2.2}
        if nivel_experto not in mult:
            raise CalculoInconsistenteError("Nivel de experto inválido (1, 2 o 3).")
        return round(self.precio_base * duracion_horas * mult[nivel_experto], 2)


# ============================================================
# CLASE RESERVA
# ============================================================

class Reserva(Entidad):
    """Integra cliente, servicio, duración y estado con manejo de excepciones."""

    ESTADOS_VALIDOS = ["pendiente", "confirmada", "cancelada"]

    def __init__(self, id_r, cliente, servicio, duracion_horas):
        super().__init__(id_r)
        if not isinstance(cliente, Cliente): raise ReservaInvalidaError("Cliente inválido.")
        if not isinstance(servicio, Servicio): raise ReservaInvalidaError("Servicio inválido.")
        if duracion_horas <= 0: raise ReservaInvalidaError("Duración debe ser > 0.")
        self.__cliente = cliente
        self.__servicio = servicio
        self.__duracion = duracion_horas
        self.__estado = "pendiente"
        self.__costo = None
        self.__fecha = date.today().isoformat()

    @property
    def cliente(self): return self.__cliente
    @property
    def servicio(self): return self.__servicio
    @property
    def estado(self): return self.__estado
    @property
    def costo(self): return self.__costo
    @property
    def duracion(self): return self.__duracion
    @property
    def fecha(self): return self.__fecha

    def confirmar(self, **kwargs):
        """Confirma la reserva verificando disponibilidad y calculando costo."""
        if self.__estado == "confirmada":
            raise OperacionNoPermitidaError(f"Reserva #{self.id_entidad} ya está confirmada.")
        if self.__estado == "cancelada":
            raise OperacionNoPermitidaError(f"Reserva #{self.id_entidad} está cancelada, no se puede confirmar.")
        self.__servicio.verificar_disponibilidad()
        if not self.__cliente.validar():
            raise ClienteInvalidoError("Datos del cliente inválidos.")
        self.__costo = self.__servicio.calcular_costo(self.__duracion, **kwargs)
        self.__estado = "confirmada"
        Logger.evento(
            f"Reserva #{self.id_entidad} CONFIRMADA | {self.__cliente.nombre} | "
            f"{self.__servicio.nombre} | ${self.__costo}"
        )

    def cancelar(self):
        if self.__estado == "cancelada":
            raise OperacionNoPermitidaError(f"Reserva #{self.id_entidad} ya está cancelada.")
        self.__estado = "cancelada"
        Logger.evento(
            f"Reserva #{self.id_entidad} CANCELADA | {self.__cliente.nombre} | {self.__servicio.nombre}"
        )

    def describir(self):
        costo = f"${self.__costo}" if self.__costo is not None else "—"
        return (f"#{self.id_entidad} | {self.__cliente.nombre} → {self.__servicio.nombre} | "
                f"{self.__duracion}h | {self.__estado.upper()} | {costo} | {self.__fecha}")

    def validar(self):
        return self.__cliente.validar() and self.__servicio.validar() and self.__duracion > 0


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
        Logger.info("Sistema Software FJ iniciado.")

    # --- Gestión de Clientes ---

    @property
    def clientes(self): return list(self.__clientes)
    @property
    def servicios(self): return list(self.__servicios)
    @property
    def reservas(self): return list(self.__reservas)

    def registrar_cliente(self, id_c, nombre, email, tel):
        c = Cliente(id_c, nombre, email, tel)
        self.__clientes.append(c)
        Logger.evento(f"Cliente registrado: {c.describir()}")
        return c

    def buscar_cliente(self, id_c):
        for c in self.__clientes:
            if c.id_entidad == id_c: return c
        raise ClienteInvalidoError(f"Cliente ID={id_c} no encontrado.")

    # --- Gestión de Servicios ---

    def agregar_servicio(self, s):
        self.__servicios.append(s)
        Logger.evento(f"Servicio agregado: {s.describir()}")

    def buscar_servicio(self, id_s):
        for s in self.__servicios:
            if s.id_entidad == id_s: return s
        raise ServicioNoDisponibleError(f"Servicio ID={id_s} no encontrado.")

    # --- Gestión de Reservas ---

    def crear_reserva(self, id_c, id_s, horas):
        try:
            cliente = self.buscar_cliente(id_c)
            servicio = self.buscar_servicio(id_s)
            r = Reserva(self.__contador, cliente, servicio, horas)
            self.__reservas.append(r)
            self.__contador += 1
            Logger.evento(f"Reserva creada (pendiente): {r.describir()}")
            return r
        except SoftwareFJException as e:
            Logger.error(f"Error al crear reserva: {e}")
            raise

    def confirmar_reserva(self, id_r, **kwargs):
        r = self._buscar_reserva(id_r)
        try:
            r.confirmar(**kwargs)
        except SoftwareFJException as e:
            Logger.error(f"Fallo al confirmar reserva #{id_r}: {e}")
            raise
        return r

    def cancelar_reserva(self, id_r):
        r = self._buscar_reserva(id_r)
        try:
            r.cancelar()
        except SoftwareFJException as e:
            Logger.error(f"Fallo al cancelar reserva #{id_r}: {e}")
            raise
        return r

    def _buscar_reserva(self, id_r):
        for r in self.__reservas:
            if r.id_entidad == id_r: return r
        raise ReservaInvalidaError(f"Reserva ID={id_r} no encontrada.")


# ============================================================
# DEMOSTRACIÓN: 10 OPERACIONES COMPLETAS
# ============================================================

def cargar_demo(sistema: SistemaGestionFJ):
    """Ejecuta las 10 operaciones de demostración."""
    Logger.info("=" * 50)
    Logger.info("INICIO DEMO — 10 OPERACIONES")
    Logger.info("=" * 50)

    sistema.agregar_servicio(ServicioReservaSala(1, "Sala Ejecutiva A", 50.0, capacidad=10))
    sistema.agregar_servicio(ServicioAlquilerEquipo(2, "Laptop HP ProBook", 15.0, tipo_equipo="Laptop"))
    sistema.agregar_servicio(ServicioAsesoria(3, "Asesoría Tecnológica", 80.0, area="tecnologia"))
    sistema.agregar_servicio(ServicioReservaSala(4, "Sala B (Mantenimiento)", 30.0, capacidad=5, disponible=False))

    ops = []

    # ================================================================
    # OPERACIÓN 1: Registro de cliente válido
    # ================================================================
    Logger.info(">>> OP1: Registrar cliente válido")
    try:
        sistema.registrar_cliente(1, "Ana García", "ana@empresa.com", "3001234567")
        ops.append(("OP1", "OK", "Cliente Ana García registrado"))
    except SoftwareFJException as e:
        ops.append(("OP1", "ERROR", str(e)))
    
    # ================================================================
    # OPERACIÓN 2: Registro de cliente inválido (email incorrecto)
    # ================================================================
    Logger.info(">>> OP2: Email inválido")
    try:
        sistema.registrar_cliente(2, "Pedro", "correo_sin_arroba", "3009999999")
        ops.append(("OP2", "OK", "No debería llegar aquí"))
    except ClienteInvalidoError as e:
        ops.append(("OP2", "EXCEPCIÓN", f"ClienteInvalidoError: {e}"))

    # ================================================================
    # OPERACIÓN 3: Registro de segundo cliente válido
    # ================================================================
    Logger.info(">>> OP3: Segundo cliente válido")
    try:
        sistema.registrar_cliente(3, "Luis Martínez", "luis@correo.com", "3107654321")
        ops.append(("OP3", "OK", "Cliente Luis Martínez registrado"))
    except SoftwareFJException as e:
        ops.append(("OP3", "ERROR", str(e)))

    # ================================================================
    # OPERACIÓN 4: Crear y confirmar reserva de sala con descuento
    # ================================================================
    Logger.info(">>> OP4: Reserva sala con 20% descuento")
    try:
        r = sistema.crear_reserva(1, 1, 3)
        sistema.confirmar_reserva(r.id_entidad, descuento=0.20)
        ops.append(("OP4", "OK", f"Sala 3h con 20% dto → ${r.costo}"))
    except SoftwareFJException as e:
        ops.append(("OP4", "ERROR", str(e)))

    # ================================================================
    # OPERACIÓN 5: Crear y confirmar reserva de equipo con IVA
    # ================================================================
    Logger.info(">>> OP5: Equipo con IVA 19%")
    try:
        r = sistema.crear_reserva(3, 2, 8)
        sistema.confirmar_reserva(r.id_entidad, impuesto=0.19)
        ops.append(("OP5", "OK", f"Laptop 8h + IVA → ${r.costo}"))
    except SoftwareFJException as e:
        ops.append(("OP5", "ERROR", str(e)))

    # ================================================================
    # OPERACIÓN 6: Crear y confirmar asesoría con experto nivel 3
    # ================================================================
    Logger.info(">>> OP6: Asesoría experto nivel 3")
    try:
        r = sistema.crear_reserva(1, 3, 2)
        sistema.confirmar_reserva(r.id_entidad, nivel_experto=3)
        ops.append(("OP6", "OK", f"Asesoría 2h nivel Lead → ${r.costo}"))
    except SoftwareFJException as e:
        ops.append(("OP6", "ERROR", str(e)))

    # ================================================================
    # OPERACIÓN 7: Intentar reservar servicio no disponible
    # ================================================================
    Logger.info(">>> OP7: Servicio no disponible")
    try:
        r = sistema.crear_reserva(3, 4, 1)
        sistema.confirmar_reserva(r.id_entidad)
        ops.append(("OP7", "OK", "No debería llegar aquí"))
    except ServicioNoDisponibleError as e:
        ops.append(("OP7", "EXCEPCIÓN", f"ServicioNoDisponibleError: {e}"))
    except SoftwareFJException as e:
        ops.append(("OP7", "ERROR", str(e)))

    # ================================================================
    # OPERACIÓN 8: Cancelar una reserva confirmada
    # ================================================================
    Logger.info(">>> OP8: Cancelar reserva #1")
    try:
        sistema.cancelar_reserva(1)
        ops.append(("OP8", "OK", "Reserva #1 cancelada"))
    except SoftwareFJException as e:
        ops.append(("OP8", "ERROR", str(e)))

    # ================================================================
    # OPERACIÓN 9: Intentar confirmar una reserva ya cancelada
    # ================================================================
    Logger.info(">>> OP9: Confirmar reserva cancelada")
    try:
        sistema.confirmar_reserva(1)
        ops.append(("OP9", "OK", "No debería llegar aquí"))
    except OperacionNoPermitidaError as e:
        ops.append(("OP9", "EXCEPCIÓN", f"OperacionNoPermitidaError: {e}"))

    # ================================================================
    # OPERACIÓN 10: Intentar crear reserva con duración inválida
    # ================================================================
    Logger.info(">>> OP10: Reserva con duración negativa")
    try:
        sistema.crear_reserva(1, 2, -5)
        ops.append(("OP10", "OK", "No debería llegar aquí"))
    except ReservaInvalidaError as e:
        ops.append(("OP10", "EXCEPCIÓN", f"ReservaInvalidaError: {e}"))

    Logger.info("FIN DEMO")
    return ops

# ============================================================
# INTERFAZ GRÁFICA
# ============================================================

class App(tk.Tk):
    # Paleta de colores
    BG      = "#0f1117"
    SURFACE = "#1a1f2e"
    SURF2   = "#222840"
    BORDER  = "#2e3650"
    ACCENT  = "#00e5a0"
    ACCENT2 = "#0099ff"
    DANGER  = "#ff4560"
    WARN    = "#ffcc00"
    TEXT    = "#e8eaf0"
    MUTED   = "#6b7591"
    FONT_H  = ("Segoe UI", 11, "bold")
    FONT_N  = ("Consolas", 10)
    FONT_S  = ("Consolas", 9)

    def __init__(self):
        super().__init__()
        self.title("Software FJ — Sistema de Gestión")
        self.geometry("1150x720")
        self.minsize(900, 600)
        self.configure(bg=self.BG)
        self.resizable(True, True)

        self.sistema = SistemaGestionFJ()
        Logger._widget = self._agregar_log

        self._build_ui()
        self._refrescar_todo()

    # ----------------------------------------------------------
    # BUILD UI
    # ----------------------------------------------------------
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=self.SURFACE, height=60)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)

        logo = tk.Label(hdr, text="FJ", bg=self.ACCENT, fg=self.BG,
                        font=("Segoe UI", 16, "bold"), width=3)
        logo.pack(side="left", padx=(16,10), pady=10)

        tk.Label(hdr, text="Software FJ", bg=self.SURFACE, fg=self.TEXT,
                 font=("Segoe UI", 14, "bold")).pack(side="left", pady=10)
        tk.Label(hdr, text=" · Sistema Integral de Gestión", bg=self.SURFACE,
                 fg=self.MUTED, font=("Segoe UI", 10)).pack(side="left", pady=10)

        # Stats en header
        self.stat_vars = {
            "clientes": tk.StringVar(value="0"),
            "servicios": tk.StringVar(value="0"),
            "reservas": tk.StringVar(value="0"),
        }
        for label, var in [("Clientes", self.stat_vars["clientes"]),
                            ("Servicios", self.stat_vars["servicios"]),
                            ("Reservas", self.stat_vars["reservas"])]:
            f = tk.Frame(hdr, bg=self.SURFACE)
            f.pack(side="right", padx=18, pady=8)
            tk.Label(f, textvariable=var, bg=self.SURFACE, fg=self.ACCENT,
                     font=("Segoe UI", 18, "bold")).pack()
            tk.Label(f, text=label, bg=self.SURFACE, fg=self.MUTED,
                     font=("Segoe UI", 8)).pack()

        # Body
        body = tk.Frame(self, bg=self.BG)
        body.pack(fill="both", expand=True)

        # Sidebar
        self._build_sidebar(body)

        # Content area
        self.content = tk.Frame(body, bg=self.BG)
        self.content.pack(side="left", fill="both", expand=True)

        # Log panel
        self._build_log_panel(body)

        # Panels
        self.panels = {}
        self._build_panel_dashboard()
        self._build_panel_clientes()
        self._build_panel_servicios()
        self._build_panel_reservas()
        self._build_panel_nueva_reserva()

        self._show_panel("dashboard")

    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=self.SURFACE, width=180)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        tk.Frame(sb, bg=self.BORDER, height=1).pack(fill="x", padx=12, pady=(16,4))
        tk.Label(sb, text="PRINCIPAL", bg=self.SURFACE, fg=self.MUTED,
                 font=("Segoe UI", 8), anchor="w").pack(fill="x", padx=16)

        self._nav_btns = {}
        nav_items = [
            ("dashboard",      "⬡  Dashboard"),
            ("clientes",       "◈  Clientes"),
            ("servicios",      "◇  Servicios"),
            ("reservas",       "◉  Reservas"),
            ("nueva_reserva",  "＋  Nueva Reserva"),
        ]
        for key, label in nav_items:
            if key == "clientes":
                tk.Frame(sb, bg=self.BORDER, height=1).pack(fill="x", padx=12, pady=(12,4))
                tk.Label(sb, text="GESTIÓN", bg=self.SURFACE, fg=self.MUTED,
                         font=("Segoe UI", 8), anchor="w").pack(fill="x", padx=16)
            if key == "nueva_reserva":
                tk.Frame(sb, bg=self.BORDER, height=1).pack(fill="x", padx=12, pady=(12,4))
                tk.Label(sb, text="OPERACIONES", bg=self.SURFACE, fg=self.MUTED,
                         font=("Segoe UI", 8), anchor="w").pack(fill="x", padx=16)

            btn = tk.Button(sb, text=label, bg=self.SURFACE, fg=self.MUTED,
                            font=self.FONT_S, anchor="w", bd=0, padx=16, pady=8,
                            activebackground=self.SURF2, activeforeground=self.TEXT,
                            cursor="hand2",
                            command=lambda k=key: self._show_panel(k))
            btn.pack(fill="x")
            self._nav_btns[key] = btn

    def _build_log_panel(self, parent):
        lp = tk.Frame(parent, bg=self.SURFACE, width=280)
        lp.pack(side="right", fill="y")
        lp.pack_propagate(False)

        # Header log
        lh = tk.Frame(lp, bg=self.SURFACE)
        lh.pack(fill="x", padx=12, pady=(12,4))
        tk.Label(lh, text="● LOG EN VIVO", bg=self.SURFACE, fg=self.ACCENT,
                 font=("Consolas", 9, "bold")).pack(side="left")
        tk.Button(lh, text="✕ Limpiar", bg=self.SURFACE, fg=self.MUTED,
                  font=("Segoe UI", 8), bd=0, cursor="hand2",
                  command=self._limpiar_log).pack(side="right")

        tk.Frame(lp, bg=self.BORDER, height=1).pack(fill="x", padx=0)

        # Text widget
        self.log_text = tk.Text(lp, bg=self.SURFACE, fg=self.TEXT,
                                font=("Consolas", 8), bd=0, relief="flat",
                                wrap="word", state="disabled", padx=8, pady=4)
        self.log_text.pack(fill="both", expand=True)

        # Tags de colores
        self.log_text.tag_config("INFO",       foreground=self.ACCENT2)
        self.log_text.tag_config("EVENTO",     foreground=self.ACCENT)
        self.log_text.tag_config("ERROR",      foreground=self.DANGER)
        self.log_text.tag_config("ADVERTENCIA",foreground=self.WARN)
        self.log_text.tag_config("TIME",       foreground=self.MUTED)

        sb_log = ttk.Scrollbar(lp, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=sb_log.set)

    def _agregar_log(self, nivel: str, linea: str):
        self.log_text.configure(state="normal")
        # separar timestamp del resto
        partes = linea.split("] ", 2)
        if len(partes) >= 3:
            ts_part = partes[0] + "] "
            lv_part = "[" + partes[1] + "] "
            msg_part = partes[2] + "\n"
            self.log_text.insert("end", ts_part, "TIME")
            self.log_text.insert("end", lv_part, nivel)
            self.log_text.insert("end", msg_part)
        else:
            self.log_text.insert("end", linea + "\n", nivel)
        self.log_text.configure(state="disabled")
        self.log_text.see("end")

    def _limpiar_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    # ----------------------------------------------------------
    # PANELS
    # ----------------------------------------------------------
    def _make_panel(self, key):
        f = tk.Frame(self.content, bg=self.BG)
        self.panels[key] = f
        return f

    def _show_panel(self, key):
        for k, p in self.panels.items():
            p.pack_forget()
        self.panels[key].pack(fill="both", expand=True, padx=24, pady=20)
        for k, btn in self._nav_btns.items():
            if k == key:
                btn.configure(bg=self.SURF2, fg=self.ACCENT)
            else:
                btn.configure(bg=self.SURFACE, fg=self.MUTED)
        if key == "clientes":       self._refresh_clientes()
        if key == "servicios":      self._refresh_servicios()
        if key == "reservas":       self._refresh_reservas()
        if key == "nueva_reserva":  self._poblar_selectores()

    # -- DASHBOARD --
    def _build_panel_dashboard(self):
        p = self._make_panel("dashboard")

        tk.Label(p, text="Dashboard", bg=self.BG, fg=self.TEXT,
                 font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(p, text="Vista general del sistema Software FJ",
                 bg=self.BG, fg=self.MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(0,16))

        # Demo banner
        banner = tk.Frame(p, bg=self.SURF2, pady=12, padx=16)
        banner.pack(fill="x", pady=(0,20))
        tk.Label(banner, text="🚀  Ejecutar Demo Completa — 10 operaciones de ejemplo",
                 bg=self.SURF2, fg=self.TEXT, font=self.FONT_H).pack(side="left")
        tk.Button(banner, text="▶  Iniciar Demo", bg=self.ACCENT, fg=self.BG,
                  font=self.FONT_H, bd=0, padx=14, pady=6, cursor="hand2",
                  command=self._ejecutar_demo).pack(side="right")

        # Stats cards
        cards_frame = tk.Frame(p, bg=self.BG)
        cards_frame.pack(fill="x", pady=(0,16))

        self.dash_stat_labels = {}
        for label, key, color in [
            ("Clientes registrados",   "clientes",  self.ACCENT),
            ("Servicios disponibles",  "servicios", self.ACCENT2),
            ("Reservas totales",       "reservas",  "#ff6b35"),
        ]:
            c = tk.Frame(cards_frame, bg=self.SURFACE, padx=20, pady=14)
            c.pack(side="left", expand=True, fill="x", padx=(0,10))
            tk.Label(c, text=label, bg=self.SURFACE, fg=self.MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w")
            lbl = tk.Label(c, text="0", bg=self.SURFACE, fg=color,
                           font=("Segoe UI", 32, "bold"))
            lbl.pack(anchor="w")
            self.dash_stat_labels[key] = lbl

        # Últimas reservas
        bot = tk.Frame(p, bg=self.BG)
        bot.pack(fill="both", expand=True)

        left = tk.Frame(bot, bg=self.SURFACE, padx=14, pady=12)
        left.pack(side="left", fill="both", expand=True, padx=(0,10))
        tk.Label(left, text="Últimas Reservas", bg=self.SURFACE, fg=self.TEXT,
                 font=self.FONT_H).pack(anchor="w", pady=(0,8))
        self.dash_reservas_text = tk.Text(left, bg=self.SURFACE, fg=self.TEXT,
                                          font=self.FONT_S, bd=0, height=10,
                                          state="disabled")
        self.dash_reservas_text.pack(fill="both", expand=True)

        right = tk.Frame(bot, bg=self.SURFACE, padx=14, pady=12)
        right.pack(side="left", fill="both", expand=True)
        tk.Label(right, text="Excepciones capturadas", bg=self.SURFACE, fg=self.TEXT,
                 font=self.FONT_H).pack(anchor="w", pady=(0,8))
        self.dash_errores_text = tk.Text(right, bg=self.SURFACE, fg=self.DANGER,
                                         font=self.FONT_S, bd=0, height=10,
                                         state="disabled")
        self.dash_errores_text.pack(fill="both", expand=True)

    def _ejecutar_demo(self):
        self.sistema = SistemaGestionFJ()
        self._limpiar_log()
        ops = cargar_demo(self.sistema)
        self._refrescar_todo()
        self._show_panel("dashboard")

        # Mostrar resultados en popup
        win = tk.Toplevel(self)
        win.title("Resultados Demo — 10 Operaciones")
        win.geometry("700x460")
        win.configure(bg=self.BG)
        win.grab_set()

        tk.Label(win, text="Resultados de la Demo",
                 bg=self.BG, fg=self.TEXT, font=("Segoe UI", 14, "bold")).pack(pady=(16,4), padx=20, anchor="w")
        tk.Label(win, text="10 operaciones ejecutadas con validaciones y manejo de excepciones",
                 bg=self.BG, fg=self.MUTED, font=("Segoe UI", 9)).pack(padx=20, anchor="w", pady=(0,12))

        # Tabla
        cols = ("Operación", "Estado", "Detalle")
        tv = ttk.Treeview(win, columns=cols, show="headings", height=12)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background=self.SURFACE, foreground=self.TEXT,
                        rowheight=28, fieldbackground=self.SURFACE,
                        font=("Consolas", 9))
        style.configure("Treeview.Heading",
                        background=self.SURF2, foreground=self.ACCENT,
                        font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", self.SURF2)])

        tv.heading("Operación", text="Operación")
        tv.heading("Estado", text="Estado")
        tv.heading("Detalle", text="Detalle")
        tv.column("Operación", width=80, anchor="center")
        tv.column("Estado", width=100, anchor="center")
        tv.column("Detalle", width=480)

        for op, estado, detalle in ops:
            tag = "ok" if estado == "OK" else ("exc" if estado == "EXCEPCIÓN" else "err")
            tv.insert("", "end", values=(op, estado, detalle), tags=(tag,))

        tv.tag_configure("ok",  foreground=self.ACCENT)
        tv.tag_configure("exc", foreground=self.WARN)
        tv.tag_configure("err", foreground=self.DANGER)
        tv.pack(fill="both", expand=True, padx=16, pady=(0,12))

        tk.Button(win, text="Cerrar", bg=self.ACCENT, fg=self.BG,
                  font=self.FONT_H, bd=0, padx=20, pady=6,
                  command=win.destroy).pack(pady=(0,16))

    # -- CLIENTES --
    def _build_panel_clientes(self):
        p = self._make_panel("clientes")

        tk.Label(p, text="Clientes", bg=self.BG, fg=self.TEXT,
                 font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(p, text="Registro y gestión de clientes con validación de datos",
                 bg=self.BG, fg=self.MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(0,14))

        # Form
        form = tk.Frame(p, bg=self.SURFACE, padx=16, pady=14)
        form.pack(fill="x", pady=(0,16))
        tk.Label(form, text="Registrar nuevo cliente", bg=self.SURFACE, fg=self.TEXT,
                 font=self.FONT_H).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0,10))

        labels = ["ID", "Nombre", "Email", "Teléfono"]
        self.c_vars = [tk.StringVar() for _ in labels]
        for i, (lbl, var) in enumerate(zip(labels, self.c_vars)):
            tk.Label(form, text=lbl, bg=self.SURFACE, fg=self.MUTED,
                     font=("Segoe UI", 8)).grid(row=1, column=i, sticky="w", padx=(0,8))
            e = tk.Entry(form, textvariable=var, bg=self.SURF2, fg=self.TEXT,
                         font=self.FONT_N, bd=0, insertbackground=self.TEXT, width=18)
            e.grid(row=2, column=i, padx=(0,10), pady=(2,8), ipady=6)

        tk.Button(form, text="◈  Registrar cliente", bg=self.ACCENT, fg=self.BG,
                  font=self.FONT_H, bd=0, padx=14, pady=6, cursor="hand2",
                  command=self._registrar_cliente).grid(row=3, column=0, columnspan=2, sticky="w")

        # Lista
        tk.Label(p, text="Clientes registrados", bg=self.BG, fg=self.TEXT,
                 font=self.FONT_H).pack(anchor="w", pady=(0,6))

        cols = ("ID", "Nombre", "Email", "Teléfono")
        self.tv_clientes = self._make_treeview(p, cols, [50, 160, 200, 130])
        self.tv_clientes.pack(fill="both", expand=True)

    def _registrar_cliente(self):
        try:
            id_c = int(self.c_vars[0].get())
            nombre = self.c_vars[1].get()
            email = self.c_vars[2].get()
            tel = self.c_vars[3].get()
            self.sistema.registrar_cliente(id_c, nombre, email, tel)
            for v in self.c_vars: v.set("")
            self._refrescar_todo()
            messagebox.showinfo("✓ Cliente registrado", f"Cliente '{nombre}' registrado correctamente.")
        except ValueError:
            messagebox.showerror("Error", "El ID debe ser un número entero.")
        except SoftwareFJException as e:
            messagebox.showerror(type(e).__name__, str(e))

    def _refresh_clientes(self):
        self.tv_clientes.delete(*self.tv_clientes.get_children())
        for c in self.sistema.clientes:
            self.tv_clientes.insert("", "end", values=(
                c.id_entidad, c.nombre, c.email, c.telefono))

    # -- SERVICIOS --
    def _build_panel_servicios(self):
        p = self._make_panel("servicios")
        tk.Label(p, text="Servicios", bg=self.BG, fg=self.TEXT,
                 font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(p, text="Catálogo de servicios de Software FJ",
                 bg=self.BG, fg=self.MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(0,14))

        cols = ("ID", "Tipo", "Nombre", "Precio/h", "Descripción", "Estado")
        self.tv_servicios = self._make_treeview(p, cols, [40, 80, 160, 70, 200, 90])
        self.tv_servicios.pack(fill="both", expand=True)

    def _refresh_servicios(self):
        self.tv_servicios.delete(*self.tv_servicios.get_children())
        for s in self.sistema.servicios:
            self.tv_servicios.insert("", "end",
                values=(s.id_entidad, s.tipo(), s.nombre, f"${s.precio_base}",
                        s.describir_servicio(),
                        "Disponible" if s.disponible else "No disponible"),
                tags=("ok" if s.disponible else "off",))
        self.tv_servicios.tag_configure("ok",  foreground=self.ACCENT)
        self.tv_servicios.tag_configure("off", foreground=self.DANGER)

    # -- RESERVAS --
    def _build_panel_reservas(self):
        p = self._make_panel("reservas")
        tk.Label(p, text="Reservas", bg=self.BG, fg=self.TEXT,
                 font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(p, text="Historial completo — selecciona una reserva para gestionarla",
                 bg=self.BG, fg=self.MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(0,14))

        # Botones de acción
        btn_frame = tk.Frame(p, bg=self.BG)
        btn_frame.pack(anchor="w", pady=(0,10))
        tk.Button(btn_frame, text="✓  Confirmar", bg=self.ACCENT, fg=self.BG,
                  font=self.FONT_H, bd=0, padx=12, pady=5, cursor="hand2",
                  command=self._confirmar_selected).pack(side="left", padx=(0,8))
        tk.Button(btn_frame, text="✕  Cancelar", bg=self.DANGER, fg="white",
                  font=self.FONT_H, bd=0, padx=12, pady=5, cursor="hand2",
                  command=self._cancelar_selected).pack(side="left")

        cols = ("ID", "Cliente", "Servicio", "Horas", "Estado", "Costo", "Fecha")
        self.tv_reservas = self._make_treeview(p, cols, [40,130,150,50,90,80,90])
        self.tv_reservas.pack(fill="both", expand=True)

    def _refresh_reservas(self):
        self.tv_reservas.delete(*self.tv_reservas.get_children())
        tag_map = {"confirmada": "conf", "cancelada": "canc", "pendiente": "pend"}
        for r in self.sistema.reservas:
            tag = tag_map.get(r.estado, "pend")
            self.tv_reservas.insert("", "end",
                values=(r.id_entidad, r.cliente.nombre, r.servicio.nombre,
                        r.duracion, r.estado.upper(),
                        f"${r.costo}" if r.costo is not None else "—",
                        r.fecha),
                tags=(tag,))
        self.tv_reservas.tag_configure("conf", foreground=self.ACCENT)
        self.tv_reservas.tag_configure("canc", foreground=self.DANGER)
        self.tv_reservas.tag_configure("pend", foreground=self.WARN)

    def _get_selected_reserva_id(self):
        sel = self.tv_reservas.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona una reserva de la lista.")
            return None
        vals = self.tv_reservas.item(sel[0])["values"]
        return int(vals[0])

    def _confirmar_selected(self):
        id_r = self._get_selected_reserva_id()
        if id_r is None: return
        try:
            r = self.sistema.confirmar_reserva(id_r)
            self._refrescar_todo()
            messagebox.showinfo("✓ Confirmada", f"Reserva #{id_r} confirmada.\nCosto: ${r.costo}")
        except SoftwareFJException as e:
            messagebox.showerror(type(e).__name__, str(e))

    def _cancelar_selected(self):
        id_r = self._get_selected_reserva_id()
        if id_r is None: return
        try:
            self.sistema.cancelar_reserva(id_r)
            self._refrescar_todo()
            messagebox.showinfo("Cancelada", f"Reserva #{id_r} cancelada.")
        except SoftwareFJException as e:
            messagebox.showerror(type(e).__name__, str(e))

    # -- NUEVA RESERVA --
    def _build_panel_nueva_reserva(self):
        p = self._make_panel("nueva_reserva")
        tk.Label(p, text="Nueva Reserva", bg=self.BG, fg=self.TEXT,
                 font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(p, text="Crear y confirmar una reserva para un cliente",
                 bg=self.BG, fg=self.MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(0,14))

        form = tk.Frame(p, bg=self.SURFACE, padx=20, pady=16)
        form.pack(fill="x")

        # Cliente
        row0 = tk.Frame(form, bg=self.SURFACE)
        row0.pack(fill="x", pady=(0,12))
        tk.Label(row0, text="CLIENTE", bg=self.SURFACE, fg=self.MUTED,
                 font=("Segoe UI", 8)).pack(anchor="w")
        self.r_cliente_var = tk.StringVar()
        self.r_cliente_cb = ttk.Combobox(row0, textvariable=self.r_cliente_var,
                                          font=self.FONT_N, state="readonly", width=35)
        self.r_cliente_cb.pack(anchor="w", ipady=4)

        # Servicio
        row1 = tk.Frame(form, bg=self.SURFACE)
        row1.pack(fill="x", pady=(0,12))
        tk.Label(row1, text="SERVICIO", bg=self.SURFACE, fg=self.MUTED,
                 font=("Segoe UI", 8)).pack(anchor="w")
        self.r_servicio_var = tk.StringVar()
        self.r_servicio_cb = ttk.Combobox(row1, textvariable=self.r_servicio_var,
                                           font=self.FONT_N, state="readonly", width=35)
        self.r_servicio_cb.pack(anchor="w", ipady=4)
        self.r_servicio_cb.bind("<<ComboboxSelected>>", self._on_servicio_selected)

        # Duración + parámetro extra
        row2 = tk.Frame(form, bg=self.SURFACE)
        row2.pack(fill="x", pady=(0,12))
        lf = tk.Frame(row2, bg=self.SURFACE)
        lf.pack(side="left", padx=(0,20))
        tk.Label(lf, text="DURACIÓN (horas)", bg=self.SURFACE, fg=self.MUTED,
                 font=("Segoe UI", 8)).pack(anchor="w")
        self.r_duracion_var = tk.StringVar()
        tk.Entry(lf, textvariable=self.r_duracion_var, bg=self.SURF2, fg=self.TEXT,
                 font=self.FONT_N, bd=0, insertbackground=self.TEXT, width=12).pack(ipady=6)

        rf = tk.Frame(row2, bg=self.SURFACE)
        rf.pack(side="left")
        self.r_extra_label_var = tk.StringVar(value="Parámetro extra")
        self.r_extra_label_w = tk.Label(rf, textvariable=self.r_extra_label_var,
                                        bg=self.SURFACE, fg=self.MUTED, font=("Segoe UI", 8))
        self.r_extra_label_w.pack(anchor="w")
        self.r_extra_var = tk.StringVar()
        self.r_extra_entry = tk.Entry(rf, textvariable=self.r_extra_var,
                                      bg=self.SURF2, fg=self.TEXT, font=self.FONT_N,
                                      bd=0, insertbackground=self.TEXT, width=12)
        self.r_extra_entry.pack(ipady=6)

        # Preview de costo
        self.costo_preview_var = tk.StringVar(value="")
        self.costo_lbl = tk.Label(form, textvariable=self.costo_preview_var,
                                  bg=self.SURFACE, fg=self.ACCENT,
                                  font=("Segoe UI", 16, "bold"))
        self.costo_lbl.pack(anchor="w", pady=(4,8))

        # Botones
        btn_row = tk.Frame(form, bg=self.SURFACE)
        btn_row.pack(anchor="w")
        tk.Button(btn_row, text="⟳  Calcular costo", bg=self.SURF2, fg=self.TEXT,
                  font=self.FONT_N, bd=0, padx=12, pady=6, cursor="hand2",
                  command=self._calcular_preview).pack(side="left", padx=(0,10))
        tk.Button(btn_row, text="◉  Crear y confirmar", bg=self.ACCENT, fg=self.BG,
                  font=self.FONT_H, bd=0, padx=14, pady=6, cursor="hand2",
                  command=self._crear_confirmar_reserva).pack(side="left")

    def _poblar_selectores(self):
        clientes = [f"{c.id_entidad} — {c.nombre}" for c in self.sistema.clientes]
        self.r_cliente_cb["values"] = clientes
        servicios = [f"{s.id_entidad} — {s.nombre} (${s.precio_base}/h)" for s in self.sistema.servicios]
        self.r_servicio_cb["values"] = servicios
        self.costo_preview_var.set("")

    def _on_servicio_selected(self, _=None):
        self.costo_preview_var.set("")
        try:
            id_s = int(self.r_servicio_var.get().split("—")[0].strip())
            s = self.sistema.buscar_servicio(id_s)
            if isinstance(s, ServicioReservaSala):
                self.r_extra_label_var.set("Descuento (0–1, ej: 0.2 = 20%)")
                self.r_extra_var.set("0")
            elif isinstance(s, ServicioAlquilerEquipo):
                self.r_extra_label_var.set("Impuesto (ej: 0.19 = 19% IVA)")
                self.r_extra_var.set("0.19")
            elif isinstance(s, ServicioAsesoria):
                self.r_extra_label_var.set("Nivel experto (1=junior, 2=senior, 3=lead)")
                self.r_extra_var.set("1")
        except Exception:
            pass

    def _get_opts(self):
        id_s = int(self.r_servicio_var.get().split("—")[0].strip())
        s = self.sistema.buscar_servicio(id_s)
        extra = self.r_extra_var.get()
        if isinstance(s, ServicioReservaSala):
            return {"descuento": float(extra or 0)}
        elif isinstance(s, ServicioAlquilerEquipo):
            return {"impuesto": float(extra if extra else 0.19)}
        elif isinstance(s, ServicioAsesoria):
            return {"nivel_experto": int(extra or 1)}
        return {}

    def _calcular_preview(self):
        try:
            id_s = int(self.r_servicio_var.get().split("—")[0].strip())
            horas = float(self.r_duracion_var.get())
            s = self.sistema.buscar_servicio(id_s)
            opts = self._get_opts()
            costo = s.calcular_costo(horas, **opts)
            self.costo_preview_var.set(f"Costo estimado: ${costo:.2f}")
        except SoftwareFJException as e:
            messagebox.showerror(type(e).__name__, str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Verifica los campos: {e}")

    def _crear_confirmar_reserva(self):
        try:
            id_c = int(self.r_cliente_var.get().split("—")[0].strip())
            id_s = int(self.r_servicio_var.get().split("—")[0].strip())
            horas = float(self.r_duracion_var.get())
            opts = self._get_opts()
            r = self.sistema.crear_reserva(id_c, id_s, horas)
            self.sistema.confirmar_reserva(r.id_entidad, **opts)
            self._refrescar_todo()
            messagebox.showinfo("✓ Reserva confirmada",
                                f"Reserva #{r.id_entidad} creada y confirmada.\nCosto total: ${r.costo}")
            self.costo_preview_var.set("")
        except SoftwareFJException as e:
            messagebox.showerror(type(e).__name__, str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Verifica los campos: {e}")

    # ----------------------------------------------------------
    # HELPERS
    # ----------------------------------------------------------
    def _make_treeview(self, parent, cols, widths):
        frame = tk.Frame(parent, bg=self.BG)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Custom.Treeview",
                        background=self.SURFACE, foreground=self.TEXT,
                        rowheight=26, fieldbackground=self.SURFACE,
                        font=("Consolas", 9))
        style.configure("Custom.Treeview.Heading",
                        background=self.SURF2, foreground=self.ACCENT,
                        font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Custom.Treeview", background=[("selected", self.SURF2)])

        tv = ttk.Treeview(frame, columns=cols, show="headings",
                          style="Custom.Treeview")
        for col, w in zip(cols, widths):
            tv.heading(col, text=col)
            tv.column(col, width=w, anchor="w")
        sb = ttk.Scrollbar(frame, orient="vertical", command=tv.yview)
        tv.configure(yscrollcommand=sb.set)
        tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        return tv

    def _refrescar_todo(self):
        n_c = len(self.sistema.clientes)
        n_s = len([s for s in self.sistema.servicios if s.disponible])
        n_r = len(self.sistema.reservas)
        self.stat_vars["clientes"].set(str(n_c))
        self.stat_vars["servicios"].set(str(n_s))
        self.stat_vars["reservas"].set(str(n_r))
        self.dash_stat_labels["clientes"].config(text=str(n_c))
        self.dash_stat_labels["servicios"].config(text=str(n_s))
        self.dash_stat_labels["reservas"].config(text=str(n_r))
        self._refresh_dashboard_lists()

    def _refresh_dashboard_lists(self):
        # Últimas reservas
        self.dash_reservas_text.configure(state="normal")
        self.dash_reservas_text.delete("1.0", "end")
        for r in reversed(self.sistema.reservas[-5:]):
            self.dash_reservas_text.insert(
                "end",
                f"#{r.id_entidad}  {r.cliente.nombre} → {r.servicio.nombre}\n"
                f"     {r.estado.upper()} | "
                f"{'$'+str(r.costo) if r.costo else '—'} | {r.fecha}\n\n"
            )
        self.dash_reservas_text.configure(state="disabled")

        # Errores del log
        errores = [l for l in Logger.logs if l[0] == "ERROR"] if hasattr(Logger, "logs") else []
        self.dash_errores_text.configure(state="normal")
        self.dash_errores_text.delete("1.0", "end")
        for _, msg in reversed(errores[-6:]):
            self.dash_errores_text.insert("end", f"✕ {msg}\n\n")
        self.dash_errores_text.configure(state="disabled")


# Guardar logs internos para el dashboard
Logger.logs = []

def _escribir_ext(nivel, mensaje):
    Logger.logs.append((nivel, mensaje))
    ts = datetime.now().strftime("%H:%M:%S")
    linea = f"[{ts}] [{nivel}] {mensaje}"
    try:
        with open(Logger.LOG_FILE, "a", encoding="utf-8") as f:
            f.write(linea + "\n")
    except IOError:
        pass
    if Logger._widget:
        Logger._widget(nivel, linea)

Logger._escribir = staticmethod(_escribir_ext)


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    app = App()
    app.mainloop()
