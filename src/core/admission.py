"""Control local y no bloqueante de admisión de trabajos.

AdmissionController está pensado para usarse desde un único event loop por
proceso. Sus métodos son síncronos y no contienen puntos de suspensión: no
crean una cola de tareas esperando permisos. Cada proceso (y cada réplica)
debe tener su propia instancia; este componente no establece un límite global
entre procesos, workers Uvicorn o réplicas.
"""


class AdmissionPermit:
    """Permiso único de admisión, con liberación idempotente."""

    def __init__(
        self,
        controller: "AdmissionController",
        *,
        _creation_key: object,
    ) -> None:
        if _creation_key is not controller._permit_creation_key:
            raise TypeError("Los permisos deben ser concedidos por el controlador")
        self._controller = controller
        self._released = False

    @property
    def released(self) -> bool:
        """Indica si este permiso ya fue liberado."""
        return self._released

    def release(self) -> None:
        """Libera el permiso una sola vez."""
        if self._released:
            return

        self._controller._release_permit(self)
        self._released = True

    def __enter__(self) -> "AdmissionPermit":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.release()


class AdmissionController:
    """Admisión acotada por capacidad, sin esperas por un permiso.

    La capacidad se inyecta al construir el controlador. La instancia está
    destinada a un único event loop por proceso; no es thread-safe ni comparte
    estado con otros procesos o réplicas.
    """

    def __init__(self, capacity: int) -> None:
        if isinstance(capacity, bool) or not isinstance(capacity, int):
            raise TypeError("capacity debe ser un entero")
        if capacity <= 0:
            raise ValueError("capacity debe ser positivo")

        self._capacity = capacity
        self._in_use = 0
        self._accepting = True
        self._permit_creation_key = object()
        self._active_permits: set[AdmissionPermit] = set()

    @property
    def capacity(self) -> int:
        """Capacidad máxima configurada."""
        return self._capacity

    @property
    def in_use(self) -> int:
        """Cantidad actual de permisos ocupados."""
        return self._in_use

    @property
    def accepting(self) -> bool:
        """Indica si se admiten nuevas solicitudes."""
        return self._accepting

    def try_acquire(self) -> AdmissionPermit | None:
        """Adquiere un permiso inmediatamente o devuelve ``None``.

        No espera ni encola al llamador. El token retornado representa una
        única adquisición y debe liberarse al terminar el trabajo admitido.
        """
        if not self._accepting or self._in_use >= self._capacity:
            return None

        permit = AdmissionPermit(self, _creation_key=self._permit_creation_key)
        self._active_permits.add(permit)
        self._in_use += 1
        return permit

    def close(self) -> None:
        """Cierra la admisión; los permisos existentes siguen siendo válidos."""
        self._accepting = False

    def reopen(self) -> None:
        """Reabre la admisión sin alterar los permisos ya ocupados."""
        self._accepting = True

    def _release_permit(self, permit: AdmissionPermit) -> None:
        if self._in_use <= 0:
            raise RuntimeError("No hay permisos ocupados para liberar")
        if permit not in self._active_permits or permit._controller is not self:
            raise RuntimeError("El permiso no fue concedido por este controlador")

        self._active_permits.remove(permit)
        self._in_use -= 1
