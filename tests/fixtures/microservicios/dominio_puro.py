# Microservicio de dominio puro — sin imports de infra ni adaptador
# Caso de prueba: todas las funciones deben clasificar como DOMINIO
# y el BusinessRuleExtractor debe encontrar reglas de negocio aquí

def calcular_comision(monto: float, tipo_tarjeta: str) -> float:
    """Calcula la comisión según el tipo de tarjeta."""
    if monto <= 0:
        raise ValueError("El monto debe ser mayor a cero")
    if tipo_tarjeta == "credito":
        return round(monto * 0.035, 2)
    elif tipo_tarjeta == "debito":
        return round(monto * 0.015, 2)
    raise ValueError(f"Tipo de tarjeta no soportado: {tipo_tarjeta}")


def validar_monto_minimo(monto: float, moneda: str) -> bool:
    """Valida que el monto cumpla el mínimo por moneda."""
    minimos = {"PEN": 1.00, "USD": 0.50, "EUR": 0.50}
    minimo = minimos.get(moneda, 1.00)
    return monto >= minimo


def aplicar_descuento(precio: float, porcentaje: float) -> float:
    """Aplica un descuento al precio."""
    if porcentaje < 0 or porcentaje > 100:
        raise ValueError("El porcentaje debe estar entre 0 y 100")
    return round(precio * (1 - porcentaje / 100), 2)


def calcular_igv(subtotal: float) -> float:
    """Calcula el IGV (18%) sobre el subtotal."""
    IGV_RATE = 0.18
    return round(subtotal * IGV_RATE, 2)
