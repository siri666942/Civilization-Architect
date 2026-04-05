import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { BookOpen, Users, GitBranch, CircleDot, Network, ChevronRight } from 'lucide-react'
import { gameApi } from '@/services/api'
import { useGame } from '@/stores/GameContext'
import type { ArchitectureType, Agent } from '@/types/game'

const STORY_BACKGROUND = `在遥远的仙女座星系边缘，一颗名为"新星"的行星正经历着前所未有的变革。

古老的星际联邦已经衰落，十个独特的Agent——从忠诚的守护者到野心勃勃的革新者——在这片废墟上建立新的文明。

作为文明的架构师，你必须选择一种组织架构来引导他们。你的选择将决定信息如何流动、资源如何分配、信任如何建立。

有些Agent生来就是领导者，有些更愿意默默付出，还有一些...他们的真实意图隐藏在微笑背后。

最终，文明的命运将取决于你的决策。`

const ARCHITECTURES = [
  {
    type: 'tree' as ArchitectureType,
    name: '树形架构',
    icon: GitBranch,
    description: '层级分明，信息自上而下流动。适合需要明确指挥的场景。',
    color: 'border-green-500',
    bgColor: 'bg-green-500/10',
  },
  {
    type: 'star' as ArchitectureType,
    name: '星形架构',
    icon: CircleDot,
    description: '中心节点连接所有其他节点。信息汇聚快速，但中心压力大。',
    color: 'border-yellow-500',
    bgColor: 'bg-yellow-500/10',
  },
  {
    type: 'mesh' as ArchitectureType,
    name: '网状架构',
    icon: Network,
    description: '所有节点互相连接。信息传播最快，但管理复杂度最高。',
    color: 'border-cyber-accent',
    bgColor: 'bg-cyber-accent/10',
  },
]

export default function SelectPage() {
  const [showModal, setShowModal] = useState(true)
  const [selectedArch, setSelectedArch] = useState<ArchitectureType | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [mockAgents, setMockAgents] = useState<Agent[]>([])
  const navigate = useNavigate()
  const { state, dispatch } = useGame()

  useEffect(() => {
    // 生成模拟Agent数据用于展示
    const agentNames = [
      '领导者', '老实人', '野心家', '社交达人', '分析师',
      '守护者', '创新者', '协调者', '执行者', '观察者'
    ]
    const descriptions = [
      '天生领袖，决策果断',
      '踏实可靠，从不抱怨',
      '志向远大，城府较深',
      '人缘极好，擅长调解',
      '逻辑严密，洞察敏锐',
      '忠诚坚定，守护正义',
      '思维活跃，打破常规',
      '圆滑周到，左右逢源',
      '执行力强，雷厉风行',
      '安静内敛，观察入微',
    ]
    const positions: ('core' | 'middle' | 'edge')[] = ['core', 'middle', 'edge']

    const agents: Agent[] = agentNames.map((name, i) => ({
      id: `AGENT-${String(i + 1).padStart(3, '0')}`,
      name,
      description: descriptions[i],
      personality: {
        authority: Math.random(),
        selfishness: Math.random(),
        resilience: Math.random(),
        altruism: Math.random(),
        sociability: Math.random(),
        risk_appetite: Math.random(),
        intelligence: Math.random(),
        loyalty_base: Math.random(),
      },
      position: positions[i % 3],
      level: i % 3,
      centrality: Math.random(),
      is_traitor: false,
    }))

    setMockAgents(agents)
  }, [])

  const handleConfirm = async () => {
    if (!selectedArch) return

    setIsLoading(true)
    try {
      const gameState = await gameApi.startGame(state.username, selectedArch)
      dispatch({ type: 'SET_GAME_STATE', payload: gameState })
      dispatch({ type: 'SET_GAME_ID', payload: gameState.game_id })
      navigate(`/editor/${gameState.game_id}`)
    } catch (error) {
      console.error('Failed to start game:', error)
      alert('启动游戏失败，请重试')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen p-4 md:p-6">
      {/* 入场弹窗 */}
      <AnimatePresence>
        {showModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="card max-w-lg w-full p-6"
            >
              <h3 className="font-heading text-2xl text-cyber-accent mb-4 flex items-center gap-2">
                <BookOpen className="w-6 h-6" />
                任务简报
              </h3>
              <p className="font-body text-cyber-text-muted mb-6 leading-relaxed">
                请仔细阅读左侧的故事背景和中间每位Agent的特点，然后在右侧选择一种组织架构。
                你的选择将决定这个文明的最终命运和<span className="text-cyber-accent">星辰值</span>。
              </p>
              <button
                onClick={() => setShowModal(false)}
                className="btn-primary w-full"
              >
                已了解，开始规划
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 主内容 */}
      <div className="max-w-7xl mx-auto grid md:grid-cols-12 gap-6">
        {/* 左侧：故事背景 */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="md:col-span-3"
        >
          <div className="card h-full">
            <h3 className="font-heading text-lg text-cyber-accent mb-4 flex items-center gap-2">
              <BookOpen className="w-5 h-5" />
              故事背景
            </h3>
            <div className="prose prose-invert prose-sm">
              {STORY_BACKGROUND.split('\n\n').map((para, i) => (
                <p key={i} className="text-cyber-text-muted mb-3 leading-relaxed">
                  {para}
                </p>
              ))}
            </div>
          </div>
        </motion.div>

        {/* 中间：Agent卡片 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="md:col-span-6"
        >
          <div className="mb-4">
            <h3 className="font-heading text-lg text-cyber-accent flex items-center gap-2">
              <Users className="w-5 h-5" />
              Agent阵列
            </h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {mockAgents.map((agent, index) => (
              <AgentCard key={agent.id} agent={agent} index={index} />
            ))}
          </div>
        </motion.div>

        {/* 右侧：架构选择 */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="md:col-span-3"
        >
          <div className="card">
            <h3 className="font-heading text-lg text-cyber-accent mb-4">
              请选择架构
            </h3>
            <div className="space-y-4">
              {ARCHITECTURES.map((arch) => (
                <button
                  key={arch.type}
                  onClick={() => setSelectedArch(arch.type)}
                  className={`w-full p-4 rounded-lg border transition-all duration-300 ${
                    selectedArch === arch.type
                      ? `${arch.color} ${arch.bgColor} border-2`
                      : 'border-cyber-border hover:border-cyber-accent/50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <arch.icon className={`w-6 h-6 ${
                      selectedArch === arch.type ? 'text-cyber-accent' : 'text-cyber-text-muted'
                    }`} />
                    <span className={`font-heading text-lg ${
                      selectedArch === arch.type ? 'text-cyber-text' : 'text-cyber-text-muted'
                    }`}>
                      {arch.name}
                    </span>
                  </div>
                  <p className="text-xs text-cyber-text-muted mt-2 text-left">
                    {arch.description}
                  </p>
                </button>
              ))}
            </div>

            <button
              onClick={handleConfirm}
              disabled={!selectedArch || isLoading}
              className={`btn-primary w-full mt-6 flex items-center justify-center gap-2 ${
                (!selectedArch || isLoading) ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              {isLoading ? (
                <span>初始化中...</span>
              ) : (
                <>
                  <span>确认选择</span>
                  <ChevronRight className="w-5 h-5" />
                </>
              )}
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

function AgentCard({ agent, index }: { agent: Agent; index: number }) {
  const positionColors = {
    core: 'border-yellow-500',
    middle: 'border-blue-500',
    edge: 'border-gray-500',
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.05 }}
      className={`card p-3 border-l-2 ${positionColors[agent.position]} cursor-pointer hover:scale-105 transition-transform`}
    >
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-8 h-8 rounded-full ${
          agent.position === 'core' ? 'bg-yellow-500/20' :
          agent.position === 'middle' ? 'bg-blue-500/20' : 'bg-gray-500/20'
        } flex items-center justify-center`}>
          <span className="font-heading text-sm text-cyber-accent">
            {agent.name[0]}
          </span>
        </div>
        <span className="font-heading text-sm text-cyber-text">{agent.name}</span>
      </div>
      <p className="text-xs text-cyber-text-muted line-clamp-2">{agent.description}</p>

      {/* 简化的属性展示 */}
      <div className="mt-2 grid grid-cols-2 gap-1">
        {Object.entries({
          '智力': agent.personality.intelligence,
          '忠诚': agent.personality.loyalty_base,
          '社交': agent.personality.sociability,
          '利他': agent.personality.altruism,
        }).map(([key, value]) => (
          <div key={key} className="flex items-center gap-1">
            <span className="text-[10px] text-cyber-text-muted">{key}</span>
            <div className="flex-1 h-1 bg-cyber-border rounded-full overflow-hidden">
              <div
                className="h-full bg-cyber-accent rounded-full"
                style={{ width: `${value * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  )
}