"""
WebSocket routes for real-time updates
"""

from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
import json

from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Accept and register a new WebSocket connection

        Args:
            websocket: WebSocket connection to register
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection

        Args:
            websocket: WebSocket connection to remove
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

            # Try to close the connection gracefully
            try:
                if websocket.client_state != WebSocketState.DISCONNECTED:
                    await websocket.close()
            except Exception as e:
                logger.debug(f"Error closing WebSocket (already closed): {e}")

            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """
        Broadcast a message to all connected clients

        Args:
            message: Dictionary to send as JSON
        """
        if not self.active_connections:
            logger.debug("No WebSocket connections to broadcast to")
            return

        logger.debug(f"Broadcasting to {len(self.active_connections)} clients")

        # Send to all connections
        disconnected = []
        success_count = 0
        for connection in self.active_connections:
            try:
                # Check connection state before sending
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_json(message)
                    success_count += 1
                else:
                    logger.debug(f"Skipping disconnected client (state: {connection.client_state})")
                    disconnected.append(connection)
            except WebSocketDisconnect:
                logger.debug("Client disconnected during broadcast")
                disconnected.append(connection)
            except Exception as e:
                logger.warning(f"Failed to send to connection: {type(e).__name__}: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        if disconnected:
            logger.info(f"Cleaning up {len(disconnected)} disconnected clients")
            for connection in disconnected:
                await self.disconnect(connection)

        logger.debug(f"Broadcast complete: {success_count} successful, {len(disconnected)} failed")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Send a message to a specific client

        Args:
            message: Dictionary to send as JSON
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            await self.disconnect(websocket)


# Global connection manager instance
websocket_manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates

    Clients connect here to receive live updates when vehicle data changes
    """
    await websocket_manager.connect(websocket)

    try:
        # Send initial status immediately
        from api.app import tesla_service, ioniq_service, decision_engine
        from datetime import datetime

        try:
            # Get Tesla status
            tesla_status = await tesla_service.get_vehicle_status()

            # Get Ioniq status (if enabled)
            ioniq_status = None
            if ioniq_service:
                ioniq_status = await ioniq_service.get_vehicle_status()

            # Calculate recommendations
            recommendations = await decision_engine.calculate_dual_recommendations(
                tesla_status,
                ioniq_status
            )

            # Build message
            message = {
                "type": "initial_status",
                "timestamp": datetime.now().isoformat(),
                "tesla": tesla_status.to_dict(),
                "tesla_recommendation": recommendations['tesla'].to_dict(),
                "priority_vehicle": recommendations['priority_vehicle']
            }

            # Add Ioniq data if available
            if ioniq_status and recommendations['ioniq']:
                message['ioniq'] = ioniq_status.to_dict()
                message['ioniq_recommendation'] = recommendations['ioniq'].to_dict()

            await websocket_manager.send_personal_message(message, websocket)

        except Exception as e:
            logger.error(f"Failed to send initial status: {e}")

        # Keep connection alive and handle incoming messages
        while True:
            # Receive message (this keeps the connection alive)
            # Clients can send ping messages to keep connection active
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                # Handle different message types
                if message.get("type") == "ping":
                    # Respond with pong
                    await websocket_manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }, websocket)

                elif message.get("type") == "request_status":
                    # Client requesting current status
                    tesla_status = await tesla_service.get_vehicle_status()

                    # Get Ioniq status (if enabled)
                    ioniq_status = None
                    if ioniq_service:
                        ioniq_status = await ioniq_service.get_vehicle_status()

                    # Calculate recommendations
                    recommendations = await decision_engine.calculate_dual_recommendations(
                        tesla_status,
                        ioniq_status
                    )

                    # Build response
                    response = {
                        "type": "status_update",
                        "timestamp": datetime.now().isoformat(),
                        "tesla": tesla_status.to_dict(),
                        "tesla_recommendation": recommendations['tesla'].to_dict(),
                        "priority_vehicle": recommendations['priority_vehicle']
                    }

                    # Add Ioniq data if available
                    if ioniq_status and recommendations['ioniq']:
                        response['ioniq'] = ioniq_status.to_dict()
                        response['ioniq_recommendation'] = recommendations['ioniq'].to_dict()

                    await websocket_manager.send_personal_message(response, websocket)

                else:
                    logger.warning(f"Unknown message type: {message.get('type')}")

            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON: {data}")
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")

    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket_manager.disconnect(websocket)
