import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeft, Play, SkipForward, Flag, MessageSquare,
  BarChart3, Users, Settings, ChevronDown, ChevronUp
} from 'lucide-react'
import { gameApi } from '@/services/api'
import { useGame } from '@/stores/GameContext'
import type { Agent, Message, MacroVariables, AgentPosition } from '@/types/game'

export default function EditorPage() {
  const { gameId } = useParams<{ gameId: string }>()
  const navigate = useNavigate()
  const { state, dispatch } = useGame()
  const [isRunning, setIsRunning] = useState(false)
  const [showCardPool, setShowCardPool] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [agentPositions, setAgentPositions] = useState<Map<number, string>>(new Map())
  const [macroVars, setMacroVars] = useState<MacroVariables | null>(null)

  const agents = state.gameState?.agents || []

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [state.messages])

  // 更新架构位置
  const handlePositionUpdate = useCallback(async () => {
    if (!gameId) return

    const positions: AgentPosition[] = Array.from(agentPositions.entries()).map(
      ([index, agentId]) => ({
        agent_id: agentId,
        position_index: index,
        connections: [], // 网状架构时使用
      })
    )

    try {
      await gameApi.updateArchitecture(gameId, positions)
    } catch (error) {
      console.error('Failed to update architecture:', error)
    }
  }, [gameId, agentPositions])

  // 执行一轮模拟
  const handleRunRound = async () => {
    if (!gameId || isRunning) return

    setIsRunning(true)
    try {
      // 先更新架构
      await handlePositionUpdate()

      // 执行模拟
      const result = await gameApi.runRound(gameId)
      dispatch({ type: 'SET_ROUND_RESULT', payload: result })
      setMacroVars(result.macro_variables)
    } catch (error) {
      console.error('Failed to run round:', error)
    } finally {
      setIsRunning(false)
    }
  }

  // 结束游戏
  const handleEndGame = async () => {
    if (!gameId) return

    try {
      const result = await gameApi.endGame(gameId)
      dispatch({ type: 'SET_FINAL_RESULT', payload: result })
      navigate(`/result/${gameId}`)
    } catch (error) {
      console.error('Failed to end game:', error)
    }
  }

  // 将Agent放置到位置
  const handleDropAgent = (agentId: string, positionIndex: number) => {
    setAgentPositions((prev) => {
      const newMap = new Map(prev)
      // 先移除该Agent的其他位置
      for (const [idx, id] of newMap.entries()) {
        if (id === agentId) {
          newMap.delete(idx)
        }
      }
      newMap.set(positionIndex, agentId)
      return newMap
    })
  }

  // 移除Agent
  const handleRemoveAgent = (positionIndex: number) => {
    setAgentPositions((prev) => {
      const newMap = new Map(prev)
      newMap.delete(positionIndex)
      return newMap
    })
  }

  const archType = state.gameState?.architecture_type || 'tree'

  return (
    <div className="min-h-screen flex flex-col">
      {/* 顶部导航栏 */}
      <header className="sticky top-0 z-40 glass border-b border-cyber-border px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <button
            onClick={() => navigate('/select')}
            className="btn-secondary flex items-center gap-2 text-sm"
          >
            <ArrowLeft className="w-4 h-4" />
            返回选择
          </button>

          <div className="flex items-center gap-6">
            <div className="font-mono text-lg">
              第 <span className="text-cyber-accent">{state.currentRound}</span> / {state.gameState?.total_rounds || 10} 轮
            </div>

            {macroVars && (
              <div className="hidden md:flex items-center gap-4 text-sm">
                <VariableBadge label="能级" value={macroVars.energy_level} color="text-yellow-400" />
                <VariableBadge label="凝聚力" value={macroVars.cohesion} color="text-green-400" />
                <VariableBadge label="保真度" value={macroVars.fidelity} color="text-blue-400" />
              </div>
            )}
          </div>

          <div className="flex items-center gap-3">
            <span className="font-mono text-cyber-success text-lg">
              ⭐ {state.gameState?.civilization_state?.total_output?.toFixed(0) || 0}
            </span>
            <button
              onClick={handleEndGame}
              className="btn-secondary flex items-center gap-2 text-sm"
            >
              <Flag className="w-4 h-4" />
              结束游戏
            </button>
          </div>
        </div>
      </header>

      {/* 主内容区 */}
      <main className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* 左侧：架构图 */}
        <div className="md:w-1/2 p-4 overflow-auto">
          <div className="card h-full">
            <h3 className="font-heading text-lg text-cyber-accent mb-4 flex items-center gap-2">
              <Settings className="w-5 h-5" />
              {archType === 'tree' ? '树形架构' : archType === 'star' ? '星形架构' : '网状架构'}
            </h3>
            <ArchitectureDiagram
              archType={archType}
              agents={agents}
              agentPositions={agentPositions}
              onDropAgent={handleDropAgent}
              onRemoveAgent={handleRemoveAgent}
            />
          </div>
        </div>

        {/* 右侧：聊天区域 */}
        <div className="md:w-1/2 flex flex-col p-4 overflow-hidden">
          <div className="card flex-1 flex flex-col overflow-hidden">
            <h3 className="font-heading text-lg text-cyber-accent mb-4 flex items-center gap-2">
              <MessageSquare className="w-5 h-5" />
              Agent实时通讯
            </h3>

            {/* 消息列表 */}
            <div className="flex-1 overflow-y-auto space-y-2 mb-4">
              <AnimatePresence>
                {state.messages.map((msg, index) => (
                  <MessageBubble key={index} message={msg} />
                ))}
              </AnimatePresence>
              <div ref={messagesEndRef} />
            </div>

            {/* 进度条 */}
            {isRunning && (
              <div className="flex items-center gap-2 p-2 bg-cyber-border/30 rounded">
                <div className="flex-1 h-2 bg-cyber-border rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-cyber-accent"
                    initial={{ width: '0%' }}
                    animate={{ width: '100%' }}
                    transition={{ duration: 2 }}
                  />
                </div>
                <span className="text-xs text-cyber-text-muted">模拟中...</span>
              </div>
            )}

            {/* 操作按钮 */}
            <div className="flex gap-3">
              <button
                onClick={handleRunRound}
                disabled={isRunning}
                className={`btn-primary flex-1 flex items-center justify-center gap-2 ${
                  isRunning ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                <Play className="w-5 h-5" />
                {isRunning ? '模拟中...' : '执行本轮'}
              </button>
              <button
                onClick={handleRunRound}
                disabled={isRunning}
                className="btn-secondary flex items-center gap-2"
              >
                <SkipForward className="w-5 h-5" />
                下一轮
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* 底部：Agent卡片池 */}
      <div className="border-t border-cyber-border">
        <button
          onClick={() => setShowCardPool(!showCardPool)}
          className="w-full px-4 py-2 flex items-center justify-center gap-2 text-cyber-text-muted hover:text-cyber-accent transition-colors"
        >
          <Users className="w-4 h-4" />
          <span>Agent卡片池</span>
          {showCardPool ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        </button>

        <AnimatePresence>
          {showCardPool && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="p-4 flex gap-3 overflow-x-auto">
                {agents.map((agent) => {
                  const isPlaced = Array.from(agentPositions.values()).includes(agent.id)
                  return (
                    <AgentMiniCard
                      key={agent.id}
                      agent={agent}
                      isPlaced={isPlaced}
                    />
                  )
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

// 架构图组件
function ArchitectureDiagram({
  archType,
  agents,
  agentPositions,
  onDropAgent,
  onRemoveAgent,
}: {
  archType: string
  agents: Agent[]
  agentPositions: Map<number, string>
  onDropAgent: (agentId: string, positionIndex: number) => void
  onRemoveAgent: (positionIndex: number) => void
}) {
  // 生成节点位置
  const getNodePositions = () => {
    const nodes: { index: number; x: number; y: number; level: number }[] = []

    if (archType === 'tree') {
      // 树形架构：根节点在上，子节点在下
      nodes.push({ index: 0, x: 50, y: 20, level: 0 })
      // 第二层
      for (let i = 0; i < 3; i++) {
        nodes.push({ index: i + 1, x: 20 + i * 30, y: 45, level: 1 })
      }
      // 第三层
      for (let i = 0; i < 6; i++) {
        nodes.push({ index: i + 4, x: 10 + i * 15, y: 75, level: 2 })
      }
    } else if (archType === 'star') {
      // 星形架构：中心节点 + 环绕节点
      nodes.push({ index: 0, x: 50, y: 50, level: 0 })
      for (let i = 0; i < 9; i++) {
        const angle = (i / 9) * Math.PI * 2 - Math.PI / 2
        nodes.push({
          index: i + 1,
          x: 50 + Math.cos(angle) * 35,
          y: 50 + Math.sin(angle) * 35,
          level: 1,
        })
      }
    } else {
      // 网状架构：随机分布
      for (let i = 0; i < 10; i++) {
        nodes.push({
          index: i,
          x: 15 + (i % 5) * 17,
          y: 20 + Math.floor(i / 5) * 35,
          level: 0,
        })
      }
    }

    return nodes
  }

  const nodes = getNodePositions()

  // 渲染连接线
  const renderConnections = () => {
    const lines: JSX.Element[] = []

    if (archType === 'tree') {
      // 根节点到第二层
      for (let i = 1; i <= 3; i++) {
        lines.push(
          <line
            key={`line-0-${i}`}
            x1={`${nodes[0].x}%`}
            y1={`${nodes[0].y}%`}
            x2={`${nodes[i].x}%`}
            y2={`${nodes[i].y}%`}
            className="stroke-cyber-accent/40 stroke-1"
          />
        )
      }
      // 第二层到第三层
      for (let i = 0; i < 3; i++) {
        for (let j = 0; j < 2; j++) {
          const fromIdx = i + 1
          const toIdx = 4 + i * 2 + j
          if (toIdx < nodes.length) {
            lines.push(
              <line
                key={`line-${fromIdx}-${toIdx}`}
                x1={`${nodes[fromIdx].x}%`}
                y1={`${nodes[fromIdx].y}%`}
                x2={`${nodes[toIdx].x}%`}
                y2={`${nodes[toIdx].y}%`}
                className="stroke-cyber-accent/40 stroke-1"
              />
            )
          }
        }
      }
    } else if (archType === 'star') {
      // 中心到所有节点
      for (let i = 1; i < nodes.length; i++) {
        lines.push(
          <line
            key={`line-0-${i}`}
            x1={`${nodes[0].x}%`}
            y1={`${nodes[0].y}%`}
            x2={`${nodes[i].x}%`}
            y2={`${nodes[i].y}%`}
            className="stroke-cyber-accent/40 stroke-1"
          />
        )
      }
    }

    return lines
  }

  return (
    <div className="relative h-96 md:h-full min-h-[300px]">
      <svg className="absolute inset-0 w-full h-full pointer-events-none">
        {renderConnections()}
      </svg>

      {nodes.map((node) => {
        const agentId = agentPositions.get(node.index)
        const agent = agents.find((a) => a.id === agentId)

        return (
          <div
            key={node.index}
            className={`absolute transform -translate-x-1/2 -translate-y-1/2 ${
              node.level === 0 ? 'z-20' : node.level === 1 ? 'z-10' : 'z-0'
            }`}
            style={{ left: `${node.x}%`, top: `${node.y}%` }}
          >
            {agent ? (
              <div
                className="w-14 h-14 rounded-xl bg-cyber-secondary border-2 border-cyber-accent flex flex-col items-center justify-center cursor-pointer hover:scale-110 transition-transform"
                onClick={() => onRemoveAgent(node.index)}
                title="点击移除"
              >
                <span className="font-heading text-xs text-cyber-accent">
                  {agent.name.slice(0, 2)}
                </span>
                <span className="text-[10px] text-cyber-text-muted">
                  {agent.position === 'core' ? '核心' : agent.position === 'middle' ? '中层' : '边缘'}
                </span>
              </div>
            ) : (
              <div
                className="w-14 h-14 rounded-xl border-2 border-dashed border-cyber-border flex items-center justify-center cursor-pointer hover:border-cyber-accent transition-colors"
                onClick={() => {
                  // 简单实现：选择第一个未放置的Agent
                  const placedIds = new Set(agentPositions.values())
                  const unplacedAgent = agents.find((a) => !placedIds.has(a.id))
                  if (unplacedAgent) {
                    onDropAgent(unplacedAgent.id, node.index)
                  }
                }}
              >
                <span className="text-cyber-text-muted text-2xl">+</span>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

// 消息气泡组件
function MessageBubble({ message }: { message: Message }) {
  const toneColors: Record<string, string> = {
    friendly: 'border-l-green-500',
    neutral: 'border-l-cyber-border',
    hostile: 'border-l-red-500',
    urgent: 'border-l-yellow-500',
  }

  const toneEmojis: Record<string, string> = {
    friendly: '😊',
    neutral: '😐',
    hostile: '😠',
    urgent: '⚠️',
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`p-3 rounded-lg bg-cyber-secondary/50 border-l-2 ${
        toneColors[message.tone] || 'border-l-cyber-border'
      } ${message.is_traitor ? 'bg-red-900/10' : ''}`}
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="font-heading text-sm text-cyber-accent">{message.sender_name}</span>
        <span className="text-xs">{toneEmojis[message.tone] || ''}</span>
        {message.is_traitor && (
          <span className="text-xs text-cyber-danger">🦊</span>
        )}
        <span className="ml-auto text-xs text-cyber-text-muted">{message.message_type}</span>
      </div>
      <p className="text-sm text-cyber-text">
        {message.content.includes('@') ? (
          <span>
            {message.content.split(/(@\w+)/g).map((part, i) =>
              part.startsWith('@') ? (
                <span key={i} className="text-cyber-accent underline">{part}</span>
              ) : (
                <span key={i}>{part}</span>
              )
            )}
          </span>
        ) : (
          message.content
        )}
      </p>
      <span className="text-[10px] text-cyber-text-muted">{message.timestamp}</span>
    </motion.div>
  )
}

// Agent迷你卡组件
function AgentMiniCard({ agent, isPlaced }: { agent: Agent; isPlaced: boolean }) {
  return (
    <div
      className={`flex-shrink-0 w-20 p-2 rounded-lg border transition-all cursor-pointer ${
        isPlaced
          ? 'opacity-40 bg-cyber-secondary/30 border-cyber-border'
          : 'bg-cyber-secondary border-cyber-accent/40 hover:border-cyber-accent hover:scale-105'
      }`}
    >
      <div className="flex flex-col items-center">
        <div className={`w-10 h-10 rounded-full ${
          agent.position === 'core' ? 'bg-yellow-500/20' :
          agent.position === 'middle' ? 'bg-blue-500/20' : 'bg-gray-500/20'
        } flex items-center justify-center mb-1`}>
          <span className="font-heading text-sm text-cyber-accent">
            {agent.name[0]}
          </span>
        </div>
        <span className="font-heading text-xs text-cyber-text truncate">{agent.name}</span>
        {!isPlaced && (
          <div className="mt-1 w-full h-1 bg-cyber-border rounded-full overflow-hidden">
            <div
              className="h-full bg-cyber-accent rounded-full"
              style={{ width: `${agent.centrality * 100}%` }}
            />
          </div>
        )}
      </div>
    </div>
  )
}

// 变量徽章组件
function VariableBadge({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-1">
      <span className="text-cyber-text-muted">{label}:</span>
      <span className={`font-mono ${color}`}>{(value * 100).toFixed(0)}%</span>
    </div>
  )
}