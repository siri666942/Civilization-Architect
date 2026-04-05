import { createContext, useContext, useReducer, type ReactNode } from 'react'
import type { GameState, RoundResult, AgentPosition, FinalResult } from '@/types/game'

interface GameState {
  gameId: string | null
  username: string
  gameState: GameState | null
  currentRound: number
  isRunning: boolean
  roundResult: RoundResult | null
  finalResult: FinalResult | null
  agentPositions: AgentPosition[]
  messages: Array<{
    sender_id: string
    sender_name: string
    receiver_id: string
    receiver_name: string
    message_type: string
    content: string
    tone: string
    timestamp: string
    is_traitor: boolean
  }>
}

type GameAction =
  | { type: 'SET_USERNAME'; payload: string }
  | { type: 'SET_GAME_ID'; payload: string }
  | { type: 'SET_GAME_STATE'; payload: GameState }
  | { type: 'SET_RUNNING'; payload: boolean }
  | { type: 'SET_ROUND_RESULT'; payload: RoundResult }
  | { type: 'SET_FINAL_RESULT'; payload: FinalResult }
  | { type: 'UPDATE_AGENT_POSITIONS'; payload: AgentPosition[] }
  | { type: 'ADD_MESSAGES'; payload: GameState['messages'] }
  | { type: 'CLEAR_MESSAGES' }
  | { type: 'RESET' }

const initialState: GameState = {
  gameId: null,
  username: '',
  gameState: null,
  currentRound: 0,
  isRunning: false,
  roundResult: null,
  finalResult: null,
  agentPositions: [],
  messages: [],
}

function gameReducer(state: GameState, action: GameAction): GameState {
  switch (action.type) {
    case 'SET_USERNAME':
      return { ...state, username: action.payload }
    case 'SET_GAME_ID':
      return { ...state, gameId: action.payload }
    case 'SET_GAME_STATE':
      return {
        ...state,
        gameState: action.payload,
        currentRound: action.payload.current_round,
      }
    case 'SET_RUNNING':
      return { ...state, isRunning: action.payload }
    case 'SET_ROUND_RESULT':
      return {
        ...state,
        roundResult: action.payload,
        currentRound: action.payload.round_num,
        messages: [...state.messages, ...action.payload.messages],
      }
    case 'SET_FINAL_RESULT':
      return { ...state, finalResult: action.payload, isRunning: false }
    case 'UPDATE_AGENT_POSITIONS':
      return { ...state, agentPositions: action.payload }
    case 'ADD_MESSAGES':
      return { ...state, messages: [...state.messages, ...action.payload] }
    case 'CLEAR_MESSAGES':
      return { ...state, messages: [] }
    case 'RESET':
      return initialState
    default:
      return state
  }
}

interface GameContextType {
  state: GameState
  dispatch: React.Dispatch<GameAction>
}

const GameContext = createContext<GameContextType | undefined>(undefined)

interface GameProviderProps {
  children: ReactNode
}

export function GameProvider({ children }: GameProviderProps) {
  const [state, dispatch] = useReducer(gameReducer, initialState)
  return (
    <GameContext.Provider value={{ state, dispatch }}>
      {children}
    </GameContext.Provider>
  )
}

export function useGame() {
  const context = useContext(GameContext)
  if (context === undefined) {
    throw new Error('useGame must be used within a GameProvider')
  }
  return context
}