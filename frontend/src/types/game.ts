// 游戏相关类型定义

export type ArchitectureType = 'star' | 'tree' | 'mesh' | 'tribal'

export interface Personality {
  authority: number
  selfishness: number
  resilience: number
  altruism: number
  sociability: number
  risk_appetite: number
  intelligence: number
  loyalty_base: number
}

export interface Agent {
  id: string
  name: string
  description: string
  personality: Personality
  position: 'core' | 'middle' | 'edge'
  level: number
  centrality: number
  is_traitor: boolean
}

export interface CivilizationState {
  total_output: number
  cycle_outputs: number[]
}

export interface GameState {
  game_id: string
  username: string
  architecture_type: ArchitectureType
  current_round: number
  total_rounds: number
  agents: Agent[]
  civilization_state: CivilizationState
  adjacency_matrix: number[][]
}

export interface Message {
  sender_id: string
  sender_name: string
  receiver_id: string
  receiver_name: string
  message_type: string
  content: string
  tone: string
  timestamp: string
  is_traitor: boolean
}

export interface MacroVariables {
  energy_level: number
  cohesion: number
  fidelity: number
  social_capital: number
}

export interface RoundResult {
  round_num: number
  cycle_outputs: number[]
  total_output: number
  macro_variables: MacroVariables
  messages: Message[]
}

export interface AgentPosition {
  agent_id: string
  position_index: number
  connections: number[]
}

export interface FinalResult {
  game_id: string
  username: string
  architecture_type: string
  total_output: number
  final_macro_variables: MacroVariables
  traitor_count: number
  achievements: string[]
  analysis_report: string
  history: Array<{
    round: number
    total_output: number
    energy_level: number
    cohesion: number
    fidelity: number
    social_capital: number
  }>
}

// API 响应类型
export interface ApiResponse<T> {
  success: boolean
  data: T | null
  error?: string
  timestamp: string
}