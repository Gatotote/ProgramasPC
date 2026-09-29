from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)


def crear_tabla(columnas, filas, chips=None, resize=None):
    """chips: dict {col: callable(valor)->QWidget}. resize: dict {col: "contenido"|"stretch"|int}."""
    tabla = QTableWidget(len(filas), len(columnas))
    tabla.setHorizontalHeaderLabels(columnas)
    tabla.verticalHeader().setVisible(False)
    tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
    tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
    tabla.setSelectionMode(QAbstractItemView.SingleSelection)
    tabla.setAlternatingRowColors(True)
    tabla.setShowGrid(False)
    tabla.verticalHeader().setDefaultSectionSize(40)
    encabezado = tabla.horizontalHeader()
    if resize:
        encabezado.setStretchLastSection(False)
        for c in range(len(columnas)):
            modo = resize.get(c, "stretch")
            if isinstance(modo, int):
                encabezado.setSectionResizeMode(c, QHeaderView.Fixed)
                tabla.setColumnWidth(c, modo)
            elif modo == "contenido":
                encabezado.setSectionResizeMode(c, QHeaderView.ResizeToContents)
            else:
                encabezado.setSectionResizeMode(c, QHeaderView.Stretch)
    else:
        encabezado.setStretchLastSection(True)
        encabezado.setSectionResizeMode(QHeaderView.Stretch)
    chips = chips or {}
    for r, fila in enumerate(filas):
        for c, valor in enumerate(fila):
            if c in chips:
                tabla.setCellWidget(r, c, chips[c](valor))
            else:
                tabla.setItem(r, c, QTableWidgetItem(str(valor)))
    return tabla
