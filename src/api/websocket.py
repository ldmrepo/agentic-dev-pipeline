"""
WebSocket 매니저
실시간 파이프라인 상태 업데이트
"""

from typing import Dict, Set, Optional
from fastapi import WebSocket
import json
import logging
import asyncio

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket 연결 관리"""
    
    def __init__(self):
        # 클라이언트 ID -> WebSocket 연결 매핑
        self.active_connections: Dict[str, WebSocket] = {}
        # 파이프라인 ID -> 구독 클라이언트 ID 세트 매핑
        self.pipeline_subscriptions: Dict[str, Set[str]] = {}
        # 클라이언트 ID -> 구독 파이프라인 ID 세트 매핑
        self.client_subscriptions: Dict[str, Set[str]] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """WebSocket 연결 수락"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_subscriptions[client_id] = set()
        logger.info(f"WebSocket client {client_id} connected")
        
    def disconnect(self, client_id: str):
        """WebSocket 연결 종료"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
        # 구독 정리
        if client_id in self.client_subscriptions:
            for pipeline_id in self.client_subscriptions[client_id]:
                if pipeline_id in self.pipeline_subscriptions:
                    self.pipeline_subscriptions[pipeline_id].discard(client_id)
                    if not self.pipeline_subscriptions[pipeline_id]:
                        del self.pipeline_subscriptions[pipeline_id]
            del self.client_subscriptions[client_id]
            
        logger.info(f"WebSocket client {client_id} disconnected")
        
    async def subscribe_to_pipeline(self, client_id: str, pipeline_id: str):
        """파이프라인 상태 구독"""
        if client_id not in self.active_connections:
            logger.error(f"Client {client_id} not connected")
            return
            
        # 파이프라인 구독 추가
        if pipeline_id not in self.pipeline_subscriptions:
            self.pipeline_subscriptions[pipeline_id] = set()
        self.pipeline_subscriptions[pipeline_id].add(client_id)
        
        # 클라이언트 구독 추가
        self.client_subscriptions[client_id].add(pipeline_id)
        
        logger.info(f"Client {client_id} subscribed to pipeline {pipeline_id}")
        
    async def unsubscribe_from_pipeline(self, client_id: str, pipeline_id: str):
        """파이프라인 구독 취소"""
        if pipeline_id in self.pipeline_subscriptions:
            self.pipeline_subscriptions[pipeline_id].discard(client_id)
            if not self.pipeline_subscriptions[pipeline_id]:
                del self.pipeline_subscriptions[pipeline_id]
                
        if client_id in self.client_subscriptions:
            self.client_subscriptions[client_id].discard(pipeline_id)
            
        logger.info(f"Client {client_id} unsubscribed from pipeline {pipeline_id}")
        
    async def send_personal_message(self, message: dict, client_id: str):
        """특정 클라이언트에게 메시지 전송"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {e}")
                self.disconnect(client_id)
                
    async def broadcast_pipeline_update(self, pipeline_id: str, update: dict):
        """파이프라인 구독자들에게 업데이트 브로드캐스트"""
        if pipeline_id not in self.pipeline_subscriptions:
            return
            
        message = {
            "type": "pipeline_update",
            "pipeline_id": pipeline_id,
            "data": update
        }
        
        # 비동기 전송을 위한 태스크 목록
        tasks = []
        disconnected_clients = []
        
        for client_id in self.pipeline_subscriptions[pipeline_id]:
            if client_id in self.active_connections:
                websocket = self.active_connections[client_id]
                try:
                    tasks.append(websocket.send_json(message))
                except Exception as e:
                    logger.error(f"Error sending update to client {client_id}: {e}")
                    disconnected_clients.append(client_id)
                    
        # 모든 메시지 동시 전송
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
        # 연결이 끊긴 클라이언트 정리
        for client_id in disconnected_clients:
            self.disconnect(client_id)
            
    async def broadcast_agent_update(self, agent_name: str, pipeline_id: str, update: dict):
        """에이전트 상태 업데이트 브로드캐스트"""
        message = {
            "type": "agent_update",
            "agent": agent_name,
            "pipeline_id": pipeline_id,
            "data": update
        }
        
        await self.broadcast_pipeline_update(pipeline_id, message)
        
    async def broadcast_error(self, pipeline_id: str, error: dict):
        """에러 메시지 브로드캐스트"""
        message = {
            "type": "error",
            "pipeline_id": pipeline_id,
            "error": error
        }
        
        await self.broadcast_pipeline_update(pipeline_id, message)
        
    def get_connection_count(self) -> int:
        """활성 연결 수 반환"""
        return len(self.active_connections)
        
    def get_pipeline_subscriber_count(self, pipeline_id: str) -> int:
        """특정 파이프라인 구독자 수 반환"""
        return len(self.pipeline_subscriptions.get(pipeline_id, set()))