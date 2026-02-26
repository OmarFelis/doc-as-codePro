# Microservicio con acoplamiento multicapa — mezcla adaptador + infraestructura
# Caso de prueba: debe detectar has_multi_layer_coupling = True y risk_level HIGH

import boto3
from fastapi import APIRouter, HTTPException

router = APIRouter()
s3_client = boto3.client("s3")


def procesar_pago_y_guardar(monto: float, bucket: str, key: str) -> dict:
    """
    PROBLEMA: Esta función mezcla lógica de entrada (FastAPI),
    lógica de negocio y llamada a infraestructura (S3).
    Viola separación de capas.
    """
    if monto <= 0:
        raise HTTPException(status_code=400, detail="Monto inválido")

    # Lógica de negocio mezclada con infraestructura
    comision = monto * 0.035
    resultado = {"monto": monto, "comision": comision}

    # Llamada directa a S3 desde función de negocio
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=str(resultado)
    )
    return resultado


def consultar_historial(user_id: str, tabla: str) -> list:
    """Consulta historial mezclando lógica con DynamoDB."""
    import boto3
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(tabla)
    response = table.query(
        KeyConditionExpression="user_id = :uid",
        ExpressionAttributeValues={":uid": user_id}
    )
    return response.get("Items", [])
