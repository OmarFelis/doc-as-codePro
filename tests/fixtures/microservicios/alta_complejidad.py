# Microservicio de alta complejidad — funciones con complejidad > 15
# Caso de prueba: debe asignar risk_level = HIGH y overall_score bajo

def procesar_transaccion_compleja(
    monto, tipo, moneda, canal, usuario_id, comercio_id,
    cuotas, descuento, igv_incluido, es_recurrente
):
    """Función con alta complejidad ciclomática — candidata a refactorización."""
    if monto <= 0:
        return {"error": "monto_invalido"}
    if tipo not in ["credito", "debito", "prepago"]:
        return {"error": "tipo_invalido"}
    if moneda not in ["PEN", "USD", "EUR"]:
        return {"error": "moneda_invalida"}
    if canal == "web":
        if usuario_id is None:
            return {"error": "usuario_requerido"}
        if comercio_id is None:
            return {"error": "comercio_requerido"}
    elif canal == "app":
        if usuario_id is None and comercio_id is None:
            return {"error": "identificacion_requerida"}
    elif canal == "pos":
        if comercio_id is None:
            return {"error": "comercio_requerido_pos"}
    else:
        return {"error": "canal_invalido"}

    subtotal = monto
    if descuento and 0 < descuento < 100:
        subtotal = monto * (1 - descuento / 100)
    if igv_incluido:
        igv = subtotal * 0.18
        subtotal = subtotal + igv
    if tipo == "credito" and cuotas:
        if cuotas < 1 or cuotas > 48:
            return {"error": "cuotas_invalidas"}
        monto_cuota = subtotal / cuotas
    else:
        monto_cuota = subtotal
    if es_recurrente:
        if tipo != "credito":
            return {"error": "recurrente_solo_credito"}
        if cuotas and cuotas > 12:
            return {"error": "recurrente_max_12_cuotas"}

    return {
        "subtotal": round(subtotal, 2),
        "monto_cuota": round(monto_cuota, 2),
        "estado": "APROBADO"
    }
