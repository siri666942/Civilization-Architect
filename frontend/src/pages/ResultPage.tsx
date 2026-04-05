import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Star, BarChart2, Award, FileText, Trophy,
  RotateCcw, Home, TrendingUp
} from 'lucide-react'
import { useGame } from '@/stores/GameContext'

const archNames: Record<string, string> = {
  star: '星形架构',
  tree: '树形架构',
  mesh: '网状架构',
  tribal: '部落架构',
}

export default function ResultPage() {
  const navigate = useNavigate()
  const { state } = useGame()
  const result = state.finalResult

  useEffect(() => {
    if (!result) {
      navigate('/')
    }
  }, [result, navigate])

  if (!result) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-cyber-text-muted">加载中...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        {/* 标题 */}
        <motion.div
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="font-display text-4xl md:text-5xl text-cyber-accent neon-text mb-4">
            🏆 游 戏 结 束
          </h1>
          <p className="font-heading text-xl text-cyber-text-muted">
            {result.username} 的文明之旅
          </p>
        </motion.div>

        {/* 主要内容 */}
        <div className="grid md:grid-cols-3 gap-6">
          {/* 左侧：最终结算 */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="space-y-6"
          >
            {/* 星辰值 */}
            <div className="card text-center">
              <div className="flex items-center justify-center gap-2 mb-4">
                <Star className="w-6 h-6 text-cyber-success" />
                <h3 className="font-heading text-lg text-cyber-text">星辰值</h3>
              </div>
              <div className="font-mono text-5xl text-cyber-success neon-text mb-4">
                {result.total_output.toFixed(0)}
              </div>
              <div className="text-sm text-cyber-text-muted">
                架构: {archNames[result.architecture_type] || result.architecture_type}
              </div>
            </div>

            {/* 核心数值 */}
            <div className="card">
              <h3 className="font-heading text-lg text-cyber-accent mb-4 flex items-center gap-2">
                <BarChart2 className="w-5 h-5" />
                核心数值
              </h3>
              <div className="space-y-3">
                <VariableBar
                  label="能级"
                  value={result.final_macro_variables.energy_level}
                  color="bg-yellow-500"
                />
                <VariableBar
                  label="凝聚力"
                  value={result.final_macro_variables.cohesion}
                  color="bg-green-500"
                />
                <VariableBar
                  label="保真度"
                  value={result.final_macro_variables.fidelity}
                  color="bg-blue-500"
                />
                <VariableBar
                  label="社会资本"
                  value={result.final_macro_variables.social_capital}
                  color="bg-purple-500"
                />
              </div>
            </div>

            {/* 成就 */}
            <div className="card">
              <h3 className="font-heading text-lg text-cyber-accent mb-4 flex items-center gap-2">
                <Award className="w-5 h-5" />
                成就解锁
              </h3>
              <div className="space-y-2">
                {result.achievements.length > 0 ? (
                  result.achievements.map((achievement, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.5 + i * 0.1 }}
                      className="flex items-center gap-2 p-2 rounded bg-cyber-accent/10"
                    >
                      <span className="text-cyber-text">{achievement}</span>
                    </motion.div>
                  ))
                ) : (
                  <p className="text-cyber-text-muted text-sm">暂无成就解锁</p>
                )}
              </div>
            </div>
          </motion.div>

          {/* 中间：玩家形象 */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="flex flex-col items-center justify-center"
          >
            <div className="relative">
              {/* 光环效果 */}
              <div className="absolute inset-0 bg-cyber-accent/20 rounded-full blur-xl scale-110" />

              {/* 玩家形象 */}
              <div className="relative w-48 h-48 rounded-full bg-gradient-to-br from-cyber-accent to-cyber-accent-alt flex items-center justify-center">
                <div className="w-40 h-40 rounded-full bg-cyber-secondary flex items-center justify-center">
                  <Trophy className="w-20 h-20 text-cyber-accent" />
                </div>
              </div>

              {/* 玩家名 */}
              <div className="mt-6 text-center">
                <h2 className="font-heading text-2xl text-cyber-text">{result.username}</h2>
                <p className="text-cyber-accent">文明架构师</p>
              </div>

              {/* 统计信息 */}
              <div className="mt-4 flex justify-center gap-4 text-center">
                <div>
                  <div className="font-mono text-xl text-cyber-text">{result.history.length}</div>
                  <div className="text-xs text-cyber-text-muted">轮次</div>
                </div>
                <div>
                  <div className="font-mono text-xl text-cyber-danger">{result.traitor_count}</div>
                  <div className="text-xs text-cyber-text-muted">内鬼</div>
                </div>
                <div>
                  <div className="font-mono text-xl text-cyber-success">{result.achievements.length}</div>
                  <div className="text-xs text-cyber-text-muted">成就</div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* 右侧：分析报告 */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6 }}
          >
            <div className="card h-full">
              <h3 className="font-heading text-lg text-cyber-accent mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5" />
                分析报告
              </h3>

              <div className="prose prose-invert prose-sm max-w-none">
                {result.analysis_report.split('\n').map((line, i) => {
                  if (line.startsWith('## ')) {
                    return (
                      <h4 key={i} className="font-heading text-cyber-accent mt-4 mb-2">
                        {line.replace('## ', '')}
                      </h4>
                    )
                  }
                  if (line.startsWith('**') && line.endsWith('**')) {
                    return (
                      <p key={i} className="text-cyber-text font-semibold">
                        {line.replace(/\*\*/g, '')}
                      </p>
                    )
                  }
                  if (line.startsWith('- ')) {
                    return (
                      <li key={i} className="text-cyber-text-muted ml-4">
                        {line.replace('- ', '')}
                      </li>
                    )
                  }
                  if (line.trim()) {
                    return (
                      <p key={i} className="text-cyber-text-muted">
                        {line}
                      </p>
                    )
                  }
                  return null
                })}
              </div>
            </div>
          </motion.div>
        </div>

        {/* 历史记录图表 */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="mt-8"
        >
          <div className="card">
            <h3 className="font-heading text-lg text-cyber-accent mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              历史趋势
            </h3>
            <div className="h-40 flex items-end gap-2">
              {result.history.map((entry, i) => (
                <div
                  key={i}
                  className="flex-1 flex flex-col items-center"
                >
                  <div
                    className="w-full bg-gradient-to-t from-cyber-accent to-cyber-success rounded-t"
                    style={{
                      height: `${Math.min(100, (entry.total_output / (result.total_output || 1)) * 100)}%`,
                    }}
                  />
                  <span className="text-xs text-cyber-text-muted mt-1">R{entry.round}</span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* 底部操作 */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="mt-8 flex justify-center gap-4"
        >
          <button
            onClick={() => navigate('/')}
            className="btn-primary flex items-center gap-2"
          >
            <RotateCcw className="w-5 h-5" />
            再来一局
          </button>
          <button
            onClick={() => navigate('/')}
            className="btn-secondary flex items-center gap-2"
          >
            <Home className="w-5 h-5" />
            返回主页
          </button>
        </motion.div>
      </div>
    </div>
  )
}

function VariableBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-cyber-text-muted">{label}</span>
        <span className="font-mono text-cyber-text">{(value * 100).toFixed(0)}%</span>
      </div>
      <div className="h-2 bg-cyber-border rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${value * 100}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>
    </div>
  )
}