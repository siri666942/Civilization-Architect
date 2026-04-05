import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Rocket, Sparkles } from 'lucide-react'
import { gameApi } from '@/services/api'
import { useGame } from '@/stores/GameContext'
import type { ArchitectureType } from '@/types/game'

export default function StartPage() {
  const [username, setUsername] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const { dispatch } = useGame()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!username.trim()) {
      setError('请输入指挥官代号')
      return
    }

    setIsLoading(true)
    setError('')

    try {
      // 默认使用树形架构，稍后在选择页面可以更改
      dispatch({ type: 'SET_USERNAME', payload: username })

      // 直接跳转到选择页面
      navigate('/select')
    } catch {
      setError('初始化失败，请重试')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-6xl w-full grid md:grid-cols-2 gap-12 items-center">
        {/* 左侧：游戏名称和简介 */}
        <motion.div
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          className="space-y-6"
        >
          <h1 className="font-display text-5xl md:text-6xl text-cyber-accent neon-text">
            文明架构师
          </h1>
          <p className="font-heading text-xl text-cyber-accent-alt">
            —— Agent文明的诞生
          </p>
          <div className="border-l-2 border-cyber-accent pl-6">
            <p className="font-body text-lg leading-relaxed text-cyber-text-muted">
              在遥远的星系中，一个新的文明正在崛起。作为文明的<span className="text-cyber-accent">架构师</span>，
              你需要选择组织架构、安排Agent位置，观察他们的<span className="text-cyber-accent-alt">互动</span>，
              最终见证文明的<span className="text-cyber-success">星辰值</span>。
            </p>
            <p className="font-body text-lg leading-relaxed text-cyber-text-muted mt-4">
              十位独特的Agent各有性格，他们会<span className="text-cyber-danger">内斗</span>、
              会<span className="text-cyber-accent">协作</span>、有时甚至会有
              <span className="text-cyber-accent-alt">内鬼</span>...
            </p>
          </div>

          {/* 装饰性数据流 */}
          <div className="h-20 overflow-hidden opacity-30">
            <div className="text-mono text-xs text-cyber-accent whitespace-pre-wrap">
{`01001000 01100101 01101100 01101100 01101111
AGENT_INIT... OK
CIVILIZATION_MATRIX... LOADING
QUANTUM_LINK... ESTABLISHED`}
            </div>
          </div>
        </motion.div>

        {/* 右侧：输入表单 */}
        <motion.div
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="flex justify-center"
        >
          <div className="card w-full max-w-md p-8">
            <div className="text-center mb-8">
              <Rocket className="w-12 h-12 mx-auto mb-4 text-cyber-accent" />
              <h2 className="font-heading text-2xl text-cyber-text">
                输入你的<span className="text-cyber-accent">指挥官代号</span>
              </h2>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="请输入代号..."
                  maxLength={12}
                  className="input-cyber text-center text-xl font-heading"
                  disabled={isLoading}
                />
              </div>

              {error && (
                <p className="text-cyber-danger text-center text-sm">{error}</p>
              )}

              <button
                type="submit"
                disabled={isLoading || !username.trim()}
                className={`btn-primary w-full flex items-center justify-center gap-2 ${
                  (!username.trim() || isLoading) ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                {isLoading ? (
                  <>
                    <Sparkles className="w-5 h-5 animate-spin" />
                    <span>正在初始化...</span>
                  </>
                ) : (
                  <>
                    <Rocket className="w-5 h-5" />
                    <span>开始游戏</span>
                  </>
                )}
              </button>
            </form>

            <p className="text-center text-cyber-text-muted text-sm mt-6">
              准备好开启你的文明之旅了吗？
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  )
}