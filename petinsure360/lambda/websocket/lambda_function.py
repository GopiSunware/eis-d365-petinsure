"""
PetInsure360 WebSocket Handler - AWS Lambda
Handles WebSocket connections via API Gateway WebSocket API

Based on proven implementation from COM Simulation (1+ year production)

Routes:
- $connect: Store connection in DynamoDB
- $disconnect: Remove connection from DynamoDB
- $default: Route actions (ping, subscribe, etc.)
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration
REGION = os.environ.get('REGION_NAME', 'us-east-1')
CONNECTIONS_TABLE = os.environ.get('CONNECTIONS_TABLE', 'petinsure360_ws_connections')
WEBSOCKET_API_ID = os.environ.get('WEBSOCKET_API_ID', '')
WEBSOCKET_STAGE = os.environ.get('WEBSOCKET_STAGE', 'prod')

# Initialize boto session and clients
boto_session = boto3.Session(region_name=REGION)
dynamodb = boto_session.resource('dynamodb')
connections_table = dynamodb.Table(CONNECTIONS_TABLE)
apigw_client = None  # Lazy init


def get_apigw_client():
    """Lazy init API Gateway Management client for pushing messages."""
    global apigw_client
    if apigw_client is None:
        endpoint_url = f"https://{WEBSOCKET_API_ID}.execute-api.{REGION}.amazonaws.com/{WEBSOCKET_STAGE}"
        apigw_client = boto_session.client('apigatewaymanagementapi', endpoint_url=endpoint_url)
    return apigw_client


def push_to_connection(connection_id: str, message: Dict) -> bool:
    """Push a message to a specific WebSocket connection."""
    try:
        client = get_apigw_client()
        client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message).encode('utf-8')
        )
        logger.info(f"Pushed message to {connection_id}: type={message.get('type')}")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'GoneException':
            # Connection is stale, remove from DynamoDB
            logger.warning(f"Connection {connection_id} is gone, removing from table")
            try:
                connections_table.delete_item(Key={'connection_id': connection_id})
            except Exception as delete_error:
                logger.error(f"Error deleting stale connection: {delete_error}")
        else:
            logger.error(f"Error pushing to connection {connection_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error pushing to connection {connection_id}: {e}")
        return False


# =============================================================================
# ROUTE HANDLERS
# =============================================================================

def handle_connect(event, context):
    """
    Handle $connect route - store connection in DynamoDB.
    """
    connection_id = event.get('requestContext', {}).get('connectionId')

    if not connection_id:
        return {'statusCode': 400, 'body': 'Missing connection ID'}

    try:
        # Store connection in DynamoDB
        connections_table.put_item(
            Item={
                'connection_id': connection_id,
                'connected_at': datetime.utcnow().isoformat(),
                'ttl': int(datetime.utcnow().timestamp()) + 86400  # 24 hour TTL
            }
        )
        logger.info(f"Connection stored: {connection_id}")
        return {'statusCode': 200, 'body': 'Connected'}

    except Exception as e:
        logger.error(f"Error storing connection {connection_id}: {e}")
        return {'statusCode': 500, 'body': f'Error: {str(e)}'}


def handle_disconnect(event, context):
    """
    Handle $disconnect route - remove connection from DynamoDB.
    """
    connection_id = event.get('requestContext', {}).get('connectionId')

    if not connection_id:
        return {'statusCode': 400, 'body': 'Missing connection ID'}

    try:
        # Remove connection from DynamoDB
        connections_table.delete_item(
            Key={'connection_id': connection_id}
        )
        logger.info(f"Connection removed: {connection_id}")
        return {'statusCode': 200, 'body': 'Disconnected'}

    except Exception as e:
        logger.error(f"Error removing connection {connection_id}: {e}")
        return {'statusCode': 500, 'body': f'Error: {str(e)}'}


def handle_default(event, context):
    """
    Handle $default route - route actions.
    """
    connection_id = event.get('requestContext', {}).get('connectionId')

    try:
        # Parse message body
        body = json.loads(event.get('body', '{}'))
        action = body.get('action', 'unknown')

        logger.info(f"Action: {action} from {connection_id}")

        # Route based on action
        if action == 'ping':
            # Respond with pong
            push_to_connection(connection_id, {
                'type': 'pong',
                'data': {'timestamp': datetime.utcnow().isoformat()}
            })

        elif action == 'subscribe_claims':
            # Subscribe to claim updates
            customer_id = body.get('customer_id')
            push_to_connection(connection_id, {
                'type': 'subscribed',
                'data': {'customer_id': customer_id}
            })

        else:
            # Echo back unknown actions
            push_to_connection(connection_id, {
                'type': 'echo',
                'data': body
            })

        return {'statusCode': 200, 'body': 'Message processed'}

    except Exception as e:
        logger.error(f"Error processing message from {connection_id}: {e}")
        return {'statusCode': 500, 'body': f'Error: {str(e)}'}


# =============================================================================
# MAIN HANDLER
# =============================================================================

def lambda_handler(event, context):
    """
    Main entry point - routes to appropriate handler based on WebSocket route.

    Routes:
    - $connect: handle_connect()
    - $disconnect: handle_disconnect()
    - $default: handle_default()
    """
    route_key = event.get('requestContext', {}).get('routeKey', '$default')
    connection_id = event.get('requestContext', {}).get('connectionId')

    logger.info(f"Route: {route_key}, Connection: {connection_id}")

    try:
        if route_key == '$connect':
            return handle_connect(event, context)
        elif route_key == '$disconnect':
            return handle_disconnect(event, context)
        else:
            # $default or any custom route
            return handle_default(event, context)

    except Exception as e:
        logger.error(f"Unhandled error in lambda_handler: {e}")
        return {'statusCode': 500, 'body': f'Internal error: {str(e)}'}


# =============================================================================
# BROADCAST HELPER (can be called by other Lambdas/services)
# =============================================================================

def broadcast_message(message: Dict) -> int:
    """
    Broadcast a message to all connected clients.
    Can be called by other services to push updates.

    Returns: number of successful deliveries
    """
    try:
        # Get all active connections
        response = connections_table.scan()
        connections = response.get('Items', [])

        logger.info(f"Broadcasting to {len(connections)} connections")

        success_count = 0
        for conn in connections:
            connection_id = conn['connection_id']
            if push_to_connection(connection_id, message):
                success_count += 1

        logger.info(f"Broadcast complete: {success_count}/{len(connections)} successful")
        return success_count

    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        return 0
