import axios from 'axios'
import type {
  GameState,
  ArchitectureType,
  AgentPosition,
  RoundResult,
  FinalResult
} from '@/types/game'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

export const gameApi = {
  // 开始新游戏
  startGame: async (username: string, architectureType: ArchitectureType, totalRounds = 10) => {
    const response = await api.post<GameState>('/game/start', {
      username,
      architecture_type: architectureType,
      total_rounds: totalRounds,
    })
    return response.data
  },

  // 获取游戏状态
  getGameStatus: async (gameId: string) => {
    const response = await api.get<GameState>(`/game/${gameId}/status`)
    return response.data
  },

  // 更新架构配置
  updateArchitecture: async (gameId: string, positions: AgentPosition[]) => {
    const response = await api.post(`/game/${gameId}/update-architecture`, {
      positions,
    })
    return response.data
  },

  // 执行一轮模拟
  runRound: async (gameId: string) => {
    const response = await api.post<RoundResult>(`/game/${gameId}/run-round`)
    return response.data
  },

  // 结束游戏
  endGame: async (gameId: string) => {
    const response = await api.post<FinalResult>(`/game/${gameId}/end`)
    return response.data
  },
}

export default api