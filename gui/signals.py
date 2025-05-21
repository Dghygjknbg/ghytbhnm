from PySide6.QtCore import QObject, Signal

class WorkerSignals(QObject):
    """Сигналы для взаимодействия с GUI"""
    log_signal = Signal(str)
    balance_signal = Signal(str)
    error_signal = Signal(str)
    finished_signal = Signal() 