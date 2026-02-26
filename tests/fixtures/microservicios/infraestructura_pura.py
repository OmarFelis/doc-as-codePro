# Microservicio de infraestructura pura — solo llamadas a AWS/BD
# Caso de prueba: todas las funciones deben clasificar como INFRAESTRUCTURA
# y el BusinessRuleExtractor NO debe procesar este archivo

import boto3
import psycopg2

sqs = boto3.client("sqs")


def publicar_evento_pago(queue_url: str, mensaje: dict) -> str:
    """Publica un evento de pago en SQS."""
    import json
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(mensaje)
    )
    return response["MessageId"]


def guardar_transaccion(conn_string: str, transaccion: dict) -> str:
    """Persiste una transacción en PostgreSQL."""
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transacciones (monto, tipo, estado) VALUES (%s, %s, %s) RETURNING id",
        (transaccion["monto"], transaccion["tipo"], "PENDIENTE")
    )
    tx_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return str(tx_id)


def obtener_config_s3(bucket: str, key: str) -> dict:
    """Lee configuración desde S3."""
    import json
    s3 = boto3.client("s3")
    response = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(response["Body"].read())
