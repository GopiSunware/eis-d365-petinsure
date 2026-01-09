# AWS WebSocket Standard Implementation Guide

**Status**: ✅ Production-Ready (1+ year proven in COM Simulation project)
**Last Updated**: 2026-01-09
**Use Case**: Real-time notifications for web applications

---

## Architecture Overview

```
React Frontend (Native WebSocket)
    ↓
AWS API Gateway WebSocket API (wss://xxx.execute-api.region.amazonaws.com/prod)
    ↓
Lambda Function (Connection handler)
    ↓
DynamoDB (Connection IDs with TTL) + Push messages via apigatewaymanagementapi
```

**Why This Architecture?**
- ✅ Native AWS WebSocket support (no App Runner/ECS limitations)
- ✅ Auto-scaling Lambda (handles 1 to 1M+ connections)
- ✅ Pay-per-use pricing (no idle costs)
- ✅ DynamoDB connection tracking with automatic TTL cleanup
- ✅ Proven stable for 1+ year in production

---

## Step 1: Create DynamoDB Connections Table

**Purpose**: Store active WebSocket connection IDs

```bash
aws dynamodb create-table \
    --table-name ${PROJECT_NAME}_ws_connections \
    --attribute-definitions AttributeName=connection_id,AttributeType=S \
    --key-schema AttributeName=connection_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1 \
    --profile ${AWS_PROFILE} \
    --tags Key=Project,Value=${PROJECT_NAME} Key=Component,Value=WebSocket

# Enable TTL for automatic cleanup (24 hour TTL)
aws dynamodb update-time-to-live \
    --table-name ${PROJECT_NAME}_ws_connections \
    --time-to-live-specification "Enabled=true,AttributeName=ttl" \
    --region us-east-1 \
    --profile ${AWS_PROFILE}
```

**Table Schema**:
```json
{
  "connection_id": "string (HASH KEY)",
  "connected_at": "ISO timestamp",
  "ttl": "unix timestamp (auto-cleanup after 24 hours)"
}
```

---

## Step 2: Create Lambda Function

### lambda_function.py

```python
"""
WebSocket Handler - AWS Lambda
Handles WebSocket connections via API Gateway WebSocket API

Routes:
- $connect: Store connection in DynamoDB
- $disconnect: Remove connection from DynamoDB
- $default: Route actions (ping, subscribe, broadcast, etc.)
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
CONNECTIONS_TABLE = os.environ.get('CONNECTIONS_TABLE')
WEBSOCKET_API_ID = os.environ.get('WEBSOCKET_API_ID')
WEBSOCKET_STAGE = os.environ.get('WEBSOCKET_STAGE', 'prod')

# Initialize clients
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


def handle_connect(event, context):
    """Handle $connect route - store connection in DynamoDB."""
    connection_id = event.get('requestContext', {}).get('connectionId')
    if not connection_id:
        return {'statusCode': 400, 'body': 'Missing connection ID'}

    try:
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
        logger.error(f"Error storing connection: {e}")
        return {'statusCode': 500, 'body': f'Error: {str(e)}'}


def handle_disconnect(event, context):
    """Handle $disconnect route - remove connection from DynamoDB."""
    connection_id = event.get('requestContext', {}).get('connectionId')
    if not connection_id:
        return {'statusCode': 400, 'body': 'Missing connection ID'}

    try:
        connections_table.delete_item(Key={'connection_id': connection_id})
        logger.info(f"Connection removed: {connection_id}")
        return {'statusCode': 200, 'body': 'Disconnected'}
    except Exception as e:
        logger.error(f"Error removing connection: {e}")
        return {'statusCode': 500, 'body': f'Error: {str(e)}'}


def handle_default(event, context):
    """Handle $default route - route actions."""
    connection_id = event.get('requestContext', {}).get('connectionId')

    try:
        body = json.loads(event.get('body', '{}'))
        action = body.get('action', 'unknown')
        logger.info(f"Action: {action} from {connection_id}")

        # Route based on action
        if action == 'ping':
            push_to_connection(connection_id, {
                'type': 'pong',
                'data': {'timestamp': datetime.utcnow().isoformat()}
            })
        else:
            # Echo back unknown actions
            push_to_connection(connection_id, {
                'type': 'echo',
                'data': body
            })

        return {'statusCode': 200, 'body': 'Message processed'}
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return {'statusCode': 500, 'body': f'Error: {str(e)}'}


def lambda_handler(event, context):
    """Main entry point - routes to appropriate handler."""
    route_key = event.get('requestContext', {}).get('routeKey', '$default')
    connection_id = event.get('requestContext', {}).get('connectionId')
    logger.info(f"Route: {route_key}, Connection: {connection_id}")

    try:
        if route_key == '$connect':
            return handle_connect(event, context)
        elif route_key == '$disconnect':
            return handle_disconnect(event, context)
        else:
            return handle_default(event, context)
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        return {'statusCode': 500, 'body': f'Internal error: {str(e)}'}


def broadcast_message(message: Dict) -> int:
    """
    Broadcast a message to all connected clients.
    Can be called by other services to push updates.

    Returns: number of successful deliveries
    """
    try:
        response = connections_table.scan()
        connections = response.get('Items', [])
        logger.info(f"Broadcasting to {len(connections)} connections")

        success_count = 0
        for conn in connections:
            if push_to_connection(conn['connection_id'], message):
                success_count += 1

        logger.info(f"Broadcast complete: {success_count}/{len(connections)}")
        return success_count
    except Exception as e:
        logger.error(f"Error broadcasting: {e}")
        return 0
```

### requirements.txt

```
boto3>=1.34.0
```

---

## Step 3: Deploy Lambda Function

```bash
# Package Lambda
cd lambda/websocket
zip -r lambda.zip lambda_function.py requirements.txt

# Create IAM role
cat > /tmp/lambda-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

aws iam create-role \
    --role-name ${PROJECT_NAME}-websocket-lambda-role \
    --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
    --profile ${AWS_PROFILE}

# Attach policies
aws iam attach-role-policy \
    --role-name ${PROJECT_NAME}-websocket-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
    --profile ${AWS_PROFILE}

aws iam attach-role-policy \
    --role-name ${PROJECT_NAME}-websocket-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess \
    --profile ${AWS_PROFILE}

# Add API Gateway permissions
cat > /tmp/apigw-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["execute-api:ManageConnections", "execute-api:Invoke"],
    "Resource": "arn:aws:execute-api:*:*:*/*"
  }]
}
EOF

aws iam put-role-policy \
    --role-name ${PROJECT_NAME}-websocket-lambda-role \
    --policy-name ApiGatewayManagement \
    --policy-document file:///tmp/apigw-policy.json \
    --profile ${AWS_PROFILE}

# Wait for IAM role propagation
sleep 10

# Create Lambda function
aws lambda create-function \
    --function-name ${PROJECT_NAME}-websocket-handler \
    --runtime python3.11 \
    --role arn:aws:iam::${AWS_ACCOUNT_ID}:role/${PROJECT_NAME}-websocket-lambda-role \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://lambda.zip \
    --timeout 30 \
    --memory-size 256 \
    --region us-east-1 \
    --profile ${AWS_PROFILE} \
    --environment "Variables={REGION_NAME=us-east-1,CONNECTIONS_TABLE=${PROJECT_NAME}_ws_connections,WEBSOCKET_STAGE=prod}"
```

---

## Step 4: Create API Gateway WebSocket API

```bash
# Create WebSocket API
API_OUTPUT=$(aws apigatewayv2 create-api \
    --name ${PROJECT_NAME}-websocket \
    --protocol-type WEBSOCKET \
    --route-selection-expression '$request.body.action' \
    --region us-east-1 \
    --profile ${AWS_PROFILE} \
    --output json)

API_ID=$(echo $API_OUTPUT | jq -r '.ApiId')
echo "API Gateway WebSocket ID: $API_ID"

# Create integration
INTEGRATION_OUTPUT=$(aws apigatewayv2 create-integration \
    --api-id $API_ID \
    --integration-type AWS_PROXY \
    --integration-uri arn:aws:lambda:us-east-1:${AWS_ACCOUNT_ID}:function:${PROJECT_NAME}-websocket-handler \
    --region us-east-1 \
    --profile ${AWS_PROFILE} \
    --output json)

INTEGRATION_ID=$(echo $INTEGRATION_OUTPUT | jq -r '.IntegrationId')

# Create routes
aws apigatewayv2 create-route \
    --api-id $API_ID \
    --route-key '$connect' \
    --target "integrations/$INTEGRATION_ID" \
    --region us-east-1 \
    --profile ${AWS_PROFILE}

aws apigatewayv2 create-route \
    --api-id $API_ID \
    --route-key '$disconnect' \
    --target "integrations/$INTEGRATION_ID" \
    --region us-east-1 \
    --profile ${AWS_PROFILE}

aws apigatewayv2 create-route \
    --api-id $API_ID \
    --route-key '$default' \
    --target "integrations/$INTEGRATION_ID" \
    --region us-east-1 \
    --profile ${AWS_PROFILE}

# Create prod stage with auto-deploy
aws apigatewayv2 create-stage \
    --api-id $API_ID \
    --stage-name prod \
    --auto-deploy \
    --region us-east-1 \
    --profile ${AWS_PROFILE}

# Grant API Gateway permission to invoke Lambda
aws lambda add-permission \
    --function-name ${PROJECT_NAME}-websocket-handler \
    --statement-id apigateway-websocket-invoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:us-east-1:${AWS_ACCOUNT_ID}:${API_ID}/*" \
    --region us-east-1 \
    --profile ${AWS_PROFILE}

# Update Lambda with API ID
aws lambda update-function-configuration \
    --function-name ${PROJECT_NAME}-websocket-handler \
    --environment "Variables={REGION_NAME=us-east-1,CONNECTIONS_TABLE=${PROJECT_NAME}_ws_connections,WEBSOCKET_API_ID=${API_ID},WEBSOCKET_STAGE=prod}" \
    --region us-east-1 \
    --profile ${AWS_PROFILE}

echo "WebSocket URL: wss://${API_ID}.execute-api.us-east-1.amazonaws.com/prod"
```

---

## Step 5: Frontend Implementation (React)

### Custom WebSocket Hook

**File**: `src/hooks/useWebSocket.js`

```javascript
import { useEffect, useRef, useState } from 'react';

export function useWebSocket(url) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);
  const eventHandlers = useRef(new Map());
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);

  const connect = () => {
    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        reconnectAttempts.current = 0;

        const connectHandlers = eventHandlers.current.get('connect') || [];
        connectHandlers.forEach(handler => handler());
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        wsRef.current = null;

        const disconnectHandlers = eventHandlers.current.get('disconnect') || [];
        disconnectHandlers.forEach(handler => handler());

        // Exponential backoff reconnection
        reconnectAttempts.current++;
        const backoffTime = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        console.log(`Reconnecting in ${backoffTime/1000}s...`);
        reconnectTimeoutRef.current = setTimeout(connect, backoffTime);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          const { type, data } = message;

          const handlers = eventHandlers.current.get(type) || [];
          handlers.forEach(handler => handler(data));
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Error creating WebSocket:', error);
    }
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  };

  const on = (eventName, handler) => {
    const handlers = eventHandlers.current.get(eventName) || [];
    handlers.push(handler);
    eventHandlers.current.set(eventName, handlers);
  };

  const off = (eventName, handler) => {
    if (!handler) {
      eventHandlers.current.delete(eventName);
    } else {
      const handlers = eventHandlers.current.get(eventName) || [];
      const filtered = handlers.filter(h => h !== handler);
      if (filtered.length > 0) {
        eventHandlers.current.set(eventName, filtered);
      } else {
        eventHandlers.current.delete(eventName);
      }
    }
  };

  const send = (action, data = {}) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action, ...data }));
    } else {
      console.warn('WebSocket not connected. Cannot send message.');
    }
  };

  useEffect(() => {
    return () => disconnect();
  }, []);

  return { isConnected, connect, disconnect, on, off, send };
}
```

### Usage in React Component

```javascript
import { useEffect } from 'react';
import { useWebSocket } from './hooks/useWebSocket';

const WEBSOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'ws://localhost:3002/ws';

function App() {
  const { isConnected, connect, on, off } = useWebSocket(WEBSOCKET_URL);

  useEffect(() => {
    // Connect to WebSocket
    connect();

    // Setup event handlers
    on('connected', (data) => {
      console.log('Connected:', data);
    });

    on('claim_submitted', (data) => {
      console.log('Claim submitted:', data);
    });

    // Cleanup
    return () => {
      off('connected');
      off('claim_submitted');
    };
  }, [connect, on, off]);

  return (
    <div>
      <p>WebSocket Status: {isConnected ? '✅ Connected' : '❌ Disconnected'}</p>
    </div>
  );
}
```

### Environment Variables

**File**: `.env.production`

```bash
VITE_SOCKET_URL=wss://${API_ID}.execute-api.us-east-1.amazonaws.com/prod
```

---

## Step 6: Broadcasting from Backend Services

### From Another Lambda Function

```python
import boto3
import json

def broadcast_claim_update(claim_data):
    """Broadcast claim update to all connected WebSocket clients."""
    lambda_client = boto3.client('lambda')

    payload = {
        "action": "broadcast",
        "message": {
            "type": "claim_status_update",
            "data": claim_data
        }
    }

    lambda_client.invoke(
        FunctionName='${PROJECT_NAME}-websocket-handler',
        InvocationType='Event',  # Async invoke
        Payload=json.dumps(payload)
    )
```

### From FastAPI Backend

```python
import boto3
import json

lambda_client = boto3.client('lambda', region_name='us-east-1')

async def broadcast_notification(event_type: str, data: dict):
    """Broadcast notification to all WebSocket clients."""
    payload = {
        "action": "broadcast",
        "message": {
            "type": event_type,
            "data": data
        }
    }

    lambda_client.invoke(
        FunctionName='${PROJECT_NAME}-websocket-handler',
        InvocationType='Event',
        Payload=json.dumps(payload)
    )
```

---

## Testing

### Test WebSocket Connection (Python)

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "wss://${API_ID}.execute-api.us-east-1.amazonaws.com/prod"
    async with websockets.connect(uri) as websocket:
        print("✓ Connected")

        # Send ping
        await websocket.send(json.dumps({"action": "ping"}))

        # Receive pong
        response = await websocket.recv()
        print(f"✓ Response: {json.loads(response)}")

asyncio.run(test_websocket())
```

### Check Active Connections

```bash
aws dynamodb scan \
    --table-name ${PROJECT_NAME}_ws_connections \
    --region us-east-1 \
    --profile ${AWS_PROFILE}
```

---

## Cost Estimate

**Per Million Messages**:
- API Gateway WebSocket: $1.00
- Lambda invocations: $0.20
- DynamoDB writes: $1.25
- **Total**: ~$2.45 per million messages

**Idle Cost**: $0 (DynamoDB on-demand, Lambda pay-per-use)

---

## Troubleshooting

### WebSocket Connection Fails

1. **Check Lambda logs**:
```bash
aws logs tail /aws/lambda/${PROJECT_NAME}-websocket-handler --follow --region us-east-1 --profile ${AWS_PROFILE}
```

2. **Verify API Gateway permissions**:
```bash
aws lambda get-policy --function-name ${PROJECT_NAME}-websocket-handler --region us-east-1 --profile ${AWS_PROFILE}
```

3. **Check DynamoDB table exists**:
```bash
aws dynamodb describe-table --table-name ${PROJECT_NAME}_ws_connections --region us-east-1 --profile ${AWS_PROFILE}
```

### Messages Not Broadcasting

1. Ensure Lambda has `WEBSOCKET_API_ID` environment variable set
2. Check IAM role has `execute-api:ManageConnections` permission
3. Verify connection IDs exist in DynamoDB

---

## Production Checklist

- [ ] Enable CloudWatch Logs for API Gateway
- [ ] Set up CloudWatch Alarms for Lambda errors
- [ ] Configure DynamoDB auto-scaling (if needed)
- [ ] Add API Gateway throttling limits
- [ ] Implement connection authentication (JWT in querystring)
- [ ] Add monitoring dashboard
- [ ] Document custom event types
- [ ] Test reconnection scenarios
- [ ] Load test with expected traffic

---

## References

- **Proven in Production**: COM Simulation (1+ year stable)
- **AWS Docs**: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api.html
- **Related Projects**:
  - PetInsure360 (this implementation)
  - Sempra COM Meter Simulation
