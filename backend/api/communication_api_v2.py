"""
通讯系统 API v2

FastAPI路由版本
"""

from fastapi import APIRouter, Query, Path
from typing import Optional, List

from backend.api.communication_api import CommunicationAPI, ApiResponse


router = APIRouter()
_api = CommunicationAPI()


@router.get("/messages")
async def get_messages(
    civilization_id: str = Query(..., description="文明ID"),
    round_num: Optional[int] = Query(None, description="回合号"),
    cycle_num: Optional[int] = Query(None, description="循环号"),
    message_type: Optional[str] = Query(None, description="消息类型"),
    min_importance: float = Query(0.0, description="最小重要性"),
    limit: int = Query(50, description="返回数量"),
    offset: int = Query(0, description="分页偏移")
):
    """获取消息列表"""
    result = _api.get_messages(
        civilization_id=civilization_id,
        round_num=round_num,
        cycle_num=cycle_num,
        message_type=message_type,
        min_importance=min_importance,
        limit=limit,
        offset=offset
    )
    return result.to_dict()


@router.get("/conversations/{agent1_id}/{agent2_id}")
async def get_conversation(
    agent1_id: str = Path(..., description="Agent1 ID"),
    agent2_id: str = Path(..., description="Agent2 ID"),
    civilization_id: str = Query(..., description="文明ID"),
    limit: int = Query(100, description="消息数量限制")
):
    """获取两个Agent之间的对话"""
    result = _api.get_conversation(
        agent1_id=agent1_id,
        agent2_id=agent2_id,
        civilization_id=civilization_id,
        limit=limit
    )
    return result.to_dict()


@router.get("/civilizations/{civilization_id}/activity")
async def get_civilization_activity(
    civilization_id: str = Path(..., description="文明ID"),
    rounds: int = Query(3, description="统计最近几回合")
):
    """获取文明活动摘要"""
    result = _api.get_civilization_activity(
        civilization_id=civilization_id,
        rounds=rounds
    )
    return result.to_dict()


@router.get("/civilizations/{civilization_id}/traitor-messages")
async def get_traitor_messages(
    civilization_id: str = Path(..., description="文明ID"),
    include_detected: bool = Query(False, description="是否包含已检测到的")
):
    """获取内鬼相关消息"""
    result = _api.get_traitor_messages(
        civilization_id=civilization_id,
        include_detected=include_detected
    )
    return result.to_dict()


@router.get("/civilizations/{civilization_id}/timeline")
async def get_timeline(
    civilization_id: str = Path(..., description="文明ID"),
    round_num: Optional[int] = Query(None, description="回合号")
):
    """获取消息时间线"""
    result = _api.get_timeline(
        civilization_id=civilization_id,
        round_num=round_num
    )
    return result.to_dict()


@router.get("/civilizations/{civilization_id}/hot-conversations")
async def get_hot_conversations(
    civilization_id: str = Path(..., description="文明ID"),
    limit: int = Query(5, description="返回数量")
):
    """获取热门对话"""
    result = _api.get_hot_conversations(
        civilization_id=civilization_id,
        limit=limit
    )
    return result.to_dict()